"""Tenant registry: one validated profile per client beneath the local state root.

A tenant profile binds advertising accounts to objectives, KPIs, budget
ceilings, approvers, reporting cadence, and a data-lifecycle contract.  The
registry keeps profiles on the local filesystem (never in the repository),
writes them atomically with owner-only permissions, refuses symlinked paths,
and guarantees that every ``(platform, account_id)`` pair belongs to exactly
one tenant so runs, findings, and future mutation plans can always be scoped.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from .workflow_contracts import WorkflowContractError, validate_workflow_contract

DEFAULT_TENANT_ROOT = ".claude-ads/tenants"
PROFILE_FILENAME = "profile.json"
_TENANT_ID = re.compile(r"^[a-z0-9][a-z0-9-]{1,62}$")


class TenantError(ValueError):
    """Raised when a tenant profile or registry operation is invalid."""


def _instant(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def run_scopes(tenant_id: str) -> list[str]:
    """Return the run-manifest scope entries that bind a run to a tenant."""
    if not _TENANT_ID.match(tenant_id):
        raise TenantError("tenant_id must be a lowercase slug")
    return [f"tenant:{tenant_id}"]


class TenantRegistry:
    """Filesystem-backed registry of tenant profiles."""

    def __init__(self, root: str | Path = DEFAULT_TENANT_ROOT) -> None:
        self.root = Path(root)

    # -- paths -----------------------------------------------------------
    @staticmethod
    def _reject_symlink_components(path: Path) -> None:
        absolute = path.absolute()
        current = Path(absolute.anchor)
        for part in absolute.parts[1:]:
            current /= part
            if current.is_symlink():
                raise TenantError(f"tenant path contains a symlink: {current}")

    def _tenant_directory(self, tenant_id: str) -> Path:
        if not isinstance(tenant_id, str) or not _TENANT_ID.match(tenant_id):
            raise TenantError("tenant_id must be a lowercase slug of letters, digits, and dashes")
        return self.root / tenant_id

    def profile_path(self, tenant_id: str) -> Path:
        return self._tenant_directory(tenant_id) / PROFILE_FILENAME

    def run_directory(self, tenant_id: str, run_id: str) -> Path:
        """Return ``<root>/<tenant>/runs/<run_id>`` without creating it."""
        if not run_id or not all(c.isalnum() or c in "._-" for c in run_id) or run_id.startswith("."):
            raise TenantError("run_id is not path-safe")
        return self._tenant_directory(tenant_id) / "runs" / run_id

    # -- validation ------------------------------------------------------
    @staticmethod
    def validate(profile: Mapping[str, Any]) -> dict[str, Any]:
        try:
            validate_workflow_contract("tenant-profile", profile)
        except WorkflowContractError as exc:
            raise TenantError(str(exc)) from exc
        return dict(profile)

    # -- persistence -----------------------------------------------------
    def register(self, profile: Mapping[str, Any]) -> Path:
        """Validate and persist a profile; accounts must be unique across tenants."""
        document = self.validate(profile)
        tenant_id = document["tenant_id"]
        self._reject_symlink_components(self.root)
        path = self.profile_path(tenant_id)
        existing = self._read_if_present(path)
        if existing is not None and _instant(document["updated_at"]) < _instant(existing["updated_at"]):
            raise TenantError(f"{tenant_id}: updated_at is older than the registered profile")
        owned = {(a["platform"], a["account_id"]) for a in document["accounts"]}
        for other in self.list():
            if other["tenant_id"] == tenant_id:
                continue
            clash = owned & {(a["platform"], a["account_id"]) for a in other["accounts"]}
            if clash:
                platform, account_id = sorted(clash)[0]
                raise TenantError(
                    f"{platform} account {account_id} already belongs to tenant {other['tenant_id']}"
                )
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        self._reject_symlink_components(path.parent)
        if path.is_symlink():
            raise TenantError(f"tenant path contains a symlink: {path}")
        temporary = path.with_name(f".{PROFILE_FILENAME}.{os.getpid()}.tmp")
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(temporary, flags, 0o600)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8", closefd=True) as handle:
                json.dump(document, handle, indent=2, sort_keys=True, ensure_ascii=False)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise
        return path

    def _read_if_present(self, path: Path) -> dict[str, Any] | None:
        if path.is_symlink():
            raise TenantError(f"tenant path contains a symlink: {path}")
        if not path.is_file():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise TenantError(f"cannot read {path}: {exc}") from exc
        return self.validate(payload)

    def load(self, tenant_id: str) -> dict[str, Any]:
        path = self.profile_path(tenant_id)
        self._reject_symlink_components(path.parent)
        document = self._read_if_present(path)
        if document is None:
            raise TenantError(f"unknown tenant {tenant_id!r}")
        if document["tenant_id"] != tenant_id:
            raise TenantError(f"profile at {path} belongs to tenant {document['tenant_id']!r}")
        return document

    def list(self) -> list[dict[str, Any]]:
        if not self.root.exists():
            return []
        self._reject_symlink_components(self.root)
        profiles = []
        for child in sorted(self.root.iterdir()):
            if child.is_symlink() or not child.is_dir() or not _TENANT_ID.match(child.name):
                continue
            document = self._read_if_present(child / PROFILE_FILENAME)
            if document is not None:
                profiles.append(document)
        return profiles

    def resolve_account(self, platform: str, account_id: str) -> dict[str, Any]:
        """Return the single tenant owning ``(platform, account_id)``."""
        matches = [
            profile
            for profile in self.list()
            if any(a["platform"] == platform and a["account_id"] == account_id for a in profile["accounts"])
        ]
        if not matches:
            raise TenantError(f"no tenant owns {platform} account {account_id}")
        if len(matches) > 1:
            raise TenantError(f"{platform} account {account_id} is claimed by multiple tenants")
        return matches[0]

    @staticmethod
    def summary(profile: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "tenant_id": profile["tenant_id"],
            "display_name": profile["display_name"],
            "relationship": profile["relationship"],
            "status": profile["status"],
            "accounts": [
                {"platform": a["platform"], "account_id": a["account_id"], "role": a["role"], "connection": a["connection"]}
                for a in profile["accounts"]
            ],
            "privacy_class": profile["privacy_class"],
        }
