---
name: business-simulation
description: >
  A battle-tested methodology for running ANY business in real-time simulation as an
  autonomous operator agent. Pick a venture — a shop, restaurant, SaaS product, boutique,
  fund, agency, nonprofit, or creator business — and the agent operates it day by day:
  calendar discipline, real-world grounding, source-of-truth locking, delegated authority,
  an operational tracker, a named persona team, finance honesty, risk/cadence management,
  and self-correction. Triggers: "simulate a business", "run a business sim", "operator
  agent", "business simulation", "Day 0 setup".
license: MIT
metadata:
  author: hyperagent
  version: "1.0.0"
  source: alexmcdonnell-airtable/hyperagent-public-skills
---

# Business Simulation Operator Method

Run a business that doesn't exist yet — in real time, as its operator. You pick the venture (a coffee shop, a restaurant, a SaaS product, a boutique, a fund, an agency, a nonprofit, a creator business), and the agent runs it day by day: making decisions, hiring a team, managing money, shipping work, and reporting to you as the founder/investor.

This is a methodology, not a fixed script — it adapts to whatever business you point it at. Every rule below was paid for by a real failure running these simulations; following them is what keeps a months-long run coherent, grounded, and trustworthy instead of drifting into fiction.

## The loop

- **You set the premise** — what the business is, where, the starting capital, and the goal with its target date.
- **The agent operates** within an agreed authority threshold: deciding and executing routine work, escalating the big calls.
- **One tracker holds the truth** — tasks, hires, finances, content, and a media library.
- **The agent reports** on a cadence you choose.

---

## Day 0 — standing up a new simulation

Do these once, before any operating happens:

1. **Define the venture & constraints.** Business type, location/market, starting capital, and the goal with a target date — "open in 130 days," "$10K MRR in 6 months," "raise and deploy a $1M fund in a year."
2. **Anchor the clock.** Pick the calendar date that is sim Day 1 and lock it in a script. Never re-derive it later. (§1)
3. **Stand up the tracker.** Create the operational record of truth with functional tables: project mgmt, hiring, finance, content, plus a media library. (§5)
4. **Agree the autonomy threshold.** What can the agent decide and execute alone vs. escalate? Put a number on it. (§4)
5. **Staff the persona team.** Name the specialist roles this business needs and attribute work to them. (§6)
6. **Lock initial sources of truth.** Any approved location, brand, or plan becomes canonical; everything downstream conforms. (§3)
7. **Set the cadence.** How often you'll check in, and whether the agent runs autonomously between check-ins. (§9)

Then operate. Open every status update with `Day X of N · Weekday, Month D, Year` and a one-line state of the business.

---

## 1. Calendar discipline — the #1 failure mode

Real days elapse 1:1 with sim days, and **day-number drift is the most persistent bug**.

- Anchor **Day 1 to a calendar date once**; always compute `sim_day = (today − day_one) + 1`. NEVER re-derive the anchor from a milestone.
- Codify the math in a **script**, not prose. Run it at the top of every check-in.
- Record **user-confirmed checkpoints** ("today is Day X") in the script's self-test; run `--check` to catch corruption.
- When the user has been away N days, **narrate the gap** using the tracker as ground truth, then continue.

### Sim clock script (template)

```python
#!/usr/bin/env python3
import sys
from datetime import date, timedelta

DAY_ONE = date(2026, 1, 5)      # the calendar date you call sim Day 1
MILESTONES = {
    "Soft Launch": date(2026, 4, 1),
    "Launch Day":  date(2026, 4, 15),
}
CHECKPOINTS = {                  # user-confirmed: date -> expected day
    date(2026, 2, 3): 30,
    date(2026, 3, 6): 61,
}

def sim_day(d): return (d - DAY_ONE).days + 1
def date_for(n): return DAY_ONE + timedelta(days=n - 1)

def main(argv):
    if "--check" in argv:
        ok = True
        for d, exp in CHECKPOINTS.items():
            got = sim_day(d)
            print(f"[{'OK' if got==exp else 'FAIL'}] {d} -> Day {got} (expected {exp})")
            ok &= got == exp
        sys.exit(0 if ok else 1)
    if "--day" in argv:
        n = int(argv[argv.index("--day") + 1])
        print(f"Day {n} = {date_for(n).strftime('%A, %B %d, %Y')}"); return
    d = date.fromisoformat(argv[1]) if len(argv) > 1 else date.today()
    print(f"Day {sim_day(d)} · {d.strftime('%A, %B %d, %Y')}")
    for name, md in MILESTONES.items():
        print(f"  {(md - d).days} days to {name} ({md.strftime('%b %d')})")

if __name__ == "__main__":
    main(sys.argv)
```

---

## 2. Real-world grounding + self-audit

Fabricated addresses, vendors, and prices destroy trust and compound.

- Every named entity (location, vendor, supplier, contractor, hire, price) must be **verified against a real source** before it enters the record. Search first; never invent.
- End updates with a short **self-audit**: sim-day verified, entities real, no drift, constraints honored.
- When an error is found, **log a correction entry** — corrections are part of the record, not embarrassments to hide.
- Vet entities for **fit, not just existence** (e.g. a real employment lawyer who only represents employees is the wrong real lawyer for an employer).

## 3. Source-of-truth locking

- When the user approves an artifact (floor plan, brand system, product spec), declare it **canonical**. Everything downstream conforms.
- When two truths conflict, **surface the conflict and let the user designate** which wins.
- Hierarchy: user designation > approved artifact > verified real-world data > generated content.

## 4. Delegated authority — decide, execute, document

- Agree an explicit **autonomy threshold** scaled to the business (e.g. ≤$10K: decide and execute; above: escalate with options + a recommendation).
- Within authority: **make the call, log it, report it** — don't ask.
- Exception: identity/branding/legal/irreversible commitments require explicit confirmation.

## 5. Operational record of truth (tracker)

- Keep one structured tracker with **functional tables**: project management, hiring, finance, content/social, plus resource + media libraries.
- **Moment-of-creation logging**: a deliverable doesn't ship until indexed; statuses move Todo → In progress → Done in the same turn.
- Mark superseded assets `Replaced`/`Archived` rather than deleting.

## 6. Persona team

- Staff the simulation with **named specialist personas** sized to the business. A café: GM, head barista, social, web, HR. A SaaS: PM, growth lead, support, eng.
- Operating principle: **AI handles volume; humans handle stakes.**

## 7. Working memory + learning hygiene

- Maintain a **context doc** (decisions, corrections, numbers, plan tasks) updated as things happen.
- **Memory bloat is dangerous**: an auto-saved memory duplicating a wrong fact re-injects the error every turn. Fix canonical facts at **all roots**.
- Codify recurring procedures as **skills** so they're drift-proof.

## 8. Finance honesty

- Build projections from **verified real costs**; when reality lands, **re-baseline publicly** and show the variance ledger.
- Distinguish **planned losses** (funded, expected) from surprises.
- Track cash position at every update. Name future decision points before they arrive.

## 9. Risk + cadence

- Actively scan for **sequencing risks** (inspection scheduled 1 day before launch = zero buffer) and fix them by re-sequencing early.
- For unattended runs: check the tracker for overdue + due-soon items, apply a **repetition guard**, and report all-clear silently.

## 10. Media discipline

- **No speculative media** — generate images/video only when requested or when the sim timeline puts that production at the current moment.
