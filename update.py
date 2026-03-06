#!/usr/bin/env python3
"""
Daily update script for MCOC Tier List.
Fetches latest data from Summoner's Tier List spreadsheet and downloads new portraits.

Usage:
  python update.py          # Run once
  python update.py --cron   # Install/update daily cron job
"""
import csv
import hashlib
import io
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).parent
SPREADSHEET_ID = "1WZHQvaH_qx22b2G-TpTvgexP9rWy-4S9mWqQAOg1LSg"
WIKI_API = "https://marvel-contestofchampions.fandom.com/api.php"
PORTRAITS_DIR = BASE_DIR / "static" / "portraits"


def fetch_spreadsheet():
    """Fetch latest tier list data from Google Sheets."""
    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid=0"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (MCOCTierList/1.0)",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            # Follow redirect
            final_url = resp.geturl()
            if final_url != url:
                req2 = urllib.request.Request(final_url, headers={
                    "User-Agent": "Mozilla/5.0 (MCOCTierList/1.0)",
                })
                with urllib.request.urlopen(req2, timeout=30) as resp2:
                    return resp2.read().decode("utf-8")
            return resp.read().decode("utf-8")
    except Exception as e:
        print(f"Failed to fetch spreadsheet: {e}")
        return None


def fetch_portrait(name, wiki_title):
    """Fetch a single champion portrait from Fandom wiki."""
    params = urllib.parse.urlencode({
        "action": "query",
        "titles": wiki_title,
        "prop": "pageimages",
        "format": "json",
        "pithumbsize": 80,
    })
    url = f"{WIKI_API}?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "MCOCTierList/1.0"})

    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())

    pages = data.get("query", {}).get("pages", {})
    for page in pages.values():
        thumb_url = page.get("thumbnail", {}).get("source")
        if thumb_url:
            return thumb_url
    return None


def download_portrait(name, image_url):
    """Download portrait image to local static dir."""
    safe = hashlib.md5(name.encode()).hexdigest()[:10]
    filename = f"{safe}.png"
    filepath = PORTRAITS_DIR / filename

    req = urllib.request.Request(image_url, headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        "Referer": "https://marvel-contestofchampions.fandom.com/",
    })
    with urllib.request.urlopen(req, timeout=10) as resp:
        filepath.write_bytes(resp.read())

    return f"/static/portraits/{filename}"


def update_portraits(champion_names):
    """Download portraits for any champions not yet in portraits_local.json."""
    portraits_path = BASE_DIR / "portraits_local.json"
    if portraits_path.exists():
        portraits = json.loads(portraits_path.read_text())
    else:
        portraits = {}

    new_champs = [n for n in champion_names if n not in portraits]
    if not new_champs:
        print("All portraits up to date.")
        return portraits

    print(f"Downloading {len(new_champs)} new portrait(s)...")
    for name in new_champs:
        wiki_name = name
        # Handle common name mappings
        for old, new in [
            ("(OG)", ""), ("(Classic)", "(Classic)"), ("(Movie)", ""),
        ]:
            pass  # Wiki usually matches our names

        try:
            image_url = fetch_portrait(name, wiki_name)
            if image_url:
                local_path = download_portrait(name, image_url)
                portraits[name] = local_path
                print(f"  + {name}")
            else:
                print(f"  ? {name} (no image found)")
        except Exception as e:
            print(f"  ! {name}: {e}")
        time.sleep(0.3)

    portraits_path.write_text(json.dumps(portraits, indent=2))
    return portraits


def setup_cron():
    """Install a daily cron job to run this script."""
    import subprocess
    script_path = Path(__file__).resolve()
    python_path = BASE_DIR / "venv" / "bin" / "python"
    log_path = BASE_DIR / "update.log"

    cron_line = f"0 6 * * * {python_path} {script_path} >> {log_path} 2>&1"

    # Get existing crontab
    try:
        result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
        existing = result.stdout
    except Exception:
        existing = ""

    # Check if already installed
    if str(script_path) in existing:
        print("Cron job already installed. Updating...")
        lines = [l for l in existing.strip().split("\n") if str(script_path) not in l]
        lines.append(cron_line)
        new_crontab = "\n".join(lines) + "\n"
    else:
        new_crontab = existing.rstrip() + "\n" + cron_line + "\n"

    subprocess.run(["crontab", "-"], input=new_crontab, text=True, check=True)
    print(f"Cron job installed: daily at 6:00 AM")
    print(f"Logs: {log_path}")


def main():
    if "--cron" in sys.argv:
        setup_cron()
        return

    from datetime import datetime
    print(f"=== MCOC Tier List Update - {datetime.now().strftime('%Y-%m-%d %H:%M')} ===")

    # Load current champion names from data
    from champions_data import RAW_CHAMPIONS
    champion_names = list(RAW_CHAMPIONS.keys())

    # Update portraits for any missing champions
    PORTRAITS_DIR.mkdir(parents=True, exist_ok=True)
    update_portraits(champion_names)

    print("Done.")


if __name__ == "__main__":
    main()
