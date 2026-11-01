"""Tests for the read-only ``doctor`` diagnosis (offline, no network, no secret output)."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import pytest

from claude_ads_core.cli import main
from claude_ads_core.doctor import (
    Check,
    classify_api_error,
    is_connected,
    render_text,
    run_doctor,
    to_json,
)
from claude_ads_core.i18n import Translator, load_catalog
from claude_ads_core.user_settings import SETTINGS_FILENAME, default_settings, save_settings

SECRET = "super-secret-refresh-token-value"
ALL_TOOLS = {"uv": "/bin/uv", "gcloud": "/bin/gcloud"}


def _which(tools):
    return lambda name: tools.get(name)


def _profile(tmp_path, *, project=True, account="1234567890", credentials="valid"):
    home = tmp_path / "home"
    profile = home / ".config" / "adbot" / "standard"
    profile.mkdir(parents=True)
    settings = default_settings("de", datetime(2026, 11, 1, tzinfo=timezone.utc))
    settings["active_account_ref"] = account
    save_settings(profile / SETTINGS_FILENAME, settings)
    if project:
        (profile / "env").write_text("GOOGLE_PROJECT_ID=demo-project\n")
    adc = home / ".config" / "gcloud" / "application_default_credentials.json"
    adc.parent.mkdir(parents=True)
    if credentials == "valid":
        adc.write_text(json.dumps({"type": "authorized_user", "client_id": "c", "client_secret": SECRET, "refresh_token": SECRET}))
    elif credentials == "broken":
        adc.write_text("{not json")
    elif credentials == "incomplete":
        adc.write_text(json.dumps({"type": "authorized_user", "client_id": "c"}))
    return home


def _by_id(checks):
    return {check.id: check for check in checks}


def test_fully_connected_profile_has_no_failures(tmp_path):
    home = _profile(tmp_path)
    checks, context = run_doctor({}, home=home, which=_which(ALL_TOOLS), python_version=(3, 12))
    assert [c.status for c in checks if c.status == "fail"] == []
    assert is_connected(checks)
    assert context["language"] == "de"
    assert _by_id(checks)["api"].status == "skip"


def test_empty_machine_reports_not_connected_without_crashing(tmp_path):
    checks, context = run_doctor({}, home=tmp_path / "nothing", which=_which({}), python_version=(3, 12))
    states = {c.id: (c.status, c.state) for c in checks}
    assert states["settings"] == ("fail", "fail")
    assert states["credentials"] == ("fail", "fail")
    assert states["project"] == ("fail", "fail")
    assert states["uv"][0] == "warn" and states["gcloud"][0] == "warn"
    assert not is_connected(checks)
    assert context == {}


@pytest.mark.parametrize(("variant", "state"), [("broken", "invalid"), ("incomplete", "invalid"), ("missing", "fail")])
def test_unusable_sign_in_files_are_flagged(tmp_path, variant, state):
    home = _profile(tmp_path, credentials=variant)
    checks, _ = run_doctor({}, home=home, which=_which(ALL_TOOLS), python_version=(3, 12))
    credentials = _by_id(checks)["credentials"]
    assert (credentials.status, credentials.state) == ("fail", state)
    assert not is_connected(checks)


def test_old_python_is_a_failure(tmp_path):
    checks, _ = run_doctor({}, home=_profile(tmp_path), which=_which(ALL_TOOLS), python_version=(3, 10))
    python = _by_id(checks)["python"]
    assert python.status == "fail" and python.params["version"] == "3.10"


def test_missing_account_is_only_a_notice(tmp_path):
    home = _profile(tmp_path, account=None)
    checks, _ = run_doctor({}, home=home, which=_which(ALL_TOOLS), python_version=(3, 12))
    assert _by_id(checks)["account"].status == "warn"
    assert is_connected(checks)


def test_environment_project_overrides_nothing_but_fills_gaps(tmp_path):
    home = _profile(tmp_path, project=False)
    checks, _ = run_doctor({"GOOGLE_PROJECT_ID": "from-env"}, home=home, which=_which(ALL_TOOLS), python_version=(3, 12))
    assert _by_id(checks)["project"].status == "ok"


# ------------------------------------------------------------------ online probe


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("google.auth.exceptions.RefreshError: invalid_grant: Token has been expired or revoked.", "invalid_grant"),
        ("Reauthentication is needed", "invalid_grant"),
        ("USER_PERMISSION_DENIED: User doesn't have permission to access customer", "permission_denied"),
        ("The caller does not have permission", "permission_denied"),
        ("something else entirely", "unknown"),
    ],
)
def test_classify_api_error(text, expected):
    assert classify_api_error(text) == expected


def test_online_probe_success_and_failures_use_injected_runner(tmp_path):
    home = _profile(tmp_path)
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "gaql_via_api.py").write_text("# stub")
    calls = []

    def ok(args, env):
        calls.append(list(args))
        return 0, ""

    checks, _ = run_doctor({}, home=home, which=_which(ALL_TOOLS), python_version=(3, 12), online=True, runner=ok, scripts_dir=scripts)
    assert _by_id(checks)["api"].status == "ok"
    assert "--customer" in calls[0] and "mutate" not in " ".join(calls[0]).lower()

    def expired(args, env):
        return 1, "RefreshError: invalid_grant"

    checks, _ = run_doctor({}, home=home, which=_which(ALL_TOOLS), python_version=(3, 12), online=True, runner=expired, scripts_dir=scripts)
    api = _by_id(checks)["api"]
    assert (api.status, api.state) == ("fail", "invalid_grant")


def test_online_probe_is_skipped_when_not_connected(tmp_path):
    def boom(args, env):  # pragma: no cover - must not be called
        raise AssertionError("runner must not be called")

    checks, _ = run_doctor({}, home=tmp_path / "none", which=_which({}), python_version=(3, 12), online=True, runner=boom)
    assert _by_id(checks)["api"].status == "skip"


# ----------------------------------------------------------------------- output


def test_every_message_key_exists_in_all_catalogs():
    states = {
        "python": ("ok", "fail"), "uv": ("ok", "warn"), "gcloud": ("ok", "warn"), "settings": ("ok", "fail"),
        "project": ("ok", "fail"), "credentials": ("ok", "fail", "invalid"), "account": ("ok", "warn"),
        "api": ("ok", "skip", "invalid_grant", "permission_denied", "unknown"),
    }
    needs_next = {("python", "fail"), ("uv", "warn"), ("gcloud", "warn"), ("settings", "fail"), ("project", "fail"),
                  ("credentials", "fail"), ("credentials", "invalid"), ("account", "warn"),
                  ("api", "invalid_grant"), ("api", "permission_denied"), ("api", "unknown")}
    for language in ("en", "de", "pl"):
        catalog = load_catalog(language)
        for check_id, options in states.items():
            for state in options:
                assert f"doctor.{check_id}.{state}" in catalog, (language, check_id, state)
                if (check_id, state) in needs_next:
                    assert f"doctor.{check_id}.{state}.next" in catalog, (language, check_id, state)
        for status in ("ok", "warn", "fail", "skip"):
            assert f"doctor.status.{status}" in catalog


@pytest.mark.parametrize("language", ("de", "pl", "en"))
def test_rendered_text_is_localized_and_never_contains_secrets(tmp_path, language):
    home = _profile(tmp_path)
    checks, _ = run_doctor({"TEST_ONLY": SECRET}, home=home, which=_which(ALL_TOOLS), python_version=(3, 12))
    text = render_text(checks, Translator(language))
    assert SECRET not in text and "demo-project" not in text and "1234567890" not in text
    assert Translator(language).t("doctor.title") in text
    assert "[en]" not in text


def test_german_and_polish_not_connected_messages(tmp_path):
    checks, _ = run_doctor({}, home=tmp_path / "x", which=_which({}), python_version=(3, 12))
    assert "nicht verbunden" in render_text(checks, Translator("de"))
    assert "nie jest połączone" in render_text(checks, Translator("pl"))


def test_json_result_has_stable_ids_and_no_free_text(tmp_path):
    checks, _ = run_doctor({}, home=_profile(tmp_path), which=_which(ALL_TOOLS), python_version=(3, 12))
    payload = to_json(checks)
    assert payload["connected"] is True and payload["ok"] is True
    assert [c["id"] for c in payload["checks"]] == ["python", "uv", "gcloud", "settings", "project", "credentials", "account", "api"]
    assert set(payload["checks"][0]) == {"id", "status", "state"}


def test_check_next_key_only_for_warn_and_fail():
    assert Check("uv", "ok", "ok").next_key() is None
    assert Check("uv", "warn", "warn").next_key() == "doctor.uv.warn.next"


# --------------------------------------------------------------------------- CLI


@pytest.fixture()
def empty_env(monkeypatch, tmp_path):
    for name in list(os.environ):
        if name.startswith(("GOOGLE_", "ADBOT_")):
            monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    return tmp_path


@pytest.mark.parametrize(("language", "phrase"), [("de", "nicht verbunden"), ("pl", "nie jest połączone")])
def test_cli_doctor_runs_offline_without_connection(empty_env, capsys, language, phrase):
    code = main(["doctor", "--lang", language, "--profile-dir", str(empty_env / "profile")])
    out = capsys.readouterr().out
    assert code == 1  # problems found, but no crash
    assert phrase in out


def test_cli_doctor_json(empty_env, capsys):
    code = main(["doctor", "--json", "--profile-dir", str(empty_env / "profile")])
    payload = json.loads(capsys.readouterr().out)
    assert code == 1 and payload["connected"] is False and payload["ok"] is False


def test_cli_doctor_uses_settings_language_when_no_option_given(empty_env, capsys):
    profile = empty_env / "profile"
    save_settings(profile / SETTINGS_FILENAME, default_settings("pl"))
    main(["doctor", "--profile-dir", str(profile)])
    assert "Kontrola Adbot" in capsys.readouterr().out
