"""
Scraper module for refreshing MCOC tier list data from online sources.
Run this script periodically to update champions_data.py with fresh data.

Usage: python scraper.py
"""
import asyncio
import json
import re
import httpx
from bs4 import BeautifulSoup

SOURCES = [
    {
        "name": "Pocket Gamer",
        "url": "https://www.pocketgamer.com/marvel-contest-of-champions/tier-list/",
    },
    {
        "name": "Pocket Tactics",
        "url": "https://www.pockettactics.com/mcoc/tier-list",
    },
    {
        "name": "FindingDulcinea",
        "url": "https://findingdulcinea.com/mcoc-champion-tier-list-rankings/",
    },
]

TIER_MAP = {
    "s+": 6, "beyond god": 6, "god": 5, "s": 5,
    "a": 4, "demi-god": 4, "b": 3, "c": 2,
    "d": 1, "n": 0, "e": 0, "f": 0,
}

CLASSES = {"cosmic", "tech", "mutant", "skill", "science", "mystic"}


async def fetch_page(url: str) -> str:
    async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; MCOCTierList/1.0)"}
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
        return resp.text


def detect_tier(text: str) -> int | None:
    text = text.lower().strip()
    for key, val in TIER_MAP.items():
        if key in text:
            return val
    return None


def detect_class(text: str) -> str | None:
    text = text.lower()
    for cls in CLASSES:
        if cls in text:
            return cls.capitalize()
    return None


def parse_generic_tierlist(html: str) -> dict[str, dict]:
    """
    Generic parser that looks for tier headings (h2/h3) containing tier names
    and class names, then extracts champion names from lists or bold text below.
    """
    soup = BeautifulSoup(html, "lxml")
    results = {}
    current_class = None
    current_tier = None

    for tag in soup.find_all(["h2", "h3", "h4", "p", "li", "strong", "b"]):
        text = tag.get_text(strip=True)

        cls = detect_class(text)
        if cls and tag.name in ("h2", "h3"):
            current_class = cls

        tier = detect_tier(text)
        if tier is not None and tag.name in ("h2", "h3", "h4", "p", "strong"):
            current_tier = tier

        if current_class and current_tier is not None:
            if tag.name in ("li", "p"):
                names = re.split(r"[,\n]", text)
                for name in names:
                    name = name.strip().rstrip(".")
                    if len(name) > 2 and not detect_tier(name) and not detect_class(name):
                        results[name] = {
                            "class": current_class,
                            "score": current_tier,
                        }

    return results


async def scrape_all():
    """Scrape all sources and merge data."""
    all_data = {}

    for i, source in enumerate(SOURCES):
        print(f"Fetching {source['name']}...")
        try:
            html = await fetch_page(source["url"])
            champions = parse_generic_tierlist(html)
            print(f"  Found {len(champions)} champions")

            for name, info in champions.items():
                if name not in all_data:
                    all_data[name] = {
                        "class": info["class"],
                        "scores": [None] * len(SOURCES),
                    }
                all_data[name]["scores"][i] = info["score"]
                if info["class"]:
                    all_data[name]["class"] = info["class"]

        except Exception as e:
            print(f"  Error: {e}")

    return all_data


async def main():
    data = await scrape_all()
    print(f"\nTotal unique champions: {len(data)}")

    # Output as JSON for easy inspection
    output_path = "scraped_data.json"
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Saved to {output_path}")
    print("Review the data and update champions_data.py accordingly.")


if __name__ == "__main__":
    asyncio.run(main())
