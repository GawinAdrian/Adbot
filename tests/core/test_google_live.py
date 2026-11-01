from __future__ import annotations

import json
from pathlib import Path

import pytest

from claude_ads_core.adapters import (
    GoogleAdsLiveReadAdapter,
    GoogleLiveReadError,
    MutationDisabledError,
    NativeCSVExportAdapter,
    NativeExportError,
    SUPPORTED_LIVE_QUERIES,
    flatten_gaql_row,
)
from claude_ads_core.adapters.mappings_v1 import PROFILES
from claude_ads_core.contracts import validate_contract

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "live_reads" / "google-campaign-daily.json"
CUSTOMER = "1234567890"


def _envelope() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _write(tmp_path: Path, envelope: dict, name: str = "response.json") -> Path:
    target = tmp_path / name
    target.write_text(json.dumps(envelope), encoding="utf-8")
    return target


def test_fixture_normalizes_to_a_valid_account_snapshot_with_lineage():
    adapter = GoogleAdsLiveReadAdapter(CUSTOMER)
    snapshot = adapter.read_snapshot(FIXTURE)
    validate_contract("account-snapshot", snapshot)
    assert snapshot["account"] == {"platform": "google", "account_id": CUSTOMER, "name": "Sanitized Live Demo"}
    assert snapshot["currency"] == "EUR"
    assert snapshot["window"] == {"start": "2026-08-01", "end": "2026-08-02"}
    assert snapshot["spend"] == 60.0
    assert snapshot["campaigns"] == [
        {"campaign_id": "222000111", "name": "Sanitized PMax Campaign", "status": "enabled", "spend": 60.0}
    ]
    lineage = adapter.lineage()
    assert lineage["profile_id"] == PROFILES["google"].profile_id
    assert lineage["query_id"] == "campaign-daily-v1"
    assert lineage["row_count"] == 2
    assert lineage["login_customer_id"] == "1122334455"
    assert "query" not in lineage


def test_nested_and_flat_rows_project_identically():
    envelope = _envelope()
    nested, flat = envelope["rows"]
    assert flatten_gaql_row(nested)["metrics.cost_micros"] == "28750000"
    assert flatten_gaql_row(nested)["campaign.advertising_channel_type"] == "PERFORMANCE_MAX"
    assert set(flatten_gaql_row(nested)) == set(flatten_gaql_row(flat))


def test_supported_queries_only_reference_fixture_verified_profiles():
    for platform in SUPPORTED_LIVE_QUERIES.values():
        assert PROFILES[platform].status == "fixture-verified"


def test_capabilities_are_live_read_only_and_mutations_stay_disabled():
    adapter = GoogleAdsLiveReadAdapter(CUSTOMER)
    caps = adapter.discover_capabilities()
    assert caps.writes_enabled is False
    modes = {cap.capability_id: (cap.mode, cap.status) for cap in caps.capabilities}
    assert modes["live-read-normalization"] == ("live-read", "fixture-verified")
    assert modes["account-mutation"] == ("live-write", "disabled")
    with pytest.raises(MutationDisabledError):
        adapter.draft_changes([{"campaign_id": "222000111", "status": "paused"}])
    with pytest.raises(GoogleLiveReadError):
        adapter.lineage()


@pytest.mark.parametrize(
    "mutate, message",
    [
        (lambda e: e.__setitem__("rows", []), "non-empty"),
        (lambda e: e.__setitem__("query_id", "search-terms-v1"), "no fixture-verified projection"),
        (lambda e: e.__setitem__("platform", "meta"), "platform must be 'google'"),
        (lambda e: e.__setitem__("customer_id", "9999999999"), "does not match the adapter"),
        (lambda e: e["rows"][1].__setitem__("customer.id", "9999999999"), "does not match requested customer_id"),
        (lambda e: e.__setitem__("retrieved_at", "2026-08-27T09:15:00"), "timezone offset"),
        (lambda e: e.__setitem__("api_version", "21"), "api_version"),
        (lambda e: e.__setitem__("extra", 1), "unsupported field"),
        (lambda e: e["rows"][0]["metrics"].__setitem__("costMicros", None), "null"),
        (lambda e: e["rows"][1].pop("metrics.conversions"), "metrics.conversions must not be empty"),
        (lambda e: [(r.pop("metrics", None), r.pop("metrics.cost_micros", None), r.pop("metrics.conversions", None)) for r in e["rows"]], "missing profile column"),
    ],
)
def test_contract_violations_fail_closed(tmp_path: Path, mutate, message: str):
    envelope = _envelope()
    mutate(envelope)
    with pytest.raises(GoogleLiveReadError, match=message):
        GoogleAdsLiveReadAdapter(CUSTOMER).read_snapshot(_write(tmp_path, envelope))


def test_video_campaigns_are_rejected_by_the_google_profile_guard(tmp_path: Path):
    envelope = _envelope()
    envelope["rows"][0]["campaign"]["advertisingChannelType"] = "VIDEO"
    with pytest.raises(GoogleLiveReadError, match="different platform profile"):
        GoogleAdsLiveReadAdapter(CUSTOMER).read_snapshot(_write(tmp_path, envelope))


def test_customer_id_must_be_ten_digits():
    with pytest.raises(GoogleLiveReadError):
        GoogleAdsLiveReadAdapter("123-456-7890")


def test_native_adapter_snapshot_from_rows_rejects_empty_input():
    with pytest.raises(NativeExportError, match="at least one data row"):
        NativeCSVExportAdapter("google").snapshot_from_rows([])
