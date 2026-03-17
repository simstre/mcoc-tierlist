"""Vercel Cron Function: fetch fresh tier list data and commit to repo.

Triggered daily at 06:00 UTC via vercel.json cron config.
Fetches Google Sheets, builds the full tierlist.json response,
and commits it to the repo via GitHub API (triggering a redeploy).
"""
import base64
import json
import os
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler
from pathlib import Path

# Add lib/ to path so we can import our modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "lib"))

from champions_data import (
    compute_tier_list, get_champions_by_class,
    SOURCES, CLASS_COLORS, TIER_COLORS, TAG_LABELS,
)
from fetch_tierlist import fetch_and_combine, fetch_priority_sheets
from immunities import CHAMPION_IMMUNITIES, get_immunity_map, IMMUNITY_TYPES
from debuffs import fetch_debuff_data
from prestige_data import PRESTIGE, SIG_LEVELS, PRESTIGE_OPTIONS

import requests


def _load_portraits():
    """Load portrait data from lib/ JSON files."""
    portraits = {}
    lib_dir = Path(__file__).resolve().parent.parent.parent / "lib"
    for fname in ["portraits.json", "portraits_local.json", "mcochub_portraits.json"]:
        fpath = lib_dir / fname
        if fpath.exists():
            portraits.update(json.loads(fpath.read_text()))
    return portraits


def _build_tierlist_json():
    """Fetch all data and build the full API response."""
    combined, count, source_meta = fetch_and_combine()
    if not combined:
        return None

    aw_data, sig_data = fetch_priority_sheets()
    portraits = _load_portraits()
    debuff_map, champion_debuffs = fetch_debuff_data()

    champions = compute_tier_list(combined)
    for c in champions:
        c["portrait"] = portraits.get(c["name"])
        c["immunities"] = CHAMPION_IMMUNITIES.get(c["name"], [])
        c["inflicts"] = champion_debuffs.get(c["name"], [])

    by_class = get_champions_by_class(champions)

    return {
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
        "awakening_data": aw_data or {},
        "sig_stones_data": sig_data or {},
        "prestige": PRESTIGE,
        "prestige_sig_levels": SIG_LEVELS,
        "prestige_options": PRESTIGE_OPTIONS,
        "prestige_portraits": portraits,
        "source_meta": source_meta,
        "last_updated": datetime.now(timezone.utc).strftime("%B %d, %Y"),
        "total_champions": len(champions),
    }


def _commit_to_github(content_json):
    """Commit tierlist.json to the repo via GitHub API."""
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPO")
    if not token or not repo:
        return False, "GITHUB_TOKEN or GITHUB_REPO not set"

    path = "public/data/tierlist.json"
    api_url = f"https://api.github.com/repos/{repo}/contents/{path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    # Get current file SHA (needed for updates)
    resp = requests.get(api_url, headers=headers, timeout=10)
    sha = resp.json().get("sha") if resp.status_code == 200 else None

    # Commit the new content
    encoded = base64.b64encode(content_json.encode("utf-8")).decode("utf-8")
    payload = {
        "message": f"Update tier list data ({datetime.now(timezone.utc).strftime('%Y-%m-%d')})",
        "content": encoded,
        "branch": "main",
    }
    if sha:
        payload["sha"] = sha

    resp = requests.put(api_url, headers=headers, json=payload, timeout=15)
    if resp.status_code in (200, 201):
        return True, "Committed successfully"
    return False, f"GitHub API error {resp.status_code}: {resp.text[:200]}"


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Verify cron secret (Vercel sets this automatically)
        auth = self.headers.get("Authorization")
        cron_secret = os.environ.get("CRON_SECRET")
        if cron_secret and auth != f"Bearer {cron_secret}":
            self.send_response(401)
            self.end_headers()
            self.wfile.write(b"Unauthorized")
            return

        try:
            data = _build_tierlist_json()
            if not data:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(b"Failed to fetch tier list data")
                return

            content = json.dumps(data, separators=(",", ":"))
            ok, msg = _commit_to_github(content)

            self.send_response(200 if ok else 500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": ok,
                "message": msg,
                "champions": data["total_champions"],
            }).encode())

        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"Error: {e}".encode())
