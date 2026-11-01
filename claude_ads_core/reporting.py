"""Deterministic, privacy-aware renderers for validated report bundles.

JSON remains the canonical artifact.  This module produces human-readable
views without recalculating scores, loading remote assets, or embedding the
source bundle in the output.
"""

from __future__ import annotations

import html
import importlib
import json
import os
import re
import stat
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence

from .contracts import ContractError, validate_contract
from .i18n import Translator


class ReportRenderError(ValueError):
    """Raised when a report cannot be rendered or written safely."""


class PDFDependencyError(ReportRenderError):
    """Raised when the optional PDF renderer is unavailable."""


_EMAIL_RE = re.compile(r"(?<![\w.+-])[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}(?![\w.-])")
_BEARER_RE = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]+")
_SECRET_ASSIGNMENT_RE = re.compile(
    r"(?i)\b(access[_-]?token|refresh[_-]?token|api[_-]?key|client[_-]?secret|"
    r"password|passwd|authorization|cookie)\s*([:=])\s*([^\s&;,]+)"
)
_SENSITIVE_KEY_RE = re.compile(
    r"(?i)(^|[_-])(access[_-]?token|refresh[_-]?token|api[_-]?key|client[_-]?secret|"
    r"password|passwd|authorization|cookie|set[_-]?cookie|email|phone)([_-]|$)"
)
_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def _redact_text(value: str) -> str:
    value = _CONTROL_CHARS_RE.sub("", value).replace("\r\n", "\n").replace("\r", "\n")
    value = _BEARER_RE.sub("Bearer [REDACTED]", value)
    value = _SECRET_ASSIGNMENT_RE.sub(lambda match: f"{match.group(1)}{match.group(2)}[REDACTED]", value)
    return _EMAIL_RE.sub("[REDACTED EMAIL]", value)


def _redact_value(value: Any, *, key: str | None = None) -> Any:
    if key is not None and _SENSITIVE_KEY_RE.search(key):
        return "[REDACTED]"
    if isinstance(value, Mapping):
        return {str(item_key): _redact_value(item, key=str(item_key)) for item_key, item in value.items()}
    if isinstance(value, list):
        return [_redact_value(item) for item in value]
    if isinstance(value, tuple):
        return [_redact_value(item) for item in value]
    if isinstance(value, str):
        return _redact_text(value)
    return value


def _text(value: Any) -> str:
    if value is None:
        return ""
    return _redact_text(str(value)).replace("\n", " ").strip()


def _md(value: Any) -> str:
    """Make untrusted text inert in a single Markdown paragraph."""

    text = _text(value)
    return re.sub(r"([\\`*_{}\[\]()<>#+.!|>-])", r"\\\1", text)


def _html(value: Any) -> str:
    return html.escape(_text(value), quote=True)


