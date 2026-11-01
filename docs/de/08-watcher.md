# 08 · Täglicher Wächter einrichten und entfernen

**Stand:** 2026-11-01

**Was er tut:** Jeden Tag liest ein Skript lesend die letzten 14 Tage und prüft: Budgetverbrauch, ob Anzeigen noch laufen, Conversions, abgelehnte Anzeigen, Alter der Daten.
**Ohne KI und ohne Kosten.** Das Ergebnis ist die Ampel im Cockpit. Regeln und Schwellen: `ads/references/kadenz-und-regeln.md`.

## Voraussetzungen

Konto verbunden (`doctor` zeigt „verbunden“) und ein aktives Konto gewählt (`/start` oder `python -m claude_ads_core settings set --account 1234567890`).

## Einmal von Hand starten

```bash
python scripts/run_daily_watch.py --dry-run     # zeigt nur die Befehle
python scripts/run_daily_watch.py               # liest und wertet aus
python -m claude_ads_core cockpit build --watch-result .adbot/runs/<lauf>/watch-result.json
```

## Täglich automatisch

```bash
python scripts/schedule_watch.py --dry-run      # zeigt, was passieren würde
python scripts/schedule_watch.py --time 07:30   # einrichten
python scripts/schedule_watch.py --remove       # wieder entfernen (mehrfach ausführbar)
```

Mac: ein Hintergrundauftrag (launchd) für deinen Benutzer. Windows: eine geplante Aufgabe „AdbotWatch“. Protokolle (Mac): `~/.config/adbot/logs`.

**Wenn der Rechner um die Zeit aus ist:** Der nächste Lauf holt die fehlenden Tage nach; das Cockpit zeigt bis dahin „Daten sind X Tage alt“.
Ausschalten ohne Entfernen: `python -m claude_ads_core settings set --watch off`.

## Was der Wächter nie tut

Er ändert nichts an deinem Konto, löscht nichts und schreibt nur in neue Ordner unter `.adbot/runs/`. Die formale Datei `monitoring-bundle.json` entsteht nur, wenn du die
Festplattenverschlüsselung bestätigt hast (Anleitung 01).

## Wenn etwas nicht klappt

Siehe Anleitung 09. Prüfe zuerst `python -m claude_ads_core doctor --online`.
