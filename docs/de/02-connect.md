# 02 · Google-Konto verbinden

**Stand:** 2026-11-01 · **Dauer:** etwa 30–45 Minuten, einmalig · **Wer:** am besten gemeinsam mit der IT-kundigen Person
**Quellen:** `ads/references/google-auth-und-zugriff.md` (Google-Dokumentation vom 29./30.10.2026)

> **Hinweis:** Die Bezeichnungen in der Google-Konsole ändern sich gelegentlich. Wenn ein Menüpunkt anders heißt, such den sinngemäß passenden. Screenshots werden ergänzt.

## Worum es geht

Adbot liest die Daten deines Google-Ads-Kontos, damit es analysieren und planen kann. Dafür braucht Adbot eine
Anmeldung, die **du selbst** bei Google erteilst. Jede Nutzerin hat ihr **eigenes Google-Cloud-Projekt** und ihr
**eigenes Google-Konto**; es gibt keinen gemeinsamen Zugang.

**Zwei Sicherheitsregeln:**
1. Passwörter, Schlüssel und Anmeldedateien gibst **du** selbst ein. Schicke sie nie in den Chat und nie an Claude.
2. Adbot ändert nichts an deinem Konto, solange du nicht ausdrücklich zustimmst. Die Anmeldung wird nur zum **Lesen** genutzt.

Ein Developer-Token brauchst du **nicht** mehr: Google hat sie am 9. September 2026 abgeschafft.

## Schritt 1 · Google-Cloud-Projekt anlegen

1. Öffne <https://console.cloud.google.com> und melde dich mit dem Google-Konto an, mit dem du auch Google Ads nutzt.
2. Oben auf die Projektauswahl klicken → **Neues Projekt** → Name z. B. `adbot-meinefirma` → **Erstellen**.
3. Notiere die **Projekt-ID** (steht unter dem Namen; sie sieht aus wie `adbot-meinefirma-123456`).

**So erkennst du, dass es geklappt hat:** Oben in der Konsole steht der Projektname.

## Schritt 2 · Google Ads API aktivieren

1. Menü → **APIs & Dienste** → **Bibliothek**.
2. Nach **Google Ads API** suchen → anklicken → **Aktivieren**.

**Geklappt:** Die Seite zeigt „API aktiviert“.

## Schritt 3 · Zustimmungsbildschirm einrichten

1. **APIs & Dienste** → **OAuth-Zustimmungsbildschirm**.
2. Nutzertyp **Extern** wählen (für private Konten) → App-Name z. B. `Adbot`, deine E-Mail-Adresse als Support- und Kontakt-Adresse.
3. Bei den **Bereichen (Scopes)** diesen Bereich hinzufügen: `https://www.googleapis.com/auth/adwords`
4. Bei **Testnutzer** dein eigenes Google-Konto eintragen.

**Wichtig – 7-Tage-Regel:** Solange der Bildschirm auf **„Testing“** steht, laufen Anmeldungen nach **7 Tagen** ab (Google-Angabe). Du musst dich dann
einmal pro Woche neu anmelden (Schritt 5 wiederholen). Auf **„In Produktion“** stellen ist möglich, kann aber nach Google-Angaben eine App-Prüfung verlangen.
Für den Anfang ist „Testing“ in Ordnung.

## Schritt 4 · OAuth-Client (Desktop-App) erstellen

1. **APIs & Dienste** → **Anmeldedaten** → **Anmeldedaten erstellen** → **OAuth-Client-ID**.
2. Anwendungstyp **Desktop-App**, Name `Adbot Desktop` → **Erstellen**.
3. **JSON herunterladen** und speichern als:
   - Mac: `~/.config/google-ads/client.json`
   - Windows: `%USERPROFILE%\.config\google-ads\client.json`

   Der Ordner `.config` muss eventuell erst angelegt werden. Diese Datei ist geheim und gehört **nicht** in ein Repository.

**Geklappt:** Die Datei `client.json` liegt am genannten Ort.

## Schritt 5 · Anmelden

Installiere zuerst das Google-Cloud-Kommandozeilenwerkzeug (siehe Anleitung 01). Dann im Terminal:

```bash
gcloud auth application-default login \
  --scopes https://www.googleapis.com/auth/adwords,https://www.googleapis.com/auth/cloud-platform \
  --client-id-file="$HOME/.config/google-ads/client.json"
```

Unter Windows (PowerShell): `--client-id-file="$env:USERPROFILE\.config\google-ads\client.json"`

Ein Browserfenster öffnet sich: Konto wählen, Zugriff erlauben. Die Anmeldedatei liegt danach in deinem Google-Cloud-Ordner
(`application_default_credentials.json`).

**Geklappt:** Im Terminal steht, dass die Zugangsdaten gespeichert wurden.

## Schritt 6 · Profil anlegen

```bash
mkdir -p ~/.config/adbot/standard
printf 'GOOGLE_PROJECT_ID=DEINE-PROJEKT-ID\n' > ~/.config/adbot/standard/env
python -m claude_ads_core settings init --lang de
```

Ersetze `DEINE-PROJEKT-ID` durch die Projekt-ID aus Schritt 1. (Windows: Ordner `%USERPROFILE%\.config\adbot\standard` anlegen und die Datei `env` darin mit einem Texteditor erstellen.)
Das Konto wählst du anschließend im Befehl `/start` aus.

## Schritt 7 · Prüfen

```bash
python -m claude_ads_core doctor --lang de --online
```

**So sieht „alles gut“ aus:** Alle Zeilen zeigen `✔`, am Ende steht „Dein Google-Konto ist verbunden.“ und bei der Online-Prüfung „Google Ads ist erreichbar und antwortet.“

## Wenn etwas nicht klappt

| Meldung | Bedeutung | Was tun |
|---|---|---|
| „Keine Google-Anmeldung gefunden“ | Schritt 5 fehlt oder die Datei wurde gelöscht | Schritt 5 wiederholen |
| „Die Google-Anmeldung ist abgelaufen oder wurde widerrufen“ | z. B. 7-Tage-Regel | Schritt 5 wiederholen |
| „Keine Berechtigung für das ausgewählte Konto“ | falsches Google-Konto | Mit dem Konto anmelden, dem das Ads-Konto gehört |
| „Das Google-Cloud-Projekt ist nicht eingetragen“ | Schritt 6 fehlt | Datei `env` prüfen |
| Meldung zum Zugriffslevel (z. B. „explorer access“) | Funktion braucht „Basic“-Zugriff, z. B. Keyword-Ideen per API | Das Lesen der Konto-Daten geht auch so; für Keyword-Ideen siehe Anleitung 04 (CSV-Weg) |

Mehr in der Fehlerbehebung (Anleitung 09). Zum Abmelden siehe Anleitung 03.
