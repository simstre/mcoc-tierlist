"""
MCOC Champion Tier List Data
Aggregated from YouTube creators: Vega, Lagacy
"""

SOURCES = [
    {"name": "Vega", "type": "YouTube"},
    {"name": "Lagacy", "type": "YouTube"},
]

CLASS_COLORS = {
    "Cosmic": "#7dd3fc",
    "Tech": "#6366f1",
    "Mutant": "#eab308",
    "Skill": "#ef4444",
    "Science": "#22c55e",
    "Mystic": "#a855f7",
}

# Unified letter-grade tiers used on every tab (best -> worst).
TIER_ORDER = ["S+", "S", "A", "B", "C", "D", "F"]

TIER_COLORS = {
    "S+": "#f59e0b",  # amber
    "S":  "#fbbf24",  # gold
    "A":  "#a3e635",  # lime
    "B":  "#34d399",  # emerald
    "C":  "#22d3ee",  # cyan
    "D":  "#60a5fa",  # blue
    "F":  "#94a3b8",  # slate
}

# Vega's awakening / sig-stone priority sheets use their own heat-scale names.
# Map them onto the same letters (these tabs rank investment priority, so the
# levels stay contiguous rather than following the main power thresholds).
PRIORITY_TIER_MAP = {
    "Tier Above All": "S+",
    "Scorching": "S",
    "Super Hot": "A",
    "Hot": "B",
    "Mild": "C",
    "Bland": "D",
    "Not Endgame Relevant": "F",
}

TAG_LABELS = {
    "defense": "BGs Defense",
    "recoil": "Recoil Friendly",
    "high_skill": "High Skill",
    "relic": "Relic Important",
    "ramp_up": "Ramp Up",
    "synergy": "Synergy Needed",
    "ascendable": "Ascendable",
    "early_ranking": "Early Ranking",
    "meteor_tactic": "Meteor Tactic",
}


def score_to_tier(score: int) -> str:
    if score >= 96:
        return "S+"
    if score >= 84:
        return "S"
    if score >= 70:
        return "A"
    if score >= 60:
        return "B"
    if score >= 46:
        return "C"
    if score >= 30:
        return "D"
    return "F"


def retier_priority(priority_dict):
    """Relabel a priority-sheet dict's tiers to the unified letter scheme.

    Entries come in as {tier: <sheet name>, score, ...}; rewrite `tier` to a
    letter grade so the Awakening/Sig Stones tabs match the main tier list.
    """
    if not priority_dict:
        return priority_dict
    for entry in priority_dict.values():
        letter = PRIORITY_TIER_MAP.get(entry.get("tier"))
        entry["tier"] = letter or score_to_tier(entry.get("score", 0))
    return priority_dict


def compute_tier_list(raw_champions: dict):
    """Convert raw champion dict into sorted tier list."""
    champions = []
    for name, data in raw_champions.items():
        tier = score_to_tier(data["score"])
        champions.append({
            "name": name,
            "class": data["class"],
            "tier": tier,
            "score": data["score"],
            "awakened": data.get("awakened", False),
            "high_sig": data.get("high_sig", False),
            "no7star": data.get("no7star", False),
            "tags": data.get("tags", []),
        })

    champions.sort(key=lambda c: (-c["score"], c["name"]))
    for i, champ in enumerate(champions):
        champ["rank"] = i + 1

    return champions


def get_champions_by_class(champions):
    by_class = {}
    for champ in champions:
        cls = champ["class"]
        if cls not in by_class:
            by_class[cls] = []
        by_class[cls].append(champ)

    for cls in by_class:
        by_class[cls].sort(key=lambda c: (-c["score"], c["name"]))
        for i, champ in enumerate(by_class[cls]):
            champ["class_rank"] = i + 1

    return by_class
