---
description: Release-Gates prüfen und Release-Paket für Adbot bauen (Ersatz für Deploy — es gibt kein Server-Deploy)
argument-hint: [optional: Version, z.B. 2.1.0]
---

# Release: Adbot

Adbot ist ein Skill-/Python-Paket, kein Server-Dienst. „Deploy" bedeutet: Release-Gates bestehen, Version bumpen, Paket bauen, Tag setzen.

Ziel-Version: $ARGUMENTS

## Phase 1: Pre-Flight

```bash
git status                      # sauber?
git log origin/main..HEAD --oneline   # ungepushte Commits?
git fetch origin main && git log HEAD..origin/main --oneline | head   # rebase nötig?
```

## Phase 2: Release-Gates (`control-plane/RELEASE_REQUIREMENTS.md`)

Lies die Datei vollständig. Prüfe dann mindestens:

```bash
[ -x .venv/bin/python ] && PY=.venv/bin/python || PY=python3
$PY -m pytest -q                                  # Evaluation-Gates
$PY scripts/release.py --help                     # Packaging-Skript kennenlernen
$PY -m pytest -q tests/release tests/audit        # Release-/Evidence-Gates
```

Manuell prüfen:
- [ ] Capability-Manifest == Code + Fixtures + Tests
- [ ] Load-bearing Sources nicht überfällig (`source-ledger.json`, 30-Tage-Regel für API/Policy)
- [ ] Keine Secrets/personenbezogenen Daten in getrackten Dateien, Fixtures, Reports
- [ ] `CHANGELOG.md` aktualisiert, `pyproject.toml` Version gebumpt
- [ ] Remote CI (`.github/workflows/ci.yml`) auf `main` grün

**⚠️ Niemals „release-ready" behaupten, wenn ein Gate fehlt.** Externe Model-Eval-Evidenz (signierte Gate-Reports) kann lokal nicht ersetzt werden — als offen markieren.

## Phase 3: Paket bauen

```bash
$PY scripts/release.py [Optionen laut --help]
```

## Phase 4: Tag (nur nach User-Freigabe)

```bash
git tag -a v$ARGUMENTS -m "release: v$ARGUMENTS"
# git push origin main --tags   ← nur auf explizite Anweisung
```

## Output

```
Release-Check abgeschlossen
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Version: …  Commit: …
Gates: ✅/❌ Tests · ✅/❌ Manifeste · ✅/❌ Sources frisch · ✅/❌ Secrets · ✅/❌ CI · ⏳ externe Eval-Evidenz
Paket: [Pfad + SHA-256] / nicht gebaut
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
