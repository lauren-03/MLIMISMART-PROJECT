"""Rain prediction model: will it rain at least 1 mm tomorrow in an area?"""
import logging
import math
from datetime import date, timedelta

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.inspection import permutation_importance
from sklearn.metrics import (accuracy_score, brier_score_loss, f1_score,
                             precision_score, recall_score, roc_auc_score)
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..data.locations import LOCATIONS, resolve
from ..models import RainPrediction, WeatherHistory
from . import climate, history, store

log = logging.getLogger(__name__)

NAME = "rain"
RAIN_DAY_MM = 1.0
FEATURES = [
    "rain_today", "rain_yesterday", "rain_2_days_ago", "rain_3_days", "rain_7_days",
    "tmax", "tmin", "temp_range", "humidity", "humidity_change",
    "pressure", "pressure_change_1d", "pressure_change_2d",
    "wind", "cloud", "cloud_change", "season_sin", "season_cos",
    "altitude", "latitude", "longitude",
]
WEATHER_ONLY = len(FEATURES)
FEATURES = FEATURES + climate.FEATURES
SOURCES = ["Open-Meteo / ERA5 (daily weather)", "ERA5-Land (soil moisture)",
           "NASA POWER (rain, sunshine, soil wetness)", "CHIRPS (monthly rainfall)"]


def _v(x):
    return np.nan if x is None else float(x)


def features(rows: list[WeatherHistory], i: int, place: dict,
             clim: climate.Climate | None = None, name: str | None = None) -> list[float]:
    """Feature vector for day rows[i] (needs at least two earlier days)."""
    r, p, q = rows[i], rows[i - 1], rows[i - 2]
    week = rows[max(0, i - 6): i + 1]
    doy = r.day.timetuple().tm_yday
    return [
        _v(r.rain_mm), _v(p.rain_mm), _v(q.rain_mm),
        sum((x.rain_mm or 0) for x in rows[i - 2: i + 1]),
        sum((x.rain_mm or 0) for x in week),
        _v(r.tmax), _v(r.tmin), _v(None if r.tmax is None or r.tmin is None else r.tmax - r.tmin),
        _v(r.humidity), _v(None if r.humidity is None or p.humidity is None else r.humidity - p.humidity),
        _v(r.pressure),
        _v(None if r.pressure is None or p.pressure is None else r.pressure - p.pressure),
        _v(None if r.pressure is None or q.pressure is None else r.pressure - q.pressure),
        _v(r.wind_kph), _v(r.cloud), _v(None if r.cloud is None or p.cloud is None else r.cloud - p.cloud),
        math.sin(2 * math.pi * doy / 365.25), math.cos(2 * math.pi * doy / 365.25),
        float(place["altitude_m"]), place["lat"], place["lon"],
        *(clim.features(name, r.day) if clim else [np.nan] * len(climate.FEATURES)),
    ]


def dataset(db: Session):
    """X, y, the target day of each row, and the 'same as today' guess."""
    X, y, days, persistence = [], [], [], []
    clim = climate.load(db)
    for name, rows in history.series(db).items():
        place = LOCATIONS.get(name)
        if place is None:
            continue
        for i in range(2, len(rows) - 1):
            if rows[i + 1].day - rows[i].day != timedelta(days=1):
                continue
            X.append(features(rows, i, place, clim, name))
            y.append(int((rows[i + 1].rain_mm or 0) >= RAIN_DAY_MM))
            days.append(rows[i + 1].day)
            persistence.append(int((rows[i].rain_mm or 0) >= RAIN_DAY_MM))
    return np.array(X, dtype=float), np.array(y), np.array(days), np.array(persistence)


def _model():
    return HistGradientBoostingClassifier(max_iter=300, learning_rate=0.06,
                                          max_leaf_nodes=31, random_state=0)


