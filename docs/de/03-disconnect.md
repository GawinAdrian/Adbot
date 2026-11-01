# 03 · Google-Konto trennen

**Stand:** 2026-11-01 · **Dauer:** etwa 10 Minuten · **Wer:** du selbst
**Quellen:** `ads/references/google-auth-und-zugriff.md`

Du kannst Adbot jederzeit den Zugriff entziehen. Das geht in **drei Stufen**; Stufe 1 und 2 solltest du immer machen.
Dein Google-Ads-Konto und deine Kampagnen bleiben dabei unverändert.

## Stufe 1 · Lokale Anmeldung entfernen

```bash
gcloud auth application-default revoke
```

Das löscht die lokale Anmeldedatei auf deinem Rechner (laut Google-Dokumentation). Ob damit der Zugriff auch bei Google selbst
widerrufen wird, steht dort nicht – deshalb gehört Stufe 2 dazu.

## Stufe 2 · Zugriff bei Google entziehen

1. Öffne <https://myaccount.google.com/permissions> (angemeldet mit deinem Google-Konto).
2. Suche die App mit dem Namen, den du im Zustimmungsbildschirm vergeben hast (z. B. `Adbot`).
3. Wähle **Zugriff entfernen**.

## Stufe 3 (optional) · Cloud-Projekt löschen

Nur, wenn du Adbot dauerhaft nicht mehr nutzen willst: Google-Cloud-Konsole → **IAM & Verwaltung** → **Einstellungen** → **Beenden**.
Die Konsole zeigt dort die Fristen. Danach ist auch die Projekt-ID weg; für eine spätere Nutzung brauchst du ein neues Projekt (Anleitung 02).

## Lokale Daten: behalten oder löschen?

- **Behalten (empfohlen):** Berichte und Einstellungen bleiben im Ordner `.adbot/` und unter `~/.config/adbot/standard`. Du kannst später wieder verbinden.
- **Löschen:** Lösche die beiden Ordner selbst im Dateimanager. **Das lässt sich nicht rückgängig machen.** Sichere vorher Berichte, die du noch brauchst.

## Prüfen

```bash
python -m claude_ads_core doctor --lang de
```

**So sieht „getrennt“ aus:** `✖ Keine Google-Anmeldung gefunden …` und am Ende „Dein Google-Konto ist nicht verbunden.“

Wieder verbinden: Anleitung 02.
