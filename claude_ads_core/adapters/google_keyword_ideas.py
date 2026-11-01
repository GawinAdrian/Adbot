"""Fail-closed normalization of stored Google Ads keyword-idea responses.

``KeywordPlanIdeaService.GenerateKeywordIdeas`` is not a GAQL surface, so the
official read-only Google Ads MCP server cannot fetch it.  The repository
script ``scripts/keyword_ideas_via_api.py`` performs the network call with the
operator's own credentials and stores one response per request as a versioned
JSON envelope.  This adapter validates that envelope, normalizes REST-style
camelCase keys and nested ``keyword_idea_metrics`` objects into the flat
``keyword-ideas`` contract shape, and self-validates the result against the
contract.  The adapter never opens a network connection.

Optional metrics honesty: a metric the API did not report stays ``null`` (or
``UNSPECIFIED`` for the competition enum).  Absence is never converted into a
zero, and unknown fields are rejected instead of being dropped silently.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from os import PathLike
from pathlib import Path
from typing import Any, Mapping

from ..models import AccountSnapshot
from ..workflow_contracts import WorkflowContractError, validate_workflow_contract
from .base import AdapterCapabilities, AdapterError, BaseAdapter, Capability
from .csv_export import MAX_EXPORT_BYTES, MAX_EXPORT_ROWS

KEYWORD_IDEAS_SCHEMA_VERSION = "1.0.0"
KEYWORD_IDEAS_PLATFORM = "google"

_ENVELOPE_FIELDS = frozenset(
    {
        "schema_version",
        "artifact_type",
        "run_id",
        "created_at",
        "platform",
        "customer_id",
        "login_customer_id",
        "api_version",
        "query_id",
        "seed",
        "geo_target_constants",
        "language",
        "keyword_plan_network",
        "retrieved_at",
        "ideas",
    }
)
_CUSTOMER_ID = re.compile(r"^[0-9]{10}$")
_API_VERSION = re.compile(r"^v[0-9]{1,3}$")
_CAMEL = re.compile(r"(?<!^)(?=[A-Z])")
_DIGITS = re.compile(r"^[0-9]+$")

# Metric fields whose absence legitimately means "not reported by the API".
_OPTIONAL_IDEA_DEFAULTS: Mapping[str, Any] = {
    "avg_monthly_searches": None,
    "competition": "UNSPECIFIED",
    "competition_index": None,
    "low_top_of_page_bid_micros": None,
    "high_top_of_page_bid_micros": None,
    "close_variants": [],
}
_INT64_IDEA_FIELDS = frozenset(
    {
        "avg_monthly_searches",
        "competition_index",
        "low_top_of_page_bid_micros",
        "high_top_of_page_bid_micros",
    }
)
_IDEA_FIELDS = frozenset(_OPTIONAL_IDEA_DEFAULTS) | {"text"}


class GoogleKeywordIdeasError(AdapterError):
    """Raised when a stored keyword-idea response violates the contract."""


def _snake(name: str) -> str:
    return _CAMEL.sub("_", name).lower()


class GoogleKeywordIdeasAdapter(BaseAdapter):
    """Normalize one stored ``GenerateKeywordIdeas`` response envelope."""

    platform = KEYWORD_IDEAS_PLATFORM
    adapter_id = "google-ads-keyword-ideas-v1"

    def __init__(self, customer_id: str) -> None:
        if not isinstance(customer_id, str) or not _CUSTOMER_ID.match(customer_id):
            raise GoogleKeywordIdeasError(
                "customer_id must be the 10-digit Google Ads customer ID without dashes"
            )
        self.customer_id = customer_id
        self._lineage: dict[str, Any] | None = None

    def discover_capabilities(self) -> AdapterCapabilities:
        return AdapterCapabilities(
            schema_version="1.0.0",
            adapter_id=self.adapter_id,
            platform=self.platform,
            default_mutation_mode="read-only",
            capabilities=(
                Capability("keyword-ideas-normalization", "live-read", "fixture-verified"),
                Capability(
                    "account-mutation",
                    "live-write",
                    "disabled",
                    "GenerateKeywordIdeas is a read-only research surface and no write adapter lifecycle is approved.",
                ),
            ),
        )

    def lineage(self) -> dict[str, Any]:
        """Return provenance counts for the run manifest (never seed keyword texts)."""
        if self._lineage is None:
            raise GoogleKeywordIdeasError("no response has been read yet")
        return dict(self._lineage)

    def read_snapshot(self, source: str | PathLike[str]) -> AccountSnapshot:
        raise GoogleKeywordIdeasError(
            "keyword ideas are not an account snapshot; use read_ideas() instead"
        )

    def read_ideas(self, source: str | PathLike[str]) -> dict[str, Any]:
        """Load, validate, and normalize one stored keyword-ideas envelope."""
        envelope = self._load_envelope(Path(source))
        ideas = [self._normalize_idea(item, index) for index, item in enumerate(envelope["ideas"], start=1)]
        normalized: dict[str, Any] = {**envelope, "ideas": ideas}
        try:
            validate_workflow_contract("keyword-ideas", normalized)
        except WorkflowContractError as exc:
            raise GoogleKeywordIdeasError(f"normalized keyword ideas violate the contract: {exc}") from exc
        self._lineage = {
            "adapter_id": self.adapter_id,
            "customer_id": self.customer_id,
            "login_customer_id": envelope["login_customer_id"],
            "api_version": envelope["api_version"],
            "query_id": envelope["query_id"],
            "retrieved_at": envelope["retrieved_at"],
            "idea_count": len(ideas),
            "seed_keyword_count": len(envelope["seed"]["keywords"]),
            "geo_target_count": len(envelope["geo_target_constants"]),
        }
        return normalized

    def _load_envelope(self, path: Path) -> dict[str, Any]:
        try:
            if not path.is_file():
                raise GoogleKeywordIdeasError(f"response is not a regular file: {path}")
            if path.stat().st_size > MAX_EXPORT_BYTES:
                raise GoogleKeywordIdeasError(f"response exceeds {MAX_EXPORT_BYTES} byte limit")
            payload = json.loads(path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise GoogleKeywordIdeasError(f"cannot read response: {exc}") from exc
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise GoogleKeywordIdeasError(f"response is not valid UTF-8 JSON: {exc}") from exc
        if not isinstance(payload, dict):
            raise GoogleKeywordIdeasError("response envelope must be a JSON object")
        keys = set(payload)
        missing = sorted(_ENVELOPE_FIELDS - keys)
        extra = sorted(keys - _ENVELOPE_FIELDS)
        if missing:
            raise GoogleKeywordIdeasError("response envelope missing field(s): " + ", ".join(missing))
        if extra:
            raise GoogleKeywordIdeasError("response envelope has unsupported field(s): " + ", ".join(extra))
        if payload["schema_version"] != KEYWORD_IDEAS_SCHEMA_VERSION:
            raise GoogleKeywordIdeasError("response envelope schema_version is unsupported")
        if payload["artifact_type"] != "keyword-ideas":
            raise GoogleKeywordIdeasError("response envelope artifact_type must be 'keyword-ideas'")
        if payload["platform"] != KEYWORD_IDEAS_PLATFORM:
            raise GoogleKeywordIdeasError("response envelope platform must be 'google'")
        if payload["customer_id"] != self.customer_id:
            raise GoogleKeywordIdeasError("response envelope customer_id does not match the adapter customer_id")
        login = payload["login_customer_id"]
        if login is not None and (not isinstance(login, str) or not _CUSTOMER_ID.match(login)):
            raise GoogleKeywordIdeasError("login_customer_id must be a 10-digit customer ID when supplied")
        if not isinstance(payload["api_version"], str) or not _API_VERSION.match(payload["api_version"]):
            raise GoogleKeywordIdeasError("api_version must look like 'v25'")
        seed = payload["seed"]
        if not isinstance(seed, Mapping) or set(seed) != {"keywords", "url"}:
            raise GoogleKeywordIdeasError("seed must be an object with exactly 'keywords' and 'url'")
        if not isinstance(seed["keywords"], list):
            raise GoogleKeywordIdeasError("seed.keywords must be an array")
        for field in ("created_at", "retrieved_at"):
            self._require_timezone(payload[field], field)
        ideas = payload["ideas"]
        if not isinstance(ideas, list) or not ideas:
            raise GoogleKeywordIdeasError(
                "ideas must be a non-empty array; an empty result is needs_input, not a dataset"
            )
        if len(ideas) > MAX_EXPORT_ROWS:
            raise GoogleKeywordIdeasError(f"response exceeds {MAX_EXPORT_ROWS} idea limit")
        return payload

    @staticmethod
    def _require_timezone(value: Any, field: str) -> None:
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError as exc:
            raise GoogleKeywordIdeasError(f"{field} must be an ISO 8601 timestamp") from exc
        if parsed.tzinfo is None:
            raise GoogleKeywordIdeasError(f"{field} must include a timezone offset")

    def _normalize_idea(self, item: Any, index: int) -> dict[str, Any]:
        if not isinstance(item, Mapping):
            raise GoogleKeywordIdeasError(f"ideas[{index}] must be an object")
        flat: dict[str, Any] = {}
        for raw_key, value in item.items():
            if not isinstance(raw_key, str) or not raw_key:
                raise GoogleKeywordIdeasError(f"ideas[{index}] keys must be non-empty strings")
            key = _snake(raw_key)
            if key == "keyword_idea_metrics":
                if value is None:
                    continue
                if not isinstance(value, Mapping):
                    raise GoogleKeywordIdeasError(f"ideas[{index}].{raw_key} must be an object")
                for metric_key, metric_value in value.items():
                    if not isinstance(metric_key, str) or not metric_key:
                        raise GoogleKeywordIdeasError(f"ideas[{index}] metric keys must be non-empty strings")
                    self._put(flat, _snake(metric_key), metric_value, index)
                continue
            self._put(flat, key, value, index)
        unknown = sorted(set(flat) - _IDEA_FIELDS)
        if unknown:
            raise GoogleKeywordIdeasError(f"ideas[{index}] has unsupported field(s): " + ", ".join(unknown))
        if "text" not in flat:
            raise GoogleKeywordIdeasError(f"ideas[{index}] is missing the required field 'text'")
        idea: dict[str, Any] = dict(_OPTIONAL_IDEA_DEFAULTS)
        idea["close_variants"] = list(_OPTIONAL_IDEA_DEFAULTS["close_variants"])
        idea.update(flat)
        for field in _INT64_IDEA_FIELDS:
            idea[field] = self._coerce_int64(idea[field], index, field)
        return idea

    @staticmethod
    def _put(flat: dict[str, Any], key: str, value: Any, index: int) -> None:
        if key in flat:
            raise GoogleKeywordIdeasError(f"ideas[{index}] repeats the field {key!r} after normalization")
        flat[key] = value

    @staticmethod
    def _coerce_int64(value: Any, index: int, field: str) -> Any:
        """Accept proto JSON's string-encoded int64 values without widening the type."""
        if isinstance(value, str):
            if _DIGITS.match(value):
                return int(value)
            raise GoogleKeywordIdeasError(f"ideas[{index}].{field} must be an integer, null, or a digit string")
        return value
