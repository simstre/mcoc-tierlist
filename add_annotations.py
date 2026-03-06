"""Add no7star field to champions_data.py based on source spreadsheet annotations."""
import re

# Champions marked with lock icon (not available as 7-star) from the source
NO_7STAR = {
    # Cosmic
    "Cosmic Ghost Rider", "Hercules", "King Groot", "Ronan", "Hela",
    "Proxima Midnight", "Ikaris", "Thor", "Black Bolt", "Annihilus",
    "The Champion", "Spider-Man (Symbiote)", "Captain Marvel (Classic)",
    "Ms. Marvel (OG)", "Air-Walker", "Ms. Marvel (Kamala)", "Drax", "Groot", "Thanos",
    # Mutant
    "Archangel", "Magneto (Red)", "Toad", "Magneto (House of X)",
    "Wolverine (OG)", "Cable", "Jubilee", "Old Man Logan", "Rogue",
    "Psylocke", "Beast", "Cyclops (New Xavier School)", "Deadpool", "Goldpool",
    # Mystic
    "Doctor Doom", "Black Widow (Claire Voyant)", "Magik", "Guillotine",
    "Mephisto", "Doctor Strange", "Morningstar", "Ghost Rider", "Loki",
    "Dormammu", "Iron Fist (Immortal)", "Iron Fist", "Unstoppable Colossus",
    # Science
    "Quake", "Hulk (Ragnarok)", "Wasp", "Yellowjacket", "Electro",
    "Abomination", "Captain America (Classic)", "Captain America (WWII)",
    # Skill
    "Kate Bishop", "Karnak", "Thor (Ragnarok)", "Agent Venom",
    "Squirrel Girl", "Black Widow (OG)", "Taskmaster", "Winter Soldier",
    "Daredevil (Classic)", "Elektra", "Moon Knight",
    # Tech
    "Ghost", "Nebula", "Darkhawk", "Doctor Octopus", "Star-Lord",
    "Vision (Age of Ultron)", "Silver Centurion", "Vulture",
    "Green Goblin", "Psycho-Man", "Iron Patriot", "Kang",
}

# Read the file
with open("champions_data.py", "r") as f:
    content = f.read()

# Replace each entry to add no7star field
for name in NO_7STAR:
    escaped = re.escape(f'"{name}"')
    pattern = f'{escaped}: {{"class": "([^"]+)", "score": (\\d+), "awakened": (True|False)}}'
    match = re.search(pattern, content)
    if match:
        old = match.group(0)
        new = old.rstrip("}") + ', "no7star": True}'
        content = content.replace(old, new)
    else:
        print(f"Not found: {name}")

# For all entries without no7star, they're implicitly False (we don't need to add it)
with open("champions_data.py", "w") as f:
    f.write(content)

print(f"Updated {len(NO_7STAR)} champions with no7star annotation")
