#!/usr/bin/env python3
"""Run a read-only Google Ads query directly through the official API client.

This is the MCP-free sibling of ``gaql_via_mcp.py``.  It exists so that scheduled jobs
(the daily watcher) can read account data without a running Claude session.  It stores
the same live-read envelope that ``GoogleAdsLiveReadAdapter`` consumes.

Read-only by construction: the only service call is ``GoogleAdsService.SearchStream``.
No mutate service is imported, and a test fails if one appears in this file.

  uv run --no-project --with google-ads==35.0.0 scripts/gaql_via_api.py \\
      --customer 1234567890 --resource campaign \\
      --fields campaign.id campaign.name campaign.status metrics.cost_micros \\
      --conditions "segments.date BETWEEN '2026-10-01' AND '2026-10-07'" \\
      --query-id campaign-daily-v1 --out .adbot/runs/example/live/campaign-daily.json

(google-ads 35.0.0 was the current PyPI release on 2026-10-29; bump deliberately.
The client accepts a configuration without a developer token since 32.0.0.)

Credentials: GOOGLE_PROJECT_ID plus Application Default Credentials; see adbot_env.py.
Secret values are never printed.  Store envelopes only beneath git-ignored directories.
"""
from __future__ import annotations

import argparse
import enum
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent))
import adbot_env  # noqa: E402  (sibling module, path set above)

ROOT = Path(__file__).resolve().parents[1]
_API_VERSION = re.compile(r"^v[0-9]{1,3}$")
_RESOURCE = re.compile(r"^[a-z][a-z0-9_]*$")
_FIELD = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$")
_ORDER = re.compile(r"^[a-z][a-z0-9_.]*( (ASC|DESC))?$")


class QueryError(ValueError):
    """Raised when query parts are not safe, simple GAQL."""


def build_query(
    resource: str,
    fields: Sequence[str],
    conditions: Sequence[str] = (),
    order_by: Sequence[str] = (),
    limit: int | None = None,
) -> str:
    """Compose one GAQL ``SELECT`` statement from validated parts."""
    if not _RESOURCE.match(resource):
        raise QueryError(f"invalid resource name: {resource!r}")
    if not fields:
        raise QueryError("at least one field is required")
    for field in fields:
        if not _FIELD.match(field):
            raise QueryError(f"invalid field name: {field!r}")
    for condition in conditions:
        if ";" in condition or "\n" in condition:
            raise QueryError("conditions must be single-line GAQL without ';'")
    for order in order_by:
        if not _ORDER.match(order):
            raise QueryError(f"invalid ordering: {order!r}")
    if limit is not None and limit < 1:
        raise QueryError("limit must be >= 1")
    query = f"SELECT {', '.join(fields)} FROM {resource}"
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    if order_by:
        query += " ORDER BY " + ", ".join(order_by)
    if limit is not None:
        query += f" LIMIT {limit}"
    return query


def _plain(value: Any) -> Any:
    """Convert one API value to a JSON-safe value (enums by name, int64 as string)."""
    if isinstance(value, enum.Enum):
        return value.name
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return value
    if isinstance(value, (list, tuple)) or type(value).__name__ in {"RepeatedScalarContainer", "RepeatedComposite"}:
        return [_plain(item) for item in value]
    return str(value)


def extract_row(row: Any, fields: Sequence[str]) -> dict[str, Any]:
    """Return ``{"campaign.id": ..., ...}`` for the requested fields only."""
    out: dict[str, Any] = {}
    for path in fields:
        current: Any = row
        for part in path.split("."):
            current = getattr(current, part)
        out[path] = _plain(current)
    return out


def _digits(value: str, label: str) -> str:
    cleaned = value.replace("-", "")
    if not re.fullmatch(r"[0-9]{10}", cleaned):
        raise SystemExit(f"{label} must be a 10-digit Google Ads customer ID")
    return cleaned


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--customer", required=True, help="10-digit customer ID (dashes allowed)")
    parser.add_argument("--login-customer-id", default=None, help="manager ID; omit for direct access")
    parser.add_argument("--resource", required=True)
    parser.add_argument("--fields", nargs="+", required=True)
    parser.add_argument("--conditions", nargs="*", default=[])
    parser.add_argument("--order-by", nargs="*", default=[])
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--query-id", required=True)
    parser.add_argument("--api-version", default=None, help="override the client default, e.g. v26")
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)

    try:
        query = build_query(args.resource, args.fields, args.conditions, args.order_by, args.limit)
    except QueryError as exc:
        raise SystemExit(f"query rejected: {exc}")

    adbot_env.load_env(ROOT, os.environ)
    try:
        project = adbot_env.require_project(os.environ)
        adc = adbot_env.adc_path(os.environ)
    except adbot_env.CredentialsError as exc:
        raise SystemExit(str(exc))
    os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project)
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(adc)

    try:
        from google.ads.googleads.client import GoogleAdsClient
        try:
            from google.ads.googleads.client import _DEFAULT_VERSION as default_version
        except ImportError:
            default_version = None
    except ImportError as exc:
        raise SystemExit(
            "the google-ads client library is not installed; run via "
            "'uv run --no-project --with google-ads==35.0.0 scripts/gaql_via_api.py ...' "
            f"(import error: {exc})"
        )
    api_version = args.api_version or default_version
    if not api_version or not _API_VERSION.match(api_version):
        raise SystemExit("could not determine the API version; pass --api-version (e.g. v26)")

    customer_id = _digits(args.customer, "--customer")
    login_id = _digits(args.login_customer_id, "--login-customer-id") if args.login_customer_id else None
    client = GoogleAdsClient.load_from_dict(adbot_env.build_client_config(os.environ, login_id))
    service = client.get_service("GoogleAdsService", version=api_version)

    rows: list[dict[str, Any]] = []
    for batch in service.search_stream(customer_id=customer_id, query=query):
        for result in batch.results:
            rows.append(extract_row(result, args.fields))
    if not rows:
        raise SystemExit("the API returned no rows; treat this as needs_input, not a dataset")

    now = datetime.now(timezone.utc).replace(microsecond=0)
    envelope = {
        "schema_version": "1.0.0",
        "platform": "google",
        "customer_id": customer_id,
        "login_customer_id": login_id,
        "api_version": api_version,
        "query_id": args.query_id,
        "query": query,
        "retrieved_at": now.isoformat().replace("+00:00", "Z"),
        "rows": rows,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(envelope, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"query_id": args.query_id, "customer_id": customer_id, "api_version": api_version,
                      "rows": len(rows), "out": str(out)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
