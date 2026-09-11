"""
Discover the current Google Sheets URLs for tier list sources by searching
YouTube for each creator's latest tier list video and parsing the description.

Most creators (Vega, Seatin) make a brand-new spreadsheet every month, so the
app's hardcoded sheet IDs go stale. This script searches YouTube via yt-dlp,
finds the most recent matching video per creator, extracts the first Google
Sheets URL from the description, and writes the results to cached_sources.json.

Intended to run once per day via the GitHub Action in
.github/workflows/discover-sources.yml. fetch_tierlist.py reads
cached_sources.json at fetch time to override its fallback sheet IDs.

Run locally:
    python fetch_sources.py            # discover, merge, write cache
    python fetch_sources.py --dry-run  # show what would change, don't write
"""
import argparse
import json
import logging
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from xml.etree import ElementTree

import requests

logger = logging.getLogger("mcoc-sources")

CACHE_PATH = Path(__file__).parent / "cached_sources.json"

SHEET_URL_PATTERN = re.compile(
    r"https?://docs\.google\.com/spreadsheets/d/([a-zA-Z0-9_-]+)"
)

# Per-source discovery configuration.
#   search_query     - passed to YouTube search (date-sorted).
#   title_keywords   - ALL keywords (case-insensitive) must appear in title.
#   channel_keywords - ANY keyword (case-insensitive) must match channel name.
#   max_results      - how many search results to scan before giving up.
#
# Vega's monthly tier list video title is always "Best Champions Ranked & Tier
# List - <Month> <Year> ..." -- the "&" makes it cleanly distinguishable from his
# PvP/PvE/Battlegrounds focus updates which use other connector words. We match
# the exact phrase to skip those.
DISCOVERY_CONFIG = {
    "Vega": {
        "search_query": "mcoc tier list vega",
        "title_keywords": ["best champions ranked & tier list"],
        "channel_keywords": ["vega"],
        "max_results": 20,
    },
    # Vega's awakening gem priority list — separate monthly video. Title varies
    # ("Best Champions to Use Awakening Gem On", "Best Champions to Awaken &
    # Sig Up", etc.) but always contains "awakening". Exclude "unawakened" to
    # skip his "Rank Unawakened" series.
    "Vega Awakening": {
        "search_query": "vega awakening tier list mcoc",
        "title_keywords": ["awakening"],
        "exclude_title_keywords": ["unawakened"],
        "channel_keywords": ["vega"],
        "max_results": 20,
    },
    # Vega's signature stone priority list. Dedicated videos use "sig stones";
    # combined awakening+sig videos also tend to mention "sig stones".
    "Vega Sig Stones": {
        "search_query": "vega sig stones tier list mcoc",
        "title_keywords": ["sig stones"],
        "channel_keywords": ["vega"],
        "max_results": 20,
    },
    "Lagacy": {
        "search_query": "mcoc tier list lagacy",
        "title_keywords": ["tier list"],
        "channel_keywords": ["lagacy"],
        "max_results": 20,
    },
    # Seatin's monthly list is "Best Champions Ranked <Month> <Year> - Seatin's
    # Tier List - ...". Matching "best champions ranked" skips his many other
    # tier list videos (Titan Crystal, Content, per-class, Ascended). Keywords
    # avoid the apostrophe in "Seatin's" since YouTube titles mix the ASCII and
    # typographic forms.
    "Seatin": {
        "search_query": "seatin tier list mcoc",
        "title_keywords": ["best champions ranked", "tier list"],
        "channel_keywords": ["seatin"],
        "max_results": 20,
    },
    # MetalSonicDude's all-class list is "<Month> <Year> Champion Tier List".
    # His per-class videos ("Mutant Champion Tier List - May 2026") share that
    # phrase, so exclude the class names to keep only the combined list.
    "MetalSonicDude": {
        "search_query": "metalsonicdude champion tier list mcoc",
        "title_keywords": ["champion tier list"],
        "exclude_title_keywords": [
            "mutant", "skill", "mystic", "tech", "science", "cosmic",
        ],
        "channel_keywords": ["metalsonicdude"],
        "max_results": 20,
    },
}


def _title_matches(title, keywords, exclude_keywords=None):
    lower = (title or "").lower()
    if not all(kw.lower() in lower for kw in keywords):
        return False
    if exclude_keywords and any(kw.lower() in lower for kw in exclude_keywords):
        return False
    return True


def _channel_matches(channel, keywords):
    if not keywords:
        return True
    lower = (channel or "").lower()
    return any(kw.lower() in lower for kw in keywords)


