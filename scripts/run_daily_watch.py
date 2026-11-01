#!/usr/bin/env python3
"""Daily job: pull the last 14 days read-only, then run the deterministic watcher.

No AI and no account changes.  Steps:

1. ``gaql_via_api.py`` stores a campaign-by-day envelope (and the ad approval status when ads exist).
2. ``python -m claude_ads_core watch run`` evaluates it into a *new* run directory.
3. ``python -m claude_ads_core cockpit build`` (if available) renders the local overview page.

If the computer was off, the next run simply covers the missing days; the cockpit shows the data gap.
Usage:  python scripts/run_daily_watch.py [--profile-dir DIR] [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
CLIENT_PIN = "google-ads==35.0.0"
CAMPAIGN_FIELDS = (
    "segments.date", "customer.id", "customer.currency_code", "campaign.id", "campaign.name", "campaign.status",
    "campaign_budget.amount_micros", "metrics.cost_micros", "metrics.clicks", "metrics.impressions", "metrics.conversions",
)
POLICY_FIELDS = ("customer.id", "campaign.id", "ad_group_ad.policy_summary.approval_status")


def pull_command(customer: str, resource: str, fields: Sequence[str], conditions: Sequence[str], query_id: str, out: Path) -> list[str]:
    """Argument vector for one read-only pull (no shell)."""
    command = ["uv", "run", "--no-project", "--with", CLIENT_PIN, str(ROOT / "scripts" / "gaql_via_api.py"),
               "--customer", customer, "--resource", resource, "--fields", *fields]
    if conditions:
        command += ["--conditions", *conditions]
    return command + ["--query-id", query_id, "--out", str(out)]


def plan(customer: str, today: datetime, runs_dir: Path, profile_dir: Path | None) -> dict[str, list[str] | Path]:
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
        "stage": stage, "campaign_out": campaign_out, "policy_out": policy_out,
        "campaign": pull_command(customer, "campaign", CAMPAIGN_FIELDS,
                                 [f"segments.date BETWEEN '{start}' AND '{end}'"], "campaign-daily-v1", campaign_out),
        "policy": pull_command(customer, "ad_group_ad", POLICY_FIELDS, ["campaign.status = 'ENABLED'"], "ad-policy-v1", policy_out),
        "watch": watch,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--profile-dir", default=None)
    parser.add_argument("--runs-dir", default=str(ROOT / ".adbot" / "runs"))
    parser.add_argument("--dry-run", action="store_true", help="print the commands and stop")
    args = parser.parse_args(argv)

    env = dict(os.environ)
    if args.profile_dir:
        env["ADBOT_PROFILE_DIR"] = args.profile_dir
    sys.path.insert(0, str(ROOT))
    from claude_ads_core.user_settings import SETTINGS_FILENAME, SettingsError, load_settings, profile_dir

    directory = Path(args.profile_dir).expanduser() if args.profile_dir else profile_dir(env)
    try:
        settings = load_settings(directory / SETTINGS_FILENAME)
    except SettingsError as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}), file=sys.stderr)
        return 2
    if settings["cadence"]["watch"] == "off":
        print(json.dumps({"status": "skipped", "reason": "watch is switched off in the settings"}))
        return 0
    customer = settings["active_account_ref"]
    if not customer:
        print(json.dumps({"status": "failed", "error": "no active account in the settings"}), file=sys.stderr)
        return 2

    steps = plan(customer, datetime.now(timezone.utc), Path(args.runs_dir), directory)
    if args.dry_run:
        print(json.dumps({k: (v if isinstance(v, list) else str(v)) for k, v in steps.items()}, indent=2))
        return 0
    Path(steps["stage"]).mkdir(parents=True, exist_ok=True)
    code = subprocess.run(steps["campaign"], env=env, check=False).returncode  # type: ignore[arg-type]
    if code != 0:
        print(json.dumps({"status": "failed", "error": "campaign data could not be read", "exit": code}), file=sys.stderr)
        return code
    policy_code = subprocess.run(steps["policy"], env=env, check=False).returncode  # type: ignore[arg-type]
    watch = list(steps["watch"])  # type: ignore[arg-type]
    if policy_code != 0:
        # No ads or no access to the policy view: the watcher reports "ad approval status" as a missing input.
        watch = [part for index, part in enumerate(watch) if part != "--policy" and (index == 0 or watch[index - 1] != "--policy")]
    return subprocess.run(watch, env=env, check=False).returncode


if __name__ == "__main__":
    sys.exit(main())
