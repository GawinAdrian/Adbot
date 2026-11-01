"""Read-only self-diagnosis for a user's Adbot installation (``adbot doctor``).

Every check returns a status and a localized message with the next step.  The doctor never
prints credential values, never writes to the Google Ads account, and works offline unless
``online=True`` is requested.  An unreachable or unconfigured setup is a normal result
("not connected"), not an exception.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Mapping, Sequence

from .i18n import Translator
from .user_settings import SETTINGS_FILENAME, SettingsError, load_settings, profile_dir

MIN_PYTHON = (3, 11)
STATUSES = ("ok", "warn", "fail", "skip")
_STATUS_SYMBOL = {"ok": "✔", "warn": "!", "fail": "✖", "skip": "–"}
_ADC_TYPES = {
    "authorized_user": ("client_id", "client_secret", "refresh_token"),
    "service_account": ("client_email", "private_key"),
}
ApiRunner = Callable[[Sequence[str], Mapping[str, str]], "tuple[int, str]"]


@dataclass(frozen=True)
class Check:
    """One diagnosis line: stable ID, status, and the message state used for the catalog key."""

    id: str
    status: str
    state: str
    params: Mapping[str, str] = field(default_factory=dict)

    def message_key(self) -> str:
        return f"doctor.{self.id}.{self.state}"

    def next_key(self) -> str | None:
        return f"{self.message_key()}.next" if self.status in {"warn", "fail"} else None


def classify_api_error(text: str) -> str:
    """Map raw API/client error text to a message state (``invalid_grant``, ``permission_denied``, ``unknown``)."""
    lowered = text.lower()
    if "invalid_grant" in lowered or "reauth" in lowered or "token has been expired or revoked" in lowered:
        return "invalid_grant"
    if "permission" in lowered and ("denied" in lowered or "not have" in lowered or "doesn't have" in lowered):
        return "permission_denied"
    return "unknown"


def _credentials_state(path: Path) -> str:
    """Return ``ok`` or ``invalid`` for a sign-in file without exposing any value."""
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return "invalid"
    if not isinstance(document, dict):
        return "invalid"
    required = _ADC_TYPES.get(str(document.get("type")))
    if required is None or any(not document.get(key) for key in required):
        return "invalid"
    return "ok"


_PROFILE_KEYS = ("GOOGLE_PROJECT_ID", "GOOGLE_APPLICATION_CREDENTIALS", "GOOGLE_ADS_LOGIN_CUSTOMER_ID")


def _merge_profile_env(path: Path, env: dict[str, str]) -> None:
    """Fill missing allowed keys in *env* from the profile file; values are never reported."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return
    for line in text.splitlines():
        stripped = line.strip()
        for key in _PROFILE_KEYS:
            if stripped.startswith(f"{key}="):
                value = stripped.split("=", 1)[1].strip().strip("'\"")
                if value and not env.get(key):
                    env[key] = value


def _default_runner(args: Sequence[str], environ: Mapping[str, str]) -> tuple[int, str]:
    result = subprocess.run(  # noqa: S603 - fixed argument vector, no shell
        list(args), capture_output=True, text=True, check=False, env=dict(environ), timeout=120
    )
    return result.returncode, (result.stderr or "") + (result.stdout if result.returncode else "")


