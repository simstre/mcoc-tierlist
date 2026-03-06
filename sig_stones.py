"""
Sig Stone Tier List Data
Champions ranked by how much they benefit from high signature ability levels.
Based on community consensus from YouTube creators: KT1, Lagacy, Vega, MGuideBlog, Omega.

Tiers:
  Essential - Sig fundamentally changes the champion; must max sig
  High - Sig significantly improves performance; worth investing
  Medium - Sig provides a nice bonus but champion works fine at low sig
"""

# Champions mapped to their sig stone priority and a short reason
SIG_STONE_DATA = {
    # ===== ESSENTIAL =====
    "Nick Fury": {"priority": "Essential", "note": "Phase 2 damage scales massively with sig"},
    "Aegon": {"priority": "Essential", "note": "Combo shield chance depends entirely on sig"},
    "Hercules": {"priority": "Essential", "note": "Sig adds extra Indestructible charges"},
    "Void": {"priority": "Essential", "note": "Debuff potency and reverse healing scale with sig"},
    "Absorbing Man": {"priority": "Essential", "note": "Sig determines absorb material duration and potency"},
    "Juggernaut": {"priority": "Essential", "note": "Unstoppable duration and fury potency from sig"},
    "Spider-Man (Stark Enhanced)": {"priority": "Essential", "note": "Poise charges and auto-evade from sig"},
    "Kitty Pryde": {"priority": "Essential", "note": "Phasing duration and miss window scale with sig"},
    "Kingpin": {"priority": "Essential", "note": "Rage mechanics and purify chance from sig"},
    "Colossus": {"priority": "Essential", "note": "Armor up potency and immunities from sig"},
    "Archangel": {"priority": "Essential", "note": "Neurotoxin potency scales dramatically with sig"},
    "Cosmic Ghost Rider": {"priority": "Essential", "note": "Judgment damage scales with sig level"},
    "Doctor Doom": {"priority": "Essential", "note": "Aura of Haazareth damage from sig"},
    "Ghost": {"priority": "Essential", "note": "Crit rating during phase scales with sig"},
    "Tigra": {"priority": "Essential", "note": "Passive stun duration scales with sig"},
    "Kate Bishop": {"priority": "Essential", "note": "Critical damage and arrow potency from sig"},

    # ===== HIGH =====
    "Mister Sinister": {"priority": "High", "note": "Genetic memory bonuses improve with sig"},
    "Jean Grey": {"priority": "High", "note": "Phoenix Force charges and damage from sig"},
    "Nico Minoru": {"priority": "High", "note": "Staff of One potency scales with sig"},
    "Kushala": {"priority": "High", "note": "Spirit charges and damage from sig"},
    "Okoye": {"priority": "High", "note": "Kimoyo charge potency scales with sig"},
    "Count Nefaria": {"priority": "High", "note": "Ionic charge potency scales with sig"},
    "Photon": {"priority": "High", "note": "Energy charges and damage from sig"},
    "Silk": {"priority": "High", "note": "Evade and spider-sense potency from sig"},
    "The Serpent": {"priority": "High", "note": "Fear mechanic potency scales with sig"},
    "Cull Obsidian": {"priority": "High", "note": "Ramp-up speed and damage scale with sig"},
    "Red Guardian": {"priority": "High", "note": "Block proficiency and perfect block from sig"},
    "Nimrod": {"priority": "High", "note": "Adaptation charges and potency from sig"},
    "Dazzler": {"priority": "High", "note": "Sound charges and damage scale with sig"},
    "Crossbones": {"priority": "High", "note": "Fury and overrun potency from sig"},
    "Shathra": {"priority": "High", "note": "Web-snare potency scales with sig"},
    "Medusa": {"priority": "High", "note": "Armor shatter and fury from sig"},
    "Hyperion": {"priority": "High", "note": "Fury and cosmic charges from sig"},
    "Spider-Man (Pavitr)": {"priority": "High", "note": "Dimensional charges scale with sig"},
    "Sentinel": {"priority": "High", "note": "Analysis charges and adaptation from sig"},
    "Dark Phoenix": {"priority": "High", "note": "Phoenix Force mechanics from sig"},
    "Hulk (OG)": {"priority": "High", "note": "Fury potency scales massively with sig"},
    "Luke Cage": {"priority": "High", "note": "Exhaustion and indestructible from sig"},
    "Ant-Man (Future)": {"priority": "High", "note": "Pym particle potency from sig"},
    "America Chavez": {"priority": "High", "note": "Dimensional charges scale with sig"},
    "Anti-Venom": {"priority": "High", "note": "Cleanse and heal potency from sig"},
    "Valkyrie": {"priority": "High", "note": "Valor charges scale with sig"},
    "Omega Red": {"priority": "High", "note": "Death spore potency from sig"},
    "Scream": {"priority": "High", "note": "Symbiote charges scale with sig"},
    "Cassie Lang": {"priority": "High", "note": "Size change potency from sig"},
    "Purgatory": {"priority": "High", "note": "Soul charges scale with sig"},
    "Guardian": {"priority": "High", "note": "Force field and block proficiency from sig"},
    "Ironheart": {"priority": "High", "note": "Auto-block and repulsor charges from sig"},
    "Spider-Man (Stealth Suit)": {"priority": "High", "note": "Miss and slow potency from sig"},
    "Deadpool (X-Force)": {"priority": "High", "note": "Regen and bleed potency from sig"},

    # ===== MEDIUM =====
    "Chee'ilth": {"priority": "Medium", "note": "Curse potency improves with sig"},
    "The Hood": {"priority": "Medium", "note": "Hex and invisibility from sig"},
    "Domino": {"priority": "Medium", "note": "Lucky and critical failure chances from sig"},
    "Negasonic": {"priority": "Medium", "note": "Charge potency from sig"},
    "Vox": {"priority": "Medium", "note": "Sonic charges scale with sig"},
    "Knull": {"priority": "Medium", "note": "Symbiote dragon potency from sig"},
    "Professor X": {"priority": "Medium", "note": "Cerebro charges scale with sig"},
    "Spot": {"priority": "Medium", "note": "Portal potency from sig"},
    "Titania": {"priority": "Medium", "note": "Fury and block proficiency from sig"},
    "Shocker": {"priority": "Medium", "note": "Vibration charge potency from sig"},
    "Viv Vision": {"priority": "Medium", "note": "Phase and power control from sig"},
    "The Maker": {"priority": "Medium", "note": "Intelligence charges from sig"},
    "Spider-Punk": {"priority": "Medium", "note": "Noise charges scale with sig"},
    "Diablo": {"priority": "Medium", "note": "Elixir potency from sig"},
    "Mojo": {"priority": "Medium", "note": "Follower count scaling from sig"},
    "Captain Britain": {"priority": "Medium", "note": "Confidence charges from sig"},
    "Dani Moonstar": {"priority": "Medium", "note": "Spirit animal potency from sig"},
    "Blade": {"priority": "Medium", "note": "Danger sense and regen from sig"},
    "Wolverine (Weapon X)": {"priority": "Medium", "note": "Regen and fury potency from sig"},
    "Masacre": {"priority": "Medium", "note": "Incinerate potency from sig"},
    "Scarlet Witch (Classic)": {"priority": "Medium", "note": "Buff trigger chance from sig"},
    "Doctor Voodoo": {"priority": "Medium", "note": "Loa charges and power control from sig"},
    "Spider-Man 2099": {"priority": "Medium", "note": "Evade and bleed potency from sig"},
    "Abomination (Immortal)": {"priority": "Medium", "note": "Poison potency from sig"},
    "Peni Parker": {"priority": "Medium", "note": "SP3 armor and regen from sig"},
    "Ultron (Prime)": {"priority": "Medium", "note": "Regen and evade from sig"},
    "Thing": {"priority": "Medium", "note": "Rock shield charges from sig"},
    "Stryfe": {"priority": "Medium", "note": "Psychic charges from sig"},
    "Killmonger": {"priority": "Medium", "note": "True strike and reverberation from sig"},
}

SIG_PRIORITY_ORDER = ["Essential", "High", "Medium"]

SIG_PRIORITY_COLORS = {
    "Essential": "#f59e0b",
    "High": "#3b82f6",
    "Medium": "#22c55e",
}
