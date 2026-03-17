"""
Champion immunity data fetched from Fandom wiki category pages.
Each champion maps to list of {type, conditional} dicts.
Conditional annotations are manually curated.
Synergy-only immunities are excluded via SYNERGY_ONLY blocklist.
"""
import json
import logging
import time
import urllib.parse
import urllib.request
from pathlib import Path

logger = logging.getLogger("mcoc-immunities")

WIKI_API = "https://marvel-contestofchampions.fandom.com/api.php"
CACHE_PATH = Path(__file__).parent / "cached_immunities.json"

IMMUNITY_TYPES = [
    "Bleed",
    "Poison",
    "Incinerate",
    "Shock",
    "Coldsnap",
    "Frostbite",
    "Nullify",
    "Stagger",
    "Armor Break",
    "Armor Shattered",
    "Fate Seal",
    "Heal Block",
    "Power Drain",
    "Power Lock",
    "Power Burn",
    "Power Steal",
    "Rupture",
    "Buff Immunity",
    "Inverted Controls",
    "Regen Rate Mod",
]

# Wiki category name -> display name
IMMUNITY_CATEGORIES = {
    "Bleed_Immunity": "Bleed",
    "Poison_Immunity": "Poison",
    "Incinerate_Immunity": "Incinerate",
    "Shock_Immunity": "Shock",
    "Coldsnap_Immunity": "Coldsnap",
    "Frostbite_Immunity": "Frostbite",
    "Nullify_Immunity": "Nullify",
    "Stagger_Immunity": "Stagger",
    "Armor_Break_Immunity": "Armor Break",
    "Armor_Shattered_Immunity": "Armor Shattered",
    "Fate_Seal_Immunity": "Fate Seal",
    "Heal_Block_Immunity": "Heal Block",
    "Power_Drain_Immunity": "Power Drain",
    "Power_Lock_Immunity": "Power Lock",
    "Power_Burn_Immunity": "Power Burn",
    "Power_Steal_Immunity": "Power Steal",
    "Rupture_Immunity": "Rupture",
    "Buff_Immunity": "Buff Immunity",
    "Inverted_Controls_Immunity": "Inverted Controls",
    "Regeneration_Rate_Modification_Immunity": "Regen Rate Mod",
}

# Champions whose immunity to a given type is synergy-only (exclude from results)
SYNERGY_ONLY = {
    "Doctor Strange": ["Coldsnap"],
    "Dormammu": ["Incinerate"],
    "Hulk": ["Nullify", "Stagger", "Fate Seal"],
    "Mordo": ["Nullify", "Fate Seal"],
    "The Champion": ["Fate Seal"],
    "Titania": ["Bleed"],
    "Venompool": ["Incinerate", "Shock", "Armor Break"],
    "Vulture": ["Poison", "Shock", "Nullify"],
    "Absorbing Man": ["Poison"],  # synergy with Abomination (Immortal)
    "Emma Frost": ["Inverted Controls"],  # she inflicts it, not immune to it
}

# Champions whose immunity to a given type requires a condition (mode, buff, pre-fight, etc.)
CONDITIONAL = {
    "Absorbing Man": ["Bleed", "Incinerate", "Shock", "Coldsnap", "Frostbite"],
    "Adam Warlock": ["Incinerate", "Shock", "Coldsnap", "Frostbite", "Nullify", "Stagger", "Fate Seal"],
    "Apocalypse": ["Bleed", "Incinerate"],
    "Arcade": ["Poison", "Incinerate", "Shock"],
    "Black Widow (Claire Voyant)": ["Bleed", "Poison", "Incinerate"],
    "Emma Frost": ["Bleed", "Poison", "Incinerate", "Shock", "Coldsnap", "Frostbite"],
    "Iron Man": ["Incinerate", "Coldsnap", "Frostbite", "Nullify", "Stagger"],
    "Iron Man (Infamous)": ["Incinerate", "Shock"],
    "Iron Man (Infinity War)": ["Bleed", "Coldsnap"],
    "Ironheart": ["Incinerate", "Coldsnap", "Frostbite"],
    "Mangog": ["Incinerate", "Shock", "Coldsnap", "Frostbite"],
    "Scorpion": ["Poison", "Shock"],
    "Viv Vision": ["Nullify", "Fate Seal"],
}

