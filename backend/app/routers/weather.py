"""Weather endpoints (Module 2: Weather)."""
from fastapi import APIRouter, Depends, Query

from ..data.locations import DISTRICTS, KIND_LABELS, LOCATIONS
from ..deps import get_current_farmer
from ..models import Farmer
from ..database import get_db
from ..ml import rain_model, store
from ..services import weather_service
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/weather", tags=["weather"])


@router.get("/locations")
def locations():
    """The tea growing areas the system covers, grouped by district order."""
    return [
        {
            "name": name,
            "district": place["district"],
            "altitude_m": place["altitude_m"],
            "kind": place["kind"],
            "kind_en": KIND_LABELS[place["kind"]][0],
            "kind_ny": KIND_LABELS[place["kind"]][1],
            "latitude": place["lat"],
            "longitude": place["lon"],
        }
        for district in DISTRICTS
        for name, place in LOCATIONS.items()
        if place["district"] == district
    ]


@router.get("/areas")
async def areas():
    """Today's weather for every area at once -- drives the map page."""
    return await weather_service.fetch_many()


@router.get("/prediction")
def prediction(location: str | None = Query(default=None), db: Session = Depends(get_db)):
    """MlimiSmart's own rain prediction for tomorrow, from the trained rain model."""
    result = rain_model.probability_for(db, location)
    runs = store.runs(db, rain_model.NAME, limit=1)
    return {
        "prediction": result,
        "model": runs[0] if runs else None,
        "live": rain_model.live_accuracy(db),
    }


@router.get("/alerts")
async def alerts(
    location: str | None = Query(default=None, description="Tea growing area"),
    language: str = Query(default="EN", pattern="^(EN|NY)$"),
):
    """Warnings for the next three days in one area."""
    weather = await weather_service.fetch_weather(location)
    return {
        "location": weather["location"],
        "offline": weather["offline"],
        "alerts": weather_service.alerts(weather, language),
    }


@router.get("")
async def current(
    location: str | None = Query(default=None, description="Tea growing area"),
    language: str = Query(default="EN", pattern="^(EN|NY)$"),
):
    """Current conditions and a 5-day forecast. Open to unauthenticated use so
    the public home page can show live weather before a farmer registers."""
    weather = await weather_service.fetch_weather(location)
    weather["summary"] = weather_service.summarise(weather, language)
    weather["alerts"] = weather_service.alerts(weather, language)
    return weather


@router.get("/mine")
async def my_weather(
    language: str | None = Query(default=None, pattern="^(EN|NY)$"),
    farmer: Farmer = Depends(get_current_farmer),
):
    """Weather for the logged-in farmer's own registered location."""
    language = language or farmer.language.value
    weather = await weather_service.fetch_weather(farmer.location)
    weather["summary"] = weather_service.summarise(weather, language)
    weather["alerts"] = weather_service.alerts(weather, language)
    return weather
