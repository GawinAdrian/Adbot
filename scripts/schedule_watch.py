#!/usr/bin/env python3
"""Install or remove the daily watcher job (macOS launchd, Windows Task Scheduler).

The job only runs ``scripts/run_daily_watch.py``: read-only pulls plus the deterministic watcher.
Nothing is installed with ``--dry-run``.  ``--remove`` is idempotent.  If the computer is off at the
scheduled time, the run is skipped; the next run covers the missing days (it pulls 14 days) and the cockpit
reports the data gap.  No platform behaviour for missed runs is assumed.

  python scripts/schedule_watch.py --dry-run
  python scripts/schedule_watch.py --time 07:30
  python scripts/schedule_watch.py --remove
"""
from __future__ import annotations

import argparse
import os
import plistlib
import re
import subprocess
import sys
from pathlib import Path
from typing import Callable, Sequence

ROOT = Path(__file__).resolve().parents[1]
LABEL = "de.adbot.watch"
TASK_NAME = "AdbotWatch"
Runner = Callable[[Sequence[str]], "tuple[int, str]"]


def parse_time(value: str) -> tuple[int, int]:
    match = re.fullmatch(r"([01]?\d|2[0-3]):([0-5]\d)", value)
    if not match:
        raise argparse.ArgumentTypeError("time must look like 07:30")
    return int(match.group(1)), int(match.group(2))


def job_arguments() -> list[str]:
    return [sys.executable, str(ROOT / "scripts" / "run_daily_watch.py")]


def launchd_plist(hour: int, minute: int, log_dir: Path) -> bytes:
    """Return the launchd property list for the daily job."""
    return plistlib.dumps({
        "Label": LABEL,
        "ProgramArguments": job_arguments(),
        "WorkingDirectory": str(ROOT),
        "StartCalendarInterval": {"Hour": hour, "Minute": minute},
        "StandardOutPath": str(log_dir / "watch.log"),
        "StandardErrorPath": str(log_dir / "watch.err.log"),
        "RunAtLoad": False,
        # launchd starts jobs with a minimal PATH; uv usually lives in one of these folders.
        "EnvironmentVariables": {"PATH": ":".join((str(Path.home() / ".local" / "bin"), "/opt/homebrew/bin", "/usr/local/bin", "/usr/bin", "/bin"))},
    })


def windows_create_command(hour: int, minute: int) -> list[str]:
    quoted = " ".join(f'"{part}"' for part in job_arguments())
    return ["schtasks", "/Create", "/SC", "DAILY", "/TN", TASK_NAME, "/TR", quoted, "/ST", f"{hour:02d}:{minute:02d}", "/F"]


def _run(command: Sequence[str]) -> tuple[int, str]:
    result = subprocess.run(list(command), capture_output=True, text=True, check=False)  # noqa: S603
    return result.returncode, (result.stderr or result.stdout).strip()


def install(platform: str, hour: int, minute: int, home: Path, runner: Runner = _run, uid: int | None = None) -> list[str]:
    """Install the job; returns a short list of actions taken."""
    if platform == "darwin":
        agents = home / "Library" / "LaunchAgents"
        log_dir = home / ".config" / "adbot" / "logs"
        agents.mkdir(parents=True, exist_ok=True)
        log_dir.mkdir(parents=True, exist_ok=True)
        plist = agents / f"{LABEL}.plist"
        plist.write_bytes(launchd_plist(hour, minute, log_dir))
        domain = f"gui/{uid if uid is not None else os.getuid()}"
        runner(["launchctl", "bootout", f"{domain}/{LABEL}"])  # replace an existing job; ignore "not loaded"
        code, message = runner(["launchctl", "bootstrap", domain, str(plist)])
        if code != 0:
            raise RuntimeError(f"launchctl could not load the job: {message}")
        return [f"wrote {plist.name}", "loaded the job"]
    if platform == "win32":
        code, message = runner(windows_create_command(hour, minute))
        if code != 0:
            raise RuntimeError(f"schtasks could not create the task: {message}")
        return [f"created task {TASK_NAME}"]
    raise RuntimeError(f"unsupported platform {platform!r}; run scripts/run_daily_watch.py by hand")


def remove(platform: str, home: Path, runner: Runner = _run, uid: int | None = None) -> list[str]:
    """Remove the job; safe to call when nothing is installed."""
    actions: list[str] = []
    if platform == "darwin":
        domain = f"gui/{uid if uid is not None else os.getuid()}"
        runner(["launchctl", "bootout", f"{domain}/{LABEL}"])
        plist = home / "Library" / "LaunchAgents" / f"{LABEL}.plist"
        if plist.exists():
            plist.unlink()
            actions.append(f"deleted {plist.name}")
    elif platform == "win32":
        code, _ = runner(["schtasks", "/Delete", "/TN", TASK_NAME, "/F"])
        if code == 0:
            actions.append(f"deleted task {TASK_NAME}")
    else:
        raise RuntimeError(f"unsupported platform {platform!r}")
    return actions or ["nothing was installed"]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--time", type=parse_time, default=(7, 30), help="local time HH:MM (default 07:30)")
    parser.add_argument("--remove", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    hour, minute = args.time
    if args.dry_run:
        print(f"platform: {sys.platform}\njob: {' '.join(job_arguments())}\ntime: {hour:02d}:{minute:02d}\naction: "
              + ("remove" if args.remove else "install"))
        return 0
    try:
        actions = remove(sys.platform, Path.home()) if args.remove else install(sys.platform, hour, minute, Path.home())
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print("\n".join(actions))
    return 0


if __name__ == "__main__":
    sys.exit(main())
