"""Monte Carlo group stage simulator."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from models.group import GroupTable
from models.match import simulate_match
from models.ratings import load_teams

DATA_DIR = Path(__file__).parent.parent / "data"


def _load_fixtures(group_id: str) -> list[dict]:
    all_fixtures = json.loads((DATA_DIR / "fixtures.json").read_text())
    return [f for f in all_fixtures if f["group"] == group_id]


def _load_group_teams(group_id: str) -> list[str]:
    groups = json.loads((DATA_DIR / "groups.json").read_text())
    return groups[group_id]["teams"]


def simulate_group(
    group_id: str,
    n: int = 10_000,
    overrides: dict[str, Any] | None = None,
    seed: int | None = None,
) -> dict:
    teams_data = load_teams(overrides)
    fixtures = _load_fixtures(group_id)
    team_codes = _load_group_teams(group_id)

    rng = np.random.default_rng(seed)

    finish_counts: dict[str, list[int]] = {c: [0, 0, 0, 0] for c in team_codes}
    pts_totals: dict[str, float] = defaultdict(float)
    gd_totals: dict[str, float] = defaultdict(float)
    fixture_scorelines: dict[str, Counter] = {
        f"{f['home']}v{f['away']}": Counter() for f in fixtures
    }

    for _ in range(n):
        table = GroupTable(team_codes)
        for fixture in fixtures:
            home_code = fixture["home"]
            away_code = fixture["away"]
            if home_code not in teams_data or away_code not in teams_data:
                continue
            hg, ag = simulate_match(
                teams_data[home_code], teams_data[away_code], fixture, rng
            )
            table.record_result(home_code, away_code, hg, ag)
            key = f"{home_code}v{away_code}"
            fixture_scorelines[key][f"{hg}-{ag}"] += 1

        standings = table.standings()
        for pos, code in enumerate(standings):
            finish_counts[code][pos] += 1
            pts_totals[code] += table.records[code].pts
            gd_totals[code] += table.records[code].gd

    results = {
        "group": group_id,
        "simulations": n,
        "teams": {},
        "fixtures": {},
    }

    for code in team_codes:
        fc = finish_counts[code]
        results["teams"][code] = {
            "name": teams_data[code]["name"],
            "p_1st": round(fc[0] / n * 100, 1),
            "p_2nd": round(fc[1] / n * 100, 1),
            "p_3rd": round(fc[2] / n * 100, 1),
            "p_4th": round(fc[3] / n * 100, 1),
            "p_advance": round((fc[0] + fc[1]) / n * 100, 1),
            "xpts": round(pts_totals[code] / n, 2),
            "xgd": round(gd_totals[code] / n, 2),
        }

    for fixture in fixtures:
        key = f"{fixture['home']}v{fixture['away']}"
        top = fixture_scorelines[key].most_common(1)
        if top:
            scoreline, count = top[0]
            results["fixtures"][key] = {
                "home": fixture["home"],
                "away": fixture["away"],
                "most_likely_score": scoreline,
                "frequency": round(count / n * 100, 1),
            }

    return results


def simulate_all_groups(n: int = 10_000, overrides: dict | None = None) -> dict:
    groups = json.loads((DATA_DIR / "groups.json").read_text())
    return {gid: simulate_group(gid, n=n, overrides=overrides) for gid in groups}
