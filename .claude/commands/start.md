---
description: Einrichtung von Adbot: Sprache, Verbindung, Unternehmen, Konto / Konfiguracja Adbota: język, połączenie, firma, konto
---

# Start

Sprache: Antworte in der Sprache aus den Einstellungen (`python -m claude_ads_core settings show`, Feld `language`: `de` oder `pl`).
Gibt es keine Einstellungen, frage einmal nach der Sprache und lege sie mit `python -m claude_ads_core settings init --lang <de|pl>` an.
Nutze das Glossar (`claude_ads_core.i18n.glossary()`) für Fachbegriffe und erkläre jeden beim ersten Auftreten kurz.

Lies die Karte „Start“ in `ads/references/prozesskarten.md` und folge ihr:

1. `python -m claude_ads_core doctor`. Ist das Konto nicht verbunden: `/verbinden` (Anleitung `docs/<sprache>/02-connect.md`).
2. Unternehmen kurz erfassen (Name, Website, Angebot, Region). Keine Annahmen erfinden.
3. Konto auswählen: mit dem MCP-Werkzeug `list_accessible_customers` (wenn verbunden) oder die Nutzerin liest die 10-stellige Kunden-ID aus Google Ads ab. Dann `python -m claude_ads_core settings set --account <ID>`.
4. Empfehlung geben: **Fall A** (Konto hat Verlauf) → `/analyse`; **Fall B** (noch keine Kampagnen) → `/analyse` (Fall B) und danach `/kampagne`.
5. Abschluss: was erledigt ist, welche Datei entstand, nächster Schritt, passende Anleitung.

Nichts am Konto ändern. Zugangsdaten niemals abfragen.
