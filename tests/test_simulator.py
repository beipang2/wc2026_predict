import pytest

from models.simulator import simulate_group


def test_probabilities_sum_to_100():
    results = simulate_group("A", n=500, seed=42)
    for code, d in results["teams"].items():
        total = d["p_1st"] + d["p_2nd"] + d["p_3rd"] + d["p_4th"]
        assert abs(total - 100.0) < 1.0, f"{code} probs sum to {total}"


def test_advance_equals_1st_plus_2nd():
    results = simulate_group("A", n=500, seed=42)
    for code, d in results["teams"].items():
        expected = round(d["p_1st"] + d["p_2nd"], 1)
        assert abs(d["p_advance"] - expected) < 0.2


def test_all_fixtures_have_scoreline():
    results = simulate_group("A", n=200, seed=42)
    assert len(results["fixtures"]) == 6
    for key, fx in results["fixtures"].items():
        assert "-" in fx["most_likely_score"]
        assert fx["frequency"] > 0


def test_reproducible_with_seed():
    r1 = simulate_group("A", n=1000, seed=99)
    r2 = simulate_group("A", n=1000, seed=99)
    for code in r1["teams"]:
        assert r1["teams"][code]["xpts"] == r2["teams"][code]["xpts"]
