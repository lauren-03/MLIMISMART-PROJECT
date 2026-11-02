"""Advisory endpoints (Module 3: AI Advisory)."""
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_farmer
from ..models import AdviceRequest, AdviceResponse, Farmer
from ..schemas import AdviceAsk, AdviceOut, HistoryItem
from ..services import advisory_service
from ..ml import advice_model, learning
from ..services.intent_model import classifier

router = APIRouter(prefix="/api/advice", tags=["advisory"])


@router.post("/ask", response_model=AdviceOut)
async def ask(
    payload: AdviceAsk,
    farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    """Ask MlimiSmart a tea farming question."""
    language = (payload.language or farmer.language.value).upper()
    location = payload.location or farmer.location

    result = await advisory_service.answer(
        db,
        question=payload.question.strip(),
        language=language,
        location=location,
        channel="WEB",
        farmer_id=farmer.farmer_id,
        phone=farmer.phone,
    )
    return AdviceOut(**result)


@router.get("/daily", response_model=AdviceOut)
async def daily(
    farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    """The advice shown on the dashboard without the farmer asking anything.

    It is driven by the weather topic, so the farmer opens the app and
    immediately sees whether today's conditions need action. It is not stored
    in the advisory history, because the farmer did not ask a question.
    """
    result = await advisory_service.answer(
        db,
        question="what is the weather advice for my farm today",
        language=farmer.language.value,
        location=farmer.location,
        channel="WEB",
        farmer_id=farmer.farmer_id,
        max_sentences=3,
        persist=False,
    )
    return AdviceOut(**result)


@router.get("/history", response_model=list[HistoryItem])
def history(
    limit: int = Query(default=25, ge=1, le=100),
    farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    """The farmer's own advisory history, newest first."""
    rows = db.execute(
        select(AdviceRequest, AdviceResponse)
        .outerjoin(AdviceResponse, AdviceResponse.request_id == AdviceRequest.request_id)
        .where(AdviceRequest.farmer_id == farmer.farmer_id)
        .order_by(AdviceRequest.request_id.desc())
        .limit(limit)
    ).all()

    return [
        HistoryItem(
            request_id=request.request_id,
            question=request.question,
            topic=request.topic,
            language=request.language.value,
            channel=request.channel.value,
            location=request.location,
            created_at=request.created_at,
            advice=response.advice if response else None,
            urgency=response.urgency if response else None,
            source=response.source if response else None,
            reasoning=response.reasoning if response else None,
        )
        for request, response in rows
    ]


@router.get("/model")
def model_info():
    """How the classifier is configured, for the admin dashboard and write-up."""
    return classifier.info()


class Rating(BaseModel):
    helpful: bool


@router.post("/{request_id}/rate")
async def rate(
    request_id: int,
    payload: Rating,
    background: BackgroundTasks,
    farmer: Farmer = Depends(get_current_farmer),
    db: Session = Depends(get_db),
):
    """The farmer says whether the advice helped. The advice model learns from it."""
    request = db.get(AdviceRequest, request_id)
    if request is None or request.farmer_id != farmer.farmer_id:
        raise HTTPException(status_code=404, detail="Advice not found")
    row = advice_model.rate(db, request_id, payload.helpful)
    if row is None:
        raise HTTPException(status_code=409, detail="This advice was not made by the advice model")
    background.add_task(learning.after_rating)
    return {"request_id": request_id, "helpful": row.helpful,
            "ratings_since_training": advice_model.ratings_since_last_training(db),
            "retrain_every": advice_model.RETRAIN_EVERY}
