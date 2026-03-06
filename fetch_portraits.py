"""Fetch champion portrait URLs from Fandom wiki API and save to portraits.json"""
import json
import re
import time
import urllib.request
import urllib.parse

from champions_data import RAW_CHAMPIONS

WIKI_API = "https://marvel-contestofchampions.fandom.com/api.php"
BATCH_SIZE = 20  # Fandom allows up to 50 titles per query
THUMB_SIZE = 80

# Map our champion names to Fandom wiki page titles
NAME_OVERRIDES = {
    "Hulkling": "Hulkling",
    "Thanos (Deathless)": "Thanos (Deathless)",
    "The Serpent": "The Serpent",
    "Cosmic Ghost Rider": "Cosmic Ghost Rider",
    "Dark Phoenix": "Dark Phoenix",
    "Adam Warlock": "Adam Warlock",
    "Captain Marvel (Movie)": "Captain Marvel (Movie)",
    "Captain Marvel (Classic)": "Captain Marvel",
    "Ms. Marvel (OG)": "Ms. Marvel",
    "Ms. Marvel (Kamala)": "Ms. Marvel (Kamala Khan)",
    "Venom the Duck": "Venom the Duck",
    "King Groot (Deathless)": "King Groot (Deathless)",
    "King Groot": "King Groot",
    "Vision (Aarkus)": "Vision (Aarkus)",
    "Super-Skrull": "Super-Skrull",
    "Spider-Man (Symbiote)": "Spider-Man (Symbiote)",
    "Jean Grey": "Jean Grey",
    "Mister Sinister": "Mister Sinister",
    "Deadpool (X-Force)": "Deadpool (X-Force)",
    "Cyclops (Blue Team)": "Cyclops (Blue Team)",
    "Cyclops (New Xavier School)": "Cyclops (New Xavier School)",
    "Magneto (Red)": "Magneto",
    "Magneto (House of X)": "Magneto (House of X)",
    "Storm (OG)": "Storm",
    "Storm (Pyramid X)": "Storm (Pyramid X)",
    "Wolverine (Weapon X)": "Wolverine (Weapon X)",
    "Wolverine (X-23)": "Wolverine (X-23)",
    "Wolverine (OG)": "Wolverine",
    "Old Man Logan": "Old Man Logan",
    "Spider-Man (Pavitr)": "Spider-Man (Pavitr Prabhakar)",
    "Nico Minoru": "Nico Minoru",
    "Absorbing Man": "Absorbing Man",
    "Black Widow (Claire Voyant)": "Black Widow (Claire Voyant)",
    "Scarlet Witch (Sigil)": "Scarlet Witch",
    "Scarlet Witch (Classic)": "Scarlet Witch (Classic)",
    "Guillotine (Deathless)": "Guillotine (Deathless)",
    "Iron Fist (Immortal)": "Iron Fist (Immortal)",
    "Spider-Woman (Jessica Drew)": "Spider-Woman",
    "Hulk (OG)": "Hulk",
    "Hulk (Immortal)": "Hulk (Immortal)",
    "Hulk (Ragnarok)": "Hulk (Ragnarok)",
    "Abomination (Immortal)": "Abomination (Immortal)",
    "Spider-Man (Classic)": "Spider-Man",
    "Spider-Man (Miles Morales)": "Spider-Man (Miles Morales)",
    "Spider-Man 2099": "Spider-Man 2099",
    "Spider-Man (Stark Enhanced)": "Spider-Man (Stark Enhanced)",
    "Spider-Man (Stealth Suit)": "Spider-Man (Stealth Suit)",
    "Spider-Man (Supreme)": "Spider-Man (Supreme)",
    "Captain America (Infinity War)": "Captain America (Infinity War)",
    "Captain America (Classic)": "Captain America",
    "Captain America (WWII)": "Captain America (WWII)",
    "Captain America (Sam Wilson)": "Captain America (Sam Wilson)",
    "Falcon (Joaquin Torres)": "Falcon (Joaquin Torres)",
    "Iron Man (OG)": "Iron Man",
    "Iron Man (Infinity War)": "Iron Man (Infinity War)",
    "Iron Man (Infamous)": "Iron Man (Infamous)",
    "She-Hulk (Deathless)": "She-Hulk (Deathless)",
    "Ant-Man (Future)": "Ant-Man (Future)",
    "Ultron (Prime)": "Ultron",
    "Ultron (Classic)": "Ultron (Classic)",
    "Vision (Age of Ultron)": "Vision (Age of Ultron)",
    "Vision (Classic)": "Vision",
    "Vision (Deathless)": "Vision (Deathless)",
    "Jack O'Lantern": "Jack O'Lantern",
    "M.O.D.O.K.": "M.O.D.O.K.",
    "Daredevil (Hell's Kitchen)": "Daredevil (Hell's Kitchen)",
    "Daredevil (Classic)": "Daredevil",
    "Black Widow (Deadly Origin)": "Black Widow (Deadly Origin)",
    "Black Widow (OG)": "Black Widow",
    "Black Panther (Civil War)": "Black Panther (Civil War)",
    "Black Panther (Classic)": "Black Panther",
    "Thor (Ragnarok)": "Thor (Ragnarok)",
    "Thor (Jane Foster)": "Thor (Jane Foster)",
    "Guillotine 2099": "Guillotine 2099",
    "Punisher 2099": "Punisher 2099",
    "Werewolf By Night": "Werewolf By Night",
    "Chee'ilth": "Chee'ilth",
}


def wiki_title(name):
    """Convert champion name to Fandom wiki page title."""
    return NAME_OVERRIDES.get(name, name)


def fetch_batch(titles):
    """Fetch portrait thumbnails for a batch of wiki titles."""
    joined = "|".join(titles)
    params = urllib.parse.urlencode({
        "action": "query",
        "titles": joined,
        "prop": "pageimages",
        "format": "json",
        "pithumbsize": THUMB_SIZE,
    })
    url = f"{WIKI_API}?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "MCOCTierList/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())

    results = {}
    pages = data.get("query", {}).get("pages", {})
    for page in pages.values():
        title = page.get("title", "")
        thumb = page.get("thumbnail", {}).get("source")
        if thumb:
            results[title] = thumb
    return results


def main():
    all_names = list(RAW_CHAMPIONS.keys())
    wiki_to_name = {}
    for name in all_names:
        wt = wiki_title(name)
        wiki_to_name[wt] = name

    wiki_titles = list(wiki_to_name.keys())
    portraits = {}
    found = 0
    missing = []

    for i in range(0, len(wiki_titles), BATCH_SIZE):
        batch = wiki_titles[i:i + BATCH_SIZE]
        print(f"Fetching batch {i // BATCH_SIZE + 1}/{(len(wiki_titles) + BATCH_SIZE - 1) // BATCH_SIZE}...")
        try:
            results = fetch_batch(batch)
            for wt, url in results.items():
                champ_name = wiki_to_name.get(wt)
                if champ_name:
                    portraits[champ_name] = url
                    found += 1
        except Exception as e:
            print(f"  Error: {e}")

        # Be polite to the API
        time.sleep(0.5)

    for name in all_names:
        if name not in portraits:
            missing.append(name)

    print(f"\nFound: {found}/{len(all_names)}")
    if missing:
        print(f"Missing ({len(missing)}): {missing}")

    with open("portraits.json", "w") as f:
        json.dump(portraits, f, indent=2)
    print("Saved to portraits.json")


if __name__ == "__main__":
    main()
