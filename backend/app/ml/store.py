"""Saving, loading and recording trained models."""
import json
from pathlib import Path

import joblib
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from ..models import ModelRun

STORE = Path(__file__).resolve().parents[2] / "ml_store"
STORE.mkdir(exist_ok=True)

_cache: dict[str, tuple[int, object]] = {}


def next_version(db: Session, name: str) -> int:
    latest = db.scalar(select(func.max(ModelRun.version)).where(ModelRun.model_name == name))
    return (latest or 0) + 1


def save(db: Session, name: str, model, *, train_rows: int, test_rows: int, metrics: dict) -> int:
    version = next_version(db, name)
    joblib.dump({"version": version, "model": model}, STORE / f"{name}.joblib")
    db.add(ModelRun(model_name=name, version=version, train_rows=train_rows,
                    test_rows=test_rows, metrics=json.dumps(metrics)))
    db.commit()
    _cache[name] = (version, model)
    return version


def load(name: str):
    """(version, model) or (None, None) if the model has never been trained."""
    if name in _cache:
        return _cache[name]
    path = STORE / f"{name}.joblib"
    if not path.exists():
        return None, None
    data = joblib.load(path)
    _cache[name] = (data["version"], data["model"])
    return _cache[name]


def runs(db: Session, name: str, limit: int = 20) -> list[dict]:
    rows = db.scalars(select(ModelRun).where(ModelRun.model_name == name)
                      .order_by(desc(ModelRun.version)).limit(limit)).all()
    return [{"version": r.version, "train_rows": r.train_rows, "test_rows": r.test_rows,
             "metrics": json.loads(r.metrics), "trained_at": r.trained_at} for r in rows]
