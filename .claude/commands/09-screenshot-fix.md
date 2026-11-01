---
description: Screenshot-basierte Bug-Analyse und Fix für Adbot (Reports, UI, Terminal-Output)
argument-hint: [Pfad zum Screenshot]
---

# Screenshot Fix

## Screenshot analysieren

Lies das Bild: `$ARGUMENTS`

1. **Was ist das Problem?** (Report-Rendering, Dashboard-UI, CLI-Output, Google-Ads-Oberfläche?)
2. **Welche Komponente?** — `claude_ads_core/reporting.py`, ein Skill-Output, ein Frontend (falls vorhanden)
3. **Erwartetes Verhalten**

## Code-Recherche

Komponente finden (`grep -rn` in `claude_ads_core/`, `skills/`, ggf. `frontend/`), Datenfluss prüfen (Schema → Normalisierung → Scoring → Rendering).

## Fix

Root Cause statt Symptom. Minimal (1-2 Dateien), keine Refactorings. Regression-Test/Fixture ergänzen.

```bash
[ -x .venv/bin/python ] && PY=.venv/bin/python || PY=python3
$PY -m pytest -q
```

## Output

```
Screenshot-Fix abgeschlossen
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Problem · Komponente · Root Cause · Fix (Dateien/Zeilen) · Validierung ✅/❌
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Nächster Schritt:** `/05-commit`
