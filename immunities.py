"""
Champion immunity data aggregated from mcoc-guide.com and pockettactics.com.
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
CHAMPION_IMMUNITIES = {
    "Abomination": ["Poison"],
    "Abomination (Immortal)": ["Poison"],
    "Annihilus": ["Coldsnap", "Frostbite", "Incinerate"],
    "Ant-Man": ["Poison", "Shock"],
    "Anti-Venom": ["Incinerate"],
    "Black Bolt": ["Poison"],
    "Black Widow (Claire Voyant)": ["Bleed", "Incinerate"],
    "Captain Marvel (Classic)": ["Poison"],
    "Captain Marvel (Movie)": ["Poison"],
    "Cassie Lang": ["Shock"],
    "Civil Warrior": ["Nullify", "Stagger"],
    "Colossus": ["Bleed", "Incinerate", "Coldsnap", "Frostbite", "Armor Break"],
    "Cosmic Ghost Rider": ["Bleed", "Incinerate"],
    "Darkhawk": ["Bleed", "Poison"],
    "Doctor Doom": ["Shock", "Armor Break"],
    "Dormammu": ["Bleed", "Poison"],
    "Dragon Man": ["Bleed"],
    "Electro": ["Shock"],
    "Gambit": ["Bleed"],
    "Ghost Rider": ["Bleed", "Incinerate"],
    "Groot": ["Bleed"],
    "Guillotine 2099": ["Bleed", "Poison"],
    "Havok": ["Incinerate"],
    "Howard the Duck": ["Bleed"],
    "Hulk": ["Poison"],
    "Hulk (Immortal)": ["Poison"],
    "Hulk (Ragnarok)": ["Poison"],
    "Human Torch": ["Incinerate", "Coldsnap", "Frostbite"],
    "Hyperion": ["Poison"],
    "Iceman": ["Bleed", "Poison", "Incinerate"],
    "Ikaris": ["Incinerate", "Shock"],
    "Joe Fixit": ["Poison"],
    "Juggernaut": [],
    "Hulkling": ["Shock"],
    "Kamala Khan": ["Poison"],
    "Kindred": ["Incinerate"],
    "King Groot": ["Bleed"],
    "Kitty Pryde": ["Incinerate"],
    "Korg": ["Bleed", "Shock"],
    "Luke Cage": ["Bleed"],
    "Magneto (House of X)": ["Bleed"],
    "Man-Thing": ["Bleed", "Armor Break"],
    "Mangog": ["Bleed", "Armor Break"],
    "Medusa": ["Poison"],
    "Mephisto": ["Incinerate", "Coldsnap", "Frostbite"],
    "Mister Negative": ["Nullify", "Stagger", "Fate Seal"],
    "Mister Sinister": [],
    "Mole Man": ["Shock"],
    "Morningstar": ["Bleed"],
    "Ms. Marvel": ["Poison"],
    "Ms. Marvel (Kamala Khan)": ["Poison"],
    "Mysterio": ["Poison"],
    "Nebula": ["Bleed", "Poison"],
    "Night Thrasher": ["Incinerate"],
    "Nimrod": ["Bleed"],
    "Omega Red": ["Poison"],
    "The Overseer": ["Nullify", "Stagger", "Fate Seal"],
    "Peni Parker": ["Poison", "Incinerate"],
    "Professor X": [],
    "Purgatory": ["Incinerate"],
    "Red Goblin": ["Incinerate"],
    "Red Hulk": ["Poison", "Incinerate"],
    "Ronan": ["Poison"],
    "Sabretooth": ["Coldsnap", "Frostbite"],
    "Sandman": ["Poison", "Shock"],
    "Sasquatch": ["Frostbite", "Armor Break"],
    "Sentinel": ["Bleed", "Poison"],
    "She-Hulk": ["Poison"],
    "Shocker": ["Shock"],
    "Shuri": ["Shock"],
    "Silver Surfer": ["Incinerate", "Shock", "Coldsnap", "Frostbite"],
    "Storm": ["Shock"],
    "Storm (Pyramid X)": ["Shock", "Coldsnap", "Frostbite"],
    "Stryfe": ["Shock"],
    "Sunspot": ["Incinerate"],
    "Super-Skrull": ["Incinerate", "Shock"],
    "Terrax": ["Bleed", "Shock"],
    "Thing": ["Bleed", "Shock", "Nullify", "Stagger", "Fate Seal", "Armor Break"],
    "Toad": ["Poison"],
    "Ultron": ["Bleed", "Poison"],
    "Ultron (Classic)": ["Bleed", "Poison"],
    "Unstoppable Colossus": ["Bleed"],
    "Vision": ["Bleed", "Poison"],
    "Vision (Age of Ultron)": ["Bleed", "Poison"],
    "Viv Vision": ["Bleed", "Poison"],
    "Void": ["Incinerate"],
    "Vulture": ["Poison", "Incinerate", "Shock"],
    "Warlock": ["Bleed", "Incinerate", "Coldsnap", "Frostbite"],
}


def get_immunities_for_champion(name: str) -> list[str]:
    return CHAMPION_IMMUNITIES.get(name, [])


def get_champions_by_immunity(immunity_type: str) -> list[str]:
    return sorted([
        name for name, immunities in CHAMPION_IMMUNITIES.items()
        if immunity_type in immunities
    ])


def get_immunity_map() -> dict[str, list[str]]:
    """Returns {immunity_type: [champion_names]}"""
    result = {}
    for imm_type in IMMUNITY_TYPES:
        result[imm_type] = get_champions_by_immunity(imm_type)
    return result
