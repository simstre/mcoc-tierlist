"""
Champion immunity data aggregated from Fandom wiki category pages.
Each champion maps to {always: [...], conditional: [...]}.
Synergy-only immunities are excluded entirely.
"""

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
    "Fate Seal",
]

# Champions mapped to their immunities
# Format: {"always": [...], "conditional": [...]}
# Shorthand: plain list = all always-active
CHAMPION_IMMUNITIES = {
    "Abomination": ["Poison"],
    "Abomination (Immortal)": ["Poison"],
    "Absorbing Man": {"always": ["Armor Break"], "conditional": ["Bleed", "Incinerate", "Shock", "Coldsnap", "Frostbite"]},
    "Adam Warlock": {"always": [], "conditional": ["Incinerate", "Shock", "Coldsnap", "Frostbite", "Nullify", "Stagger", "Fate Seal"]},
    "Annihilus": ["Incinerate", "Coldsnap", "Frostbite"],
    "Ant-Man": ["Poison", "Shock"],
    "Anti-Venom": ["Poison", "Incinerate"],
    "Apocalypse": {"always": [], "conditional": ["Bleed", "Incinerate"]},
    "Arcade": {"always": [], "conditional": ["Poison", "Incinerate", "Shock"]},
    "Arnim Zola": ["Bleed", "Poison"],
    "Attuma": ["Incinerate"],
    "Beta Ray Bill": ["Shock"],
    "Black Bolt": ["Poison"],
    "Black Widow (Claire Voyant)": {"always": [], "conditional": ["Bleed", "Poison", "Incinerate"]},
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
    "Emma Frost": {"always": [], "conditional": ["Bleed", "Poison", "Incinerate", "Shock", "Coldsnap", "Frostbite"]},
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
    "Iron Man": {"always": [], "conditional": ["Incinerate", "Coldsnap", "Frostbite", "Nullify", "Stagger"]},
    "Iron Man (Infamous)": {"always": [], "conditional": ["Incinerate", "Shock"]},
    "Iron Man (Infinity War)": {"always": [], "conditional": ["Bleed", "Coldsnap"]},
    "Ironheart": {"always": [], "conditional": ["Incinerate", "Coldsnap", "Frostbite"]},
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
    "Mangog": {"always": ["Bleed", "Armor Break"], "conditional": ["Incinerate", "Shock", "Coldsnap", "Frostbite"]},
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
    "Scorpion": {"always": [], "conditional": ["Poison", "Shock"]},
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
    "Venompool": {"always": [], "conditional": ["Incinerate", "Shock", "Armor Break"]},
    "Vision": ["Bleed", "Poison"],
    "Vision (Age of Ultron)": ["Bleed", "Poison"],
    "Vision (Deathless)": ["Bleed", "Poison", "Coldsnap", "Frostbite"],
    "Viv Vision": {"always": ["Bleed", "Poison"], "conditional": ["Nullify", "Fate Seal"]},
    "Void": ["Incinerate"],
    "Vox": ["Poison"],
    "Vulture": ["Incinerate"],
    "Warlock": ["Coldsnap", "Frostbite"],
    "X-23 (Orochi)": ["Bleed"],
}


def _normalize(entry):
    """Normalize entry to {always: [], conditional: []} format."""
    if isinstance(entry, list):
        return {"always": entry, "conditional": []}
    return entry


def get_immunities_for_champion(name: str) -> list[dict]:
    """Returns list of {type, conditional} dicts for a champion."""
    entry = CHAMPION_IMMUNITIES.get(name)
    if not entry:
        return []
    norm = _normalize(entry)
    result = []
    for imm in norm["always"]:
        result.append({"type": imm, "conditional": False})
    for imm in norm["conditional"]:
        result.append({"type": imm, "conditional": True})
    return result


def get_champions_by_immunity(immunity_type: str) -> list[str]:
    result = []
    for name, entry in CHAMPION_IMMUNITIES.items():
        norm = _normalize(entry)
        if immunity_type in norm["always"] or immunity_type in norm["conditional"]:
            result.append(name)
    return sorted(result)


def get_immunity_map() -> dict[str, list[str]]:
    """Returns {immunity_type: [champion_names]}"""
    result = {}
    for imm_type in IMMUNITY_TYPES:
        result[imm_type] = get_champions_by_immunity(imm_type)
    return result
