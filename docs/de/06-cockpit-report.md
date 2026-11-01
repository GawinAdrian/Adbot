# 06 · Cockpit und Wochenbericht lesen

**Stand:** 2026-11-01

**Befehl:** `/bericht` · **Ergebnis:** `cockpit.html` und ein Wochenbericht · **Ändert nichts** an deinem Konto

## Das Cockpit öffnen

`/bericht` baut die Übersicht und nennt den Pfad der Datei `cockpit.html` (im Ordner des letzten Laufs unter `.adbot/runs/`).
Doppelklick auf die Datei öffnet sie im Browser. Die Seite ist eine **lokale Datei**: Beim Öffnen werden keine Daten versendet.

Selbst bauen: `python -m claude_ads_core cockpit build --watch-result .adbot/runs/<lauf>/watch-result.json`

## So liest du sie (von oben nach unten)

1. **Ampel** – Grün: nichts zu tun. Gelb: bitte hinschauen. Rot: bald handeln. Grau: zu wenig Daten. Die Farbe steht immer auch als Text da.
2. **Was ist passiert?** – ein Satz und bis zu fünf Meldungen, jeweils mit einem nächsten Schritt.
3. **Kennzahlen** – die letzten 7 Tage im Vergleich mit den 7 Tagen davor, jede Zahl mit Erklärung.
4. **Wichtigste Empfehlungen** – höchstens drei, mit Vorher/Nachher, Aufwand, Risiko und Sicherheit der Aussage. „Auf mehr Daten warten“ ist oft richtig.
5. **Wartet auf deine Freigabe** und **Änderungsprotokoll** – was offen ist und was du geändert hast.
6. **Lücken und Hinweise** – was Adbot nicht lesen konnte (z. B. Zahlungsstatus) oder wenn Daten alt sind.

## Wochenrhythmus

Standard: **Montag**. Ändern: `python -m claude_ads_core settings set --weekday friday` (oder `--report monthly`).
Die Wochenanalyse startest du selbst mit `/bericht`; der Wächter läuft täglich von allein (Anleitung 08).

## Wenn etwas nicht klappt

- „Daten sind X Tage alt“: Rechner war aus oder Abruf fehlgeschlagen → Anleitung 08.
- Die Seite ist leer: Es gibt noch keinen Lauf; Anleitung 08, Abschnitt „Einmal von Hand starten“.
