# Markets: Germany and Poland (Adbot)

Retrieved: 2026-11-01 · Refresh due: 2026-12-01

## Language constants (confirmed)

Source: Google Ads API "Codes and formats" (language table).

| Language | Code | Criterion ID | Resource name |
|---|---|---|---|
| German | `de` | 1001 | `languageConstants/1001` |
| Polish | `pl` | 1030 | `languageConstants/1030` |

## Geo target constants (not confirmed from documentation)

The country rows could not be read from the documentation page in this refresh. The repository
used `2276` (Germany) in an earlier keyword run, but that is **not** a documentation check.
`2616` for Poland is **unconfirmed** and must not be shown to users as fact.

Resolve at runtime with a read-only query and store the result with date and API version:

```sql
SELECT geo_target_constant.id, geo_target_constant.name, geo_target_constant.country_code,
       geo_target_constant.target_type
FROM geo_target_constant
WHERE geo_target_constant.country_code IN ('DE', 'PL') AND geo_target_constant.target_type = 'Country'
```

(Verify the field names against the current API version before use.)

## Currency and time zone

Defaults per country (`EUR` / `Europe/Berlin`, `PLN` / `Europe/Warsaw`) are conventions; the account's
own currency and time zone are authoritative and must be read from the account, never assumed.

## Legal and policy notes

Not yet researched (PRP step 6): imprint, privacy, advertising rules in Germany and Poland.
Until sourced, the assistant gives no legal statements beyond "check with a qualified advisor".
