"""Weather data from Open-Meteo, with MET Norway as a backup."""
import copy
import logging
import time
from datetime import date, datetime, timedelta, timezone

import httpx

from ..data.locations import LOCATIONS, resolve

log = logging.getLogger(__name__)

# Readings are reused for ten minutes. Weather does not change faster than
# that, and it keeps the map (23 areas) and busy SMS periods from hammering
# the free API.
CACHE_SECONDS = 600
_cache: dict[str, tuple[float, dict]] = {}
_last_good: dict[str, dict] = {}

BASE_URL = "https://api.open-meteo.com/v1/forecast"
TIMEZONE = "Africa/Blantyre"

# WMO weather interpretation codes, in both languages.
WMO_CODES: dict[int, tuple[str, str]] = {
    0: ("Clear sky", "Kumwamba kwaiyera"),
    1: ("Mainly clear", "Kwaiyera pangono"),
    2: ("Partly cloudy", "Mitambo pangono"),
    3: ("Overcast", "Mitambo yambiri"),
    45: ("Fog", "Chifunga"),
    48: ("Freezing fog", "Chifunga chozizira"),
    51: ("Light drizzle", "Chimvula chapepala"),
    53: ("Drizzle", "Chimvula"),
    55: ("Heavy drizzle", "Chimvula chambiri"),
    61: ("Light rain", "Mvula yaing ono"),
    63: ("Rain", "Mvula"),
    65: ("Heavy rain", "Mvula yaikulu"),
    80: ("Rain showers", "Mvula yamphepo"),
    81: ("Heavy showers", "Mvula yamphamvu"),
    82: ("Violent showers", "Mvula yamphamvu kwambiri"),
    95: ("Thunderstorm", "Mvula ya mabingu"),
    96: ("Thunderstorm with hail", "Mabingu ndi matalala"),
    99: ("Severe thunderstorm", "Mabingu aakulu"),
}


def describe_code(code: int | None, language: str = "EN") -> str:
    en, ny = WMO_CODES.get(code or 0, ("Unknown", "Sichidziwika"))
    return ny if language == "NY" else en


async def fetch_weather(location: str | None) -> dict:
    """Return current conditions plus a 5-day forecast for a tea district."""
    name, place = resolve(location)
    cached = _cache.get(name)
    if cached and time.monotonic() - cached[0] < CACHE_SECONDS:
        # A copy, because callers add fields such as "summary" to the result.
        return copy.deepcopy(cached[1])

    params = {
        "latitude": place["lat"],
        "longitude": place["lon"],
        "current": "temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,"
                 "precipitation_sum,precipitation_probability_max,wind_speed_10m_max",
        "timezone": TIMEZONE,
        "forecast_days": 5,
    }
    shaped = None
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            response = await client.get(BASE_URL, params=params)
            response.raise_for_status()
            payload = response.json()
        shaped = _shape(name, place, payload)
    except Exception as exc:  # noqa: BLE001 - try the backup service next
        log.warning("Open-Meteo request failed for %s: %s", name, exc)
        try:
            shaped = await _met_norway(name, place)
        except Exception as exc2:  # noqa: BLE001
            log.warning("MET Norway request failed for %s: %s", name, exc2)

    if shaped:
        _cache[name] = (time.monotonic(), shaped)
        _last_good[name] = shaped
        return copy.deepcopy(shaped)
    if name in _last_good:
        # Both services are down: show the last reading, marked as old.
        stale = copy.deepcopy(_last_good[name])
        stale["stale"] = True
        return stale
    return _offline(name, place)


