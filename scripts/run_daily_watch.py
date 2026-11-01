#!/usr/bin/env python3
"""Daily job: pull the last 14 days read-only, run the deterministic watcher, build the cockpit.

No AI and no account changes.  Steps:

1. ``gaql_via_api.py`` stores a campaign-by-day envelope (and the ad approval status of active ads).
   If the pull returns no rows (nothing was shown in 14 days, or no campaign exists) the job records a
   yellow "no data" result instead of failing.
2. ``python -m claude_ads_core watch run`` evaluates the data into a *new* run directory.
3. ``python -m claude_ads_core cockpit build`` renders ``cockpit.html`` next to the result.

The job is started by a scheduler with a minimal environment, so it finds ``uv`` itself, runs from the
repository folder, and sets ``PYTHONPATH``.  If the computer was off, the next run pulls the 14 days again
and the watcher reports the data gap.
Usage:  python scripts/run_daily_watch.py [--profile-dir DIR] [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
CLIENT_PIN = "google-ads==35.0.0"
NO_ROWS_EXIT_CODE = 3  # keep in sync with scripts/gaql_via_api.py
CAMPAIGN_FIELDS = (
    "segments.date", "customer.id", "customer.currency_code", "campaign.id", "campaign.name", "campaign.status",
    "campaign_budget.amount_micros", "metrics.cost_micros", "metrics.clicks", "metrics.impressions", "metrics.conversions",
)
POLICY_FIELDS = ("customer.id", "campaign.id", "ad_group_ad.status", "ad_group_ad.policy_summary.approval_status")
# Only ads that can actually be shown: removed or paused ads (or paused groups) must not keep the light red.
POLICY_CONDITIONS = ("campaign.status = 'ENABLED'", "ad_group.status = 'ENABLED'", "ad_group_ad.status = 'ENABLED'")


def tool_path(environ: Mapping[str, str], home: Path | None = None) -> str:
    """PATH that also contains the usual install folders of ``uv`` (schedulers start with a minimal PATH)."""
    base = home or Path.home()
    extra = [base / ".local" / "bin", base / ".cargo" / "bin", Path("/opt/homebrew/bin"), Path("/usr/local/bin")]
    local = environ.get("LOCALAPPDATA")
    if local:
        extra.append(Path(local) / "Programs" / "uv")
    current = environ.get("PATH", "")
    return os.pathsep.join([current, *(str(p) for p in extra)] if current else [str(p) for p in extra])


def find_uv(environ: Mapping[str, str], home: Path | None = None) -> str | None:
    """Absolute path of ``uv`` or None."""
    return shutil.which("uv", path=tool_path(environ, home))


def job_environment(environ: Mapping[str, str], profile_dir: str | None) -> dict[str, str]:
    env = dict(environ)
    env["PATH"] = tool_path(environ)
    env["PYTHONPATH"] = os.pathsep.join([str(ROOT), env["PYTHONPATH"]] if env.get("PYTHONPATH") else [str(ROOT)])
    if profile_dir:
        env["ADBOT_PROFILE_DIR"] = profile_dir
    return env


def pull_command(uv: str, customer: str, resource: str, fields: Sequence[str], conditions: Sequence[str],
                 query_id: str, out: Path) -> list[str]:
    """Argument vector for one read-only pull (no shell)."""
    command = [uv, "run", "--no-project", "--with", CLIENT_PIN, str(ROOT / "scripts" / "gaql_via_api.py"),
               "--customer", customer, "--resource", resource, "--fields", *fields]
    if conditions:
        command += ["--conditions", *conditions]
    return command + ["--query-id", query_id, "--out", str(out)]


def plan(customer: str, today: datetime, runs_dir: Path, profile_dir: Path | None, uv: str = "uv") -> dict[str, object]:
    """Return the commands of one daily run; pure, so it can be tested without a network."""
    end = (today - timedelta(days=1)).date()
    start = end - timedelta(days=13)
    stage = runs_dir / f"pull-{today:%Y%m%d-%H%M%S}" / "live"
    campaign_out, policy_out = stage / "campaign-daily.json", stage / "ad-policy.json"
    watch = [sys.executable, "-m", "claude_ads_core", "watch", "run", "--live", str(campaign_out),
             "--policy", str(policy_out), "--customer", customer, "--out", str(runs_dir)]
    if profile_dir:
        watch += ["--profile-dir", str(profile_dir)]
    return {
        "stage": stage, "campaign_out": campaign_out, "policy_out": policy_out, "window": (start, end),
        "campaign": pull_command(uv, customer, "campaign", CAMPAIGN_FIELDS,
                                 [f"segments.date BETWEEN '{start}' AND '{end}'"], "campaign-daily-v1", campaign_out),
        "policy": pull_command(uv, customer, "ad_group_ad", POLICY_FIELDS, POLICY_CONDITIONS, "ad-policy-v1", policy_out),
        "watch": watch,
    }


def without_policy(watch: Sequence[str]) -> list[str]:
    """The watch command without ``--policy PATH`` (used when no ad status could be read)."""
    result: list[str] = []
    skip = False
    for part in watch:
        if skip:
            skip = False
        elif part == "--policy":
            skip = True
        else:
            result.append(part)
    return result


def _fail(message: str, code: int = 2) -> int:
    print(json.dumps({"status": "failed", "error": message}), file=sys.stderr)
    return code


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--profile-dir", default=None)
    parser.add_argument("--runs-dir", default=str(ROOT / ".adbot" / "runs"))
    parser.add_argument("--dry-run", action="store_true", help="print the commands and stop")
    args = parser.parse_args(argv)

    env = job_environment(os.environ, args.profile_dir)
    sys.path.insert(0, str(ROOT))
    from claude_ads_core.user_settings import SETTINGS_FILENAME, SettingsError, load_settings, profile_dir
    from claude_ads_core.watch import empty_result, store_result

    directory = Path(args.profile_dir).expanduser() if args.profile_dir else profile_dir(env)
    try:
        settings = load_settings(directory / SETTINGS_FILENAME)
    except SettingsError as exc:
        return _fail(str(exc))
    if settings["cadence"]["watch"] == "off":
        print(json.dumps({"status": "skipped", "reason": "watch is switched off in the settings"}))
        return 0
    customer = settings["active_account_ref"]
    if not customer:
        return _fail("no active account in the settings")
    uv = find_uv(env)
    if not uv and not args.dry_run:
        return _fail("the tool uv was not found; install it (docs/de/01-install.md) and run again")

    now = datetime.now(timezone.utc)
    steps = plan(customer, now, Path(args.runs_dir), directory, uv or "uv")
    if args.dry_run:
        print(json.dumps({k: (list(map(str, v)) if isinstance(v, (list, tuple)) else str(v)) for k, v in steps.items()}, indent=2))
        return 0
    stage = Path(steps["stage"])  # type: ignore[arg-type]
    stage.mkdir(parents=True, exist_ok=True, mode=0o700)
    run = lambda command: subprocess.run(list(command), env=env, cwd=ROOT, check=False, capture_output=True, text=True)  # noqa: E731
    pulled = run(steps["campaign"])  # type: ignore[arg-type]
    if pulled.returncode == NO_ROWS_EXIT_CODE:
        start, end = steps["window"]  # type: ignore[misc]
        result = empty_result(as_of=now.date(), currency=settings["currency"], query_id="campaign-daily-v1",
                              window_start=start, window_end=end)
        stored = store_result(result, out_dir=args.runs_dir, attested_on=None, timezone_name=settings["timezone"], now=now)
        print(json.dumps({"status": "no-data", **stored}))
        result_path = stored["result"]
    elif pulled.returncode != 0:
        print(pulled.stderr[-400:], file=sys.stderr)
        return _fail("campaign data could not be read", pulled.returncode)
    else:
        policy = run(steps["policy"])  # type: ignore[arg-type]
        command = list(steps["watch"])  # type: ignore[arg-type]
        if policy.returncode != 0:  # no active ads or no access: the watcher lists "ad approval status" as missing
            command = without_policy(command)
        watched = run(command)
        if watched.returncode != 0:
            print(watched.stderr[-400:], file=sys.stderr)
            return _fail("the watcher failed", watched.returncode)
        print(watched.stdout.strip())
        result_path = json.loads(watched.stdout)["result"]
    cockpit = [sys.executable, "-m", "claude_ads_core", "cockpit", "build", "--watch-result", result_path, "--profile-dir", str(directory)]
    built = run(cockpit)
    if built.returncode != 0:
        print(built.stderr[-400:], file=sys.stderr)
        return _fail("the cockpit could not be built", built.returncode)
    print(built.stdout.strip())
    return 0


if __name__ == "__main__":
    sys.exit(main())
