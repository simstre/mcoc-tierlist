import json
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from champions_data import (
    compute_tier_list, get_champions_by_class,
    SOURCES, CLASS_COLORS, TIER_COLORS, RAW_CHAMPIONS,
)
from immunities import CHAMPION_IMMUNITIES, get_immunity_map, IMMUNITY_TYPES
from sig_stones import SIG_STONE_DATA, SIG_PRIORITY_ORDER, SIG_PRIORITY_COLORS

PORT = int(os.environ.get("PORT", 8100))
BASE_DIR = Path(__file__).parent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcoc-updater")

_portraits = {}
_portraits_path = BASE_DIR / "portraits_local.json"
if _portraits_path.exists():
    _portraits = json.loads(_portraits_path.read_text())


scheduler = BackgroundScheduler()


def daily_update():
    """Scheduled task: download any missing portraits."""
    from update import update_portraits
    logger.info("Running daily update...")
    try:
        global _portraits
        _portraits = update_portraits(list(RAW_CHAMPIONS.keys()))
        logger.info("Daily update complete.")
    except Exception as e:
        logger.error(f"Daily update failed: {e}")


@asynccontextmanager
async def lifespan(app):
    scheduler.add_job(daily_update, "cron", hour=6, minute=0, id="daily_update")
    scheduler.start()
    logger.info("Scheduler started — daily update at 06:00")
    yield
    scheduler.shutdown()


app = FastAPI(title="MCOC Tier List", lifespan=lifespan)


@app.get("/api/tierlist")
def get_tierlist():
    champions = compute_tier_list()
    for c in champions:
        c["portrait"] = _portraits.get(c["name"])
        c["immunities"] = CHAMPION_IMMUNITIES.get(c["name"], [])
    by_class = get_champions_by_class(champions)
    return {
        "champions": champions,
        "by_class": by_class,
        "sources": SOURCES,
        "class_colors": CLASS_COLORS,
        "tier_colors": TIER_COLORS,
        "immunity_map": get_immunity_map(),
        "immunity_types": IMMUNITY_TYPES,
        "sig_stone_data": SIG_STONE_DATA,
        "sig_priority_order": SIG_PRIORITY_ORDER,
        "sig_priority_colors": SIG_PRIORITY_COLORS,
        "last_updated": "December 21, 2025",
        "total_champions": len(champions),
    }


app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def root():
    return FileResponse("static/index.html")


@app.get("/immunity-map")
def immunity_map():
    return FileResponse("static/immunities.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
