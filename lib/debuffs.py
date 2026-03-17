"""
Fetch champion debuff infliction data from Fandom wiki categories.
Maps which champions inflict each debuff type.
"""
import json
import logging
import time
import urllib.parse
import urllib.request
from pathlib import Path

logger = logging.getLogger("mcoc-debuffs")

WIKI_API = "https://marvel-contestofchampions.fandom.com/api.php"
CACHE_PATH = Path(__file__).parent / "cached_debuffs.json"

# Category name on wiki -> display name
DEBUFF_CATEGORIES = {
    "Bleed": "Bleed",
    "Poison": "Poison",
    "Incinerate": "Incinerate",
    "Shock": "Shock",
    "Coldsnap": "Coldsnap",
    "Frostbite": "Frostbite",
    "Nullify": "Nullify",
    "Stagger": "Stagger",
    "Armor_Break": "Armor Break",
    "Fate_Seal": "Fate Seal",
    "Heal_Block": "Heal Block",
    "Power_Drain": "Power Drain",
    "Power_Lock": "Power Lock",
    "Power_Burn": "Power Burn",
    "Stun": "Stun",
    "Degeneration": "Degeneration",
}


def _fetch_category_members(category):
    """Fetch all champion page titles from a wiki category."""
    members = []
    cmcontinue = None

    while True:
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": f"Category:{category}",
            "cmlimit": "500",
            "cmtype": "page",
            "format": "json",
        }
        if cmcontinue:
            params["cmcontinue"] = cmcontinue

        url = f"{WIKI_API}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={"User-Agent": "MCOCTierList/1.0"})

        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())

        for member in data.get("query", {}).get("categorymembers", []):
            title = member.get("title", "")
            # Skip non-champion pages (categories, templates, etc.)
            if ":" in title or not title:
                continue
            members.append(title)

        # Handle pagination
        cont = data.get("continue", {})
        cmcontinue = cont.get("cmcontinue")
        if not cmcontinue:
            break

    return members


def fetch_debuff_data():
    """Fetch all debuff infliction data from Fandom wiki.

    Returns two dicts:
    - debuff_map: {debuff_type: [champion_names]} - which champions inflict each debuff
    - champion_debuffs: {champion_name: [debuff_types]} - what debuffs each champion inflicts
    """
    debuff_map = {}
    champion_debuffs = {}

    for category, display_name in DEBUFF_CATEGORIES.items():
        try:
            members = _fetch_category_members(category)
            debuff_map[display_name] = sorted(members)
            logger.info(f"Fetched {display_name}: {len(members)} champions")

            # Build reverse mapping
            for champ in members:
                if champ not in champion_debuffs:
                    champion_debuffs[champ] = []
                champion_debuffs[champ].append(display_name)

            time.sleep(0.3)  # Rate limiting
        except Exception as e:
            logger.warning(f"Failed to fetch {display_name}: {e}")
            debuff_map[display_name] = []

    return debuff_map, champion_debuffs


def fetch_and_cache_debuffs():
    """Fetch debuff data and cache to disk."""
    debuff_map, champion_debuffs = fetch_debuff_data()

    cache = {
        "debuff_map": debuff_map,
        "champion_debuffs": champion_debuffs,
    }
    CACHE_PATH.write_text(json.dumps(cache, indent=2))
    logger.info(f"Cached debuff data: {len(DEBUFF_CATEGORIES)} types, {len(champion_debuffs)} champions")
    return debuff_map, champion_debuffs


def load_cached_debuffs():
    """Load cached debuff data."""
    if CACHE_PATH.exists():
        try:
            cache = json.loads(CACHE_PATH.read_text())
            return cache.get("debuff_map", {}), cache.get("champion_debuffs", {})
        except Exception as e:
            logger.error(f"Failed to load debuff cache: {e}")
    return {}, {}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    debuff_map, champion_debuffs = fetch_and_cache_debuffs()
    total = sum(len(v) for v in debuff_map.values())
    print(f"\n{len(debuff_map)} debuff types, {len(champion_debuffs)} unique champions, {total} total entries")
    for dtype, champs in debuff_map.items():
        print(f"  {dtype}: {len(champs)}")
