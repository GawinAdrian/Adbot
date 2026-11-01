"""Tests for the deterministic watcher: rules, small-number safety, bundle contract, determinism."""
from __future__ import annotations

import json
import shutil
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from claude_ads_core.cli import main
from claude_ads_core.i18n import Translator
from claude_ads_core.user_settings import SETTINGS_FILENAME, default_settings, save_settings
from claude_ads_core.watch import (
    WatchError,
    describe,
    evaluate,
    load_rows,
    render_watch_text,
    run_watch,
    to_monitoring_bundle,
    attested_lifecycle,
)
from claude_ads_core.workflow_contracts import validate_workflow_contract

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "watch"
AS_OF = date(2026, 11, 2)
NOW = datetime(2026, 11, 2, 6, 0, tzinfo=timezone.utc)


def _result(name, *, as_of=AS_OF, policy=None):
    rows, meta = load_rows(FIXTURES / name, "1234567890")
    policy_rows = None
    if policy:
        policy_rows, _ = __import__("claude_ads_core.watch", fromlist=["_load_policy"])._load_policy(FIXTURES / policy, "1234567890")
    retrieved = datetime.fromisoformat(meta["retrieved_at"].replace("Z", "+00:00"))
    return evaluate(rows, as_of=as_of, currency="EUR", query_id=meta["query_id"], retrieved_at=retrieved, policy_rows=policy_rows)


def _states(result):
    return {(c.rule, c.state) for c in result.checks}


def test_healthy_account_is_green():
    result = _result("healthy.json", policy="policy-ok.json")
    assert result.ampel == "green"
    assert _states(result) >= {("pacing", "normal"), ("delivery", "normal"), ("conversions", "normal"), ("policy", "normal"), ("data", "normal")}


@pytest.mark.parametrize(
    ("fixture", "rule", "state", "status", "ampel"),
    [
        ("capped.json", "pacing", "capped", "warning", "yellow"),
        ("under.json", "pacing", "under", "warning", "yellow"),
        ("over.json", "pacing", "over", "warning", "yellow"),
        ("stopped.json", "delivery", "stopped", "critical", "red"),
        ("tracking-loss.json", "conversions", "drop", "critical", "red"),
        ("no-conversions.json", "conversions", "none", "warning", "yellow"),
    ],
)
def test_each_rule_fires_on_its_fixture(fixture, rule, state, status, ampel):
    result = _result(fixture, policy="policy-ok.json")
    hit = [c for c in result.checks if c.rule == rule and c.state == state]
    assert hit and hit[0].status == status
    assert result.ampel == ampel


def test_small_numbers_never_raise_an_alarm():
    result = _result("small-numbers.json", policy="policy-ok.json")
    conv = [c for c in result.checks if c.rule == "conversions"][0]
    assert (conv.state, conv.status) == ("insufficient", "unknown")
    assert conv.params["clicks"] < conv.params["minimum"]
    assert "drop" not in {c.state for c in result.checks}


def test_disapproved_ads_are_critical_and_missing_policy_data_is_reported():
    red = _result("healthy.json", policy="policy-disapproved.json")
    policy = [c for c in red.checks if c.rule == "policy"][0]
    assert (policy.state, policy.status, policy.params["count"]) == ("disapproved", "critical", 2)
    assert red.ampel == "red"
    unknown = _result("healthy.json")
    assert "ad policy status" in unknown.missing_inputs
    assert [c for c in unknown.checks if c.rule == "policy"][0].status == "unknown"
    assert "billing and payment status" in unknown.missing_inputs  # always stated, never guessed


def test_data_gap_is_a_warning_with_the_age():
    result = _result("healthy.json", as_of=date(2026, 11, 6), policy="policy-ok.json")
    gap = [c for c in result.checks if c.rule == "data"][0]
    assert (gap.state, gap.params["days"], gap.params["newest"]) == ("gap", 4, "2026-11-01")


def test_paused_campaigns_are_not_judged_and_all_unknown_is_grey():
    result = _result("paused.json")
    assert ("campaigns", "none_enabled") in _states(result)
    assert not [c for c in result.checks if c.rule in {"pacing", "delivery", "conversions"}]


def test_empty_or_malformed_input_fails_loudly(tmp_path):
    with pytest.raises(WatchError, match="no rows"):
        evaluate([], as_of=AS_OF, currency="EUR", query_id="q", retrieved_at=NOW)
    broken = json.loads((FIXTURES / "healthy.json").read_text(encoding="utf-8"))
    for row in broken["rows"]:
        del row["metrics.clicks"]
    path = tmp_path / "broken.json"
    path.write_text(json.dumps(broken))
    with pytest.raises(WatchError, match="metrics.clicks"):
        load_rows(path, "1234567890")


def test_wrong_customer_is_rejected():
    with pytest.raises(Exception, match="customer"):
        load_rows(FIXTURES / "healthy.json", "9999999999")


def test_result_is_deterministic():
    first = _result("tracking-loss.json", policy="policy-ok.json").to_dict()
    second = _result("tracking-loss.json", policy="policy-ok.json").to_dict()
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


