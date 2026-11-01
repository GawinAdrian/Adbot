---
description: Git Commit mit Conventional Format für Adbot
argument-hint: [optional: spezifische Dateien]
---

# Commit: Git Änderungen committen

Spezifizierte Dateien: $ARGUMENTS (leer = alle Änderungen)

## 1. Status + Secrets-Check

```bash
git status && git diff --stat HEAD
git diff HEAD | grep -nE "/Users/|AIza|ya29\.|refresh_token|developer_token|client_secret" && echo "❌ STOPP: Secret/Pfad gefunden" || echo "OK"
```

## 2. Commit-Typ

| Typ | Wann |
|-----|------|
| `feat` | neues Feature |
| `fix` | Bugfix |
| `refactor` | Umbau ohne Verhaltensänderung |
| `docs` | nur Dokumentation (PRD/PRP/Wiki/README) |
| `test` | Tests/Fixtures |
| `chore` | Wartung, Dependencies, Manifeste, Config |

**Scope** (optional): `core`, `adapters`, `google`, `meta`, `skills`, `agents`, `control-plane`, `docs`, `commands`, `evals`

## 3. Stagen + Committen

```bash
git add $ARGUMENTS   # oder: git add -A (nach Secrets-Check!)
git commit -m "type(scope): kurze beschreibung

- Detail 1
- Detail 2"
```

## 4. Bestätigung

```bash
git log -1 --oneline && git show --stat HEAD
```

## 5. PRPs abschließen (automatisch)

PRPs in `docs/PRPs/` (nicht `completed/`), deren „Betroffene Dateien" im Commit enthalten sind oder deren Scope zum Commit passt:

a) Header: `## Status: COMPLETED ✅` + `**Abgeschlossen:** [Datum]` + `**Commit:** [hash]`
b) `git mv docs/PRPs/PRP_[Name].md docs/PRPs/completed/`
c) `git add docs/PRPs/ && git commit --amend --no-edit` (oder Mini-Commit `chore(docs): mark PRP_[Name] as completed`)

⚠️ Nur PRPs verschieben, die WIRKLICH vollständig umgesetzt wurden. Handoff-PRPs NICHT verschieben. Im Zweifel fragen.

**Nächster Schritt:** `git push` (nur auf Anweisung) oder `/06-release`
