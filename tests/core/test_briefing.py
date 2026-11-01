"""Tests for the campaign briefing gate and the paused Editor draft (dry run, DE and PL)."""
from __future__ import annotations

import copy
import csv
import io
import json
from pathlib import Path

import pytest

from claude_ads_core.briefing import BriefingError, briefing_to_campaign, validate_briefing
from claude_ads_core.editor_export import (
    EditorKeyword,
    EditorNegativeKeyword,
    EditorResponsiveSearchAd,
    build_editor_rows,
    render_editor_csv,
)

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "assistant"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _ad(url: str) -> EditorResponsiveSearchAd:
    return EditorResponsiveSearchAd(
        headlines=("Beispiel Titel Eins", "Beispiel Titel Zwei", "Beispiel Titel Drei"),
        descriptions=("Beispielbeschreibung eins.", "Beispielbeschreibung zwei."),
        final_url=url,
    )


@pytest.mark.parametrize(("name", "language", "currency", "budget"), [("briefing-de.json", "de", "EUR", "15.00"), ("briefing-pl.json", "pl", "PLN", "60.00")])
def test_confirmed_briefing_is_valid_and_normalized(name, language, currency, budget):
    checked = validate_briefing(_load(name))
    assert checked["language"] == language and checked["currency"] == currency
    assert checked["daily_budget"] == budget


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: d.update(confirmed_by_user=False),
        lambda d: d.pop("confirmed_by_user"),
        lambda d: d.update(daily_budget="0"),
        lambda d: d.update(daily_budget="-5"),
        lambda d: d.update(daily_budget="viel"),
        lambda d: d.update(daily_budget="NaN"),
        lambda d: d.update(currency="eur"),
        lambda d: d.update(language="en"),
        lambda d: d.update(goal_kind="fame"),
        lambda d: d.update(website="http://example.invalid"),
        lambda d: d.update(goal="   "),
        lambda d: d.update(confirmed_at="gestern"),
        lambda d: d.update(api_token="x"),
        lambda d: d.update(confirmation_quote=""),
        lambda d: d.pop("confirmation_quote"),
    ],
)
def test_unconfirmed_or_inconsistent_briefings_are_refused(mutate):
    document = copy.deepcopy(_load("briefing-de.json"))
    mutate(document)
    with pytest.raises(BriefingError):
        validate_briefing(document)


def test_non_object_briefing_is_refused():
    with pytest.raises(BriefingError):
        validate_briefing(["not", "an", "object"])


@pytest.mark.parametrize(("name", "language", "location"), [("briefing-de.json", "German", "Germany"), ("briefing-pl.json", "Polish", "Poland")])
def test_dry_run_builds_a_paused_editor_draft(tmp_path, name, language, location):
    briefing = _load(name)
    campaign = briefing_to_campaign(
        briefing,
        campaign_name="Entwurf Suche",
        ad_group_name="Wartung",
        keywords=(EditorKeyword("heizungswartung", "Phrase"), EditorKeyword("ofen przegląd", "Exact")),
        ads=(_ad(briefing["website"]),),
        negatives=(EditorNegativeKeyword("kostenlos", "Phrase", evidence_ref="search-terms-report-2026-10"),),
    )
    rows = build_editor_rows([campaign])
    assert rows[0]["Campaign status"] == "Paused"
    assert rows[0]["Languages"] == language and rows[0]["Location"] == location
    csv_text = render_editor_csv([campaign])
    parsed = list(csv.DictReader(io.StringIO(csv_text)))
    assert parsed and all(row["Campaign status"] in {"Paused", ""} for row in parsed)
    assert "Enabled" not in {row["Campaign status"] for row in parsed}


def test_draft_is_refused_for_an_unconfirmed_briefing():
    document = _load("briefing-de.json")
    document["confirmed_by_user"] = False
    with pytest.raises(BriefingError, match="confirmed"):
        briefing_to_campaign(document, campaign_name="X", ad_group_name="Y",
                             keywords=(EditorKeyword("a", "Exact"),), ads=(_ad("https://example.invalid"),))


def test_briefing_currency_must_match_the_account_currency_when_known():
    document = _load("briefing-de.json")
    assert validate_briefing(document, account_currency="EUR")["currency"] == "EUR"
    with pytest.raises(BriefingError, match="differs from the account currency"):
        validate_briefing(document, account_currency="PLN")
    with pytest.raises(BriefingError, match="account currency"):
        briefing_to_campaign(document, campaign_name="X", ad_group_name="Y", keywords=(EditorKeyword("a", "Exact"),),
                             ads=(_ad("https://example.invalid"),), account_currency="PLN")


def test_the_users_own_words_are_kept_in_the_normalized_briefing():
    assert validate_briefing(_load("briefing-pl.json"))["confirmation_quote"] == "Tak, tak jest dobrze."
