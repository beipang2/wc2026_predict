# WC 2026 Prediction Tool

Monte Carlo simulator for the 2026 FIFA World Cup. Runs 10,000+ simulations per stage using Poisson goal models with Dixon-Coles correction, per-match jitter, and heat venue variance.

---

## Setup

```bash
pip install -r requirements.txt
```

---

## Workflow

Run in order — each step depends on the previous output.

### 1. Simulate group stage + wildcards

```bash
python3 main.py --groups
```

Simulates all 12 groups and wildcard selection (best 8 of 12 third-place teams). Saves to `results/group_stage.json` and `results/wildcards.json`.

To simulate a single group:
```bash
python3 main.py --group E
```

### 2. Simulate knockout bracket

```bash
python3 main.py --knockout
```

Runs the full tournament internally (group stage + wildcards + knockout bracket R32 → Final). Saves to `results/knockout.json`.

---

## View Results

```bash
# Full group stage bracket + wildcard table
python3 parse_results.py --mode bracket

# Knockout stage win probabilities per team
python3 parse_results.py --mode knockout

# Predicted bracket (most likely winner each match)
python3 parse_results.py --mode picks

# Everything
python3 parse_results.py --mode all
```

Output is also saved as plain text to `results/bracket.txt`.

---

## Fill Your Bracket

Interactive head-to-head picker — shows simulation probabilities for each matchup and lets you pick winners round by round:

```bash
python3 bracket_picker.py
```

---

## Tune Team Ratings

Edit `data/teams.json` to adjust team ratings before running simulations.

**Do not add `attack` or `defense` fields.** Both are derived from ELO automatically — see Model Details below.

| Field | Type | Description |
|---|---|---|
| `elo` | required | World Football Elo rating. This is the primary strength signal — attack and defense baselines are computed from it. |
| `style` | optional | Structural attacking tendency vs ELO expectation. Positive = team consistently scores more than ELO implies (e.g. Norway with Haaland: `+0.10`). Bounded to `±0.15`. Leave unset (defaults to `0`) for most teams. |
| `form` | optional | Current squad readiness multiplier. `1.0` = at ELO baseline. `1.1` = hot (strong warm-ups, full squad). `0.85` = poor (injuries, coaching collapse). Applied to both attack and defense unless overridden below. |
| `form_attack` | optional | Overrides `form` for attack only. Use when injuries are attacker-specific (e.g. Brazil missing two starting wingers). |
| `form_defense` | optional | Overrides `form` for defense only. Use when injuries are defender/goalkeeper-specific. |

After editing, rerun all three simulation steps to propagate changes.

---

## Model Details

### Rating pipeline

Each team's match parameters are derived in three layers:

```
attack  = (elo_attack_base(elo)  + style) × form_attack
defense = elo_defense_base(elo)            / form_defense
```

**ELO baseline formulas** (calibrated so France ELO 1985 → attack 1.85, defense 0.78; Curacao ELO 1455 → 0.79, 1.28):

```
elo_attack_base(elo)  = max(0.50,  0.002 × elo − 2.12)
elo_defense_base(elo) = max(0.65,  2.652 − 0.000943 × elo)
```

`defense` is a goals-against multiplier — lower means harder to score against. A neutral team (ELO ~1650) has attack ≈ 1.18 and defense ≈ 1.10. An elite team (ELO ~1950) has attack ≈ 1.78 and defense ≈ 0.81.

In each match: `λ_home = attack(home) × defense(away) × home_advantage`

### Simulation mechanics

- **Poisson distribution** for goal scoring, with Dixon-Coles correction for low-score draws
- **Per-match jitter** (`σ=0.10`): random day-factor multiplied into each team's ratings — captures upsets, tactical surprises, individual errors
- **Heat venue variance**: open-air hot stadiums (Miami, Kansas City) add extra jitter; climate-controlled venues (Arlington, Atlanta, Houston) add none
- **Home advantage** (`1.04`): applied to co-host nations (USA, Mexico, Canada) for their home group stage matches
- **Altitude penalty**: applied to matches at Mexico City and Guadalupe

---

## Files

```
data/
  teams.json       # Team ratings and notes
  groups.json      # Group compositions
  fixtures.json    # Group stage fixtures with venue/city/altitude
  bracket.json     # Knockout bracket structure (position codes)

models/
  match.py         # Poisson match simulator
  simulator.py     # Group stage Monte Carlo
  wildcard.py      # Wildcard selection simulator
  knockout.py      # Knockout bracket simulator
  ratings.py       # Team rating loader

results/           # Generated — do not edit manually
  group_stage.json
  wildcards.json
  knockout.json
  bracket.txt

main.py            # CLI entrypoint
parse_results.py   # Display results
bracket_picker.py  # Interactive bracket filler
```