def _canonical_json(value: Any) -> str:
    return json.dumps(_redact_value(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _validated_bundle(bundle: Mapping[str, Any]) -> Mapping[str, Any]:
    try:
        validate_contract("report-bundle", bundle)
    except ContractError as exc:
        raise ReportRenderError(f"invalid report bundle: {exc}") from exc
    for field in ("contradictions", "actions"):
        if field in bundle and not isinstance(bundle[field], list):
            raise ReportRenderError(f"$.{field} must be an array when present")
    return bundle


def _score_text(score: Any, tr: Translator | None = None) -> str:
    tr = tr or Translator("en")
    return tr.score(None if score is None else float(score))


def _coverage_text(coverage: Any, tr: Translator | None = None) -> str:
    tr = tr or Translator("en")
    return tr.percent(float(coverage))


def _category_label(tr: Translator, value: Any) -> str:
    """Localized category name; unknown categories keep the legacy title-case text."""
    if value is None:
        return tr.t("report.uncategorized")
    text = str(value)
    if tr.has(f"enum.category.{text}"):
        return tr.label("category", text)
    return text.title()


def _unspecified(tr: Translator) -> str:
    text = tr.t("report.not_specified")
    return text.title() if tr.language == "en" else text


def _controls(bundle: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    return {str(control["control_id"]): control for control in bundle["control_definitions"]}


def _findings(bundle: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    return sorted(bundle["findings"], key=lambda finding: str(finding["control_id"]))


def _categories(bundle: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    return sorted(bundle["scoring"]["categories"], key=lambda category: str(category.get("category", "")))


def _extension_item_text(item: Any, tr: Translator | None = None) -> str:
    tr = tr or Translator("en")
    if isinstance(item, str):
        return _text(item)
    if isinstance(item, Mapping):
        preferred = ("summary", "title", "action", "claim", "description", "recommendation")
        headline = next((_text(item[key]) for key in preferred if item.get(key)), "")
        details = [
            f"{tr.label('item_key', key)}: {_text(value)}"
            for key, value in sorted(item.items(), key=lambda pair: str(pair[0]))
            if key not in preferred and value not in (None, "", [], {})
        ]
        if headline and details:
            return f"{headline} ({'; '.join(details)})"
        return headline or "; ".join(details) or _canonical_json(item)
    return _text(item)


def _actions(bundle: Mapping[str, Any]) -> list[Any]:
    explicit = list(bundle.get("actions", []))
    if explicit:
        return explicit
    return [
        {
            "action": finding["recommendation"],
            "confidence": finding["confidence"],
            "control_id": finding["control_id"],
        }
        for finding in _findings(bundle)
        if finding["status"] in {"fail", "unknown"} and _text(finding.get("recommendation"))
    ]


def render_markdown(bundle: Mapping[str, Any], lang: str | None = "en") -> str:
    """Render a validated ReportBundle as deterministic Markdown in *lang* (de, pl, en)."""

    tr = Translator(lang)
    bundle = _validated_bundle(bundle)
    manifest = bundle["run_manifest"]
    snapshot = bundle["account_snapshot"]
    scoring = bundle["scoring"]
    controls = _controls(bundle)
    completeness = str(manifest["completeness"])
    score_status = str(scoring["status"])
    account = snapshot["account"]

    lines = [
        f"# {tr.t('report.title')}",
        "",
        f"> {tr.t('report.run_completeness')}: **{tr.label('completeness', completeness)}** · "
        f"{tr.t('report.evidence_status')}: **{tr.label('score_status', score_status)}**",
        "",
        f"## {tr.t('report.run_summary')}",
        "",
        f"- {tr.t('report.run_id')}: {_md(manifest['run_id'])}",
        f"- {tr.t('report.started')}: {_md(manifest['started_at'])}",
        f"- {tr.t('report.platform')}: {_md(str(account['platform']).title())}",
        f"- {tr.t('report.account')}: {_md(account.get('name') or account['account_id'])}",
        f"- {tr.t('report.window')}: {_md(tr.t('report.window_range', start=snapshot['window']['start'], end=snapshot['window']['end']))}",
        f"- {tr.t('report.privacy_class')}: {_md(tr.label('privacy_class', manifest['privacy_class']))}",
        "",
        f"## {tr.t('report.decision_status')}",
        "",
        f"- {tr.t('report.run_completeness')}: **{tr.label('completeness', completeness)}**",
        f"- {tr.t('report.evidence_status')}: **{tr.label('score_status', score_status)}**",
        f"- {tr.t('report.health_score')}: **{_score_text(scoring['health_score'], tr)}**",
        f"- {tr.t('report.evidence_coverage')}: **{_coverage_text(scoring['evidence_coverage'], tr)}**",
    ]
    if completeness != "complete":
        lines.extend(("", f"> {tr.t('report.warning_label_md')} {tr.t('report.warn_incomplete')}"))
    if score_status == "provisional":
        lines.extend(("", f"> {tr.t('report.warning_label_md')} {tr.t('report.warn_provisional')}"))
    elif score_status == "insufficient_evidence":
        lines.extend(("", f"> {tr.t('report.warning_label_md')} {tr.t('report.warn_insufficient')}"))

    lines.extend(("", f"## {tr.t('report.category_health')}", ""))
    categories = _categories(bundle)
    if categories:
        for category in categories:
            lines.append(
                f"- **{_md(_category_label(tr, category.get('category')))}:** "
                f"{_score_text(category.get('health_score'), tr)}; {tr.t('report.evidence_lower')} {_coverage_text(category.get('evidence_coverage', 0), tr)}"
            )
    else:
        lines.append(tr.t("report.no_categories"))

    lines.extend(("", f"## {tr.t('report.findings')}", ""))
    findings = _findings(bundle)
    if not findings:
        lines.append(tr.t("report.no_findings"))
    for finding in findings:
        control = controls.get(str(finding["control_id"]), {})
        heading = (
            f"### [{_md(tr.label('finding_status', finding['status']).upper())}] "
            f"{_md(finding['control_id'])} — {_md(_category_label(tr, control.get('category', 'uncategorized')))}"
        )
        lines.extend(
            (
                heading,
                "",
                f"- {tr.t('report.severity')}: {_md(tr.label('severity', control['severity']) if 'severity' in control else _unspecified(tr))}",
                f"- {tr.t('report.confidence')}: {_md(tr.label('confidence', finding['confidence']))}",
                f"- {tr.t('report.source_classification')}: {_md(tr.label('source_classification', finding['source_classification']) if 'source_classification' in finding else _unspecified(tr))}",
                "",
                f"**{tr.t('report.observation')}:** {_md(finding['observation']) or tr.t('report.not_supplied')}",
                "",
                f"**{tr.t('report.diagnosis')}:** {_md(finding['diagnosis']) or tr.t('report.not_supplied')}",
                "",
                f"**{tr.t('report.recommended_action')}:** {_md(finding['recommendation']) or tr.t('report.no_action')}",
                "",
                f"**{tr.t('report.evidence')}:**",
                "",
            )
        )
        if finding["evidence"]:
            for index, evidence in enumerate(finding["evidence"], start=1):
                lines.extend((f"{index}.", "", f"        {_canonical_json(evidence)}", ""))
        else:
            lines.extend((tr.t("report.no_evidence"), ""))

    lines.extend((f"## {tr.t('report.contradictions')}", ""))
    contradictions = list(bundle.get("contradictions", []))
    if contradictions:
        lines.extend(f"- {_md(_extension_item_text(item, tr))}" for item in contradictions)
    else:
        lines.append(tr.t("report.no_contradictions"))

    lines.extend(("", f"## {tr.t('report.prioritized_actions')}", ""))
    actions = _actions(bundle)
    if actions:
        lines.extend(f"{index}. {_md(_extension_item_text(item, tr))}" for index, item in enumerate(actions, start=1))
    else:
        lines.append(tr.t("report.no_actions"))

    lines.extend(("", "---", "", tr.t("report.footer"), ""))
    return "\n".join(lines)


_HTML_STYLE = """
:root{color-scheme:light;--ink:#172033;--muted:#596579;--line:#d8dee9;--paper:#fff;--soft:#f5f7fa;--ok:#18794e;--warn:#9a6700;--bad:#c62828}
*{box-sizing:border-box}body{margin:0;background:#eef1f5;color:var(--ink);font:15px/1.55 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
main{max-width:960px;margin:32px auto;padding:40px;background:var(--paper);box-shadow:0 8px 30px #17203318}h1,h2,h3{line-height:1.2}h1{margin-top:0}h2{margin-top:2rem;border-bottom:1px solid var(--line);padding-bottom:.4rem}h3{margin-top:1.5rem}.banner{padding:12px 16px;border-left:5px solid var(--ok);background:var(--soft);font-weight:700}.banner.partial,.banner.failed,.banner.provisional{border-color:var(--warn)}.banner.insufficient_evidence{border-color:var(--bad)}.warning{padding:10px 14px;background:#fff6d6;border:1px solid #e9c46a}.metrics{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px}.metric{padding:14px;background:var(--soft);border:1px solid var(--line)}.metric strong{display:block;font-size:1.25rem}.meta{display:grid;grid-template-columns:max-content 1fr;gap:4px 16px}.finding{padding:18px;margin:14px 0;border:1px solid var(--line);border-radius:6px}.status-pass{border-left:5px solid var(--ok)}.status-fail{border-left:5px solid var(--bad)}.status-unknown{border-left:5px solid var(--warn)}pre{overflow-wrap:anywhere;white-space:pre-wrap;background:var(--soft);padding:10px;border:1px solid var(--line)}dt{font-weight:700}dd{margin:0 0 10px}footer{margin-top:2rem;padding-top:1rem;border-top:1px solid var(--line);color:var(--muted)}@media print{body{background:#fff}main{box-shadow:none;margin:0;max-width:none}}
""".strip()


def render_html(bundle: Mapping[str, Any], lang: str | None = "en") -> str:
    """Render a validated ReportBundle as self-contained deterministic HTML in *lang*."""

    tr = Translator(lang)
    bundle = _validated_bundle(bundle)
    manifest = bundle["run_manifest"]
    snapshot = bundle["account_snapshot"]
    scoring = bundle["scoring"]
    controls = _controls(bundle)
    completeness = str(manifest["completeness"])
    score_status = str(scoring["status"])
    account = snapshot["account"]
    warnings: list[str] = []
    if completeness != "complete":
        warnings.append(tr.t("report.warn_incomplete"))
    if score_status == "provisional":
        warnings.append(tr.t("report.warn_provisional"))
    elif score_status == "insufficient_evidence":
        warnings.append(tr.t("report.warn_insufficient"))

    category_html = "".join(
        ("<li><strong>{}</strong>: {}; " + html.escape(tr.t("report.evidence_lower")) + " {}</li>").format(
            _html(_category_label(tr, category.get("category"))),
            _html(_score_text(category.get("health_score"), tr)),
            _html(_coverage_text(category.get("evidence_coverage", 0), tr)),
        )
        for category in _categories(bundle)
    ) or f"<li>{_html(tr.t('report.no_categories'))}</li>"

    finding_parts: list[str] = []
    for finding in _findings(bundle):
        control = controls.get(str(finding["control_id"]), {})
        evidence = "".join(f"<pre>{html.escape(_canonical_json(item))}</pre>" for item in finding["evidence"])
        if not evidence:
            evidence = f"<p>{_html(tr.t('report.no_evidence'))}</p>"
        status = str(finding["status"])
        finding_parts.append(
            f'<article class="finding status-{html.escape(status)}">'
            f"<h3>[{_html(tr.label('finding_status', status).upper())}] {_html(finding['control_id'])} — "
            f"{_html(_category_label(tr, control.get('category', 'uncategorized')))}</h3>"
            "<dl>"
            f"<dt>{_html(tr.t('report.severity'))}</dt><dd>{_html(tr.label('severity', control['severity']) if 'severity' in control else _unspecified(tr))}</dd>"
            f"<dt>{_html(tr.t('report.confidence'))}</dt><dd>{_html(tr.label('confidence', finding['confidence']))}</dd>"
            f"<dt>{_html(tr.t('report.source_classification'))}</dt><dd>{_html(tr.label('source_classification', finding['source_classification']) if 'source_classification' in finding else _unspecified(tr))}</dd>"
            f"<dt>{_html(tr.t('report.observation'))}</dt><dd>{_html(finding['observation']) or html.escape(tr.t('report.not_supplied'))}</dd>"
            f"<dt>{_html(tr.t('report.diagnosis'))}</dt><dd>{_html(finding['diagnosis']) or html.escape(tr.t('report.not_supplied'))}</dd>"
            f"<dt>{_html(tr.t('report.recommended_action'))}</dt><dd>{_html(finding['recommendation']) or html.escape(tr.t('report.no_action'))}</dd>"
            f"</dl><h4>{_html(tr.t('report.evidence'))}</h4>{evidence}</article>"
        )
    findings_html = "".join(finding_parts) or f"<p>{_html(tr.t('report.no_findings'))}</p>"

    contradictions = list(bundle.get("contradictions", []))
    contradictions_html = (
        "<ul>" + "".join(f"<li>{_html(_extension_item_text(item, tr))}</li>" for item in contradictions) + "</ul>"
        if contradictions
        else f"<p>{_html(tr.t('report.no_contradictions'))}</p>"
    )
    actions = _actions(bundle)
    actions_html = (
        "<ol>" + "".join(f"<li>{_html(_extension_item_text(item, tr))}</li>" for item in actions) + "</ol>"
        if actions
        else f"<p>{_html(tr.t('report.no_actions'))}</p>"
    )
    warnings_html = "".join(
        f'<p class="warning"><strong>{_html(tr.t("report.warning_label"))}</strong> {_html(item)}</p>' for item in warnings
    )

    title = _html(tr.t("report.title"))
    return (
        f"<!doctype html>\n<html lang=\"{tr.language}\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        f"<title>{title}</title><style>" + _HTML_STYLE + f"</style></head><body><main><h1>{title}</h1>"
        f'<p class="banner {html.escape(completeness)} {html.escape(score_status)}">{_html(tr.t("report.run_completeness"))}: '
        f"{_html(tr.label('completeness', completeness))} · {_html(tr.t('report.evidence_status'))}: {_html(tr.label('score_status', score_status))}</p>"
        f"<h2>{_html(tr.t('report.run_summary'))}</h2><dl class=\"meta\">"
        f"<dt>{_html(tr.t('report.run_id'))}</dt><dd>{_html(manifest['run_id'])}</dd>"
        f"<dt>{_html(tr.t('report.started'))}</dt><dd>{_html(manifest['started_at'])}</dd>"
        f"<dt>{_html(tr.t('report.platform'))}</dt><dd>{_html(str(account['platform']).title())}</dd>"
        f"<dt>{_html(tr.t('report.account'))}</dt><dd>{_html(account.get('name') or account['account_id'])}</dd>"
        f"<dt>{_html(tr.t('report.window'))}</dt><dd>{_html(tr.t('report.window_range', start=snapshot['window']['start'], end=snapshot['window']['end']))}</dd>"
        f"<dt>{_html(tr.t('report.privacy_class'))}</dt><dd>{_html(tr.label('privacy_class', manifest['privacy_class']))}</dd></dl>"
        f"<h2>{_html(tr.t('report.decision_status'))}</h2><div class=\"metrics\">"
        f'<div class="metric">{_html(tr.t("report.run_completeness"))}<strong>{_html(tr.label("completeness", completeness))}</strong></div>'
        f'<div class="metric">{_html(tr.t("report.evidence_status"))}<strong>{_html(tr.label("score_status", score_status))}</strong></div>'
        f'<div class="metric">{_html(tr.t("report.health_score"))}<strong>{_html(_score_text(scoring["health_score"], tr))}</strong></div>'
        f'<div class="metric">{_html(tr.t("report.evidence_coverage"))}<strong>{_html(_coverage_text(scoring["evidence_coverage"], tr))}</strong></div></div>'
        + warnings_html
        + f"<h2>{_html(tr.t('report.category_health'))}</h2><ul>{category_html}</ul><h2>{_html(tr.t('report.findings'))}</h2>{findings_html}"
        + f"<h2>{_html(tr.t('report.contradictions'))}</h2>{contradictions_html}<h2>{_html(tr.t('report.prioritized_actions'))}</h2>{actions_html}"
        + f"<footer>{_html(tr.t('report.footer'))}</footer>"
        + "</main></body></html>\n"
    )


def render_pdf(bundle: Mapping[str, Any], lang: str | None = "en") -> bytes:
    """Render PDF bytes through the optional WeasyPrint bridge."""

    source = render_html(bundle, lang)
    try:
        weasyprint = importlib.import_module("weasyprint")
    except (ImportError, OSError) as exc:
        raise PDFDependencyError(
            "PDF rendering requires the optional 'weasyprint' package and its system libraries; "
            "install WeasyPrint or render Markdown/HTML instead"
        ) from exc
    try:
        result = weasyprint.HTML(string=source, base_url=None).write_pdf()
    except Exception as exc:
        raise ReportRenderError(f"PDF rendering failed: {exc}") from exc
    if not isinstance(result, bytes):
        raise ReportRenderError("PDF renderer returned an invalid result")
    return result


def render_report(bundle: Mapping[str, Any], output_format: str, lang: str | None = "en") -> str | bytes:
    """Render *bundle* to ``markdown``, ``html``, or ``pdf`` in *lang* (de, pl, en)."""

    normalized = output_format.lower()
    if normalized in {"md", "markdown"}:
        return render_markdown(bundle, lang)
    if normalized == "html":
        return render_html(bundle, lang)
    if normalized == "pdf":
        return render_pdf(bundle, lang)
    raise ReportRenderError("format must be one of: markdown, html, pdf")


def resolve_report_path(root: str | Path, destination: str | Path) -> Path:
    """Resolve a relative output path beneath *root*, rejecting symlinks."""

    relative = Path(destination)
    if relative.is_absolute() or not relative.name or any(part in {"", ".", ".."} for part in relative.parts):
        raise ReportRenderError("report output must be a non-empty relative path without traversal")
    root_path = Path(root)
    root_path.mkdir(parents=True, exist_ok=True)
    root_resolved = root_path.resolve(strict=True)
    if not root_resolved.is_dir():
        raise ReportRenderError("report root must be a directory")

    parent = root_resolved
    for part in relative.parts[:-1]:
        candidate = parent / part
        if os.path.lexists(candidate):
            mode = candidate.lstat().st_mode
            if stat.S_ISLNK(mode):
                raise ReportRenderError("report output parent must not be a symlink")
            if not stat.S_ISDIR(mode):
                raise ReportRenderError("report output parent must be a directory")
        else:
            candidate.mkdir(mode=0o700)
        parent = candidate

    destination_path = parent / relative.name
    if os.path.lexists(destination_path) and stat.S_ISLNK(destination_path.lstat().st_mode):
        raise ReportRenderError("report output must not be a symlink")
    try:
        parent.resolve(strict=True).relative_to(root_resolved)
    except (OSError, ValueError) as exc:
        raise ReportRenderError("report output escapes the configured root") from exc
    return destination_path


def atomic_write_report(root: str | Path, destination: str | Path, content: str | bytes) -> Path:
    """Atomically write report content beneath a safe root."""

    output_path = resolve_report_path(root, destination)
    file_descriptor, temporary_name = tempfile.mkstemp(prefix=f".{output_path.name}.", dir=output_path.parent)
    temporary_path = Path(temporary_name)
    try:
        mode = "wb" if isinstance(content, bytes) else "w"
        kwargs = {} if isinstance(content, bytes) else {"encoding": "utf-8", "newline": "\n"}
        with os.fdopen(file_descriptor, mode, **kwargs) as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary_path, 0o600)
        # Recheck after writing so a swapped parent or destination cannot be
        # silently followed at commit time.
        checked_path = resolve_report_path(root, destination)
        if checked_path.parent.resolve(strict=True) != output_path.parent.resolve(strict=True):
            raise ReportRenderError("report output parent changed during write")
        os.replace(temporary_path, checked_path)
        return checked_path
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise


def write_report_bundle(
    bundle: Mapping[str, Any],
    output_format: str,
    root: str | Path,
    destination: str | Path,
    lang: str | None = "en",
) -> Path:
    """Validate, render, and atomically write a report bundle."""

    return atomic_write_report(root, destination, render_report(bundle, output_format, lang))
