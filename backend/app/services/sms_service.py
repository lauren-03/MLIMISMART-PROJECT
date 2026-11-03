"""SMS delivery, and the parsing of incoming SMS commands."""
import logging
import re

import httpx
from sqlalchemy.orm import Session

from ..config import settings
from ..models import SmsLog

log = logging.getLogger(__name__)

AT_SANDBOX_URL = "https://api.sandbox.africastalking.com/version1/messaging"
AT_LIVE_URL = "https://api.africastalking.com/version1/messaging"

# A single SMS is 160 characters. Advice is trimmed to two parts so a farmer is
# never charged for a long multi-part message they did not ask for.
SMS_LIMIT = 320
# Reference replies the farmer asked for (the area list, this month's work)
# may use a third part; they are not useful cut short.
LONG_SMS_LIMIT = 459


def gateway() -> str:
    """The SMS gateway in use: "android", "africastalking" or "simulator"."""
    mode = settings.sms_gateway.lower()
    if mode == "android" and settings.android_sms_url:
        return "android"
    if (mode == "africastalking" or settings.sms_enabled) and settings.at_api_key:
        return "africastalking"
    return "simulator"


def _android_auth() -> tuple[str, str]:
    return settings.android_sms_username, settings.android_sms_password


async def _send_android(phone: str, message: str) -> str:
    """Send through the phone running SMS Gateway for Android (Local Server)."""
    url = settings.android_sms_url.rstrip("/") + "/message"
    body = {"textMessage": {"text": message}, "phoneNumbers": [_to_e164(phone)]}
    try:
        async with httpx.AsyncClient(timeout=20.0, auth=_android_auth()) as client:
            response = await client.post(url, json=body)
            response.raise_for_status()
        return "ok"
    except Exception as exc:  # noqa: BLE001 - log the failure, keep the record
        log.error("Android SMS gateway send failed for %s: %s", phone, exc)
        return "failed"


async def register_android_webhook(public_url: str) -> bool:
    """Ask the phone to forward every received SMS to this API."""
    if gateway() != "android" or not public_url:
        return False
    base = settings.android_sms_url.rstrip("/")
    target = public_url.rstrip("/") + "/api/sms/android"
    try:
        async with httpx.AsyncClient(timeout=15.0, auth=_android_auth()) as client:
            existing = (await client.get(base + "/webhooks")).json() or []
            for hook in existing:
                if hook.get("event") == "sms:received" and hook.get("url") != target:
                    await client.delete(f"{base}/webhooks/{hook['id']}")
            if not any(h.get("url") == target for h in existing):
                response = await client.post(base + "/webhooks", json={
                    "id": "mlimismart-sms", "url": target, "event": "sms:received"})
                response.raise_for_status()
        log.info("Android SMS gateway will forward received SMS to %s", target)
        return True
    except Exception as exc:  # noqa: BLE001
        log.error("Could not register the webhook on the Android phone: %s", exc)
        return False


async def send_sms(db: Session, phone: str, message: str, *, limit: int = SMS_LIMIT) -> dict:
    """Send an outgoing SMS through the active gateway and log it."""
    message = _trim(message, limit)
    mode = gateway()

    if mode == "android":
        status = await _send_android(phone, message)
        db.add(SmsLog(phone=phone, direction="OUT", message=message, gateway="android", status=status))
        db.commit()
        return {"gateway": "android", "status": status, "message": message}

    if mode == "simulator":
        entry = SmsLog(phone=phone, direction="OUT", message=message,
                       gateway="simulator", status="ok")
        db.add(entry)
        db.commit()
        return {"gateway": "simulator", "status": "ok", "message": message}

    url = AT_LIVE_URL if settings.at_username != "sandbox" else AT_SANDBOX_URL
    data = {
        "username": settings.at_username,
        "to": _to_e164(phone),
        "message": message,
    }
    if settings.at_sender_id:
        data["from"] = settings.at_sender_id

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                url,
                data=data,
                headers={
                    "apiKey": settings.at_api_key,
                    "Accept": "application/json",
                },
            )
            response.raise_for_status()
        status = "ok"
    except Exception as exc:  # noqa: BLE001 - log the failure, keep the record
        log.error("Africa's Talking send failed for %s: %s", phone, exc)
        status = "failed"

    entry = SmsLog(phone=phone, direction="OUT", message=message,
                   gateway="africastalking", status=status)
    db.add(entry)
    db.commit()
    return {"gateway": "africastalking", "status": status, "message": message}


