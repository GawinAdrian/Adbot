---
description: End-to-End Feature-Entwicklung für Adbot (Plan → Execute → Validate → Review → Commit)
argument-hint: [Feature-Beschreibung in 1-2 Sätzen]
---

# End-to-End Feature

## Feature

$ARGUMENTS

Nur für klar definierte Features. Bei komplexen Features Schritt für Schritt (`/01-plan` → `/02-execute` → …).

## Schritt 1: Kontext laden
`CLAUDE.md`, `AGENTS.md`, `ads/SKILL.md`, `docs/PRDs/PRD_Adbot.md`, `docs/wiki/` (falls vorhanden), `control-plane/manifests/capability-manifest.json`.

## Schritt 2: Planen (= /01-plan)
PRP nach `docs/PRPs/PRP_[Name].md`. Kurze Zusammenfassung an den User: betroffene/neue Dateien, Komplexität, Risiken, Manifest-Änderungen, manuelle Schritte.

**⚠️ PAUSE: Warte auf Bestätigung des Users.**

## Schritt 3: Implementieren (= /02-execute)
Adbot-Regeln (untrusted data, capability honesty, read-only default, keine Secrets). Tests: Happy + Edge + Failure.

## Schritt 4: Validieren (= /03-validate)
```bash
[ -x .venv/bin/python ] && PY=.venv/bin/python || PY=python3
$PY -m pytest -q && $PY -m claude_ads_core --version && bash -n install.sh uninstall.sh
```

## Schritt 5: Review (= /04-review, Kurzform)
Secrets? Untrusted-Data-Pfade? Mutation-Gate? Manifest ehrlich? Tests vorhanden?

## Schritt 6: Commit (= /05-commit)
```bash
git add -A && git commit -m "feat(scope): …"
```

## Abschluss
```
Feature-Entwicklung abgeschlossen
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. ✅ Kontext · 2. ✅ PRP · 3. ✅ Implementiert · 4. ✅ Validiert · 5. ✅ Reviewed · 6. ✅ Committed [hash]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
