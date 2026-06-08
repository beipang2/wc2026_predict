"""Interactive bracket picker — runs head-to-head sims and lets you pick winners."""

from __future__ import annotations

import json
from pathlib import Path
from collections import Counter

import numpy as np

from models.match import simulate_match
from models.ratings import load_teams

TEAMS = load_teams()
N = 100_000
RNG = np.random.default_rng(42)

DATA_DIR = Path("data")
RESULTS_DIR = Path("results")


def resolve_slots() -> dict[str, str]:
    """Map position codes (1A, 2B, WC-C) to team codes."""
    gs = json.loads((RESULTS_DIR / "group_stage.json").read_text())
    wc = json.loads((RESULTS_DIR / "wildcards.json").read_text())

    slot_map: dict[str, str] = {}
    top2: set[str] = set()

    for gid, data in gs.items():
        ranked = sorted(data["teams"].items(), key=lambda x: x[1]["p_advance"], reverse=True)
        slot_map[f"1{gid}"] = ranked[0][0]
        slot_map[f"2{gid}"] = ranked[1][0]
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


def h2h(a: str, b: str) -> tuple[float, float, float, list]:
    ta, tb = TEAMS[a], TEAMS[b]
    fixture = {"home": a, "away": b, "city": ""}
    wa = wb = d = 0
    scores: Counter = Counter()
    for _ in range(N):
        hg, ag = simulate_match(ta, tb, fixture, RNG)
        scores[f"{hg}-{ag}"] += 1
        if hg > ag: wa += 1
        elif ag > hg: wb += 1
        else: d += 1
    return wa / N * 100, d / N * 100, wb / N * 100, scores.most_common(5)


def pick(match_id, home: str, away: str, winners: dict) -> str:
    hn = TEAMS[home]["name"]
    an = TEAMS[away]["name"]
    pa, pd, pb, top = h2h(home, away)
    print(f"\n{'─'*55}")
    print(f"  #{match_id}  {hn} vs {an}")
    print(f"  {hn}: {pa:.1f}%  |  Draw: {pd:.1f}%  |  {an}: {pb:.1f}%")
    print(f"  Top scorelines: " + "  ".join(f"{s}({c/N*100:.1f}%)" for s, c in top))
    while True:
        choice = input(f"  Pick [1={hn} / 2={an}]: ").strip()
        if choice == "1":
            print(f"  → {hn} advances")
            return home
        if choice == "2":
            print(f"  → {an} advances")
            return away
        print("  Enter 1 or 2.")


def main():
    slots = resolve_slots()

    # Manual overrides — your bracket picks for group stage finishing positions
    slots["2A"] = "KOR"
    slots["WC-A"] = "CZE"

    bracket = json.loads((DATA_DIR / "bracket.json").read_text())
    r32_matches = {m["id"]: m for m in bracket["round_of_32"]}
    r16_matches = {m["id"]: m for m in bracket["round_of_16"]}

    print("\n" + "═"*55)
    print("  RESOLVED GROUP STAGE SLOTS")
    print("═"*55)
    for slot, code in sorted(slots.items()):
        print(f"  {slot:<6} → {TEAMS[code]['name']}")

    winners: dict = {}

    # R32
    print("\n" + "═"*55)
    print("  ROUND OF 32")
    print("═"*55)
    for mid in sorted(r32_matches):
        m = r32_matches[mid]
        home = slots.get(m["home"], m["home"])
        away = slots.get(m["away"], m["away"])
        if home not in TEAMS or away not in TEAMS:
            print(f"  #{mid}: skipping — missing team ({home} or {away})")
            continue
        winners[mid] = pick(mid, home, away, winners)

    # R16
    print("\n" + "═"*55)
    print("  ROUND OF 16")
    print("═"*55)
    for mid in sorted(r16_matches):
        m = r16_matches[mid]
        home = winners[m["slot_a"]]
        away = winners[m["slot_b"]]
        winners[mid] = pick(mid, home, away, winners)

    # QF: QF1=(89,90), QF2=(93,94), QF3=(91,92), QF4=(95,96)
    qf_sources = [("QF1", 89, 90), ("QF2", 93, 94), ("QF3", 91, 92), ("QF4", 95, 96)]
    print("\n" + "═"*55)
    print("  QUARTER-FINALS")
    print("═"*55)
    for mid, a_src, b_src in qf_sources:
        winners[mid] = pick(mid, winners[a_src], winners[b_src], winners)

    # SF
    sf_sources = [("SF1", "QF1", "QF2"), ("SF2", "QF3", "QF4")]
    print("\n" + "═"*55)
    print("  SEMI-FINALS")
    print("═"*55)
    for mid, a_src, b_src in sf_sources:
        winners[mid] = pick(mid, winners[a_src], winners[b_src], winners)

    # Final
    print("\n" + "═"*55)
    print("  FINAL")
    print("═"*55)
    winners["F"] = pick("F", winners["SF1"], winners["SF2"], winners)

    champion = TEAMS[winners["F"]]["name"]
    print(f"\n{'═'*55}")
    print(f"  🏆  CHAMPION: {champion}")
    print(f"{'═'*55}\n")

    print("YOUR BRACKET PICKS:")
    labels = {
        **{mid: f"R32 #{mid}" for mid in range(73, 89)},
        **{mid: f"R16 #{mid}" for mid in range(89, 97)},
        "QF1": "QF1", "QF2": "QF2", "QF3": "QF3", "QF4": "QF4",
        "SF1": "SF1", "SF2": "SF2", "F": "FINAL",
    }
    for mid, code in winners.items():
        print(f"  {labels[mid]}: {TEAMS[code]['name']}")


if __name__ == "__main__":
    main()
