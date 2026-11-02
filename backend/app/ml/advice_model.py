"""Advice decision model."""
import json
import logging
import math
import random
from datetime import date, datetime, timedelta

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..data.locations import LOCATIONS, resolve
from ..models import AdviceDecision, ModelRun
from . import climate, history, rain_model, store
from .actions import ACTIONS, ALL_ACTIONS, TOPICS, expert_label

log = logging.getLogger(__name__)

NAME = "advice"
SEED_SITUATIONS = 1500
FEEDBACK_WEIGHT = 25.0
RETRAIN_EVERY = 5
NUMERIC = ["rain_today", "rain_tomorrow", "rain_prob", "rain_3d", "tmax", "humidity", "wind",
           "soil_moisture", "rain_anomaly", "month"]


def encode(f: dict, topic: str, action: str) -> list[float]:
    month = f["month"]
    row = [math.nan if f.get(k) is None else float(f[k]) for k in NUMERIC if k != "month"]
    row += [math.sin(2 * math.pi * month / 12), math.cos(2 * math.pi * month / 12), float(f["altitude"])]
    row += [1.0 if topic == t else 0.0 for t in TOPICS]
    row += [1.0 if (topic, action) == pair else 0.0 for pair in ALL_ACTIONS]
    return row


def situation(db: Session, location: str, weather: dict, rain: dict | None) -> dict:
    """Features describing today's situation in one area."""
    name, place = resolve(location)
    recent = history.recent(db, name, 4)
    past = [r for r in recent if r.day < date.today()][-3:]
    current = weather.get("current", {}) if not weather.get("offline") else {}
    forecast = weather.get("forecast") or []
    tomorrow = forecast[1] if len(forecast) > 1 else {}
    last = recent[-1] if recent else None

    rain_prob = rain["probability"] if rain else (tomorrow.get("rain_probability") or 0) / 100
    clim = climate.load(db, location=name, since=date.today() - timedelta(days=30))
    return {
        "soil_moisture": clim.soil_top(name, date.today()),
        "rain_anomaly": clim.chirps_anomaly(name, date.today()),
        "rain_today": current.get("rain_today_mm") if current.get("rain_today_mm") is not None
        else (last.rain_mm if last else 0) or 0,
        "rain_tomorrow": tomorrow.get("rain_mm") or 0,
        "rain_prob": rain_prob,
        "rain_3d": sum((r.rain_mm or 0) for r in past),
        "tmax": (forecast[0].get("temp_max") if forecast else None)
        or current.get("temperature") or (last.tmax if last else 25) or 25,
        "humidity": current.get("humidity") or (last.humidity if last else 70) or 70,
        "wind": current.get("wind_kph") or (last.wind_kph if last else 10) or 10,
        "month": date.today().month,
        "altitude": place["altitude_m"],
    }


def _seed_situations(db: Session) -> list[dict]:
    """Real past days from the weather history, with the rain model's view of each."""
    rng = random.Random(42)
    version, rmodel = store.load(rain_model.NAME)
    picks = []
    for name, rows in history.series(db).items():
        place = LOCATIONS.get(name)
        if place is None or len(rows) < 10:
            continue
        for i in range(3, len(rows) - 1):
            picks.append((name, place, rows, i))
    rng.shuffle(picks)
    picks = picks[:SEED_SITUATIONS]

    clim = climate.load(db)
    X = [rain_model.features(rows, i, place, clim, name) for name, place, rows, i in picks]
    probs = rmodel.predict_proba(np.array(X, dtype=float))[:, 1] if rmodel is not None and X else None
    out = []
    for k, (name, place, rows, i) in enumerate(picks):
        r = rows[i]
        out.append({
            "soil_moisture": clim.soil_top(name, r.day),
            "rain_anomaly": clim.chirps_anomaly(name, r.day),
            "rain_today": r.rain_mm or 0,
            "rain_tomorrow": rows[i + 1].rain_mm or 0,
            "rain_prob": float(probs[k]) if probs is not None else float((rows[i + 1].rain_mm or 0) >= 1),
            "rain_3d": sum((x.rain_mm or 0) for x in rows[i - 3:i]),
            "tmax": r.tmax or 25, "humidity": r.humidity or 70, "wind": r.wind_kph or 10,
            "month": r.day.month, "altitude": place["altitude_m"],
        })
    return out


