# -*- coding: utf-8 -*-
"""USSD menu engine (Module 7"""
import logging
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..data.locations import DISTRICTS, LOCATIONS, areas_in
from ..data.tea_calendar import month_text
from ..models import Farmer, Language, UssdSession
from . import advisory_service, profiles

log = logging.getLogger(__name__)

# A USSD screen is limited to 182 characters by the protocol. The body is kept
# shorter than that to leave room for the navigation footer underneath it.
SCREEN_LIMIT = 182
BODY_LIMIT = 130

# The service code a farmer dials. This is assigned by the gateway or the
# mobile operator; *384*211# is the shape Africa's Talking issues on its
# sandbox. The short code in the proposal (*211#) would be the production
# equivalent applied for through Airtel or TNM.
SERVICE_CODE = "*384*36247#"


# ---------------------------------------------------------------------------
# Screen text, in both languages. Kept together so each screen can be checked
# against the 182-character limit at a glance.
# ---------------------------------------------------------------------------
SCREENS = {
    "main": {
        "EN": ("MLIMISMART\n"
               "1. Weather\n"
               "2. Farming Advice\n"
               "3. Tea Advice\n"
               "4. Ask a question\n"
               "5. Language\n"
               "6. My Area\n"
               "7. This Month's Tasks\n"
               "8. Weather Alerts\n"
               "9. Exit"),
        "NY": ("MLIMISMART\n"
               "1. Nyengo\n"
               "2. Uphungu wa ulimi\n"
               "3. Uphungu wa tiyi\n"
               "4. Funsani funso\n"
               "5. Chilankhulo\n"
               "6. Dera langa\n"
               "7. Ntchito za mwezi uno\n"
               "8. Machenjezo a nyengo\n"
               "9. Tulukani"),
    },
    "crop": {
        "EN": ("Choose your crop:\n"
               "1. Tea\n"
               "2. Other\n"
               "3. Back"),
        "NY": ("Sankhani mbewu yanu:\n"
               "1. Tiyi\n"
               "2. Zina\n"
               "3. Bwererani"),
    },
    "topics": {
        "EN": ("TEA ADVICE\n"
               "1. Fertilizer\n"
               "2. Plucking\n"
               "3. Pruning\n"
               "4. Pests\n"
               "5. Harvesting\n"
               "0. Back"),
        "NY": ("UPHUNGU WA TIYI\n"
               "1. Fetereza\n"
               "2. Kuthyola\n"
               "3. Kutema\n"
               "4. Tizilombo\n"
               "5. Kokolola\n"
               "0. Bwererani"),
    },
    "ask": {
        "EN": "Type your question:",
        "NY": "Lembani funso lanu:",
    },
    "language": {
        "EN": ("Choose language:\n"
               "1. English\n"
               "2. Chichewa"),
        "NY": ("Sankhani chilankhulo:\n"
               "1. Chingerezi\n"
               "2. Chichewa"),
    },
    "other_crop": {
        "EN": ("MlimiSmart currently advises on tea only. Advice for other "
               "crops is not yet available."),
        "NY": ("MlimiSmart pakadali pano amapereka uphungu wa tiyi wokha. "
               "Uphungu wa mbewu zina sulipo pano."),
    },
    "exit": {
        "EN": "Thank you for using MlimiSmart.",
        "NY": "Zikomo kwambiri pogwiritsa ntchito MlimiSmart.",
    },
    "invalid": {
        "EN": "Invalid choice. Please dial again.",
        "NY": "Sankho lolakwika. Yesaninso kuyimba.",
    },
    "no_question": {
        "EN": "No question received. Please dial again.",
        "NY": "Palibe funso lomwe lalandiridwa. Yesaninso kuyimba.",
    },
    "language_set_en": {
        "EN": "Your language is now English.",
        "NY": "Your language is now English.",
    },
    "language_set_ny": {
        "EN": "Chilankhulo chanu tsopano ndi Chichewa.",
        "NY": "Chilankhulo chanu tsopano ndi Chichewa.",
    },
    "district": {
        "EN": ("Choose your district:\n"
               "1. Thyolo\n"
               "2. Mulanje\n"
               "0. Back"),
        "NY": ("Sankhani boma lanu:\n"
               "1. Thyolo\n"
               "2. Mulanje\n"
               "0. Bwererani"),
    },
    "alerts_on": {
        "EN": "Weather alerts are ON. You will get an SMS when heavy rain, heat or a dry spell is coming.",
        "NY": "Machenjezo a nyengo ayatsidwa. Mudzalandira SMS mvula yamphamvu, kutentha kapena chilala chikabwera.",
    },
    "alerts_off": {
        "EN": "Weather alerts are OFF. Dial again and choose 8 to turn them on.",
        "NY": "Machenjezo a nyengo azimitsidwa. Imbaninso ndipo sankhani 8 kuti muwayatse.",
    },
    "not_registered": {
        # The choice is remembered against the phone number for future calls,
        # so this says "saved for this number" rather than claiming a profile
        # was updated.
        "EN": "Saved for this number. Register to use the website too.",
        "NY": "Zasungidwa pa nambala iyi. Lembetsani kuti mugwiritse webusaiti.",
    },
}

