"""Climate datasets used as extra model inputs: ERA5-Land, NASA POWER and CHIRPS."""
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import date, timedelta

import httpx
from sqlalchemy import func, insert, select
from sqlalchemy.orm import Session

from ..data.locations import LOCATIONS
from ..models import ChirpsMonthly, NasaPower, SoilMoisture

log = logging.getLogger(__name__)

FIRST_DAY = date(2016, 1, 1)
ERA5_URL = "https://archive-api.open-meteo.com/v1/archive"
POWER_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
CHIRPS_URL = ("https://data.chc.ucsb.edu/products/CHIRPS/v3.0/monthly/africa/tifs/"
              "chirps-v3.0.{year}.{month:02d}.tif")

# Each dataset is published a few days (or months) late. Features always use
# data this old, so training and live predictions see the same thing.
SOIL_LAG_DAYS = 6
POWER_LAG_DAYS = 4
CHIRPS_LAG_MONTHS = 2

FEATURES = ["soil_top", "soil_root", "power_rain", "solar", "root_wetness",
            "chirps_rain", "chirps_anomaly"]


def _latest(db: Session, model, column) -> dict[str, date]:
    rows = db.execute(select(model.location, func.max(column)).group_by(model.location)).all()
    return {name: day for name, day in rows}


def _start(latest: dict[str, date]) -> date:
    return min((latest.get(n, FIRST_DAY - timedelta(days=1)) for n in LOCATIONS)) + timedelta(days=1)


async def update_soil(db: Session) -> int:
    """ERA5-Land soil moisture, through the Open-Meteo archive."""
    latest = _latest(db, SoilMoisture, SoilMoisture.day)
    start, end = _start(latest), date.today()
    if start > end:
        return 0
    names = list(LOCATIONS)
    params = {
        "latitude": ",".join(str(LOCATIONS[n]["lat"]) for n in names),
        "longitude": ",".join(str(LOCATIONS[n]["lon"]) for n in names),
        "start_date": start.isoformat(), "end_date": end.isoformat(),
        "daily": "soil_moisture_0_to_7cm_mean,soil_moisture_7_to_28cm_mean",
        "models": "era5_land", "timezone": "Africa/Blantyre",
    }
    async with httpx.AsyncClient(timeout=300) as client:
        response = await client.get(ERA5_URL, params=params)
        response.raise_for_status()
        payload = response.json()
    results = payload if isinstance(payload, list) else [payload]

    rows = []
    for name, result in zip(names, results):
        daily = result.get("daily") or {}
        since = latest.get(name)
        for day_text, top, root in zip(daily.get("time", []),
                                       daily.get("soil_moisture_0_to_7cm_mean", []),
                                       daily.get("soil_moisture_7_to_28cm_mean", [])):
            day = date.fromisoformat(day_text)
            if top is None or (since and day <= since):
                continue
            rows.append({"location": name, "day": day, "top": top, "root": root})
    if rows:
        db.execute(insert(SoilMoisture), rows)
    db.commit()
    log.info("ERA5-Land soil moisture: %d new days", len(rows))
    return len(rows)


def _clean(value):
    return None if value is None or value == -999 else value


async def update_power(db: Session) -> int:
    """NASA POWER daily rainfall, solar radiation and root-zone wetness."""
    latest = _latest(db, NasaPower, NasaPower.day)
    end = date.today()
    sem = asyncio.Semaphore(4)

    async def fetch(client, name):
        start = latest.get(name, FIRST_DAY - timedelta(days=1)) + timedelta(days=1)
        if start > end:
            return []
        place = LOCATIONS[name]
        params = {"parameters": "PRECTOTCORR,ALLSKY_SFC_SW_DWN,GWETROOT", "community": "AG",
                  "latitude": place["lat"], "longitude": place["lon"],
                  "start": start.strftime("%Y%m%d"), "end": end.strftime("%Y%m%d"), "format": "JSON"}
        async with sem:
            response = await client.get(POWER_URL, params=params)
        response.raise_for_status()
        data = response.json()["properties"]["parameter"]
        out = []
        for key, rain in data["PRECTOTCORR"].items():
            solar, wet = data["ALLSKY_SFC_SW_DWN"].get(key), data["GWETROOT"].get(key)
            if _clean(rain) is None and _clean(solar) is None and _clean(wet) is None:
                continue
            out.append({"location": name, "day": date(int(key[:4]), int(key[4:6]), int(key[6:])),
                        "rain_mm": _clean(rain), "solar": _clean(solar), "root_wetness": _clean(wet)})
        return out

    async with httpx.AsyncClient(timeout=300) as client:
        batches = await asyncio.gather(*(fetch(client, n) for n in LOCATIONS))
    rows = [row for batch in batches for row in batch]
    if rows:
        db.execute(insert(NasaPower), rows)
    db.commit()
    log.info("NASA POWER: %d new days", len(rows))
    return len(rows)


