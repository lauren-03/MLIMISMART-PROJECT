"""Admin endpoints (Module 6: Admin dashboard)."""
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from ..data.locations import DISTRICTS, LOCATIONS, areas_in, match
from ..database import active_database_url, get_db
from ..deps import get_current_admin
from ..models import (
    AdviceRequest, AdviceResponse, Broadcast, Channel, Farmer, HarvestRecord,
    KnowledgeItem, PhoneProfile, Role, SmsLog, UssdSession,
    WeatherRecord,
)
from ..schemas import FarmerOut, HistoryItem, KnowledgeIn, KnowledgeOut
from ..services import llm_service, sms_service, ussd_service, weather_service
from ..services.intent_model import classifier

router = APIRouter(prefix="/api/admin", tags=["admin"],
                   dependencies=[Depends(get_current_admin)])


@router.get("/stats")
def stats(db: Session = Depends(get_db)):
    """The headline figures for the admin dashboard."""
    total_requests = db.scalar(select(func.count()).select_from(AdviceRequest)) or 0
    sms_requests = db.scalar(
        select(func.count()).select_from(AdviceRequest)
        .where(AdviceRequest.channel == Channel.SMS)
    ) or 0
    ussd_requests = db.scalar(
        select(func.count()).select_from(AdviceRequest)
        .where(AdviceRequest.channel == Channel.USSD)
    ) or 0
    web_requests = total_requests - sms_requests - ussd_requests

    topic_rows = db.execute(
        select(AdviceRequest.topic, func.count().label("n"))
        .group_by(AdviceRequest.topic)
        .order_by(desc("n"))
    ).all()

    language_rows = db.execute(
        select(Farmer.language, func.count().label("n")).group_by(Farmer.language)
    ).all()

    location_rows = db.execute(
        select(Farmer.location, func.count().label("n"))
        .where(Farmer.role == Role.FARMER)
        .group_by(Farmer.location)
        .order_by(desc("n"))
    ).all()

    district_counts = {district: 0 for district in DISTRICTS}
    for location, n in location_rows:
        district = LOCATIONS.get(location, {}).get("district")
        if district:
            district_counts[district] += n

    return {
        "farmers_by_district": [
            {"district": d, "count": n} for d, n in district_counts.items()
        ],
        "harvest_entries": db.scalar(select(func.count()).select_from(HarvestRecord)) or 0,
        "harvest_kg": round(db.scalar(select(func.sum(HarvestRecord.kg))) or 0, 1),
        "alert_subscribers": db.scalar(
            select(func.count()).select_from(PhoneProfile)
            .where(PhoneProfile.alerts_enabled.is_(True))
        ) or 0,
        "broadcasts_sent": db.scalar(select(func.count()).select_from(Broadcast)) or 0,
        "farmers": db.scalar(
            select(func.count()).select_from(Farmer).where(Farmer.role == Role.FARMER)
        ) or 0,
        "advice_requests": total_requests,
        "sms_requests": sms_requests,
        "ussd_requests": ussd_requests,
        "web_requests": web_requests,
        "ussd_sessions": db.scalar(select(func.count()).select_from(UssdSession)) or 0,
        "sms_messages_logged": db.scalar(select(func.count()).select_from(SmsLog)) or 0,
        "knowledge_items": db.scalar(select(func.count()).select_from(KnowledgeItem)) or 0,
        "weather_readings": db.scalar(select(func.count()).select_from(WeatherRecord)) or 0,
        "most_asked_topics": [
            {"topic": topic or "unknown", "count": n} for topic, n in topic_rows
        ],
        "farmers_by_language": [
            {"language": getattr(lang, "value", lang), "count": n}
            for lang, n in language_rows
        ],
        "farmers_by_location": [
            {"location": location, "count": n} for location, n in location_rows
        ],
    }


@router.get("/system")
def system_status():
    """What the system is currently wired to. Useful for the demonstration."""
    database = active_database_url
    if database.startswith("mysql"):
        # host:port/schema, without the credentials.
        target = database.split("@")[-1]
    else:
        target = Path(database.replace("sqlite:///", "")).name
    return {
        "database": "MySQL" if database.startswith("mysql") else "SQLite (fallback)",
        "database_target": target,
        "weather_provider": "Open-Meteo (no API key required)",
        "ai": llm_service.status(),
        "classifier": classifier.info(),
        "sms": sms_service.status(),
        "ussd": ussd_service.status(),
    }