# Hardcoded fallback data (used if wiki fetch fails and no cache exists)
CHAMPION_IMMUNITIES_FALLBACK = {
    "Abomination": ["Poison"],
    "Abomination (Immortal)": ["Poison"],
    "Absorbing Man": ["Bleed", "Incinerate", "Shock", "Coldsnap", "Frostbite", "Armor Break"],
    "Adam Warlock": ["Incinerate", "Shock", "Coldsnap", "Frostbite", "Nullify", "Stagger", "Fate Seal"],
    "Annihilus": ["Incinerate", "Coldsnap", "Frostbite"],
    "Ant-Man": ["Poison", "Shock"],
    "Anti-Venom": ["Poison", "Incinerate"],
    "Apocalypse": ["Bleed", "Incinerate"],
    "Arcade": ["Poison", "Incinerate", "Shock"],
    "Arnim Zola": ["Bleed", "Poison"],
    "Attuma": ["Incinerate"],
    "Beta Ray Bill": ["Shock"],
    "Black Bolt": ["Poison"],
    "Black Widow (Claire Voyant)": ["Bleed", "Poison", "Incinerate"],
    "Blue Marvel": ["Bleed"],
    "Captain Marvel (Classic)": ["Poison"],
    "Captain Marvel (Movie)": ["Poison"],
    "Cassie Lang": ["Poison", "Shock"],
    "Civil Warrior": ["Nullify", "Stagger"],
    "Colossus": ["Bleed", "Incinerate", "Coldsnap", "Frostbite", "Armor Break"],
    "Cosmic Ghost Rider": ["Bleed", "Incinerate"],
    "Count Nefaria": ["Bleed"],
    "Crossbones": ["Nullify", "Stagger"],
    "Dark Phoenix": ["Incinerate"],
    "Darkhawk": ["Bleed", "Poison"],
    "Dazzler": ["Nullify"],
    "Diablo": ["Armor Break"],
    "Doctor Doom": ["Shock", "Armor Break"],
    "Dormammu": ["Bleed", "Poison"],
    "Dragon Man": ["Bleed", "Poison"],
    "Dust": ["Bleed", "Poison", "Shock"],
    "Electro": ["Shock"],
    "Emma Frost": ["Bleed", "Poison", "Incinerate", "Shock", "Coldsnap", "Frostbite"],
    "Franken-Castle": ["Poison"],
    "Galan": ["Nullify", "Fate Seal"],
    "Gentle": ["Bleed"],
    "Ghost Rider": ["Bleed", "Incinerate"],
    "Groot": ["Bleed"],
    "Guillotine 2099": ["Bleed", "Poison"],
    "Havok": ["Incinerate"],
    "Hawkeye": ["Poison"],
    "Heimdall": ["Fate Seal"],
    "Howard the Duck": ["Bleed"],
    "Hulk": ["Poison"],
    "Hulk (Immortal)": ["Poison"],
    "Hulk (Ragnarok)": ["Poison"],
    "Hulkling": ["Poison", "Shock"],
    "Human Torch": ["Incinerate", "Coldsnap", "Frostbite"],
    "Hyperion": ["Poison"],
    "Iceman": ["Bleed", "Poison", "Incinerate", "Coldsnap", "Frostbite"],
    "Ikaris": ["Incinerate", "Shock"],
    "Imperiosa": ["Bleed"],
    "Iron Man": ["Incinerate", "Coldsnap", "Frostbite", "Nullify", "Stagger"],
    "Iron Man (Infamous)": ["Incinerate", "Shock"],
    "Iron Man (Infinity War)": ["Bleed", "Coldsnap"],
    "Ironheart": ["Incinerate", "Coldsnap", "Frostbite"],
    "Isophyne": ["Bleed", "Coldsnap", "Frostbite"],
    "Jack O'Lantern": ["Incinerate"],
    "Joe Fixit": ["Poison"],
    "Karolina Dean": ["Coldsnap", "Frostbite"],
    "Kindred": ["Poison", "Incinerate"],
    "King Groot": ["Bleed"],
    "King Groot (Deathless)": ["Bleed"],
    "Kitty Pryde": ["Incinerate"],
    "Korg": ["Bleed", "Shock"],
    "Kushala": ["Bleed", "Incinerate"],
    "Lizard": ["Poison"],
    "Luke Cage": ["Bleed"],
    "Lumatrix": ["Bleed"],
    "M'Baku": ["Frostbite"],
    "Magneto (House of X)": ["Bleed"],
    "Man-Thing": ["Bleed", "Armor Break"],
    "Mangog": ["Bleed", "Incinerate", "Shock", "Coldsnap", "Frostbite", "Nullify", "Armor Break"],
    "Medusa": ["Poison"],
    "Mephisto": ["Poison", "Coldsnap", "Frostbite"],
    "Mister Negative": ["Nullify", "Stagger", "Fate Seal"],
    "Mole Man": ["Shock"],
    "Morningstar": ["Bleed"],
    "Ms. Marvel": ["Poison"],
    "Ms. Marvel (Kamala Khan)": ["Poison"],
    "Mysterio": ["Poison"],
    "Nebula": ["Bleed", "Poison", "Shock"],
    "Nico Minoru": ["Poison"],
    "Night Thrasher": ["Incinerate"],
    "Nimrod": ["Bleed", "Poison"],
    "Omega Red": ["Poison"],
    "Omega Sentinel": ["Nullify", "Stagger", "Fate Seal"],
    "Peni Parker": ["Poison", "Incinerate"],
    "Phoenix": ["Incinerate"],
    "Photon": ["Bleed"],
    "Prowler": ["Bleed", "Incinerate"],
    "Purgatory": ["Incinerate"],
    "Red Goblin": ["Incinerate"],
    "Red Hulk": ["Poison", "Incinerate"],
    "Red Skull": ["Nullify", "Stagger", "Fate Seal"],
    "Ronan": ["Poison"],
    "Sabretooth": ["Coldsnap", "Frostbite"],
    "Sandman": ["Bleed", "Poison", "Shock"],
    "Sasquatch": ["Frostbite", "Armor Break"],
    "Sauron": ["Poison"],
    "Scorpion": ["Poison", "Shock"],
    "Sentinel": ["Bleed", "Poison", "Coldsnap", "Frostbite", "Armor Break"],
    "Sentry": ["Incinerate", "Nullify", "Fate Seal"],
    "She-Hulk": ["Poison"],
    "She-Hulk (Deathless)": ["Poison"],
    "Shocker": ["Shock"],
    "Shuri": ["Shock"],
    "Silver Centurion": ["Bleed", "Shock"],
    "Silver Surfer": ["Shock", "Coldsnap", "Frostbite"],
    "Solvarch": ["Bleed", "Poison"],
    "Spider-Slayer (J. Jonah Jameson)": ["Bleed", "Poison"],
    "Spider-Woman (Jessica Drew)": ["Poison"],
    "Storm": ["Shock"],
    "Storm (Pyramid X)": ["Shock", "Coldsnap", "Frostbite"],
    "Sunspot": ["Incinerate"],
    "Super-Skrull": ["Incinerate", "Shock"],
    "Terrax": ["Bleed", "Shock"],
    "Thanos (Deathless)": ["Poison", "Coldsnap", "Frostbite"],
    "The Destroyer": ["Bleed", "Poison", "Armor Break"],
    "The Leader": ["Poison"],
    "The Overseer": ["Poison", "Nullify", "Stagger", "Fate Seal"],
    "The Serpent": ["Coldsnap", "Nullify", "Stagger", "Fate Seal"],
    "Thing": ["Bleed", "Shock", "Nullify", "Stagger", "Armor Break", "Fate Seal"],
    "Toad": ["Poison"],
    "Ultron": ["Bleed", "Poison"],
    "Ultron (Classic)": ["Bleed", "Poison"],
    "Unstoppable Colossus": ["Bleed"],
    "Vision": ["Bleed", "Poison"],
    "Vision (Age of Ultron)": ["Bleed", "Poison"],
    "Vision (Deathless)": ["Bleed", "Poison", "Coldsnap", "Frostbite"],
    "Viv Vision": ["Bleed", "Poison", "Nullify", "Fate Seal"],
    "Void": ["Incinerate"],
    "Vox": ["Poison"],
    "Vulture": ["Incinerate"],
    "Warlock": ["Coldsnap", "Frostbite"],
    "X-23 (Orochi)": ["Bleed"],
}