FOOTERS = {
    "more_back": {
        "EN": "1. More advice\n0. Back",
        "NY": "1. Zambiri\n0. Bwererani",
    },
    "back": {
        "EN": "0. Back",
        "NY": "0. Bwererani",
    },
    "alerts_menu": {
        "EN": "1. Alerts ON\n2. Alerts OFF\n0. Back",
        "NY": "1. Yatsani\n2. Zimitsani\n0. Bwererani",
    },
    "forecast_back": {
        "EN": "1. 5-day forecast\n0. Back",
        "NY": "1. Masiku 5 akubwera\n0. Bwererani",
    },
}

# Menu option -> advisory topic, for the "Tea Advice" branch.
TOPIC_BY_OPTION = {
    "1": "fertilizer",
    "2": "plucking",
    "3": "pruning",
    "4": "pest_disease",
    "5": "harvest",
}


def screen(key: str, language: str) -> str:
    entry = SCREENS[key]
    return entry.get(language, entry["EN"])


def footer(key: str, language: str) -> str:
    entry = FOOTERS[key]
    return entry.get(language, entry["EN"])


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------
def paginate(text: str, limit: int = BODY_LIMIT) -> list[str]:
    """Split advice into USSD-sized pages, breaking on word boundaries.

    Breaking mid-word on a feature phone screen is the difference between
    advice a farmer can act on and advice they have to guess at, so pages are
    split on spaces and never on characters.
    """
    words = " ".join((text or "").split()).split(" ")
    pages: list[str] = []
    current = ""

    for word in words:
        # A single word longer than the limit would loop forever; hard-split it.
        while len(word) > limit:
            if current:
                pages.append(current)
                current = ""
            pages.append(word[:limit])
            word = word[limit:]
        candidate = f"{current} {word}".strip()
        if len(candidate) <= limit:
            current = candidate
        else:
            if current:
                pages.append(current)
            current = word

    if current:
        pages.append(current)
    return pages or [""]


def render(body: str, language: str, *, footer_key: str | None = None,
           end: bool = False) -> str:
    """Build one gateway reply, with the CON/END prefix the gateway expects."""
    text = body
    if footer_key:
        text = f"{body}\n\n{footer(footer_key, language)}"
    prefix = "END" if end else "CON"
    reply = f"{prefix} {text}"

    if len(reply) - 4 > SCREEN_LIMIT:
        # Should not happen -- pagination runs first -- but a screen that
        # overflows is silently cut off by the network, so it is logged.
        log.warning("USSD screen exceeds %d characters: %d", SCREEN_LIMIT,
                    len(reply) - 4)
    return reply


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------
def find_farmer(db: Session, phone: str) -> Farmer | None:
    """Match a dialling number to a registered farmer.

    Matching is on the last nine digits so +265991234567, 0991234567 and
    991234567 all resolve to the same farmer.
    """
    digits = "".join(c for c in (phone or "") if c.isdigit())
    tail = digits[-9:]
    if not tail:
        return None
    return db.scalar(select(Farmer).where(Farmer.phone.endswith(tail)))


def _starting_language(db: Session, farmer: Farmer | None, phone: str) -> Language:
    """Which language this dial-in should open in.

    A registered farmer gets their stored preference. For an unregistered
    caller there is no profile to read and no text to detect a language from,
    because the first screen arrives before they have typed anything -- so the
    language chosen on their last call is reused.

    That matters for this channel specifically: a farmer without a smartphone
    cannot register on the website, and asking them to re-select Chichewa on
    every call would undermine the reason USSD exists here. The fallback is
    English only for a number that has never dialled before.
    """
    if farmer:
        return farmer.language

    profile = profiles.get_profile(db, phone)
    if profile and profile.language:
        return profile.language

    digits = "".join(c for c in (phone or "") if c.isdigit())
    tail = digits[-9:]
    if tail:
        previous = db.scalar(
            select(UssdSession)
            .where(UssdSession.phone.endswith(tail))
            .order_by(UssdSession.id.desc())
        )
        if previous:
            return previous.language
    return Language.EN