def train(db: Session) -> dict:
    X, y, days, persistence = dataset(db)
    if len(y) < 1000:
        raise RuntimeError("Not enough weather history to train the rain model yet")

    cutoff = days.max() - timedelta(days=365)
    train_mask, test_mask = days <= cutoff, days > cutoff
    # Climatology baseline probability, from the training years only.
    train_rainy_rate = float(y[train_mask].mean())
    model = _model().fit(X[train_mask], y[train_mask])
    prob = model.predict_proba(X[test_mask])[:, 1]
    pred = (prob >= 0.5).astype(int)
    truth = y[test_mask]
    metrics = {
        "accuracy": round(accuracy_score(truth, pred), 3),
        "precision": round(precision_score(truth, pred, zero_division=0), 3),
        "recall": round(recall_score(truth, pred, zero_division=0), 3),
        "f1": round(f1_score(truth, pred, zero_division=0), 3),
        "roc_auc": round(roc_auc_score(truth, prob), 3),
        "brier": round(brier_score_loss(truth, prob), 3),
        "baseline_same_as_today": round(accuracy_score(truth, persistence[test_mask]), 3),
        "rainy_day_share": round(float(truth.mean()), 3),

        # Both baselines below are scored with brier_score_loss on exactly the
        # same test rows as the model, so the three Brier figures are
        # comparable. Persistence forecasts a hard 0 or 1, for which the Brier
        # score equals its error rate; it is still computed directly rather
        # than inferred from the accuracy above. The climatology forecast is
        # the rainy-day rate of the TRAINING years only, so that the baseline
        # never sees the held-out year it is being judged on.
        "brier_persistence": round(
            brier_score_loss(truth, persistence[test_mask].astype(float)), 3),
        "brier_climatology": round(
            brier_score_loss(truth, np.full(truth.shape, train_rainy_rate)), 3),
        "climatology_probability": round(float(train_rainy_rate), 3),
        "brier_skill_vs_climatology": round(
            1 - brier_score_loss(truth, prob)
            / brier_score_loss(truth, np.full(truth.shape, train_rainy_rate)), 3),
        "brier_skill_vs_persistence": round(
            1 - brier_score_loss(truth, prob)
            / brier_score_loss(truth, persistence[test_mask].astype(float)), 3),
        "test_period": f"{(cutoff + timedelta(days=1)).isoformat()} to {days.max().isoformat()}",
        "areas": len(LOCATIONS),
        "inputs": len(FEATURES),
        "sources": SOURCES,
    }

    # The same model using only the daily weather, to show what the extra
    # datasets add.
    base = _model().fit(X[train_mask][:, :WEATHER_ONLY], y[train_mask])
    metrics["accuracy_weather_only"] = round(accuracy_score(
        truth, base.predict(X[test_mask][:, :WEATHER_ONLY])), 3)
    metrics["roc_auc_weather_only"] = round(roc_auc_score(
        truth, base.predict_proba(X[test_mask][:, :WEATHER_ONLY])[:, 1]), 3)

    # Which inputs the model relies on most (drop in AUC when shuffled).
    sample = np.random.default_rng(0).choice(int(test_mask.sum()), size=min(3000, int(test_mask.sum())),
                                             replace=False)
    imp = permutation_importance(model, X[test_mask][sample], truth[sample], scoring="roc_auc",
                                 n_repeats=3, random_state=0)
    ranked = sorted(zip(FEATURES, imp.importances_mean), key=lambda kv: -kv[1])[:8]
    metrics["top_inputs"] = [[name, round(float(v), 4)] for name, v in ranked]

    # Evaluated on the held-out year; the model in use learns from every day.
    final = _model().fit(X, y)
    version = store.save(db, NAME, final, train_rows=int(train_mask.sum()),
                         test_rows=int(test_mask.sum()), metrics=metrics)
    log.info("Rain model v%d trained: accuracy %.3f (same-as-today %.3f), AUC %.3f",
             version, metrics["accuracy"], metrics["baseline_same_as_today"], metrics["roc_auc"])
    return {"version": version, **metrics}


def probability_for(db: Session, location: str) -> dict | None:
    """The model's chance of rain on the day after the latest stored day."""
    version, model = store.load(NAME)
    if model is None:
        return None
    name, place = resolve(location)
    rows = history.recent(db, name, 7)
    if len(rows) < 3:
        return None
    clim = climate.load(db, location=name, since=date.today() - timedelta(days=90))
    prob = float(model.predict_proba([features(rows, len(rows) - 1, place, clim, name)])[0, 1])
    target = rows[-1].day + timedelta(days=1)
    if target < date.today():
        return None  # weather history is behind; no prediction for a past day
    _remember(db, name, target, prob, version)
    return {"location": name, "target_day": target.isoformat(), "probability": round(prob, 3),
            "will_rain": prob >= 0.5, "model_version": version}


def _remember(db: Session, location: str, target: date, prob: float, version: int) -> None:
    row = db.scalar(select(RainPrediction).where(RainPrediction.location == location,
                                                 RainPrediction.target_day == target))
    if row is None:
        db.add(RainPrediction(location=location, target_day=target,
                              probability=prob, model_version=version))
    elif row.actual_rain_mm is None:
        row.probability, row.model_version = prob, version
    db.commit()


def check_past_predictions(db: Session) -> int:
    """Compare predictions with the rain that actually fell."""
    pending = db.scalars(select(RainPrediction).where(RainPrediction.actual_rain_mm.is_(None),
                                                      RainPrediction.target_day < date.today())).all()
    checked = 0
    for p in pending:
        actual = db.scalar(select(WeatherHistory.rain_mm).where(
            WeatherHistory.location == p.location, WeatherHistory.day == p.target_day))
        if actual is None:
            continue
        p.actual_rain_mm = actual
        p.correct = (p.probability >= 0.5) == (actual >= RAIN_DAY_MM)
        checked += 1
    db.commit()
    return checked


def live_accuracy(db: Session) -> dict:
    rows = db.scalars(select(RainPrediction).where(RainPrediction.correct.is_not(None))).all()
    if not rows:
        return {"checked": 0, "accuracy": None}
    return {"checked": len(rows), "accuracy": round(sum(r.correct for r in rows) / len(rows), 3)}


def predict_all(db: Session) -> int:
    return sum(1 for name in LOCATIONS if probability_for(db, name))