def _fetch_category_members(category):
    """Fetch all champion page titles from a wiki category."""
    members = []
    cmcontinue = None
    while True:
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": f"Category:{category}",
            "cmlimit": "500",
            "cmtype": "page",
            "format": "json",
        }
        if cmcontinue:
            params["cmcontinue"] = cmcontinue
        url = f"{WIKI_API}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={"User-Agent": "MCOCTierList/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        for member in data.get("query", {}).get("categorymembers", []):
            title = member.get("title", "")
            if ":" in title or not title:
                continue
            members.append(title)
        cont = data.get("continue", {})
        cmcontinue = cont.get("cmcontinue")
        if not cmcontinue:
            break
    return members


def fetch_immunity_data():
    """Fetch immunity data from Fandom wiki categories.

    Returns dict: {champion_name: [immunity_types]}
    Applies SYNERGY_ONLY filtering.
    """
    champion_immunities = {}

    for category, display_name in IMMUNITY_CATEGORIES.items():
        try:
            members = _fetch_category_members(category)
            logger.info(f"Fetched {display_name} Immunity: {len(members)} champions")

            for champ in members:
                # Skip synergy-only immunities
                if champ in SYNERGY_ONLY and display_name in SYNERGY_ONLY[champ]:
                    continue
                if champ not in champion_immunities:
                    champion_immunities[champ] = []
                champion_immunities[champ].append(display_name)

            time.sleep(0.3)
        except Exception as e:
            logger.warning(f"Failed to fetch {display_name} Immunity: {e}")

    # Sort each champion's immunities in IMMUNITY_TYPES order
    type_order = {t: i for i, t in enumerate(IMMUNITY_TYPES)}
    for name in champion_immunities:
        champion_immunities[name].sort(key=lambda x: type_order.get(x, 99))

    return champion_immunities