async def fetch_many() -> list[dict]:
    """Today's headline weather for every area, in one Open-Meteo request.

    Open-Meteo accepts comma-separated coordinates and returns one result per
    point, so the whole map costs a single call instead of twenty-three.
    """
    cached = _cache.get("__all__")
    if cached and time.monotonic() - cached[0] < CACHE_SECONDS:
        return copy.deepcopy(cached[1]["areas"])

    names = list(LOCATIONS)
    params = {
        "latitude": ",".join(str(LOCATIONS[n]["lat"]) for n in names),
        "longitude": ",".join(str(LOCATIONS[n]["lon"]) for n in names),
        "current": "temperature_2m,relative_humidity_2m,weather_code",
        "daily": "precipitation_probability_max,temperature_2m_max,temperature_2m_min",
        "timezone": TIMEZONE,
        "forecast_days": 1,
    }
    areas = []
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(BASE_URL, params=params)
            response.raise_for_status()
            payload = response.json()
        results = payload if isinstance(payload, list) else [payload]
        for name, result in zip(names, results):
            current = result.get("current", {}) or {}
            daily = result.get("daily", {}) or {}
            areas.append(_area_row(name, {
                "temperature": current.get("temperature_2m"),
                "humidity": current.get("relative_humidity_2m"),
                "code": current.get("weather_code"),
                "rain_probability": (daily.get("precipitation_probability_max") or [None])[0],
                "temp_max": (daily.get("temperature_2m_max") or [None])[0],
                "temp_min": (daily.get("temperature_2m_min") or [None])[0],
            }))
        _cache["__all__"] = (time.monotonic(), {"areas": areas})
    except Exception as exc:  # noqa: BLE001 - fall back to one reading per area
        log.warning("Open-Meteo multi-area request failed: %s", exc)
        areas = []
        for name in names:
            w = await fetch_weather(name)
            if w["offline"]:
                areas.append(_area_row(name, None))
                continue
            today = (w["forecast"] or [{}])[0]
            c = w["current"]
            areas.append(_area_row(name, {
                "temperature": c["temperature"], "humidity": c["humidity"], "code": c["code"],
                "rain_probability": c["rain_probability"],
                "temp_max": today.get("temp_max"), "temp_min": today.get("temp_min"),
            }))
    return copy.deepcopy(areas)


def _area_row(name: str, reading: dict | None) -> dict:
    place = LOCATIONS[name]
    row = {
        "name": name,
        "district": place["district"],
        "kind": place["kind"],
        "altitude_m": place["altitude_m"],
        "latitude": place["lat"],
        "longitude": place["lon"],
        "offline": reading is None,
    }
    if reading:
        row.update(reading)
        row["condition_en"] = describe_code(reading["code"], "EN")
        row["condition_ny"] = describe_code(reading["code"], "NY")
    return row


def _shape(name: str, place: dict, payload: dict) -> dict:
    current = payload.get("current", {}) or {}
    daily = payload.get("daily", {}) or {}

    def day(key: str, index: int = 0):
        values = daily.get(key) or []
        return values[index] if index < len(values) else None

    forecast = []
    for i, day_str in enumerate(daily.get("time", [])):
        forecast.append({
            "date": day_str,
            "weekday": _weekday(day_str),
            "code": day("weather_code", i),
            "condition_en": describe_code(day("weather_code", i), "EN"),
            "condition_ny": describe_code(day("weather_code", i), "NY"),
            "temp_max": day("temperature_2m_max", i),
            "temp_min": day("temperature_2m_min", i),
            "rain_mm": day("precipitation_sum", i),
            "rain_probability": day("precipitation_probability_max", i),
            "wind_kph": day("wind_speed_10m_max", i),
        })

    return {
        "location": name,
        "district": place["district"],
        "latitude": place["lat"],
        "longitude": place["lon"],
        "offline": False,
        "source": "Open-Meteo",
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "current": {
            "temperature": current.get("temperature_2m"),
            "humidity": current.get("relative_humidity_2m"),
            "rain_mm": current.get("precipitation"),
            "wind_kph": current.get("wind_speed_10m"),
            "code": current.get("weather_code"),
            "condition_en": describe_code(current.get("weather_code"), "EN"),
            "condition_ny": describe_code(current.get("weather_code"), "NY"),
            # Today's max probability is the figure the rule engine uses.
            "rain_probability": day("precipitation_probability_max", 0),
            "rain_today_mm": day("precipitation_sum", 0),
        },
        "forecast": forecast,
    }


