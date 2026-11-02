"""Database browser for the administrator (read-only)."""
from datetime import date, datetime
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import String, Text, func, or_, select
from sqlalchemy.orm import Session

from .. import models  # noqa: F401 - registers every table on Base.metadata
from ..database import Base, get_db
from ..deps import get_current_admin

router = APIRouter(prefix="/api/admin/db", tags=["admin database"],
                   dependencies=[Depends(get_current_admin)])

HIDDEN = {"password_hash"}

# What each table is for, shown above it so the admin knows what they are reading.
DESCRIPTIONS = {
    "farmers": "Registered farmers and administrators",
    "advice_requests": "Every question asked, on the website, SMS or USSD",
    "advice_responses": "The advice given for each question, and the rules behind it",
    "weather": "Weather readings the advice was based on",
    "knowledge_items": "Tea farming knowledge in English and Chichewa",
    "sms_logs": "Every SMS received and sent",
    "ussd_sessions": "USSD dial-ins",
    "phone_profiles": "Area, language and alert choice saved per phone number",
    "harvest_records": "Harvest diary entries",
    "broadcasts": "SMS weather alerts sent by the administrator",
    "weather_history": "Daily weather per area since 2016 (Open-Meteo / ERA5), rain model training data",
    "soil_moisture": "Daily soil moisture per area from ERA5-Land",
    "nasa_power": "Daily rainfall, sunshine and soil wetness per area from NASA POWER",
    "chirps_monthly": "Monthly rainfall per area from CHIRPS",
    "rain_predictions": "Rain model predictions, checked against the rain that fell",
    "advice_decisions": "Advice model decisions and farmers' ratings",
    "model_runs": "Every training run of the models, with test results",
}


def _table(name: str):
    table = Base.metadata.tables.get(name)
    if table is None:
        raise HTTPException(status_code=404, detail="No such table")
    return table


def _value(value):
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (datetime, date)):
        return value.isoformat(sep=" ") if isinstance(value, datetime) else value.isoformat()
    return value


@router.get("/tables")
def tables(db: Session = Depends(get_db)):
    """Every table with its row count."""
    out = []
    for name in sorted(Base.metadata.tables):
        table = Base.metadata.tables[name]
        count = db.scalar(select(func.count()).select_from(table)) or 0
        out.append({"name": name, "rows": count, "description": DESCRIPTIONS.get(name, "")})
    return out


@router.get("/tables/{name}")
def rows(
    name: str,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=25, ge=5, le=100),
    q: str = Query(default="", max_length=100),
    db: Session = Depends(get_db),
):
    """One page of a table's rows, newest first, optionally filtered by a word."""
    table = _table(name)
    columns = [c for c in table.columns if c.name not in HIDDEN]

    query = select(*columns)
    count_query = select(func.count()).select_from(table)
    word = q.strip()
    if word:
        text_columns = [c for c in table.columns
                        if isinstance(c.type, (String, Text)) and c.name not in HIDDEN]
        if text_columns:
            condition = or_(*[c.ilike(f"%{word}%") for c in text_columns])
            query = query.where(condition)
            count_query = count_query.where(condition)

    primary = list(table.primary_key.columns)
    if primary:
        query = query.order_by(primary[0].desc())

    total = db.scalar(count_query) or 0
    result = db.execute(query.limit(size).offset((page - 1) * size)).all()
    return {
        "table": name,
        "description": DESCRIPTIONS.get(name, ""),
        "columns": [c.name for c in columns],
        "hidden": sorted(HIDDEN & {c.name for c in table.columns}),
        "rows": [[_value(v) for v in row] for row in result],
        "total": total,
        "page": page,
        "size": size,
    }
