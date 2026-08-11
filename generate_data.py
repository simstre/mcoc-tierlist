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
    compute_tier_list, get_champions_by_class, retier_priority,
    SOURCES, CLASS_COLORS, TIER_COLORS, TIER_ORDER, TAG_LABELS,
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


SITE_URL = "https://mcoc.app"

# One static, SEO-optimized page per tab. index.html is the "/" template; the
# other four are generated from it with their own title/description/canonical/
# og/twitter/H1/intro and the matching tab pre-activated (so crawlers and
# no-JS loads get the right content). Keep this in sync with the ROUTES map in
# public/app.js, which drives client-side navigation.
PAGE_ROUTES = [
    {
        "page": "tierlist", "path": "/", "file": "index.html",
        "title_base": "MCOC YouTubers Tier List",
        "desc": "Marvel Contest of Champions tier list aggregated from top YouTubers Vega, Lagacy, MetalSonicDude and Seatin. Champion rankings for every class, awakening gems, sig stones, prestige and immunities — updated daily.",
        "h1": "Marvel Contest of Champions YouTubers Tier List",
        "intro": "A quick reference for casual players and newcomers. Rankings reflect general champion value across all game modes, aggregated from Vega, Lagacy, MetalSonicDude and Seatin and updated daily.",
    },
    {
        "page": "awakening", "path": "/awakening", "file": "awakening.html",
        "title_base": "MCOC Awakening Gem Tier List",
        "desc": "The best MCOC champions to use an Awakening Gem on, ranked by priority. A Marvel Contest of Champions awakening gem tier list from Vega, updated daily.",
        "h1": "MCOC Awakening Gem Tier List",
        "intro": "The best Marvel Contest of Champions champions to spend an Awakening Gem on, grouped by priority — so your generic and class gems go where they pay off most.",
    },
    {
        "page": "sigstones", "path": "/sig-stones", "file": "sig-stones.html",
        "title_base": "MCOC Signature Stone Tier List",
        "desc": "The best MCOC champions to invest Signature Stones into, ranked by priority. A Marvel Contest of Champions sig stone tier list from Vega, updated daily.",
        "h1": "MCOC Signature Stone Tier List",
        "intro": "Which Marvel Contest of Champions champions gain the most from a high signature ability, grouped by priority — so your sig stones go to the champions that truly need them.",
    },
    {
        "page": "prestige", "path": "/prestige", "file": "prestige.html",
        "title_base": "MCOC Prestige List",
        "desc": "MCOC champion prestige values for 7-star ranks R3, R4 and R5. A Marvel Contest of Champions prestige chart, updated daily.",
        "h1": "MCOC Prestige List",
        "intro": "Champion prestige values for 7-star ranks 3, 4 and 5 in Marvel Contest of Champions — search any champion to compare prestige and build your highest-prestige roster.",
    },
    {
        "page": "immunities", "path": "/immunities", "file": "immunities.html",
        "title_base": "MCOC Champion Immunity List",
        "desc": "Find MCOC champions by immunity and by the debuffs they inflict — who is immune to Bleed, Poison, Shock, Incinerate and more. A Marvel Contest of Champions immunity chart, updated daily.",
        "h1": "MCOC Champion Immunity List",
        "intro": "Search Marvel Contest of Champions champions by immunity and by the debuffs they inflict — find who shrugs off Bleed, Poison, Shock, Incinerate and more.",
    },
]


def _current_month():
    return datetime.now(timezone.utc).strftime("%B %Y")


def _render_page(base_html, route, month):
    """Derive one route's static HTML from the index.html base template."""
    import re
    title = f"{route['title_base']} - {month}"
    url = SITE_URL + route["path"]
    page = route["page"]

    def set_meta(html, selector, value):
        pat = r'(<meta ' + re.escape(selector) + r' content=")[^"]*(">)'
        return re.sub(pat, lambda m: m.group(1) + value + m.group(2), html, count=1)

    html = base_html
    html = re.sub(r"(<title>).*?(</title>)", lambda m: m.group(1) + title + m.group(2), html, count=1, flags=re.S)
    html = set_meta(html, 'name="description"', route["desc"])
    html = set_meta(html, 'property="og:title"', title)
    html = set_meta(html, 'property="og:description"', route["desc"])
    html = set_meta(html, 'name="twitter:title"', title)
    html = set_meta(html, 'name="twitter:description"', route["desc"])
    html = re.sub(r'(<meta property="og:url" content=")[^"]*(">)', lambda m: m.group(1) + url + m.group(2), html, count=1)
    html = re.sub(r'(<link rel="canonical" href=")[^"]*(">)', lambda m: m.group(1) + url + m.group(2), html, count=1)
    html = re.sub(r"(<h1>).*?(</h1>)", lambda m: m.group(1) + route["h1"] + m.group(2), html, count=1, flags=re.S)
    html = re.sub(r'(<p class="desc">).*?(</p>)', lambda m: m.group(1) + route["intro"] + m.group(2), html, count=1, flags=re.S)
    html = re.sub(r'("description":\s*")[^"]*(")', lambda m: m.group(1) + route["desc"] + m.group(2), html, count=1)
    # Activate this route's tab and page (normalize first, then set).
    html = html.replace('class="ptab active"', 'class="ptab"')
    html = re.sub(r'class="ptab" (data-page="%s")' % re.escape(page), r'class="ptab active" \1', html, count=1)
    html = html.replace('<div id="page-tierlist" class="page active">', '<div id="page-tierlist" class="page">')
    html = re.sub(r'(<div id="page-%s" class="page)(">)' % re.escape(page), r'\1 active\2', html, count=1)
    return html


def _generate_pages(base_dir):
    """Regenerate every per-route static page from the index.html base template."""
    index_path = base_dir / "public" / "index.html"
    if not index_path.exists():
        return
    base_html = index_path.read_text()
    month = _current_month()
    for route in PAGE_ROUTES:
        out = base_dir / "public" / route["file"]
        out.write_text(_render_page(base_html, route, month))
        print(f"  page: {route['path']}  ->  public/{route['file']}")


def main():
    # Try fresh fetch, fall back to cache
    data, meta, aw, sig = fetch_and_cache()
    if not data:
        data, meta, aw, sig = load_cached()
    if not data:
        print("ERROR: No data available")
        sys.exit(1)

    # Relabel the priority sheets onto the unified letter tiers.
    retier_priority(aw)
    retier_priority(sig)

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
        "tier_order": TIER_ORDER,
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

    # Regenerate the per-route static SEO pages (index + one per tab).
    _generate_pages(base)


if __name__ == "__main__":
    main()
