import numpy as np
import pytest

from models.match import expected_goals, simulate_match

HOME_TEAM = {"attack": 1.6, "defense": 0.85, "elo": 1850}
AWAY_TEAM = {"attack": 1.0, "defense": 1.2, "elo": 1510}

FIXTURE_NEUTRAL = {
    "home": "MEX", "away": "RSA",
    "altitude_m": 300, "home_advantage": None,
}
FIXTURE_HOME_ADV = {
    "home": "MEX", "away": "RSA",
    "altitude_m": 300, "home_advantage": "MEX",
}
FIXTURE_HIGH_ALT = {
    "home": "MEX", "away": "RSA",
    "altitude_m": 2250, "home_advantage": "MEX",
}


def test_simulate_match_returns_nonneg_integers():
    rng = np.random.default_rng(42)
    hg, ag = simulate_match(HOME_TEAM, AWAY_TEAM, FIXTURE_NEUTRAL, rng)
    assert isinstance(hg, int) and hg >= 0
    assert isinstance(ag, int) and ag >= 0


def test_home_advantage_increases_lambda():
    lh_neutral, la_neutral = expected_goals(HOME_TEAM, AWAY_TEAM, FIXTURE_NEUTRAL)
    lh_home, la_home = expected_goals(HOME_TEAM, AWAY_TEAM, FIXTURE_HOME_ADV)
    assert lh_home > lh_neutral
    assert la_home == la_neutral  # home advantage only affects home attack


def test_altitude_reduces_away_attack():
    _, la_low = expected_goals(HOME_TEAM, AWAY_TEAM, FIXTURE_NEUTRAL)
    _, la_high = expected_goals(HOME_TEAM, AWAY_TEAM, FIXTURE_HIGH_ALT)
    assert la_high < la_low


def test_altitude_thresholds():
    from models.match import _altitude_factor
    assert _altitude_factor(2001) == 0.88
    assert _altitude_factor(1600) == 0.94
    assert _altitude_factor(500) == 1.0