def _extract_sheet_id(text):
    m = SHEET_URL_PATTERN.search(text or "")
    return m.group(1) if m else None


def _ydl_opts(extra=None):
    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extractor_retries": 3,
        "socket_timeout": 30,
    }
    if extra:
        opts.update(extra)
    return opts


def _search_youtube(query, max_results):
    """Date-sorted YouTube search. Returns a list of entry dicts.

    Uses YouTube's search results URL with sp=CAI%3D (sort by upload date),
    which yt-dlp accepts as a playlist-style input. The `ytsearchdate{N}`
    virtual-URL form was removed in recent yt-dlp builds, so this is the
    forward-compatible path.
    """
    import yt_dlp

    url = (
        "https://www.youtube.com/results?"
        + urlencode({"search_query": query})
        + "&sp=CAI%3D"
    )
    opts = _ydl_opts({
        "extract_flat": "in_playlist",
        "playlistend": max_results,
    })
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    return (info or {}).get("entries", []) or []


BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

_ATOM_NS = {
    "a": "http://www.w3.org/2005/Atom",
    "yt": "http://www.youtube.com/xml/schemas/2015",
    "media": "http://search.yahoo.com/mrss/",
}

# The watch page carries the description twice: in the player response
# ("shortDescription") and in the rendered page data ("attributedDescription").
# Datacenter IPs are served a degraded page that drops the player response and
# strips every link out of the rendered description, so both are tried.
_DESC_RES = (
    re.compile(r'"shortDescription":"((?:[^"\\]|\\.)*)"'),
    re.compile(r'"attributedDescription":\{"content":"((?:[^"\\]|\\.)*)"'),
)
_UPLOAD_DATE_RE = re.compile(r'"uploadDate":"(\d{4})-(\d{2})-(\d{2})')


def _http_get(url):
    resp = requests.get(
        url,
        timeout=30,
        headers={"User-Agent": BROWSER_UA, "Accept-Language": "en-US,en;q=0.9"},
    )
    resp.raise_for_status()
    return resp.text


_rss_cache = {}


def _rss_descriptions(channel_id):
    """{video_id: (description, upload_date)} for a channel's 15 newest uploads."""
    if channel_id not in _rss_cache:
        entries = {}
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        try:
            root = ElementTree.fromstring(_http_get(url))
            for entry in root.findall("a:entry", _ATOM_NS):
                vid = entry.findtext("yt:videoId", "", _ATOM_NS)
                desc = entry.findtext("media:group/media:description", "", _ATOM_NS)
                published = entry.findtext("a:published", "", _ATOM_NS)
                if vid:
                    entries[vid] = (desc, published[:10].replace("-", "") or None)
        except Exception as e:
            logger.warning(f"Atom feed fetch failed for channel {channel_id}: {e}")
        _rss_cache[channel_id] = entries
    return _rss_cache[channel_id]


def _watch_page_details(video_id):
    """(description, upload_date) scraped from the watch page HTML.

    Best-effort only: whether a given IP gets the full page or the link-stripped
    one is fixed per caller, so retrying is pointless. Prefers whichever copy of
    the description still has its links, since a stripped one is useless here.
    """
    html = _http_get(f"https://www.youtube.com/watch?v={video_id}&hl=en")
    d = _UPLOAD_DATE_RE.search(html)
    upload_date = "".join(d.groups()) if d else None

    best = None
    for pattern in _DESC_RES:
        m = pattern.search(html)
        if not m:
            continue
        try:
            desc = json.loads(f'"{m.group(1)}"')
        except ValueError:
            continue
        if SHEET_URL_PATTERN.search(desc):
            return desc, upload_date
        best = best or desc
    if best is None:
        raise ValueError("no description in watch page")
    return best, upload_date


def _video_details(video_id, channel_id=None):
    """Return (description, upload_date) for one video.

    Deliberately avoids yt-dlp's video extractor. YouTube's player API answers
    metadata-only requests from datacenter IPs (i.e. the GitHub Action) with
    "Sign in to confirm you're not a bot" regardless of player_client, which
    silently froze sheet discovery for a month. The channel's Atom feed is tried
    first: it only covers the 15 newest uploads, but it is never bot-checked and
    never link-stripped, so a tier list video is reliably readable for the days
    right after it goes up. Older videos fall back to scraping the watch page.
    """
    if channel_id:
        desc, upload_date = _rss_descriptions(channel_id).get(video_id, (None, None))
        if desc:
            return desc, upload_date
    return _watch_page_details(video_id)


