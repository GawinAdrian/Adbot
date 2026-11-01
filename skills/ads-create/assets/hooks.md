# Hook generation: angles, rules, and output

> Status: qualitative, unscored creative aid. Hooks are hypotheses, never proof of attention or performance.

## Required gates

- Context gate: load the validated brand profile, audience, offer, approved claims, locale, and placement before writing a single hook.
- Evidence gate: every proof-based hook cites an approved claim with evidence refs; unproven numbers, testimonials, awards, scarcity, and outcomes are not allowed.
- Specification gate: resolve length and field rules through the current official source IDs in `ads/references/creative-source-registry.md`; return `needs_input` when the source is stale.
- Regulatory gate: route regulated categories, health, finance, employment, and personal-attribute targeting through `ads/references/compliance.md` before publishing.
- Review gate: hooks stay `human_review: pending` inside the creative brief until the owner approves them.

## Psychological angles (use several, never only one)

| Angle | Question the hook answers | Watch-outs |
| --- | --- | --- |
| Pain | Which concrete frustration does the audience already feel? | No fear-mongering, no implied personal attributes |
| Desire | Which outcome do they picture for themselves? | Outcome must be plausible and unguaranteed |
| Curiosity | Which open loop makes the next second worth watching? | Close the loop inside the ad |
| Social proof | Which approved, sourced proof can be shown, not claimed? | Only approved claims with evidence refs |
| Contrarian | Which common belief in the category can be respectfully challenged? | No disparagement of named competitors |
| Specificity | Which concrete detail signals expertise (place, process, moment)? | Details must be true for this brand |
| Time and moment | Which season, life event, or deadline is real for the audience? | Real deadlines only; no artificial urgency |

## Output contract

For each hook record: angle, target persona, platform and placement, primary text, an A/B variant, the intended follow-on line, and the approved claim or evidence ref it relies on (or `none`). Group hooks by angle; keep video hooks in spoken and on-screen variants. Store the set as `hypotheses[].hook` inside the creative brief so the copy deck and scripts reference the same IDs.

## Do not

- Do not invent statistics, review counts, awards, prices, or availability.
- Do not manufacture urgency or scarcity that the offer does not have.
- Do not imply sensitive personal attributes or target them.
- Do not copy competitor phrasing or trademarked lines.
- Do not present a hook as tested; every hook enters an experiment plan via `ads-test`.
