"""
Fetch and parse tier list data from Google Sheets sources.
Sources: Vega, Lagacy, Omega (Lightvayne)
"""
import csv
import io
import json
import logging
import re
from collections import defaultdict
from pathlib import Path

import requests

logger = logging.getLogger("mcoc-fetcher")

SOURCES_CONFIG = [
    {
        "name": "Vega",
        "type": "YouTube",
        "sheet_id": "1S1qrtmsVjfd-jkkHwjJcEj_tWvDrII49pv8-huomzgM",
        "gid": "0",
        "parser": "vega",
    },
    {
        "name": "Lagacy",
        "type": "YouTube",
        "sheet_id": "1Vm6CrMpL7dExQlRZguNuC38x3VV6YVpo4qgZ-wu2iAQ",
        "gid": "1318739461",
        "parser": "lagacy",
    },
    {
        "name": "Omega",
        "type": "YouTube",
        "sheet_id": "1c-Y25KPFDRDFrmfvQMcxGNuqQ5eQgxxLQk-Yb4YkSIA",
        "gid": "0",
        "parser": "omega",
    },
]

CACHE_PATH = Path(__file__).parent / "cached_tierlist.json"


def _strip_emojis(text):
    # Keep only ASCII letters/digits/punctuation + Æ (for Ægon)
    clean = ''.join(c for c in text if (32 <= ord(c) <= 126) or c == '\u00c6')
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean


def _extract_traits(text):
    """Extract traits from emoji annotations in champion name text.

    Uses both unicode codepoints and common UTF-8 byte patterns.
    """
    traits = set()
    # Map: (emoji_char, trait_name)
    checks = [
        ('\U0001F31F', 'awakened'),       # 🌟
        ('\U0001F9BE', 'awakened'),       # 🦾
        ('\U0001F680', 'high_sig'),       # 🚀
        ('\U0001F4C8', 'high_sig'),       # 📈
        ('\U0001F48E', 'ascendable'),     # 💎
        ('\U0001F6E1', 'defense'),        # 🛡
        ('\U0001F480', 'recoil'),         # 💀
        ('\U0001F47E', 'high_skill'),     # 👾
        ('\U0001F431', 'high_skill'),     # 🐱 (part of ninja cat)
        ('\U0001F942', 'synergy'),        # 🥂
        ('\U0001F3B2', 'early_ranking'),  # 🎲
        ('\U0001F339', 'projected_7star'),# 🌹
        ('\U0001F512', 'rarity_locked'),  # 🔒
        ('\U0001F5FF', 'relic'),          # 🗿
        ('\U0001F4BE', 'relic'),          # 💾
        ('\U0001F3D4', 'ramp_up'),        # 🏔
    ]
    for char, trait in checks:
        if char in text:
            traits.add(trait)
    # Also check for common text patterns (some sheets use text markers)
    non_ascii = ''.join(c for c in text if ord(c) > 126)
    if non_ascii:
        # Check UTF-8 byte patterns for emojis that might not match as codepoints
        raw = text.encode('utf-8', errors='ignore')
        emoji_bytes = {
            b'\xf0\x9f\x8c\x9f': 'awakened',       # 🌟
            b'\xf0\x9f\xa6\xbe': 'awakened',       # 🦾
            b'\xf0\x9f\x9a\x80': 'high_sig',       # 🚀
            b'\xf0\x9f\x93\x88': 'high_sig',       # 📈
            b'\xf0\x9f\x92\x8e': 'ascendable',     # 💎
            b'\xf0\x9f\x9b\xa1': 'defense',        # 🛡
            b'\xf0\x9f\x92\x80': 'recoil',         # 💀
            b'\xf0\x9f\x91\xbe': 'high_skill',     # 👾
            b'\xf0\x9f\x90\xb1': 'high_skill',     # 🐱
            b'\xf0\x9f\xa5\x82': 'synergy',        # 🥂
            b'\xf0\x9f\x8e\xb2': 'early_ranking',  # 🎲
            b'\xf0\x9f\x8c\xb9': 'projected_7star',# 🌹
            b'\xf0\x9f\x94\x92': 'rarity_locked',  # 🔒
            b'\xf0\x9f\x97\xbf': 'relic',          # 🗿
            b'\xf0\x9f\x92\xbe': 'relic',          # 💾
            b'\xf0\x9f\x8f\x94': 'ramp_up',        # 🏔
        }
        for pattern, trait in emoji_bytes.items():
            if pattern in raw:
                traits.add(trait)
    return traits


