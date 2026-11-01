# GAQL query library for live reads

**Verified:** 2026-08-27
**Refresh due:** 2026-09-26
**Scope:** read-only queries for the official Google Ads MCP `search` tool; not a field catalog
**Sources:** `google-ads-mcp-official`, `google-ads-campaign-fields-official`

Every query below records its resource, grain, and the deduplication rule that
keeps totals honest. Bind the customer ID and an explicit date window before
calling. Validate selected fields against the current field reference for the
API version in use ([campaign fields](https://developers.google.com/google-ads/api/fields/latest/campaign));
`INVALID_ARGUMENT` or `UNRECOGNIZED_FIELD` is `needs_input`, never an empty dataset.
See `gaql-notes.md` for compatibility discovery and `mcp-integration.md` for the
approval boundary: reads are the only operations these queries perform.

## Response envelope

Store each response as `{schema_version, platform, customer_id, login_customer_id,
api_version, query_id, query, retrieved_at, rows}` and normalize it with
`GoogleAdsLiveReadAdapter`. Only `query_id` values listed as *profile-verified*
project onto a native profile; the others are evidence for findings and stay raw.

## Account discovery

| id | tool | purpose |
| --- | --- | --- |
| `accessible-customers` | `list_accessible_customers` | Enumerate customer IDs the login can reach; expected: the manager plus its client accounts. |

```sql
-- customer-clients-v1 (from the manager account): map client IDs to names
SELECT customer_client.id, customer_client.descriptive_name, customer_client.status,
       customer_client.manager, customer_client.currency_code, customer_client.time_zone
FROM customer_client
WHERE customer_client.level <= 1
```

## `campaign-daily-v1` — profile-verified (`google-ads-api-campaign-daily-v1`)

Grain: one row per campaign per day. Dedup: `(campaign.id, segments.date)` must be unique; the
adapter rejects duplicates. VIDEO campaigns are routed to the YouTube profile and rejected here.

```sql
SELECT segments.date, customer.id, customer.descriptive_name, customer.currency_code,
       campaign.id, campaign.name, campaign.status, campaign.advertising_channel_type,
       campaign_budget.amount_micros, metrics.cost_micros, metrics.conversions
FROM campaign
WHERE segments.date BETWEEN '{start}' AND '{end}'
  AND campaign.status IN ('ENABLED', 'PAUSED')
  AND campaign.advertising_channel_type != 'VIDEO'
```

## Evidence queries (raw, not profile-projected)

```sql
-- budget-pacing-v1: budget-limited campaigns and delivery status
SELECT campaign.id, campaign.name, campaign.status, campaign.bidding_strategy_type,
       campaign_budget.amount_micros, campaign_budget.delivery_method,
       campaign_budget.recommended_budget_amount_micros,
       metrics.cost_micros, metrics.search_budget_lost_impression_share,
       metrics.search_impression_share
FROM campaign
WHERE segments.date DURING LAST_30_DAYS AND campaign.status = 'ENABLED'
```

```sql
-- search-terms-v1: evidence for negative-keyword review (never generate negatives without it)
SELECT campaign.id, ad_group.id, search_term_view.search_term, search_term_view.status,
       segments.keyword.info.match_type, metrics.impressions, metrics.clicks,
       metrics.cost_micros, metrics.conversions
FROM search_term_view
WHERE segments.date DURING LAST_30_DAYS
ORDER BY metrics.cost_micros DESC
LIMIT 500
```

```sql
-- pmax-asset-groups-v1: Performance Max structure and asset-group strength
SELECT campaign.id, asset_group.id, asset_group.name, asset_group.status,
       asset_group.ad_strength, asset_group.final_urls
FROM asset_group
WHERE campaign.advertising_channel_type = 'PERFORMANCE_MAX'
```

```sql
-- conversion-actions-v1: measurement inventory
SELECT conversion_action.id, conversion_action.name, conversion_action.type,
       conversion_action.category, conversion_action.status,
       conversion_action.primary_for_goal, conversion_action.counting_type,
       conversion_action.attribution_model_settings.attribution_model
FROM conversion_action
WHERE conversion_action.status = 'ENABLED'
```

```sql
-- recommendations-v1: platform recommendations as observations, not instructions
SELECT recommendation.type, recommendation.campaign, recommendation.resource_name
FROM recommendation
```

```sql
-- keyword-daily-v1: dedupe by (ad_group.id, keyword text, match type) before totals
SELECT segments.date, ad_group.id, ad_group_criterion.criterion_id,
       ad_group_criterion.keyword.text, ad_group_criterion.keyword.match_type,
       ad_group_criterion.quality_info.quality_score,
       metrics.impressions, metrics.clicks, metrics.cost_micros, metrics.conversions
FROM keyword_view
WHERE segments.date DURING LAST_30_DAYS AND ad_group_criterion.status = 'ENABLED'
```

## Rules

- Prefer explicit `BETWEEN` dates over date constants when the window must be reproducible.
- Record `api_version`, `customer_id`, `login_customer_id`, and `retrieved_at` with every response.
- Micros divide by 1,000,000 in the account currency; `metrics.conversions` follows the account's
  conversion settings, so label it `google_ads_conversions_metric`, never a cross-platform total.
- Manager-account queries need `login-customer-id`; metrics for a client are read from the client ID.
- Redact search terms and personal data before any artifact leaves the run directory.

## Daily watcher queries (Adbot, added 2026-11-01)

Used by `scripts/run_daily_watch.py` through `scripts/gaql_via_api.py` (read-only, `SearchStream`).

| Query ID | Resource | Fields | Conditions |
|---|---|---|---|
| `campaign-daily-v1` | `campaign` | `segments.date`, `customer.id`, `customer.currency_code`, `campaign.id`, `campaign.name`, `campaign.status`, `campaign_budget.amount_micros`, `metrics.cost_micros`, `metrics.clicks`, `metrics.impressions`, `metrics.conversions` | `segments.date BETWEEN <14 days ago> AND <yesterday>` |
| `ad-policy-v1` | `ad_group_ad` | `customer.id`, `campaign.id`, `ad_group_ad.status`, `ad_group_ad.policy_summary.approval_status` | `campaign.status = 'ENABLED'`, `ad_group.status = 'ENABLED'`, `ad_group_ad.status = 'ENABLED'` |

Only ads that can be shown are read, so removed or paused ads cannot keep a traffic light red. Rows exist only for days with
delivery; the watcher treats a missing day as zero delivery. Field existence of `approval_status` is recorded in CLM-0227
(not yet observed on a real disapproved ad). A pull with no rows exits with code 3.
