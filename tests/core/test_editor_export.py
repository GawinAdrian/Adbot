from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from claude_ads_core.editor_export import (
    COLUMNS,
    EditorAdGroup,
    EditorCampaign,
    EditorExportError,
    EditorKeyword,
    EditorNegativeKeyword,
    EditorResponsiveSearchAd,
    build_editor_rows,
    render_editor_csv,
    write_editor_csv,
)

GOLDEN = Path(__file__).resolve().parents[1] / "fixtures" / "editor" / "google-editor-draft.csv"


def _draft() -> EditorCampaign:
    ad = EditorResponsiveSearchAd(
        headlines=("Sanitized Headline One", "Sanitized Headline Two", "Sanitized Headline Three"),
        descriptions=("Sanitized description one.", "Sanitized description two."),
        final_url="https://example.invalid/service",
        path1="service",
    )
    group = EditorAdGroup(
        name="Sanitized Ad Group",
        keywords=(
            EditorKeyword("sanitized service city", "Phrase"),
            EditorKeyword("sanitized service", "Exact", final_url="https://example.invalid/service"),
        ),
        ads=(ad,),
        max_cpc="1.50",
    )
    return EditorCampaign(
        name="Sanitized Search Campaign",
        daily_budget="10",
        ad_groups=(group,),
        bid_strategy_type="Maximize clicks",
        languages=("German",),
        locations=("Sanitized City",),
    )


def test_rows_follow_editor_column_contract_and_stay_paused():
    rows = build_editor_rows([_draft()])
    assert [row["Campaign"] for row in rows] == ["Sanitized Search Campaign"] * 5
    assert rows[0]["Campaign status"] == "Paused"
    assert rows[0]["Campaign daily budget"] == "10.00"
    assert rows[1]["Ad group"] == "Sanitized Ad Group" and rows[1]["Max CPC"] == "1.50"
    assert rows[2]["Keyword"] == "sanitized service city" and rows[2]["Match type"] == "Phrase"
    assert rows[4]["Headline 3"] == "Sanitized Headline Three" and rows[4]["Headline 4"] == ""
    assert all(set(row) == set(COLUMNS) for row in rows)


def test_rendered_csv_matches_golden_fixture():
    assert render_editor_csv([_draft()]) == GOLDEN.read_text(encoding="utf-8", newline="")


def test_write_adds_bom_and_refuses_overwrite(tmp_path: Path):
    target = tmp_path / "draft.csv"
    write_editor_csv([_draft()], target)
    assert target.read_bytes().startswith(b"\xef\xbb\xbf")
    with pytest.raises(EditorExportError, match="refusing to overwrite"):
        write_editor_csv([_draft()], target)
    with pytest.raises(EditorExportError, match="end with .csv"):
        write_editor_csv([_draft()], tmp_path / "draft.txt")


@pytest.mark.parametrize(
    "mutate, message",
    [
        (lambda c: replace(c, status="Enabled"), "must be exported Paused"),
        (lambda c: replace(c, bid_strategy_type="Enhanced CPC"), "bid_strategy_type"),
        (lambda c: replace(c, locations=()), "at least one language and one location"),
        (lambda c: replace(c, daily_budget="0"), "positive finite amount"),
        (lambda c: replace(c, ad_groups=(c.ad_groups[0], c.ad_groups[0])), "duplicate ad group"),
        (
            lambda c: replace(c, ad_groups=(replace(c.ad_groups[0], keywords=(EditorKeyword("x", "Negative"),)),)),
            "use EditorCampaign.negative_keywords",
        ),
        (lambda c: replace(c, negative_keywords=(EditorNegativeKeyword("jobs", "Broad", ""),)), "no evidence_ref"),
        (lambda c: replace(c, negative_keywords=(EditorNegativeKeyword("jobs", "Negative", "evidence:x"),)), "match_type must be one of"),
        (lambda c: replace(c, negative_keywords=(EditorNegativeKeyword('"jobs"', "Phrase", "evidence:x"),)), "must be plain text"),
        (
            lambda c: replace(c, negative_keywords=(EditorNegativeKeyword("jobs", "Phrase", "evidence:x"), EditorNegativeKeyword("Jobs", "Phrase", "evidence:y"))),
            "duplicate negative keyword",
        ),
        (
            lambda c: replace(c, ad_groups=(replace(c.ad_groups[0], ads=(replace(c.ad_groups[0].ads[0], final_url="http://example.invalid"),)),)),
            "https URL",
        ),
        (
            lambda c: replace(c, ad_groups=(replace(c.ad_groups[0], ads=(replace(c.ad_groups[0].ads[0], headlines=tuple(f"H{i}" for i in range(16))),)),)),
            "exceeds the Editor column set",
        ),
        (
            lambda c: replace(c, ad_groups=(replace(c.ad_groups[0], keywords=(EditorKeyword("dup", "Exact"), EditorKeyword("Dup", "Exact"))),)),
            "duplicate keyword",
        ),
    ],
)
def test_unsafe_drafts_fail_closed(mutate, message: str):
    with pytest.raises(EditorExportError, match=message):
        build_editor_rows([mutate(_draft())])


def test_campaign_negatives_with_evidence_render_in_editor_notation():
    draft = replace(
        _draft(),
        negative_keywords=(
            EditorNegativeKeyword("sanitized job", "Broad", "evidence:search-terms-report"),
            EditorNegativeKeyword("sanitized salary", "Phrase", "evidence:search-terms-report"),
            EditorNegativeKeyword("sanitized brand", "Exact", "evidence:form-review"),
        ),
    )
    rows = build_editor_rows([draft])
    negatives = [row for row in rows if row["Match type"] == "Campaign negative"]
    assert [row["Keyword"] for row in negatives] == ["sanitized job", '"sanitized salary"', "[sanitized brand]"]
    assert all(row["Campaign"] == "Sanitized Search Campaign" and row["Ad group"] == "" and row["Status"] == "Enabled" for row in negatives)
    assert rows.index(negatives[0]) == 1  # negatives follow the campaign row, before ad groups


def test_duplicate_campaign_names_and_empty_drafts_are_rejected():
    with pytest.raises(EditorExportError, match="duplicate campaign name"):
        build_editor_rows([_draft(), _draft()])
    with pytest.raises(EditorExportError, match="no campaigns"):
        build_editor_rows([])
