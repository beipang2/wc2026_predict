---
name: wc-team-buzz
description: >
  Collects and summarises outside opinions, tactical takes, and fan sentiment on a
  national team's World Cup 2026 chances. Use this skill when the user wants a
  "side note" or "what are people saying" perspective on a team — blog posts,
  football journalists, tactical Twitter/X threads, Reddit match threads, pundit
  previews. This is opinion and narrative, not facts. It complements wc-team-analysis
  but deliberately does not overlap with it — no squad lists, no scorelines, no ages.
  Trigger when the user says things like "what's the vibe on X team", "what are
  analysts saying", "is there any hype or concern around them", or "give me a side note".
---

# WC Team Buzz Skill

Your job is to compile a **Side Note** — a short, honest summary of what the football
world is saying about a team heading into WC 2026. This is qualitative and opinionated
by design. It should feel like the smartest thing you'd read in a pre-tournament preview
piece, not a Wikipedia entry.

This skill deliberately avoids facts already covered by wc-team-analysis (squad lists,
scorelines, player ages). Its value is in capturing narrative, sentiment, and tactical
reputation that raw data misses.

## What to search for

Run 2-3 targeted searches:
- `"[team] 2026 World Cup" site:theathletic.com OR site:theanalyst.com OR site:tifo.co`
- `"[team] 2026 World Cup" tactical analysis OR preview OR dark horse OR concern`
- `[team] 2026 site:reddit.com/r/soccer` for raw fan sentiment

Prioritise sources that go beyond match reports — tactical breakdowns, pre-tournament
previews, contrarian takes. Skim quickly and pull the most distinctive 2-3 angles.
Don't cite sources that just restate squad lists or fixtures.

## Output format

Produce a single clearly labelled block:

---
**Side Note: [Team Name]**

**The narrative**: One sentence on how the football world is framing this team going
into the tournament. (e.g. "dark horse", "over-relying on one player", "peak generation
now or never", "written off but dangerous")

**What analysts are saying**: 2-3 bullet points, each a distinct angle or concern from
a specific source or community. Keep each bullet to 1-2 sentences. Attribute loosely
(e.g. "The Athletic notes...", "r/soccer consensus is...", "Tifo Football argues...").

**Contrarian take**: One honest pushback — either against the hype or against the
dismissal. What would a smart skeptic say?

**Sentiment score**: A simple read: Overhyped / Fairly assessed / Underappreciated
---

## Style rules
- This is opinion, so own it — write with a point of view
- Quotes are good if you find a sharp one; paraphrase if not
- If the sentiment across sources is genuinely mixed, say so — don't force consensus
- Keep the whole output under 200 words — this is a side note, not a report
- If you can't find useful outside analysis (e.g. team is obscure), say so briefly
  rather than padding with generic observations