def get_session(db: Session, session_id: str, phone: str, service_code: str,
                gateway: str) -> UssdSession:
    """Fetch or create the session row for this dial-in."""
    session = db.scalar(
        select(UssdSession).where(UssdSession.session_id == session_id)
    )
    if session:
        return session

    farmer = find_farmer(db, phone)
    session = UssdSession(
        session_id=session_id,
        phone=phone,
        service_code=service_code or SERVICE_CODE,
        language=_starting_language(db, farmer, phone),
        farmer_id=farmer.farmer_id if farmer else None,
        gateway=gateway,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


# ---------------------------------------------------------------------------
# The menu machine
# ---------------------------------------------------------------------------
async def handle(db: Session, *, session_id: str, phone: str, text: str,
                 service_code: str = SERVICE_CODE,
                 gateway: str = "simulator") -> str:
    """Return the gateway reply for one USSD request.

    `text` is the whole accumulated input, so "2*1*1" means the farmer pressed
    2, then 1, then 1.
    """
    session = get_session(db, session_id, phone, service_code, gateway)
    session.last_input = text or ""
    session.screens_served += 1

    parts = [part for part in (text or "").split("*") if part != ""]
    language = session.language.value

    # Nothing entered yet: the farmer has just dialled in.
    if not parts:
        db.commit()
        return render(screen("main", language), language)

    choice = parts[0]

    # "0" anywhere returns to the main menu, which is the convention farmers
    # already know from other USSD services.
    if parts[-1] == "0":
        session.pending_advice = None
        db.commit()
        return render(screen("main", language), language)

    if choice == "1":
        return await _weather_branch(db, session, parts, language)
    if choice == "2":
        return await _farming_branch(db, session, parts, language)
    if choice == "3":
        return await _tea_branch(db, session, parts, language)
    if choice == "4":
        return await _ask_branch(db, session, parts, language, text)
    if choice == "5":
        return _language_branch(db, session, parts, language)
    if choice == "6":
        return _area_branch(db, session, parts, language)
    if choice == "7":
        return _calendar_branch(db, session, parts, language)
    if choice == "8":
        return await _alerts_branch(db, session, parts, language)
    if choice == "9":
        session.completed = True
        db.commit()
        return render(screen("exit", language), language, end=True)

    session.completed = True
    db.commit()
    return render(screen("invalid", language), language, end=True)


async def _weather_branch(db: Session, session: UssdSession, parts: list[str],
                          language: str) -> str:
    """1. Weather -- current conditions, then an optional 5-day forecast."""
    from . import weather_service

    location = _location_for(db, session)

    # 1*1 = the farmer asked for the forecast.
    if len(parts) >= 2 and parts[1] == "1":
        weather = await weather_service.fetch_weather(location)
        if weather["offline"]:
            db.commit()
            return render(_offline_text(language), language, footer_key="back")

        lines = [location.upper()]
        for day in weather["forecast"][:5]:
            lines.append(
                f"{day['weekday']} {round(day['temp_max'])}C " +
                (f"{day['rain_probability']}%" if day['rain_probability'] is not None else f"{day['rain_mm']}mm")
            )
        db.commit()
        return render("\n".join(lines), language, footer_key="back")

    weather = await weather_service.fetch_weather(location)
    if weather["offline"]:
        db.commit()
        return render(_offline_text(language), language, footer_key="back")

    current = weather["current"]
    condition = current["condition_ny"] if language == "NY" else current["condition_en"]
    if language == "NY":
        body = (f"NYENGO - {location}\n"
                f"{condition}\n"
                f"Kutentha: {current['temperature']}C\n"
                f"Mvula: {_rain_text(current)}\n"
                f"Chinyezi: {current['humidity']}%")
    else:
        body = (f"WEATHER - {location}\n"
                f"{condition}\n"
                f"Temp: {current['temperature']}C\n"
                f"Rain: {_rain_text(current)}\n"
                f"Humidity: {current['humidity']}%")
    db.commit()
    return render(body, language, footer_key="forecast_back")


async def _farming_branch(db: Session, session: UssdSession, parts: list[str],
                          language: str) -> str:
    """2. Farming Advice -- choose a crop, then general advice for today."""
    # Just "2": show the crop menu.
    if len(parts) == 1:
        db.commit()
        return render(screen("crop", language), language)

    crop = parts[1]

    if crop == "2":  # Other crop
        session.completed = True
        db.commit()
        return render(screen("other_crop", language), language, end=True)

    if crop == "3":  # Back
        db.commit()
        return render(screen("main", language), language)

    if crop != "1":  # Not tea
        session.completed = True
        db.commit()
        return render(screen("invalid", language), language, end=True)

    # 2*1 and any following "1" presses page through today's tea advice.
    page = _count_page(parts, anchor_index=2)
    return await _serve_advice(
        db, session, language,
        question="what should I do on my tea farm today",
        page=page,
        heading="TEA ADVICE" if language == "EN" else "UPHUNGU WA TIYI",
    )


async def _tea_branch(db: Session, session: UssdSession, parts: list[str],
                      language: str) -> str:
    """3. Tea Advice -- pick a specific topic."""
    if len(parts) == 1:
        db.commit()
        return render(screen("topics", language), language)

    topic = TOPIC_BY_OPTION.get(parts[1])
    if not topic:
        session.completed = True
        db.commit()
        return render(screen("invalid", language), language, end=True)

    page = _count_page(parts, anchor_index=2)
    return await _serve_advice(
        db, session, language,
        question=topic.replace("_", " "),
        page=page,
        topic_hint=topic,
    )


async def _ask_branch(db: Session, session: UssdSession, parts: list[str],
                      language: str, raw_text: str) -> str:
    """4. Ask a question -- a free-text question, exactly as on the website."""
    if len(parts) == 1:
        db.commit()
        return render(screen("ask", language), language)

    question = parts[1].strip()
    if not question:
        session.completed = True
        db.commit()
        return render(screen("no_question", language), language, end=True)

    page = _count_page(parts, anchor_index=2)
    return await _serve_advice(db, session, language, question=question, page=page)


def _language_branch(db: Session, session: UssdSession, parts: list[str],
                     language: str) -> str:
    """5. Change Language -- switches the session, and the profile if known."""
    if len(parts) == 1:
        db.commit()
        return render(screen("language", language), language)

    chosen = parts[1]
    if chosen not in {"1", "2"}:
        session.completed = True
        db.commit()
        return render(screen("invalid", language), language, end=True)

    new_language = "EN" if chosen == "1" else "NY"
    session.language = Language(new_language)

    farmer = db.get(Farmer, session.farmer_id) if session.farmer_id else None
    # Persisting it means the change also applies to SMS replies (and the
    # website, for a registered farmer), not only to the rest of this call.
    profiles.set_language(db, session.phone, new_language, farmer)

    confirmation = screen(
        "language_set_en" if new_language == "EN" else "language_set_ny",
        new_language,
    )
    if not farmer:
        confirmation = f"{confirmation}\n{screen('not_registered', new_language)}"

    session.completed = True
    db.commit()
    return render(confirmation, new_language, end=True)


# Areas are listed a few per screen. "98" pages forward, because "0" already
# means Back and every single digit may be an area number.
AREAS_PER_SCREEN = 6
MORE_KEY = "98"


def _area_branch(db: Session, session: UssdSession, parts: list[str],
                 language: str) -> str:
    """6. My Area -- district, then area, saved for this number."""
    if len(parts) == 1:
        db.commit()
        return render(screen("district", language), language)

    if parts[1] not in {"1", "2"}:
        session.completed = True
        db.commit()
        return render(screen("invalid", language), language, end=True)

    district = DISTRICTS[int(parts[1]) - 1]
    names = areas_in(district)

    page = 0
    picked = None
    for part in parts[2:]:
        if part == MORE_KEY:
            page += 1
        else:
            picked = part
            break

    if picked is None:
        pages = max(1, -(-len(names) // AREAS_PER_SCREEN))
        page = page % pages
        start = page * AREAS_PER_SCREEN
        lines = [district.upper()]
        for number, name in enumerate(names[start:start + AREAS_PER_SCREEN], start + 1):
            lines.append(f"{number}. {name}")
        if pages > 1:
            lines.append(f"{MORE_KEY}. " + ("More" if language == "EN" else "Zina"))
        lines.append("0. " + ("Back" if language == "EN" else "Bwererani"))
        db.commit()
        return render("\n".join(lines), language)

    if not picked.isdigit() or not 1 <= int(picked) <= len(names):
        session.completed = True
        db.commit()
        return render(screen("invalid", language), language, end=True)

    name = names[int(picked) - 1]
    farmer = db.get(Farmer, session.farmer_id) if session.farmer_id else None
    profiles.set_location(db, session.phone, name, farmer)
    session.completed = True
    db.commit()
    altitude = LOCATIONS[name]["altitude_m"]
    if language == "NY":
        body = (f"Dera lanu tsopano ndi {name}, {district} ({altitude} m). "
                f"Nyengo ndi uphungu zidzakhala za {name}.")
    else:
        body = (f"Your area is now {name}, {district} ({altitude} m). "
                f"Weather and advice will be for {name}.")
    return render(body, language, end=True)


def _calendar_branch(db: Session, session: UssdSession, parts: list[str],
                     language: str) -> str:
    """7. This Month's Tasks -- the tea calendar, a screen at a time."""
    page = _count_page(parts, anchor_index=1)
    pages = paginate(month_text(date.today().month, language))
    index = min(page, len(pages) - 1)
    db.commit()
    if index < len(pages) - 1:
        return render(f"{pages[index]} ({index + 1}/{len(pages)})", language,
                      footer_key="more_back")
    return render(pages[index], language, footer_key="back")


async def _alerts_branch(db: Session, session: UssdSession, parts: list[str],
                         language: str) -> str:
    """8. Weather Alerts -- the current warning, and SMS alerts on or off."""
    from . import weather_service

    if len(parts) == 1:
        location = _location_for(db, session)
        weather = await weather_service.fetch_weather(location)
        found = weather_service.alerts(weather, language)
        if weather["offline"]:
            body = _offline_text(language)
        elif found:
            body = f"{location}: {found[0]['title']}"
        else:
            body = (f"{location}: no warnings for 3 days." if language == "EN"
                    else f"{location}: palibe chenjezo masiku 3.")
        db.commit()
        return render(body, language, footer_key="alerts_menu")

    if parts[1] not in {"1", "2"}:
        session.completed = True
        db.commit()
        return render(screen("invalid", language), language, end=True)

    enabled = parts[1] == "1"
    profiles.set_alerts(db, session.phone, enabled)
    session.completed = True
    db.commit()
    return render(screen("alerts_on" if enabled else "alerts_off", language),
                  language, end=True)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------
def _count_page(parts: list[str], anchor_index: int) -> int:
    """How many times "1" (More advice) has been pressed after a menu choice.

    The gateway resends the whole input, so "3*1*1*1" is the fertilizer topic
    followed by two "More advice" presses, which is page 2 counting from zero.
    """
    page = 0
    for part in parts[anchor_index:]:
        if part == "1":
            page += 1
        else:
            break
    return page


def _location_for(db: Session, session: UssdSession) -> str:
    farmer = db.get(Farmer, session.farmer_id) if session.farmer_id else None
    return profiles.location_for(db, session.phone, farmer)


def _offline_text(language: str) -> str:
    if language == "NY":
        return "Nyengo sikupezeka pano. Yesaninso pakapita kanthawi."
    return "Weather is unavailable right now. Please try again shortly."


async def _serve_advice(db: Session, session: UssdSession, language: str, *,
                        question: str, page: int, heading: str | None = None,
                        topic_hint: str | None = None) -> str:
    """Generate advice once, then serve it one USSD screen at a time.

    The advice is produced on the first screen and kept on the session row, so
    pressing "More advice" pages through the stored text instead of repeating
    the weather lookup and the whole pipeline.
    """
    if page == 0 or not session.pending_advice:
        result = await advisory_service.answer(
            db,
            question=question,
            language=language,
            location=_location_for(db, session),
            channel="USSD",
            farmer_id=session.farmer_id,
            phone=session.phone,
            max_sentences=3,
            brief=False,
        )
        session.pending_advice = result["advice"]
        session.pending_topic = result["topic"]
        db.commit()

    pages = paginate(session.pending_advice)

    # Pressing "More advice" past the end simply holds on the last page rather
    # than dropping the farmer out of the session.
    index = min(page, len(pages) - 1)
    body = pages[index]

    if heading and index == 0:
        body = f"{heading}\n{body}"

    # Only offer "More advice" when there is actually more to read.
    if index < len(pages) - 1:
        counter = f"({index + 1}/{len(pages)})"
        return render(f"{body} {counter}", language, footer_key="more_back")

    db.commit()
    return render(body, language, footer_key="back")


def status() -> dict:
    """Reported on the admin dashboard and the simulator screen."""
    from ..config import settings

    from . import tunnel

    live = bool(settings.at_api_key)
    base = tunnel.public_url()
    return {
        "mode": ("africastalking-sandbox" if settings.at_username == "sandbox" else "africastalking")
        if live else "simulator",
        "gateway": "Africa's Talking",
        "service_code": settings.ussd_code or SERVICE_CODE,
        "callback_url": f"{base}/api/ussd" if base else None,
        "screen_limit": SCREEN_LIMIT,
        "configured": bool(settings.at_api_key),
    }


def _rain_text(current: dict) -> str:
    """Chance of rain as a percentage, or the expected amount when there is none."""
    if current.get("rain_probability") is not None:
        return f"{current['rain_probability']}%"
    return f"{current.get('rain_today_mm') or 0}mm"
