"""Password hashing and JWT issuing."""
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from .config import settings


# ---------------------------------------------------------------------------
# Password strength
# ---------------------------------------------------------------------------
# A farmer's account holds their phone number, area and farm records, so the
# password must not be something a neighbour could guess. The rules are kept
# few and easy to explain on a phone screen: long enough, mixes letters and
# numbers, and is not the farmer's own name, phone number or a common word.
# "lauren" is refused for a farmer called Lauren; "Laur3n2026" is accepted.
PASSWORD_MIN_LENGTH = 8

COMMON_WORDS = {
    "password", "passw0rd", "qwerty", "abc", "abcd", "letmein", "welcome",
    "admin", "farmer", "mlimi", "mlimismart", "tea", "tiyi", "malawi",
    "thyolo", "mulanje", "blantyre", "lilongwe", "iloveyou", "monkey",
    "football", "secret", "zikomo", "moni", "12345678", "123456789",
    "1234567890", "87654321", "11111111", "00000000",
}


def password_problems(password: str, *, name: str = "", phone: str = "") -> list[str]:
    """Every rule the password breaks, as messages a farmer can act on.

    An empty list means the password is acceptable. The same rules are shown
    as a live checklist on the registration form, so the farmer sees them
    before submitting rather than after.
    """
    password = password or ""
    problems = []
    lowered = password.lower()
    letters_only = "".join(ch for ch in lowered if ch.isalpha())
    digits_only = "".join(ch for ch in password if ch.isdigit())

    if len(password) < PASSWORD_MIN_LENGTH:
        problems.append(f"Use at least {PASSWORD_MIN_LENGTH} characters.")
    if not any(ch.isalpha() for ch in password) or not any(ch.isdigit() for ch in password):
        problems.append("Mix letters and numbers, for example Laur3n2026.")

    name_parts = [part for part in "".join(
        ch if ch.isalpha() else " " for ch in (name or "").lower()).split() if len(part) >= 3]
    if any(part in lowered for part in name_parts):
        problems.append("Do not use your own name in your password.")

    phone_digits = "".join(ch for ch in (phone or "") if ch.isdigit())
    if phone_digits and len(digits_only) >= 6 and (
            digits_only in phone_digits or phone_digits[-6:] in digits_only):
        problems.append("Do not use your phone number in your password.")

    if lowered in COMMON_WORDS or letters_only in COMMON_WORDS or len(set(lowered)) <= 2:
        problems.append("This password is too easy to guess. Choose something less common.")
    return problems


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        # Raised when the stored value is not a valid bcrypt hash.
        return False


def create_access_token(farmer_id: int, role: str) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": str(farmer_id), "role": role, "exp": expires}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
    except jwt.PyJWTError:
        return None
