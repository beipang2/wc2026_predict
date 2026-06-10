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
    """ELO-derived base + structural style offset, scaled by attacking form."""
    base = _elo_attack_base(team["elo"]) + float(team.get("style", 0))
    return max(0.40, base) * _form_attack(team)


def get_defense(team: dict) -> float:
    """ELO-derived base scaled by defensive form. Lower = harder to score against."""
    base = _elo_defense_base(team["elo"])
    return max(0.55, base) / _form_defense(team)


def _elo_attack_base(elo: float) -> float:
    """
    ELO → attack baseline. Calibrated so that:
      ELO 1985 (France)   → 1.85
      ELO 1935 (Brazil)   → 1.75
      ELO 1658 (Scotland) → 1.20
      ELO 1455 (Curacao)  → 0.79
    """
    return max(0.50, 0.002 * elo - 2.12)


def _elo_defense_base(elo: float) -> float:
    """
    ELO → defensive solidity baseline. Low = hard to score against.
      ELO 1985 (France)   → 0.78
      ELO 1935 (Brazil)   → 0.83
      ELO 1658 (Scotland) → 1.09
      ELO 1455 (Curacao)  → 1.28
    """
    return max(0.65, 2.652 - 0.000943 * elo)


def _form_attack(team: dict) -> float:
    """form_attack if set, else falls back to form. 1.0 = baseline."""
    return float(team.get("form_attack") or team.get("form", 1.0))


def _form_defense(team: dict) -> float:
    """form_defense if set, else falls back to form. 1.0 = baseline."""
    return float(team.get("form_defense") or team.get("form", 1.0))