MET_URL = "https://api.met.no/weatherapi/locationforecast/2.0/compact"
MET_HEADERS = {"User-Agent": "MlimiSmart/1.0 (student project, github.com/lauren-03)"}
LOCAL_OFFSET = timedelta(hours=2)  # Malawi time, UTC+2

# MET Norway symbol names mapped to the WMO codes the rest of the system uses.
MET_SYMBOLS = {
    "clearsky": 0, "fair": 1, "partlycloudy": 2, "cloudy": 3, "fog": 45,
    "lightrain": 61, "rain": 63, "heavyrain": 65,
    "lightrainshowers": 80, "rainshowers": 80, "heavyrainshowers": 81,
    "lightsleet": 61, "sleet": 63, "heavysleet": 65,
}


def _met_code(symbol):
    if not symbol:
        return None
    base = symbol.split("_")[0]
    if "thunder" in base:
        return 95
    return MET_SYMBOLS.get(base, 3)


async def _met_norway(name: str, place: dict) -> dict:
    """Backup forecast from MET Norway, shaped like an Open-Meteo reading.

    MET Norway gives the expected amount of rain but no percentage chance,
    so rain_probability is left empty rather than guessed.
    """
    async with httpx.AsyncClient(timeout=15.0, headers=MET_HEADERS) as client:
        response = await client.get(MET_URL, params={"lat": round(place["lat"], 4),
                                                     "lon": round(place["lon"], 4)})
        response.raise_for_status()
        series = response.json()["properties"]["timeseries"]

    days = {}
    for entry in series:
        when = datetime.fromisoformat(entry["time"].replace("Z", "+00:00")) + LOCAL_OFFSET
        key = when.date().isoformat()
        data = entry["data"]
        details = data["instant"]["details"]
        d = days.setdefault(key, {"temps": [], "rain": 0.0, "wind": 0.0, "symbols": []})
        d["temps"].append(details.get("air_temperature"))
        d["wind"] = max(d["wind"], (details.get("wind_speed") or 0) * 3.6)
        if "next_1_hours" in data:
            d["rain"] += data["next_1_hours"]["details"].get("precipitation_amount", 0)
            if 9 <= when.hour <= 17:
                d["symbols"].append(data["next_1_hours"]["summary"]["symbol_code"])
        elif "next_6_hours" in data:
            d["rain"] += data["next_6_hours"]["details"].get("precipitation_amount", 0)
            d["symbols"].append(data["next_6_hours"]["summary"]["symbol_code"])

    forecast = []
    for key in sorted(days)[:5]:
        d = days[key]
        temps = [t for t in d["temps"] if t is not None]
        codes = [c for c in (_met_code(x) for x in d["symbols"]) if c is not None]
        code = max(codes) if codes else None   # the wettest weather of the day
        forecast.append({
            "date": key,
            "weekday": _weekday(key),
            "code": code,
            "condition_en": describe_code(code, "EN"),
            "condition_ny": describe_code(code, "NY"),
            "temp_max": round(max(temps), 1) if temps else None,
            "temp_min": round(min(temps), 1) if temps else None,
            "rain_mm": round(d["rain"], 1),
            "rain_probability": None,
            "wind_kph": round(d["wind"], 1),
        })

    now = series[0]["data"]
    details = now["instant"]["details"]
    nxt = now.get("next_1_hours") or now.get("next_6_hours") or {}
    code = _met_code(nxt.get("summary", {}).get("symbol_code"))
    return {
        "location": name,
        "district": place["district"],
        "latitude": place["lat"],
        "longitude": place["lon"],
        "offline": False,
        "source": "MET Norway",
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "current": {
            "temperature": details.get("air_temperature"),
            "humidity": details.get("relative_humidity"),
            "rain_mm": nxt.get("details", {}).get("precipitation_amount"),
            "wind_kph": round((details.get("wind_speed") or 0) * 3.6, 1),
            "code": code,
            "condition_en": describe_code(code, "EN"),
            "condition_ny": describe_code(code, "NY"),
            "rain_probability": None,
            "rain_today_mm": forecast[0]["rain_mm"] if forecast else None,
        },
        "forecast": forecast,
    }


