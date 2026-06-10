"""Knockout stage simulator: R32 → R16 → QF → SF → Final.

Bracket slots use position codes resolved from group stage results:
  1A = 1st place Group A,  2B = 2nd place Group B,  WC-C = wildcard from Group C

Knockout rules:
- 90 min regulation (Poisson + Dixon-Coles, same as group stage)
- If draw: 30 min extra time (goals scaled by 1/3)
- If still draw: penalty shootout (ELO-weighted, 30% regression to 50/50)
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from models.match import simulate_match, expected_goals
from models.ratings import load_teams

DATA_DIR = Path(__file__).parent.parent / "data"
RESULTS_DIR = Path(__file__).parent.parent / "results"

BRACKET_TREE = {
    "qf": [(89, 90), (93, 94), (91, 92), (95, 96)],
    "sf": [(0, 1), (2, 3)],
}


def resolve_bracket(gs: dict, wc: dict) -> dict[str, str]:
    """Build position-code -> team-code mapping from simulation results."""
    slot_map: dict[str, str] = {}

    for gid, data in gs.items():
        ranked = sorted(data["teams"].items(), key=lambda x: x[1]["p_advance"], reverse=True)
        slot_map[f"1{gid}"] = ranked[0][0]
        slot_map[f"2{gid}"] = ranked[1][0]

    top2 = set()
    for gid, data in gs.items():
        ranked = sorted(data["teams"].items(), key=lambda x: x[1]["p_advance"], reverse=True)
        top2.update(code for code, _ in ranked[:2])

    wc_teams = sorted(wc["teams"].items(), key=lambda x: x[1]["p_wildcard"], reverse=True)
    group_wc: dict[str, str] = {}
    for code, d in wc_teams:
        if code in top2:
            continue
        grp = d.get("group", "?")
        if grp not in group_wc:
            group_wc[grp] = code

    for grp, code in group_wc.items():
        slot_map[f"WC-{grp}"] = code

    return slot_map


def _penalty_winner(home: str, away: str, teams_data: dict, rng: np.random.Generator) -> str:
    diff = teams_data[home]["elo"] - teams_data[away]["elo"]
    p_home = 1 / (1 + 10 ** (-diff / 400))
    p_home = 0.5 + (p_home - 0.5) * 0.3
    return home if rng.random() < p_home else away


def simulate_ko_match(
    home: str,
    away: str,
    teams_data: dict,
    rng: np.random.Generator,
    fixture: dict | None = None,
) -> str:
    if fixture is None:
        fixture = {"home": home, "away": away, "altitude_m": 0, "home_advantage": None, "city": ""}

    hg, ag = simulate_match(teams_data[home], teams_data[away], fixture, rng)
    if hg != ag:
        return home if hg > ag else away

    lh, la = expected_goals(teams_data[home], teams_data[away], fixture)
    et_hg = int(rng.poisson(lh * (30 / 90)))
    et_ag = int(rng.poisson(la * (30 / 90)))
    if et_hg != et_ag:
        return home if et_hg > et_ag else away

    return _penalty_winner(home, away, teams_data, rng)


def simulate_knockout(n: int = 10_000, seed: int | None = None) -> dict:
    bracket = json.loads((DATA_DIR / "bracket.json").read_text())
    gs      = json.loads((RESULTS_DIR / "group_stage.json").read_text())
    wc      = json.loads((RESULTS_DIR / "wildcards.json").read_text())
    teams_data = load_teams()
    rng = np.random.default_rng(seed)

    slot_map = resolve_bracket(gs, wc)

    def resolve(slot: str) -> str:
        team = slot_map.get(slot)
        if team is None:
            raise ValueError(f"Cannot resolve bracket slot '{slot}' — run --all and --wildcards first.")
        return team

    r32_matches: dict[int, dict] = {}
    for m in bracket["round_of_32"]:
        home = resolve(m["home"])
        away = resolve(m["away"])
        r32_matches[m["id"]] = {**m, "home": home, "away": away}

    r16_pairs = {m["id"]: m for m in bracket["round_of_16"]}

    r32_teams: set[str] = {m["home"] for m in r32_matches.values()} | {m["away"] for m in r32_matches.values()}
    reach: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for _ in range(n):
        # R32
        r32_winners: dict[int, str] = {}
        for mid, m in r32_matches.items():
            fixture = {"home": m["home"], "away": m["away"], "altitude_m": 0,
                       "home_advantage": m["home"], "city": m.get("city", "")}
            winner = simulate_ko_match(m["home"], m["away"], teams_data, rng, fixture)
            r32_winners[mid] = winner
            reach[winner]["r32"] += 1

        # R16
        r16_winners: dict[int, str] = {}
        for rid, r in r16_pairs.items():
            home = r32_winners[r["slot_a"]]
            away = r32_winners[r["slot_b"]]
            winner = simulate_ko_match(home, away, teams_data, rng)
            r16_winners[rid] = winner
            reach[winner]["r16"] += 1

        # QF
        qf_winners: list[str] = []
        for r16a_id, r16b_id in BRACKET_TREE["qf"]:
            winner = simulate_ko_match(r16_winners[r16a_id], r16_winners[r16b_id], teams_data, rng)
            qf_winners.append(winner)
            reach[winner]["qf"] += 1

        # SF
        sf_winners: list[str] = []
        for qa_idx, qb_idx in BRACKET_TREE["sf"]:
            winner = simulate_ko_match(qf_winners[qa_idx], qf_winners[qb_idx], teams_data, rng)
            sf_winners.append(winner)
            reach[winner]["sf"] += 1

        # Final
        champion = simulate_ko_match(sf_winners[0], sf_winners[1], teams_data, rng)
        reach[champion]["final"] += 1

    results = {"simulations": n, "teams": {}}
    for code in r32_teams:
        r = reach[code]
        results["teams"][code] = {
            "name":    teams_data[code]["name"],
            "p_r32":   round(r.get("r32",  0) / n * 100, 1),
            "p_r16":   round(r.get("r16",  0) / n * 100, 1),
            "p_qf":    round(r.get("qf",   0) / n * 100, 1),
            "p_sf":    round(r.get("sf",   0) / n * 100, 1),
            "p_final": round(r.get("final",0) / n * 100, 1),
        }

    results["bracket"] = {
        "round_of_32": list(r32_matches.values()),
        "round_of_16": bracket["round_of_16"],
    }
    results["slot_map"] = slot_map
    return results
