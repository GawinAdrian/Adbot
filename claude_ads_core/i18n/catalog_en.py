"""Message catalog for language ``en`` (flat keys; see ``claude_ads_core.i18n``).

Shipped as a Python module so that no package-data entry is needed.
"""
from __future__ import annotations

META = {'language': 'en', 'review_status': 'reference', 'reviewed_by': None}

MESSAGES = {'report.title': 'Claude Ads Audit Report',
 'report.run_completeness': 'Run completeness',
 'report.evidence_status': 'Evidence status',
 'report.run_summary': 'Run summary',
 'report.run_id': 'Run ID',
 'report.started': 'Started',
 'report.platform': 'Platform',
 'report.account': 'Account',
 'report.window': 'Window',
 'report.window_range': '{start} to {end}',
 'report.privacy_class': 'Privacy class',
 'report.decision_status': 'Decision status',
 'report.health_score': 'Health score',
 'report.evidence_coverage': 'Evidence coverage',
 'report.warning_label': 'Warning:',
 'report.warning_label_md': 'WARNING:',
 'report.warn_incomplete': 'Required work did not complete; this report must not be presented as a '
                           'complete audit.',
 'report.warn_provisional': 'The health score is provisional because evidence coverage is below '
                            'the normal threshold.',
 'report.warn_insufficient': 'Evidence is insufficient for a defensible health score.',
 'report.category_health': 'Category health',
 'report.no_categories': 'No category scores were supplied.',
 'report.uncategorized': 'Uncategorized',
 'report.evidence_lower': 'evidence',
 'report.findings': 'Findings',
 'report.no_findings': 'No findings were supplied.',
 'report.severity': 'Severity',
 'report.confidence': 'Confidence',
 'report.source_classification': 'Source classification',
 'report.observation': 'Observation',
 'report.diagnosis': 'Diagnosis',
 'report.recommended_action': 'Recommended action',
 'report.evidence': 'Evidence',
 'report.no_evidence': 'No evidence was supplied.',
 'report.not_supplied': 'Not supplied.',
 'report.no_action': 'No action supplied.',
 'report.not_specified': 'not specified',
 'report.contradictions': 'Contradictions',
 'report.no_contradictions': 'No contradictions were reported.',
 'report.prioritized_actions': 'Prioritized actions',
 'report.no_actions': 'No follow-up actions were reported.',
 'report.footer': 'Generated deterministically from ReportBundle JSON. Scores were not '
                  'recalculated.',
 'report.not_scored': 'Not scored',
 'enum.completeness.complete': 'Complete',
 'enum.completeness.partial': 'Partial',
 'enum.completeness.failed': 'Failed',
 'enum.score_status.normal': 'Normal',
 'enum.score_status.provisional': 'Provisional',
 'enum.score_status.insufficient_evidence': 'Insufficient evidence'}
