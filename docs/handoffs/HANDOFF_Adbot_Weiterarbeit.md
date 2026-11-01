# Handoff: Adbot – Weiterarbeit im eigenen Repo

**Stand:** 2026-11-01 · Dieses Dokument ist für eine **neue Claude-Code-Session in diesem Ordner** gedacht.
Lies zuerst `CLAUDE.md`, `AGENTS.md`, `README.md`, dann dieses Handoff.

## Was Adbot ist

Selbstbedienungs-Assistent für Google Ads (Deutsch und Polnisch) für kleine Unternehmen: analysieren, planen, als **pausierten** Entwurf vorbereiten, überwachen.
Read-only gegenüber dem Konto; Kampagnen nur als Google-Ads-Editor-CSV; jede Nutzerin mit eigenem Google-Konto und eigenem Cloud-Projekt; keine Developer-Tokens (seit 2026-09-09 abgeschafft).
Basis: Claude Ads v2 (MIT).

## Was funktioniert (verifiziert)

- **Zugriff ohne Token:** MCP-Server und `scripts/gaql_via_api.py` (nur `SearchStream`, `google-ads==35.0.0`) – am 2026-11-01 gegen ein echtes Konto lesend getestet.
- **Sprachen:** `claude_ads_core/i18n/` (Kataloge DE/PL/EN als Python-Module, Glossar mit 31 Begriffen), lokalisierte Berichte (`render --lang`), Einstellungen (`settings init|show|set`).
- **`doctor`** (offline lauffähig, lokalisiert, ohne Geheimnisse), **Briefing-Tor** (`briefing.py`), **Wächter** (`watch.py`, 6 Regeln, kleine Nenner lösen keinen Alarm aus), **Tagesjob** (`scripts/run_daily_watch.py`) und **Planer** (`scripts/schedule_watch.py`, macOS launchd / Windows-Aufgabenplanung, `--remove` idempotent), **Cockpit** (`cockpit build`, eine HTML-Datei ohne Skripte/Netz; im Browser auf Desktop und 390 px geprüft).
- **Befehle:** `/start`, `/verbinden`, `/trennen`, `/analyse`, `/kampagne`, `/bericht`, `/optimieren`, `/hilfe`; Skill `ads-assistent`; Prozesskarten `ads/references/prozesskarten.md`.
- **Anleitungen** `docs/de` und `docs/pl` (00–10, gleiche Dateinamen, Paritätstest).
- **Tests:** `python -m pytest -q` → 898 bestanden, 23 übersprungen, **2 bekannte Umgebungsfehler** (WeasyPrint-Systembibliothek; `test_valid_native_report_writes_commit_lock_…`). Frischer Klon liefert dasselbe Ergebnis. Leak-Test `tests/repo/test_no_client_data.py`.

## Was noch offen ist (ehrlich)

**Von Menschen zu erledigen**
1. **Polnisch prüfen** (Muttersprachler): `claude_ads_core/i18n/catalog_pl.py`, `glossary_data.py`, `docs/pl/*`. Danach `META["review_status"]` in `catalog_pl.py` auf `"geprueft"` und `reviewed_by` setzen und in allen `docs/pl/*.md` den Hinweis „Wersja robocza“ entfernen (Test koppelt beides).
2. **Handtest verbinden → `doctor --online` → trennen** auf einem Test-Google-Konto (Anleitungen 02/03); **Screenshots** für die Anleitungen ergänzen.
3. **Pilotlauf** mit einer echten Nutzerin: `/start` → `/analyse` → `/kampagne` (Import in den Google Ads Editor, nichts veröffentlichen) → `/bericht`. Befunde in `docs/handoffs/` festhalten.
4. **Claude-Zugang/Kosten** je Nutzerin klären (Anleitung 01 nennt nur, dass er nötig ist). Tarifvoraussetzung der Desktop-App ist auf der Anthropic-Seite nicht eindeutig; vor der Empfehlung prüfen.
5. **Erster Push:** Dieses Repo hat **keinen Remote**. Vor dem Anlegen eines privaten GitHub-Repos: `.github/workflows/*` und `.github/dependabot.yml` stammen aus Upstream und müssen geprüft/angepasst werden. `CODEOWNERS` wurde bewusst nicht übernommen.

**Technisch / Folgearbeiten**
6. **API-Schreibpfad** (Kampagne anlegen, pausieren, Budget) mit vollem Mutation-Gate – eigener PRP (PRD Feature D). Bis dahin bleibt `account-mutation` im Manifest `disabled`.
7. **Release-Gates neu aufsetzen:** `scripts/release.py` bindet `pyproject.toml`, Locks und das Dependency-Inventar an ein unabhängig geprüftes Upstream-Dokument. Jede Änderung daran lässt ~32 Release-Tests scheitern (Grund, warum die Kataloge Python-Module statt JSON-Package-Data sind). `status` meldet außerdem **veraltete tragende Claims aus dem Upstream-Stand (August)** als nächsten Blocker. Beides blockiert jeden Release-Anspruch; Adbot erhebt keinen.
8. **Rechtshinweise** DE/PL (Impressum, Datenschutz, Einwilligung, regulierte Kategorien) sind **nicht recherchiert** (`ads/references/markt-de-pl.md`); der Assistent stellt nur Fragen, gibt keine Rechtsaussagen.
9. **Installer:** Es gibt keinen eigenen Installer; Anleitung 01 beschreibt die manuellen Schritte (Windows nicht praktisch getestet). Die geerbten `install.sh`/`install.ps1` installieren den Upstream-Skill und sind unverändert.
10. **Schwellen des Wächters** (`claude_ads_core/watch.py`, Tabelle in `ads/references/kadenz-und-regeln.md`) sind Startwerte; nach dem Pilot anhand echter Konten justieren (Test koppelt Doku und Code).
11. **Weitere Plattformen** sind im Code vorhanden (Export-Audits), aber nicht Teil des Assistenten.