def discover_sheet_for(name, cfg):
    """Find the latest matching video for one source and pull its sheet URL.

    Returns a discovery dict on success, or None on any failure.
    """
    try:
        entries = _search_youtube(cfg["search_query"], cfg.get("max_results", 15))
    except Exception as e:
        logger.warning(f"[{name}] YouTube search failed: {e}")
        return None

    title_kw = cfg.get("title_keywords", [])
    exclude_kw = cfg.get("exclude_title_keywords", [])
    channel_kw = cfg.get("channel_keywords", [])

    for entry in entries:
        title = entry.get("title") or ""
        channel = entry.get("channel") or entry.get("uploader") or ""
        video_id = entry.get("id") or ""
        if not video_id:
            continue
        if not _title_matches(title, title_kw, exclude_kw):
            continue
        if not _channel_matches(channel, channel_kw):
            continue

        try:
            desc, upload_date = _video_details(video_id, entry.get("channel_id"))
        except Exception as e:
            logger.warning(f"[{name}] description fetch failed for {video_id}: {e}")
            continue

        sheet_id = _extract_sheet_id(desc)
        if not sheet_id:
            logger.info(f"[{name}] no sheet URL in {video_id}; trying next match")
            continue

        return {
            "name": name,
            "sheet_id": sheet_id,
            "sheet_url": f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit",
            "video_id": video_id,
            "video_title": title,
            "video_url": f"https://www.youtube.com/watch?v={video_id}",
            "channel": channel,
            "video_upload_date": upload_date,
            "discovered_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }

    logger.warning(f"[{name}] no matching video found in {len(entries)} results")
    return None


def discover_all_sheets(config=None):
    """Run discovery for every configured source.

    Returns {source_name: discovery_dict_or_None}.
    """
    cfg = config or DISCOVERY_CONFIG
    return {name: discover_sheet_for(name, c) for name, c in cfg.items()}


def load_cache(path=CACHE_PATH):
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception as e:
            logger.error(f"failed to load {path}: {e}")
    return {}


def save_cache(data, path=CACHE_PATH):
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def merge_into_cache(cached, fresh):
    """Merge fresh discoveries into the existing cache.

    Failed discoveries (None) keep the previous cache entry. Successful ones
    overwrite. Returns (merged_dict, list_of_changes).
    """
    merged = dict(cached or {})
    changes = []
    for name, info in (fresh or {}).items():
        if info is None:
            if name in merged:
                changes.append(f"{name}: discovery failed, keeping cached sheet "
                               f"{merged[name].get('sheet_id')!r}")
            else:
                changes.append(f"{name}: discovery failed, no cached fallback")
            continue
        prev = merged.get(name) or {}
        prev_id = prev.get("sheet_id")
        new_id = info.get("sheet_id")
        # A source never moves backwards in time. When the newest video's
        # description comes back unusable, discovery walks on to older matches,
        # and accepting one would swap a current tier list for a stale one.
        prev_date = prev.get("video_upload_date")
        new_date = info.get("video_upload_date")
        if prev_date and new_date and new_date < prev_date:
            changes.append(f"{name}: ignoring older video {info.get('video_url')} "
                           f"({new_date} < cached {prev_date})")
            continue
        if prev_id != new_id:
            changes.append(f"{name}: sheet_id {prev_id!r} -> {new_id!r} "
                           f"(via {info.get('video_url')})")
        else:
            changes.append(f"{name}: unchanged ({new_id})")
        merged[name] = info
    return merged, changes


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true",
                        help="show changes but don't write cache")
    parser.add_argument("--cache", type=Path, default=CACHE_PATH,
                        help="path to cached_sources.json")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    cached = load_cache(args.cache)
    fresh = discover_all_sheets()
    merged, changes = merge_into_cache(cached, fresh)

    for line in changes:
        print(line)

    any_change = any(
        (cached.get(name) or {}).get("sheet_id") != (info or {}).get("sheet_id")
        for name, info in merged.items()
        if info is not None
    )

    if args.dry_run:
        print("(dry-run: not writing cache)")
        return 0

    if any_change or not args.cache.exists():
        save_cache(merged, args.cache)
        print(f"wrote {args.cache}")
    else:
        # Still touch the file's discovered_at to keep it fresh-ish in git history?
        # No -- avoid churn. Only write when sheet_ids actually change.
        print("no sheet_id changes; cache not rewritten")

    # Every source failing at once means discovery itself is broken (YouTube
    # blocking us, a yt-dlp break), not that nobody posted this month. Exit
    # non-zero so the Action goes red instead of quietly serving stale sheets --
    # that failure mode went unnoticed for a month.
    if all(info is None for info in fresh.values()):
        logger.error("every source failed discovery; cached sheet IDs left in place")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