@router.get("/farmers", response_model=list[FarmerOut])
def farmers(
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    rows = db.scalars(
        select(Farmer).order_by(Farmer.farmer_id.desc()).limit(limit)
    ).all()
    return [FarmerOut.model_validate(row) for row in rows]


@router.get("/requests", response_model=list[HistoryItem])
def requests(
    limit: int = Query(default=50, ge=1, le=200),
    channel: str | None = Query(default=None, pattern="^(WEB|SMS|USSD)$"),
    db: Session = Depends(get_db),
):
    """Every advice request across both channels."""
    query = (
        select(AdviceRequest, AdviceResponse)
        .outerjoin(AdviceResponse, AdviceResponse.request_id == AdviceRequest.request_id)
        .order_by(AdviceRequest.request_id.desc())
        .limit(limit)
    )
    if channel:
        query = query.where(AdviceRequest.channel == Channel(channel))

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
        for request, response in db.execute(query).all()
    ]


@router.get("/sms-logs")
def sms_logs(limit: int = Query(default=50, ge=1, le=200),
             db: Session = Depends(get_db)):
    rows = db.scalars(
        select(SmsLog).order_by(SmsLog.id.desc()).limit(limit)
    ).all()
    return [
        {
            "id": row.id, "phone": row.phone, "direction": row.direction,
            "message": row.message, "gateway": row.gateway,
            "status": row.status, "created_at": row.created_at,
        }
        for row in rows
    ]


@router.get("/weather-log")
def weather_log(limit: int = Query(default=50, ge=1, le=200),
                db: Session = Depends(get_db)):
    """Weather readings the advisory engine acted on."""
    rows = db.scalars(
        select(WeatherRecord).order_by(WeatherRecord.id.desc()).limit(limit)
    ).all()
    return [
        {
            "id": row.id, "location": row.location,
            "temperature": row.temperature,
            "rainfall_probability": row.rainfall_probability,
            "rainfall_mm": row.rainfall_mm, "humidity": row.humidity,
            "wind_kph": row.wind_kph, "condition": row.condition,
            "recorded_at": row.recorded_at,
        }
        for row in rows
    ]


# ---------------------------- knowledge base ------------------------------
@router.get("/knowledge", response_model=list[KnowledgeOut])
def list_knowledge(db: Session = Depends(get_db)):
    rows = db.scalars(select(KnowledgeItem).order_by(KnowledgeItem.topic)).all()
    return [KnowledgeOut.model_validate(row) for row in rows]


