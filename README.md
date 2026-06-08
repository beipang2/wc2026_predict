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

### 1. Simulate group stage

```bash
python3 main.py --all
```

Simulates all 12 groups and saves to `results/group_stage.json`.

To simulate a single group:
```bash
python3 main.py --group E
```

### 2. Simulate wildcard selection

```bash
python3 main.py --wildcards
```

Determines the best 8 of 12 third-place teams. Saves to `results/wildcards.json`.

### 3. Simulate knockout bracket

```bash
python3 main.py --knockout
```

Resolves bracket positions from group/wildcard results, then simulates R32 → Final. Saves to `results/knockout.json`.

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

Edit `data/teams.json` to adjust team ratings before running simulations:

| Field | Description |
|---|---|
| `attack` | Goals scored multiplier (baseline ~1.0, elite ~1.8) |
| `defense` | Goals conceded multiplier (lower = better, elite ~0.78) |
| `form` | Recent form multiplier (1.0 = neutral, 1.1 = hot, 0.9 = poor) |

After editing, rerun all three simulation steps to propagate changes.

---

## Model Details

- **Poisson distribution** for goal scoring, with Dixon-Coles correction for low-score draws
- **Per-match jitter** (`σ=0.10`): random day-factor multiplied into each team's ratings per match — captures upsets, tactical surprises, individual errors
- **Heat venue variance**: open-air hot stadiums (Miami, Kansas City) get extra jitter; climate-controlled venues (Arlington, Atlanta, Houston) get none
- **Home advantage** (`1.04`): applied only to co-host nations (USA, Mexico, Canada) for their home group stage matches
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
