"""
MCOC Champion Tier List Data
Aggregated from YouTube creators: Vega, Lagacy, Omega
"""

SOURCES = [
    {"name": "Vega", "type": "YouTube"},
    {"name": "Lagacy", "type": "YouTube"},
    {"name": "Omega", "type": "YouTube"},
]

CLASS_COLORS = {
    "Cosmic": "#7dd3fc",
    "Tech": "#6366f1",
    "Mutant": "#eab308",
    "Skill": "#ef4444",
    "Science": "#22c55e",
    "Mystic": "#a855f7",
}

TIER_COLORS = {
    "God": "#f59e0b",
    "Great": "#3b82f6",
    "Good": "#22c55e",
    "OK": "#9ca3af",
    "Low": "#6b7280",
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
    if score >= 90:
        return "God"
    if score >= 70:
        return "Great"
    if score >= 50:
        return "Good"
    if score >= 30:
        return "OK"
    return "Low"


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
