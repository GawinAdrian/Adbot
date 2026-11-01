---
description: Schneller Bugfix-Workflow für Adbot (Diagnose → Fix → Validate → Commit)
argument-hint: [Bug-Beschreibung]
---

# Bugfix: Schneller Fix ohne PRP

## Problem

$ARGUMENTS

## Phase 1: Diagnose

Kontext je nach Bereich: `claude_ads_core/` (Core/Adapter/Scoring) · `skills/`, `ads/` (Skill-Routing) · `control-plane/` (Manifeste/Gates) · `docs/wiki/` falls vorhanden. Immer: `CLAUDE.md`, `AGENTS.md`.

```bash
git log --oneline -10 && git diff HEAD~1 --stat
grep -rn "[Suchbegriff]" claude_ads_core/ skills/ ads/ --include="*.py" --include="*.md" | head
[ -x .venv/bin/python ] && PY=.venv/bin/python || PY=python3
$PY -m pytest -q -x   # reproduzieren
```

Root Cause: **Symptom** → **Erwartet** → **Ursache** → **Betroffene Dateien**.

## Phase 2: Fix

Minimal, keine Refactorings, Tests nicht schwächen, Regression-Test hinzufügen.

## Phase 3: Validieren

```bash
$PY -m pytest -q && $PY -m claude_ads_core --version
```

## Phase 4: Committen

```bash
git add -A
git commit -m "fix(scope): kurze Beschreibung

- Root Cause: …
- Fix: …"
```

## Output

```
Bugfix abgeschlossen
━━━━━━━━━━━━━━━━━━━━━
Problem · Root Cause · Fix · Dateien · Tests ✅ · Commit [hash]
━━━━━━━━━━━━━━━━━━━━━
```
