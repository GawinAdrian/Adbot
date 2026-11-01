"""Tests for the daily job planner and the scheduler (no network, no real scheduler calls)."""
from __future__ import annotations

import json
import os
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


# ------------------------------------------------- regressions from the independent review


def test_tool_path_contains_the_usual_uv_folders_for_a_minimal_scheduler_environment(tmp_path):
    path = run_daily_watch.tool_path({"PATH": "/usr/bin:/bin"}, home=tmp_path)
    assert str(tmp_path / ".local" / "bin") in path and "/opt/homebrew/bin" in path and path.startswith("/usr/bin:/bin")


def test_find_uv_uses_the_extended_path(tmp_path):
    home = tmp_path / "home"
    (home / ".local" / "bin").mkdir(parents=True)
    fake = home / ".local" / "bin" / "uv"
    fake.write_text("#!/bin/sh\n")
    fake.chmod(0o755)
    assert run_daily_watch.find_uv({"PATH": "/usr/bin:/bin"}, home=home) == str(fake)


def test_job_environment_sets_pythonpath_and_keeps_the_profile(tmp_path):
    env = run_daily_watch.job_environment({"PATH": "/usr/bin"}, str(tmp_path))
    assert env["PYTHONPATH"].split(os.pathsep)[0] == str(run_daily_watch.ROOT)
    assert env["ADBOT_PROFILE_DIR"] == str(tmp_path)


def test_policy_pull_only_looks_at_ads_that_can_be_shown(tmp_path):
    steps = run_daily_watch.plan("1234567890", NOW, tmp_path, None)
    command = steps["policy"]
    conditions = command[command.index("--conditions") + 1: command.index("--query-id")]
    assert {"campaign.status = 'ENABLED'", "ad_group.status = 'ENABLED'", "ad_group_ad.status = 'ENABLED'"} <= set(conditions)


def test_without_policy_removes_the_option_and_its_value():
    command = ["py", "-m", "x", "--live", "a.json", "--policy", "p.json", "--customer", "1"]
    assert run_daily_watch.without_policy(command) == ["py", "-m", "x", "--live", "a.json", "--customer", "1"]


def test_launchd_plist_sets_a_path_that_finds_uv(tmp_path):
    data = plistlib.loads(schedule_watch.launchd_plist(7, 30, tmp_path))
    assert "/opt/homebrew/bin" in data["EnvironmentVariables"]["PATH"]


def _profile(tmp_path, language="de"):
    from claude_ads_core.user_settings import SETTINGS_FILENAME, default_settings, save_settings

    profile = tmp_path / "profile"
    settings = default_settings(language)
    settings["active_account_ref"] = "1234567890"
    save_settings(profile / SETTINGS_FILENAME, settings)
    return profile


def test_job_runs_end_to_end_with_stubbed_pulls_and_builds_the_cockpit(tmp_path, monkeypatch, capsys):
    """The two pulls are stubbed with fixtures; the real watcher and cockpit run."""
    import shutil

    fixtures = Path(__file__).resolve().parents[1] / "fixtures" / "watch"
    profile = _profile(tmp_path)
    real_run = subprocess.run

    def fake_run(command, **kwargs):
        command = list(command)
        if "gaql_via_api.py" in " ".join(command):
            out = Path(command[command.index("--out") + 1])
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(fixtures / ("healthy.json" if "campaign-daily-v1" in command else "policy-ok.json"), out)
            return subprocess.CompletedProcess(command, 0, "", "")
        return real_run(command, **kwargs)

    monkeypatch.setattr(run_daily_watch.subprocess, "run", fake_run)
    monkeypatch.setattr(run_daily_watch, "find_uv", lambda env, home=None: "/fake/uv")
    assert run_daily_watch.main(["--profile-dir", str(profile), "--runs-dir", str(tmp_path / "runs")]) == 0
    assert '"status": "built"' in capsys.readouterr().out
    cockpits = list((tmp_path / "runs").glob("watch-*/cockpit.html"))
    assert len(cockpits) == 1 and "Adbot-Cockpit" in cockpits[0].read_text(encoding="utf-8")


def test_an_empty_pull_is_recorded_as_a_yellow_result_not_a_crash(tmp_path, monkeypatch):
    profile = _profile(tmp_path, "pl")
    real_run = subprocess.run

    def fake_run(command, **kwargs):
        if "gaql_via_api.py" in " ".join(map(str, command)):
            return subprocess.CompletedProcess(command, run_daily_watch.NO_ROWS_EXIT_CODE, "", "no rows")
        return real_run(command, **kwargs)

    monkeypatch.setattr(run_daily_watch.subprocess, "run", fake_run)
    monkeypatch.setattr(run_daily_watch, "find_uv", lambda env, home=None: "/fake/uv")
    assert run_daily_watch.main(["--profile-dir", str(profile), "--runs-dir", str(tmp_path / "runs")]) == 0
    stored = json.loads(next((tmp_path / "runs").glob("watch-*/watch-result.json")).read_text(encoding="utf-8"))
    assert stored["ampel"] == "yellow" and stored["checks"][0]["state"] == "empty"
    assert next((tmp_path / "runs").glob("watch-*/cockpit.html")).is_file()


def test_a_real_pull_failure_is_not_hidden_as_no_data(tmp_path, monkeypatch, capsys):
    profile = _profile(tmp_path)
    monkeypatch.setattr(run_daily_watch.subprocess, "run", lambda command, **kw: subprocess.CompletedProcess(command, 1, "", "invalid_grant"))
    monkeypatch.setattr(run_daily_watch, "find_uv", lambda env, home=None: "/fake/uv")
    assert run_daily_watch.main(["--profile-dir", str(profile), "--runs-dir", str(tmp_path / "runs")]) == 1
    assert "could not be read" in capsys.readouterr().err
    assert not list((tmp_path / "runs").glob("watch-*"))


def test_missing_uv_fails_clearly(tmp_path, monkeypatch, capsys):
    profile = _profile(tmp_path)
    monkeypatch.setattr(run_daily_watch, "find_uv", lambda env, home=None: None)
    assert run_daily_watch.main(["--profile-dir", str(profile), "--runs-dir", str(tmp_path / "r")]) == 2
    assert "uv was not found" in capsys.readouterr().err