# fmt: off
_NAME_MAP = {
    # Vega
    'Spider-Man Pavitr': 'Spider-Man (Pavitr)', 'Negasonic Teenage Warhead': 'Negasonic',
    'Spider-Man (Stark)': 'Spider-Man (Stark Enhanced)',
    'Cap America (Infinity War)': 'Captain America (Infinity War)',
    'Cap America (Sam Wilson)': 'Captain America (Sam Wilson)',
    'Spider-Man (Stealth)': 'Spider-Man (Stealth Suit)',
    'Spider-Man Miles Morales': 'Spider-Man (Miles Morales)',
    'Black Widow (Claire)': 'Black Widow (Claire Voyant)',
    'Cap Marvel': 'Captain Marvel (Classic)', 'Ms. Marvel Kamala': 'Ms. Marvel (Kamala)',
    'Deadpool (Red Suit)': 'Deadpool', 'Scarlet Witch': 'Scarlet Witch (Sigil)',
    'Aegon - Long Form King': 'Aegon', 'Magik - 5 Star Locked': 'Magik',
    'Quake - 5 Star Locked': 'Quake', 'Abomination OG': 'Abomination',
    'Cap America OG': 'Captain America (Classic)', 'Gladiator Hulk': 'Hulk (Ragnarok)',
    'Guillotine Deathless': 'Guillotine (Deathless)', 'Daredevil OG': 'Daredevil (Classic)',
    "Daredevil Hell's Kitchen": "Daredevil (Hell's Kitchen)",
    'Black Widow OG': 'Black Widow (OG)',
    'Black Widow Deadly Origin': 'Black Widow (Deadly Origin)',
    'Black Widow DO': 'Black Widow (Deadly Origin)',
    'Thor Ragnarok': 'Thor (Ragnarok)', 'Thor Jane Foster': 'Thor (Jane Foster)',
    'Vision Aarkus': 'Vision (Aarkus)', 'Wolverine X-23': 'Wolverine (X-23)',
    'Thanos (OG)': 'Thanos', 'Spider Slayer J Jameson': 'Spider-Slayer',
    'Doc Octopus': 'Doctor Octopus', 'Iron Fist Immortal': 'Iron Fist (Immortal)',
    'Black Panther': 'Black Panther (Classic)', 'Wolverine': 'Wolverine (OG)',
    'Hulk': 'Hulk (OG)', 'Iron Man': 'Iron Man (OG)', 'Storm': 'Storm (OG)',
    'Magneto': 'Magneto (Red)', 'Ms. Marvel': 'Ms. Marvel (OG)',
    'Archangel': 'Archangel', 'Werewolf': 'Werewolf By Night',
    'Falcon': 'Falcon', 'Ultron': 'Ultron (Prime)', 'Ultron Classic': 'Ultron (Classic)',
    'Vision': 'Vision (Classic)', 'Frankencastle': 'Franken-Castle',
    'Stealth Spiderman': 'Spider-Man (Stealth Suit)',
    'Star-Lord (Stellar Forge)': 'Star-Lord (Stellar Forge)',
    'Masacre': 'Masacre',
    # Lagacy
    'DThanos': 'Thanos (Deathless)', 'Pavitr Spidey': 'Spider-Man (Pavitr)',
    'AbsorbingMan': 'Absorbing Man', 'WerewolfBN': 'Werewolf By Night',
    'BW Claire Voyant': 'Black Widow (Claire Voyant)', 'Wongerz': 'Wong',
    'Sigil Witch': 'Scarlet Witch (Sigil)', 'OG Scarlet Witch': 'Scarlet Witch (Classic)',
    'Spidey Supreme': 'Spider-Man (Supreme)', 'Deathless Guillotine': 'Guillotine (Deathless)',
    'KittyPryde': 'Kitty Pryde', 'White Mangeto': 'Magneto (House of X)',
    'WolverineX-23': 'Wolverine (X-23)', 'Capt Britian': 'Captain Britain',
    'Negasonic Warhead': 'Negasonic', 'Night-Crawler': 'Nightcrawler',
    'Storm OG': 'Storm (OG)', 'Storm X': 'Storm (Pyramid X)',
    'Sabertooth': 'Sabretooth', 'Colosuss': 'Colossus', 'Oldman Logan': 'Old Man Logan',
    'Deadpools': 'Deadpool', 'Deadpool X-Force': 'Deadpool (X-Force)',
    'Wolverine Weapon X': 'Wolverine (Weapon X)', 'Future Antman': 'Ant-Man (Future)',
    'Stark Spidey': 'Spider-Man (Stark Enhanced)', 'OG Ironman': 'Iron Man (OG)',
    'Ironman Buffed': 'Iron Man (OG)', 'Iron Doom (Infamous)': 'Iron Man (Infamous)',
    'ironHeart': 'Ironheart', 'Sam Wilson Cap': 'Captain America (Sam Wilson)',
    'Punisher 2099 (CTM)': 'Punisher 2099', 'J Jonah Jameson': 'Spider-Slayer',
    'Visions': 'Vision (Classic)', 'Ironman Infinity War': 'Iron Man (Infinity War)',
    'Venom Z Duck': 'Venom the Duck', 'Deathless KGroot': 'King Groot (Deathless)',
    'Cap Marvel Movie': 'Captain Marvel (Movie)', 'Gorr The God Butcher': 'Gorr',
    'Odin sama': 'Odin', 'Beta Ray Billy': 'Beta Ray Bill',
    'Symbiote Spider-man': 'Spider-Man (Symbiote)', 'Super Skrull': 'Super-Skrull',
    'Spider-Woman': 'Spider-Woman (Jessica Drew)',
    'iAbombination': 'Abomination (Immortal)', 'Abombination': 'Abomination',
    'Deathless She Hulk': 'She-Hulk (Deathless)', 'She Hulk': 'She-Hulk',
    'Overseer': 'The Overseer', 'Mr Negative': 'Mister Negative', 'Modok': 'M.O.D.O.K.',
    'Cap Infinity War': 'Captain America (Infinity War)',
    'Spider-Man OG': 'Spider-Man (Classic)', 'Joaquin Falcon': 'Falcon (Joaquin Torres)',
    'Antman': 'Ant-Man', 'Miles Morales': 'Spider-Man (Miles Morales)',
    'iHulk': 'Hulk (Immortal)', 'Yellow Jacket': 'Yellowjacket',
    "Captain America's": 'Captain America (Classic)', 'Moleman': 'Mole Man',
    'Massacre': 'Masacre', 'Franken Castle': 'Franken-Castle',
    'Black Panther CW': 'Black Panther (Civil War)',
    'Black Panther OG': 'Black Panther (Classic)',
    'Stellar Forge Star Lord': 'Star-Lord (Stellar Forge)',
    'Cyclops (red)': 'Cyclops (New Xavier School)', 'Cyclops': 'Cyclops (Blue Team)',
    'Airwalker': 'Air-Walker', 'Blackbolt': 'Black Bolt',
    'Jane Foster': 'Thor (Jane Foster)', 'Manthing': 'Man-Thing',
    'Guillotine OG': 'Guillotine', 'Iron Fists': 'Iron Fist',
    'Unstoppable Colosuss': 'Unstoppable Colossus', 'Warmachine': 'War Machine',
    'Psycho man': 'Psycho-Man', 'Howard The Duck': 'Howard the Duck',
    'Winter Solider': 'Winter Soldier', 'Daredevils': 'Daredevil (Classic)',
    'Hood': 'The Hood', 'Superior Ironman': 'Superior Iron Man',
    'Wolverine OG': 'Wolverine (OG)', 'Kamala Khan': 'Ms. Marvel (Kamala)',
    'Captain&Ms Marvel': 'Captain Marvel (Classic)',
    'Dragon man': 'Dragon Man', 'Star Lord': 'Star-Lord',
    # Omega
    'Spider-Man (Pavitr Prabhakar)': 'Spider-Man (Pavitr)',
    '\u00c6gon': 'Aegon', 'Werewolf by Night': 'Werewolf By Night',
    'Kraven the Hunter': 'Kraven', 'Venom The Duck': 'Venom the Duck',
    'Ultron (AOU)': 'Ultron (Prime)',
    'Ms. Marvel (Kamala Khan)': 'Ms. Marvel (Kamala)',
    'Spider-Slayer (J. Jonah Jameson)': 'Spider-Slayer',
    'Vision (Age Of Ultron)': 'Vision (Age of Ultron)',
    'Magneto (House Of X)': 'Magneto (House of X)',
    'Captain America': 'Captain America (Classic)',
    'Captain America (WWII)': 'Captain America (WWII)',
    'Scarlet Witch (Classic)': 'Scarlet Witch (Classic)',
    'Black Widow': 'Black Widow (OG)',
    "Daredevil (Hell's Kitchen)": "Daredevil (Hell's Kitchen)",
    'Chee\u2019ilth': "Chee'ilth",
    '312': None,
}
# fmt: on

