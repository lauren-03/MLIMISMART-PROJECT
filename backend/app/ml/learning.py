"""The daily learning cycle and on-demand retraining."""
import asyncio
import logging

from ..database import SessionLocal
from . import advice_model, climate, history, rain_model, store

log = logging.getLogger(__name__)

DAY_SECONDS = 24 * 60 * 60
_lock = asyncio.Lock()


def _train(which: str) -> dict:
    db = SessionLocal()
    try:
        return rain_model.train(db) if which == "rain" else advice_model.train(db)
    finally:
        db.close()


async def retrain(which: str) -> dict:
    async with _lock:
        return await asyncio.to_thread(_train, which)


async def daily_cycle() -> None:
    """New weather -> check old predictions -> retrain -> predict tomorrow."""
    db = SessionLocal()
    try:
        added = await history.update(db)
        checked = rain_model.check_past_predictions(db)
        log.info("Learning cycle: %d new weather days, %d predictions checked", added, checked)
    except Exception:  # noqa: BLE001 - keep serving with the existing models
        log.exception("Weather history update failed")
    finally:
        db.close()

    db = SessionLocal()
    try:
        log.info("Climate datasets: %s new rows", await climate.update_all(db))
    finally:
        db.close()

    for which in ("rain", "advice"):
        try:
            await retrain(which)
        except Exception:  # noqa: BLE001
            log.exception("Training the %s model failed", which)

    db = SessionLocal()
    try:
        if store.load(rain_model.NAME)[1] is not None:
            rain_model.predict_all(db)
    finally:
        db.close()


async def run_forever() -> None:
    while True:
        await daily_cycle()
        await asyncio.sleep(DAY_SECONDS)


async def after_rating() -> None:
    db = SessionLocal()
    try:
        due = advice_model.ratings_since_last_training(db) >= advice_model.RETRAIN_EVERY
    finally:
        db.close()
    if due:
        try:
            await retrain("advice")
        except Exception:  # noqa: BLE001
            log.exception("Retraining after ratings failed")
