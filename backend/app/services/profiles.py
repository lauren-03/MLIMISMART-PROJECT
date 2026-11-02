"""Who is on the other end of a phone number, and what they prefer."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..data.locations import DEFAULT_LOCATION
from ..models import Farmer, Language, PhoneProfile


def phone_tail(phone: str | None) -> str:
    return "".join(c for c in (phone or "") if c.isdigit())[-9:]


def find_farmer(db: Session, phone: str | None) -> Farmer | None:
    tail = phone_tail(phone)
    if not tail:
        return None
    return db.scalar(select(Farmer).where(Farmer.phone.endswith(tail)))


def get_profile(db: Session, phone: str | None) -> PhoneProfile | None:
    tail = phone_tail(phone)
    if not tail:
        return None
    return db.scalar(select(PhoneProfile).where(PhoneProfile.phone == tail))


def upsert_profile(db: Session, phone: str, **fields) -> PhoneProfile:
    """Create or update the profile for a number. Caller commits."""
    profile = get_profile(db, phone)
    if profile is None:
        profile = PhoneProfile(phone=phone_tail(phone))
        db.add(profile)
    for key, value in fields.items():
        setattr(profile, key, value)
    return profile


def location_for(db: Session, phone: str | None, farmer: Farmer | None = None) -> str:
    """The area to advise for: farmer profile, then phone profile, then default."""
    farmer = farmer or find_farmer(db, phone)
    if farmer:
        return farmer.location
    profile = get_profile(db, phone)
    return profile.location if profile and profile.location else DEFAULT_LOCATION


def language_for(db: Session, phone: str | None, farmer: Farmer | None = None) -> Language | None:
    farmer = farmer or find_farmer(db, phone)
    if farmer:
        return farmer.language
    profile = get_profile(db, phone)
    return profile.language if profile else None


def set_location(db: Session, phone: str, location: str, farmer: Farmer | None = None) -> None:
    """Save the area on the farmer's profile if registered, else on the number."""
    farmer = farmer or find_farmer(db, phone)
    if farmer:
        farmer.location = location
    else:
        upsert_profile(db, phone, location=location)


def set_language(db: Session, phone: str, language: str, farmer: Farmer | None = None) -> None:
    farmer = farmer or find_farmer(db, phone)
    if farmer:
        farmer.language = Language(language)
    else:
        upsert_profile(db, phone, language=Language(language))


def set_alerts(db: Session, phone: str, enabled: bool) -> None:
    upsert_profile(db, phone, alerts_enabled=enabled)
