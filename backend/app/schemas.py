"""Request and response shapes for the API."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ------------------------------- farmers ---------------------------------
class FarmerRegister(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    phone: str = Field(min_length=9, max_length=20)
    password: str = Field(min_length=4, max_length=128)
    location: str = Field(default="Thyolo", max_length=80)
    language: str = Field(default="NY")
    farm_size_ha: float | None = Field(default=None, ge=0, le=1000)
    years_farming: int | None = Field(default=None, ge=0, le=100)

    @field_validator("phone")
    @classmethod
    def clean_phone(cls, value: str) -> str:
        digits = "".join(c for c in value if c.isdigit())
        if len(digits) < 9:
            raise ValueError("Enter a valid Malawi phone number, e.g. 0991234567")
        return digits

    @field_validator("language")
    @classmethod
    def check_language(cls, value: str) -> str:
        value = value.upper()
        if value not in {"EN", "NY"}:
            raise ValueError("Language must be EN or NY")
        return value


class FarmerLogin(BaseModel):
    phone: str
    password: str

    @field_validator("phone")
    @classmethod
    def clean_phone(cls, value: str) -> str:
        return "".join(c for c in value if c.isdigit())


class FarmerUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    location: str | None = Field(default=None, max_length=80)
    language: str | None = None
    farm_size_ha: float | None = Field(default=None, ge=0, le=1000)
    years_farming: int | None = Field(default=None, ge=0, le=100)


class FarmerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    farmer_id: int
    name: str
    phone: str
    location: str
    language: str
    farm_size_ha: float | None
    years_farming: int | None
    role: str
    created_at: datetime | None = None

    @field_validator("language", "role", mode="before")
    @classmethod
    def enum_to_value(cls, value):
        return getattr(value, "value", value)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    farmer: FarmerOut


# ------------------------------- advisory ---------------------------------
class AdviceAsk(BaseModel):
    question: str = Field(min_length=2, max_length=500)
    language: str | None = None
    location: str | None = None


class AdviceOut(BaseModel):
    request_id: int | None
    topic: str
    confidence: float
    classification_method: str
    urgency: str
    advice: str
    source: str
    reasoning: str
    rules_fired: list[str]
    language: str
    location: str
    season: str
    weather_summary: str
    action: str | None = None
    rain_prediction: dict | None = None
    model_version: int | None = None


class HistoryItem(BaseModel):
    request_id: int
    question: str
    topic: str | None
    language: str
    channel: str
    location: str
    created_at: datetime | None
    advice: str | None
    urgency: str | None
    source: str | None
    reasoning: str | None


# ------------------------------ knowledge ---------------------------------
class KnowledgeIn(BaseModel):
    topic: str
    title_en: str = Field(min_length=3, max_length=200)
    title_ny: str = Field(min_length=3, max_length=200)
    body_en: str = Field(min_length=10)
    body_ny: str = Field(min_length=10)
    season: str | None = None


class KnowledgeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    topic: str
    title_en: str
    title_ny: str
    body_en: str
    body_ny: str
    season: str | None
    is_active: bool


# --------------------------------- sms ------------------------------------
class SmsIn(BaseModel):
    """An inbound SMS, from the simulator or an Africa's Talking webhook."""
    phone: str = Field(min_length=5, max_length=20, alias="from")
    text: str = Field(min_length=1, max_length=500)

    model_config = ConfigDict(populate_by_name=True)


class SmsOut(BaseModel):
    phone: str
    incoming: str
    reply: str
    topic: str | None
    gateway: str
    language: str
    characters: int
