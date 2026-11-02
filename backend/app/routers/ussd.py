"""USSD endpoints (Module 7: USSD advisory)."""
import logging
import uuid

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import UssdSession
from ..services import ussd_service

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ussd", tags=["ussd"])


class UssdSimulateIn(BaseModel):
    """One keypress sequence from the simulator screen."""
    model_config = ConfigDict(populate_by_name=True)

    phone: str = Field(min_length=5, max_length=20)
    # The accumulated input, e.g. "2*1". Empty means the farmer just dialled.
    text: str = Field(default="", max_length=255)
    session_id: str | None = Field(default=None, alias="sessionId")


class UssdSimulateOut(BaseModel):
    session_id: str
    raw: str          # exactly what the gateway would receive
    message: str      # the text the farmer sees, prefix removed
    is_end: bool      # True when the session closed
    language: str
    characters: int
    text: str         # the accumulated input that produced this screen


@router.post("", response_class=PlainTextResponse)
async def gateway(
    request: Request,
    db: Session = Depends(get_db),
    sessionId: str | None = Form(default=None),
    phoneNumber: str | None = Form(default=None),
    serviceCode: str | None = Form(default=None),
    text: str | None = Form(default=None),
):
    """Africa's Talking USSD callback.

    The reply must be plain text beginning with CON or END. Any failure still
    returns a valid END screen: an unhandled error would otherwise leave the
    farmer looking at a network error message with no explanation.
    """
    form = await request.form()
    session_id = sessionId or str(form.get("sessionId") or "")
    phone = phoneNumber or str(form.get("phoneNumber") or "")
    service_code = serviceCode or str(form.get("serviceCode") or ussd_service.SERVICE_CODE)
    entered = text if text is not None else str(form.get("text") or "")

    if not session_id or not phone:
        log.warning("USSD callback missing sessionId or phoneNumber")
        return PlainTextResponse("END Invalid request.")

    try:
        reply = await ussd_service.handle(
            db,
            session_id=session_id,
            phone=phone,
            text=entered,
            service_code=service_code,
            gateway="africastalking",
        )
    except Exception:  # noqa: BLE001 - never show the farmer a stack trace
        log.exception("USSD handling failed for session %s", session_id)
        reply = "END Service is temporarily unavailable. Please try again."

    return PlainTextResponse(reply)


@router.post("/simulate", response_model=UssdSimulateOut)
async def simulate(payload: UssdSimulateIn, db: Session = Depends(get_db)):
    """Demonstrate the USSD channel without a gateway account."""
    session_id = payload.session_id or f"sim-{uuid.uuid4().hex[:12]}"

    raw = await ussd_service.handle(
        db,
        session_id=session_id,
        phone=payload.phone,
        text=payload.text,
        gateway="simulator",
    )

    is_end = raw.startswith("END")
    message = raw[4:] if raw[:4] in ("CON ", "END ") else raw

    session = db.scalar(
        select(UssdSession).where(UssdSession.session_id == session_id)
    )

    return UssdSimulateOut(
        session_id=session_id,
        raw=raw,
        message=message,
        is_end=is_end,
        language=session.language.value if session else "EN",
        characters=len(message),
        text=payload.text,
    )


@router.get("/status")
def status():
    """Which USSD mode is active, and the service code to dial."""
    return ussd_service.status()
