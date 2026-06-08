---
name: wc-team-analysis
description: >
  Deep-dive analysis of a national football team's World Cup readiness. Use this skill
  whenever someone asks to evaluate, compare, debate, or fact-check a national team's
  strength for the 2026 World Cup — especially questions like "are they as good as their
  ELO suggests?", "how do they compare to their last World Cup squad?", "is the coach
  new?", "who are the key players and how old are they?", or "should we adjust this
  team's ratings?". Also trigger when the user wants to debate a specific team matchup
  (e.g. "can Morocco really go head to head with Brazil?") or when they've just watched
  a match and want to cross-check it against the model's assumptions.
---

# WC Team Analysis Skill

Your job is to produce a structured, debate-ready factual brief on a national football
team's World Cup 2026 readiness. The user is using this to decide whether to adjust the
team's ratings in a Monte Carlo simulation — so facts matter more than hype, and honest
assessments of weakness are more valuable than cheerleading.

## What to research

Use web search to find current, specific information. Don't rely on training data for
squad details, ages, or coaching staff — these change constantly and stale data produces
wrong conclusions.

Search for:
- Current 2026 WC squad announcement
- Previous WC squad (2022 or last tournament appearance)
- Coach name, when appointed, and whether they replaced someone recently
- Key player ages (especially stars who were central at the last WC)
- Notable absences — injuries, retirements, dropped
- World Cup 2026 qualifying campaign: record, style, who they struggled against
- Recent tournament results (last AFCON / Euros / Copa America / Nations League)
- Pre-tournament friendly results (June 2026)

## Output structure

Always produce exactly these five sections in this order. Be concise — one tight
paragraph or a short table per section. No padding.

### 1. Coach
- Who is the current coach and when were they appointed?
- Same coach as their last WC, or a change?
- If changed recently (< 6 months before tournament): flag this as a red flag.
- What system/style do they play?

### 2. Squad vs Last WC
A short comparison across three buckets:
- **Gone since last WC**: key players no longer in the squad (retired, dropped, injured out)
- **Still here**: key returnees and their current ages
- **New faces**: notable additions who weren't at the last WC

Focus on impact players — the ones who actually shaped results — not squad fillers.

### 3. Key Player Ages
For the 5-6 most important players, list: name, position, club, age, and a one-line
assessment (peaking / prime / aging / declining). This tells the user whether the
team's ELO — which reflects past results — still matches their current personnel ceiling.

### 4. Form & Context
Four data points, in this order:

**Qualifying campaign**: How did they get here? Dominant, scraped through, playoffs?
Who did they struggle against? A team that barely survived CAF/CONCACAF qualifying
is a different beast from one that went unbeaten. Note goal difference and standout
results.

**Last confederation tournament**: AFCON / Euros / Copa America / Nations League —
result, style, and any honest red flags (e.g. knocked out early despite good squad,
relied on one player, defensive frailty).

**Pre-tournament friendlies (June 2026)**: Scores and what they revealed about
the starting XI, pressing intensity, and set-piece threat.


### 5. Verdict: Is the ELO/Rating Stale or Fair?
Make a clear call — this is the most important section:

- **Overrated**: explain specifically why (e.g. "2022 was their peak, three key attackers
  gone, new coach 3 months in — ELO hasn't caught up yet")
- **Fairly rated**: explain why the rating holds
- **Underrated**: explain why they're stronger than the ELO suggests

Give a concrete steer on the form multiplier used in the simulation (range 0.80–1.20).
For example: "form should be around 0.90–0.93, not 1.08 — here's why." The user needs
a number they can act on, not a hedge.

## Style rules
- Lead with facts, not adjectives
- Name players specifically when calling them "key"
- If the user says they watched a match, treat that as primary evidence and cross-check
  against what you find — don't dismiss it
- Do not say "it remains to be seen" or "only time will tell" — make a call
- Flag genuine uncertainty clearly rather than hedging everything softly
