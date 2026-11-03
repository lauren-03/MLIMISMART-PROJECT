"""Advice read aloud in Chichewa or English."""
import asyncio

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field

from ..services import speech_service

router = APIRouter(prefix="/api/speech", tags=["speech"])


class SpeechIn(BaseModel):
    text: str = Field(min_length=1, max_length=speech_service.MAX_CHARS)
    language: str = Field(default="EN", pattern="^(EN|NY)$")


@router.post("", response_class=Response)
async def speak(payload: SpeechIn):
    if not speech_service.available():
        raise HTTPException(status_code=503, detail="Voice is not installed on the server")
    audio = await asyncio.to_thread(speech_service.synthesize, payload.text, payload.language)
    return Response(content=audio, media_type="audio/wav",
                    headers={"Cache-Control": "private, max-age=86400"})


@router.get("/status")
def status():
    return {"available": speech_service.available(),
            "voices": {lang: speech_service.voice_name(lang) for lang in ("NY", "EN")}}
