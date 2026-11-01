# Runbook: Google Ads Live-Read über den offiziellen MCP-Server

**Stand:** 2026-08-28 · **Gilt für:** das eigene Google-Ads-Konto der Nutzerin (Hinweis: Developer-Token-Schritte sind veraltet und werden ersetzt)

Der Server `googleads/google-ads-mcp` ist read-only und stellt drei Tools bereit:
`list_accessible_customers`, `search` (GAQL) und `get_resource_metadata`. Adbot registriert ihn
über die Projekt-Datei `.mcp.json`; alle Werte kommen aus Umgebungsvariablen.

## Teil A – Einmalige manuelle Schritte (Kontoinhaber)

1. **Developer-Token** – Google Ads → Verwaltungskonto <MCC-ID> → Verwaltung → API-Center:
   Kontakt-E-Mail, Firmenname, URL, Unternehmenstyp „Werbetreibender“, Nutzungsbedingungen,
   „Token erstellen“. Neue Tokens erhalten meist direkt Explorer-Zugriff; erscheint später
   `developer token is only approved for use with test accounts`, im API-Center Basic Access beantragen.
2. **Google-Cloud-Projekt** – console.cloud.google.com (gleicher Login): Projekt anlegen, *Google Ads API*
   aktivieren, OAuth-Zustimmungsbildschirm (intern/extern, eigene E-Mail als Testnutzer).
3. **OAuth-Client (Desktop-App)** – APIs & Dienste → Anmeldedaten → OAuth-Client-ID → Typ „Desktop-App“;
   JSON herunterladen nach `~/.config/google-ads/client.json` (nicht ins Repo).
4. **gcloud + ADC-Login**
   ```bash
   brew install --cask google-cloud-sdk
   gcloud auth application-default login \
     --scopes https://www.googleapis.com/auth/adwords,https://www.googleapis.com/auth/cloud-platform \
     --client-id-file="$HOME/.config/google-ads/client.json"
   ```
   Ergebnis: `~/.config/gcloud/application_default_credentials.json`.
5. **Werte in die lokale `.env`** (git-ignoriert, Rechte 600; niemals in getrackte Dateien):
   ```
   GOOGLE_PROJECT_ID=<cloud-projekt-id>
   GOOGLE_ADS_DEVELOPER_TOKEN=<token>          # alternativ: DEVELOPER_TOKEN=<token>
   GOOGLE_ADS_LOGIN_CUSTOMER_ID=<mcc-id>      # nur bei Zugriff über ein Verwaltungskonto
   ```
   `.mcp.json` startet den Server über `scripts/google_ads_mcp.sh`; der Wrapper liest nur diese
   Schlüssel aus der `.env` (sourced sie nicht) und bricht mit klarer Meldung ab, wenn etwas fehlt.

## Teil B – Verifikation in Claude Code

```bash
claude mcp list            # google-ads muss als connected erscheinen
```
Dann im Chat: `list_accessible_customers` → erwartet werden die Konten, auf die die Anmeldung Zugriff hat.

## Teil C – Ablauf eines Live-Reads (Conductor)

1. Query aus `ads/references/gaql-query-library.md` wählen (z. B. `campaign-daily-v1`), Kunden-ID und
   Datumsfenster einsetzen.
2. `search` aufrufen; Antwort **unverändert** als Envelope speichern:
   `.claude-ads/runs/<run-id>/live/google-<customer_id>-campaign-daily-v1.json`
   mit den Feldern `schema_version`, `platform`, `customer_id`, `login_customer_id`, `api_version`,
   `query_id`, `query`, `retrieved_at`, `rows` (Beispiel: `tests/fixtures/live_reads/google-campaign-daily.json`).
3. Normalisieren:
   ```python
   from claude_ads_core.adapters import GoogleAdsLiveReadAdapter
   adapter = GoogleAdsLiveReadAdapter("1234567890")
   snapshot = adapter.read_snapshot(".claude-ads/runs/<run-id>/live/google-1234567890-campaign-daily-v1.json")
   lineage = adapter.lineage()   # in run-manifest.adapters aufnehmen (mode: live_read)
   ```
4. Stichprobe gegen die Google-Ads-Oberfläche (Kosten, Conversions, ±1 %). Erst dann darf die
   Capability im Manifest von `fixture-verified` auf `live-verified` gehoben werden.

## Fehlerbilder

| Meldung | Bedeutung | Reaktion |
|---|---|---|
| `INVALID_ARGUMENT` / `UNRECOGNIZED_FIELD` | GAQL-Feld passt nicht zur API-Version | `needs_input`, Query gegen aktuelle Felddoku prüfen |
| `developer token is only approved for use with test accounts` | Token ohne Produktionszugriff | Basic Access beantragen |
| `rows must be a non-empty array` | leere Antwort | kein Datensatz – Fenster/Filter prüfen, nicht als „0 Spend“ werten |
| `customer.id … does not match` | Antwort eines anderen Kontos gespeichert | Envelope verwerfen, Query mit korrekter Kunden-ID wiederholen |
