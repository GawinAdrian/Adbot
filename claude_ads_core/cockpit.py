"""Static, local "cockpit" page: the whole state of an account on one screen, in German or Polish.

The page is a single self-contained HTML file: no scripts, no external fonts or images, no network.  It is
built deterministically from stored JSON (the watcher result plus optional recommendations, pending
approvals, and a change log), so the same input always produces the same bytes.  Every dynamic text is
HTML-escaped.  Account changes are never made here; the page only shows and explains.
"""
from __future__ import annotations

import html
from typing import Any, Mapping, Sequence

from .i18n import Translator, glossary
from .watch import WatchCheck, describe

MAX_RECOMMENDATIONS = 3
RECOMMENDATION_KEYS = ("title", "before", "after", "effort", "risk", "confidence")
CONFIDENCE_VALUES = ("high", "medium", "low", "none")
APPROVAL_KEYS = ("title", "status")
CHANGE_KEYS = ("date", "what", "before", "after")
_AMPEL_CLASS = {"green": "ok", "yellow": "warn", "red": "bad", "unknown": "grey"}
_KPI_ORDER = (("cost", None), ("clicks", "click"), ("impressions", "impression"), ("conversions", "conversion"),
              ("ctr_percent", "ctr"), ("cpa", "cpa"))

_STYLE = """
:root{--ink:#14213d;--muted:#4b5563;--line:#cbd5e1;--paper:#fff;--soft:#f1f5f9;--ok:#14532d;--warn:#7c4a03;--bad:#7f1d1d;--grey:#334155}
*{box-sizing:border-box}body{margin:0;background:#e2e8f0;color:var(--ink);font:18px/1.6 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:980px;margin:24px auto;padding:28px;background:var(--paper)}h1{margin:0 0 4px;font-size:1.7rem}h2{margin:2rem 0 .6rem;font-size:1.25rem;border-bottom:2px solid var(--line);padding-bottom:.3rem}
.sub{color:var(--muted);margin:0 0 1rem}.ampel{display:flex;gap:16px;align-items:center;padding:18px;border-radius:8px;border:3px solid;font-weight:700;font-size:1.3rem}
.ampel .dot{width:34px;height:34px;border-radius:50%;flex:none}.ampel.ok{border-color:var(--ok);color:var(--ok)}.ampel.ok .dot{background:var(--ok)}
.ampel.warn{border-color:var(--warn);color:var(--warn)}.ampel.warn .dot{background:#d97706}.ampel.bad{border-color:var(--bad);color:var(--bad)}.ampel.bad .dot{background:var(--bad)}
.ampel.grey{border-color:var(--grey);color:var(--grey)}.ampel.grey .dot{background:#94a3b8}
table{border-collapse:collapse;width:100%}th,td{padding:8px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}th{background:var(--soft)}th .hint{font-weight:400}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}.hint{color:var(--muted);font-size:.9rem}
.card{border:1px solid var(--line);border-radius:8px;padding:14px 16px;margin:10px 0;background:var(--soft)}.card h3{margin:0 0 6px;font-size:1.05rem}
.tag{display:inline-block;padding:1px 8px;border-radius:10px;border:1px solid var(--line);background:#fff;font-size:.85rem;margin-right:6px}
ul{padding-left:1.2rem}li{margin:.25rem 0}footer{margin-top:2rem;color:var(--muted);font-size:.9rem}
@media (max-width:600px){main{margin:0;padding:16px}body{font-size:17px}th,td{padding:6px}}
""".strip()


class CockpitError(ValueError):
    """Raised when optional cockpit inputs are malformed."""


