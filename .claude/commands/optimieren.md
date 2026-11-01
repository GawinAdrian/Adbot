---
description: Verbesserungsvorschläge als Entwurf mit Vorher/Nachher / Propozycje usprawnień jako szkic z porównaniem przed/po
---

# Optimieren

Sprache: Antworte in der Sprache aus den Einstellungen (`python -m claude_ads_core settings show`, Feld `language`: `de` oder `pl`).
Gibt es keine Einstellungen, frage einmal nach der Sprache und lege sie mit `python -m claude_ads_core settings init --lang <de|pl>` an.
Nutze das Glossar (`claude_ads_core.i18n.glossary()`) für Fachbegriffe und erkläre jeden beim ersten Auftreten kurz.

Lies `ads/references/kadenz-und-regeln.md` und den Skill `ads-optimize`.

1. Vorschläge nur aus dem aktuellen Bericht ableiten. Pro Vorschlag: Vorher/Nachher, betroffene Objekte (IDs), erwartete Wirkung, Hinweis zur Lernphase, Rückgängig-Anleitung, Sicherheit der Aussage.
2. Höchstens **eine Änderungsrunde je Kampagne und Woche**, außer bei Tracking-, Zahlungs- oder Budget-Ausreißern. „Datenlage zu dünn, abwarten“ ist ein gültiges Ergebnis.
3. Keine feste Pausier-Regel nach CPA-Vielfachen, keine pauschalen Budget-Verhältnisse.
4. Ergebnis als `optimisation-draft.md`. Die Umsetzung macht die Nutzerin selbst; Schreibzugriff per API ist in dieser Version abgeschaltet.
5. Löschen wird abgelehnt; Alternativen: pausieren, archivieren, Label, Sicherung.
