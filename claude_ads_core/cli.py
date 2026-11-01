"""Command-line interface for deterministic Claude Ads core operations."""

from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
import json
import os
import sys
from pathlib import Path
from typing import Any, Sequence

from . import __version__
from .adapters import AdapterError, GenericCSVExportAdapter
from .contracts import CONTRACT_NAMES, ContractError, load_contract, validate_contract
from .doctor import render_text, run_doctor, to_json
from .i18n import I18nError, SUPPORTED_LANGUAGES, Translator, normalize_language
from .reporting import ReportRenderError, write_report_bundle
from .product_status import ProductStatusError, evaluate_product_status
from .scoring import ScoringError, score_account, score_portfolio
from .tenants import DEFAULT_TENANT_ROOT, TenantError, TenantRegistry
from .user_settings import SETTINGS_FILENAME, SettingsError, default_settings, load_settings, profile_dir, save_settings


def _read_json(path: str) -> Any:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot load {path}: {exc}") from exc


def _emit(payload: Any) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="claude-ads-core")
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)

    validate = commands.add_parser("validate", help="validate a versioned JSON contract")
    validate.add_argument("contract", choices=CONTRACT_NAMES)
    validate.add_argument("path")

    score = commands.add_parser("score", help="score one account")
    score.add_argument("--controls", required=True)
    score.add_argument("--findings", required=True)
    score.add_argument("--weights", required=True)

    portfolio = commands.add_parser("portfolio", help="aggregate account scores")
    portfolio.add_argument("path", help="JSON array of account score records")

    status = commands.add_parser("status", help="show repository status, or a report bundle when path is supplied")
    status.add_argument("path", nargs="?")
    status.add_argument("--root", default=".")
    status.add_argument("--as-of")
    status.add_argument("--release-gate")

    next_command = commands.add_parser("next", help="show exactly one repository-artifact blocker")
    next_command.add_argument("--root", default=".")
    next_command.add_argument("--as-of", required=True)
    next_command.add_argument("--release-gate")

    render = commands.add_parser(
        "render",
        aliases=["report"],
        help="render a validated report bundle beneath a safe output root",
    )
    render.add_argument("path", help="ReportBundle JSON input")
    render.add_argument("--format", choices=("markdown", "html", "pdf"), default="markdown")
    render.add_argument("--root", default=".claude-ads/runs", help="safe root for report artifacts")
    render.add_argument("--output", help="relative output path; defaults to <run-id>/report.<extension>")
    render.add_argument(
        "--lang",
        choices=SUPPORTED_LANGUAGES,
        default=None,
        help="report language; defaults to the ADBOT_LANG environment variable, then en",
    )

    ingest = commands.add_parser("ingest-export", help="normalize a generic CSV export")
    ingest.add_argument("--platform", required=True)
    ingest.add_argument("path")

    doctor = commands.add_parser("doctor", help="check the installation and the Google connection (read-only)")
    doctor.add_argument("--lang", choices=SUPPORTED_LANGUAGES, default=None, help="message language; default: ADBOT_LANG, settings, then en")
    doctor.add_argument("--json", action="store_true", help="machine-readable result without free text")
    doctor.add_argument("--online", action="store_true", help="also test a read-only request to Google Ads")
    doctor.add_argument("--profile-dir", default=None, help="defaults to ADBOT_PROFILE_DIR or ~/.config/adbot/standard")

    settings = commands.add_parser("settings", help="manage local user settings (language, market, cadence)")
    settings_commands = settings.add_subparsers(dest="settings_command", required=True)
    settings_init = settings_commands.add_parser("init", help="create default settings for a language")
    settings_init.add_argument("--lang", required=True, choices=("de", "pl"))
    settings_init.add_argument("--profile-dir", default=None, help="defaults to ADBOT_PROFILE_DIR or ~/.config/adbot/standard")
    settings_init.add_argument("--force", action="store_true", help="overwrite existing settings")
    settings_show = settings_commands.add_parser("show", help="print the validated settings")
    settings_show.add_argument("--profile-dir", default=None)
    settings_set = settings_commands.add_parser("set", help="change selected settings (validated before writing)")
    settings_set.add_argument("--profile-dir", default=None)
    settings_set.add_argument("--account", help="10-digit Google Ads customer ID, or 'none'")
    settings_set.add_argument("--watch", choices=("daily", "off"))
    settings_set.add_argument("--report", choices=("weekly", "biweekly", "monthly", "on-demand"))
    settings_set.add_argument("--weekday", choices=("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"))
    settings_set.add_argument("--deep-review", choices=("monthly", "quarterly", "off"))

    tenant = commands.add_parser("tenant", help="manage tenant profiles beneath the local state root")
    tenant_commands = tenant.add_subparsers(dest="tenant_command", required=True)
    tenant_validate = tenant_commands.add_parser("validate", help="validate a tenant profile file")
    tenant_validate.add_argument("path")
    tenant_register = tenant_commands.add_parser("register", help="validate and persist a tenant profile")
    tenant_register.add_argument("path")
    tenant_register.add_argument("--root", default=DEFAULT_TENANT_ROOT)
    tenant_list = tenant_commands.add_parser("list", help="list registered tenants")
    tenant_list.add_argument("--root", default=DEFAULT_TENANT_ROOT)
    tenant_show = tenant_commands.add_parser("show", help="print one registered tenant profile")
    tenant_show.add_argument("tenant_id")
    tenant_show.add_argument("--root", default=DEFAULT_TENANT_ROOT)
    tenant_resolve = tenant_commands.add_parser("resolve", help="find the tenant owning an account")
    tenant_resolve.add_argument("--platform", required=True)
    tenant_resolve.add_argument("--account-id", required=True)
    tenant_resolve.add_argument("--root", default=DEFAULT_TENANT_ROOT)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "validate":
            load_contract(args.contract, args.path)
            _emit({"contract": args.contract, "path": args.path, "status": "valid"})
        elif args.command == "score":
            controls = _read_json(args.controls)
            findings = _read_json(args.findings)
            weights = _read_json(args.weights)
            if not isinstance(controls, list) or not isinstance(findings, list) or not isinstance(weights, dict):
                raise ScoringError("controls/findings must be arrays and weights must be an object")
            _emit(score_account(controls, findings, weights).to_dict())
        elif args.command == "portfolio":
            accounts = _read_json(args.path)
            if not isinstance(accounts, list):
                raise ScoringError("portfolio input must be an array")
            _emit(score_portfolio(accounts).to_dict())
        elif args.command == "status":
            if args.path:
                bundle = _read_json(args.path)
                validate_contract("report-bundle", bundle)
                scoring = bundle["scoring"]
                manifest = bundle["run_manifest"]
                _emit(
                    {
                        "run_id": manifest["run_id"],
                        "completeness": manifest["completeness"],
                        "health_score": scoring["health_score"],
                        "evidence_coverage": scoring["evidence_coverage"],
                        "status": scoring["status"],
                    }
                )
            else:
                if not args.as_of:
                    raise ProductStatusError("repository status requires --as-of YYYY-MM-DD")
                try:
                    as_of = date.fromisoformat(args.as_of)
                except ValueError as exc:
                    raise ProductStatusError("--as-of must be an ISO 8601 date") from exc
                _emit(
                    evaluate_product_status(
                        args.root, as_of=as_of, release_gate_path=args.release_gate
                    )
                )
        elif args.command == "next":
            try:
                as_of = date.fromisoformat(args.as_of)
            except ValueError as exc:
                raise ProductStatusError("--as-of must be an ISO 8601 date") from exc
            status_payload = evaluate_product_status(
                args.root, as_of=as_of, release_gate_path=args.release_gate
            )
            _emit(
                {
                    "schema_version": status_payload["schema_version"],
                    "as_of": status_payload["as_of"],
                    "selection_policy": status_payload["selection_policy"],
                    "next_blocker": status_payload["next_blocker"],
                }
            )
        elif args.command in {"render", "report"}:
            bundle = load_contract("report-bundle", args.path)
            extension = {"markdown": "md", "html": "html", "pdf": "pdf"}[args.format]
            destination = args.output or f"{bundle['run_manifest']['run_id']}/report.{extension}"
            requested = args.lang or os.environ.get("ADBOT_LANG")
            lang = normalize_language(requested)
            output_path = write_report_bundle(bundle, args.format, args.root, destination, lang)
            result = {
                "format": args.format,
                "path": str(output_path),
                "run_id": bundle["run_manifest"]["run_id"],
                "status": "rendered",
            }
            if requested:  # keep the established output contract unchanged unless a language was chosen
                result["lang"] = lang
            _emit(result)
        elif args.command == "doctor":
            environment = dict(os.environ)
            if args.profile_dir:
                environment["ADBOT_PROFILE_DIR"] = str(Path(args.profile_dir).expanduser())
            checks, context = run_doctor(environment, online=args.online)
            if args.json:
                _emit(to_json(checks))
            else:
                requested = args.lang or environment.get("ADBOT_LANG") or context.get("language")
                print(render_text(checks, Translator(normalize_language(requested))), end="")
            return 1 if any(check.status == "fail" for check in checks) else 0
        elif args.command == "settings":
            directory = Path(args.profile_dir).expanduser() if args.profile_dir else profile_dir()
            target = directory / SETTINGS_FILENAME
            if args.settings_command == "init":
                if target.exists() and not args.force:
                    raise SettingsError(f"settings already exist: {target.name} (use --force to overwrite)")
                save_settings(target, default_settings(args.lang))
                _emit({"path": str(target), "status": "created", "lang": args.lang})
            elif args.settings_command == "set":
                current = load_settings(target)
                if args.account is not None:
                    current["active_account_ref"] = None if args.account == "none" else args.account.replace("-", "")
                for option, key in (("watch", "watch"), ("report", "report"), ("weekday", "report_weekday"), ("deep_review", "deep_review")):
                    value = getattr(args, option)
                    if value is not None:
                        current["cadence"][key] = value
                current["updated_at"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
                save_settings(target, current)
                _emit({"path": str(target), "status": "updated"})
            else:
                _emit(load_settings(target))
        elif args.command == "tenant":
            registry = TenantRegistry(getattr(args, "root", DEFAULT_TENANT_ROOT))
            if args.tenant_command == "validate":
                profile = registry.validate(_read_json(args.path))
                _emit({"tenant_id": profile["tenant_id"], "path": args.path, "status": "valid"})
            elif args.tenant_command == "register":
                path = registry.register(_read_json(args.path))
                _emit({"tenant_id": registry.load(path.parent.name)["tenant_id"], "path": str(path), "status": "registered"})
            elif args.tenant_command == "list":
                _emit({"root": str(registry.root), "tenants": [registry.summary(p) for p in registry.list()]})
            elif args.tenant_command == "show":
                _emit(registry.load(args.tenant_id))
            elif args.tenant_command == "resolve":
                _emit(registry.summary(registry.resolve_account(args.platform, args.account_id)))
        elif args.command == "ingest-export":
            _emit(GenericCSVExportAdapter(args.platform).read_snapshot(args.path))
    except (AdapterError, ContractError, I18nError, ProductStatusError, ReportRenderError, ScoringError, SettingsError, TenantError) as exc:
        print(json.dumps({"status": "invalid", "error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
