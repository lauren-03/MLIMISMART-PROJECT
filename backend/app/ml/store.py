"""Saving, loading, approving and recording trained models.

Where models live
-----------------
Render replaces the container filesystem on every deployment, so a model
written only to ``ml_store/`` disappears the next time the site deploys.
Every saved model is therefore also written into the database as bytes,
together with the record of how it was trained and how well it scored.

Approval
--------
``load`` returns the newest approved and active model, not the newest one
trained. A training run that scores badly, or that has not been looked at
yet, can be saved without taking over from the model farmers are using.
The day-ahead models keep approving themselves, which is what they did
before; the seasonal model is saved unapproved and must be approved on
purpose with ``approve()``.
"""
import hashlib
import io
import json
import logging
from datetime import date, datetime, timezone
from pathlib import Path

import joblib
from sqlalchemy import desc, func, select, update as sa_update
from sqlalchemy.orm import Session

from ..models import ModelArtifact, ModelRun

log = logging.getLogger(__name__)

STORE = Path(__file__).resolve().parents[2] / "ml_store"
STORE.mkdir(exist_ok=True)

_cache: dict[str, tuple[int, object]] = {}


def _library_versions() -> str:
    import sys

    import numpy
    import sklearn
    return json.dumps({
        "python": sys.version.split()[0],
        "numpy": numpy.__version__,
        "scikit-learn": sklearn.__version__,
        "joblib": joblib.__version__,
    })


def next_version(db: Session, name: str) -> int:
    latest = db.scalar(select(func.max(ModelRun.version)).where(ModelRun.model_name == name))
    return (latest or 0) + 1


def save(db: Session, name: str, model, *, train_rows: int, test_rows: int,
         metrics: dict, approve: bool = True, dataset_version: str = "",
         training_start: date | None = None, training_end: date | None = None,
         features: list[str] | None = None, report: dict | None = None,
         notes: str | None = None) -> int:
    """Store a trained model and the record of its training.

    ``approve=False`` keeps the model out of service until someone has read
    its evaluation report and called ``approve()``.
    """
    version = next_version(db, name)

    # Serialise once, so the file and the database hold identical bytes.
    buffer = io.BytesIO()
    joblib.dump({"version": version, "model": model}, buffer)
    blob = buffer.getvalue()

    db.add(ModelRun(model_name=name, version=version, train_rows=train_rows,
                    test_rows=test_rows, metrics=json.dumps(metrics)))
    row = ModelArtifact(
        model_name=name, version=version, artifact=blob,
        artifact_sha256=hashlib.sha256(blob).hexdigest(),
        artifact_bytes=len(blob),
        dataset_version=dataset_version or "unspecified",
        training_start=training_start, training_end=training_end,
        features=json.dumps(features or []),
        train_rows=train_rows, test_rows=test_rows,
        metrics=json.dumps(metrics),
        report=json.dumps(report, default=str) if report else None,
        library_versions=_library_versions(),
        approved=approve, active=False, notes=notes,
        approved_by="training job" if approve else None,
        approved_at=datetime.now(timezone.utc) if approve else None,
    )
    db.add(row)
    db.commit()

    if approve:
        activate(db, name, version)
        (STORE / f"{name}.joblib").write_bytes(blob)
        _cache[name] = (version, model)
        log.info("Model %s v%d saved, approved and active", name, version)
    else:
        log.info("Model %s v%d saved but NOT approved; the active model is unchanged",
                 name, version)
    return version


def approve(db: Session, name: str, version: int, by: str = "manual",
            activate_now: bool = True) -> bool:
    """Mark a saved model fit for service. False if that version is not there."""
    row = db.scalar(select(ModelArtifact).where(ModelArtifact.model_name == name,
                                                ModelArtifact.version == version))
    if row is None:
        return False
    row.approved = True
    row.approved_by = by
    row.approved_at = datetime.now(timezone.utc)
    db.commit()
    if activate_now:
        activate(db, name, version)
    return True


