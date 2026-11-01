"""Deterministic daily watcher: rules over stored live-read envelopes, no AI, no network.

The watcher reads campaign-by-day rows that ``scripts/gaql_via_api.py`` (or the MCP helper) stored as a
live-read envelope, applies a small set of transparent rules, and returns a :class:`WatchResult` with
a traffic light.  It never contacts Google and never writes to an account.

Principles (see ``ads/references/kadenz-und-regeln.md``):

* Thresholds are Adbot starting values, not platform facts; they are named constants below.
* Small denominators never raise an alarm: with too few clicks the answer is "not enough data".
* A day without a row counts as zero delivery; a missing input is reported, never guessed.
* Output ordering is deterministic so reruns on the same input are byte-identical.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from .adapters.google_live import GoogleAdsLiveReadAdapter, flatten_gaql_row
from .i18n import Translator
from .workflow_contracts import validate_workflow_contract

# ---- Adbot starting values (adjustable decisions, documented in kadenz-und-regeln.md) -------------
PACING_WINDOW_DAYS = 3          # consecutive recent days used for pacing and delivery
PACING_CAPPED_RATIO = 0.90      # cost >= 90 % of the daily budget on every recent day: budget-limited
PACING_UNDER_RATIO = 0.20       # cost <= 20 % of the daily budget on every recent day: delivers very little
PACING_OVER_RATIO = 1.50        # one day above 150 % of the daily budget: unusually high
CONVERSION_WINDOW_DAYS = 7      # compare the last 7 days with the 7 days before
MIN_CLICKS_FOR_CONVERSION_RULES = 30
MIN_CLICKS_FOR_NO_CONVERSION = 50
DATA_GAP_DAYS = 2               # newest data older than this many days is a data gap
STATUS_RANK = {"normal": 0, "unknown": 1, "warning": 2, "critical": 3}
REQUIRED_FIELDS = (
    "segments.date", "campaign.id", "campaign.name", "campaign.status",
    "campaign_budget.amount_micros", "metrics.cost_micros", "metrics.clicks",
    "metrics.impressions", "metrics.conversions", "customer.currency_code",
)


class WatchError(ValueError):
    """Raised when watcher input is malformed; fails loudly instead of returning a quiet result."""


@dataclass(frozen=True)
class WatchCheck:
    """One rule outcome for one campaign (or the account when ``campaign_id`` is None)."""

    rule: str
    state: str
    status: str
    campaign_id: str | None = None
    campaign_name: str | None = None
    params: Mapping[str, Any] = field(default_factory=dict)

    def message_key(self) -> str:
        return f"watch.{self.rule}.{self.state}"

    def hint_key(self) -> str:
        return f"watch.{self.rule}.{self.state}.hint"


@dataclass(frozen=True)
class WatchResult:
    """Outcome of one watcher run."""

    ampel: str
    checks: tuple[WatchCheck, ...]
    window_start: str | None
    window_end: str | None
    as_of: str
    currency: str
    missing_inputs: tuple[str, ...]
    query_id: str
    summary: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0.0",
            "artifact_type": "watch-result",
            "ampel": self.ampel,
            "as_of": self.as_of,
            "window": {"start": self.window_start, "end": self.window_end},
            "currency": self.currency,
            "query_id": self.query_id,
            "summary": dict(self.summary),
            "missing_inputs": list(self.missing_inputs),
            "checks": [
                {"rule": c.rule, "state": c.state, "status": c.status, "campaign_id": c.campaign_id,
                 "campaign_name": c.campaign_name, "params": dict(c.params)}
                for c in self.checks
            ],
        }


def _num(row: Mapping[str, str], key: str) -> float:
    try:
        return float(row[key])
    except (KeyError, ValueError) as exc:
        raise WatchError(f"row has no numeric {key}") from exc


def load_rows(envelope_path: str | Path, customer_id: str) -> tuple[list[dict[str, str]], dict[str, Any]]:
    """Load and flatten a stored envelope; validation is delegated to the live-read adapter rules."""
    adapter = GoogleAdsLiveReadAdapter(customer_id)
    envelope = adapter._load_envelope(Path(envelope_path))  # noqa: SLF001 - same-package reuse of the strict loader
    rows = [adapter._flatten_checked(row, index) for index, row in enumerate(envelope["rows"])]  # noqa: SLF001
    for index, row in enumerate(rows):
        for key in REQUIRED_FIELDS:
            if key not in row:
                raise WatchError(f"rows[{index}] is missing {key}; the watcher needs {', '.join(REQUIRED_FIELDS)}")
    return rows, envelope


def _day_sum(rows: Sequence[Mapping[str, str]], key: str, start: date, end: date) -> float:
    total = 0.0
    for row in rows:
        day = date.fromisoformat(row["segments.date"])
        if start <= day <= end:
            total += _num(row, key)
    return total


def _period(rows: Sequence[Mapping[str, str]], start: date, end: date) -> dict[str, Any]:
    """Sums over ENABLED and PAUSED campaigns for one period; ratios only with a non-zero denominator."""
    cost = _day_sum(rows, "metrics.cost_micros", start, end) / 1_000_000
    clicks = _day_sum(rows, "metrics.clicks", start, end)
    impressions = _day_sum(rows, "metrics.impressions", start, end)
    conversions = _day_sum(rows, "metrics.conversions", start, end)
    return {
        "start": start.isoformat(), "end": end.isoformat(), "cost": round(cost, 2), "clicks": int(clicks),
        "impressions": int(impressions), "conversions": round(conversions, 2),
        "ctr_percent": round(clicks / impressions * 100, 2) if impressions else None,
        "cpa": round(cost / conversions, 2) if conversions else None,
    }


def _pacing(campaign_rows: Sequence[Mapping[str, str]], last: date, budget: float) -> tuple[str, str, dict[str, Any]]:
    days = [last - timedelta(days=offset) for offset in range(PACING_WINDOW_DAYS)]
    costs = [_day_sum(campaign_rows, "metrics.cost_micros", day, day) / 1_000_000 for day in days]
    params = {"budget": round(budget, 2), "days": PACING_WINDOW_DAYS, "max_cost": round(max(costs), 2)}
    if budget <= 0:
        return "unknown", "unknown", params
    if max(costs) > budget * PACING_OVER_RATIO:
        return "warning", "over", params
    if all(cost >= budget * PACING_CAPPED_RATIO for cost in costs):
        return "warning", "capped", params
    if all(cost <= budget * PACING_UNDER_RATIO for cost in costs):
        return "warning", "under", params
    return "normal", "normal", params


def _delivery(campaign_rows: Sequence[Mapping[str, str]], last: date) -> tuple[str, str, dict[str, Any]]:
    recent_start = last - timedelta(days=PACING_WINDOW_DAYS - 1)
    recent = _day_sum(campaign_rows, "metrics.impressions", recent_start, last)
    earlier = _day_sum(campaign_rows, "metrics.impressions", last - timedelta(days=9), recent_start - timedelta(days=1))
    params = {"days": PACING_WINDOW_DAYS}
    if recent == 0 and earlier > 0:
        return "critical", "stopped", params
    return "normal", "normal", params


def _conversions(campaign_rows: Sequence[Mapping[str, str]], last: date) -> tuple[str, str, dict[str, Any]]:
    span = CONVERSION_WINDOW_DAYS
    recent_start = last - timedelta(days=span - 1)
    prev_end, prev_start = recent_start - timedelta(days=1), recent_start - timedelta(days=span)
    clicks = _day_sum(campaign_rows, "metrics.clicks", recent_start, last)
    conv = _day_sum(campaign_rows, "metrics.conversions", recent_start, last)
    prev_conv = _day_sum(campaign_rows, "metrics.conversions", prev_start, prev_end)
    params = {"clicks": int(clicks), "days": span, "previous": round(prev_conv, 2)}
    if clicks < MIN_CLICKS_FOR_CONVERSION_RULES:
        return "unknown", "insufficient", {**params, "minimum": MIN_CLICKS_FOR_CONVERSION_RULES}
    if conv == 0 and prev_conv >= 1:
        return "critical", "drop", params
    if conv == 0 and prev_conv == 0 and clicks >= MIN_CLICKS_FOR_NO_CONVERSION:
        return "warning", "none", params
    return "normal", "normal", params


def evaluate(
    rows: Sequence[Mapping[str, str]],
    *,
    as_of: date,
    currency: str,
    query_id: str,
    retrieved_at: datetime,
    policy_rows: Sequence[Mapping[str, str]] | None = None,
) -> WatchResult:
    """Apply all rules to *rows* (flattened GAQL rows) and return the result.

    The reference day is the last complete day before the data was retrieved.  Rows exist only for days with
    delivery, so the newest *row* date cannot tell "stopped" apart from "stale data"; the retrieval time can.
    """
    missing: list[str] = []
    checks: list[WatchCheck] = []
    if not rows:
        raise WatchError("no rows supplied; an empty result is needs_input, not a healthy account")
    first = min(date.fromisoformat(row["segments.date"]) for row in rows)
    pulled = retrieved_at.astimezone(timezone.utc).date()
    last = pulled - timedelta(days=1)
    if last < first:
        raise WatchError("the data was retrieved before its own first day; check the stored envelope")
    gap_days = (as_of - pulled).days
    if gap_days > DATA_GAP_DAYS:
        checks.append(WatchCheck("data", "gap", "warning", params={"days": gap_days, "newest": pulled.isoformat()}))
    else:
        checks.append(WatchCheck("data", "normal", "normal", params={"newest": last.isoformat()}))

    campaigns: dict[str, list[Mapping[str, str]]] = {}
    for row in rows:
        campaigns.setdefault(row["campaign.id"], []).append(row)
    ordered = {cid: sorted(items, key=lambda r: r["segments.date"]) for cid, items in campaigns.items()}
    enabled = {cid: items for cid, items in ordered.items() if items[-1]["campaign.status"] == "ENABLED"}
    if not enabled:
        checks.append(WatchCheck("campaigns", "none_enabled", "unknown"))
    for cid in sorted(enabled):
        items = enabled[cid]
        name = items[-1]["campaign.name"]
        budget = _num(items[-1], "campaign_budget.amount_micros") / 1_000_000
        for rule, outcome in (("pacing", _pacing(items, last, budget)), ("delivery", _delivery(items, last)),
                              ("conversions", _conversions(items, last))):
            status, state, params = outcome
            checks.append(WatchCheck(rule, state, status, cid, name, params))

    if policy_rows is None:
        missing.append("ad policy status")
        checks.append(WatchCheck("policy", "unknown", "unknown"))
    else:
        disapproved = sum(1 for row in policy_rows if row.get("ad_group_ad.policy_summary.approval_status") == "DISAPPROVED")
        checks.append(WatchCheck("policy", "disapproved", "critical", params={"count": disapproved}) if disapproved
                      else WatchCheck("policy", "normal", "normal"))
    missing.append("billing and payment status")  # not readable with the supported access; stated, never guessed

    worst = max((STATUS_RANK[c.status] for c in checks), default=0)
    ampel = {3: "red", 2: "yellow"}.get(worst, "green")
    if all(c.status == "unknown" for c in checks):
        ampel = "unknown"
    span = CONVERSION_WINDOW_DAYS
    summary = {
        "days": span,
        "last": _period(rows, last - timedelta(days=span - 1), last),
        "previous": _period(rows, last - timedelta(days=2 * span - 1), last - timedelta(days=span)),
    }
    return WatchResult(ampel, tuple(checks), first.isoformat(), last.isoformat(), as_of.isoformat(), currency,
                       tuple(missing), query_id, summary)


def describe(check: WatchCheck, tr: Translator, currency: str) -> tuple[str, str | None]:
    """Return ``(observation, hint)`` for *check* in the translator's language."""
    params: dict[str, Any] = dict(check.params)
    for key in ("budget", "max_cost"):
        if key in params:
            params[key] = tr.money(float(params[key]), currency)
    for key, value in list(params.items()):
        if key == "newest":
            params[key] = tr.date(str(value))
        elif isinstance(value, bool):
            continue
        elif isinstance(value, int):
            params[key] = tr.number(value, 0)
        elif isinstance(value, float):
            params[key] = tr.number(value, 0 if value == int(value) else 2)
    params["campaign"] = check.campaign_name or ""
    text = tr.t(check.message_key(), **{key: str(value) for key, value in params.items()})
    hint = tr.t(check.hint_key()) if tr.has(check.hint_key()) else None
    return text, hint


