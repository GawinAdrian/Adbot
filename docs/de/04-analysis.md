# 04 · Erste Analyse

**Stand:** 2026-11-01

**Befehl:** `/analyse` · **Ergebnis:** Datei im Ordner `.adbot/runs/…` · **Ändert nichts** an deinem Konto

## Fall A: Du hast schon Kampagnen

Adbot liest Kampagnen, Anzeigengruppen, Keywords, Suchbegriffe, Conversions und Budget (nur lesend), nennt Zeitraum, Zeitzone und Währung
und liefert **höchstens drei Prioritäten**. Jede hat einen Beleg, eine Sicherheit der Aussage und einen nächsten Schritt. Fehlende Daten und Widersprüche stehen offen dabei.

**Fragen, die Adbot dir stellen kann:** Was zählt für dich als Erfolg (Anruf, Formular, Kauf)? Gab es zuletzt große Änderungen?

## Fall B: Du hast noch keine Kampagnen

Adbot untersucht deine **Website** (Verständlichkeit, Zielseite, Kontaktwege), den **Markt und Wettbewerb**, mögliche **Keywords** und prüft, ob
**Conversion-Tracking** vorhanden ist. Es sagt ausdrücklich, was ohne Verlauf nicht bekannt sein kann.

**Keyword-Ideen:** Per Schnittstelle gibt es sie nur mit „Basic“-Zugriff deines Google-Cloud-Projekts. Ohne Basic exportierst du in Google Ads aus dem Keyword-Planer
eine CSV-Datei und gibst sie Adbot; es liest sie.

## So erkennst du, dass es geklappt hat

- Adbot nennt am Ende die Ergebnisdatei und den nächsten Schritt.
- Es nennt keine Zahlen ohne Einheit, Zeitraum und Quelle.
- Es nennt keine ausschließenden Keywords, solange du keinen Suchbegriffsbericht geliefert hast.

## Wenn etwas nicht klappt

`python -m claude_ads_core doctor --lang de --online` zeigt, ob die Verbindung steht. Siehe Anleitung 09.