def activate(db: Session, name: str, version: int) -> bool:
    """Make one approved version the one the backend serves."""
    row = db.scalar(select(ModelArtifact).where(ModelArtifact.model_name == name,
                                                ModelArtifact.version == version))
    if row is None or not row.approved:
        return False
    db.execute(sa_update(ModelArtifact)
               .where(ModelArtifact.model_name == name)
               .values(active=False))
    row.active = True
    db.commit()
    _cache.pop(name, None)
    return True


def _approved_row(db: Session, name: str) -> ModelArtifact | None:
    """The active approved model, or the newest approved one if none is flagged."""
    row = db.scalar(select(ModelArtifact).where(ModelArtifact.model_name == name,
                                                ModelArtifact.approved.is_(True),
                                                ModelArtifact.active.is_(True)))
    if row is not None:
        return row
    return db.scalar(select(ModelArtifact)
                     .where(ModelArtifact.model_name == name,
                            ModelArtifact.approved.is_(True))
                     .order_by(desc(ModelArtifact.version)).limit(1))


def load(name: str, db: Session | None = None):
    """(version, model), or (None, None) if there is no approved model.

    Looks in memory, then on disk, then in the database. The database copy
    is the one that survives a deployment, so it is written back to disk
    once fetched.
    """
    if name in _cache:
        return _cache[name]

    path = STORE / f"{name}.joblib"
    if path.exists():
        data = joblib.load(path)
        _cache[name] = (data["version"], data["model"])
        return _cache[name]

    if db is None:
        return None, None
    row = _approved_row(db, name)
    if row is None:
        return None, None
    if hashlib.sha256(row.artifact).hexdigest() != row.artifact_sha256:
        log.error("Model %s v%d failed its checksum and was not loaded", name, row.version)
        return None, None
    data = joblib.load(io.BytesIO(row.artifact))
    path.write_bytes(row.artifact)
    _cache[name] = (row.version, data["model"])
    log.info("Model %s v%d restored from the database", name, row.version)
    return _cache[name]


def restore_all(db: Session) -> list[str]:
    """Write every approved model from the database to disk, at startup.

    This is what makes a deployment survivable: the container starts with an
    empty ``ml_store/`` and fills it from the database before serving.
    """
    restored = []
    names = db.scalars(select(ModelArtifact.model_name)
                       .where(ModelArtifact.approved.is_(True)).distinct()).all()
    for name in names:
        if (STORE / f"{name}.joblib").exists():
            continue
        version, model = load(name, db)
        if model is not None:
            restored.append(f"{name} v{version}")
    return restored


def runs(db: Session, name: str, limit: int = 20) -> list[dict]:
    rows = db.scalars(select(ModelRun).where(ModelRun.model_name == name)
                      .order_by(desc(ModelRun.version)).limit(limit)).all()
    return [{"version": r.version, "train_rows": r.train_rows, "test_rows": r.test_rows,
             "metrics": json.loads(r.metrics), "trained_at": r.trained_at} for r in rows]


def artifacts(db: Session, name: str | None = None, limit: int = 20) -> list[dict]:
    """The stored models and their approval state, newest first."""
    if name:
        query = select(ModelArtifact).where(ModelArtifact.model_name == name) \
            .order_by(desc(ModelArtifact.version)).limit(limit)
    else:
        query = select(ModelArtifact).order_by(desc(ModelArtifact.id)).limit(limit)
    return [{
        "model_name": r.model_name, "version": r.version,
        "dataset_version": r.dataset_version,
        "training_period": [r.training_start, r.training_end],
        "features": json.loads(r.features or "[]"),
        "train_rows": r.train_rows, "test_rows": r.test_rows,
        "metrics": json.loads(r.metrics or "{}"),
        "size_bytes": r.artifact_bytes, "sha256": r.artifact_sha256,
        "approved": r.approved, "active": r.active,
        "approved_by": r.approved_by, "trained_at": r.trained_at,
        "notes": r.notes,
    } for r in db.scalars(query).all()]