def _offline(name: str, place: dict) -> dict:
    """A reading marked offline, with no invented values."""
    return {
        "location": name,
        "district": place["district"],
        "latitude": place["lat"],
        "longitude": place["lon"],
        "offline": True,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "current": {
            "temperature": None, "humidity": None, "rain_mm": None,
            "wind_kph": None, "code": None,
            "condition_en": "Weather unavailable", "condition_ny": "Nyengo sikupezeka",
            "rain_probability": None, "rain_today_mm": None,
        },
        "forecast": [],
    }


def _weekday(day_str: str) -> str:
    try:
        return date.fromisoformat(day_str).strftime("%a")
    except ValueError:
        return ""


def summarise(weather: dict, language: str = "EN") -> str:
    """One-line weather summary for embedding in advice and SMS replies."""
    current = weather["current"]
    if weather["offline"]:
        return "Weather data unavailable" if language == "EN" else "Nyengo sikupezeka"
    condition = current["condition_ny"] if language == "NY" else current["condition_en"]
    temp = current["temperature"]
    probability = current["rain_probability"]
    if probability is None:
        mm = current.get("rain_today_mm") or 0
        if language == "NY":
            return f"{condition}, {temp}C, mvula lero {mm} mm"
        return f"{condition}, {temp}C, rain today {mm} mm"
    if language == "NY":
        return f"{condition}, {temp}C, mwayi wa mvula {probability}%"
    return f"{condition}, {temp}C, rain chance {probability}%"


# ---------------------------------------------------------------------------
# Weather alerts
# ---------------------------------------------------------------------------
# Thresholds are shared with the advisory engine so an alert and the advice
# beneath it can never disagree about what counts as "heavy rain".
COLD_NIGHT = 6.0    # degrees C: cold damage risk in low-lying fields
DRY_SPELL_MM = 2.0  # total rain over the forecast below which it is a dry spell

ALERT_TEXT = {
    "heavy_rain": (
        "Heavy rain {day}",
        "Mvula yamphamvu {day}",
        "Up to {mm} mm of rain expected. Do not apply fertilizer - it will wash away. Clear your drains.",
        "Mvula yokwana {mm} mm ikuyembekezeka. Musathire fetereza - ikokoloka. Konzani ngalande.",
    ),
    "rain_likely": (
        "Rain likely {day}",
        "Mvula ikhoza kugwa {day}",
        "{p}% chance of rain. Plan plucking early in the day and keep fertilizer covered.",
        "Mwayi wa mvula ndi {p}%. Thyolani m'mawa ndipo phimbani fetereza.",
    ),
    "heat": (
        "Hot day {day}",
        "Kutentha kwambiri {day}",
        "Up to {t}C. Mulch around young plants, water them if you can and do not prune today.",
        "Kutentha kufika {t}C. Ikani malichi kuzungulira mbande, zithirireni ngati mungathe ndipo musateme lero.",
    ),
    "wind": (
        "Strong wind {day}",
        "Mphepo yamphamvu {day}",
        "Wind up to {w} km/h can break young shoots. Check shade trees for loose branches.",
        "Mphepo yofika {w} km/h ikhoza kuthyola mphukira. Yang'anani nthambi zomasuka za mitengo yamthunzi.",
    ),
    "cold": (
        "Cold night {day}",
        "Usiku wozizira {day}",
        "Down to {t}C. Low-lying fields may get cold damage; do not prune those fields this week.",
        "Kuzizira kufika {t}C. Minda ya m'zigwa ikhoza kuonongeka; musateme minda imeneyo sabata ino.",
    ),
    "disease": (
        "Damp and humid",
        "Chinyezi chambiri",
        "Humidity is {h}%. Leaf diseases spread fast in these conditions - check your bushes.",
        "Chinyezi ndi {h}%. Matenda a masamba amafalikira msanga nyengo yotere - yang'anani zitsamba zanu.",
    ),
    "dry_spell": (
        "Dry spell ahead",
        "Chilala chikubwera",
        "Almost no rain in the next {n} days. Mulch the soil and watch mature leaves for red spider mite.",
        "Mvula yochepa kwambiri masiku {n} akubwerawa. Ikani malichi ndipo yang'anani nthata zofiira pa masamba akulu.",
    ),
}