def to_monitoring_bundle(
    result: WatchResult,
    *,
    run_id: str,
    created_at: datetime,
    lifecycle: Mapping[str, Any],
    timezone_name: str,
) -> dict[str, Any]:
    """Build a contract-valid ``monitoring-bundle`` (English text) from *result*.

    *lifecycle* is the embedded data-lifecycle object; non-public data requires verified
    encryption evidence, which the caller only has when the user attested disk encryption.
    """
    tr = Translator("en")
    stamp = created_at.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    checkpoints = []
    for index, check in enumerate(result.checks):
        observation, hint = describe(check, tr, result.currency)
        status = check.status
        refs = [] if status == "unknown" else [f"live-read:{result.query_id}:{check.campaign_id or 'account'}:{result.window_start}..{result.window_end}"]
        checkpoints.append({
            "checkpoint_id": f"{check.rule}-{check.campaign_id or 'account'}-{index:02d}",
            "platform": "google",
            "observed_at": stamp,
            "control_id": f"ADBOT-WATCH-{check.rule.upper()}",
            "status": status,
            "evidence_refs": refs,
            "observation": observation,
            "recovery_hint": hint or "No action needed.",
        })
    bundle = {
        "schema_version": "1.0.0",
        "artifact_type": "monitoring-bundle",
        "run_id": run_id,
        "created_at": stamp,
        "window": {"start": result.window_start, "end": result.window_end, "timezone": timezone_name},
        "checkpoints": checkpoints,
        "missing_inputs": list(result.missing_inputs),
        "contradictions": [],
        "completeness": "partial" if result.missing_inputs else "complete",
        "data_lifecycle": dict(lifecycle),
    }
    validate_workflow_contract("monitoring-bundle", bundle)
    return bundle


