"""Tests for the daily job planner and the scheduler (no network, no real scheduler calls)."""
from __future__ import annotations

import json
import plistlib
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import run_daily_watch  # noqa: E402
import schedule_watch  # noqa: E402

NOW = datetime(2026, 11, 2, 6, 0, tzinfo=timezone.utc)


def test_plan_pulls_14_days_read_only_and_never_names_a_mutation(tmp_path):
    steps = run_daily_watch.plan("1234567890", NOW, tmp_path, None)
    campaign = steps["campaign"]
    assert "gaql_via_api.py" in " ".join(campaign) and run_daily_watch.CLIENT_PIN in campaign
    assert "segments.date BETWEEN '2026-10-19' AND '2026-11-01'" in campaign
    flat = " ".join(map(str, [steps["campaign"], steps["policy"], steps["watch"]])).lower()
    assert "mutate" not in flat and "gaql_via_mcp" not in flat
    assert steps["watch"][1:3] == ["-m", "claude_ads_core"]
    assert str(steps["campaign_out"]).startswith(str(tmp_path))


def test_dry_run_prints_the_commands_without_running_anything(tmp_path, capsys):
    from claude_ads_core.user_settings import SETTINGS_FILENAME, default_settings, save_settings

    profile = tmp_path / "profile"
    settings = default_settings("de")
    settings["active_account_ref"] = "1234567890"
    save_settings(profile / SETTINGS_FILENAME, settings)
    assert run_daily_watch.main(["--profile-dir", str(profile), "--runs-dir", str(tmp_path / "runs"), "--dry-run"]) == 0
    printed = json.loads(capsys.readouterr().out)
    assert {"campaign", "policy", "watch"} <= set(printed)
    assert not (tmp_path / "runs").exists()


def test_job_stops_cleanly_when_watch_is_off_or_no_account(tmp_path, capsys):
    from claude_ads_core.user_settings import SETTINGS_FILENAME, default_settings, save_settings

    profile = tmp_path / "profile"
    settings = default_settings("pl")
    save_settings(profile / SETTINGS_FILENAME, settings)
    assert run_daily_watch.main(["--profile-dir", str(profile), "--dry-run"]) == 2  # no account
    assert "no active account" in capsys.readouterr().err
    settings["cadence"]["watch"] = "off"
    save_settings(profile / SETTINGS_FILENAME, settings)
    assert run_daily_watch.main(["--profile-dir", str(profile), "--dry-run"]) == 0
    assert "skipped" in capsys.readouterr().out


def test_job_without_settings_fails_loudly(tmp_path, capsys):
    assert run_daily_watch.main(["--profile-dir", str(tmp_path / "none"), "--dry-run"]) == 2
    assert "settings" in capsys.readouterr().err


# ------------------------------------------------------------------ scheduler


@pytest.mark.parametrize(("value", "expected"), [("07:30", (7, 30)), ("7:05", (7, 5)), ("23:59", (23, 59))])
def test_parse_time(value, expected):
    assert schedule_watch.parse_time(value) == expected


@pytest.mark.parametrize("value", ["24:00", "7", "07:60", "abc", ""])
def test_parse_time_rejects_bad_values(value):
    with pytest.raises(Exception):
        schedule_watch.parse_time(value)


def test_launchd_plist_runs_only_the_daily_job(tmp_path):
    data = plistlib.loads(schedule_watch.launchd_plist(7, 30, tmp_path))
    assert data["Label"] == "de.adbot.watch"
    assert data["StartCalendarInterval"] == {"Hour": 7, "Minute": 30}
    assert data["ProgramArguments"][-1].endswith("run_daily_watch.py")
    assert data["RunAtLoad"] is False


def test_windows_command_creates_a_daily_task():
    command = schedule_watch.windows_create_command(7, 5)
    assert command[:2] == ["schtasks", "/Create"] and "DAILY" in command and "07:05" in command and "/F" in command


def test_install_and_remove_on_macos_are_idempotent(tmp_path):
    calls = []

    def runner(command):
        calls.append(list(command))
        return 0, ""

    first = schedule_watch.install("darwin", 7, 30, tmp_path, runner, uid=501)
    assert (tmp_path / "Library" / "LaunchAgents" / "de.adbot.watch.plist").is_file() and "loaded the job" in first
    assert calls[0][:2] == ["launchctl", "bootout"] and calls[1][:2] == ["launchctl", "bootstrap"]
    removed = schedule_watch.remove("darwin", tmp_path, runner, uid=501)
    assert removed == ["deleted de.adbot.watch.plist"]
    again = schedule_watch.remove("darwin", tmp_path, lambda c: (3, "not loaded"), uid=501)
    assert again == ["nothing was installed"]


def test_windows_install_and_remove_report_failures_clearly(tmp_path):
    assert schedule_watch.install("win32", 7, 30, tmp_path, lambda c: (0, "")) == ["created task AdbotWatch"]
    with pytest.raises(RuntimeError, match="schtasks"):
        schedule_watch.install("win32", 7, 30, tmp_path, lambda c: (1, "access denied"))
    assert schedule_watch.remove("win32", tmp_path, lambda c: (1, "not found")) == ["nothing was installed"]


def test_unsupported_platform_is_rejected(tmp_path):
    with pytest.raises(RuntimeError, match="unsupported"):
        schedule_watch.install("linux", 7, 30, tmp_path, lambda c: (0, ""))


def test_dry_run_never_touches_the_system():
    result = subprocess.run([sys.executable, str(SCRIPTS / "schedule_watch.py"), "--dry-run"], capture_output=True, text=True, check=False)
    assert result.returncode == 0 and "action: install" in result.stdout
