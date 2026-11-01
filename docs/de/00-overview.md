# 00 · Überblick: Was Adbot tut und was nicht

**Stand:** 2026-11-01 · Alle Anleitungen gibt es auf Deutsch (`docs/de`) und Polnisch (`docs/pl`) mit gleichen Dateinamen.

## Was Adbot ist

Adbot hilft dir, **deine eigene Google-Werbung** zu verstehen und aufzubauen. Du schreibst in normalem Deutsch oder Polnisch,
Adbot liest die Daten deines Google-Ads-Kontos, wertet sie aus und bereitet Vorschläge vor.

| Du willst … | Befehl | Anleitung |
|---|---|---|
| alles einrichten | `/start` | 01, 02 |
| dein Google-Konto verbinden / trennen | `/verbinden`, `/trennen` | 02, 03 |
| wissen, wie deine Werbung steht | `/analyse` | 04 |
| deine erste Kampagne vorbereiten | `/kampagne` | 05 |
| Wochenbericht und Übersicht sehen | `/bericht` | 06 |
| Verbesserungen vorgeschlagen bekommen | `/optimieren` | 07 |
| tägliche Kontrolle automatisch laufen lassen | – | 08 |
| bei Problemen nachschlagen | `/hilfe` | 09, 10 |

## Die drei Sicherheitsregeln

1. **Zugangsdaten gibst du selbst ein.** Passwörter, Schlüssel und Anmeldedateien schickst du nie in den Chat.
2. **Nichts ändert sich ohne dein ausdrückliches Ja.** In dieser Version legt Adbot Kampagnen nur als **pausierten Entwurf** an. Importieren und Veröffentlichen machst du selbst.
3. **Nichts wird gelöscht.** Adbot pausiert, archiviert oder sichert; endgültiges Löschen lehnt es ab.

## Was Adbot nicht tut

- Es garantiert keine Ergebnisse (keine „50 Anfragen im Monat“). Zahlen sind Szenarien mit offenen Annahmen.
- Es gibt keine Rechtsberatung. Fragen zu Impressum, Datenschutz oder Einwilligung klärst du mit einer qualifizierten Stelle.
- Es ändert dein Konto nicht selbst. Schreibzugriff per Schnittstelle ist in dieser Version abgeschaltet.
- Es bewertet dein Konto nicht mit einer „Gesundheitsnote“. Es nennt höchstens drei Prioritäten mit Beleg.

## Wie es zusammenarbeitet

**Zahlen** kommen von einem Skript (täglich, ohne KI, ohne Kosten). **Deutung und Vorschläge** kommen von der KI, wenn du `/bericht` oder `/analyse` startest.
Alles wird als Datei im Ordner `.adbot/` auf deinem Rechner abgelegt.
