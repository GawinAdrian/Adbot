---
description: Wiki-Dokumentation (docs/wiki/) anhand der letzten Code-Änderungen aktualisieren
---

# Task: Projekt-Dokumentation aktualisieren

Du aktualisierst `docs/wiki/`. Jede Wiki-Datei hat Frontmatter mit `last_updated` und `covers` (Liste der dokumentierten Quelldateien/Verzeichnisse).

Falls `docs/wiki/` leer ist → stattdessen `/rebuild-docs`.

## Schritt 1: Was hat sich geändert?

```bash
OLDEST=$(grep -h "last_updated:" docs/wiki/*.md | sed 's/last_updated: //' | sort | head -1)
echo "Docs zuletzt aktualisiert: $OLDEST"
git log --since="$OLDEST" --oneline -- ':!docs/' ':!*.md'

for doc in docs/wiki/*.md; do
  DATE=$(grep "last_updated:" "$doc" | sed 's/last_updated: //' | tr -d ' ')
  COVERS=$(grep "covers:" "$doc" | sed 's/covers: \[//' | sed 's/\]//' | tr ',' '\n' | tr -d ' ')
  for f in $COVERS; do
    if [ -n "$(git log --since="$DATE" --oneline -- "$f" 2>/dev/null)" ]; then echo "NEEDS UPDATE: $(basename $doc)"; break; fi
  done
done
```

## Schritt 2: Geänderte Dateien lesen
Wiki-Doc, die geänderten `covers`-Dateien, den Diff.

## Schritt 3: Nur Betroffenes aktualisieren
- Nur Abschnitte ändern, die von Code-Änderungen betroffen sind
- `last_updated` auf heute
- Neue Module/Skills/Adapter ergänzen, entfernte Referenzen löschen
- Struktur und Stil beibehalten, `Update-Hinweise` am Ende erhalten

## Schritt 4: Neue Features ohne passendes Doc
Ins nächstliegende Doc; neues Wiki-Doc nur für große Systemkomponenten.

## Regeln
- Chirurgisch vorgehen, nichts unnötig umschreiben
- Unsicheres markieren: `> ⚠️ Bitte verifizieren:`
- Zahlen (Skill-/Adapter-/Plattform-Counts) aus Manifesten ableiten, nicht raten
