"""Local, secret-free user settings for Adbot: language, market, account reference, cadence.

The settings file lives in the user's profile directory (``$ADBOT_PROFILE_DIR``, default
``~/.config/adbot/standard``), never in the repository.  It contains no credentials; the
active account is referenced by its ten-digit customer ID only.

Market defaults (currency, time zone) are conventions for a new profile.  The account's own
currency and time zone are authoritative and must be read from the account.
"""
from __future__ import annotations

import json
import os
import stat
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .i18n import normalize_language
from .workflow_contracts import WorkflowContractError, validate_workflow_contract

SETTINGS_FILENAME = "settings.json"
DEFAULT_PROFILE_SUBPATH = Path(".config") / "adbot" / "standard"
MARKET_DEFAULTS: dict[str, dict[str, str]] = {
    "de": {"country": "DE", "currency": "EUR", "timezone": "Europe/Berlin"},
    "pl": {"country": "PL", "currency": "PLN", "timezone": "Europe/Warsaw"},
}
DEFAULT_CADENCE: dict[str, str] = {
    "watch": "daily",
    "report": "weekly",
    "report_weekday": "monday",
    "deep_review": "monthly",
}


class SettingsError(ValueError):
    """Raised when settings are missing, invalid, or cannot be written safely."""


def profile_dir(environ: Mapping[str, str] | None = None, home: Path | None = None) -> Path:
    """Return the profile directory from ``ADBOT_PROFILE_DIR`` or the per-user default."""
    env = os.environ if environ is None else environ
    configured = env.get("ADBOT_PROFILE_DIR")
    if configured:
        return Path(configured).expanduser()
    return (home or Path.home()) / DEFAULT_PROFILE_SUBPATH


def default_settings(language: str, now: datetime | None = None) -> dict[str, Any]:
    """Return valid default settings for a new profile in *language* (``de`` or ``pl``)."""
    code = normalize_language(language)
    if code not in MARKET_DEFAULTS:
        raise SettingsError("settings support the languages 'de' and 'pl' only")
    stamp = (now or datetime.now(timezone.utc)).astimezone(timezone.utc).replace(microsecond=0)
    return {
        "schema_version": "1.0.0",
        "artifact_type": "user-settings",
        "updated_at": stamp.isoformat().replace("+00:00", "Z"),
        "language": code,
        **MARKET_DEFAULTS[code],
        "active_account_ref": None,
        "disk_encryption_attested_on": None,
        "cadence": dict(DEFAULT_CADENCE),
    }


def validate_settings(document: Any) -> dict[str, Any]:
    """Validate *document* against the ``user-settings`` contract and return it."""
    try:
        validate_workflow_contract("user-settings", document)
    except WorkflowContractError as exc:
        raise SettingsError(f"invalid settings: {exc}") from exc
    return document


def load_settings(path: str | Path) -> dict[str, Any]:
    """Load and validate a settings file; fails loudly when it is missing or malformed."""
    target = Path(path)
    try:
        document = json.loads(target.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SettingsError(f"settings file not found: {target.name} (run the start command first)") from exc
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SettingsError(f"cannot read settings {target.name}: {exc}") from exc
    return validate_settings(document)


def save_settings(path: str | Path, document: Mapping[str, Any]) -> Path:
    """Validate and atomically write *document* with owner-only permissions (0600)."""
    validate_settings(dict(document))
    target = Path(path)
    if target.is_symlink():
        raise SettingsError("settings file must not be a symlink")
    target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor, temporary = tempfile.mkstemp(prefix=".settings-", suffix=".tmp", dir=target.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(document, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
        os.chmod(temporary, stat.S_IRUSR | stat.S_IWUSR)
        os.replace(temporary, target)
    except Exception:
        Path(temporary).unlink(missing_ok=True)
        raise
    return target
