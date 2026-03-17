"""
Scrape champion prestige data from mcochub.insaneskull.com.
Fetches HTML tables for 7-star Rank 3/4/5 and parses prestige values.
"""
import json
import logging
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

logger = logging.getLogger("mcoc-prestige")

BASE_URL = "https://mcochub.insaneskull.com/prestige"
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
}

# tier, rank pairs to fetch
RANKS_TO_FETCH = [
    (7, 5),
    (7, 4),
    (7, 3),
]


def _fetch_prestige_page(tier, rank):
    """Fetch prestige HTML page for a given tier and rank."""
    params = {"tier": tier, "rank": rank}
    url = f"{BASE_URL}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "MCOCTierList/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode()


def _parse_prestige_table(html):
    """Parse champion prestige data from HTML table.

    Returns dict: {champion_name: [sig0, sig20, ..., sig200]}
    """
    result = {}

    # Find tbody content
    tbody_match = re.search(r"<tbody[^>]*>(.*?)</tbody>", html, re.DOTALL)
    if not tbody_match:
        return result

    tbody = tbody_match.group(1)
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", tbody, re.DOTALL)

    for row in rows:
        # Extract champion name from img alt attribute
        name_match = re.search(r'alt="([^"]+)"', row)
        if not name_match:
            continue
        name = name_match.group(1).strip()

        # Extract all td numeric values
        tds = re.findall(r"<td[^>]*>\s*(\d+)\s*</td>", row)
        # tds: [rank#, tier, rank, sig0, sig20, ..., sig200] = 14 values
        # or on mobile view some hidden, but we get all from HTML
        if len(tds) < 14:
            continue

        # Skip first 3 (rank#, tier, rank), take 11 sig values
        try:
            values = [int(v) for v in tds[3:14]]
        except ValueError:
            continue

        if len(values) == 11:
            name = NAME_MAP.get(name, name)
            result[name] = values

    return result


def fetch_prestige_data():
    """Fetch all prestige data from mcochub.

    Returns dict: {"7-5": {name: [vals]}, "7-4": {...}, "7-3": {...}}
    """
    prestige = {}

    for tier, rank in RANKS_TO_FETCH:
        key = f"{tier}-{rank}"
        try:
            html = _fetch_prestige_page(tier, rank)
            data = _parse_prestige_table(html)
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
