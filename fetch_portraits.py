"""Fetch champion portrait URLs from Fandom wiki API and mcochub.insaneskull.com.

Primary source: Fandom wiki (batch API, consistent naming)
Fallback: mcochub champion page scrape (for any wiki misses)

Called during daily update to fill in missing portraits.
"""
import json
import logging
import time
import urllib.parse
import urllib.request
from pathlib import Path

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger("mcoc-portraits")

BASE_DIR = Path(__file__).parent
PORTRAITS_PATH = BASE_DIR / "portraits.json"
WIKI_API = "https://marvel-contestofchampions.fandom.com/api.php"
BATCH_SIZE = 20
THUMB_SIZE = 80

# Map our canonical champion names to Fandom wiki page titles
WIKI_NAME_MAP = {
    "Captain Marvel (Classic)": "Captain Marvel",
    "Ms. Marvel": "Ms. Marvel",
    "Ms. Marvel (Kamala Khan)": "Ms. Marvel (Kamala Khan)",
    "Spider-Man (Pavitr Prabhakar)": "Spider-Man (Pavitr Prabhakar)",
    "Spider-Woman (Jessica Drew)": "Spider-Woman",
    "Scarlet Witch": "Scarlet Witch",
    "Scarlet Witch (Classic)": "Scarlet Witch (Classic)",
    "Hulk": "Hulk",
    "Iron Man": "Iron Man",
    "Storm": "Storm",
    "Wolverine": "Wolverine",
    "Magneto": "Magneto",
    "Spider-Man": "Spider-Man",
    "Captain America": "Captain America",
    "Black Panther": "Black Panther",
    "Black Widow": "Black Widow",
    "Daredevil": "Daredevil",
    "Ultron": "Ultron",
    "Vision": "Vision",
    "Star-Lord (Stellar-Forged)": "Star-Lord (Stellar-Forged)",
    "Spider-Slayer (J. Jonah Jameson)": "Spider-Slayer (J. Jonah Jameson)",
}

# Map mcochub alt-text names to our canonical names
MCOCHUB_NAME_MAP = {
    "Captain Marvel": "Captain Marvel (Movie)",
    "Spider Man (Stark Enhanced)": "Spider-Man (Stark Enhanced)",
    "Spider Man 2099": "Spider-Man 2099",
    "Spider man (Miles Morales)": "Spider-Man (Miles Morales)",
    "Spider-Man (Stealth-Suit)": "Spider-Man (Stealth Suit)",
    "Wolverine (X 23)": "Wolverine (X-23)",
    "Star-Lord (Stellar Forged)": "Star-Lord (Stellar Forge)",
    "Summoned Symbioid": "Summoned Symbiote",
    "Platinum Pool": "Platinumpool",
    "QuickSilver": "Quicksilver",
    "Shang Chi": "Shang-Chi",
    "Kang the Conqueror": "Kang",
    "Jack O\u2019Lantern": "Jack O'Lantern",
    "Jack O'Lantern": "Jack O'Lantern",
}


def _fetch_wiki_batch(titles):
    """Fetch portrait thumbnails for a batch of wiki titles."""
    joined = "|".join(titles)
    params = urllib.parse.urlencode({
        "action": "query",
        "titles": joined,
        "prop": "pageimages",
        "format": "json",
        "pithumbsize": THUMB_SIZE,
    })
    url = f"{WIKI_API}?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "MCOCTierList/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())

    results = {}
    pages = data.get("query", {}).get("pages", {})
    for page in pages.values():
        title = page.get("title", "")
        thumb = page.get("thumbnail", {}).get("source")
        if thumb:
            results[title] = thumb
    return results


def _fetch_from_wiki(names):
    """Fetch portraits from Fandom wiki for a list of champion names.
    Returns dict {canonical_name: url}.
    """
    wiki_to_name = {}
    for name in names:
        wt = WIKI_NAME_MAP.get(name, name)
        wiki_to_name[wt] = name

    wiki_titles = list(wiki_to_name.keys())
    portraits = {}

    for i in range(0, len(wiki_titles), BATCH_SIZE):
        batch = wiki_titles[i:i + BATCH_SIZE]
        try:
            results = _fetch_wiki_batch(batch)
            for wt, url in results.items():
                champ_name = wiki_to_name.get(wt)
                if champ_name:
                    portraits[champ_name] = url
        except Exception as e:
            logger.warning(f"Wiki batch error: {e}")
        time.sleep(0.3)

    return portraits


def _fetch_from_mcochub(names):
    """Scrape mcochub champions page for portrait URLs.
    Returns dict {canonical_name: url} for requested names.
    """
    try:
        resp = requests.get('https://mcochub.insaneskull.com/champions', timeout=30,
                            headers={'User-Agent': 'Mozilla/5.0 (MCOCTierList/1.0)'})
        if resp.status_code != 200:
            logger.warning(f"mcochub returned {resp.status_code}")
            return {}
    except Exception as e:
        logger.warning(f"mcochub fetch failed: {e}")
        return {}

    soup = BeautifulSoup(resp.text, 'lxml')
    names_set = set(names)

    # Build hub_name -> url mapping
    hub_portraits = {}
    for img in soup.find_all('img'):
        src = img.get('src', '')
        if '/storage/champs/' not in src:
            continue
        alt = img.get('alt', '').strip()
        if alt:
            hub_portraits[alt] = src

    # Map hub names to our canonical names
    portraits = {}
    for hub_name, url in hub_portraits.items():
        # Direct match
        if hub_name in names_set:
            portraits[hub_name] = url
            continue
        # Explicit mapping
        canonical = MCOCHUB_NAME_MAP.get(hub_name)
        if canonical and canonical in names_set:
            portraits[canonical] = url
            continue
        # Case-insensitive match
        hub_lower = hub_name.lower().replace(' ', '').replace('-', '')
        for name in names_set:
            name_lower = name.lower().replace(' ', '').replace('-', '')
            if hub_lower == name_lower:
                portraits[name] = url
                break

    return portraits


def fetch_missing_portraits(champion_names):
    """Fetch portraits for champions that don't have one yet.

    Loads existing portraits.json, fetches missing from wiki then mcochub,
    saves updated file. Returns the full portrait dict.
    """
    if PORTRAITS_PATH.exists():
        existing = json.loads(PORTRAITS_PATH.read_text())
    else:
        existing = {}

    missing = [n for n in champion_names if n not in existing]
    if not missing:
        logger.info("All portraits up to date.")
        return existing

    logger.info(f"Fetching portraits for {len(missing)} champions...")

    # Try wiki first
    wiki_results = _fetch_from_wiki(missing)
    existing.update(wiki_results)
    logger.info(f"Wiki: found {len(wiki_results)}/{len(missing)}")

    # Try mcochub for any still missing
    still_missing = [n for n in missing if n not in existing]
    if still_missing:
        hub_results = _fetch_from_mcochub(still_missing)
        existing.update(hub_results)
        logger.info(f"mcochub: found {len(hub_results)}/{len(still_missing)}")

    # Report final missing
    final_missing = [n for n in champion_names if n not in existing]
    if final_missing:
        logger.warning(f"Still missing portraits: {final_missing}")

    PORTRAITS_PATH.write_text(json.dumps(existing, indent=2))
    logger.info(f"Saved {len(existing)} portraits to {PORTRAITS_PATH.name}")
    return existing


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from fetch_tierlist import fetch_and_combine
    data, _, _ = fetch_and_combine()
    fetch_missing_portraits(list(data.keys()))
