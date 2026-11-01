"""Shared, dependency-free credential and client-config helpers for Adbot's Google scripts.

Rules enforced here:

* Secret *values* are never printed or returned in messages; only key names are reported.
* The developer token is optional.  Google sunset developer tokens on 2026-09-09; access
  levels are tied to the Google Cloud project.  The ``google-ads`` client accepts a
  configuration without a token since 32.0.0 (checked 2026-11-01).  If a token is set it is
  still passed through, because older client versions require it.
* Values come from the process environment first, then from a profile file
  (``$ADBOT_PROFILE_DIR/env``), then from a git-ignored ``.env`` in the repository root.
"""
from __future__ import annotations

from pathlib import Path
from typing import Mapping, MutableMapping

ENV_KEYS: tuple[str, ...] = (
    "GOOGLE_PROJECT_ID",
    "GOOGLE_ADS_DEVELOPER_TOKEN",
    "DEVELOPER_TOKEN",
    "GOOGLE_ADS_LOGIN_CUSTOMER_ID",
    "GOOGLE_APPLICATION_CREDENTIALS",
)
PROFILE_ENV_NAME = "env"


class CredentialsError(Exception):
    """Raised when required credentials or configuration are missing or invalid."""


def parse_env_text(text: str, keys: tuple[str, ...] = ENV_KEYS) -> dict[str, str]:
    """Return the allowed ``KEY=value`` pairs from ``text``; the last occurrence wins."""
    values: dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        for key in keys:
            if stripped.startswith(f"{key}="):
                value = stripped.split("=", 1)[1].strip().strip("'\"")
                if value:
                    values[key] = value
    return values


def load_env(root: Path, environ: MutableMapping[str, str]) -> list[str]:
    """Fill missing ``ENV_KEYS`` in ``environ`` from the profile file and ``root/.env``.

    Returns the names (never the values) of the keys that were filled in.
    """
    sources: list[Path] = []
    profile_dir = environ.get("ADBOT_PROFILE_DIR")
    if profile_dir:
        sources.append(Path(profile_dir).expanduser() / PROFILE_ENV_NAME)
    sources.append(root / ".env")
    loaded: list[str] = []
    for source in sources:
        if not source.is_file():
            continue
        for key, value in parse_env_text(source.read_text(encoding="utf-8")).items():
            if not environ.get(key):
                environ[key] = value
                loaded.append(key)
    return loaded


def developer_token(environ: Mapping[str, str]) -> str | None:
    """Return the developer token if one is set; it is optional since 2026-09-09."""
    return environ.get("GOOGLE_ADS_DEVELOPER_TOKEN") or environ.get("DEVELOPER_TOKEN") or None


def adc_path(environ: Mapping[str, str], home: Path | None = None) -> Path:
    """Return the Application Default Credentials file; fail loudly when it is missing."""
    explicit = environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    path = Path(explicit) if explicit else (home or Path.home()) / ".config" / "gcloud" / "application_default_credentials.json"
    if not path.is_file():
        raise CredentialsError(
            f"credentials file missing: {path.name} "
            "(run: gcloud auth application-default login)"
        )
    return path


def require_project(environ: Mapping[str, str]) -> str:
    """Return the Google Cloud project ID; fail loudly when it is not set."""
    project = environ.get("GOOGLE_PROJECT_ID") or environ.get("GOOGLE_CLOUD_PROJECT")
    if not project:
        raise CredentialsError("GOOGLE_PROJECT_ID is not set (profile env file or environment)")
    return project


def resolve_login_customer_id(flag: str | None, environ: Mapping[str, str]) -> str | None:
    """Manager (MCC) ID from the flag, else ``GOOGLE_ADS_LOGIN_CUSTOMER_ID``; None for direct access."""
    value = flag or environ.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID") or None
    if value is None:
        return None
    digits = value.replace("-", "")
    if not (len(digits) == 10 and digits.isdigit()):
        raise CredentialsError("the manager (login) customer ID must be a 10-digit Google Ads customer ID")
    return digits


def build_client_config(
    environ: Mapping[str, str], login_customer_id: str | None = None
) -> dict[str, object]:
    """Build the ``GoogleAdsClient.load_from_dict`` configuration.

    ``developer_token`` is included only when the user set one.
    """
    config: dict[str, object] = {
        "use_proto_plus": True,
        "use_application_default_credentials": True,
    }
    token = developer_token(environ)
    if token:
        config["developer_token"] = token
    if login_customer_id:
        config["login_customer_id"] = login_customer_id
    return config
