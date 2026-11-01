#!/usr/bin/env python3
"""Fetch Google Ads keyword ideas and store them as a keyword-ideas envelope.

``KeywordPlanIdeaService.GenerateKeywordIdeas`` is not exposed by the official
read-only Google Ads MCP server, so this script calls the Google Ads API
directly through the official ``google-ads`` Python client.  The dependency is
loaded ephemerally and stays out of the repository lock files:

  uv run --no-project --with google-ads==31.4.0 scripts/keyword_ideas_via_api.py \\
      --customer 1234567890 --login-customer-id 1122334455 \\
      --keywords "beispiel dienstleistung" "beispiel dienstleistung anbieter" \\
      --geo-target-constants 2276 --language 1001 \\
      --query-id beispiel-cluster-v1 --out path/to/keyword-ideas.json

(google-ads==31.4.0 was the current release on PyPI when this script was
written, 2026-09-01; bump deliberately, not implicitly.)

Credentials load exactly like scripts/google_ads_mcp.sh: GOOGLE_PROJECT_ID,
GOOGLE_ADS_DEVELOPER_TOKEN (or DEVELOPER_TOKEN), GOOGLE_APPLICATION_CREDENTIALS
and optionally GOOGLE_ADS_LOGIN_CUSTOMER_ID come from the environment first and
the git-ignored .env second.  Secret values are never printed.

The stored envelope is validated and normalized by
``claude_ads_core.adapters.GoogleKeywordIdeasAdapter``; metrics the API does
not report are stored as null, never as zero.  Store envelopes only beneath
git-ignored run directories (``.claude-ads/``).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_ENV_KEYS = (
    "GOOGLE_PROJECT_ID",
    "GOOGLE_ADS_DEVELOPER_TOKEN",
    "DEVELOPER_TOKEN",
    "GOOGLE_ADS_LOGIN_CUSTOMER_ID",
    "GOOGLE_APPLICATION_CREDENTIALS",
)
_API_VERSION = re.compile(r"^v[0-9]{1,3}$")
MAX_SEED_KEYWORDS = 10  # conservative service cap; verify against the live API during the pilot


def _load_env_file() -> None:
    """Port of scripts/google_ads_mcp.sh: fill missing keys from the git-ignored .env."""
    env_path = ROOT / ".env"
    if not env_path.is_file():
        return
    values: dict[str, str] = {}
    for line in env_path.read_text(encoding="utf-8").splitlines():
        for key in _ENV_KEYS:
            if line.startswith(f"{key}="):
                value = line.split("=", 1)[1].strip().strip("'\"")
                if value:
                    values[key] = value
    for key, value in values.items():
        os.environ.setdefault(key, value)


def _digits(value: str, label: str) -> str:
    cleaned = value.replace("-", "")
    if not re.fullmatch(r"[0-9]{10}", cleaned):
        raise SystemExit(f"{label} must be a 10-digit Google Ads customer ID")
    return cleaned


def _resource(value: str, prefix: str) -> str:
    if value.startswith(f"{prefix}/"):
        suffix = value.split("/", 1)[1]
    else:
        suffix = value
    if not re.fullmatch(r"[0-9]+", suffix):
        raise SystemExit(f"{prefix} value must be numeric, got {value!r}")
    return f"{prefix}/{suffix}"


def _optional_int(message: object, field: str) -> int | None:
    """Return an optional int64 metric, honoring proto presence where available."""
    try:
        if field not in message:  # type: ignore[operator]
            return None
    except (TypeError, ValueError):
        pass
    value = getattr(message, field, None)
    if value is None:
        return None
    return int(value)


def _competition_name(metrics: object) -> str:
    value = getattr(metrics, "competition", None)
    name = getattr(value, "name", None)
    if isinstance(name, str) and name:
        return name
    return "UNSPECIFIED"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--customer", required=True, help="10-digit customer ID (dashes allowed)")
    parser.add_argument("--login-customer-id", default=None, help="manager (MCC) ID for managed accounts")
    parser.add_argument("--keywords", nargs="*", default=[], help=f"seed keywords (max {MAX_SEED_KEYWORDS})")
    parser.add_argument("--url-seed", default=None, help="page URL seed (alone or combined with keywords)")
    parser.add_argument("--geo-target-constants", nargs="+", required=True, help="geo IDs, e.g. 2276 for Germany")
    parser.add_argument("--language", default="1001", help="language constant ID (default 1001 = German)")
    parser.add_argument(
        "--keyword-plan-network",
        default="GOOGLE_SEARCH",
        choices=("GOOGLE_SEARCH", "GOOGLE_SEARCH_AND_PARTNERS"),
    )
    parser.add_argument("--query-id", required=True, help="stable identifier for this request")
    parser.add_argument("--run-id", default=None, help="defaults to <query-id>-<YYYYMMDD>")
    parser.add_argument("--api-version", default=None, help="override the client default, e.g. v25")
    parser.add_argument("--limit", type=int, default=200, help="maximum ideas to store (default 200)")
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)

    if not args.keywords and not args.url_seed:
        raise SystemExit("provide --keywords, --url-seed, or both")
    if len(args.keywords) > MAX_SEED_KEYWORDS:
        raise SystemExit(
            f"{len(args.keywords)} seed keywords exceed the {MAX_SEED_KEYWORDS}-seed cap; split the call"
        )
    if args.limit < 1:
        raise SystemExit("--limit must be >= 1")

    _load_env_file()
    developer_token = os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN") or os.environ.get("DEVELOPER_TOKEN")
    if not developer_token:
        raise SystemExit("GOOGLE_ADS_DEVELOPER_TOKEN is not set (add it to .env)")
    os.environ.setdefault("GOOGLE_CLOUD_PROJECT", os.environ.get("GOOGLE_PROJECT_ID", ""))
    adc_path = Path(
        os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        or Path.home() / ".config" / "gcloud" / "application_default_credentials.json"
    )
    if not adc_path.is_file():
        raise SystemExit(
            f"credentials file missing: {adc_path} (run gcloud auth application-default login)"
        )
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(adc_path)

    try:
        from google.ads.googleads.client import GoogleAdsClient
        try:
            from google.ads.googleads.client import _DEFAULT_VERSION as default_version
        except ImportError:
            default_version = None
    except ImportError as exc:
        raise SystemExit(
            "the google-ads client library is not installed; run this script via "
            "'uv run --no-project --with google-ads==31.4.0 scripts/keyword_ideas_via_api.py ...' "
            f"(import error: {exc})"
        )

    api_version = args.api_version or default_version
    if not api_version or not _API_VERSION.match(api_version):
        raise SystemExit(
            "could not determine the API version; pass --api-version (e.g. v25)"
        )

    customer_id = _digits(args.customer, "--customer")
    login_customer_id = _digits(args.login_customer_id, "--login-customer-id") if args.login_customer_id else None
    config: dict[str, object] = {
        "developer_token": developer_token,
        "use_proto_plus": True,
        "use_application_default_credentials": True,
    }
    if login_customer_id:
        config["login_customer_id"] = login_customer_id
    client = GoogleAdsClient.load_from_dict(config)

    service = client.get_service("KeywordPlanIdeaService", version=api_version)
    request = client.get_type("GenerateKeywordIdeasRequest", version=api_version)
    request.customer_id = customer_id
    request.language = _resource(args.language, "languageConstants")
    request.geo_target_constants.extend(
        _resource(value, "geoTargetConstants") for value in args.geo_target_constants
    )
    request.include_adult_keywords = False
    request.keyword_plan_network = getattr(
        client.enums.KeywordPlanNetworkEnum, args.keyword_plan_network
    )
    if args.keywords and args.url_seed:
        request.keyword_and_url_seed.url = args.url_seed
        request.keyword_and_url_seed.keywords.extend(args.keywords)
    elif args.keywords:
        request.keyword_seed.keywords.extend(args.keywords)
    else:
        request.url_seed.url = args.url_seed

    ideas: list[dict[str, object]] = []
    for result in service.generate_keyword_ideas(request=request):
        metrics = getattr(result, "keyword_idea_metrics", None)
        ideas.append(
            {
                "text": result.text,
                "avg_monthly_searches": _optional_int(metrics, "avg_monthly_searches"),
                "competition": _competition_name(metrics),
                "competition_index": _optional_int(metrics, "competition_index"),
                "low_top_of_page_bid_micros": _optional_int(metrics, "low_top_of_page_bid_micros"),
                "high_top_of_page_bid_micros": _optional_int(metrics, "high_top_of_page_bid_micros"),
                "close_variants": [str(item) for item in getattr(metrics, "close_variants", []) or []],
            }
        )
        if len(ideas) >= args.limit:
            break
    if not ideas:
        raise SystemExit("the API returned no keyword ideas; treat this as needs_input, not a dataset")

    now = datetime.now(timezone.utc).replace(microsecond=0)
    envelope = {
        "schema_version": "1.0.0",
        "artifact_type": "keyword-ideas",
        "run_id": args.run_id or f"{args.query_id}-{now:%Y%m%d}",
        "created_at": now.isoformat().replace("+00:00", "Z"),
        "platform": "google",
        "customer_id": customer_id,
        "login_customer_id": login_customer_id,
        "api_version": api_version,
        "query_id": args.query_id,
        "seed": {"keywords": list(args.keywords), "url": args.url_seed},
        "geo_target_constants": [
            _resource(value, "geoTargetConstants") for value in args.geo_target_constants
        ],
        "language": _resource(args.language, "languageConstants"),
        "keyword_plan_network": args.keyword_plan_network,
        "retrieved_at": now.isoformat().replace("+00:00", "Z"),
        "ideas": ideas,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(envelope, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "query_id": args.query_id,
                "customer_id": customer_id,
                "api_version": api_version,
                "ideas": len(ideas),
                "out": str(out),
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