# Fallback class for champions only in Omega (which has no class info)
_FALLBACK_CLASS = {
    'Captain America (WWII)': 'Science',
    "Chee'ilth": 'Skill',
    'Goldpool': 'Mutant',
    'Platinumpool': 'Mutant',
    'Summoned Symbiote': 'Cosmic',
}


def _normalize(name):
    result = _NAME_MAP.get(name, name)
    return result


def _fetch_csv(sheet_id, gid):
    """Fetch a Google Sheet as CSV. Try two URL patterns."""
    urls = [
        f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}",
        f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&gid={gid}",
    ]
    for url in urls:
        try:
            resp = requests.get(url, timeout=30, allow_redirects=True)
            if resp.status_code == 200 and not resp.text.strip().startswith('<!DOCTYPE'):
                # Fix double-encoding: Google Sheets sometimes serves UTF-8 bytes
                # that get misinterpreted as Latin-1
                text = resp.text
                try:
                    text = resp.content.decode('utf-8')
                except UnicodeDecodeError:
                    pass
                return list(csv.reader(io.StringIO(text)))
        except Exception as e:
            logger.warning(f"Failed to fetch {url}: {e}")
    return None


def _extract_edition(rows, source_name):
    """Try to find an edition/date string from the first rows of a sheet."""
    import re as _re
    if source_name == 'Vega':
        # Look for "Nth Edition - Month, Year" pattern
        for row in rows[:15]:
            for cell in row:
                m = _re.search(r'(\d+\w*\s+Edition\s*-?\s*\w+,?\s*\d{4})', cell)
                if m:
                    return m.group(1)
    elif source_name == 'Lagacy':
        # First cell typically has "Month Year ... Lagacy's ..."
        for row in rows[:3]:
            for cell in row:
                m = _re.search(r'((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})', cell)
                if m:
                    return m.group(1)
    elif source_name == 'Omega':
        # Omega doesn't have dates; check anyway
        for row in rows[:10]:
            for cell in row:
                m = _re.search(r'((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})', cell)
                if m:
                    return m.group(1)
    return None