ALERT_LEVEL = {
    "heavy_rain": "urgent", "rain_likely": "info", "heat": "caution",
    "wind": "caution", "cold": "caution", "disease": "caution", "dry_spell": "caution",
}

ALERT_ICON = {
    "heavy_rain": "cloud-lightning-rain", "rain_likely": "cloud-drizzle",
    "heat": "thermometer-sun", "wind": "wind", "cold": "thermometer-snow",
    "disease": "droplet-half", "dry_spell": "sun",
}


def alerts(weather: dict, language: str = "EN", days: int = 3) -> list[dict]:
    """Warnings a farmer should act on, from the next few days' forecast.

    Each kind of alert is raised once, for the first day it applies, so the
    list stays short enough to read at a glance and to fit in an SMS.
    """
    from .advisory_engine import (
        HEAVY_RAIN_MM, HEAVY_RAIN_PROBABILITY, HIGH_HUMIDITY, HOT_TEMPERATURE,
        STRONG_WIND_KPH,
    )

    if weather.get("offline"):
        return []

    ny = language == "NY"
    forecast = weather.get("forecast") or []
    raised: dict[str, dict] = {}

    def add(kind: str, index: int, **values) -> None:
        if kind in raised:
            return
        title_en, title_ny, text_en, text_ny = ALERT_TEXT[kind]
        day = _day_word(forecast[index], index, language) if index is not None else ""
        raised[kind] = {
            "kind": kind,
            "level": ALERT_LEVEL[kind],
            "icon": ALERT_ICON[kind],
            "date": forecast[index]["date"] if index is not None else None,
            "title": (title_ny if ny else title_en).format(day=day).strip(),
            "text": (text_ny if ny else text_en).format(**values),
        }

    for i, item in enumerate(forecast[:days]):
        p = item.get("rain_probability") or 0
        mm = item.get("rain_mm") or 0
        if p >= HEAVY_RAIN_PROBABILITY and mm >= HEAVY_RAIN_MM:
            add("heavy_rain", i, mm=round(mm))
        elif p >= HEAVY_RAIN_PROBABILITY:
            add("rain_likely", i, p=p)
        if (item.get("temp_max") or 0) >= HOT_TEMPERATURE:
            add("heat", i, t=round(item["temp_max"]))
        if (item.get("wind_kph") or 0) >= STRONG_WIND_KPH:
            add("wind", i, w=round(item["wind_kph"]))
        if item.get("temp_min") is not None and item["temp_min"] <= COLD_NIGHT:
            add("cold", i, t=round(item["temp_min"]))

    humidity = weather["current"].get("humidity")
    if humidity is not None and humidity >= HIGH_HUMIDITY:
        add("disease", None, h=humidity)

    if forecast and sum((d.get("rain_mm") or 0) for d in forecast) < DRY_SPELL_MM \
            and max((d.get("temp_max") or 0) for d in forecast) >= 26:
        add("dry_spell", None, n=len(forecast))

    order = {"urgent": 0, "caution": 1, "info": 2}
    return sorted(raised.values(), key=lambda a: order[a["level"]])


def _day_word(item: dict, index: int, language: str) -> str:
    if index == 0:
        return "lero" if language == "NY" else "today"
    if index == 1:
        return "mawa" if language == "NY" else "tomorrow"
    return f"({item.get('weekday', '')})" if language == "NY" else f"on {item.get('weekday', '')}"
