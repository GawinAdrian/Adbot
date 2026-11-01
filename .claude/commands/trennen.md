---
description: Google-Konto von Adbot trennen (geführt) / Odłącz konto Google od Adbota (krok po kroku)
argument-hint: [optional: de|pl]
---

# Google-Konto trennen

Sprache: Antworte in der Sprache aus den Einstellungen (`python -m claude_ads_core settings show`, Feld `language`).
Wurde `$ARGUMENTS` übergeben, nutze diese Sprache.

## Regeln (nicht verhandelbar)

- Das Trennen verändert **nie** das Google-Ads-Konto oder Kampagnen. Es entzieht nur Adbot den Zugriff.
- Löschen von Dateien (Anmeldedatei, Profil, `.adbot/`) nur nach **ausdrücklicher** Bestätigung der Nutzerin und mit dem Hinweis, dass es nicht rückgängig zu machen ist.
- Die Schritte bei Google (Berechtigungsseite, Projekt löschen) macht die Nutzerin selbst im Browser.

## Ablauf

1. Lies `docs/de/03-disconnect.md` bzw. `docs/pl/03-disconnect.md` und erkläre kurz die drei Stufen.
2. Frage, was die Nutzerin möchte: nur trennen (Stufe 1 und 2, empfohlen), zusätzlich das Cloud-Projekt löschen (Stufe 3), und ob lokale Daten behalten oder gelöscht werden sollen.
3. Stufe 1: Erkläre, dass `gcloud auth application-default revoke` die lokale Anmeldedatei löscht; die Nutzerin führt es selbst aus (Präfix `!`).
4. Stufe 2: Führe sie zu <https://myaccount.google.com/permissions>, dort die App „Adbot“ (oder den vergebenen Namen) auswählen und „Zugriff entfernen“.
5. Stufe 3 nur auf ausdrücklichen Wunsch, ebenfalls durch die Nutzerin.
6. Prüfen: `python -m claude_ads_core doctor`. Erwartet: „Dein Google-Konto ist nicht verbunden.“ Bestätige das Ergebnis mit dem tatsächlichen Befehlsausgabe-Text.
7. Erinnere an das erneute Verbinden mit `/verbinden`.
