# Runbook: Google Ads Live-Read (eigenes Konto, ohne Developer-Token)

**Stand:** 2026-11-01 · **Gilt für:** das eigene Google-Ads-Konto einer Nutzerin mit eigenem Google-Cloud-Projekt
**Quellen:** `ads/references/google-auth-und-zugriff.md` (datiert, mit Ledger-Claims CLM-0214 bis CLM-0223)

Developer-Tokens wurden von Google am **2026-09-09 abgeschafft**. Der Zugriffslevel hängt am Google-Cloud-Projekt,
aus dem die OAuth-Zugangsdaten stammen. Ein vorhandenes Token darf gesetzt bleiben, wird aber nicht mehr gebraucht.
Es gibt zwei lesende Wege, beide ohne Token:

1. **MCP-Server** `googleads/google-ads-mcp` (nur lesend: `list_accessible_customers`, `search`, `get_resource_metadata`),
   registriert über `.mcp.json` → `scripts/google_ads_mcp.sh`.
2. **Direkter Skript-Weg** `scripts/gaql_via_api.py` (nur `GoogleAdsService.SearchStream`), für geplante Läufe ohne Claude-Sitzung.

## Teil A – Einmalige manuelle Schritte (Nutzerin, mit Begleitung)

1. **Google-Cloud-Projekt** – console.cloud.google.com (gleiches Google-Konto wie Google Ads): Projekt anlegen, *Google Ads API* aktivieren.
2. **Zugriffslevel prüfen/beantragen** – im Google-Ads-API-Center steht der Level des Projekts. Steht dort „Test", Explorer beantragen
   (Google stuft meist automatisch hoch). Keyword-Ideen per API brauchen **Basic** (Markenprüfung nötig).
3. **OAuth-Zustimmungsbildschirm und Desktop-Client** – OAuth-Client-ID vom Typ „Desktop-App" anlegen, JSON nach `~/.config/google-ads/client.json`
   speichern (nicht ins Repo). Achtung: Steht der Zustimmungsbildschirm auf „Testing", **laufen Anmeldungen nach 7 Tagen ab** (CLM-0220).
4. **gcloud + Anmeldung**
   ```bash
   gcloud auth application-default login \
     --scopes https://www.googleapis.com/auth/adwords,https://www.googleapis.com/auth/cloud-platform \
     --client-id-file="$HOME/.config/google-ads/client.json"
   ```
   Ergebnis: `~/.config/gcloud/application_default_credentials.json`. Der Scope-String ist aus dem bisherigen Betrieb übernommen und wird in PRP-Schritt 5 gegen die Google-Seite neu geprüft.
5. **Profil-Datei** (Rechte 600, außerhalb des Repos, nie in getrackte Dateien):
   ```bash
   mkdir -p ~/.config/adbot/standard && chmod 700 ~/.config/adbot/standard
   printf 'GOOGLE_PROJECT_ID=<cloud-projekt-id>\n' > ~/.config/adbot/standard/env && chmod 600 ~/.config/adbot/standard/env
   export ADBOT_PROFILE_DIR=~/.config/adbot/standard
   ```
   Optional: `GOOGLE_ADS_LOGIN_CUSTOMER_ID=<mcc-id>` nur bei Zugriff über ein Verwaltungskonto. Reihenfolge der Werte:
   Umgebung, dann `$ADBOT_PROFILE_DIR/env`, dann `.env` im Repo (git-ignoriert).

## Teil B – Verifikation

```bash
ADBOT_DRY_RUN=1 bash scripts/google_ads_mcp.sh   # erwartet: "configuration ok (dry run)"
claude mcp list                                   # google-ads muss als connected erscheinen
```
Dann im Chat `list_accessible_customers` aufrufen: erwartet werden die Konten, auf die die Anmeldung Zugriff hat.

## Teil C – Ablauf eines Live-Reads

1. Query aus `ads/references/gaql-query-library.md` wählen (z. B. `campaign-daily-v1`), Kunden-ID und Datumsfenster einsetzen.
2. Lesen und als Envelope speichern (Ausgabe nur unter `.adbot/`, git-ignoriert):
   ```bash
   uv run --no-project --with google-ads==35.0.0 scripts/gaql_via_api.py \
     --customer 1234567890 --resource campaign \
     --fields segments.date customer.id customer.descriptive_name customer.currency_code campaign.id campaign.name \
              campaign.status campaign.advertising_channel_type campaign_budget.amount_micros metrics.cost_micros metrics.conversions \
     --conditions "segments.date BETWEEN '2026-10-01' AND '2026-10-07'" \
     --query-id campaign-daily-v1 --out .adbot/runs/<run-id>/live/google-1234567890-campaign-daily-v1.json
   ```
   `--login-customer-id` nur bei Zugriff über ein Verwaltungskonto angeben; für nicht verknüpfte Konten führt der Header zu „permission denied".
   Alternativ liefert `scripts/gaql_via_mcp.py` dasselbe Envelope über den MCP-Server.
3. Normalisieren:
   ```python
   from claude_ads_core.adapters import GoogleAdsLiveReadAdapter
   adapter = GoogleAdsLiveReadAdapter("1234567890")
   snapshot = adapter.read_snapshot(".adbot/runs/<run-id>/live/google-1234567890-campaign-daily-v1.json")
   lineage = adapter.lineage()   # in run-manifest.adapters aufnehmen (mode: live_read)
   ```
4. Stichprobe gegen die Google-Ads-Oberfläche (Kosten, Conversions, ±1 %). Erst dann darf die Capability im Manifest von
   `fixture-verified` auf `live-verified` gehoben werden.

## Fehlerbilder

| Meldung | Bedeutung | Reaktion |
|---|---|---|
| `GOOGLE_PROJECT_ID is not set` | Projekt-ID fehlt | in `$ADBOT_PROFILE_DIR/env` eintragen |
| `credentials file missing` | keine Anmeldung vorhanden | `gcloud auth application-default login` (Teil A, Schritt 4) |
| `invalid_grant` | Anmeldung abgelaufen oder widerrufen (z. B. Zustimmungsbildschirm auf „Testing", nach 7 Tagen) | erneut anmelden; Zustimmungsbildschirm auf „In Produktion" stellen, wenn vertretbar |
| `This method is not allowed for use with explorer access` | Planungsdienst (Keyword-Ideen) braucht Basic | Basic für das Projekt beantragen oder Keyword-Planner-CSV nutzen |
| `INVALID_ARGUMENT` / `UNRECOGNIZED_FIELD` | GAQL-Feld passt nicht zur API-Version | `needs_input`, Query gegen aktuelle Felddoku prüfen |
| `rows must be a non-empty array` / „returned no rows" | leere Antwort | kein Datensatz – Fenster/Filter prüfen, nicht als „0 Spend" werten |
| `customer.id … does not match` | Antwort eines anderen Kontos gespeichert | Envelope verwerfen, Query mit korrekter Kunden-ID wiederholen |
