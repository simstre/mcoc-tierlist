"""Self-host portraits for any champion missing a browser-usable image.

Every champion in the current combined tier list should have a portrait
that actually loads in the browser. Two portrait sources already work in the
browser: locally-mirrored files under public/portraits/ (served at
/portraits/...) and mcochub.insaneskull.com URLs. Raw Fandom wiki URLs do NOT
work at serve time — Fandom blocks hotlinking by Referer, so those 404 in the
browser even though they resolve server-side.

This script finds champions that have neither a local file nor an mcochub URL,
discovers a portrait URL for them (Fandom wiki API, then mcochub), downloads a
copy into public/portraits/, and registers it in lib/portraits_local.json —
the file the Vercel build (generate_data.py / api/cron/refresh.py) reads and
which overrides raw URLs at build time. Idempotent: already-covered champions
are skipped, so re-runs only fetch genuinely new champions.

Run daily by .github/workflows/refresh-portraits.yml, or locally:
    venv/bin/python3 mirror_portraits.py
"""
import hashlib
import json
import logging
import urllib.request
from pathlib import Path

from fetch_tierlist import fetch_and_combine
from fetch_portraits import _fetch_from_wiki, _fetch_from_mcochub

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("mcoc-mirror")

BASE = Path(__file__).parent
PUBLIC_PORTRAITS = BASE / "public" / "portraits"
LIB = BASE / "lib"
LOCAL_JSON = LIB / "portraits_local.json"   # name -> /portraits/<hash>.<ext>  (self-hosted)
URL_JSON = LIB / "portraits.json"           # name -> Fandom wiki URL          (discovery cache)
HUB_JSON = LIB / "mcochub_portraits.json"   # name -> mcochub URL              (works in browser)

# Fandom serves the image only when the Referer looks like their own site.
WIKI_REFERER = "https://marvel-contestofchampions.fandom.com/"


def _load(path):
    return json.loads(path.read_text()) if path.exists() else {}


def _save(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n")


def _download_local(url, name):
    """Download `url` into public/portraits/ and return its /portraits/ path."""
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        "Referer": WIKI_REFERER,
    })
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = resp.read()
    # Fandom's CDN returns webp; keep whatever the bytes actually are.
    ext = ".webp" if data[:4] == b"RIFF" else ".png"
    fname = hashlib.md5(name.encode()).hexdigest()[:10] + ext
    PUBLIC_PORTRAITS.mkdir(parents=True, exist_ok=True)
    (PUBLIC_PORTRAITS / fname).write_bytes(data)
    return f"/portraits/{fname}"


def _needs_hosting(portrait):
    """A portrait needs self-hosting if it is missing or a raw Fandom wiki URL
    (Fandom blocks hotlinking, so those 404 in the browser). Local paths and
    mcochub URLs already work in the browser."""
    return (not portrait) or ("static.wikia.nocookie.net" in portrait)


def main():
    combined, count, _ = fetch_and_combine()
    if not combined or not count:
        logger.error("No tier list data fetched; aborting without changes.")
        return 1
    champions = list(combined.keys())

    local = _load(LOCAL_JSON)
    urls = _load(URL_JSON)
    hub = _load(HUB_JSON)

    # Resolve each champion's portrait exactly as the build does
    # (generate_data.py / api/cron/refresh.py): portraits.json, then
    # portraits_local.json, then mcochub_portraits.json (last wins).
    merged = {}
    for source in (urls, local, hub):
        merged.update(source)

    need = [n for n in champions if _needs_hosting(merged.get(n))]
    if not need:
        logger.info("All %d champions already have a browser-usable portrait.", len(champions))
        return 0

    logger.info("%d champion(s) need a self-hosted portrait: %s", len(need), need)

    # Champions with no portrait at all need a URL discovered (wiki, then mcochub).
    # Champions already resolving to a wiki URL are downloaded from that URL.
    no_url = [n for n in need if not merged.get(n)]
    if no_url:
        urls.update(_fetch_from_wiki(no_url))
        still = [n for n in no_url if n not in urls]
        if still:
            urls.update(_fetch_from_mcochub(still))

    mirrored, failed = [], []
    for name in need:
        url = urls.get(name) or merged.get(name)
        if not url:
            failed.append(name)
            continue
        try:
            local[name] = _download_local(url, name)
            mirrored.append(name)
            logger.info("  + %s -> %s", name, local[name])
        except Exception as e:
            failed.append(name)
            logger.warning("  ! %s: %s", name, e)

    if mirrored:
        _save(LOCAL_JSON, local)
        _save(URL_JSON, urls)
        logger.info("Mirrored %d new portrait(s) into public/portraits/.", len(mirrored))
    if failed:
        logger.warning("No portrait found for %d champion(s): %s", len(failed), failed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
