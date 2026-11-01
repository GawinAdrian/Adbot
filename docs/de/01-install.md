# 01 · Installation (Mac und Windows)

**Stand:** 2026-11-01 · **Wer:** die IT-kundige Person richtet es einmal ein · **Dauer:** etwa 30 Minuten

## Was du brauchst

| Was | Wofür | Prüfen |
|---|---|---|
| **Claude-Zugang** (eigenes Konto/Abo oder API-Schlüssel) | die KI-Arbeit läuft in Claude Code | Kosten und Tarif legt Anthropic fest; vorher auf der Anthropic-Webseite prüfen |
| **Claude Code** (Terminal oder Tab „Code“ der Claude-Desktop-App, Mac und Windows) | führt `/start`, `/analyse` usw. aus | Tarifvoraussetzungen der Desktop-App in der Anthropic-Dokumentation prüfen |
| **Python 3.11 oder neuer** | führt die Auswertung aus | `python3 --version` (Windows: `py --version`) |
| **uv** | holt die Google-Bibliothek bei Bedarf | `uv --version` |
| **Google-Cloud-Kommandozeilenwerkzeug (`gcloud`)** | Anmeldung bei Google | `gcloud --version` |
| **Google Ads Editor** | importiert den Kampagnenentwurf | im Startmenü bzw. Programme |

Installiere die Werkzeuge über die offiziellen Seiten bzw. Paketverwalter (z. B. Mac: `brew install uv`, `brew install --cask google-cloud-sdk`;
Windows: `winget install astral-sh.uv`). **Führe keine Anleitung aus, die `curl … | bash` oder `irm … | iex` verlangt.**

## Adbot einrichten

1. Ordner von Adbot holen (Git-Klon oder heruntergeladenes Archiv) und im Terminal in den Ordner wechseln.
2. Virtuelle Umgebung anlegen und aktivieren:
   - Mac: `python3 -m venv .venv && source .venv/bin/activate`
   - Windows (PowerShell): `py -m venv .venv` und dann `.venv\Scripts\Activate.ps1`

   Danach heißt der Befehl überall `python`. Adbot braucht keine weiteren Python-Pakete.
3. Prüfen: `python -m claude_ads_core --version` zeigt eine Versionsnummer.
4. Claude Code im Adbot-Ordner starten (Terminal: `claude`; Desktop-App: Ordner als Projekt wählen).
5. `/start` eingeben. Die Befehle erscheinen, wenn du `/` tippst.

## Prüfen

```bash
python -m claude_ads_core doctor --lang de
```

Direkt nach der Installation sind „Einstellungen“, „Google-Cloud-Projekt“ und „Google-Anmeldung“ noch rot. Das ist richtig; weiter mit Anleitung 02.

## Festplattenverschlüsselung (empfohlen)

Die Berichte enthalten Daten deines Kontos. Schalte **FileVault** (Mac) bzw. **BitLocker** (Windows) ein und bestätige es einmal:

```bash
python -m claude_ads_core settings set --disk-encryption-attested 2026-11-01
```

(Datum von heute einsetzen.) Erst dann legt der tägliche Wächter zusätzlich die formale Berichtsdatei `monitoring-bundle.json` an. Ohne Bestätigung läuft alles andere normal.

## Entfernen

Ordner löschen, nachdem du das Google-Konto getrennt hast (Anleitung 03) und den Wächter entfernt hast (Anleitung 08).
