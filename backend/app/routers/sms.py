"""SMS endpoints (Module 4: SMS advisory)."""
import logging
from datetime import date

from fastapi import APIRouter, Depends, Form, Request
from sqlalchemy.orm import Session

from ..data.knowledge_base import msg
from ..data.locations import DISTRICTS, LOCATIONS, areas_in, match
from ..data.tea_calendar import month_text
from ..database import get_db
from ..schemas import SmsIn, SmsOut
from ..services import advisory_service, profiles, sms_service, weather_service

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/sms", tags=["sms"])


async def _handle(db: Session, phone: str, text: str) -> dict:
    """Shared handling for an inbound SMS, whatever the source."""
    sms_service.log_incoming(db, phone, text)

    farmer = profiles.find_farmer(db, phone)
    saved_language = profiles.language_for(db, phone, farmer)
    language = saved_language.value if saved_language else (
        sms_service.detect_language(text) or "NY"
    )
    location = profiles.location_for(db, phone, farmer)

    command = sms_service.parse_command(text)

    def reply(message: str, topic: str = "general", lang: str | None = None,
              long: bool = False) -> dict:
        return {"reply": message, "topic": topic, "language": lang or language,
                "limit": sms_service.LONG_SMS_LIMIT if long else sms_service.SMS_LIMIT}

    if command["command"] == "help":
        return reply(msg("sms_help", language))

    if command["command"] == "language":
        language = command["value"]
        profiles.set_language(db, phone, language, farmer)
        db.commit()
        key = "language_set_en" if language == "EN" else "language_set_ny"
        return reply(msg(key, language))

    if command["command"] == "location":
        name = match(command["value"])
        if not name:
            return reply(_areas_text(language, unknown=command["value"]), long=True)
        profiles.set_location(db, phone, name, farmer)
        db.commit()
        district = LOCATIONS[name]["district"]
        return reply(
            f"MlimiSmart area set to {name} ({district}). Advice and weather will now be for {name}."
            if language == "EN" else
            f"Dera lanu la MlimiSmart tsopano ndi {name} ({district}). Uphungu ndi nyengo zikhala za {name}."
        )

    if command["command"] == "areas":
        return reply(_areas_text(language), long=True)

    if command["command"] == "calendar":
        return reply(month_text(date.today().month, language), "calendar", long=True)

    if command["command"] == "alerts":
        profiles.set_alerts(db, phone, command["value"])
        db.commit()
        if command["value"]:
            text_out = (f"Weather alerts ON for {location}. Send ALERTS OFF to stop."
                        if language == "EN" else
                        f"Machenjezo a nyengo ayatsidwa a {location}. Tumizani CHENJEZO AYI kuti asiye.")
        else:
            text_out = ("Weather alerts OFF. Send ALERTS ON to start again."
                        if language == "EN" else
                        "Machenjezo a nyengo azimitsidwa. Tumizani CHENJEZO INDE kuti ayambirenso.")
        return reply(text_out)

    if command["command"] == "alerts_now":
        weather = await weather_service.fetch_weather(location)
        found = weather_service.alerts(weather, language)
        if not found:
            return reply(f"{location}: no weather warnings for the next 3 days."
                         if language == "EN" else
                         f"{location}: palibe chenjezo la nyengo masiku 3 akubwerawa.", "weather")
        return reply(f"{location}: " + " ".join(f"{a['title']}. {a['text']}" for a in found[:2]),
                     "weather")

    # An ordinary question goes through the full advisory pipeline. Advice is
    # kept short because it has to fit in an SMS.
    result = await advisory_service.answer(
        db,
        question=command["value"],
        language=language,
        location=location,
        channel="SMS",
        farmer_id=farmer.farmer_id if farmer else None,
        phone=phone,
        max_sentences=2,
        brief=True,
    )
    return reply(result["advice"], result["topic"])


def _areas_text(language: str, unknown: str | None = None) -> str:
    """The areas MlimiSmart covers, short enough for two SMS parts."""
    lines = []
    if unknown:
        lines.append(f"'{unknown}' is not on our list." if language == "EN"
                     else f"'{unknown}' sili pa mndandanda wathu.")
    for district in DISTRICTS:
        lines.append(f"{district}: " + ", ".join(areas_in(district)))
    lines.append("Send AREA and the name, e.g. AREA Luchenza." if language == "EN"
                 else "Tumizani DERA ndi dzina, mwachitsanzo DERA Luchenza.")
    return " ".join(lines)


@router.post("/simulate", response_model=SmsOut)
async def simulate(payload: SmsIn, db: Session = Depends(get_db)):
    """Demonstrate the SMS channel without a gateway account."""
    outcome = await _handle(db, payload.phone, payload.text)
    sent = await sms_service.send_sms(db, payload.phone, outcome["reply"],
                                     limit=outcome["limit"])
    return SmsOut(
        phone=payload.phone,
        incoming=payload.text,
        reply=sent["message"],
        topic=outcome["topic"],
        gateway=sent["gateway"],
        language=outcome["language"],
        characters=len(sent["message"]),
    )


@router.post("/incoming")
async def incoming(
    request: Request,
    db: Session = Depends(get_db),
    to: str | None = Form(default=None),
    text: str | None = Form(default=None),
):
    """Africa's Talking inbound SMS webhook.

    Africa's Talking posts form-encoded fields named `from`, `to`, `text`,
    `date` and `id`. `from` is a Python keyword, so it is read from the form
    directly rather than declared as a parameter.
    """
    form = await request.form()
    sender = str(form.get("from") or "")
    body = str(text or form.get("text") or "")

    if not sender or not body:
        log.warning("Inbound SMS webhook called without from/text")
        return {"status": "ignored"}

    outcome = await _handle(db, sender, body)
    await sms_service.send_sms(db, sender, outcome["reply"], limit=outcome["limit"])
    # Africa's Talking only needs a 200; the reply goes out as its own message.
    return {"status": "ok"}


@router.get("/status")
def status():
    """Which SMS mode is active, shown on the simulator screen."""
    return sms_service.status()
