"""Wildcard selection simulator: best 8 of 12 third-place teams advance.

FIFA 2026 tiebreaker order for third-place ranking:
  1. Points
  2. Goal difference
  3. Goals scored
  4. FIFA ranking (lower = better, used as final tiebreaker since we don't model fair play)
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from models.group import GroupTable
from models.match import simulate_match
from models.ratings import load_teams

DATA_DIR = Path(__file__).parent.parent / "data"


@dataclass
class ThirdPlaceEntry:
    code: str
    group: str
    pts: int
    gd: int
    gf: int
    fifa_rank: int

    def sort_key(self) -> tuple:
        # higher pts/gd/gf is better; lower fifa_rank is better
        return (self.pts, self.gd, self.gf, -self.fifa_rank)


def _load_all_fixtures() -> dict[str, list[dict]]:
    all_fixtures = json.loads((DATA_DIR / "fixtures.json").read_text())
    by_group: dict[str, list[dict]] = defaultdict(list)
    for f in all_fixtures:
        by_group[f["group"]].append(f)
    return dict(by_group)


def simulate_wildcards(n: int = 10_000, seed: int | None = None) -> dict:
    """Run n full-tournament group-stage simulations and determine wildcard selection."""
    groups_data = json.loads((DATA_DIR / "groups.json").read_text())
    all_fixtures = _load_all_fixtures()
    teams_data = load_teams()

    group_ids = list(groups_data.keys())
    rng = np.random.default_rng(seed)

    # count how often each team is selected as a wildcard
    wildcard_counts: dict[str, int] = defaultdict(int)
    third_place_counts: dict[str, int] = defaultdict(int)

    # track stats when a team finishes 3rd
    pts_when_3rd: dict[str, list[int]] = defaultdict(list)
    gd_when_3rd: dict[str, list[int]] = defaultdict(list)

    for _ in range(n):
        third_place_entries: list[ThirdPlaceEntry] = []

        for gid in group_ids:
            team_codes = groups_data[gid]["teams"]
            fixtures = all_fixtures.get(gid, [])

            table = GroupTable(team_codes)
            for fixture in fixtures:
                hc, ac = fixture["home"], fixture["away"]
                if hc not in teams_data or ac not in teams_data:
                    continue
                hg, ag = simulate_match(teams_data[hc], teams_data[ac], fixture, rng)
                table.record_result(hc, ac, hg, ag)

            standings = table.standings()
            if len(standings) >= 3:
                third_code = standings[2]
                rec = table.records[third_code]
                third_place_entries.append(ThirdPlaceEntry(
                    code=third_code,
                    group=gid,
                    pts=rec.pts,
                    gd=rec.gd,
                    gf=rec.gf,
                    fifa_rank=teams_data[third_code].get("fifa_rank", 999),
                ))
                third_place_counts[third_code] += 1
                pts_when_3rd[third_code].append(rec.pts)
                gd_when_3rd[third_code].append(rec.gd)

        # rank the 12 third-place teams, take best 8
        third_place_entries.sort(key=lambda e: e.sort_key(), reverse=True)
        for entry in third_place_entries[:8]:
            wildcard_counts[entry.code] += 1

    # build results
    all_third_place_teams = list(third_place_counts.keys())

    results = {
        "simulations": n,
        "teams": {},
    }

    # find each team's most common group when finishing 3rd
    team_group: dict[str, str] = {}
    for gid in group_ids:
        for code in groups_data[gid]["teams"]:
            team_group[code] = gid

    for code in all_third_place_teams:
        n3 = third_place_counts[code]
        nw = wildcard_counts.get(code, 0)
        results["teams"][code] = {
            "name": teams_data[code]["name"],
            "group": team_group.get(code, "?"),
            "p_3rd": round(n3 / n * 100, 1),
            "p_wildcard_given_3rd": round(nw / n3 * 100, 1) if n3 > 0 else 0.0,
            "p_wildcard": round(nw / n * 100, 1),
            "xpts_when_3rd": round(sum(pts_when_3rd[code]) / n3, 2) if n3 > 0 else 0.0,
            "xgd_when_3rd": round(sum(gd_when_3rd[code]) / n3, 2) if n3 > 0 else 0.0,
        }

    return results