def _parse_vega(rows):
    champions = {}
    current_class = None
    tier_col_map = {1: 100, 2: 80, 3: 60, 4: 40, 5: 20, 6: 0}
    classes = ['Mystic', 'Science', 'Skill', 'Mutant', 'Tech', 'Cosmic']
    skip = [
        'Edition', 'Tier', 'OP', 'Phenomenal', 'Great', 'Very Good', 'Goodish',
        'Need a Buff', 'MCoC', 'Vega', 'Cantona', 'Grass', 'Liam', 'Nagase',
        'TJarvis', 'William', 'Creator', 'Legend', 'Socials', 'YouTube',
        'Twitter', 'BlueSky', 'Instagram', 'Discord', 'Videos', 'Guides',
        'Tier List', 'Player', 'Fighter', 'Encyclop', 'NOOB', 'NAGASE',
        'mcoce', 'mcocnoob', 'nagase', 'Ranking a projection', 'Big Caution',
        'Benefits Greatly', 'Ascendable', 'Ramp Up', 'Correct relic',
        'Defense Part', 'Recoil', 'Synergy needed', 'Requires high',
        'Early Ranking', 'Talked about', 'Use As a Guide', 'Non 7 Star',
        'Even Hot', 'All Modes', 'Information', 'More Helpful', "Vega's",
        'New & Progressing', 'How to Fight', "William's War",
    ]
    for row in rows:
        if len(row) < 7:
            continue
        first = row[0].strip()
        if first in classes:
            current_class = first
        if current_class is None:
            continue
        for col, score in tier_col_map.items():
            if col >= len(row):
                continue
            cell = row[col].strip()
            if not cell or cell in classes:
                continue
            if any(s in cell for s in skip):
                continue
            name = _strip_emojis(cell)
            if not name or len(name) < 2:
                continue
            champions[name] = {'class': current_class, 'score': score, 'traits': _extract_traits(cell)}
    return champions


