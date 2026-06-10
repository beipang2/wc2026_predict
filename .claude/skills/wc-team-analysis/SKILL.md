---
name: wc-team-analysis
description: >
  Deep-dive analysis of a national football team's World Cup readiness. Use this skill
  whenever someone asks to evaluate, compare, debate, or fact-check a national team's
  strength for the 2026 World Cup — especially questions like "are they as good as their
  ELO suggests?", "how do they compare to their last World Cup squad?", "is the coach
  new?", "who are the key players and how old are they?", or "should we adjust this
  team's ratings?". Also trigger when the user asks about all teams in a group: "analyze
  each team in Group B", "preview Group A", "tell me about the teams in Group C" — treat
  this as running the same per-team analysis on each team in the group, one after another.
  Also trigger when the user wants to debate a specific team matchup (e.g. "can Morocco
  really go head to head with Brazil?") or when they've just watched a match and want to
  cross-check it against the model's assumptions.
---

# WC Team Analysis Skill

Your job is to produce a structured, debate-ready factual brief on a national football
team's World Cup 2026 readiness. The user is using this to decide whether to adjust the
team's ratings in a Monte Carlo simulation — so facts matter more than hype, and honest
assessments of weakness are more valuable than cheerleading.

If the user asks about all teams in a group, first confirm which four teams are in that
group (one quick web search), then apply this same analysis to each team in turn. No
group comparison table, no advancement odds — just four consecutive team briefs.

## What to research

Use web search to find current, specific information. Don't rely on training data for
squad details, ages, or coaching staff — these change constantly and stale data produces
wrong conclusions.

**Only use results from 2024 onwards.** Earlier history is largely irrelevant — squads
turn over, coaches change, form shifts. Pre-2024 data should only be referenced to flag
aging players still in the squad.

Search for:
- Current 2026 WC squad announcement and notable absences (injuries, dropped)
- Coach name, when appointed, system/style
- Key player ages for current squad starters
- 2024–2026 competitive results: Nations League, AFCON, Euros, Copa America, qualifying
- June 2026 pre-tournament friendly results with scores

## Output structure

Always produce exactly these four sections in this order. Be concise — one tight
paragraph or a short table per section. No padding.

### 1. Coach & System
- Who is the current coach, when appointed, what system/style?
- If appointed < 6 months before tournament: flag as red flag.

### 2. Key Players (2026 squad)
For the 5-6 most important players, list: name, position, club, age, and a one-line
assessment (peaking / prime / aging / declining). Flag any key absences due to injury
or form. This tells the user whether the ELO — which reflects past results — still
matches their current personnel ceiling.

### 3. Form & Results (2024–2026 only)
Three data points, in this order:

**2024–2025 competitive record**: Nations League / confederation tournament / qualifying.
How dominant or shaky? Who did they struggle against? Note standout results and GD.

**2026 qualifying stretch + pre-tournament friendlies**: Final qualifying results and
all June 2026 friendly scores. What did these reveal about readiness?

**Injury/availability concerns**: Who is doubtful or confirmed out for the tournament?

### 4. Verdict: Is the Rating Stale or Fair?
Make a clear call:

- **Overrated**: explain specifically why
- **Fairly rated**: explain why the rating holds
- **Underrated**: explain why they're stronger than the rating suggests

Give a concrete steer on the form multiplier (range 0.80–1.20) with a specific
recommended value the user can act on. No hedging.

## Style rules
- Lead with facts, not adjectives
- Name players specifically when calling them "key"
- If the user says they watched a match, treat that as primary evidence and cross-check
  against what you find — don't dismiss it
- Do not say "it remains to be seen" or "only time will tell" — make a call
- Flag genuine uncertainty clearly rather than hedging everything softly