def fetch_and_cache_immunities():
    """Fetch immunity data and cache to disk."""
    champion_immunities = fetch_immunity_data()
    CACHE_PATH.write_text(json.dumps(champion_immunities, indent=2))
    logger.info(f"Cached immunity data: {len(champion_immunities)} champions")
    return champion_immunities


def load_cached_immunities():
    """Load cached immunity data."""
    if CACHE_PATH.exists():
        try:
            return json.loads(CACHE_PATH.read_text())
        except Exception as e:
            logger.error(f"Failed to load immunity cache: {e}")
    return None


def _apply_conditional(champion_immunities):
    """Apply conditional annotations to raw immunity data.

    Takes {champion: [types]} and returns {champion: [{type, conditional}]}.
    """
    result = {}
    for name, imm_types in champion_immunities.items():
        cond_list = CONDITIONAL.get(name, [])
        result[name] = [
            {"type": t, "conditional": t in cond_list}
            for t in imm_types
        ]
    return result


def get_immunities_for_champion(name, champion_immunities=None):
    """Returns list of {type, conditional} dicts for a champion."""
    if champion_immunities is None:
        champion_immunities = CHAMPION_IMMUNITIES_FALLBACK
    imm_types = champion_immunities.get(name, [])
    if not imm_types:
        return []
    # Handle both raw list format and already-annotated format
    if imm_types and isinstance(imm_types[0], dict):
        return imm_types
    cond_list = CONDITIONAL.get(name, [])
    return [{"type": t, "conditional": t in cond_list} for t in imm_types]


def get_immunity_map(champion_immunities=None):
    """Returns {immunity_type: [champion_names]}"""
    if champion_immunities is None:
        champion_immunities = CHAMPION_IMMUNITIES_FALLBACK
    result = {t: [] for t in IMMUNITY_TYPES}
    for name, imm_list in champion_immunities.items():
        for entry in imm_list:
            t = entry["type"] if isinstance(entry, dict) else entry
            if t in result:
                result[t].append(name)
    for t in result:
        result[t].sort()
    return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    raw = fetch_and_cache_immunities()
    annotated = _apply_conditional(raw)
    print(f"\n{len(annotated)} champions with immunities")
    cond_count = sum(1 for imms in annotated.values() if any(i["conditional"] for i in imms))
    print(f"{cond_count} with conditional immunities")
    for imm_type in IMMUNITY_TYPES:
        count = sum(1 for imms in annotated.values() if any(i["type"] == imm_type for i in imms))
        print(f"  {imm_type}: {count}")
