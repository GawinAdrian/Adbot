---
description: Übersicht: Befehle und Anleitungen in deiner Sprache / Przegląd: polecenia i instrukcje w Twoim języku
---

# Hilfe

Sprache: Antworte in der Sprache aus den Einstellungen (`python -m claude_ads_core settings show`, Feld `language`: `de` oder `pl`).
Gibt es keine Einstellungen, frage einmal nach der Sprache und lege sie mit `python -m claude_ads_core settings init --lang <de|pl>` an.
Nutze das Glossar (`claude_ads_core.i18n.glossary()`) für Fachbegriffe und erkläre jeden beim ersten Auftreten kurz.

Zeige in der Sprache der Nutzerin diese Liste mit je einem Satz und verweise auf `docs/<sprache>/00-overview.md`:

`/start` Einrichtung · `/verbinden` Google-Konto verbinden · `/trennen` Verbindung lösen · `/analyse` Ist-Stand · `/kampagne` erste Kampagne als Entwurf · `/bericht` Wochenbericht und Cockpit · `/optimieren` Verbesserungsvorschläge · `/hilfe` diese Übersicht.

Erinnere an die drei Regeln: Zugangsdaten gibt die Nutzerin selbst ein; nichts am Konto ohne ihre ausdrückliche Zustimmung; nichts wird gelöscht.
