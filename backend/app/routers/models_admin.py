"""Admin view of the trained models: results, training history, retraining."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_admin
from ..ml import advice_model, learning, rain_model, store
from ..models import AdviceDecision, WeatherHistory

router = APIRouter(prefix="/api/admin/models", tags=["admin models"],
                   dependencies=[Depends(get_current_admin)])


@router.get("")
def overview(db: Session = Depends(get_db)):
    days = db.scalar(select(func.count()).select_from(WeatherHistory)) or 0
    first = db.scalar(select(func.min(WeatherHistory.day)))
    last = db.scalar(select(func.max(WeatherHistory.day)))
    rated = db.scalars(select(AdviceDecision.helpful).where(AdviceDecision.helpful.is_not(None))).all()
    decisions = db.scalar(select(func.count()).select_from(AdviceDecision)) or 0
    return {
        "rain": {
            "runs": store.runs(db, rain_model.NAME),
            "live": rain_model.live_accuracy(db),
            "history_days": days,
            "history_from": first, "history_to": last,
        },
        "advice": {
            "runs": store.runs(db, advice_model.NAME),
            "decisions": decisions,
            "ratings": len(rated),
            "helpful": sum(1 for h in rated if h),
            "since_training": advice_model.ratings_since_last_training(db),
            "retrain_every": advice_model.RETRAIN_EVERY,
        },
    }


@router.post("/{name}/retrain")
async def retrain(name: str):
    if name not in (rain_model.NAME, advice_model.NAME):
        raise HTTPException(status_code=404, detail="Unknown model")
    try:
        return await learning.retrain(name)
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/update")
async def update_now():
    """Run the daily learning cycle now: new weather, checks, retraining."""
    await learning.daily_cycle()
    return {"status": "done"}
