"""Set the site banner to the newest champion's official spotlight art.

Kabam publishes a Champion Spotlight post for every champion they release, and
each one carries a square piece of key art. This picks the most recent
spotlight whose champion has actually made it into the combined tier list,
crops the art to the banner's shape, and writes it over public/banner.jpg --
so the banner rolls forward to the newest champion roughly once a month,
tracking the creators' monthly tier list refresh.

Why "has made it into the tier list" rather than simply the newest spotlight:
the creators lag a month or two behind a release, so the three newest
spotlights are usually champions the site can't yet rank. Banner-ing one of
them would show a champion who isn't on the page.

Nothing is touched unless a new champion is found, so re-runs are free. A
failed fetch leaves the current banner in place, and if there is no usable
banner at all it restores public/banner-default.jpg -- the generic art the
site used before this script existed.

Run daily by .github/workflows/refresh-portraits.yml, or locally:
    venv/bin/python3 fetch_banner.py
"""
import html
import io
import json
import logging
import re
import sys
from pathlib import Path

import requests
from PIL import Image

from fetch_tierlist import (
    fetch_and_combine, load_cached, _normalize, _apply_canonical_renames,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("mcoc-banner")

BASE = Path(__file__).parent
BANNER_PATH = BASE / "public" / "banner.jpg"
# The generic multi-champion banner the site used before this script existed.
# Committed, never written to, and restored whenever banner.jpg is missing or
# unreadable -- so a broken banner degrades to the old art rather than to a
# hole in the header.
DEFAULT_BANNER_PATH = BASE / "public" / "banner-default.jpg"
GENERIC_ALT = "Marvel Contest of Champions Tier List – Champion Rankings"
META_PATH = BASE / "banner_meta.json"

SITE = "https://playcontestofchampions.com"
API = f"{SITE}/wp-json/wp/v2"
SPOTLIGHT_SLUG = "champion-spotlights"
SPOTLIGHT_CATEGORY_FALLBACK = 61

# playcontestofchampions.com sits behind Cloudflare, which 403s anything that
# doesn't look like a real browser -- a bare User-Agent is not enough, it wants
# the Sec-Fetch/Accept set a navigation would send.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Dest": "document",
    "Upgrade-Insecure-Requests": "1",
}

# How many spotlights back to look for a champion the tier lists already rank.
# Kabam ships two or three champions a month and the creators trail by about
# two months, so a dozen is comfortably deep enough.
SPOTLIGHT_LOOKBACK = 12

# The banner is a 3:1 strip (see .banner in public/style.css). The spotlight art
# is always square, and composed with the champion's head in the upper middle --
# so a band starting a tenth of the way down frames the face without any
# per-champion tuning. Measured against 15 spotlights back to Feb 2026.
BANNER_RATIO = 3.0
BANNER_TOP_FRACTION = 0.10
JPEG_QUALITY = 88


