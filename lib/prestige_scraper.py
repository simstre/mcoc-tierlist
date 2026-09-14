"""
Fetch champion prestige data from mcochub.insaneskull.com.
Reads the JSON feed behind their prestige table for 7-star Rank 3/4/5.

The page itself renders its table client-side from /data/prestige.json, so
there is no server-rendered HTML to parse — the same JSON the page fetches is
requested directly here.
"""
import json
import logging
import time
import urllib.parse
import urllib.request
from pathlib import Path

logger = logging.getLogger("mcoc-prestige")

# The endpoint the prestige page's own JS calls, one slice per tier/rank.
DATA_URL = "https://mcochub.insaneskull.com/data/prestige.json"
CACHE_PATH = Path(__file__).parent / "cached_prestige.json"

SIG_LEVELS = [0, 20, 40, 60, 80, 100, 120, 140, 160, 180, 200]

PRESTIGE_OPTIONS = [
    {"label": "7\u2605 Rank 5", "key": "7-5"},
    {"label": "7\u2605 Rank 4", "key": "7-4"},
    {"label": "7\u2605 Rank 3", "key": "7-3"},
]

# mcochub name -> canonical tier list name
NAME_MAP = {
    "QuickSilver": "Quicksilver",
    "Howard The Duck": "Howard the Duck",
    "Venom The Duck": "Venom the Duck",
    "Shang Chi": "Shang-Chi",
    "Spider Man 2099": "Spider-Man 2099",
    "Spider man (Miles Morales)": "Spider-Man (Miles Morales)",
    "Spider Man (Stark Enhanced)": "Spider-Man (Stark Enhanced)",
    "Wolverine (X 23)": "Wolverine (X-23)",
    "Platinum Pool": "Platinumpool",
    "Falcon (Joaquin Torres)": "Falcon (Joaqu\u00edn Torres)",
    "Star-Lord (Stellar Forged)": "Star-Lord (Stellar-Forged)",
    "Spider-Man (Stealth-Suit)": "Spider-Man (Stealth Suit)",
    "Spider-Woman": "Spider-Woman (Jessica Drew)",
    "Kang the Conqueror": "Kang",
    "Spider-Man (Classic)": "Spider-Man",
    "Daredevil (Classic)": "Daredevil",
    "Jack O\u2019Lantern": "Jack O'Lantern",
    "M\u2019Baku": "M'Baku",
    "Blade (Stellar Forged)": "Blade (Stellar Forge)",
    "Hobgoblin (Phil Urich)": "Hobgoblin",
    "Scarlet Witch (Sigil)": "Scarlet Witch",
    # mcochub only lists 7-star champions, and Captain Marvel (Classic) has no
    # 7-star version, so their plain "Captain Marvel" is the movie one.
    "Captain Marvel": "Captain Marvel (Movie)",
}

# tier, rank pairs to fetch
RANKS_TO_FETCH = [
    (7, 5),
    (7, 4),
    (7, 3),
]


def _fetch_prestige_slice(tier, rank):
    """Fetch the prestige JSON for one tier/rank (ascension 0)."""
    params = {"tier": tier, "rank": rank, "ascension": 0}
    url = f"{DATA_URL}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "MCOCTierList/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def _parse_prestige_rows(payload):
    """Pull champion prestige values out of one JSON slice.

    Each row carries a `sigs` map keyed by signature level ("0".."200").
    Returns dict: {champion_name: [sig0, sig20, ..., sig200]}
    """
    result = {}

    for row in payload.get("rows") or []:
        name = (row.get("name") or "").strip()
        sigs = row.get("sigs") or {}
        if not name:
            continue

        try:
            values = [int(sigs[str(level)]) for level in SIG_LEVELS]
        except (KeyError, TypeError, ValueError):
            continue

        result[NAME_MAP.get(name, name)] = values

    return result


def fetch_prestige_data():
    """Fetch all prestige data from mcochub.

    Returns dict: {"7-5": {name: [vals]}, "7-4": {...}, "7-3": {...}}
    """
    prestige = {}

    for tier, rank in RANKS_TO_FETCH:
        key = f"{tier}-{rank}"
        try:
            payload = _fetch_prestige_slice(tier, rank)
            data = _parse_prestige_rows(payload)
            prestige[key] = data
            logger.info(f"Fetched prestige {key}: {len(data)} champions")
            time.sleep(0.5)
        except Exception as e:
            logger.warning(f"Failed to fetch prestige {key}: {e}")
            prestige[key] = {}

    return prestige


def fetch_and_cache_prestige():
    """Fetch prestige data and cache to disk."""
    prestige = fetch_prestige_data()
    total = sum(len(v) for v in prestige.values())
    if total > 0:
        CACHE_PATH.write_text(json.dumps(prestige, indent=2))
        logger.info(f"Cached prestige data: {total} total entries")
    return prestige


def load_cached_prestige():
    """Load cached prestige data."""
    if CACHE_PATH.exists():
        try:
            return json.loads(CACHE_PATH.read_text())
        except Exception as e:
            logger.error(f"Failed to load prestige cache: {e}")
    return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    prestige = fetch_and_cache_prestige()
    for key, data in prestige.items():
        if data:
            first = next(iter(data.items()))
            print(f"  {key}: {len(data)} champions (e.g. {first[0]}: {first[1]})")
