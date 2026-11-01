---
description: Wächter-Ergebnis und Wochenbericht lesen, Cockpit öffnen / Odczytaj wynik strażnika i raport tygodniowy, otwórz kokpit
---

# Bericht

Sprache: Antworte in der Sprache aus den Einstellungen (`python -m claude_ads_core settings show`, Feld `language`: `de` oder `pl`).
Gibt es keine Einstellungen, frage einmal nach der Sprache und lege sie mit `python -m claude_ads_core settings init --lang <de|pl>` an.
Nutze das Glossar (`claude_ads_core.i18n.glossary()`) für Fachbegriffe und erkläre jeden beim ersten Auftreten kurz.

Lies die Karte „Report“ in `ads/references/prozesskarten.md` und `ads/references/kadenz-und-regeln.md`.

1. Letztes Wächter-Ergebnis laden (`python -m claude_ads_core watch --help` für den Aufruf); ist es älter als erwartet, als Datenlücke ausweisen.
2. Wochen-Deutung: Trend gegenüber der Vorwoche, wahrscheinliche Ursachen, **höchstens drei Empfehlungen** mit Nutzen, Risiko, Sicherheit. Bei dünner Datenlage „abwarten“ als Ergebnis zulassen.
3. Cockpit bauen: `python -m claude_ads_core cockpit build --help`. Der Pfad der HTML-Datei wird genannt.
4. Nichts am Konto ändern.
