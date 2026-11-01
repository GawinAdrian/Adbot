# Cadence and rules: watching, reporting, optimising (Adbot)

Dated 2026-11-01. **These are Adbot product decisions, not platform facts.** No threshold below is a Google
statement. Each can be changed by editing the named constant in `claude_ads_core/watch.py`; the table is checked
against the code by `tests/core/test_cadence_doc.py`.

## Who looks, and how often

| Level | Rhythm | Who | What | Result |
|---|---|---|---|---|
| Watcher | daily, automatic (`scripts/schedule_watch.py`) | script, **no AI, no cost** | spend vs. daily budget, delivery stopped, conversion drop, rejected ads, stale data | `watch-result.json` and a traffic light (green, yellow, red, grey) |
| Weekly analysis | once a week (setting `report_weekday`, default Monday), started by the user with `/bericht` | AI interprets the watcher numbers | trend vs. previous week, likely causes, **at most 3 recommendations** with benefit, risk, confidence | weekly report and cockpit |
| Monthly analysis | once a month (setting `deep_review`) | AI | search terms (negatives and new keywords only with the report), landing page, budget split | monthly report |
| Change rhythm | **at most one change round per campaign per week** | the user approves | exceptions: tracking, payment, or runaway-spend events | change log with before/after |

If the computer is off, the next run covers the missing days and the cockpit shows a **data gap**. Cloud routines
are not used because they cannot reach the local sign-in; `/loop` needs an open session.

## Watcher thresholds (Adbot starting values)

| Constant | Value | Meaning |
|---|---|---|
| `PACING_WINDOW_DAYS` | 3 | recent days used for spend and delivery |
| `PACING_CAPPED_RATIO` | 0.90 | spend at or above 90 % of the daily budget on every recent day: limited by budget |
| `PACING_UNDER_RATIO` | 0.20 | spend at or below 20 % of the daily budget on every recent day: delivers very little |
| `PACING_OVER_RATIO` | 2.50 | one day above 250 % of the daily budget: unusually high (Adbot default; no platform limit is claimed) |
| `CONVERSION_WINDOW_DAYS` | 7 | compare the last 7 days with the 7 days before |
| `MIN_CLICKS_FOR_CONVERSION_RULES` | 30 | fewer clicks in the window: "not enough data", no alarm |
| `MIN_CLICKS_FOR_NO_CONVERSION` | 50 | clicks needed before "no conversions at all" is reported |
| `MIN_PREVIOUS_CONVERSIONS_FOR_DROP` | 3 | conversions needed in the week before a "drop" is reported; fewer is "too few to call it a drop" |
| `DATA_GAP_DAYS` | 2 | data pulled more than this many days ago is a data gap |

Rules, in plain words:

1. **Budget used up / very low / unusually high** (warning). Says what happened, not what to change.
2. **Delivery stopped** (critical): no impression for 3 days although there were impressions before.
3. **Conversion drop** (critical): enough clicks, zero conversions, but at least 3 conversions in the week before. Check tracking first. With 1 or 2 conversions before, the answer is "too few to call it a drop".
4. **No conversions** (warning): many clicks, zero now and zero before.
5. **Rejected ads** (critical): needs the ad approval status; without it the check is "unknown" and listed as missing.
6. **Small numbers never alarm**: under the click minimum the answer is "not enough data".
7. Billing and payment status is **always listed as a missing input**; it is not readable with the supported access.

The reference day is the last complete day before the data was pulled. A day without a row counts as zero delivery, **except** for days before a campaign's first row: a campaign with less than 3 days of data is "too new to judge".

Delivery stopped compares the last 3 days with **every** earlier day in the pulled window, so a campaign that went quiet long ago is still reported. If a whole pull returns no rows (nothing was shown), the job records a yellow "no data" result instead of failing.

**Data gap** is reported when the data is stale **or** when no successful run happened for more than 2 days (the watcher compares with the previous run's date).

## Optimisation rules (what the assistant may suggest)

- Suggestions come from the current report only; each has before/after, object IDs, expected effect, learning-phase
  note, rollback, and confidence. "Data too thin, wait" is a valid result and often the right one for small accounts.
- After a larger change (budget, bid strategy, structure) wait at least **7 days** before judging it (Adbot default;
  Google does not publish one fixed waiting time that fits every account).
- No fixed pause rule after a CPA multiple, no fixed budget-to-CPA ratio, no change to a learning campaign during a
  compliance, tracking, or runaway-spend event unless that event is the reason.
- Negative keywords only with a search terms report and an over-blocking review; never named from memory.
- Beta, premium, or unavailable features are recorded as opportunities, never as missing health.
- No deletion. Pause, archive, label, or back up instead.
- In this version the user applies every change herself; API writes are disabled.

## Where results live

`.adbot/runs/<run-id>/` (git-ignored): `watch-result.json`, `monitoring-bundle.json` (only when disk encryption is
confirmed in the settings, because the contract requires verified encryption for account data), and the cockpit page.
Each run uses a new directory; earlier runs are never overwritten.
