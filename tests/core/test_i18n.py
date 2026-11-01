"""Tests for the German/Polish/English message catalogs, formatting, and localized reports."""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from claude_ads_core.cli import main
from claude_ads_core.i18n import (
    DEFAULT_LANGUAGE,
    MISSING_MARKER,
    SUPPORTED_LANGUAGES,
    I18nError,
    Translator,
    catalog_meta,
    glossary,
    load_catalog,
    normalize_language,
    placeholders,
)
from claude_ads_core.reporting import render_html, render_markdown

BUNDLE_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "reports" / "sanitized-report-bundle.json"


def load_bundle() -> dict:
    return json.loads(BUNDLE_PATH.read_text(encoding="utf-8"))


# ------------------------------------------------------------------ catalogs


def test_german_and_polish_define_identical_keys():
    de, pl = load_catalog("de"), load_catalog("pl")
    assert set(de) == set(pl), sorted(set(de) ^ set(pl))


def test_english_is_a_subset_and_extras_are_only_enum_labels():
    en, de = load_catalog("en"), load_catalog("de")
    assert set(en) <= set(de), sorted(set(en) - set(de))
    assert all(key.startswith("enum.") or key == "common.draft_notice" for key in set(de) - set(en))


@pytest.mark.parametrize("language", SUPPORTED_LANGUAGES)
def test_no_empty_values_and_placeholders_match_english(language):
    en = load_catalog("en")
    for key, message in load_catalog(language).items():
        assert message.strip(), f"{language}:{key} is empty"
        if key in en:
            assert placeholders(message) == placeholders(en[key]), f"{language}:{key} placeholder mismatch"


def test_german_uses_real_umlauts_not_ascii_substitutes():
    text = " ".join(load_catalog("de").values())
    assert re.search(r"[äöüß]", text)
    for bad in ("Vollstaendig", "Gesundheitswert fuer", "waehrend", "Massnahme", "Widersprueche", "Pruefung", "Loesch"):
        assert bad not in text


def test_polish_uses_diacritics():
    text = " ".join(load_catalog("pl").values())
    for char in "ąęłńóśźż":
        assert char in text, f"no Polish value contains {char!r}"


def test_catalog_review_status_is_honest():
    assert catalog_meta("en")["review_status"] == "reference"
    for language in ("de", "pl"):
        meta = catalog_meta(language)
        assert meta["language"] == language
        assert meta["review_status"] in {"entwurf", "geprueft"}
        if meta["review_status"] == "geprueft":
            assert meta["reviewed_by"], "a reviewed catalog must name the reviewer role"


def test_catalog_modules_define_meta_and_string_messages():
    for language in SUPPORTED_LANGUAGES:
        assert catalog_meta(language)["language"] == language
        assert load_catalog(language)


# ---------------------------------------------------------------- translator


def test_normalize_language_accepts_locale_codes_and_rejects_unknown():
    assert normalize_language(None) == DEFAULT_LANGUAGE
    assert normalize_language("de-DE") == "de"
    assert normalize_language("PL_pl") == "pl"
    with pytest.raises(I18nError):
        normalize_language("fr")


def test_unknown_key_and_missing_parameter_fail_loudly():
    tr = Translator("de")
    with pytest.raises(I18nError, match="unknown message key"):
        tr.t("report.does_not_exist")
    with pytest.raises(I18nError, match="needs parameter"):
        tr.t("report.window_range", start="2026-10-01")


def test_missing_translation_is_visible_and_recorded(monkeypatch):
    tr = Translator("pl")
    monkeypatch.delitem(tr._messages, "report.findings")
    text = tr.t("report.findings")
    assert text == MISSING_MARKER + "Findings"
    assert tr.missing == ["report.findings"]


def test_label_translates_known_values_and_falls_back_to_legacy_title_case():
    assert Translator("de").label("severity", "critical") == "Kritisch"
    assert Translator("pl").label("severity", "critical") == "Krytyczna"
    assert Translator("en").label("severity", "high") == "High"
    assert Translator("en").label("source_classification", "evidence_based") == "Evidence Based"
    assert Translator("de").label("severity", "brand_new_value") == "Brand New Value"


@pytest.mark.parametrize(
    ("language", "number", "percent", "money", "day"),
    [
        ("en", "1,234.50", "12.50%", "€1,234.50", "2026-11-01"),
        ("de", "1.234,50", "12,50\u00a0%", "1.234,50 €", "01.11.2026"),
        ("pl", "1 234,50", "12,50%", "1 234,50 zł", "01.11.2026"),
    ],
)
def test_locale_formatting(language, number, percent, money, day):
    tr = Translator(language)
    assert tr.number(1234.5) == number
    assert tr.percent(12.5) == percent
    currency = {"en": "EUR", "de": "EUR", "pl": "PLN"}[language]
    assert tr.money(1234.5, currency) == money
    assert tr.date("2026-11-01") == day


def test_formatting_edge_cases():
    tr = Translator("de")
    assert tr.number(-0.5) == "-0,50"
    assert tr.number(0) == "0,00"
    assert tr.score(None) == "Nicht bewertet"
    assert tr.score(87.5) == "87,50 / 100"
    assert Translator("en").money(10, "CHF") == "CHF10.00"
    assert Translator("en").money(10, "SEK") == "SEK 10.00"
    with pytest.raises(I18nError):
        tr.money(1, "euro")
    with pytest.raises(ValueError):
        tr.date("not-a-date")


