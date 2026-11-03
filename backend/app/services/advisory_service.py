"""One advisory request, the same for website, SMS and USSD."""
import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import (
    AdviceRequest, AdviceResponse, Channel, KnowledgeItem, Language, WeatherRecord,
)
from ..ml import advice_model, rain_model
from . import advisory_engine, llm_service, speech_service, weather_service
from .intent_model import classifier

log = logging.getLogger(__name__)


async def answer(
    db: Session,
    *,
    question: str,
    language: str,
    location: str,
    channel: str = "WEB",
    farmer_id: int | None = None,
    phone: str | None = None,
    max_sentences: int = 4,
    brief: bool = False,
    persist: bool = True,
) -> dict:
    """Produce advice for one question and record it."""
    topic, confidence, method = classifier.predict(question)

    weather = await weather_service.fetch_weather(location)
    summary = weather_service.summarise(weather, language)

    try:
        rain = rain_model.probability_for(db, location)
    except Exception:  # noqa: BLE001 - advice still works without the rain model
        log.exception("Rain model prediction failed")
        rain = None
    situation = advice_model.situation(db, location, weather, rain)
    decision = advice_model.decide(topic, situation)

    advice = advisory_engine.generate(
        topic, situation, decision, rain, confidence=confidence, method=method
    )
    raw_text = advice.body(language, brief=brief)

    open_answer = None
    if topic == "general" and llm_service.enabled():
        # Outside the model's topics: Gemini answers from the knowledge base.
        open_answer = await llm_service.answer_open(
            question,
            language,
            location=weather["location"],
            season=advisory_engine.season_label(advisory_engine.current_season(), "EN"),
            weather_summary=summary if not weather["offline"] else "",
            knowledge=_knowledge_text(db),
            max_sentences=max_sentences + 1,
        )
    if open_answer:
        text, source = open_answer, "gemini"
        advice.rules_fired.append("outside the model's topics: Gemini answered from the knowledge base")
    else:
        text, source = await llm_service.phrase(
            raw_text,
            language,
            weather_summary=summary if not weather["offline"] else "",
            question=question,
            max_sentences=max_sentences,
        )

    result = {
        "topic": topic,
        "confidence": round(confidence, 3),
        "classification_method": method,
        "urgency": advice.urgency,
        "advice": text,
        "advice_template": raw_text,
        "source": source,
        "reasoning": advice.reasoning(),
        "rules_fired": advice.rules_fired,
        "language": language,
        "location": weather["location"],
        "weather_summary": summary,
        "weather": weather,
        "season": advisory_engine.current_season(),
        "action": advice.action,
        "rain_prediction": rain,
        "model_version": decision["version"] if decision else None,
        "request_id": None,
    }

    if channel == "WEB":
        speech_service.prepare(text, language)

    if persist:
        result["request_id"] = _persist(
            db,
            question=question,
            language=language,
            channel=channel,
            farmer_id=farmer_id,
            phone=phone,
            weather=weather,
            result=result,
        )
        if decision:
            advice_model.record(db, result["request_id"], topic, decision, situation)
    return result


def _persist(db: Session, *, question, language, channel, farmer_id, phone,
             weather, result) -> int:
    request = AdviceRequest(
        farmer_id=farmer_id,
        phone=phone,
        question=question,
        language=Language(language),
        channel=Channel(channel),
        location=result["location"],
        topic=result["topic"],
    )
    db.add(request)
    db.flush()  # assigns request_id before the response references it

    db.add(AdviceResponse(
        request_id=request.request_id,
        advice=result["advice"],
        language=Language(language),
        source=result["source"],
        urgency=result["urgency"],
        reasoning=result["reasoning"],
        weather_summary=result["weather_summary"],
    ))

    # Keep the reading the advice was based on, so the admin can audit it.
    if not weather["offline"]:
        current = weather["current"]
        db.add(WeatherRecord(
            location=weather["location"],
            temperature=current["temperature"],
            rainfall_probability=current["rain_probability"],
            rainfall_mm=current["rain_today_mm"],
            humidity=current["humidity"],
            wind_kph=current["wind_kph"],
            condition=current["condition_en"],
        ))

    db.commit()
    return request.request_id


def _knowledge_text(db: Session) -> str:
    """The active knowledge base as plain English text, for grounding Gemini."""
    items = db.scalars(
        select(KnowledgeItem).where(KnowledgeItem.is_active.is_(True))
        .order_by(KnowledgeItem.topic)
    ).all()
    return "\n\n".join(f"{item.title_en}: {item.body_en}" for item in items)
