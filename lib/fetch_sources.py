"""
Discover the current Google Sheets URLs for tier list sources by searching
YouTube for each creator's latest tier list video and parsing the description.

Some creators (notably Vega) make a brand-new spreadsheet every month, so the
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


def _get_video_metadata(video_id):
    """Full metadata for a single video (needed for the description)."""
    import yt_dlp

    url = f"https://www.youtube.com/watch?v={video_id}"
    with yt_dlp.YoutubeDL(_ydl_opts()) as ydl:
        return ydl.extract_info(url, download=False) or {}


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
            meta = _get_video_metadata(video_id)
        except Exception as e:
            logger.warning(f"[{name}] description fetch failed for {video_id}: {e}")
            continue

        desc = meta.get("description") or ""
        sheet_id = _extract_sheet_id(desc)
        if not sheet_id:
            logger.info(f"[{name}] no sheet URL in {video_id}; trying next match")
            continue

        upload_date = meta.get("upload_date")  # "YYYYMMDD"
        return {
            "name": name,
            "sheet_id": sheet_id,
            "sheet_url": f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit",
            "video_id": video_id,
            "video_title": title,
            "video_url": f"https://www.youtube.com/watch?v={video_id}",
            "channel": channel or meta.get("channel") or meta.get("uploader") or "",
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

    # Exit non-zero if every source failed AND no cache exists -- bad state.
    all_failed = all(info is None for info in fresh.values())
    no_cache = not merged
    if all_failed and no_cache:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