## Unabhängiger Review (2026-11-01) und was daraus wurde

Ein Reviewer in frischem Kontext (kein signierter externer Review im Sinne von `control-plane/RELEASE_REQUIREMENTS.md`) fand 12 Punkte. Alle belegten sind behoben und mit Regressionstests abgesichert:
Wächter erkannte lange stillstehende Kampagnen nicht (jetzt: Vergleich mit **allen** früheren Tagen); kleine Conversion-Zahlen lösten Rot aus (jetzt mindestens 3 Conversions in der Vorwoche; neue Kampagnen werden bei den Ausgaben nicht beurteilt); Datenlücke konnte im Tageslauf nie auslösen (jetzt Vergleich mit dem Datum des letzten Laufs); Tagesjob scheiterte mit schmalem PATH (jetzt `uv` wird gesucht, `PYTHONPATH`/`cwd` gesetzt, PATH im launchd-Auftrag, Cockpit wird wirklich gebaut, „keine Zeilen“ wird als gelbes Ergebnis gespeichert); `GOOGLE_ADS_LOGIN_CUSTOMER_ID` wurde im Skript ignoriert; Anzeigenstatus-Abfrage las auch entfernte/pausierte Anzeigen (jetzt nur anzeigbare; Feld live akzeptiert, CLM-0227); Ergebnisdateien waren 0644 (jetzt 0600/0700); `doctor` schrieb nach `/tmp` und stürzte ohne `uv` ab; polnische Pluralform bei Klicks; englische Glossar-Erklärungen fehlten; Entwurfshinweis fehlte zur Laufzeit; Währung des Briefings wird gegen die Kontowährung geprüft und die Zustimmung wörtlich festgehalten; wirkungslose Tests (`or True`) ersetzt, Schreibfreiheit des Lese-Skripts jetzt per Syntaxbaum geprüft.

**Bewusst offen geblieben (ehrlich):**
- **Der MCP-Server wird ungepinnt von GitHub gestartet** (`scripts/google_ads_mcp.sh`); die Aussage „nur lesend“ gilt für den geprüften Stand. Vor ernsthafter Nutzung auf ein geprüftes Tag/Commit pinnen. Der direkte Weg (`gaql_via_api.py`) braucht den MCP-Server nicht.
- **Der OAuth-Bereich `adwords` ist technisch nicht „nur lesend“.** Nur-Lesen wird im Code und durch Tests sichergestellt, nicht durch die Anmeldung (Anleitung 02 sagt das offen).
- `monitoring-bundle` beruht auf der **eigenen Bestätigung** der Festplattenverschlüsselung (kein Zukunftsdatum mehr); „verified“ im Bundle heißt „vom Nutzer bestätigt“.
- **Conversion-Verzögerung** ist nicht modelliert (der jüngste Tag kann unvollständig sein); die Regeln nutzen deshalb ganze Wochen und Mindestmengen.
- Die Regel „abgelehnte Anzeigen“ wurde nur mit Fixtures und einem akzeptierten Live-Feld geprüft, nicht an einer echten abgelehnten Anzeige.
- **Windows:** Aufgabenplanung, Pfade und `uv`-Suche sind nur per Code-Lesen geprüft, nicht praktisch.
- CLM-0211 bis CLM-0213 (Upstream) sind über ihrem Prüfdatum (geerbt).
- Beim Aufruf aus einem fremden Ordner kann eine gemeinsame `.venv` `claude_ads_core` aus einem anderen Repo laden; im eigenen Adbot-`venv` (Anleitung 01) tritt das nicht auf.

## Konventionen

- Neue Meldungen in **allen drei** Katalogen (`i18n/catalog_en|de|pl.py`); de/pl identische Schlüssel, en nur ohne `enum.*`-Extras.
- Deutsch mit echten Umlauten, Polnisch mit Diakritika; keine Plattformzahl ohne Quellen-/Claim-Eintrag (Ledger werden per Textanhängen erweitert; tragende Claims müssen `verified` sein).
- Run-Daten liegen in `.adbot/runs/<run-id>/` (git-ignoriert), Profil in `~/.config/adbot/standard` (`ADBOT_PROFILE_DIR`).
- Keine Geheimnisse, keine absoluten Pfade, keine Kundennamen im Repo – der Leak-Test läuft in der normalen Suite.

## Erste Schritte in der neuen Session

```bash
python3 -m venv .venv && source .venv/bin/activate
python -m pytest -q                       # erwartet: 898 passed, 2 bekannte Fehler
python -m claude_ads_core doctor --lang de
claude                                    # dann /hilfe
```