# --------------------------------------------------------------- contract output


@pytest.mark.parametrize("fixture", ["healthy.json", "stopped.json", "tracking-loss.json", "capped.json", "small-numbers.json"])
def test_bundle_is_a_valid_monitoring_bundle(fixture):
    result = _result(fixture, policy="policy-ok.json")
    lifecycle = attested_lifecycle("2026-11-01", "watch-test", NOW)
    bundle = to_monitoring_bundle(result, run_id="watch-test", created_at=NOW, lifecycle=lifecycle, timezone_name="Europe/Berlin")
    validate_workflow_contract("monitoring-bundle", bundle)
    assert bundle["completeness"] == "partial"  # billing status is always a missing input
    if fixture == "small-numbers.json":
        assert any(cp["status"] == "unknown" and not cp["evidence_refs"] for cp in bundle["checkpoints"])
    assert all(cp["evidence_refs"] for cp in bundle["checkpoints"] if cp["status"] != "unknown")


def test_bundle_without_verified_encryption_is_refused_by_the_contract():
    result = _result("healthy.json", policy="policy-ok.json")
    lifecycle = attested_lifecycle("2026-11-01", "watch-test", NOW)
    lifecycle["encryption"] = {"at_rest": "not-applicable", "in_transit": "verified", "evidence_refs": []}
    with pytest.raises(Exception, match="encryption"):
        to_monitoring_bundle(result, run_id="watch-test", created_at=NOW, lifecycle=lifecycle, timezone_name="UTC")


# ------------------------------------------------------------------ localized text


@pytest.mark.parametrize("language", ("de", "pl", "en"))
def test_every_state_has_text_in_every_language(language):
    tr = Translator(language)
    for fixture, policy in (("capped.json", "policy-disapproved.json"), ("tracking-loss.json", None), ("stopped.json", None),
                            ("small-numbers.json", None), ("under.json", None), ("over.json", None), ("no-conversions.json", None),
                            ("paused.json", None)):
        result = _result(fixture, policy=policy)
        for check in result.checks:
            text, _ = describe(check, tr, "EUR")
            assert text and "[en]" not in text and "{" not in text, (language, check.rule, check.state)
        assert "[en]" not in render_watch_text(result.to_dict(), tr)


def test_german_and_polish_text_use_local_money_formats():
    result = _result("capped.json", policy="policy-ok.json")
    de = render_watch_text(result.to_dict(), Translator("de"))
    pl = render_watch_text(result.to_dict(), Translator("pl"))
    assert "15,00 €" in de and "15,00 €" in pl.replace("zł", "€") or "15,00 zł" in pl
    assert "Gelb" in de and "Żółty" in pl


# ------------------------------------------------------------------- run + CLI


def test_run_watch_writes_a_new_directory_and_never_overwrites(tmp_path):
    first = run_watch(FIXTURES / "healthy.json", "1234567890", as_of=AS_OF, out_dir=tmp_path, policy_envelope=FIXTURES / "policy-ok.json", now=NOW)
    assert Path(first["result"]).is_file() and first["bundle_written"] is False
    with pytest.raises(FileExistsError):
        run_watch(FIXTURES / "healthy.json", "1234567890", as_of=AS_OF, out_dir=tmp_path, now=NOW)  # same second -> same run id


def test_run_watch_writes_a_bundle_only_when_encryption_is_attested(tmp_path):
    result = run_watch(FIXTURES / "healthy.json", "1234567890", as_of=AS_OF, out_dir=tmp_path, attested_on="2026-11-01", now=NOW)
    assert result["bundle_written"] is True
    validate_workflow_contract("monitoring-bundle", json.loads(Path(result["bundle"]).read_text(encoding="utf-8")))


def test_cli_watch_run_and_show(tmp_path, capsys):
    profile = tmp_path / "profile"
    settings = default_settings("pl")
    settings["active_account_ref"] = "1234567890"
    save_settings(profile / SETTINGS_FILENAME, settings)
    code = main(["watch", "run", "--live", str(FIXTURES / "tracking-loss.json"), "--policy", str(FIXTURES / "policy-ok.json"),
                 "--as-of", "2026-11-02", "--out", str(tmp_path / "runs"), "--profile-dir", str(profile)])
    payload = json.loads(capsys.readouterr().out)
    assert code == 0 and payload["ampel"] == "red" and payload["bundle_written"] is False
    assert main(["watch", "show", payload["result"], "--lang", "pl"]) == 0
    out = capsys.readouterr().out
    assert "Czerwony" in out and "śledzenie konwersji" in out


def test_cli_watch_run_without_account_fails_clearly(tmp_path, capsys):
    profile = tmp_path / "profile"
    save_settings(profile / SETTINGS_FILENAME, default_settings("de"))
    code = main(["watch", "run", "--live", str(FIXTURES / "healthy.json"), "--out", str(tmp_path / "r"), "--profile-dir", str(profile)])
    assert code == 2 and "no active account" in capsys.readouterr().err


