"""Fail-closed normalization of Google Ads MCP/GAQL search responses.

The official Google Ads MCP server is a read-only transport.  Its ``search``
tool returns GAQL rows as JSON objects whose nesting mirrors the API resource
paths (``customer.id``, ``metrics.cost_micros``).  The conductor stores one
response per query in a small JSON envelope; this adapter validates that
envelope, flattens each row to GAQL dot paths, and projects it onto the exact
versioned native profile so live reads and CSV exports share one
normalization path.  The adapter never opens a network connection.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from os import PathLike
from pathlib import Path
from typing import Any, Mapping

from ..models import AccountSnapshot
from .base import AdapterCapabilities, AdapterError, BaseAdapter, Capability
from .csv_export import MAX_EXPORT_BYTES, MAX_EXPORT_ROWS
from .native_export import NativeCSVExportAdapter, NativeExportError

LIVE_READ_SCHEMA_VERSION = "1.0.0"
LIVE_READ_PLATFORM = "google"

# Query identifiers whose projection is fixture-verified against a native profile.
# A response with any other query_id fails closed instead of being guessed.
SUPPORTED_LIVE_QUERIES: Mapping[str, str] = {
    "campaign-daily-v1": "google",
}

_ENVELOPE_FIELDS = frozenset(
    {
        "schema_version",
        "platform",
        "customer_id",
        "login_customer_id",
        "api_version",
        "query_id",
        "query",
        "retrieved_at",
        "rows",
    }
)
_REQUIRED_ENVELOPE_FIELDS = _ENVELOPE_FIELDS - {"login_customer_id", "query"}
_CUSTOMER_ID = re.compile(r"^[0-9]{10}$")
_API_VERSION = re.compile(r"^v[0-9]{1,3}$")
_CAMEL = re.compile(r"(?<!^)(?=[A-Z])")


class GoogleLiveReadError(AdapterError):
    """Raised when a stored MCP response does not satisfy the live-read contract."""


def _snake(name: str) -> str:
    return _CAMEL.sub("_", name).lower()


def flatten_gaql_row(row: Mapping[str, Any], prefix: str = "") -> dict[str, str]:
    """Flatten a nested GAQL result row into ``resource.field`` string pairs.

    camelCase keys (``costMicros``) are normalized to the GAQL snake_case form
    (``cost_micros``).  Scalars become strings; booleans become ``TRUE``/``FALSE``
    like the API enum style.  Lists and ``None`` are rejected because the
    campaign-level profile has no list-valued field and missing values must not
    be silently converted to empty strings.
    """
    flat: dict[str, str] = {}
    for raw_key, value in row.items():
        if not isinstance(raw_key, str) or not raw_key:
            raise GoogleLiveReadError("row keys must be non-empty strings")
        key = f"{prefix}{_snake(raw_key)}"
        if isinstance(value, Mapping):
            flat.update(flatten_gaql_row(value, f"{key}."))
        elif isinstance(value, bool):
            flat[key] = "TRUE" if value else "FALSE"
        elif isinstance(value, (int, float)):
            flat[key] = repr(value) if isinstance(value, float) else str(value)
        elif isinstance(value, str):
            flat[key] = value
        elif value is None:
            raise GoogleLiveReadError(f"field {key} is null; missing values must stay missing")
        else:
            raise GoogleLiveReadError(f"field {key} has unsupported type {type(value).__name__}")
    return flat


class GoogleAdsLiveReadAdapter(BaseAdapter):
    """Normalize one stored Google Ads MCP ``search`` response."""

    platform = LIVE_READ_PLATFORM
    adapter_id = "google-ads-mcp-live-read-v1"

    def __init__(self, customer_id: str) -> None:
        if not isinstance(customer_id, str) or not _CUSTOMER_ID.match(customer_id):
            raise GoogleLiveReadError("customer_id must be the 10-digit Google Ads customer ID without dashes")
        self.customer_id = customer_id
        self._lineage: dict[str, Any] | None = None

    def discover_capabilities(self) -> AdapterCapabilities:
        return AdapterCapabilities(
            schema_version="1.0.0",
            adapter_id=self.adapter_id,
            platform=self.platform,
            default_mutation_mode="read-only",
            capabilities=(
                Capability("live-read-normalization", "live-read", "fixture-verified"),
                Capability(
                    "account-mutation",
                    "live-write",
                    "disabled",
                    "The official Google Ads MCP server is read-only and no write adapter lifecycle is approved.",
                ),
            ),
        )

    def lineage(self) -> dict[str, Any]:
        """Return provenance of the last read for the run manifest (never the query text)."""
        if self._lineage is None:
            raise GoogleLiveReadError("no response has been read yet")
        return dict(self._lineage)

    def read_snapshot(self, source: str | PathLike[str]) -> AccountSnapshot:
        envelope = self._load_envelope(Path(source))
        query_id = envelope["query_id"]
        profile_platform = SUPPORTED_LIVE_QUERIES.get(query_id)
        if profile_platform is None:
            raise GoogleLiveReadError(
                f"query_id {query_id!r} has no fixture-verified projection; supported: "
                + ", ".join(sorted(SUPPORTED_LIVE_QUERIES))
            )
        rows = envelope["rows"]
        flat_rows = [self._flatten_checked(row, index) for index, row in enumerate(rows, start=1)]
        native = NativeCSVExportAdapter(profile_platform)
        try:
            snapshot = native.snapshot_from_rows(flat_rows)
        except NativeExportError as exc:
            raise GoogleLiveReadError(f"{query_id}: {exc}") from exc
        if snapshot["account"]["account_id"] != self.customer_id:
            raise GoogleLiveReadError("normalized account_id does not match the requested customer_id")
        self._lineage = {
            "adapter_id": self.adapter_id,
            "profile_id": native.profile.profile_id,
            "customer_id": self.customer_id,
            "login_customer_id": envelope.get("login_customer_id"),
            "api_version": envelope["api_version"],
            "query_id": query_id,
            "retrieved_at": envelope["retrieved_at"],
            "row_count": len(rows),
        }
        return snapshot

    def _load_envelope(self, path: Path) -> dict[str, Any]:
        try:
            if not path.is_file():
                raise GoogleLiveReadError(f"response is not a regular file: {path}")
            if path.stat().st_size > MAX_EXPORT_BYTES:
                raise GoogleLiveReadError(f"response exceeds {MAX_EXPORT_BYTES} byte limit")
            payload = json.loads(path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise GoogleLiveReadError(f"cannot read response: {exc}") from exc
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise GoogleLiveReadError(f"response is not valid UTF-8 JSON: {exc}") from exc
        if not isinstance(payload, dict):
            raise GoogleLiveReadError("response envelope must be a JSON object")
        keys = set(payload)
        missing = sorted(_REQUIRED_ENVELOPE_FIELDS - keys)
        extra = sorted(keys - _ENVELOPE_FIELDS)
        if missing:
            raise GoogleLiveReadError("response envelope missing field(s): " + ", ".join(missing))
        if extra:
            raise GoogleLiveReadError("response envelope has unsupported field(s): " + ", ".join(extra))
        if payload["schema_version"] != LIVE_READ_SCHEMA_VERSION:
            raise GoogleLiveReadError("response envelope schema_version is unsupported")
        if payload["platform"] != LIVE_READ_PLATFORM:
            raise GoogleLiveReadError("response envelope platform must be 'google'")
        if payload["customer_id"] != self.customer_id:
            raise GoogleLiveReadError("response envelope customer_id does not match the adapter customer_id")
        login = payload.get("login_customer_id")
        if login is not None and (not isinstance(login, str) or not _CUSTOMER_ID.match(login)):
            raise GoogleLiveReadError("login_customer_id must be a 10-digit customer ID when supplied")
        if not isinstance(payload["api_version"], str) or not _API_VERSION.match(payload["api_version"]):
            raise GoogleLiveReadError("api_version must look like 'v21'")
        if not isinstance(payload["query_id"], str) or not payload["query_id"]:
            raise GoogleLiveReadError("query_id must be a non-empty string")
        retrieved = payload["retrieved_at"]
        try:
            parsed = datetime.fromisoformat(str(retrieved).replace("Z", "+00:00"))
        except ValueError as exc:
            raise GoogleLiveReadError("retrieved_at must be an ISO 8601 timestamp") from exc
        if parsed.tzinfo is None:
            raise GoogleLiveReadError("retrieved_at must include a timezone offset")
        rows = payload["rows"]
        if not isinstance(rows, list) or not rows:
            raise GoogleLiveReadError("rows must be a non-empty array; an empty result is needs_input, not a dataset")
        if len(rows) > MAX_EXPORT_ROWS:
            raise GoogleLiveReadError(f"response exceeds {MAX_EXPORT_ROWS} row limit")
        return payload

    def _flatten_checked(self, row: Any, index: int) -> dict[str, str]:
        if not isinstance(row, Mapping):
            raise GoogleLiveReadError(f"rows[{index}] must be an object")
        try:
            flat = flatten_gaql_row(row)
        except GoogleLiveReadError as exc:
            raise GoogleLiveReadError(f"rows[{index}]: {exc}") from exc
        row_customer = flat.get("customer.id")
        if row_customer != self.customer_id:
            raise GoogleLiveReadError(
                f"rows[{index}]: customer.id {row_customer!r} does not match requested customer_id"
            )
        return flat
