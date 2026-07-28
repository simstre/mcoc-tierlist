"""Generate public/data/tierlist.json locally.

Run this to seed the initial data file before deploying to Vercel,
or to update data manually at any time.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Use root-level modules (not lib/)
from champions_data import (
    compute_tier_list, get_champions_by_class,
    SOURCES, CLASS_COLORS, TIER_COLORS, TAG_LABELS,
)
from fetch_tierlist import fetch_and_cache, load_cached
from immunities import (
    fetch_and_cache_immunities, load_cached_immunities,
    _apply_conditional, get_immunities_for_champion, get_immunity_map,
    IMMUNITY_TYPES, CHAMPION_IMMUNITIES_FALLBACK,
)
from debuffs import fetch_and_cache_debuffs, load_cached_debuffs
from prestige_scraper import (
    fetch_and_cache_prestige, load_cached_prestige,
    SIG_LEVELS, PRESTIGE_OPTIONS,
)
from prestige_data import PRESTIGE as PRESTIGE_FALLBACK


def _seo_title():
    """SEO <title> using the current month, e.g. "MCOC YouTubers Tier List - July 2026"."""
    return f"MCOC YouTubers Tier List - {datetime.now(timezone.utc).strftime('%B %Y')}"


def _apply_seo_title(html, title):
    """Rewrite <title>/og:title/twitter:title in the HTML to `title`."""
    import re
    repl = lambda m: m.group(1) + title + m.group(2)
    html = re.sub(r"(<title>).*?(</title>)", repl, html, count=1, flags=re.S)
    html = re.sub(r'(<meta property="og:title" content=").*?(">)', repl, html, count=1)
    html = re.sub(r'(<meta name="twitter:title" content=").*?(">)', repl, html, count=1)
    return html


def main():
    # Try fresh fetch, fall back to cache
    data, meta, aw, sig = fetch_and_cache()
    if not data:
        data, meta, aw, sig = load_cached()
    if not data:
        print("ERROR: No data available")
        sys.exit(1)

    # Load portraits from lib/ — the same source the production Vercel cron
    # (api/cron/refresh.py) uses. The root copies carry legacy Flask-era
    # "/static/portraits/..." paths that 404 on Vercel, where portraits are
    # served from public/portraits/ as "/portraits/...".
    portraits = {}
    base = Path(__file__).parent
    for fname in ["portraits.json", "portraits_local.json", "mcochub_portraits.json"]:
        fpath = base / "lib" / fname
        if fpath.exists():
            portraits.update(json.loads(fpath.read_text()))

    # Fetch debuff data
    debuff_map, champion_debuffs = fetch_and_cache_debuffs()
    if not debuff_map:
        debuff_map, champion_debuffs = load_cached_debuffs()

    # Fetch immunity data (wiki -> cache -> fallback)
    raw_immunities = fetch_and_cache_immunities()
    if not raw_immunities:
        raw_immunities = load_cached_immunities()
    if not raw_immunities:
        raw_immunities = CHAMPION_IMMUNITIES_FALLBACK
    imm_annotated = _apply_conditional(raw_immunities)

    # Fetch prestige data (mcochub -> cache -> fallback)
    prestige = fetch_and_cache_prestige()
    if not prestige or not any(prestige.values()):
        prestige = load_cached_prestige()
    if not prestige:
        prestige = PRESTIGE_FALLBACK

    # Build response
    champions = compute_tier_list(data)
    for c in champions:
        c["portrait"] = portraits.get(c["name"])
        c["immunities"] = imm_annotated.get(c["name"], [])
        c["inflicts"] = champion_debuffs.get(c["name"], [])

    by_class = get_champions_by_class(champions)

    response = {
        "champions": champions,
        "by_class": by_class,
        "sources": SOURCES,
        "class_colors": CLASS_COLORS,
        "tier_colors": TIER_COLORS,
        "tag_labels": TAG_LABELS,
        "immunity_map": get_immunity_map(imm_annotated),
        "immunity_types": IMMUNITY_TYPES,
        "debuff_map": debuff_map,
        "debuff_types": list(debuff_map.keys()),
        "awakening_data": aw or {},
        "sig_stones_data": sig or {},
        "prestige": prestige,
        "prestige_sig_levels": SIG_LEVELS,
        "prestige_options": PRESTIGE_OPTIONS,
        "prestige_portraits": portraits,
        "source_meta": meta or [],
        "last_updated": datetime.now(timezone.utc).strftime("%B %d, %Y"),
        "total_champions": len(champions),
    }

    out = base / "public" / "data" / "tierlist.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(response, separators=(",", ":")))
    print(f"Generated {out} ({out.stat().st_size:,} bytes, {len(champions)} champions)")

    # Keep the static SEO <title> month in sync with Lagacy's edition.
    index_path = base / "public" / "index.html"
    if index_path.exists():
        title = _seo_title()
        html = index_path.read_text()
        new_html = _apply_seo_title(html, title)
        if new_html != html:
            index_path.write_text(new_html)
            print(f"Updated index.html SEO title: {title!r}")


if __name__ == "__main__":
    main()