def test_numbers_inside_messages_use_the_language_format():
    result = _result("tracking-loss.json", policy="policy-ok.json")
    drop = [c for c in result.checks if c.state == "drop"][0]
    pl, _ = describe(drop, Translator("pl"), "EUR")
    de, _ = describe(drop, Translator("de"), "EUR")
    en, _ = describe(drop, Translator("en"), "EUR")
    assert "14.0" not in pl and "14.0" not in de and "14.0" not in en
    assert "liczba kliknięć: 140" in pl and "14" in pl
    assert "140 Klicks" in de
    data = [c for c in result.checks if c.rule == "data"][0]
    assert "01.11.2026" in describe(data, Translator("de"), "EUR")[0]  # dates use the local format


# ----------------------------------------------------- regressions from the independent review


def test_campaign_that_went_quiet_long_ago_is_still_reported_as_stopped():
    result = _result("dead-long.json", policy="policy-ok.json")
    delivery = [c for c in result.checks if c.rule == "delivery"][0]
    assert (delivery.state, delivery.status) == ("stopped", "critical")
    assert result.ampel == "red"


def test_a_brand_new_campaign_is_not_judged_on_spending():
    result = _result("new-campaign.json", policy="policy-ok.json")
    pacing = [c for c in result.checks if c.rule == "pacing"][0]
    assert (pacing.state, pacing.status) == ("new", "unknown")


def test_one_or_two_earlier_conversions_never_raise_a_red_alarm():
    result = _result("thin-conversions.json", policy="policy-ok.json")
    conv = [c for c in result.checks if c.rule == "conversions"][0]
    assert (conv.state, conv.status) == ("thin", "unknown")
    assert result.ampel != "red"


def test_over_delivery_needs_a_large_excess():
    from claude_ads_core import watch

    assert watch.PACING_OVER_RATIO >= 2.0
    assert ("pacing", "over") in _states(_result("over.json", policy="policy-ok.json"))
    assert ("pacing", "over") not in _states(_result("capped.json", policy="policy-ok.json"))


def test_data_gap_is_found_by_comparing_with_the_previous_run():
    rows, meta = load_rows(FIXTURES / "healthy.json", "1234567890")
    retrieved = datetime.fromisoformat(meta["retrieved_at"].replace("Z", "+00:00"))
    quiet = evaluate(rows, as_of=AS_OF, currency="EUR", query_id="q", retrieved_at=retrieved, previous_run=date(2026, 10, 28))
    gap = [c for c in quiet.checks if c.rule == "data"][0]
    assert (gap.state, gap.params["days"]) == ("gap", 5)
    fresh = evaluate(rows, as_of=AS_OF, currency="EUR", query_id="q", retrieved_at=retrieved, previous_run=date(2026, 11, 1))
    assert [c for c in fresh.checks if c.rule == "data"][0].state == "normal"


def test_run_watch_uses_the_previous_run_to_report_a_gap(tmp_path):
    first = run_watch(FIXTURES / "healthy.json", "1234567890", as_of=date(2026, 10, 25), out_dir=tmp_path, now=datetime(2026, 10, 25, 6, tzinfo=timezone.utc))
    assert first["ampel"] in {"green", "yellow"}
    second = run_watch(FIXTURES / "healthy.json", "1234567890", as_of=AS_OF, out_dir=tmp_path, now=NOW)
    data = json.loads(Path(second["result"]).read_text(encoding="utf-8"))["checks"][0]
    assert data["rule"] == "data" and data["state"] == "gap"


def test_empty_pull_gives_a_yellow_notice_not_a_failure():
    from claude_ads_core.watch import empty_result

    result = empty_result(as_of=AS_OF, currency="EUR", query_id="q", window_start=date(2026, 10, 19), window_end=date(2026, 11, 1))
    assert result.ampel == "yellow" and result.checks[0].state == "empty" and result.checks[0].params["days"] == 14
    for language in ("de", "pl", "en"):
        text = render_watch_text(result.to_dict(), Translator(language))
        assert "14" in text and "[en]" not in text


def test_policy_envelope_for_another_account_is_rejected(tmp_path):
    policy = json.loads((FIXTURES / "policy-ok.json").read_text(encoding="utf-8"))
    policy["customer_id"] = "9999999999"
    path = tmp_path / "other.json"
    path.write_text(json.dumps(policy))
    with pytest.raises(Exception, match="customer"):
        run_watch(FIXTURES / "healthy.json", "1234567890", as_of=AS_OF, out_dir=tmp_path / "r", policy_envelope=path, now=NOW)


def test_results_are_written_private(tmp_path):
    import os
    import stat

    result = run_watch(FIXTURES / "healthy.json", "1234567890", as_of=AS_OF, out_dir=tmp_path / "runs", attested_on="2026-11-01", now=NOW)
    if os.name == "posix":
        for key in ("result", "bundle"):
            assert stat.S_IMODE(Path(result[key]).stat().st_mode) == 0o600
        assert stat.S_IMODE(Path(result["result"]).parent.stat().st_mode) == 0o700
