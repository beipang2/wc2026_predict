"""Convert team data into attack/defense parameters for match simulation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).parent.parent / "data"


def load_teams(overrides: dict[str, Any] | None = None) -> dict[str, dict]:
    teams = json.loads((DATA_DIR / "teams.json").read_text())
    if overrides:
        for code, values in overrides.items():
            if code in teams:
                teams[code].update(values)
    return teams


def get_attack(team: dict) -> float:
    base = float(team.get("attack") or _elo_to_attack(team["elo"]))
    return base * _form_factor(team)


def get_defense(team: dict) -> float:
    base = float(team.get("defense") or 1.0)
    # good form tightens defense (lower multiplier), bad form loosens it
    return base / _form_factor(team)


def _form_factor(team: dict) -> float:
    """form in teams.json: 0.8 (poor) to 1.2 (excellent), default 1.0."""
    return float(team.get("form", 1.0))


def _elo_to_attack(elo: float) -> float:
    """Fallback: map ELO to a rough goals/game estimate."""
    return max(0.5, (elo - 1400) / 400 + 1.0)
