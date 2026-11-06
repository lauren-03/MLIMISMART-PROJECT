"""Database tables for MlimiSmart."""
from datetime import datetime, timezone
from enum import Enum as PyEnum

from datetime import date

from sqlalchemy import (
    Boolean, Date, DateTime, Enum, Float, ForeignKey, Integer, LargeBinary,
    String, Text,
    UniqueConstraint, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Language(str, PyEnum):
    """EN = English, NY = Chichewa/Chinyanja (ISO 639 'ny')."""
    EN = "EN"
    NY = "NY"


class Channel(str, PyEnum):
    WEB = "WEB"
    SMS = "SMS"
    USSD = "USSD"


class Role(str, PyEnum):
    FARMER = "FARMER"
    ADMIN = "ADMIN"


class Farmer(Base):
    __tablename__ = "farmers"

    farmer_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str] = mapped_column(String(80), nullable=False, default="Thyolo")
    language: Mapped[Language] = mapped_column(Enum(Language), default=Language.NY)
    farm_size_ha: Mapped[float | None] = mapped_column(Float, nullable=True)
    years_farming: Mapped[int | None] = mapped_column(Integer, nullable=True)
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.FARMER)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    requests: Mapped[list["AdviceRequest"]] = relationship(
        back_populates="farmer", cascade="all, delete-orphan"
    )