def _strict_list(value: Any, name: str, keys: Sequence[str]) -> list[Mapping[str, str]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise CockpitError(f"{name} must be a list")
    for index, item in enumerate(value):
        if not isinstance(item, Mapping) or set(item) != set(keys):
            raise CockpitError(f"{name}[{index}] must have exactly the keys: {', '.join(keys)}")
        if not all(isinstance(item[key], str) and item[key].strip() for key in keys):
            raise CockpitError(f"{name}[{index}] values must be non-empty strings")
    return value


def validate_inputs(
    recommendations: Any = None, approvals: Any = None, changes: Any = None
) -> tuple[list[Mapping[str, str]], list[Mapping[str, str]], list[Mapping[str, str]]]:
    """Validate the optional lists; at most three recommendations, confidence from a fixed set."""
    recs = _strict_list(recommendations, "recommendations", RECOMMENDATION_KEYS)
    if len(recs) > MAX_RECOMMENDATIONS:
        raise CockpitError(f"at most {MAX_RECOMMENDATIONS} recommendations are shown; got {len(recs)}")
    for index, rec in enumerate(recs):
        if rec["confidence"] not in CONFIDENCE_VALUES:
            raise CockpitError(f"recommendations[{index}].confidence must be one of: {', '.join(CONFIDENCE_VALUES)}")
    return recs, _strict_list(approvals, "approvals", APPROVAL_KEYS), _strict_list(changes, "changes", CHANGE_KEYS)


def _e(value: object) -> str:
    return html.escape(str(value), quote=True)


def _term(term_id: str, tr: Translator) -> tuple[str, str]:
    for term in glossary()["terms"]:
        if term["id"] == term_id:
            return (term[tr.language] if tr.language in {"de", "pl", "en"} else term["en"],
                    term.get(f"explain_{tr.language}", term["explain_de"]))
    raise CockpitError(f"unknown glossary term {term_id!r}")


def _kpi_value(key: str, value: Any, tr: Translator, currency: str) -> str:
    if value is None:
        return tr.t("cockpit.kpi.na")
    if key in {"cost", "cpa"}:
        return tr.money(float(value), currency)
    if key == "ctr_percent":
        return tr.percent(float(value))
    if key == "conversions":
        return tr.number(float(value), 2)
    return tr.number(float(value), 0)


def build_cockpit(
    watch_result: Mapping[str, Any],
    *,
    lang: str,
    created: str,
    recommendations: Any = None,
    approvals: Any = None,
    changes: Any = None,
) -> str:
    """Return the cockpit as one HTML document (``created`` is an ISO date shown in the header)."""
    tr = Translator(lang)
    recs, pending, log = validate_inputs(recommendations, approvals, changes)
    currency = str(watch_result["currency"])
    checks = [WatchCheck(c["rule"], c["state"], c["status"], c["campaign_id"], c["campaign_name"], c["params"])
              for c in watch_result["checks"]]
    critical = sum(1 for c in checks if c.status == "critical")
    warning = sum(1 for c in checks if c.status == "warning")
    ampel = str(watch_result["ampel"])

    if ampel == "unknown":
        headline = tr.t("cockpit.summary_unknown")
    elif critical or warning:
        headline = tr.t("cockpit.summary_issues", critical=critical, warning=warning)
    else:
        headline = tr.t("cockpit.summary_ok")
    ranked = sorted((c for c in checks if c.status in {"critical", "warning"}),
                    key=lambda c: (0 if c.status == "critical" else 1, c.rule, c.campaign_id or ""))[:5]
    items = []
    for check in ranked:
        text, hint = describe(check, tr, currency)
        items.append(f"<li><span class=\"tag\">{_e(tr.label('check_status', check.status))}</span>{_e(text)}"
                     + (f"<div class=\"hint\">→ {_e(hint)}</div>" if hint else "") + "</li>")
    what = f"<p><strong>{_e(headline)}</strong></p>" + (f"<ul>{''.join(items)}</ul>" if items else "")

    summary = watch_result.get("summary") or {}
    kpi_html = ""
    if summary:
        days = summary["days"]
        rows = []
        for key, term_id in _KPI_ORDER:
            if term_id:
                name, explain = _term(term_id, tr)
            else:
                name, explain = tr.t("cockpit.kpi.cost"), tr.t("cockpit.kpi.cost.explain")
            rows.append(
                f"<tr><th scope=\"row\">{_e(name)}<div class=\"hint\">{_e(explain)}</div></th>"
                f"<td class=\"num\">{_e(_kpi_value(key, summary['last'][key], tr, currency))}</td>"
                f"<td class=\"num\">{_e(_kpi_value(key, summary['previous'][key], tr, currency))}</td></tr>")
        kpi_html = (f"<h2>{_e(tr.t('cockpit.kpis', days=days))}</h2><table><thead><tr><th></th>"
                    f"<th class=\"num\">{_e(tr.t('cockpit.kpi.column_now', days=days))}</th>"
                    f"<th class=\"num\">{_e(tr.t('cockpit.kpi.column_before', days=days))}</th></tr></thead><tbody>"
                    + "".join(rows) + "</tbody></table>")

    if recs:
        cards = "".join(
            f"<div class=\"card\"><h3>{_e(r['title'])}</h3>"
            f"<p><strong>{_e(tr.t('cockpit.rec.before'))}:</strong> {_e(r['before'])}<br>"
            f"<strong>{_e(tr.t('cockpit.rec.after'))}:</strong> {_e(r['after'])}</p>"
            f"<span class=\"tag\">{_e(tr.t('cockpit.rec.effort'))}: {_e(r['effort'])}</span>"
            f"<span class=\"tag\">{_e(tr.t('cockpit.rec.risk'))}: {_e(r['risk'])}</span>"
            f"<span class=\"tag\">{_e(tr.t('cockpit.rec.confidence'))}: {_e(tr.label('confidence', r['confidence']))}</span></div>"
            for r in recs)
    else:
        cards = f"<p>{_e(tr.t('cockpit.no_recommendations'))}</p>"

    approvals_html = ("<ul>" + "".join(f"<li>{_e(a['title'])} <span class=\"tag\">{_e(tr.t('cockpit.status.pending')) if a['status'] == 'pending' else _e(a['status'])}</span></li>" for a in pending)
                      + "</ul>") if pending else f"<p>{_e(tr.t('cockpit.no_approvals'))}</p>"
    changes_html = ("<table><tbody>" + "".join(
        f"<tr><td>{_e(tr.date(c['date']))}</td><td>{_e(c['what'])}<div class=\"hint\">{_e(tr.t('cockpit.change.before'))}: {_e(c['before'])} · "
        f"{_e(tr.t('cockpit.change.after'))}: {_e(c['after'])}</div></td></tr>" for c in log) + "</tbody></table>") if log else f"<p>{_e(tr.t('cockpit.no_changes'))}</p>"

    notes = []
    for missing in watch_result.get("missing_inputs", []):
        key = {"ad policy status": "watch.missing.policy", "billing and payment status": "watch.missing.billing"}.get(missing)
        notes.append(f"<li>{_e(tr.t(key) if key else missing)}</li>")
    for check in checks:
        if check.rule == "data" and check.status != "normal":
            text, hint = describe(check, tr, currency)
            notes.append(f"<li>{_e(text)}" + (f"<div class=\"hint\">→ {_e(hint)}</div>" if hint else "") + "</li>")
    notes_html = f"<ul>{''.join(notes)}</ul>" if notes else f"<p>{_e(tr.t('cockpit.no_notes'))}</p>"

    all_rows = "".join(
        f"<tr><td>{_e(tr.label('check_status', c.status))}</td><td>{_e(describe(c, tr, currency)[0])}</td></tr>" for c in checks)
    title = _e(tr.t("cockpit.title"))
    return (
        f"<!doctype html>\n<html lang=\"{tr.language}\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        f"<title>{title}</title><style>{_STYLE}</style></head><body><main>"
        f"<h1>{title}</h1><p class=\"sub\">{_e(tr.t('cockpit.generated', date=tr.date(created)))}</p>"
        f"<div class=\"ampel {_AMPEL_CLASS[ampel]}\" role=\"status\"><span class=\"dot\" aria-hidden=\"true\"></span>"
        f"<span>{_e(tr.t(f'watch.ampel.{ampel}'))}</span></div>"
        f"<h2>{_e(tr.t('cockpit.what_happened'))}</h2>{what}{kpi_html}"
        f"<h2>{_e(tr.t('cockpit.recommendations'))}</h2>{cards}"
        f"<h2>{_e(tr.t('cockpit.approvals'))}</h2>{approvals_html}"
        f"<h2>{_e(tr.t('cockpit.changes'))}</h2>{changes_html}"
        f"<h2>{_e(tr.t('cockpit.notes'))}</h2>{notes_html}"
        f"<details><summary>{_e(tr.t('cockpit.checks'))}</summary><table><tbody>{all_rows}</tbody></table></details>"
        f"<footer>{_e(tr.t('cockpit.footer'))}</footer></main></body></html>\n"
    )