def attested_lifecycle(attested_on: str, run_id: str, created_at: datetime) -> dict[str, Any]:
    """Data-lifecycle object for a user who confirmed disk encryption on *attested_on* (ISO date)."""
    keep_until = (created_at + timedelta(days=365)).astimezone(timezone.utc).replace(microsecond=0)
    return {
        "schema_version": "1.0.0",
        "lifecycle_id": f"lifecycle-{run_id}",
        "classification": "confidential",
        "retention": {"minimum_seconds": 0, "mode": "operator-defined",
                      "delete_after": keep_until.isoformat().replace("+00:00", "Z"),
                      "purpose": "Show the user how her own Google Ads account is doing", "exception_reason": None},
        "encryption": {"at_rest": "verified", "in_transit": "verified",
                       "evidence_refs": [f"operator-attestation:disk-encryption {attested_on}", "transport:https-only"]},
        "access": {"owner": "account-owner", "authorized_roles": ["account-owner"], "access_log_locator": None},
        "deletion": {"status": "scheduled", "method": "The user deletes the run folder", "verification_required": True,
                     "verification_artifact_locator": None},
        "incident": {"owner": "account-owner", "reporting_channel": "Contact the account owner", "status": "not-triggered",
                     "record_locator": None},
    }


def run_watch(
    envelope: str | Path,
    customer_id: str,
    *,
    as_of: date,
    out_dir: str | Path,
    policy_envelope: str | Path | None = None,
    attested_on: str | None = None,
    timezone_name: str = "UTC",
    now: datetime | None = None,
) -> dict[str, Any]:
    """Read stored envelopes, evaluate, and write results beneath a *new* run directory."""
    rows, meta = load_rows(envelope, customer_id)
    policy = None
    if policy_envelope is not None:
        policy, _ = _load_policy(policy_envelope, customer_id)
    currency = rows[0]["customer.currency_code"]
    retrieved = datetime.fromisoformat(str(meta["retrieved_at"]).replace("Z", "+00:00"))
    result = evaluate(rows, as_of=as_of, currency=currency, query_id=meta["query_id"], retrieved_at=retrieved, policy_rows=policy)
    stamp = (now or datetime.now(timezone.utc)).astimezone(timezone.utc).replace(microsecond=0)
    run_id = f"watch-{stamp:%Y%m%d-%H%M%S}"
    target = Path(out_dir) / run_id
    target.mkdir(parents=True, exist_ok=False)  # never overwrite an earlier run
    written = {"result": str(target / "watch-result.json")}
    (target / "watch-result.json").write_text(json.dumps(result.to_dict(), indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    if attested_on:
        bundle = to_monitoring_bundle(result, run_id=run_id, created_at=stamp,
                                      lifecycle=attested_lifecycle(attested_on, run_id, stamp), timezone_name=timezone_name)
        (target / "monitoring-bundle.json").write_text(json.dumps(bundle, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
        written["bundle"] = str(target / "monitoring-bundle.json")
    return {"run_id": run_id, "ampel": result.ampel, **written, "bundle_written": bool(attested_on)}


def _load_policy(path: str | Path, customer_id: str) -> tuple[list[dict[str, str]], dict[str, Any]]:
    adapter = GoogleAdsLiveReadAdapter(customer_id)
    envelope = adapter._load_envelope(Path(path))  # noqa: SLF001
    return [flatten_gaql_row(row) for row in envelope["rows"]], envelope


def render_watch_text(result: Mapping[str, Any], tr: Translator) -> str:
    """Render a stored ``watch-result`` as plain text in the translator's language."""
    currency = str(result["currency"])
    lines = [tr.t(f"watch.ampel.{result['ampel']}"), ""]
    for item in result["checks"]:
        check = WatchCheck(item["rule"], item["state"], item["status"], item["campaign_id"], item["campaign_name"], item["params"])
        text, hint = describe(check, tr, currency)
        lines.append(f"[{tr.label('check_status', check.status)}] {text}")
        if hint and check.status != "normal":
            lines.append(f"    → {hint}")
    for missing in result["missing_inputs"]:
        key = {"ad policy status": "watch.missing.policy", "billing and payment status": "watch.missing.billing"}.get(missing)
        lines.append(f"[{tr.label('check_status', 'unknown')}] {tr.t(key) if key else missing}")
    return "\n".join(lines) + "\n"
