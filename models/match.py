"""Poisson match simulator with Dixon-Coles low-score correction."""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from models.ratings import get_attack, get_defense

HOME_ADVANTAGE = 1.04
ALTITUDE_THRESHOLDS = [(2000, 0.88), (1500, 0.94)]
RHO = -0.1  # Dixon-Coles correction strength

# Per-match rating jitter: Normal(1.0, σ) multiplied into each team's attack+defense.
# Captures heat exhaustion, individual errors, tactical surprises, referee variance.
JITTER_SIGMA_BASE = 0.10

# Hot outdoor venues get extra jitter — fatigue and mistakes amplified.
# Indoor/domed stadiums (NRG Houston, MB Atlanta, BC Place Vancouver) are climate-controlled.
# AT&T/Arlington, MB/Atlanta, NRG/Houston are fully climate-controlled — no heat penalty.
# BC Place/Vancouver and SoFi/Inglewood have retractable roofs but no full AC.
_HOT_VENUES = {
    "Miami Gardens":  0.05,   # Hard Rock Stadium — open-air, Florida humidity
    "Kansas City":    0.04,   # Arrowhead — open-air, midwest summer heat
    "East Rutherford":0.03,   # MetLife — open-air, NJ summer
    "Inglewood":      0.02,   # SoFi — partial roof, no AC
    "Santa Clara":    0.02,   # Levi's — open-air, Bay Area afternoon heat
    "Foxborough":     0.02,   # Gillette — open-air, New England
    "Toronto":        0.02,   # BMO Field — open-air
    "Guadalupe":      0.03,   # Estadio BBVA — open-air, NL Mexico heat
    "Mexico City":    0.02,   # Azteca — open-air (altitude already modeled separately)
    "Vancouver":      0.01,   # BC Place — retractable roof, no AC, but mild climate
}


def _heat_sigma(city: str) -> float:
    return _HOT_VENUES.get(city, 0.0)


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


def _sample_jitter(sigma: float, rng: np.random.Generator) -> float:
    """Sample a positive day-factor multiplier. Clipped so it can't go below 0.5."""
    return float(np.clip(rng.normal(1.0, sigma), 0.5, 1.5))


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

    # Per-match jitter: each team gets an independent random day-factor.
    # Hot outdoor venues add extra variance on top of the base sigma.
    city = fixture.get("city", "")
    sigma = JITTER_SIGMA_BASE + _heat_sigma(city)
    lh *= _sample_jitter(sigma, rng)
    la *= _sample_jitter(sigma, rng)

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
