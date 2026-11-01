"""Tests for the secret-free user settings contract, storage, and CLI."""
from __future__ import annotations

import copy
import json
import os
import stat
from datetime import datetime, timezone
from pathlib import Path

import pytest

from claude_ads_core.cli import main
from claude_ads_core.user_settings import (
    SETTINGS_FILENAME,
    SettingsError,
    default_settings,
    load_settings,
    profile_dir,
    save_settings,
    validate_settings,
)

FIXED = datetime(2026, 11, 1, 8, 0, tzinfo=timezone.utc)


@pytest.mark.parametrize(
    ("language", "country", "currency", "timezone_name"),
    [("de", "DE", "EUR", "Europe/Berlin"), ("pl", "PL", "PLN", "Europe/Warsaw")],
)
def test_default_settings_are_valid_per_language(language, country, currency, timezone_name):
    settings = default_settings(language, FIXED)
    assert validate_settings(settings) is settings
    assert (settings["country"], settings["currency"], settings["timezone"]) == (country, currency, timezone_name)
    assert settings["updated_at"] == "2026-11-01T08:00:00Z"
    assert settings["active_account_ref"] is None


def test_default_settings_reject_unsupported_languages():
    with pytest.raises(SettingsError):
        default_settings("en")
    with pytest.raises(Exception):
        default_settings("fr")


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: d.update(language="en"),
        lambda d: d.update(country="AT"),
        lambda d: d.update(currency="eur"),
        lambda d: d.update(timezone="Berlin"),
        lambda d: d.update(active_account_ref="123-456-7890"),
        lambda d: d.update(unexpected="x"),
        lambda d: d["cadence"].update(report="hourly"),
        lambda d: d["cadence"].pop("watch"),
        lambda d: d.pop("language"),
        lambda d: d.update(updated_at="yesterday"),
        lambda d: d.update(api_token="abc"),  # secrets have no place in the contract
    ],
)
def test_invalid_settings_fail_closed(mutate):
    settings = copy.deepcopy(default_settings("de", FIXED))
    mutate(settings)
    with pytest.raises(SettingsError):
        validate_settings(settings)


def test_save_and_load_roundtrip_with_owner_only_permissions(tmp_path):
    target = tmp_path / "profile" / SETTINGS_FILENAME
    settings = default_settings("pl", FIXED)
    settings["active_account_ref"] = "1234567890"
    save_settings(target, settings)
    assert load_settings(target) == settings
    if os.name == "posix":
        assert stat.S_IMODE(target.stat().st_mode) == 0o600
        assert stat.S_IMODE(target.parent.stat().st_mode) == 0o700
    assert not list(target.parent.glob(".settings-*.tmp"))


def test_save_refuses_invalid_data_and_symlinks(tmp_path):
    target = tmp_path / SETTINGS_FILENAME
    bad = default_settings("de", FIXED)
    bad["language"] = "xx"
    with pytest.raises(SettingsError):
        save_settings(target, bad)
    assert not target.exists()
    real = tmp_path / "real.json"
    real.write_text("{}")
    link = tmp_path / "link.json"
    link.symlink_to(real)
    with pytest.raises(SettingsError, match="symlink"):
        save_settings(link, default_settings("de", FIXED))


def test_load_fails_loudly_for_missing_and_broken_files(tmp_path):
    with pytest.raises(SettingsError, match="not found"):
        load_settings(tmp_path / SETTINGS_FILENAME)
    broken = tmp_path / "broken.json"
    broken.write_text("{not json")
    with pytest.raises(SettingsError, match="cannot read"):
        load_settings(broken)


def test_profile_dir_prefers_environment(tmp_path):
    assert profile_dir({"ADBOT_PROFILE_DIR": str(tmp_path)}) == tmp_path
    assert profile_dir({}, home=tmp_path) == tmp_path / ".config" / "adbot" / "standard"


def test_cli_settings_init_show_and_overwrite_guard(tmp_path, capsys):
    base = ["settings", "init", "--lang", "pl", "--profile-dir", str(tmp_path)]
    assert main(base) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "created"
    assert main(["settings", "show", "--profile-dir", str(tmp_path)]) == 0
    shown = json.loads(capsys.readouterr().out)
    assert shown["language"] == "pl" and shown["currency"] == "PLN"
    assert main(base) == 2
    assert "already exist" in capsys.readouterr().err
    assert main(base + ["--force"]) == 0


def test_cli_settings_show_without_file_reports_clear_error(tmp_path, capsys):
    assert main(["settings", "show", "--profile-dir", str(tmp_path)]) == 2
    assert "not found" in capsys.readouterr().err


def test_cli_settings_set_updates_selected_values_and_validates(tmp_path, capsys):
    base = ["--profile-dir", str(tmp_path)]
    assert main(["settings", "init", "--lang", "de", *base]) == 0
    capsys.readouterr()
    assert main(["settings", "set", *base, "--account", "123-456-7890", "--report", "monthly", "--weekday", "friday"]) == 0
    capsys.readouterr()
    main(["settings", "show", *base])
    shown = json.loads(capsys.readouterr().out)
    assert shown["active_account_ref"] == "1234567890"
    assert shown["cadence"]["report"] == "monthly" and shown["cadence"]["report_weekday"] == "friday"
    assert main(["settings", "set", *base, "--account", "none"]) == 0
    capsys.readouterr()
    main(["settings", "show", *base])
    assert json.loads(capsys.readouterr().out)["active_account_ref"] is None


def test_cli_settings_set_rejects_a_malformed_account_id(tmp_path, capsys):
    base = ["--profile-dir", str(tmp_path)]
    main(["settings", "init", "--lang", "pl", *base])
    capsys.readouterr()
    assert main(["settings", "set", *base, "--account", "12345"]) == 2
    assert "invalid settings" in capsys.readouterr().err


def test_a_future_disk_encryption_date_is_refused():
    settings = default_settings("de", FIXED)
    settings["disk_encryption_attested_on"] = "2099-01-01"
    with pytest.raises(SettingsError, match="future"):
        validate_settings(settings)
    settings["disk_encryption_attested_on"] = "2026-11-01"
    assert validate_settings(settings)
