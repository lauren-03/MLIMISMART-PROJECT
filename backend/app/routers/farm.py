"""Farm tools: the tea calendar and the farmer's harvest diary."""
from collections import defaultdict
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..data.tea_calendar import month_entry
from ..database import get_db
from ..deps import get_current_farmer
from ..models import Farmer, HarvestRecord

router = APIRouter(prefix="/api", tags=["farm tools"])


# ------------------------------- calendar ---------------------------------
@router.get("/calendar")
def calendar(language: str = Query(default="EN", pattern="^(EN|NY)$")):
    """All twelve months, with the current month flagged."""
    return {
        "current_month": date.today().month,
        "months": [month_entry(m, language) for m in range(1, 13)],
    }


# ---------------------------- harvest diary -------------------------------
class HarvestIn(BaseModel):
    harvest_date: date
    kg: float = Field(gt=0, le=5000)
    price_per_kg: float | None = Field(default=None, ge=0, le=100000)
    notes: str | None = Field(default=None, max_length=255)

    @field_validator("harvest_date")
    @classmethod
    def not_in_future(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("The harvest date cannot be in the future")
        return value


def _row(record: HarvestRecord) -> dict:
    income = record.kg * record.price_per_kg if record.price_per_kg is not None else None
    return {
        "id": record.id,
        "harvest_date": record.harvest_date.isoformat(),
        "kg": record.kg,
        "price_per_kg": record.price_per_kg,
        "income": round(income, 2) if income is not None else None,
        "notes": record.notes,
    }


@router.get("/harvest")
def harvest(farmer: Farmer = Depends(get_current_farmer),
            db: Session = Depends(get_db)):
    """The diary, plus the totals and monthly series the page charts."""
    records = db.scalars(
        select(HarvestRecord).where(HarvestRecord.farmer_id == farmer.farmer_id)
        .order_by(HarvestRecord.harvest_date.desc(), HarvestRecord.id.desc())
    ).all()

    today = date.today()
    by_month: dict[str, dict] = defaultdict(lambda: {"kg": 0.0, "income": 0.0})
    total_kg = total_income = this_month_kg = 0.0
    priced_kg = 0.0
    for r in records:
        key = r.harvest_date.strftime("%Y-%m")
        by_month[key]["kg"] += r.kg
        total_kg += r.kg
        if r.price_per_kg is not None:
            by_month[key]["income"] += r.kg * r.price_per_kg
            total_income += r.kg * r.price_per_kg
            priced_kg += r.kg
        if r.harvest_date.year == today.year and r.harvest_date.month == today.month:
            this_month_kg += r.kg

    # The last twelve months, oldest first, including months with nothing
    # plucked -- a gap in the chart is information too.
    series = []
    year, month = today.year, today.month
    for _ in range(12):
        key = f"{year:04d}-{month:02d}"
        series.append({"month": key, "kg": round(by_month[key]["kg"], 1),
                       "income": round(by_month[key]["income"], 2)})
        month -= 1
        if month == 0:
            year, month = year - 1, 12
    series.reverse()

    last_price = next((r.price_per_kg for r in records if r.price_per_kg is not None), None)
    return {
        "records": [_row(r) for r in records[:100]],
        "summary": {
            "total_kg": round(total_kg, 1),
            "total_income": round(total_income, 2),
            "this_month_kg": round(this_month_kg, 1),
            "rounds": len(records),
            "average_price": round(total_income / priced_kg, 2) if priced_kg else None,
            "last_price": last_price,
            "kg_per_ha": round(total_kg / farmer.farm_size_ha, 1) if farmer.farm_size_ha else None,
        },
        "monthly": series,
    }


@router.post("/harvest", status_code=201)
def add_harvest(payload: HarvestIn,
                farmer: Farmer = Depends(get_current_farmer),
                db: Session = Depends(get_db)):
    record = HarvestRecord(farmer_id=farmer.farmer_id, **payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return _row(record)


@router.delete("/harvest/{record_id}", status_code=204)
def delete_harvest(record_id: int,
                   farmer: Farmer = Depends(get_current_farmer),
                   db: Session = Depends(get_db)):
    record = db.get(HarvestRecord, record_id)
    # A farmer can only remove their own entries; someone else's id is
    # reported as not found rather than forbidden, so ids cannot be probed.
    if not record or record.farmer_id != farmer.farmer_id:
        raise HTTPException(status_code=404, detail="Harvest entry not found")
    db.delete(record)
    db.commit()
