from __future__ import annotations

import json
from pathlib import Path

import pytest

from claude_ads_core.adapters import (
    GoogleKeywordIdeasAdapter,
    GoogleKeywordIdeasError,
    MutationDisabledError,
)
from claude_ads_core.contracts import CONTRACT_NAMES, schema_path, validate_contract

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "live_reads" / "google-keyword-ideas.json"
CUSTOMER = "1234567890"


def _envelope() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _write(tmp_path: Path, envelope: dict, name: str = "response.json") -> Path:
    target = tmp_path / name
    target.write_text(json.dumps(envelope), encoding="utf-8")
    return target


def test_fixture_normalizes_to_a_valid_contract_with_lineage():
    adapter = GoogleKeywordIdeasAdapter(CUSTOMER)
    result = adapter.read_ideas(FIXTURE)
    validate_contract("keyword-ideas", result)
    assert result["customer_id"] == CUSTOMER
    assert result["api_version"] == "v25"
    assert [idea["text"] for idea in result["ideas"]] == [
        "beispiel dienstleistung",
        "beispiel dienstleistung anbieter",
        "beispiel dienstleistung kosten",
        "beispiel dienstleistung mittelstand",
    ]
    assert result["ideas"][0]["avg_monthly_searches"] == 1300
    assert result["ideas"][0]["close_variants"] == ["beispieldienstleistung"]
    assert result["ideas"][3]["avg_monthly_searches"] is None
    assert result["ideas"][3]["competition"] == "UNKNOWN"
    lineage = adapter.lineage()
    assert lineage["adapter_id"] == "google-ads-keyword-ideas-v1"
    assert lineage["idea_count"] == 4
    assert lineage["seed_keyword_count"] == 2
    assert lineage["geo_target_count"] == 1
    assert lineage["query_id"] == "sanitized-service-cluster-v1"
    assert "keywords" not in lineage and "seed" not in lineage


def test_rest_shaped_envelope_projects_identically(tmp_path: Path):
    """camelCase keys, nested keywordIdeaMetrics, string int64s, omitted optionals."""
    envelope = _envelope()
    rest_ideas = []
    for idea in envelope["ideas"]:
        metrics: dict = {}
        if idea["avg_monthly_searches"] is not None:
            metrics["avgMonthlySearches"] = str(idea["avg_monthly_searches"])
        if idea["competition"] != "UNSPECIFIED":
            metrics["competition"] = idea["competition"]
        if idea["competition_index"] is not None:
            metrics["competitionIndex"] = str(idea["competition_index"])
        if idea["low_top_of_page_bid_micros"] is not None:
            metrics["lowTopOfPageBidMicros"] = str(idea["low_top_of_page_bid_micros"])
        if idea["high_top_of_page_bid_micros"] is not None:
            metrics["highTopOfPageBidMicros"] = str(idea["high_top_of_page_bid_micros"])
        rest_idea: dict = {"text": idea["text"], "keywordIdeaMetrics": metrics}
        if idea["close_variants"]:
            rest_idea["closeVariants"] = idea["close_variants"]
        rest_ideas.append(rest_idea)
    envelope["ideas"] = rest_ideas
    # The UNKNOWN competition of the last idea is presence-relevant: keep it explicit.
    rest_ideas[3]["keywordIdeaMetrics"]["competition"] = "UNKNOWN"
    expected = GoogleKeywordIdeasAdapter(CUSTOMER).read_ideas(FIXTURE)
    result = GoogleKeywordIdeasAdapter(CUSTOMER).read_ideas(_write(tmp_path, envelope))
    assert result == expected


def test_capabilities_are_read_only_and_mutations_stay_disabled():
    adapter = GoogleKeywordIdeasAdapter(CUSTOMER)
    caps = adapter.discover_capabilities()
    assert caps.writes_enabled is False
    modes = {cap.capability_id: (cap.mode, cap.status) for cap in caps.capabilities}
    assert modes["keyword-ideas-normalization"] == ("live-read", "fixture-verified")
    assert modes["account-mutation"] == ("live-write", "disabled")
    with pytest.raises(MutationDisabledError):
        adapter.apply_changes({})
    with pytest.raises(GoogleKeywordIdeasError, match="use read_ideas"):
        adapter.read_snapshot(FIXTURE)
    with pytest.raises(GoogleKeywordIdeasError, match="no response has been read"):
        adapter.lineage()


def test_customer_id_must_be_ten_digits():
    with pytest.raises(GoogleKeywordIdeasError):
        GoogleKeywordIdeasAdapter("123-456-7890")


@pytest.mark.parametrize(
    "mutate, message",
    [
        (lambda e: e.pop("seed"), "missing field"),
        (lambda e: e.__setitem__("extra", 1), "unsupported field"),
        (lambda e: e.__setitem__("platform", "meta"), "platform must be 'google'"),
        (lambda e: e.__setitem__("artifact_type", "media-plan"), "artifact_type"),
        (lambda e: e.__setitem__("customer_id", "9999999999"), "does not match the adapter"),
        (lambda e: e.__setitem__("login_customer_id", "112-233-4455"), "login_customer_id"),
        (lambda e: e.__setitem__("api_version", "25"), "api_version"),
        (lambda e: e.__setitem__("retrieved_at", "2026-09-01T08:29:57"), "timezone offset"),
        (lambda e: e.__setitem__("ideas", []), "non-empty"),
        (lambda e: e["seed"].__setitem__("keywords", "not-a-list"), "seed.keywords must be an array"),
        (lambda e: e["ideas"][0].pop("text"), "missing the required field 'text'"),
        (lambda e: e["ideas"][0].__setitem__("monthlySearchVolumes", []), "unsupported field"),
        (lambda e: e["ideas"][0].__setitem__("avg_monthly_searches", 12.5), "integer"),
        (lambda e: e["ideas"][0].__setitem__("avg_monthly_searches", "12.5"), "digit string"),
        (lambda e: e["ideas"][0].__setitem__("competition", "FIERCE"), "competition"),
        (lambda e: e["ideas"][0].__setitem__("competition_index", 250), "<= 100"),
        (lambda e: e["ideas"][1].__setitem__("text", "beispiel dienstleistung"), "must be unique"),
        (
            lambda e: e["ideas"][0].update(
                {"low_top_of_page_bid_micros": 900, "high_top_of_page_bid_micros": 800}
            ),
            "high_top_of_page_bid_micros",
        ),
        (
            lambda e: e["ideas"][0].__setitem__(
                "keyword_idea_metrics", {"avg_monthly_searches": 5}
            ),
            "repeats the field",
        ),
        (
            lambda e: (e["seed"].__setitem__("keywords", []), e["seed"].__setitem__("url", None)),
            "keywords, a url, or both",
        ),
    ],
)
def test_contract_violations_fail_closed(tmp_path: Path, mutate, message: str):
    envelope = _envelope()
    mutate(envelope)
    with pytest.raises(GoogleKeywordIdeasError, match=message):
        GoogleKeywordIdeasAdapter(CUSTOMER).read_ideas(_write(tmp_path, envelope))


def test_contract_is_registered_with_a_packaged_schema():
    assert "keyword-ideas" in CONTRACT_NAMES
    schema = json.loads(schema_path("keyword-ideas").read_text(encoding="utf-8"))
    assert schema["$id"] == "urn:ai-marketing-hub:claude-ads:schema:core:v1:keyword-ideas.schema.json"
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == set(schema["properties"])
