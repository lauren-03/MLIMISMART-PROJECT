"""Daily weather history for every area, from the Open-Meteo archive."""
import logging
from collections import defaultdict
from datetime import date, timedelta

import httpx
from sqlalchemy import func, insert, select
from sqlalchemy.orm import Session

from ..data.locations import LOCATIONS
from ..models import WeatherHistory

log = logging.getLogger(__name__)

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
# Earliest day fetched for an area that has no stored history at all.
# The record was extended back to 2010 by backfill_history.py; a newly
# added area is downloaded from the same date so all areas match.
FIRST_DAY = date(2010, 1, 1)
FIELDS = {
    "precipitation_sum": "rain_mm",
    "temperature_2m_max": "tmax",
    "temperature_2m_min": "tmin",
    "relative_humidity_2m_mean": "humidity",
    "wind_speed_10m_max": "wind_kph",
    "pressure_msl_mean": "pressure",
    "cloud_cover_mean": "cloud",
}


def latest_per_area(db: Session) -> dict[str, date]:
    rows = db.execute(select(WeatherHistory.location, func.max(WeatherHistory.day))
                      .group_by(WeatherHistory.location)).all()
    return {name: day for name, day in rows}


async def update(db: Session) -> int:
    """Download and store the days not yet in the database. Returns rows added.

    Yesterday and today are always fetched again, because the archive keeps
    refining the most recent days.
    """
    recent_start = date.today() - timedelta(days=1)
    # Treat yesterday and today as not stored yet. The old rows are only
    # deleted once the new ones have downloaded, so a failed download loses nothing.
    keep_until = recent_start - timedelta(days=1)
    latest = {name: min(day, keep_until) for name, day in latest_per_area(db).items()}
    start = min((latest.get(name, FIRST_DAY - timedelta(days=1)) for name in LOCATIONS),
                default=FIRST_DAY - timedelta(days=1)) + timedelta(days=1)
    end = date.today()
    if start > end:
        return 0

    names = list(LOCATIONS)
    params = {
        "latitude": ",".join(str(LOCATIONS[n]["lat"]) for n in names),
        "longitude": ",".join(str(LOCATIONS[n]["lon"]) for n in names),
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "daily": ",".join(FIELDS),
        "timezone": "Africa/Blantyre",
    }
    async with httpx.AsyncClient(timeout=180.0) as client:
        response = await client.get(ARCHIVE_URL, params=params)
        response.raise_for_status()
        payload = response.json()
    results = payload if isinstance(payload, list) else [payload]

    rows = []
    for name, result in zip(names, results):
        daily = result.get("daily") or {}
        since = latest.get(name)
        for i, day_text in enumerate(daily.get("time", [])):
            day = date.fromisoformat(day_text)
            if since and day <= since:
                continue
            values = {column: (daily.get(field) or [None] * (i + 1))[i]
                      for field, column in FIELDS.items()}
            if values["rain_mm"] is None:
                continue
            rows.append({"location": name, "day": day, **values})
    if rows:
        first_new: dict[str, date] = {}
        for r in rows:
            first_new[r["location"]] = min(r["day"], first_new.get(r["location"], r["day"]))
        for name, day in first_new.items():
            db.query(WeatherHistory).filter(WeatherHistory.location == name,
                                            WeatherHistory.day >= day).delete()
        db.execute(insert(WeatherHistory), rows)
    db.commit()
    added = len(rows)
    log.info("Weather history: %d new days stored (%s to %s)", added, start, end)
    return added


def series(db: Session) -> dict[str, list[WeatherHistory]]:
    """All stored days, per area, oldest first."""
    grouped: dict[str, list[WeatherHistory]] = defaultdict(list)
    for row in db.scalars(select(WeatherHistory).order_by(WeatherHistory.location,
                                                          WeatherHistory.day)):
        grouped[row.location].append(row)
    return grouped


def recent(db: Session, location: str, days: int = 7) -> list[WeatherHistory]:
    rows = db.scalars(select(WeatherHistory).where(WeatherHistory.location == location)
                      .order_by(WeatherHistory.day.desc()).limit(days)).all()
    return list(reversed(rows))


async def _fetch_range(start: date, end: date) -> dict[str, dict[date, dict]]:
    """Archive rows for every area between two dates, keyed by area and day."""
    names = list(LOCATIONS)
    params = {
        "latitude": ",".join(str(LOCATIONS[n]["lat"]) for n in names),
        "longitude": ",".join(str(LOCATIONS[n]["lon"]) for n in names),
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "daily": ",".join(FIELDS),
        "timezone": "Africa/Blantyre",
    }
    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.get(ARCHIVE_URL, params=params)
        response.raise_for_status()
        payload = response.json()
    results = payload if isinstance(payload, list) else [payload]

    out: dict[str, dict[date, dict]] = {}
    for name, result in zip(names, results):
        daily = result.get("daily") or {}
        days: dict[date, dict] = {}
        for i, day_text in enumerate(daily.get("time", [])):
            values = {column: (daily.get(field) or [None] * (i + 1))[i]
                      for field, column in FIELDS.items()}
            if values["rain_mm"] is None:
                continue
            days[date.fromisoformat(day_text)] = values
        out[name] = days
    return out


async def backfill(db: Session, start: date, end: date, *, year_chunk: bool = True) -> int:
    """Add older days that are missing, without touching what is already stored.

    Unlike update(), this takes an explicit range and never deletes. Days
    already in the database are skipped, so running it twice is harmless.
    Used for the one-off extension of the record back to 2010.
    """
    existing: dict[str, set[date]] = defaultdict(set)
    for name, day in db.execute(
            select(WeatherHistory.location, WeatherHistory.day)
            .where(WeatherHistory.day >= start, WeatherHistory.day <= end)).all():
        existing[name].add(day)

    added = 0
    spans = []
    if year_chunk:
        year = start.year
        while year <= end.year:
            spans.append((max(start, date(year, 1, 1)), min(end, date(year, 12, 31))))
            year += 1
    else:
        spans.append((start, end))

    for span_start, span_end in spans:
        fetched = await _fetch_range(span_start, span_end)
        rows = [{"location": name, "day": day, **values}
                for name, days in fetched.items()
                for day, values in sorted(days.items())
                if day not in existing[name]]
        if rows:
            db.execute(insert(WeatherHistory), rows)
            db.commit()
            for r in rows:
                existing[r["location"]].add(r["day"])
            added += len(rows)
        log.info("Backfill %s to %s: %d rows stored", span_start, span_end, len(rows))
    return added
