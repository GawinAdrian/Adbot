---
description: Bestehende PRD von Adbot aktualisieren — Feature-Status, Capabilities, Roadmap synchronisieren
---

# PRD aktualisieren: Adbot

Du aktualisierst `docs/PRDs/PRD_Adbot.md` auf den aktuellen Stand.
Wahrheitsquellen in dieser Reihenfolge: **Wiki-Docs** (`docs/wiki/`) → **Capability-Manifest** → **Git-Historie** → **PRPs**.

**⚠️ NUR die PRD-Datei ändern. Kein Code, keine Wiki-Docs, keine anderen Dateien.**

---

## Phase 1: Aktuelle Wahrheit sammeln

```bash
ls -1 docs/wiki/ 2>/dev/null
PRD_DATE=$(grep "Letzte Aktualisierung:" docs/PRDs/PRD_Adbot.md | head -1 | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}')
echo "PRD zuletzt aktualisiert: $PRD_DATE"
git log --oneline --since="$PRD_DATE" | head -50
ls -1 docs/PRPs/ docs/PRPs/completed/ 2>/dev/null
python3 -c "import json;d=json.load(open('control-plane/manifests/capability-manifest.json'));[print(p['platform'],[(c['id'],c['mode'],c['status']) for c in p['capabilities']]) for p in d['platforms']]"
cat docs/PRDs/PRD_Adbot.md
```

Lies alle Wiki-Docs (falls vorhanden) und extrahiere Features, Architektur, Adapter, Skills, externe Services.

---

## Phase 2: Delta identifizieren (interne Checkliste)

| Bereich | Prüfung | Quelle |
|---------|---------|--------|
| Feature-Status | „geplant" aber jetzt live (oder umgekehrt) | Wiki + Git |
| Capability-Matrix | Modus/Status pro Plattform geändert | capability-manifest.json |
| Adapter | neue Adapter in `claude_ads_core/adapters/` | Code |
| Skills/Agents | neue/entfernte Einträge in `skills/`, `agents/` | Code |
| Externe Services | neue MCPs, APIs, Env-Var-Namen | Wiki + Code |
| Mandanten/Konten | neue Konten oder Plattformen | Wiki |
| Roadmap | erledigte Meilensteine, neue Prioritäten | PRPs + Git |
| PRP-Referenz | neue/abgeschlossene PRPs | docs/PRPs/ |
| Tech Stack | neue Dependencies | pyproject.toml, requirements*.txt |

---

## Phase 3: PRD aktualisieren

1. **Version bumpen** (große Änderung +1.0, kleine +0.1)
2. **Datum** auf heute
3. **Änderungstabelle:** neue Zeile (vorher → nachher)
4. **Status-Ehrlichkeit:** ✅ nur bei Code + Fixture + Test-Evidenz
5. **Nicht aufblähen:** Details gehören ins Wiki
6. **Erledigtes** in „Abgeschlossen" verschieben
7. **Unveränderte Abschnitte in Ruhe lassen**

---

## Phase 4: Validierung

1. ✅ Konsistenz mit Wiki und Capability-Manifest
2. ✅ Keine Zombie-Features, keine Phantome
3. ✅ Version + Datum gebumpt, Änderungstabelle ergänzt
4. ✅ Keine Secrets/absoluten Pfade

---

## Phase 5: Output

```
PRD-Update abgeschlossen
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Version: [alt] → [neu]   Datum: [alt] → [neu]
Wichtigste Änderungen:
- [Feature X]: ⬜ → ✅
- [Capability]: [Änderung]
Statistik: Live [X] · In Arbeit [X] · Geplant [X] · Geänderte Abschnitte [X/Y]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Empfehlung:** Wiki veraltet → erst `/update-docs` oder `/rebuild-docs`.
**Nächster Schritt:** `/05-commit`
