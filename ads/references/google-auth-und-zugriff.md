# Google Ads access and authentication (Adbot)

Retrieved: 2026-11-01 · Refresh due: 2026-12-01 (API and policy sources: 30 days)
Confidence: high for items marked *confirmed*; items marked *unconfirmed* must not be
stated to users as fact.

## Findings

| # | Finding | Status | Source |
|---|---|---|---|
| 1 | Developer tokens were sunset on 2026-09-09. API access levels are tied to the Google Cloud project that issued the OAuth credentials. | confirmed | Google Ads API, "Developer token" and "Access levels and permissible use" (both last updated 2026-10-30) |
| 2 | A developer-token header may still be sent; it is optional and ignored. Future major API versions are expected to reject it. | confirmed | "Developer token" |
| 3 | The official Google Ads MCP server no longer requires `GOOGLE_ADS_DEVELOPER_TOKEN`. Required: `GOOGLE_PROJECT_ID`, and ADC via `GOOGLE_APPLICATION_CREDENTIALS` or `gcloud auth application-default login`. `GOOGLE_ADS_LOGIN_CUSTOMER_ID` is optional (manager-account access). Tools: `list_accessible_customers`, `search` (GAQL), `get_resource_metadata`; read-only. | confirmed (documentation) · **not yet tested in this repo** | "Google Ads MCP server: Developer integration guide" (2026-10-30) |
| 4 | Access levels: Test; Explorer (test and production, 2,880 operations/day on production); Basic (15,000/day, brand verification prerequisite); Standard (unlimited, manual audit). Google usually upgrades Explorer applications automatically. | confirmed | "Access levels and permissible use"; "Create a Google Cloud project" |
| 5 | Explorer cannot use planning services (KeywordPlan services, AudienceInsightsService, ReachPlanService), account creation, user management, or billing services. Keyword ideas via API therefore need Basic. | confirmed | "Access levels and permissible use" |
| 6 | Permissible use and Required Minimum Functionality apply to projects with Standard access. Providing a tool to clients requires an update application and demo sign-in. | confirmed | same page |
| 7 | Users review and revoke app access at their Google Account permissions page. | confirmed | "OAuth overview" (2026-10-30) |
| 8 | OAuth consent screen in status "Testing": refresh tokens expire after 7 days. Admin session policies can force re-authentication after 1–24 hours (`invalid_grant`). | confirmed | "Using OAuth 2.0 to access Google APIs" (2026-10-29) |
| 9 | The OAuth overview page still says "A developer token is required in addition to OAuth credentials", which contradicts findings 1–3. | **contradiction, unresolved** | "OAuth overview" |
| 10 | The scope string for the Google Ads API is `https://www.googleapis.com/auth/adwords` (used in the runbook; not re-read on the pages above). | unconfirmed in this refresh | existing runbook |

## Consequences for Adbot

- Every user works with **their own Google Cloud project and Google account**. No shared OAuth
  client is provided; otherwise the provider becomes a tool provider (finding 6).
- Scripts must treat the developer token as **optional** and must not abort without it.
- Consent screen: if the user's project stays in "Testing", expect weekly re-login (finding 8).
  The user guide must state this and explain `adbot doctor` output for `invalid_grant`.
- Keyword ideas by API need Basic access; fallback is a Keyword Planner CSV export.

## Open checks (owner: step 3 and 5 of the PRP)

1. Start the MCP server without a developer token against a real account and record the result here.
2. Re-read the user-authentication page for the exact scope and desktop-client steps (finding 10).
3. Resolve finding 9 by testing, not by assuming.
