# 05 · Erste Kampagne: Briefing, Entwurf, Import

**Stand:** 2026-11-01

**Befehl:** `/kampagne` · **Ergebnis:** CSV-Entwurf, **alles pausiert** · **Veröffentlicht wird nur von dir**

## 1. Briefing (du bestätigst jede Angabe)

Adbot fragt dich nach fünf Dingen und lässt sie dich **ausdrücklich bestätigen**. Ohne Bestätigung entsteht kein Entwurf:

1. **Ziel:** Anrufe, Anfragen oder Verkäufe?
2. **Tagesbudget** mit Währung: Was darf die Werbung höchstens pro Tag kosten?
3. **Region oder Umkreis.**
4. **Conversion-Definition:** Was zählt als Erfolg (z. B. ausgefülltes Formular, Anruf über eine bestimmte Dauer)?
5. **Angebot und Website** (`https://…`).

## 2. Plan und Entwurf

Adbot zeigt Szenarien statt Versprechen (mit offenen Annahmen), Keywords nach Suchabsicht, Anzeigentexte mit geprüften Zeichenlimits.
**Ausschließende Keywords** nimmt es nur auf, wenn du einen Suchbegriffsbericht mit Begründung lieferst. Der Entwurf wird als CSV-Datei für den
Google Ads Editor gespeichert. **Jede Kampagne ist pausiert.**

## 3. In den Google Ads Editor importieren

1. Google Ads Editor öffnen und dein Konto **herunterladen**.
2. Menü *Konto → Importieren → Aus Datei* → die CSV-Datei wählen.
3. **Vorschau prüfen:** Spaltenzuordnung, **Standorte** (der Editor fragt eventuell nach der Zuordnung der Ortsangabe), **Sprachen**, Gebotsstrategie, Tagesbudget.
4. Änderungen im Editor ansehen. **Noch nicht veröffentlichen („Posten“).**
5. Erst wenn alles stimmt und **das Conversion-Tracking funktioniert**: veröffentlichen und die Kampagne bewusst **aktivieren**.

Hinweis: Der Entwurf nennt Sprache und Land auf Englisch (z. B. „German“, „Germany“). Prüfe beim ersten Import in der Vorschau, dass der Editor sie richtig zuordnet.

## Wenn etwas nicht klappt

- Der Editor meldet einen Fehler in einer Zeile: Adbot die Meldung nennen; es korrigiert den Entwurf.
- Ort wird nicht erkannt: im Editor den Ort manuell wählen.
- Mehr: Anleitung 09 und das Runbook `docs/runbooks/editor-csv-import.md`.