def _parse_lagacy(rows):
    champions = {}
    current_class = None
    tier_col_map = {0: 100, 1: 80, 2: 60, 3: 40, 4: 20, 5: 0}
    class_markers = {
        'Science Class': 'Science', 'Cosmic Class': 'Cosmic', 'Mystic Class': 'Mystic',
        'Mutant Class': 'Mutant', 'Tech Class': 'Tech', 'Skill Class': 'Skill',
    }
    skip = [
        'One Above All Tier', 'Beyonder Tier', 'God Tier', 'Amazing Tier',
        'Solid Tier', 'MID Tier', 'Temporary', 'Emoji', 'Reworked',
        'WANTS Awakened', 'High Defensive', 'Want High Sig', 'Skillz To Play',
        'Powerful Relic', 'Ouchies Friendly', 'Rarity Locked', 'Recoil Friendly',
        'Powerful Synergy', 'January', 'Lagacy', 'Promoted', 'Demoted',
        'New entry', '5* or 6*',
    ]
    for row in rows:
        if len(row) < 6:
            continue
        first = row[0].strip()
        for marker, cls in class_markers.items():
            if first.startswith(marker):
                current_class = cls
                break
        if current_class is None:
            continue
        for col, score in tier_col_map.items():
            if col >= len(row):
                continue
            cell = row[col].strip()
            if not cell:
                continue
            if any(cell.startswith(m) for m in class_markers):
                continue
            if any(s in cell for s in skip):
                continue
            name = _strip_emojis(cell)
            if not name or len(name) < 2:
                continue
            champions[name] = {'class': current_class, 'score': score, 'traits': _extract_traits(cell)}
    return champions


def _parse_omega(rows):
    champions = {}
    tier_col_map = {1: 100, 4: 80, 7: 60, 10: 40, 13: 20, 16: 0}
    skip = [
        'Champions:', 'ATK', 'Lightvayne', 'Omega Discord', 'Total Champs',
        'KEY', 'Hover for', 'Notes', 'Working on', 'Still Need',
        'MVP Level', 'Omega Level', 'Alpha Level', 'Beta Level',
        'Gamma Level', 'Epsilon Level', 'Click the', 'Attack Tactic',
        'Description', 'Meteor', 'When a Buff',
    ]
    for row in rows:
        if len(row) < 17:
            continue
        for col, score in tier_col_map.items():
            cell = row[col].strip()
            if not cell or cell.startswith('[') or cell.startswith('\u2191'):
                continue
            if any(s in cell for s in skip):
                continue
            name = _strip_emojis(cell)
            if not name or len(name) < 2:
                continue
            traits = set()
            if col + 1 < len(row) and '\u2604' in row[col + 1]:
                traits.add('meteor_tactic')
            champions[name] = {'class': None, 'score': score, 'traits': traits}
    return champions


