import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from champions_data import (
    compute_tier_list, get_champions_by_class,
    SOURCES, CLASS_COLORS, TIER_COLORS, TAG_LABELS,
)
from fetch_tierlist import fetch_and_cache, load_cached
from immunities import CHAMPION_IMMUNITIES, get_immunity_map, IMMUNITY_TYPES
from prestige_data import PRESTIGE, SIG_LEVELS, PRESTIGE_OPTIONS

PORT = int(os.environ.get("PORT", 8100))
BASE_DIR = Path(__file__).parent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcoc-updater")

# ── Portraits ──
_portraits = {}
for _pfile in ["portraits.json", "portraits_local.json", "mcochub_portraits.json"]:
    _ppath = BASE_DIR / _pfile
    if _ppath.exists():
        _portraits.update(json.loads(_ppath.read_text()))

# ── Champion data (mutable, refreshed daily) ──
_raw_champions = {}
_source_meta = []
_awakening_data = {}
_sig_stones_data = {}
_last_updated = "March 7, 2026"

scheduler = BackgroundScheduler()


def _refresh_tierlist():
    """Fetch fresh tier list data from Google Sheets."""
    global _raw_champions, _source_meta, _awakening_data, _sig_stones_data, _last_updated
    logger.info("Fetching tier list data from sheets...")
    data, meta, aw, sig = fetch_and_cache()
    if meta:
        _source_meta = meta
    if aw:
        _awakening_data = aw
    if sig:
        _sig_stones_data = sig
    if data:
        _raw_champions = data
        _last_updated = datetime.now(timezone.utc).strftime("%B %d, %Y")
        logger.info(f"Tier list updated: {len(data)} champions")
    else:
        logger.warning("Sheet fetch failed, keeping existing data")


def _refresh_portraits():
    """Fetch any missing portraits from wiki/mcochub."""
    from fetch_portraits import fetch_missing_portraits
    try:
        global _portraits
        result = fetch_missing_portraits(list(_raw_champions.keys()))
        _portraits.update(result)
        logger.info("Portrait update complete.")
    except Exception as e:
        logger.error(f"Portrait update failed: {e}")


def daily_update():
    """Scheduled task: refresh tier list + portraits."""
    logger.info("Running daily update...")
    _refresh_tierlist()
    _refresh_portraits()
    logger.info("Daily update complete.")


@asynccontextmanager
async def lifespan(app):
    # Load data: try fresh fetch, fall back to cache
    global _raw_champions, _source_meta, _awakening_data, _sig_stones_data
    data, meta, aw, sig = fetch_and_cache()
    if meta:
        _source_meta = meta
    if aw:
        _awakening_data = aw
    if sig:
        _sig_stones_data = sig
    if data:
        _raw_champions = data
        logger.info(f"Loaded {len(data)} champions from sheets")
    else:
        data, meta, aw, sig = load_cached()
        if meta:
            _source_meta = meta
        if aw:
            _awakening_data = aw
        if sig:
            _sig_stones_data = sig
        if data:
            _raw_champions = data
            logger.info(f"Loaded {len(data)} champions from cache")
        else:
            logger.error("No champion data available!")

    scheduler.add_job(daily_update, "cron", hour=6, minute=0, id="daily_update")
    scheduler.start()
    logger.info("Scheduler started - daily update at 06:00")
    yield
    scheduler.shutdown()


app = FastAPI(title="MCOC Tier List", lifespan=lifespan)


@app.get("/api/tierlist")
def get_tierlist():
    champions = compute_tier_list(_raw_champions)
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
        "tag_labels": TAG_LABELS,
        "immunity_map": get_immunity_map(),
        "immunity_types": IMMUNITY_TYPES,
        "awakening_data": _awakening_data,
        "sig_stones_data": _sig_stones_data,
        "prestige": PRESTIGE,
        "prestige_sig_levels": SIG_LEVELS,
        "prestige_options": PRESTIGE_OPTIONS,
        "prestige_portraits": _portraits,
        "source_meta": _source_meta,
        "last_updated": _last_updated,
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
