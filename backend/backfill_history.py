# -*- coding: utf-8 -*-
"""Extend the weather record backwards and check what arrived.

Run as a one-off job, after taking a database backup. It only adds days
that are missing, so running it twice changes nothing.

    python backfill_history.py --from 2010-01-01 --check --report backfill.json

--check alone verifies what is already stored and downloads nothing.

Source: Open-Meteo historical archive (ERA5 reanalysis), queried per area
by latitude and longitude from app/data/locations.py, daily values in the
Africa/Blantyre time zone. The retrieval timestamp is recorded in the
report, since the archive revises its most recent days.
"""
from __future__ import annotations

import argparse
import asyncio
import json
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select


def verify(db, start: date, end: date) -> dict:
    """Coverage, gaps, missing values and duplicates in the stored history."""
    from app.data.locations import LOCATIONS
    from app.models import WeatherHistory

    rows = db.execute(
        select(WeatherHistory.location, WeatherHistory.day, WeatherHistory.rain_mm,
               WeatherHistory.tmax, WeatherHistory.tmin)
        .where(WeatherHistory.day >= start, WeatherHistory.day <= end)).all()

    days: dict[str, list[date]] = defaultdict(list)
    seen: dict[str, set[date]] = defaultdict(set)
    duplicates: dict[str, int] = defaultdict(int)
    blanks: dict[str, int] = defaultdict(int)
    for name, day, rain, tmax, tmin in rows:
        if day in seen[name]:
            duplicates[name] += 1
            continue
        seen[name].add(day)
        days[name].append(day)
        if rain is None or tmax is None or tmin is None:
            blanks[name] += 1

    expected = (end - start).days + 1
    areas = {}
    for name in sorted(LOCATIONS):
        got = sorted(days.get(name, []))
        gaps = []
        if got:
            have = set(got)
            run_start = None
            day = start
            while day <= end:
                if day not in have:
                    run_start = run_start or day
                elif run_start:
                    gaps.append([run_start.isoformat(), (day - timedelta(days=1)).isoformat()])
                    run_start = None
                day += timedelta(days=1)
            if run_start:
                gaps.append([run_start.isoformat(), end.isoformat()])
        areas[name] = {
            "days_stored": len(got),
            "days_expected": expected,
            "coverage": round(len(got) / expected, 4) if expected else 0,
            "first_day": got[0].isoformat() if got else None,
            "last_day": got[-1].isoformat() if got else None,
            "missing_runs": gaps[:20],
            "missing_runs_total": len(gaps),
            "rows_with_blank_values": blanks.get(name, 0),
            "duplicate_day_rows": duplicates.get(name, 0),
        }

    unknown = sorted({name for name, *_ in rows} - set(LOCATIONS))
    return {
        "range_checked": [start.isoformat(), end.isoformat()],
        "areas_in_locations_file": len(LOCATIONS),
        "areas_with_data": sum(1 for a in areas.values() if a["days_stored"]),
        "areas_in_database_not_in_locations_file": unknown,
        "total_rows": len(rows),
        "total_duplicate_day_rows": sum(duplicates.values()),
        "total_rows_with_blank_values": sum(blanks.values()),
        "per_area": areas,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Backfill and verify weather history.")
    ap.add_argument("--from", dest="start", default="2010-01-01",
                    help="first day to fetch (default 2010-01-01)")
    ap.add_argument("--to", dest="end", default=None,
                    help="last day to fetch (default: the day before the oldest stored day)")
    ap.add_argument("--check", action="store_true", help="also verify what is stored")
    ap.add_argument("--check-only", action="store_true", help="verify only, download nothing")
    ap.add_argument("--report", help="write the result to this JSON file")
    args = ap.parse_args()

    from app.database import SessionLocal
    from app.ml import history
    from app.models import WeatherHistory

    start = date.fromisoformat(args.start)
    db = SessionLocal()
    try:
        oldest = db.scalar(select(func.min(WeatherHistory.day)))
        end = (date.fromisoformat(args.end) if args.end
               else (oldest - timedelta(days=1) if oldest else date.today()))

        result = {
            "source": "Open-Meteo historical archive (ERA5 reanalysis)",
            "endpoint": history.ARCHIVE_URL,
            "timezone": "Africa/Blantyre",
            "fields": list(history.FIELDS.values()),
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "oldest_day_before_run": oldest.isoformat() if oldest else None,
            "requested_range": [start.isoformat(), end.isoformat()],
        }

        if args.check_only:
            result["rows_added"] = 0
        elif start > end:
            result["rows_added"] = 0
            result["note"] = "Nothing to do: the record already starts at or before this date."
        else:
            result["rows_added"] = asyncio.run(history.backfill(db, start, end))

        if args.check or args.check_only:
            newest = db.scalar(select(func.max(WeatherHistory.day))) or date.today()
            result["verification"] = verify(db, start, newest)

        text = json.dumps(result, indent=2, default=str)
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