class AdviceRequest(Base):
    __tablename__ = "advice_requests"

    request_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    farmer_id: Mapped[int | None] = mapped_column(
        ForeignKey("farmers.farmer_id", ondelete="CASCADE"), index=True, nullable=True
    )
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[Language] = mapped_column(Enum(Language), default=Language.NY)
    channel: Mapped[Channel] = mapped_column(Enum(Channel), default=Channel.WEB)
    location: Mapped[str] = mapped_column(String(80), default="Thyolo")
    topic: Mapped[str | None] = mapped_column(String(40), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    farmer: Mapped["Farmer | None"] = relationship(back_populates="requests")
    response: Mapped["AdviceResponse | None"] = relationship(
        back_populates="request", cascade="all, delete-orphan", uselist=False
    )


class AdviceResponse(Base):
    __tablename__ = "advice_responses"

    response_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    request_id: Mapped[int] = mapped_column(
        ForeignKey("advice_requests.request_id", ondelete="CASCADE"), index=True
    )
    advice: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[Language] = mapped_column(Enum(Language), default=Language.NY)
    # How the wording was produced: "llm" or "template". The decision itself
    # always comes from the rule engine, which is what `reasoning` records.
    source: Mapped[str] = mapped_column(String(20), default="template")
    urgency: Mapped[str] = mapped_column(String(20), default="normal")
    reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    weather_summary: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    request: Mapped["AdviceRequest"] = relationship(back_populates="response")


class WeatherRecord(Base):
    """Cache of weather readings, so the admin can review what the engine saw."""
    __tablename__ = "weather"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    location: Mapped[str] = mapped_column(String(80), index=True)
    temperature: Mapped[float | None] = mapped_column(Float)
    rainfall_probability: Mapped[int | None] = mapped_column(Integer)
    rainfall_mm: Mapped[float | None] = mapped_column(Float)
    humidity: Mapped[int | None] = mapped_column(Integer)
    wind_kph: Mapped[float | None] = mapped_column(Float)
    condition: Mapped[str | None] = mapped_column(String(60))
    recorded_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class KnowledgeItem(Base):
    """Tea farming knowledge the admin maintains, in both languages."""
    __tablename__ = "knowledge_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    topic: Mapped[str] = mapped_column(String(40), index=True)
    title_en: Mapped[str] = mapped_column(String(200))
    title_ny: Mapped[str] = mapped_column(String(200))
    body_en: Mapped[str] = mapped_column(Text)
    body_ny: Mapped[str] = mapped_column(Text)
    season: Mapped[str | None] = mapped_column(String(40), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class SmsLog(Base):
    __tablename__ = "sms_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    phone: Mapped[str] = mapped_column(String(20), index=True)
    direction: Mapped[str] = mapped_column(String(10))  # "IN" or "OUT"
    message: Mapped[str] = mapped_column(Text)
    # "simulator" when demonstrated locally, "africastalking" when sent live
    gateway: Mapped[str] = mapped_column(String(30), default="simulator")
    status: Mapped[str] = mapped_column(String(20), default="ok")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class UssdSession(Base):
    """One USSD dial-in session.

    A USSD gateway sends the whole accumulated input on every request (for
    example "2*1*1"), so menu navigation is driven by that string and does not
    strictly need server state. This table exists for two reasons that do:

      1. Advice is far longer than a 182-character USSD screen, so the
         generated text is held here and served a page at a time. Without it,
         every "More advice" press would re-run the weather lookup.
      2. It gives the administrator a record of USSD usage, which is one of
         the research questions.
    """
    __tablename__ = "ussd_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    phone: Mapped[str] = mapped_column(String(20), index=True)
    service_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    language: Mapped[Language] = mapped_column(Enum(Language), default=Language.EN)
    farmer_id: Mapped[int | None] = mapped_column(
        ForeignKey("farmers.farmer_id", ondelete="SET NULL"), nullable=True
    )
    # The advice currently being paged through, and how far the farmer has read.
    pending_advice: Mapped[str | None] = mapped_column(Text, nullable=True)
    pending_topic: Mapped[str | None] = mapped_column(String(40), nullable=True)
    last_input: Mapped[str | None] = mapped_column(String(255), nullable=True)
    screens_served: Mapped[int] = mapped_column(Integer, default=0)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    gateway: Mapped[str] = mapped_column(String(30), default="simulator")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class PhoneProfile(Base):
    """Preferences for a phone number, whether or not it belongs to a farmer.

    SMS and USSD are meant for farmers who cannot register on the website, so
    their chosen area, language and alert subscription have to be remembered
    against the number itself. A registered farmer's own profile still takes
    priority; this row only adds the alert opt-in for them.
    """
    __tablename__ = "phone_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    phone: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    location: Mapped[str | None] = mapped_column(String(80), nullable=True)
    language: Mapped[Language | None] = mapped_column(Enum(Language), nullable=True)
    alerts_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class HarvestRecord(Base):
    """One plucking round in the farmer's harvest diary."""
    __tablename__ = "harvest_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    farmer_id: Mapped[int] = mapped_column(
        ForeignKey("farmers.farmer_id", ondelete="CASCADE"), index=True
    )
    harvest_date: Mapped[date] = mapped_column(Date, index=True)
    kg: Mapped[float] = mapped_column(Float)
    # Price per kg of green leaf in Malawi Kwacha, as the farmer was paid.
    price_per_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Broadcast(Base):
    """A weather alert or notice the administrator sent by SMS."""
    __tablename__ = "broadcasts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(120))
    message_en: Mapped[str] = mapped_column(Text)
    message_ny: Mapped[str] = mapped_column(Text)
    district: Mapped[str | None] = mapped_column(String(40), nullable=True)
    location: Mapped[str | None] = mapped_column(String(80), nullable=True)
    recipients: Mapped[int] = mapped_column(Integer, default=0)
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("farmers.farmer_id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class WeatherHistory(Base):
    """Daily observed weather per area. Training data for the rain model."""
    __tablename__ = "weather_history"
    __table_args__ = (UniqueConstraint("location", "day", name="uq_history_location_day"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    location: Mapped[str] = mapped_column(String(80), index=True)
    day: Mapped[date] = mapped_column(Date, index=True)
    rain_mm: Mapped[float | None] = mapped_column(Float)
    tmax: Mapped[float | None] = mapped_column(Float)
    tmin: Mapped[float | None] = mapped_column(Float)
    humidity: Mapped[float | None] = mapped_column(Float)
    wind_kph: Mapped[float | None] = mapped_column(Float)
    pressure: Mapped[float | None] = mapped_column(Float)
    cloud: Mapped[float | None] = mapped_column(Float)


class SoilMoisture(Base):
    """Daily soil moisture per area from ERA5-Land (m3 of water per m3 of soil)."""
    __tablename__ = "soil_moisture"
    __table_args__ = (UniqueConstraint("location", "day", name="uq_soil_location_day"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    location: Mapped[str] = mapped_column(String(80), index=True)
    day: Mapped[date] = mapped_column(Date, index=True)
    top: Mapped[float | None] = mapped_column(Float)    # 0-7 cm
    root: Mapped[float | None] = mapped_column(Float)   # 7-28 cm


class NasaPower(Base):
    """Daily agroclimate data per area from NASA POWER."""
    __tablename__ = "nasa_power"
    __table_args__ = (UniqueConstraint("location", "day", name="uq_power_location_day"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    location: Mapped[str] = mapped_column(String(80), index=True)
    day: Mapped[date] = mapped_column(Date, index=True)
    rain_mm: Mapped[float | None] = mapped_column(Float)
    solar: Mapped[float | None] = mapped_column(Float)          # MJ/m2/day
    root_wetness: Mapped[float | None] = mapped_column(Float)   # 0-1


class ChirpsMonthly(Base):
    """Monthly rainfall per area from CHIRPS (satellite and rain gauge)."""
    __tablename__ = "chirps_monthly"
    __table_args__ = (UniqueConstraint("location", "month", name="uq_chirps_location_month"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    location: Mapped[str] = mapped_column(String(80), index=True)
    month: Mapped[date] = mapped_column(Date, index=True)   # first day of the month
    rain_mm: Mapped[float | None] = mapped_column(Float)


class RainPrediction(Base):
    """What the rain model predicted, checked later against what happened."""
    __tablename__ = "rain_predictions"
    __table_args__ = (UniqueConstraint("location", "target_day", name="uq_prediction_location_day"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    location: Mapped[str] = mapped_column(String(80), index=True)
    target_day: Mapped[date] = mapped_column(Date, index=True)
    probability: Mapped[float] = mapped_column(Float)
    model_version: Mapped[int] = mapped_column(Integer)
    actual_rain_mm: Mapped[float | None] = mapped_column(Float, nullable=True)
    correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class AdviceDecision(Base):
    """The advice model's decision for one request, and the farmer's rating of it."""
    __tablename__ = "advice_decisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    request_id: Mapped[int] = mapped_column(
        ForeignKey("advice_requests.request_id", ondelete="CASCADE"), unique=True, index=True
    )
    topic: Mapped[str] = mapped_column(String(40))
    action: Mapped[str] = mapped_column(String(40))
    confidence: Mapped[float] = mapped_column(Float)
    features: Mapped[str] = mapped_column(Text)  # JSON
    model_version: Mapped[int] = mapped_column(Integer)
    helpful: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    rated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ModelRun(Base):
    """One training run of a model, with its test results."""
    __tablename__ = "model_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    model_name: Mapped[str] = mapped_column(String(40), index=True)
    version: Mapped[int] = mapped_column(Integer)
    train_rows: Mapped[int] = mapped_column(Integer)
    test_rows: Mapped[int] = mapped_column(Integer)
    metrics: Mapped[str] = mapped_column(Text)  # JSON
    trained_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ModelArtifact(Base):
    """A trained model kept in the database, with the record of its training.

    Render rebuilds its filesystem on every deployment, so a model saved only
    as a file is lost. The bytes live here instead, beside the figures that
    justify them, and the backend loads the newest *approved* row - never
    simply the newest one, so a poor training run cannot take over.
    """
    __tablename__ = "model_artifacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    model_name: Mapped[str] = mapped_column(String(40), index=True)
    version: Mapped[int] = mapped_column(Integer)
    artifact: Mapped[bytes] = mapped_column(LargeBinary)       # joblib bytes
    artifact_sha256: Mapped[str] = mapped_column(String(64))
    artifact_bytes: Mapped[int] = mapped_column(Integer)
    # what the model was taught on
    dataset_version: Mapped[str] = mapped_column(String(60))   # e.g. "history-2010-2025"
    training_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    training_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    features: Mapped[str] = mapped_column(Text)                # JSON list
    train_rows: Mapped[int] = mapped_column(Integer, default=0)
    test_rows: Mapped[int] = mapped_column(Integer, default=0)
    # how well it did, and the whole report behind the summary
    metrics: Mapped[str] = mapped_column(Text)                 # JSON
    report: Mapped[str | None] = mapped_column(Text, nullable=True)   # JSON
    library_versions: Mapped[str | None] = mapped_column(Text, nullable=True)
    # whether it is allowed to serve farmers
    approved: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    approved_by: Mapped[str | None] = mapped_column(String(60), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    trained_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
