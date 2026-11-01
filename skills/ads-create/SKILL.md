---
name: ads-create
description: "Create source-grounded paid-ad campaign concepts, messaging, copy, creative briefs, and production plans from a validated brand profile, campaign objective, platform requirements, and optional audit evidence. Triggers on: campaign brief, campaign concepts, create a campaign, ad concepts, ad copy, ad messaging, creative brief, headlines, descriptions."
---

# Campaign Concepts and Copy

1. Load the validated setup/brand profile, objective, audience, offer, proof,
   platform/placement requirements, policy context, and optional audit findings.
2. Separate factual claims, operator-approved claims, and creative hypotheses.
3. Generate materially distinct strategic concepts, not cosmetic rewrites.
4. For each concept, define insight, promise, proof, hook, narrative, CTA, objections,
   platform adaptations, destination, and experiment hypothesis.
5. Validate copy limits and policy against current platform references. Load only
   the active files among `ads/references/google-creative-specs.md`,
   `meta-creative-specs.md`, `youtube-creative-specs.md`,
   `linkedin-creative-specs.md`, `tiktok-creative-specs.md`, and
   `microsoft-creative-specs.md`; use the dated source ledger for every current
   specification claim.
6. Return a versioned creative brief and copy deck inside the run directory.
7. For hooks, personas, funnel roles, video scripts, and shoot planning load only the
   needed asset from `assets/` (`hooks.md`, `personas.md`, `funnel-stages.md`,
   `video-scripts.md`, `shoot-planning.md`). They are qualitative aids; limits and
   formats still resolve through current specification source IDs.
8. When the operator wants a campaign draft without a live write path, hand the
   approved copy deck to `claude_ads_core.editor_export` to produce a paused
   Google Ads Editor import CSV (`docs/runbooks/editor-csv-import.md`). Campaign
   negatives are only accepted with an evidence reference (search terms report or
   equivalent review), never from generic lists.

Do not invent testimonials, certifications, scarcity, prices, outcomes, or regulated
claims. Human review remains required before production or launch.
