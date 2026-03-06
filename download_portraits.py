"""Download all champion portraits locally to avoid hotlink issues."""
import json
import hashlib
import time
import urllib.request

with open("portraits.json") as f:
    portraits = json.load(f)

local_map = {}
total = len(portraits)

for i, (name, url) in enumerate(portraits.items()):
    # Create a safe filename from champion name
    safe = hashlib.md5(name.encode()).hexdigest()[:10]
    filename = f"{safe}.png"
    filepath = f"static/portraits/{filename}"

    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
            "Referer": "https://marvel-contestofchampions.fandom.com/",
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read()
            with open(filepath, "wb") as f:
                f.write(data)
            local_map[name] = f"/static/portraits/{filename}"
    except Exception as e:
        print(f"  FAIL: {name} - {e}")

    if (i + 1) % 50 == 0:
        print(f"  {i + 1}/{total}...")
        time.sleep(0.3)

with open("portraits_local.json", "w") as f:
    json.dump(local_map, f, indent=2)

print(f"Done: {len(local_map)}/{total} downloaded")