_PARSERS = {
    'vega': _parse_vega,
    'lagacy': _parse_lagacy,
    'omega': _parse_omega,
}


def fetch_and_combine():
    """Fetch all 3 sheets, parse, normalize, and combine into champion list.

    Returns (champions_dict, success_count, source_meta) or (None, 0, []) on total failure.
    source_meta is a list of dicts: {name, edition, champion_count}
    """
    source_data = {}
    source_meta = []

    for src in SOURCES_CONFIG:
        rows = _fetch_csv(src['sheet_id'], src['gid'])
        if rows is None:
            logger.warning(f"Could not fetch {src['name']} sheet")
            source_meta.append({'name': src['name'], 'edition': None, 'champion_count': 0, 'status': 'failed'})
            continue
        parser = _PARSERS[src['parser']]
        raw = parser(rows)
        edition = _extract_edition(rows, src['name'])
        # Normalize names
        normed = {}
        for name, data in raw.items():
            n = _normalize(name)
            if n is None:
                continue
            normed[n] = data
        source_data[src['name']] = normed
        source_meta.append({'name': src['name'], 'edition': edition, 'champion_count': len(normed), 'status': 'ok'})
        logger.info(f"Parsed {src['name']}: {len(normed)} champions, edition: {edition}")

    if not source_data:
        return None, 0, source_meta

    # Combine
    all_names = set()
    for d in source_data.values():
        all_names |= set(d.keys())

    combined = {}
    for name in sorted(all_names):
        all_scores = []
        traits = set()
        cls = None

        for src_name, src_champs in source_data.items():
            if name in src_champs:
                c = src_champs[name]
                all_scores.append(c['score'])
                traits |= c['traits']
                if c.get('class') and cls is None:
                    cls = c['class']

        if cls is None:
            cls = _FALLBACK_CLASS.get(name)
        if cls is None:
            continue  # skip champions with no class

        # Exclude 0 scores from averaging unless ALL sources give 0.
        # A 0 typically means "not rated" (e.g. rarity-locked), not "rated as worst".
        nonzero = [s for s in all_scores if s > 0]
        if nonzero:
            avg = round(sum(nonzero) / len(nonzero))
        else:
            avg = 0
        combined[name] = {
            'class': cls,
            'score': avg,
            'awakened': 'awakened' in traits,
            'high_sig': 'high_sig' in traits,
            'no7star': 'rarity_locked' in traits or 'projected_7star' in traits,
            'tags': sorted(t for t in traits if t not in
                          ('awakened', 'high_sig', 'rarity_locked', 'projected_7star')),
        }

    return combined, len(source_data), source_meta


CACHE_META_PATH = Path(__file__).parent / "cached_source_meta.json"


def fetch_and_cache():
    """Fetch fresh data, cache to disk, return (champion_dict, source_meta) or (None, [])."""
    combined, count, source_meta = fetch_and_combine()
    if combined and count > 0:
        CACHE_PATH.write_text(json.dumps(combined, indent=2, default=list))
        CACHE_META_PATH.write_text(json.dumps(source_meta, indent=2))
        logger.info(f"Cached {len(combined)} champions from {count} sources")
        return combined, source_meta
    return None, source_meta


def load_cached():
    """Load previously cached tier list data and source meta."""
    data = None
    meta = []
    if CACHE_PATH.exists():
        try:
            data = json.loads(CACHE_PATH.read_text())
            logger.info(f"Loaded {len(data)} champions from cache")
        except Exception as e:
            logger.error(f"Failed to load cache: {e}")
    if CACHE_META_PATH.exists():
        try:
            meta = json.loads(CACHE_META_PATH.read_text())
        except Exception:
            pass
    return data, meta
