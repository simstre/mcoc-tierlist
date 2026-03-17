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
from immunities import get_immunities_for_champion, get_immunity_map, IMMUNITY_TYPES
from debuffs import fetch_and_cache_debuffs, load_cached_debuffs
from prestige_data import PRESTIGE, SIG_LEVELS, PRESTIGE_OPTIONS


def main():
    # Try fresh fetch, fall back to cache
    data, meta, aw, sig = fetch_and_cache()
    if not data:
        data, meta, aw, sig = load_cached()
    if not data:
        print("ERROR: No data available")
        sys.exit(1)

    # Load portraits
    portraits = {}
    base = Path(__file__).parent
    for fname in ["portraits.json", "portraits_local.json", "mcochub_portraits.json"]:
        fpath = base / fname
        if fpath.exists():
            portraits.update(json.loads(fpath.read_text()))

    # Fetch debuff data
    debuff_map, champion_debuffs = fetch_and_cache_debuffs()
    if not debuff_map:
        debuff_map, champion_debuffs = load_cached_debuffs()

    # Build response
    champions = compute_tier_list(data)
    for c in champions:
        c["portrait"] = portraits.get(c["name"])
        c["immunities"] = get_immunities_for_champion(c["name"])
        c["inflicts"] = champion_debuffs.get(c["name"], [])

    by_class = get_champions_by_class(champions)

    response = {
        "champions": champions,
        "by_class": by_class,
        "sources": SOURCES,
        "class_colors": CLASS_COLORS,
        "tier_colors": TIER_COLORS,
        "tag_labels": TAG_LABELS,
        "immunity_map": get_immunity_map(),
        "immunity_types": IMMUNITY_TYPES,
        "debuff_map": debuff_map,
        "debuff_types": list(debuff_map.keys()),
        "awakening_data": aw or {},
        "sig_stones_data": sig or {},
        "prestige": PRESTIGE,
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


if __name__ == "__main__":
    main()
