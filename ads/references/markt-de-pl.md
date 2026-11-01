# Markets: Germany and Poland (Adbot)

Retrieved: 2026-11-01 · Refresh due: 2026-12-01

## Language and geo constants (confirmed by live API, 2026-11-01)

Source: read-only GAQL on `language_constant` and `geo_target_constant` (API v26) through
`scripts/gaql_via_api.py`; ledger claim CLM-0222. Re-check with the same queries when the
API version changes.

| Item | Code | ID | Resource name |
|---|---|---|---|
| German (language) | `de` | 1001 | `languageConstants/1001` |
| Polish (language) | `pl` | 1030 | `languageConstants/1030` |
| Germany (country) | `DE` | 2276 | `geoTargetConstants/2276` |
| Poland (country) | `PL` | 2616 | `geoTargetConstants/2616` |

Re-check queries:

```sql
SELECT language_constant.id, language_constant.code, language_constant.name
FROM language_constant WHERE language_constant.code IN ('de', 'pl')

SELECT geo_target_constant.id, geo_target_constant.name, geo_target_constant.country_code,
       geo_target_constant.target_type
FROM geo_target_constant
WHERE geo_target_constant.country_code IN ('DE', 'PL') AND geo_target_constant.target_type = 'Country'
```

## Currency and time zone

Defaults per country (`EUR` / `Europe/Berlin`, `PLN` / `Europe/Warsaw`) are conventions; the account's
own currency and time zone are authoritative and must be read from the account, never assumed.

## Legal and policy notes

Status 2026-11-01: **not researched, no legal statements are made.** The assistant never says what the law
requires. It may only list *topics to clarify with a qualified advisor*, as questions, without answers:

- Which imprint, privacy, and consent information must the landing page show for this business and country?
- Is a cookie or tracking consent needed before conversion measurement runs on the site?
- Is the offer in a regulated category with special advertising rules (health, finance, legal, housing, employment)?
- If the account belongs to someone else, is a data-processing agreement needed before account data reaches Google or Claude?

Add rules here only with an official source (law text, regulator, or Google policy page), retrieval date, and a
ledger claim (`control-plane/manifests/claim-ledger.json`).
