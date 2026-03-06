"""
Fetch champion guide transcripts from MetalSonicDude YouTube channel,
then summarize into concise rotation guides.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

from youtube_transcript_api import YouTubeTranscriptApi

CHANNEL_URL = "https://www.youtube.com/@MetalSonicDude/videos"
GUIDES_PATH = Path(__file__).parent / "champion_guides.json"

# Map video title champion names to our data champion names
NAME_MAP = {
    "The Lizard": "Lizard",
    "The Maker": "The Maker",
    "Spider-Woman": "Spider-Woman (Jessica Drew)",
    "Deathless Thanos": "Thanos (Deathless)",
    "Serpent": "The Serpent",
    "Spider Man 2099": "Spider-Man 2099",
    "Deadpool X-Force": "Deadpool (X-Force)",
    "Mr. Knight": "Mr. Knight",
    "Mr Knight": "Mr. Knight",
    "Wolverine X-23": "Wolverine (X-23)",
    "Arnim Zola": "Arnim Zola",
    "Jean Grey": "Jean Grey",
    "Deathless She-Hulk": "She-Hulk (Deathless)",
    "Spider-Man Pavitr Prabhakar": "Spider-Man (Pavitr)",
    "Pavitr Prabhakar": "Spider-Man (Pavitr)",
}


def get_guide_videos():
    """Get list of 'How To Use' videos from the channel."""
    result = subprocess.run(
        ["yt-dlp", "--flat-playlist", "--print", "%(id)s|%(title)s", CHANNEL_URL],
        capture_output=True, text=True, timeout=120
    )
    # Strip ANSI codes
    clean = result.stdout
    clean = re.sub(r'\x1b\[[0-9;]*[mK]', '', clean)

    videos = []
    for line in clean.strip().split('\n'):
        if '|' not in line:
            continue
        vid_id, title = line.split('|', 1)
        if re.search(r'how to.*use', title, re.IGNORECASE):
            videos.append((vid_id.strip(), title.strip()))
    return videos


def extract_champion_name(title):
    """Extract champion name from video title."""
    # Pattern: "How To Effectively Use [and Fight] CHAMPION_NAME | ..."
    m = re.search(r'How [Tt]o.*?Use(?:\s+and\s+Fight)?\s+(.+?)(?:\s*\||\s*$)', title)
    if m:
        name = m.group(1).strip()
        name = re.sub(r'\s*\|\s*Marvel Contest of Champions', '', name)
        return NAME_MAP.get(name, name)
    return None


def fetch_transcript(video_id):
    """Fetch transcript text for a video."""
    try:
        ytt = YouTubeTranscriptApi()
        transcript = ytt.fetch(video_id)
        entries = list(transcript)
        if len(entries) < 10:
            return None
        return ' '.join(e.text for e in entries)
    except Exception:
        return None


def summarize_transcript(text):
    """Extract key guide points from transcript. Simple extraction approach."""
    text = text.strip()
    sentences = re.split(r'(?<=[.!?])\s+', text)

    # Keywords that indicate useful guide content
    guide_keywords = [
        'rotation', 'special', 'heavy', 'combo', 'parry', 'dex', 'block',
        'intercept', 'bait', 'ramp', 'charge', 'stack', 'buff', 'debuff',
        'sp1', 'sp2', 'sp3', 'special one', 'special two', 'special three',
        'damage', 'power gain', 'regen', 'heal', 'bleed', 'poison',
        'incinerate', 'shock', 'stun', 'immunity', 'immune', 'evade',
        'miss', 'unstoppable', 'unblockable', 'fury', 'cruelty', 'crit',
        'armor', 'nullify', 'stagger', 'power control', 'power drain',
        'power lock', 'passive', 'prowess',
        'ideal', 'want to', 'you should', 'make sure', 'important',
        'key', 'tip', 'trick', 'strategy', 'prioritize',
    ]

    scored = []
    for s in sentences:
        s_lower = s.lower()
        # Skip intro/outro fluff
        if any(skip in s_lower for skip in [
            'subscribe', 'like button', 'comment', 'welcome back',
            'thank you', 'next video', 'peace', 'link in',
            'let me know', 'hope you', 'channel',
        ]):
            continue
        score = sum(1 for kw in guide_keywords if kw in s_lower)
        if score > 0:
            scored.append((score, s))

    # Take top sentences, preserving rough order
    scored.sort(key=lambda x: -x[0])
    top = scored[:12]

    # Rebuild in original order
    top_texts = {s for _, s in top}
    ordered = [s for s in sentences if s in top_texts]

    if not ordered:
        return None

    summary = ' '.join(ordered)
    # Truncate to ~500 chars
    if len(summary) > 500:
        summary = summary[:497] + '...'
    return summary


def main():
    # Load existing guides
    existing = {}
    if GUIDES_PATH.exists():
        existing = json.loads(GUIDES_PATH.read_text())

    videos = get_guide_videos()
    print(f"Found {len(videos)} guide videos")

    new_count = 0
    for vid_id, title in videos:
        champ_name = extract_champion_name(title)
        if not champ_name:
            print(f"  Skip (can't parse name): {title}")
            continue

        if champ_name in existing:
            print(f"  Skip (already have): {champ_name}")
            continue

        print(f"  Fetching: {champ_name} ({vid_id})...", end=" ")
        transcript = fetch_transcript(vid_id)
        if not transcript:
            print("no captions")
            continue

        summary = summarize_transcript(transcript)
        if not summary:
            print("no useful content")
            continue

        existing[champ_name] = {
            "guide": summary,
            "video_id": vid_id,
            "source": "MetalSonicDude",
        }
        new_count += 1
        print(f"OK ({len(summary)} chars)")

    GUIDES_PATH.write_text(json.dumps(existing, indent=2))
    print(f"\nDone. {new_count} new guides added. Total: {len(existing)}")


if __name__ == "__main__":
    main()
