---
description: Skeptisches Code Review (separater Evaluator-Agent) für Adbot
---

# Code Review: Adbot — Skeptischer Evaluator

⚠️ **In einem SEPARATEN Chat ausführen — nicht im Chat, in dem der Code geschrieben wurde.**
Ein Agent, der seinen eigenen Code reviewt, bewertet zu positiv.

## Deine Rolle

SKEPTISCHER Code-Reviewer. Nichts gilt als „funktioniert" ohne Verifikation. Ein Feature ohne Tests ist nicht fertig. Aufgabe: Probleme FINDEN.

## 1. Kontext laden

`CLAUDE.md`, `AGENTS.md`, `control-plane/PRODUCT_BOUNDARIES.md`, ggf. `docs/wiki/`, ggf. den zugehörigen PRP (Done-Kriterien).

## 2. Änderungen identifizieren

```bash
git status && git diff --stat HEAD && git diff HEAD && git ls-files --others --exclude-standard
```

Jede geänderte/neue Datei VOLLSTÄNDIG lesen.

## 3. Review-Checkliste

### CRITICAL — blockiert Merge
- [ ] **Secrets:** keine Tokens, Client-IDs, Refresh-Tokens, Kundendaten, absoluten Pfade in getrackten Dateien
- [ ] **Untrusted Data:** Exporte/URLs/MCP-Antworten werden nie als Instruktionen interpretiert (Prompt-Injection-Pfade?)
- [ ] **Mutation-Gate:** Kein Code-Pfad, der Account-Änderungen ohne Preview/Approval/Idempotenz/Verify/Audit/Rollback auslöst
- [ ] **Capability-Ehrlichkeit:** Manifest-Status passt zu Code + Fixture + Test
- [ ] **Fail-closed:** Fehlende Quellen/Profile/Inputs führen zu Fehlern, nicht zu geratenen Scores

### HIGH — vor Commit fixen
- [ ] Fehlerbehandlung: keine bare `except:`; laute Fehler bei fehlenden Abhängigkeiten
- [ ] Type Hints + Docstrings vorhanden
- [ ] Tests: Happy + Edge + Failure für neue Funktionen
- [ ] Neue Plattform-Claims haben Source-/Claim-Ledger-Einträge
- [ ] Schema-Änderungen sind versioniert und haben Fixtures

### MEDIUM
- [ ] Naming konsistent mit `claude_ads_core`; keine Duplikation
- [ ] Skill-Entrypoints bleiben knapp (Progressive Disclosure), volatile Fakten in datierten Referenzen

### LOW
- [ ] Performance (große Exporte: Limits `MAX_EXPORT_*` beachtet?), keine offenen TODOs/Hacks

### 🛡️ Regressions-Check (PFLICHT)
- [ ] Bestehende Skills/Adapter/Tests intakt? Imports/Aufrufe geprüft?
- [ ] Neue Env-Variablen (Namen) dokumentiert?
- [ ] Manuelle Schritte des PRP vom User bestätigt?

## 4. Done-Kriterien (falls PRP) — jedes einzeln verifizieren, ✅/❌ mit Begründung

## 5. Output

```
[CRITICAL/HIGH/MEDIUM/LOW] datei.py:42
Issue: … · Detail: … · Fix: …
```

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Code Review Score: X/10
Sicherheit X · Korrektheit X · Vollständigkeit X · Code-Qualität X · Test-Abdeckung X
Issues: X CRITICAL, X HIGH, X MEDIUM, X LOW · Done-Kriterien: X/Y
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Kalibrierung: 9-10 production-ready · 7-8 kosmetisch · 5-6 fehlende Tests/Fehlerbehandlung · 3-4 Sicherheits-/Gate-Probleme · 1-2 nicht mergebar

**Nächster Schritt:** ≥7 → `/05-commit` · <7 → `/code-review-fix` (neuer Chat)