def _month_add(month: date, n: int) -> date:
    index = month.year * 12 + month.month - 1 + n
    return date(index // 12, index % 12 + 1, 1)


def _read_chirps(month: date) -> list[float | None] | None:
    """Rainfall for every area in one month, read straight from the CHIRPS file."""
    import rasterio
    from rasterio.env import Env
    from rasterio.errors import RasterioIOError

    url = "/vsicurl/" + CHIRPS_URL.format(year=month.year, month=month.month)
    points = [(p["lon"], p["lat"]) for p in LOCATIONS.values()]
    for _ in range(3):
        try:
            with Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", GDAL_HTTP_TIMEOUT="60"):
                with rasterio.open(url) as src:
                    return [None if v[0] < 0 else round(float(v[0]), 1) for v in src.sample(points)]
        except RasterioIOError as exc:
            if "404" in str(exc) or "does not exist" in str(exc):
                return None
    return None


def update_chirps(db: Session) -> int:
    """CHIRPS monthly rainfall for the months not yet stored."""
    have = set(db.scalars(select(ChirpsMonthly.month).distinct()).all())
    first = date(FIRST_DAY.year, FIRST_DAY.month, 1)
    last = _month_add(date.today().replace(day=1), -1)
    months, m = [], first
    while m <= last:
        if m not in have:
            months.append(m)
        m = _month_add(m, 1)
    if not months:
        return 0
    with ThreadPoolExecutor(max_workers=4) as pool:
        values = list(pool.map(_read_chirps, months))
    rows = [{"location": name, "month": month, "rain_mm": v}
            for month, vals in zip(months, values) if vals
            for name, v in zip(LOCATIONS, vals)]
    if rows:
        db.execute(insert(ChirpsMonthly), rows)
    db.commit()
    log.info("CHIRPS: %d new months", len(rows) // max(len(LOCATIONS), 1))
    return len(rows)


def _chirps_job() -> int:
    from ..database import SessionLocal
    db = SessionLocal()
    try:
        return update_chirps(db)
    finally:
        db.close()


async def update_all(db: Session) -> dict:
    added = {}
    for name, job in (("soil", update_soil), ("power", update_power)):
        try:
            added[name] = await job(db)
        except Exception:  # noqa: BLE001 - one source failing must not stop the others
            db.rollback()
            log.exception("%s update failed", name)
    try:
        added["chirps"] = await asyncio.to_thread(_chirps_job)
    except Exception:  # noqa: BLE001
        log.exception("CHIRPS update failed")
    return added


@dataclass
class Climate:
    """All three datasets in memory, for building model features quickly."""
    soil: dict = field(default_factory=dict)
    power: dict = field(default_factory=dict)
    chirps: dict = field(default_factory=dict)
    normals: dict = field(default_factory=dict)

    def _back(self, table: dict, name: str, day: date, lag: int):
        for extra in range(5):
            value = table.get((name, day - timedelta(days=lag + extra)))
            if value is not None:
                return value
        return None

    def features(self, name: str, day: date) -> list[float]:
        nan = float("nan")
        soil = self._back(self.soil, name, day, SOIL_LAG_DAYS) or (None, None)
        power = self._back(self.power, name, day, POWER_LAG_DAYS) or (None, None, None)
        month = _month_add(day.replace(day=1), -CHIRPS_LAG_MONTHS)
        rain = self.chirps.get((name, month))
        normal = self.normals.get((name, month.month))
        return [
            *(nan if v is None else v for v in soil),
            *(nan if v is None else v for v in power),
            nan if rain is None else rain,
            nan if rain is None or normal is None else rain - normal,
        ]

    def soil_top(self, name: str, day: date) -> float | None:
        value = self._back(self.soil, name, day, SOIL_LAG_DAYS)
        return value[0] if value else None

    def chirps_anomaly(self, name: str, day: date) -> float | None:
        month = _month_add(day.replace(day=1), -CHIRPS_LAG_MONTHS)
        rain, normal = self.chirps.get((name, month)), self.normals.get((name, month.month))
        return None if rain is None or normal is None else rain - normal


def load(db: Session, location: str | None = None, since: date | None = None) -> Climate:
    clim = Climate()
    q_soil = select(SoilMoisture.location, SoilMoisture.day, SoilMoisture.top, SoilMoisture.root)
    q_power = select(NasaPower.location, NasaPower.day, NasaPower.rain_mm, NasaPower.solar,
                     NasaPower.root_wetness)
    if location:
        q_soil = q_soil.where(SoilMoisture.location == location)
        q_power = q_power.where(NasaPower.location == location)
    if since:
        q_soil = q_soil.where(SoilMoisture.day >= since)
        q_power = q_power.where(NasaPower.day >= since)
    clim.soil = {(n, d): (t, r) for n, d, t, r in db.execute(q_soil)}
    clim.power = {(n, d): (r, s, w) for n, d, r, s, w in db.execute(q_power)}

    totals: dict = {}
    for name, month, rain in db.execute(select(ChirpsMonthly.location, ChirpsMonthly.month,
                                               ChirpsMonthly.rain_mm)):
        clim.chirps[(name, month)] = rain
        if rain is not None:
            totals.setdefault((name, month.month), []).append(rain)
    clim.normals = {key: sum(v) / len(v) for key, v in totals.items()}
    return clim