def _rows_for(situations: list[dict]):
    X, y = [], []
    for f in situations:
        for topic in TOPICS:
            best = expert_label(topic, f)
            for action in ACTIONS[topic]:
                X.append(encode(f, topic, action))
                y.append(1 if action == best else 0)
    return X, y


def _model():
    return HistGradientBoostingClassifier(max_iter=200, learning_rate=0.08, random_state=0)


def _choose(model, f: dict, topic: str) -> tuple[str, dict]:
    actions = list(ACTIONS[topic])
    probs = model.predict_proba(np.array([encode(f, topic, a) for a in actions]))[:, 1]
    scores = {a: round(float(p), 3) for a, p in zip(actions, probs)}
    return max(scores, key=scores.get), scores


def train(db: Session) -> dict:
    situations = _seed_situations(db)
    if len(situations) < 200:
        raise RuntimeError("Not enough weather history to train the advice model yet")
    split = int(len(situations) * 0.8)
    train_sit, test_sit = situations[:split], situations[split:]

    ratings = db.scalars(select(AdviceDecision).where(AdviceDecision.helpful.is_not(None))).all()
    fb_X = [encode(json.loads(r.features), r.topic, r.action) for r in ratings]
    fb_y = [1 if r.helpful else 0 for r in ratings]

    def fit(sits):
        X, y = _rows_for(sits)
        weights = [1.0] * len(y) + [FEEDBACK_WEIGHT] * len(fb_y)
        return _model().fit(np.array(X + fb_X, dtype=float), np.array(y + fb_y), sample_weight=weights)

    model = fit(train_sit)
    agree = total = 0
    for f in test_sit:
        for topic in TOPICS:
            total += 1
            agree += _choose(model, f, topic)[0] == expert_label(topic, f)

    helpful = sum(fb_y)
    metrics = {
        "decision_accuracy": round(agree / total, 3),
        "test_cases": total,
        "farmer_ratings": len(fb_y),
        "rated_helpful": round(helpful / len(fb_y), 3) if fb_y else None,
        "topics": len(TOPICS),
        "actions": len(ALL_ACTIONS),
    }
    final = fit(situations)
    version = store.save(db, NAME, final, train_rows=len(situations) * len(ALL_ACTIONS) + len(fb_y),
                         test_rows=total, metrics=metrics)
    log.info("Advice model v%d trained: decision accuracy %.3f, %d farmer ratings",
             version, metrics["decision_accuracy"], len(fb_y))
    return {"version": version, **metrics}


def decide(topic: str, f: dict) -> dict | None:
    """The model's chosen action for a topic, or None if it is not trained."""
    version, model = store.load(NAME)
    if model is None or topic not in ACTIONS:
        return None
    action, scores = _choose(model, f, topic)
    return {"action": action, "confidence": scores[action], "scores": scores, "version": version}


def record(db: Session, request_id: int, topic: str, decision: dict, f: dict) -> None:
    db.add(AdviceDecision(request_id=request_id, topic=topic, action=decision["action"],
                          confidence=decision["confidence"], features=json.dumps(f),
                          model_version=decision["version"]))
    db.commit()


def rate(db: Session, request_id: int, helpful: bool) -> AdviceDecision | None:
    row = db.scalar(select(AdviceDecision).where(AdviceDecision.request_id == request_id))
    if row is None:
        return None
    row.helpful, row.rated_at = helpful, datetime.now()
    db.commit()
    return row


def ratings_since_last_training(db: Session) -> int:
    last = db.scalar(select(func.max(ModelRun.trained_at)).where(ModelRun.model_name == NAME))
    query = select(func.count()).select_from(AdviceDecision).where(AdviceDecision.rated_at.is_not(None))
    if last:
        query = query.where(AdviceDecision.rated_at > last)
    return db.scalar(query) or 0