def log_incoming(db: Session, phone: str, message: str, source: str | None = None) -> None:
    db.add(SmsLog(phone=phone, direction="IN", message=message,
                  gateway=source or gateway(), status="ok"))
    db.commit()


def parse_command(text: str) -> dict:
    """Recognise the control commands a farmer can send.

    Returns {"command": ..., "value": ...}. A message that is not a command is
    returned as {"command": "question"} and goes to the advisory engine.
    """
    cleaned = (text or "").strip()
    upper = cleaned.upper()

    if upper in {"HELP", "INFO", "START", "THANDIZO"}:
        return {"command": "help"}

    language_match = re.match(r"^LANG(?:UAGE)?\s+(EN|NY|ENGLISH|CHICHEWA)$", upper)
    if language_match:
        token = language_match.group(1)
        value = "EN" if token in {"EN", "ENGLISH"} else "NY"
        return {"command": "language", "value": value}

    location_match = re.match(r"^(?:LOC|AREA|DERA)\s+(.+)$", upper)
    if location_match:
        return {"command": "location", "value": location_match.group(1).title()}

    if upper in {"AREAS", "MADERA"}:
        return {"command": "areas"}

    if upper in {"CALENDAR", "KALENDALA", "MONTH", "MWEZI", "TASKS", "NTCHITO"}:
        return {"command": "calendar"}

    alerts_match = re.match(r"^(?:ALERTS?|CHENJEZO|MACHENJEZO)\s+(ON|OFF|INDE|AYI)$", upper)
    if alerts_match:
        return {"command": "alerts", "value": alerts_match.group(1) in {"ON", "INDE"}}

    if upper in {"ALERT", "ALERTS", "CHENJEZO", "MACHENJEZO"}:
        return {"command": "alerts_now"}

    return {"command": "question", "value": cleaned}


def detect_language(text: str) -> str | None:
    """Guess the language of an unregistered sender from common Chichewa words.

    Only used when we have no stored preference for the phone number. Returns
    None when there is no signal, and the caller keeps its default.
    """
    words = set(re.findall(r"\w+", (text or "").lower()))
    chichewa_markers = {
        "kodi", "ndi", "ndingathire", "fetereza", "mvula", "nyengo", "liti",
        "bwanji", "kusenda", "kutema", "tizilombo", "masamba", "tiyi", "moni",
        "ndiike", "lero", "mawa", "munda", "chiyani", "zikomo", "kokolola",
    }
    if words & chichewa_markers:
        return "NY"
    return None


def _trim(message: str, limit: int = SMS_LIMIT) -> str:
    message = " ".join((message or "").split())
    if len(message) <= limit:
        return message
    return message[: limit - 3].rstrip() + "..."


def _to_e164(phone: str) -> str:
    """Normalise a Malawi number to +265 format for the gateway."""
    digits = re.sub(r"\D", "", phone or "")
    if digits.startswith("265"):
        return "+" + digits
    if digits.startswith("0"):
        return "+265" + digits[1:]
    if len(digits) == 9:
        return "+265" + digits
    return "+" + digits


def status() -> dict:
    mode = gateway()
    return {
        "mode": mode,
        "gateway": {"android": "SMS Gateway for Android", "africastalking": "Africa's Talking",
                    "simulator": "Simulator"}[mode],
        "number": settings.sms_number or None,
        "username": settings.at_username if mode == "africastalking" else None,
        "configured": mode != "simulator",
    }