def run_doctor(
    environ: Mapping[str, str] | None = None,
    *,
    home: Path | None = None,
    python_version: tuple[int, int] | None = None,
    which: Callable[[str], str | None] = shutil.which,
    online: bool = False,
    runner: ApiRunner = _default_runner,
    scripts_dir: Path | None = None,
) -> tuple[list[Check], dict[str, str]]:
    """Run all checks; returns ``(checks, context)`` where context holds the settings language."""
    env = dict(os.environ if environ is None else environ)
    version = python_version or (sys.version_info.major, sys.version_info.minor)
    checks: list[Check] = []
    context: dict[str, str] = {}

    checks.append(Check("python", "ok" if version >= MIN_PYTHON else "fail",
                        "ok" if version >= MIN_PYTHON else "fail", {"version": f"{version[0]}.{version[1]}"}))
    checks.append(Check("uv", "ok" if which("uv") else "warn", "ok" if which("uv") else "warn"))
    checks.append(Check("gcloud", "ok" if which("gcloud") else "warn", "ok" if which("gcloud") else "warn"))

    directory = profile_dir(env, home)
    settings = None
    try:
        settings = load_settings(directory / SETTINGS_FILENAME)
        context["language"] = settings["language"]
        checks.append(Check("settings", "ok", "ok", {"language": settings["language"]}))
    except SettingsError:
        checks.append(Check("settings", "fail", "fail"))

    _merge_profile_env(directory / "env", env)
    project = env.get("GOOGLE_PROJECT_ID") or env.get("GOOGLE_CLOUD_PROJECT")
    checks.append(Check("project", "ok" if project else "fail", "ok" if project else "fail"))

    explicit = env.get("GOOGLE_APPLICATION_CREDENTIALS")
    adc = Path(explicit) if explicit else (home or Path.home()) / ".config" / "gcloud" / "application_default_credentials.json"
    if not adc.is_file():
        checks.append(Check("credentials", "fail", "fail"))
        credentials_ok = False
    else:
        state = _credentials_state(adc)
        credentials_ok = state == "ok"
        checks.append(Check("credentials", "ok" if credentials_ok else "fail", "ok" if credentials_ok else "invalid"))

    account = settings["active_account_ref"] if settings else None
    checks.append(Check("account", "ok" if account else "warn", "ok" if account else "warn"))

    if not online:
        checks.append(Check("api", "skip", "skip"))
    elif not (project and credentials_ok and account):
        checks.append(Check("api", "skip", "skip"))
    else:
        base = scripts_dir or Path(__file__).resolve().parents[1] / "scripts"
        script = base / "gaql_via_api.py"
        if not script.is_file():
            checks.append(Check("api", "fail", "unknown"))
        else:
            out = Path(env.get("TMPDIR", "/tmp")) / "adbot-doctor-probe.json"
            code, text = runner(
                ["uv", "run", "--no-project", "--with", "google-ads==35.0.0", str(script),
                 "--customer", account, "--resource", "customer", "--fields", "customer.id",
                 "--query-id", "doctor-probe-v1", "--out", str(out)],
                env,
            )
            out.unlink(missing_ok=True)
            checks.append(Check("api", "ok", "ok") if code == 0 else Check("api", "fail", classify_api_error(text)))
    return checks, context


def is_connected(checks: Sequence[Check]) -> bool:
    """True when project and sign-in are present and valid (the account may still be unselected)."""
    by_id = {check.id: check for check in checks}
    return by_id["project"].status == "ok" and by_id["credentials"].status == "ok"


def render_text(checks: Sequence[Check], tr: Translator) -> str:
    """Render checks as plain text in the translator's language; no secret values are included."""
    lines = [tr.t("doctor.title"), ""]
    for check in checks:
        label = tr.t(f"doctor.status.{check.status}")
        lines.append(f"{_STATUS_SYMBOL[check.status]} [{label}] {tr.t(check.message_key(), **check.params)}")
        next_key = check.next_key()
        if next_key:
            lines.append(f"    → {tr.t(next_key)}")
    failures = sum(1 for check in checks if check.status == "fail")
    lines.append("")
    lines.append(tr.t("doctor.summary_fail", count=failures) if failures else tr.t("doctor.summary_ok"))
    lines.append(tr.t("doctor.connected") if is_connected(checks) else tr.t("doctor.not_connected"))
    return "\n".join(lines) + "\n"


def to_json(checks: Sequence[Check]) -> dict[str, object]:
    """Machine-readable result with stable IDs and statuses (no free text, no secrets)."""
    return {
        "connected": is_connected(checks),
        "ok": all(check.status != "fail" for check in checks),
        "checks": [{"id": check.id, "status": check.status, "state": check.state} for check in checks],
    }