@router.post("/knowledge", response_model=KnowledgeOut, status_code=201)
def add_knowledge(payload: KnowledgeIn, db: Session = Depends(get_db)):
    item = KnowledgeItem(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return KnowledgeOut.model_validate(item)


@router.put("/knowledge/{item_id}", response_model=KnowledgeOut)
def update_knowledge(item_id: int, payload: KnowledgeIn,
                     db: Session = Depends(get_db)):
    item = db.get(KnowledgeItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Knowledge item not found")
    for key, value in payload.model_dump().items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return KnowledgeOut.model_validate(item)


@router.delete("/knowledge/{item_id}", status_code=204)
def delete_knowledge(item_id: int, db: Session = Depends(get_db)):
    item = db.get(KnowledgeItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Knowledge item not found")
    db.delete(item)
    db.commit()


@router.get("/ussd-sessions")
def ussd_sessions(limit: int = Query(default=50, ge=1, le=200),
                  db: Session = Depends(get_db)):
    """USSD dial-in sessions, newest first."""
    rows = db.scalars(
        select(UssdSession).order_by(UssdSession.id.desc()).limit(limit)
    ).all()
    return [
        {
            "id": row.id,
            "session_id": row.session_id,
            "phone": row.phone,
            "service_code": row.service_code,
            "language": row.language.value,
            "last_input": row.last_input,
            "topic": row.pending_topic,
            "screens_served": row.screens_served,
            "completed": row.completed,
            "gateway": row.gateway,
            "created_at": row.created_at,
        }
        for row in rows
    ]


# ------------------------------- broadcasts --------------------------------
class BroadcastIn(BaseModel):
    title: str = Field(min_length=2, max_length=120)
    message_en: str = Field(min_length=5, max_length=459)
    message_ny: str = Field(min_length=5, max_length=459)
    # Leave both empty to send to everyone; an area narrows a district.
    district: str | None = None
    location: str | None = None


def _target_areas(district: str | None, location: str | None) -> tuple[list[str], str | None, str | None]:
    if location:
        name = match(location)
        if not name:
            raise HTTPException(status_code=422, detail=f"Unknown area: {location}")
        return [name], LOCATIONS[name]["district"], name
    if district:
        if district not in DISTRICTS:
            raise HTTPException(status_code=422, detail=f"Unknown district: {district}")
        return areas_in(district), district, None
    return list(LOCATIONS), None, None


@router.get("/broadcast/suggest")
async def suggest_broadcast(location: str = Query(default="Thyolo")):
    """Draft an alert from the live forecast, in both languages, for editing."""
    weather = await weather_service.fetch_weather(location)
    found_en = weather_service.alerts(weather, "EN")
    found_ny = weather_service.alerts(weather, "NY")
    if not found_en:
        return {"location": weather["location"], "has_alert": False,
                "title": f"Weather update - {weather['location']}",
                "message_en": f"MlimiSmart {weather['location']}: no weather warnings for the next 3 days. "
                              f"{weather_service.summarise(weather, 'EN')}.",
                "message_ny": f"MlimiSmart {weather['location']}: palibe chenjezo la nyengo masiku 3 akubwerawa. "
                              f"{weather_service.summarise(weather, 'NY')}."}
    first_en, first_ny = found_en[0], found_ny[0]
    return {
        "location": weather["location"], "has_alert": True,
        "title": f"{first_en['title']} - {weather['location']}",
        "message_en": f"MlimiSmart alert, {weather['location']}: {first_en['title']}. {first_en['text']}",
        "message_ny": f"Chenjezo la MlimiSmart, {weather['location']}: {first_ny['title']}. {first_ny['text']}",
    }


@router.post("/broadcast", status_code=201)
async def send_broadcast(payload: BroadcastIn,
                         db: Session = Depends(get_db),
                         admin: Farmer = Depends(get_current_admin)):
    """Send a notice by SMS to every farmer and alert subscriber in the target.

    Each person gets it in their own language. Registered farmers in the area
    always receive it; unregistered numbers receive it only if they turned
    alerts on by SMS or USSD.
    """
    areas, district, location = _target_areas(payload.district, payload.location)

    recipients: dict[str, str] = {}  # phone tail -> language
    farmers = db.scalars(
        select(Farmer).where(Farmer.role == Role.FARMER, Farmer.is_active.is_(True),
                             Farmer.location.in_(areas))
    ).all()
    for farmer in farmers:
        recipients[farmer.phone[-9:]] = farmer.language.value
    subscribers = db.scalars(
        select(PhoneProfile).where(PhoneProfile.alerts_enabled.is_(True),
                                   PhoneProfile.location.in_(areas))
    ).all()
    for profile in subscribers:
        recipients.setdefault(profile.phone[-9:],
                              profile.language.value if profile.language else "NY")

    sent = failed = 0
    for phone, language in recipients.items():
        message = payload.message_ny if language == "NY" else payload.message_en
        result = await sms_service.send_sms(db, "0" + phone, message,
                                            limit=sms_service.LONG_SMS_LIMIT)
        if result["status"] == "ok":
            sent += 1
        else:
            failed += 1

    record = Broadcast(title=payload.title, message_en=payload.message_en,
                       message_ny=payload.message_ny, district=district,
                       location=location, recipients=sent, created_by=admin.farmer_id)
    db.add(record)
    db.commit()
    return {"id": record.id, "recipients": len(recipients), "sent": sent,
            "failed": failed, "gateway": sms_service.status()["mode"],
            "target": location or district or "All areas"}


@router.get("/broadcasts")
def broadcasts(db: Session = Depends(get_db)):
    rows = db.scalars(select(Broadcast).order_by(Broadcast.id.desc()).limit(30)).all()
    return [
        {"id": r.id, "title": r.title, "message_en": r.message_en,
         "message_ny": r.message_ny,
         "target": r.location or r.district or "All areas",
         "recipients": r.recipients, "created_at": r.created_at}
        for r in rows
    ]
