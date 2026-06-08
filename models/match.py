"""Poisson match simulator with Dixon-Coles low-score correction."""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from models.ratings import get_attack, get_defense

HOME_ADVANTAGE = 1.15
ALTITUDE_THRESHOLDS = [(2000, 0.88), (1500, 0.94)]
RHO = -0.1  # Dixon-Coles correction strength


def _altitude_factor(altitude_m: float) -> float:
    for threshold, factor in ALTITUDE_THRESHOLDS:
        if altitude_m > threshold:
            return factor
    return 1.0


def _dc_correction(home_g: int, away_g: int, lh: float, la: float, rho: float) -> float:
    """Dixon-Coles tau correction for low-scoring outcomes."""
    if home_g == 0 and away_g == 0:
        return 1 - lh * la * rho
    if home_g == 1 and away_g == 0:
        return 1 + la * rho
    if home_g == 0 and away_g == 1:
        return 1 + lh * rho
    if home_g == 1 and away_g == 1:
        return 1 - rho
    return 1.0


def expected_goals(
    home_team: dict,
    away_team: dict,
    fixture: dict[str, Any],
) -> tuple[float, float]:
    alt = fixture.get("altitude_m", 0) or 0
    alt_factor = _altitude_factor(alt)
    ha_team = fixture.get("home_advantage")

    ha = HOME_ADVANTAGE if ha_team == fixture["home"] else 1.0

    lh = get_attack(home_team) * get_defense(away_team) * ha
    # away team suffers altitude penalty
    la = get_attack(away_team) * get_defense(home_team) * alt_factor
    return lh, la


def simulate_match(
    home_team: dict,
    away_team: dict,
    fixture: dict[str, Any],
    rng: np.random.Generator | None = None,
) -> tuple[int, int]:
    """Return (home_goals, away_goals) for one match simulation."""
    lh, la = expected_goals(home_team, away_team, fixture)

    if rng is None:
        rng = np.random.default_rng()

    # Dixon-Coles: sample via rejection on low-score grid
    max_goals = 10
    while True:
        hg = int(rng.poisson(lh))
        ag = int(rng.poisson(la))
        hg = min(hg, max_goals)
        ag = min(ag, max_goals)

        tau = _dc_correction(hg, ag, lh, la, RHO)
        # tau can be slightly > 1 for some cells; cap accept probability at 1
        accept_prob = min(1.0, max(0.0, tau))
        # For DC correction: only apply adjustment for low scores
        if hg > 1 or ag > 1:
            break
        if rng.random() < accept_prob:
            break

    return hg, ag