def _get(url, **params):
    resp = requests.get(url, params=params or None, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp


def _spotlight_category_id():
    """Resolve the Champion Spotlights category by slug, so a re-numbered
    category doesn't silently freeze the banner."""
    try:
        cats = _get(f"{API}/categories", slug=SPOTLIGHT_SLUG).json()
        if cats:
            return cats[0]["id"]
    except Exception as e:
        logger.warning(f"Category lookup failed ({e}); using id {SPOTLIGHT_CATEGORY_FALLBACK}")
    return SPOTLIGHT_CATEGORY_FALLBACK


def _fetch_spotlights():
    """Return recent spotlights, newest first: [(champion, date, image_url)].

    `champion` is the post title run through the tier list's own alias maps, so
    Kabam's spelling lines up with the site's canonical names ("Blade (Stellar
    Forged)" -> "Blade (Stellar Forge)") without a second map to maintain.
    """
    posts = _get(f"{API}/posts", categories=_spotlight_category_id(),
                 per_page=SPOTLIGHT_LOOKBACK, _embed="wp:featuredmedia").json()
    spotlights = []
    for post in posts:
        media = (post.get("_embedded", {}).get("wp:featuredmedia") or [{}])[0]
        image_url = media.get("source_url")
        if not image_url:
            continue
        name = _canonical(post["title"]["rendered"])
        if name:
            spotlights.append((name, post["date"][:10], image_url))
    return spotlights


def _canonical(title):
    """Map a spotlight post title to the site's canonical champion name."""
    # Titles arrive HTML-escaped and use a typographic apostrophe where the
    # sheets use a plain one (M&#8217;Baku -> M'Baku).
    clean = html.unescape(title).replace("’", "'").strip()
    normed = _normalize(clean)
    if normed is None:
        return None
    return next(iter(_apply_canonical_renames({normed: None})))


def _ranked_champions():
    """Names of every champion the site currently ranks."""
    combined, count, _ = fetch_and_combine()
    if not combined or not count:
        logger.warning("Live tier list fetch failed; falling back to cache")
        combined = load_cached()[0]
    return set(combined or ())


def _crop_to_banner(image_bytes):
    """Crop square spotlight art to the banner's 3:1 strip."""
    art = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    width, height = art.size
    band = round(width / BANNER_RATIO)
    top = round(height * BANNER_TOP_FRACTION)
    if top + band > height:
        # Not the square art we expect -- centre the band rather than fail.
        top = max(0, (height - band) // 2)
    return art.crop((0, top, width, top + band))


def _update_alt_text(alt):
    """Set the banner's alt text on every page.

    index.html is the template the other four pages are derived from
    (generate_data.py), so all five are rewritten to keep them consistent
    until the next rebuild.
    """
    alt = html.escape(alt)
    pattern = re.compile(r'(<div class="banner"><img src="/banner\.jpg" alt=")[^"]*(")')
    for page in sorted((BASE / "public").glob("*.html")):
        text = page.read_text()
        updated, count = pattern.subn(lambda m: m.group(1) + alt + m.group(2), text, count=1)
        if count and updated != text:
            page.write_text(updated)
            logger.info(f"Updated banner alt text in {page.name}")


def _banner_is_usable():
    """True if public/banner.jpg exists and actually decodes."""
    if not BANNER_PATH.exists():
        return False
    try:
        with Image.open(BANNER_PATH) as img:
            img.verify()
        return True
    except Exception as e:
        logger.warning(f"{BANNER_PATH.name} is unreadable ({e})")
        return False


def _fall_back(reason):
    """Give up on a champion banner, keeping the header intact.

    A banner already in place is left alone -- a champion banner from an
    earlier run beats reverting to the generic art over one bad fetch. Only a
    missing or corrupt banner.jpg is replaced, with the pre-existing generic
    art, so the site can never end up with a broken image.
    """
    logger.warning(reason)
    if _banner_is_usable():
        logger.warning("Keeping the current banner")
        return 0
    if not DEFAULT_BANNER_PATH.exists():
        logger.error(f"No usable banner and no {DEFAULT_BANNER_PATH.name} to fall back on")
        return 0
    BANNER_PATH.write_bytes(DEFAULT_BANNER_PATH.read_bytes())
    _update_alt_text(GENERIC_ALT)
    META_PATH.unlink(missing_ok=True)
    logger.warning(f"No usable banner; restored the generic {DEFAULT_BANNER_PATH.name}")
    return 0


def main():
    previous = json.loads(META_PATH.read_text()) if META_PATH.exists() else {}

    try:
        spotlights = _fetch_spotlights()
    except Exception as e:
        return _fall_back(f"Could not read champion spotlights ({e})")
    if not spotlights:
        return _fall_back("No champion spotlights found")

    ranked = _ranked_champions()
    if not ranked:
        return _fall_back("No tier list available")

    for champion, date, image_url in spotlights:
        if champion in ranked:
            break
    else:
        newest = ", ".join(name for name, _, _ in spotlights[:3])
        return _fall_back(f"No ranked champion in the last {len(spotlights)} spotlights "
                          f"(newest: {newest})")

    if previous.get("champion") == champion and _banner_is_usable():
        logger.info(f"Banner is already {champion} (spotlight {date}); nothing to do")
        return 0

    logger.info(f"Newest ranked champion: {champion} (spotlight {date})")
    try:
        image_bytes = _get(image_url).content
        banner = _crop_to_banner(image_bytes)
    except Exception as e:
        return _fall_back(f"Could not build a banner from {image_url} ({e})")

    banner.save(BANNER_PATH, "JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)
    logger.info(f"Wrote {BANNER_PATH.name}: {banner.width}x{banner.height}, "
                f"{BANNER_PATH.stat().st_size // 1024} KB")
    _update_alt_text(f"{champion} – Marvel Contest of Champions Tier List")

    META_PATH.write_text(json.dumps({
        "champion": champion,
        "spotlight_date": date,
        "source_url": image_url,
    }, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
