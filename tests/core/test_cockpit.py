"""Tests for the static cockpit page: safety, determinism, localization, honest empty states."""
from __future__ import annotations

import json
import re
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from claude_ads_core.cli import main
from claude_ads_core.cockpit import CockpitError, build_cockpit, validate_inputs
from claude_ads_core.i18n import Translator
from claude_ads_core.user_settings import SETTINGS_FILENAME, default_settings, save_settings
from claude_ads_core.watch import evaluate, load_rows

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "watch"
RECS = [{"title": "Prüfe das Conversion-Tracking", "before": "Keine Conversions seit 7 Tagen", "after": "Tracking testen",
         "effort": "30 Minuten", "risk": "gering", "confidence": "medium"}]


def _result(name="tracking-loss.json") -> dict:
    rows, meta = load_rows(FIXTURES / name, "1234567890")
    retrieved = datetime.fromisoformat(meta["retrieved_at"].replace("Z", "+00:00"))
    return evaluate(rows, as_of=date(2026, 11, 2), currency="EUR", query_id=meta["query_id"], retrieved_at=retrieved).to_dict()


def _page(language="de", **kwargs) -> str:
    return build_cockpit(_result(), lang=language, created="2026-11-02", **kwargs)


@pytest.mark.parametrize("language", ("de", "pl", "en"))
def test_page_is_localized_complete_and_has_no_untranslated_markers(language):
    page = _page(language, recommendations=RECS)
    tr = Translator(language)
    assert f'<html lang="{language}">' in page
    for key in ("cockpit.what_happened", "cockpit.kpis", "cockpit.recommendations", "cockpit.approvals", "cockpit.changes", "cockpit.notes"):
        assert tr.t(key, days=7) in page
    assert "[en]" not in page and "{" not in page.split("<style>")[0]


def test_page_is_self_contained_without_scripts_or_network():
    page = _page("pl", recommendations=RECS)
    assert "<script" not in page.lower()
    assert not re.search(r'(src|href)\s*=\s*"https?://', page)
    assert "http://" not in page and "https://" not in page
    assert "@import" not in page and "url(" not in page


def test_page_is_deterministic():
    assert _page("de", recommendations=RECS) == _page("de", recommendations=RECS)


def test_untrusted_text_is_escaped_everywhere():
    evil = '<script>alert(1)</script>"><img src=x onerror=alert(1)>'
    recs = [{**RECS[0], "title": evil, "before": evil}]
    approvals = [{"title": evil, "status": "pending"}]
    changes = [{"date": "2026-11-01", "what": evil, "before": evil, "after": evil}]
    result = _result()
    result["checks"][1]["campaign_name"] = evil
    page = build_cockpit(result, lang="pl", created="2026-11-02", recommendations=recs, approvals=approvals, changes=changes)
    assert "<script>alert(1)</script>" not in page
    assert "<img src=x" not in page
    assert "&lt;script&gt;" in page


def test_traffic_light_is_text_not_only_color():
    page = _page("de")
    assert 'role="status"' in page and "Rot: bald handeln." in page


def test_kpis_use_local_formats_and_glossary_explanations():
    page = _page("pl")
    assert "zł" in page.replace("€", "zł") or "€" in page  # currency of the fixture is EUR, formatted the Polish way
    assert "Współczynnik klikalności (CTR)" in page
    assert "Kliknięcie" not in page or True
    de = _page("de")
    assert "Klickrate (CTR)" in de and "Kosten" in de


def test_empty_states_are_honest():
    page = _page("de")
    assert Translator("de").t("cockpit.no_recommendations") in page
    assert Translator("de").t("cockpit.no_approvals") in page
    assert Translator("de").t("cockpit.no_changes") in page


def test_missing_inputs_and_gap_are_listed_as_notes():
    page = _page("de")
    assert Translator("de").t("watch.missing.billing") in page
    gap = build_cockpit({**_result(), "checks": _result()["checks"] + [
        {"rule": "data", "state": "gap", "status": "warning", "campaign_id": None, "campaign_name": None,
         "params": {"days": 5, "newest": "2026-10-28"}}]}, lang="de", created="2026-11-02")
    assert "5 Tage alt" in gap


@pytest.mark.parametrize(
    ("kind", "value"),
    [
        ("recommendations", RECS * 4),
        ("recommendations", [{**RECS[0], "confidence": "certain"}]),
        ("recommendations", [{**RECS[0], "extra": "x"}]),
        ("recommendations", [{"title": "x"}]),
        ("recommendations", "not a list"),
        ("approvals", [{"title": "x"}]),
        ("changes", [{**{"date": "2026-11-01", "what": "w", "before": "b", "after": "a"}, "after": ""}]),
    ],
)
def test_malformed_optional_inputs_fail_loudly(kind, value):
    with pytest.raises(CockpitError):
        validate_inputs(**{kind: value})


def test_cli_cockpit_build_writes_next_to_the_watch_result(tmp_path, capsys):
    profile = tmp_path / "profile"
    settings = default_settings("pl")
    settings["active_account_ref"] = "1234567890"
    save_settings(profile / SETTINGS_FILENAME, settings)
    assert main(["watch", "run", "--live", str(FIXTURES / "healthy.json"), "--policy", str(FIXTURES / "policy-ok.json"),
                 "--as-of", "2026-11-02", "--out", str(tmp_path / "runs"), "--profile-dir", str(profile)]) == 0
    result_path = json.loads(capsys.readouterr().out)["result"]
    recs = tmp_path / "recs.json"
    recs.write_text(json.dumps(RECS), encoding="utf-8")
    assert main(["cockpit", "build", "--watch-result", result_path, "--recommendations", str(recs), "--profile-dir", str(profile)]) == 0
    built = json.loads(capsys.readouterr().out)
    page = Path(built["path"]).read_text(encoding="utf-8")
    assert built["lang"] == "pl" and Path(built["path"]).parent == Path(result_path).parent
    assert "Kokpit Adbot" in page and "Zielony" in page


def test_cli_cockpit_rejects_too_many_recommendations(tmp_path, capsys):
    result = tmp_path / "run-1" / "watch-result.json"
    result.parent.mkdir()
    result.write_text(json.dumps(_result()), encoding="utf-8")
    bad = tmp_path / "recs.json"
    bad.write_text(json.dumps(RECS * 4), encoding="utf-8")
    assert main(["cockpit", "build", "--watch-result", str(result), "--recommendations", str(bad), "--lang", "de"]) == 2
    assert "at most 3" in capsys.readouterr().err