# ------------------------------------------------------------ localized reports


@pytest.mark.parametrize("language", ("de", "pl"))
def test_markdown_report_is_localized_without_english_leftovers(language):
    output = render_markdown(load_bundle(), language)
    tr = Translator(language)
    assert output.startswith(f"# {tr.t('report.title')}")
    assert tr.t("report.footer") in output
    assert MISSING_MARKER not in output
    assert "Run summary" not in output and "Prioritized actions" not in output
    assert tr.t("report.findings") in output


@pytest.mark.parametrize("language", ("de", "pl"))
def test_html_report_sets_language_and_localizes_headings(language):
    output = render_html(load_bundle(), language)
    tr = Translator(language)
    assert f'<html lang="{language}">' in output
    assert f"<h2>{tr.t('report.run_summary')}</h2>" in output
    assert MISSING_MARKER not in output
    assert "<script" not in output


def test_localized_numbers_use_the_language_separators():
    bundle = load_bundle()
    de = render_markdown(bundle, "de")
    en = render_markdown(bundle, "en")
    score = bundle["scoring"]["health_score"]
    if score is not None:
        assert f"{score:.2f}".replace(".", ",") + " / 100" in de
        assert f"{score:.2f} / 100" in en


def test_localized_html_still_escapes_untrusted_text():
    bundle = load_bundle()
    bundle["findings"][0]["observation"] = "<script>alert(1)</script>"
    output = render_html(bundle, "pl")
    assert "<script>alert(1)</script>" not in output
    assert "&lt;script&gt;" in output


def test_default_language_output_is_unchanged_english():
    assert render_markdown(load_bundle()) == render_markdown(load_bundle(), "en")
    assert "Run summary" in render_markdown(load_bundle())


# ------------------------------------------------------------------------- CLI


def test_cli_render_honours_lang_option(tmp_path, capsys):
    root = tmp_path / "out"
    code = main(["render", str(BUNDLE_PATH), "--format", "markdown", "--root", str(root), "--lang", "pl"])
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["lang"] == "pl"
    text = Path(payload["path"]).read_text(encoding="utf-8")
    assert text.startswith("# " + Translator("pl").t("report.title"))


def test_cli_render_reads_adbot_lang_environment(tmp_path, capsys, monkeypatch):
    monkeypatch.setenv("ADBOT_LANG", "de")
    assert main(["render", str(BUNDLE_PATH), "--root", str(tmp_path / "o")]) == 0
    assert json.loads(capsys.readouterr().out)["lang"] == "de"


def test_cli_render_rejects_unsupported_language_from_environment(tmp_path, capsys, monkeypatch):
    monkeypatch.setenv("ADBOT_LANG", "fr")
    assert main(["render", str(BUNDLE_PATH), "--root", str(tmp_path / "o")]) == 2
    assert "unsupported language" in capsys.readouterr().err


# -------------------------------------------------------------------- glossary


def _glossary() -> dict:
    data = glossary()
    return {"_meta": data["meta"], "terms": data["terms"]}


def test_glossary_entries_are_complete_unique_and_marked_as_draft():
    glossary = _glossary()
    assert glossary["_meta"]["pl_terms_status"] in {"entwurf", "geprueft"}
    terms = glossary["terms"]
    assert len(terms) >= 25
    ids = [term["id"] for term in terms]
    assert len(ids) == len(set(ids))
    for term in terms:
        assert set(term) == {"id", "en", "de", "pl", "explain_de", "explain_pl", "explain_en"}
        assert all(isinstance(value, str) and value.strip() for value in term.values()), term["id"]
        assert re.fullmatch(r"[a-z][a-z0-9_]*", term["id"])


def test_glossary_makes_no_unsourced_numeric_platform_claims():
    text = json.dumps(_glossary(), ensure_ascii=False)
    for forbidden in ("30 Zeichen", "90 Zeichen", "30 znak", "90 znak", "1 bis 10", "od 1 do 10"):
        assert forbidden not in text


def test_glossary_terms_cover_the_labels_used_in_user_facing_text():
    terms = {term["id"] for term in _glossary()["terms"]}
    for needed in ("campaign", "ad_group", "keyword", "negative_keyword", "conversion", "daily_budget", "bid_strategy"):
        assert needed in terms


def test_english_money_keeps_the_minus_sign_in_front():
    assert Translator("en").money(-3, "PLN") == "-zł3.00"
    assert Translator("en").money(-3, "EUR") == "-€3.00"
    assert Translator("de").money(-3, "EUR") == "-3,00\u00a0€"


def test_draft_notice_is_shown_for_unreviewed_languages_only():
    assert Translator("en").draft_notice() is None
    assert "Entwurf" in Translator("de").draft_notice()
    assert "wersją roboczą" in Translator("pl").draft_notice()


def test_every_glossary_term_is_explained_in_every_language():
    for term in glossary()["terms"]:
        explanations = [term["explain_de"], term["explain_pl"], term["explain_en"]]
        assert all(text.strip() for text in explanations), term["id"]
        assert len(set(explanations)) == 3, f"{term['id']}: an explanation is copied between languages"
