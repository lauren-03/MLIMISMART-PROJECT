"""MlimiSmart API entry point."""
import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from .database import active_database_url, init_db
from .ml import learning
from .services import sms_service, speech_service, tunnel
from .routers import (
    admin, advisory, auth, db_browser, farm, models_admin, sms, speech, ussd, weather,
)
from .services.intent_model import classifier

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s %(name)s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("mlimismart")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create the tables, train the topic classifier, start the learning cycle."""
    init_db()
    log.info("Database ready: %s", active_database_url.split("@")[-1])
    _restore_models()
    classifier.train()
    cycle = asyncio.create_task(learning.run_forever())
    gateways = asyncio.create_task(_connect_gateways())
    speech_service.warm_up()
    log.info("MlimiSmart API is ready")
    yield
    cycle.cancel()
    gateways.cancel()
    await tunnel.stop()


def _restore_models() -> None:
    """Bring the approved models back after a deployment.

    Render starts each deployment with an empty ml_store/ directory. The
    approved model bytes are kept in the database, so they are written back
    to disk here, before the first farmer request arrives. A failure is
    logged and not raised: the site must still serve rules-based advice.
    """
    from .database import SessionLocal
    from .ml import store

    db = SessionLocal()
    try:
        restored = store.restore_all(db)
        log.info("Models restored from the database: %s", restored or "none needed")
    except Exception:  # noqa: BLE001 - never block startup on this
        log.exception("Could not restore models from the database")
    finally:
        db.close()


async def _connect_gateways() -> None:
    """Open the public address and tell the SMS phone where to forward texts."""
    url = await tunnel.start()
    if url:
        log.info("USSD callback for Africa's Talking: %s/api/ussd", url)
        await sms_service.register_android_webhook(url)


app = FastAPI(
    title="MlimiSmart API",
    description=(
        "AI-based advisory system for smallholder tea farmers in Malawi. "
        "Serves the React web application, the SMS channel and the USSD menu, "
        "with Google Gemini for natural Chichewa/English wording."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# The Vite dev server runs on 5173. Both loopback spellings are allowed because
# the browser may resolve either.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", "http://127.0.0.1:5173",
        "http://localhost:4173", "http://127.0.0.1:4173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(weather.router)
app.include_router(advisory.router)
app.include_router(sms.router)
app.include_router(ussd.router)
app.include_router(farm.router)
app.include_router(admin.router)
app.include_router(db_browser.router)
app.include_router(models_admin.router)
app.include_router(speech.router)


@app.get("/api", tags=["health"])
def root():
    return {
        "system": "MlimiSmart",
        "description": "AI-based advisory system for smallholder tea farmers in Malawi",
        "version": "1.0.0",
        "docs": "/docs",
        "modules": [
            "Farmer Management", "Weather", "AI Advisory",
            "SMS Advisory", "USSD Advisory",
            "Language (English/Chichewa)", "Admin",
            "Tea Calendar", "Harvest Diary", "Weather Alerts",
        ],
    }


@app.get("/api/health", tags=["health"])
def health():
    return {
        "status": "ok",
        "database": "mysql" if active_database_url.startswith("mysql") else "sqlite",
        "classifier_trained": classifier.pipeline is not None,
    }


# Online, the built website is served by the API itself, so the site and the
# API share one address. Locally the Vite dev server is used instead.
WEBSITE = Path(__file__).resolve().parents[2] / "frontend" / "dist"

if WEBSITE.is_dir():
    @app.get("/{path:path}", include_in_schema=False)
    def website(path: str):
        if path.startswith("api/") or path == "api":
            raise HTTPException(status_code=404)
        file = (WEBSITE / path).resolve()
        if path and file.is_file() and WEBSITE in file.parents:
            return FileResponse(file)
        return FileResponse(WEBSITE / "index.html")

