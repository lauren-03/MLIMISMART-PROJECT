# -*- coding: utf-8 -*-
"""Train the seasonal rainfall classifier for MlimiSmart.

Run this as a one-off job, never inside a farmer request. It reads the
weather history from the database, builds one row per area per season,
labels each row below / normal / above normal, trains a classifier and
writes an evaluation report. The backend only ever loads the saved model.

    python train_seasonal.py --report seasonal_report.json

What the model predicts
-----------------------
Total rainfall of the Malawi main rainy season, November to April, placed
in one of three classes. Season "2019" means Nov 2019 to Apr 2020.

Three periods are kept distinct, as they must be when reporting this:

  observation period   every day of weather held in the database
  reference period     the seasons used to work out the tercile cut-offs
  target seasons       the seasons the model is asked to classify

Why the thresholds move
-----------------------
Terciles are recomputed inside every fold from the training seasons alone.
If they were computed once over all seasons, the held-out season would have
helped decide its own class boundary, and the score would be optimistic.

Predictors
----------
Only things known before 1 November of the season being predicted: the dry
season that preceded it, the previous season's rainfall, and where the area
is. Nothing from inside the target season is used.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from datetime import date

import numpy as np

from app.ml import store

SEASON_START_MONTH = 11          # November
SEASON_MONTHS = 6                # November to April inclusive
PRE_SEASON = (7, 8, 9, 10)       # the dry months that precede it
CLASSES = ["below", "normal", "above"]


def season_of(day: date) -> int | None:
    """Which season a day belongs to, or None if outside Nov-Apr."""
    if day.month >= SEASON_START_MONTH:
        return day.year
    if day.month <= (SEASON_START_MONTH + SEASON_MONTHS - 1) - 12:
        return day.year - 1
    return None


def pre_season_of(day: date) -> int | None:
    """The season whose July-October run-up this day belongs to."""
    return day.year if day.month in PRE_SEASON else None


# ---------------------------------------------------------------- dataset
def build_rows(db) -> list[dict]:
    """One row per area per season, from the weather history."""
    from app.data.locations import LOCATIONS
    from app.ml import history

    season_rain: dict = defaultdict(float)
    season_days: dict = defaultdict(int)
    pre_rain: dict = defaultdict(float)
    pre_days: dict = defaultdict(int)
    pre_tmax: dict = defaultdict(list)

    for name, rows in history.series(db).items():
        if name not in LOCATIONS:
            continue
        for r in rows:
            s = season_of(r.day)
            if s is not None:
                season_days[(name, s)] += 1
                if r.rain_mm is not None:
                    season_rain[(name, s)] += r.rain_mm
            p = pre_season_of(r.day)
            if p is not None:
                pre_days[(name, p)] += 1
                if r.rain_mm is not None:
                    pre_rain[(name, p)] += r.rain_mm
                if r.tmax is not None:
                    pre_tmax[(name, p)].append(r.tmax)

    # A season needs nearly all its days present before it can be labelled.
    expected = 181
    out = []
    for (name, s), days in sorted(season_days.items()):
        if days < expected * 0.95:
            continue
        if pre_days.get((name, s), 0) < 100:
            continue
        place = LOCATIONS[name]
        tmaxes = pre_tmax.get((name, s), [])
        out.append({
            "area": name,
            "season": s,
            "rain_total": season_rain[(name, s)],
            "days": days,
            # predictors, all known before 1 November of season s
            "pre_rain": pre_rain.get((name, s), 0.0),
            "pre_tmax": float(np.mean(tmaxes)) if tmaxes else float("nan"),
            "prev_rain": season_rain.get((name, s - 1), float("nan")),
            "altitude": float(place["altitude_m"]),
            "lat": float(place["lat"]),
            "lon": float(place["lon"]),
        })
    return out


def terciles(values: list[float]) -> tuple[float, float]:
    """The two cut-offs that split a set of season totals into thirds."""
    a, b = np.quantile(np.asarray(values, dtype=float), [1 / 3, 2 / 3])
    return float(a), float(b)


def label_of(total: float, low: float, high: float) -> str:
    if total < low:
        return "below"
    if total > high:
        return "above"
    return "normal"


FEATURES = ["pre_rain", "pre_tmax", "prev_rain", "altitude", "lat", "lon"]


def matrix(rows: list[dict]) -> np.ndarray:
    return np.array([[r[f] for f in FEATURES] for r in rows], dtype=float)


# ------------------------------------------------------------- evaluation
def leave_one_season_out(rows: list[dict]) -> dict:
    """Validate by holding out one whole season at a time.

    Holding out a season, rather than random rows, is what stops the model
    being judged on a year it has already seen through a neighbouring area.
    Terciles are recomputed from the training seasons inside each fold.
    """
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import (balanced_accuracy_score, classification_report,
                                 confusion_matrix, f1_score)

    seasons = sorted({r["season"] for r in rows})
    truth_all, pred_all, base_all, persist_all = [], [], [], []
    clim_expected = []   # expected accuracy of guessing at the training rates

    for held in seasons:
        train = [r for r in rows if r["season"] != held]
        test = [r for r in rows if r["season"] == held]
        if not test or len(train) < 20:
            continue

        # cut-offs from the training seasons only
        low, high = terciles([r["rain_total"] for r in train])
        y_train = [label_of(r["rain_total"], low, high) for r in train]
        y_test = [label_of(r["rain_total"], low, high) for r in test]

        model = RandomForestClassifier(
            n_estimators=400, min_samples_leaf=3, random_state=0)
        model.fit(matrix(train), y_train)
        pred = model.predict(matrix(test))

        # baseline 1: always say normal
        base_all.extend(["normal"] * len(test))
        # baseline 2: the class this area had last season
        prev = {}
        for r in train:
            if r["season"] == held - 1:
                prev[r["area"]] = label_of(r["rain_total"], low, high)
        persist_all.extend([prev.get(r["area"], "normal") for r in test])

        # baseline 3: climatology. Guessing each class at the rate it had in
        # the training seasons. Its expected accuracy is the sum of p_i * q_i,
        # the training rate times the rate in the held-out season, which is
        # scored exactly rather than by drawing random guesses.
        for cls in CLASSES:
            p_train = y_train.count(cls) / len(y_train)
            clim_expected.append(p_train * y_test.count(cls))

        truth_all.extend(y_test)
        pred_all.extend(list(pred))

    if not truth_all:
        return {"error": "no fold had enough data to evaluate"}

    def scores(pred):
        return {
            "accuracy": round(float(np.mean(np.array(truth_all) == np.array(pred))), 3),
            "balanced_accuracy": round(balanced_accuracy_score(truth_all, pred), 3),
            "macro_f1": round(f1_score(truth_all, pred, average="macro",
                                       labels=CLASSES, zero_division=0), 3),
        }

    return {
        "folds": len(seasons),
        "observations": len(truth_all),
        "model": scores(pred_all),
        "baseline_always_normal": scores(base_all),
        "baseline_previous_season": scores(persist_all),
        "baseline_climatology": {
            "expected_accuracy": round(sum(clim_expected) / len(truth_all), 3),
            "note": ("Guessing the three classes at their training-season "
                     "rates. Scored as an expected value, not by drawing "
                     "random guesses, so it does not move between runs."),
        },
        "per_class": classification_report(truth_all, pred_all, labels=CLASSES,
                                           zero_division=0, output_dict=True),
        "confusion_matrix": {
            "labels": CLASSES,
            "rows_are_truth": confusion_matrix(truth_all, pred_all,
                                               labels=CLASSES).tolist(),
        },
    }


def independence_note(rows: list[dict]) -> dict:
    """How much of the data is really independent.

    Areas a few kilometres apart share the same weather, so area-seasons are
    not independent samples. The correlation between area totals in the same
    season shows how far the effective sample size falls below the row count.
    """
    seasons = sorted({r["season"] for r in rows})
    areas = sorted({r["area"] for r in rows})
    table = {(r["area"], r["season"]): r["rain_total"] for r in rows}
    grid = np.array([[table.get((a, s), np.nan) for s in seasons] for a in areas],
                    dtype=float)
    ok = ~np.isnan(grid).any(axis=1)
    corr = np.corrcoef(grid[ok]) if ok.sum() > 1 else np.array([[1.0]])
    off = corr[np.triu_indices_from(corr, k=1)]
    mean_r = float(np.nanmean(off)) if off.size else float("nan")
    n_areas = int(ok.sum())
    # Effective number of independent areas, from the mean correlation.
    eff_areas = n_areas / (1 + (n_areas - 1) * mean_r) if mean_r == mean_r else float("nan")
    return {
        "rows": len(rows),
        "seasons": len(seasons),
        "areas": n_areas,
        "mean_correlation_between_areas": round(mean_r, 3),
        "effective_independent_areas": round(eff_areas, 2),
        "effective_sample_size": round(eff_areas * len(seasons), 1),
        "note": ("Area-seasons are not independent: neighbouring areas share "
                 "the same weather. Treat the effective sample size, not the "
                 "row count, as the basis for any claim of skill."),
    }


# ------------------------------------------------------------- final model
NAME = "seasonal_rain"


def fit_final(rows: list[dict]):
    """The model that goes into service, fitted on every season available.

    Its cut-offs come from the whole record, which is correct for making a
    forecast; the honest accuracy figures are the fold ones above.
    """
    from sklearn.ensemble import RandomForestClassifier

    low, high = terciles([r["rain_total"] for r in rows])
    y = [label_of(r["rain_total"], low, high) for r in rows]
    model = RandomForestClassifier(
        n_estimators=400, min_samples_leaf=3, random_state=0)
    model.fit(matrix(rows), y)
    bundle = {
        "model": model,
        "features": FEATURES,
        "classes": CLASSES,
        "tercile_low_mm": round(low, 1),
        "tercile_high_mm": round(high, 1),
        "reference_seasons": sorted({r["season"] for r in rows}),
    }
    return bundle, low, high


# -------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser(description="Train the seasonal rainfall classifier.")
    ap.add_argument("--report", help="write the evaluation report to this JSON file")
    ap.add_argument("--dry-run", action="store_true",
                    help="evaluate and report, but do not save the model")
    args = ap.parse_args()

    from app.database import SessionLocal

    db = SessionLocal()
    try:
        rows = build_rows(db)
        if len(rows) < 30:
            print(f"Only {len(rows)} complete area-seasons found. "
                  "Backfill more history before training.", file=sys.stderr)
            return 2

        report = {
            "model": NAME,
            "target": "November-April rainfall total, three classes",
            "classes": CLASSES,
            "predictors": FEATURES,
            "predictors_known_by": "31 October of the season being predicted",
            "data": independence_note(rows),
            "observation_period": {
                "first_season": min(r["season"] for r in rows),
                "last_season": max(r["season"] for r in rows),
            },
            "evaluation": leave_one_season_out(rows),
        }

        bundle, low, high = fit_final(rows)
        report["service_model"] = {
            "tercile_low_mm": bundle["tercile_low_mm"],
            "tercile_high_mm": bundle["tercile_high_mm"],
            "reference_seasons": bundle["reference_seasons"],
            "note": ("These cut-offs are fitted on the whole record and are "
                     "used for live forecasts. The accuracy figures under "
                     "'evaluation' come from folds with their own cut-offs."),
        }

        if args.dry_run:
            report["saved"] = False
        else:
            ev = report["evaluation"].get("model", {})
            report["version"] = store.save(
                db, NAME, bundle,
                train_rows=len(rows),
                test_rows=report["evaluation"].get("observations", 0),
                metrics=ev)
            report["saved"] = True

        text = json.dumps(report, indent=2, default=str)
        if args.report:
            with open(args.report, "w", encoding="utf8") as fh:
                fh.write(text)
            print(f"report written to {args.report}")
        print(text)
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
