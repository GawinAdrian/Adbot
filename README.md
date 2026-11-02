# Adbot

**Deutsch** · [Polski](README.pl.md)

**DE:** Google-Werbung für kleine Unternehmen – analysieren, planen, als pausierten Entwurf vorbereiten und überwachen.
Auf **Deutsch und Polnisch**, mit Anleitungen Schritt für Schritt.
**PL:** Reklama w Google dla małych firm – analiza, planowanie, wstrzymany szkic kampanii i monitorowanie.
Po **niemiecku i po polsku**, z instrukcjami krok po kroku.

Adbot arbeitet mit [Claude Code](https://claude.com/claude-code) und liest dein **eigenes** Google-Ads-Konto nur lesend.
Es ändert nichts an deinem Konto, löscht nichts und veröffentlicht keine Kampagne – das machst du selbst.

> **Status:** frühe Version. Polnische Texte sind **Entwurf** und warten auf die Prüfung durch einen Muttersprachler.
> Das Projekt erhebt keinen Release-Anspruch (siehe `control-plane/RELEASE_REQUIREMENTS.md`).

## Loslegen / Zacznij tutaj

| | Deutsch | Polski |
|---|---|---|
| Überblick / Przegląd | [docs/de/00-overview.md](docs/de/00-overview.md) | [docs/pl/00-overview.md](docs/pl/00-overview.md) |
| Installation / Instalacja | [docs/de/01-install.md](docs/de/01-install.md) | [docs/pl/01-install.md](docs/pl/01-install.md) |
| Google-Konto verbinden / Połącz konto | [docs/de/02-connect.md](docs/de/02-connect.md) | [docs/pl/02-connect.md](docs/pl/02-connect.md) |
| Konto trennen / Odłącz konto | [docs/de/03-disconnect.md](docs/de/03-disconnect.md) | [docs/pl/03-disconnect.md](docs/pl/03-disconnect.md) |
| Analyse / Analiza | [docs/de/04-analysis.md](docs/de/04-analysis.md) | [docs/pl/04-analysis.md](docs/pl/04-analysis.md) |
| Erste Kampagne / Pierwsza kampania | [docs/de/05-first-campaign.md](docs/de/05-first-campaign.md) | [docs/pl/05-first-campaign.md](docs/pl/05-first-campaign.md) |
| Cockpit & Bericht / Kokpit i raport | [docs/de/06-cockpit-report.md](docs/de/06-cockpit-report.md) | [docs/pl/06-cockpit-report.md](docs/pl/06-cockpit-report.md) |
| Freigaben / Zatwierdzanie | [docs/de/07-approvals-undo.md](docs/de/07-approvals-undo.md) | [docs/pl/07-approvals-undo.md](docs/pl/07-approvals-undo.md) |
| Täglicher Wächter / Strażnik | [docs/de/08-watcher.md](docs/de/08-watcher.md) | [docs/pl/08-watcher.md](docs/pl/08-watcher.md) |
| Fehlerbehebung / Problemy | [docs/de/09-troubleshooting.md](docs/de/09-troubleshooting.md) | [docs/pl/09-troubleshooting.md](docs/pl/09-troubleshooting.md) |
| Glossar & Datenschutz / Słowniczek i dane | [docs/de/10-glossary-privacy.md](docs/de/10-glossary-privacy.md) | [docs/pl/10-glossary-privacy.md](docs/pl/10-glossary-privacy.md) |

## Kurzstart

```bash
python3 -m venv .venv && source .venv/bin/activate     # Windows: py -m venv .venv ; .venv\Scripts\Activate.ps1
python -m claude_ads_core doctor --lang de              # oder --lang pl
claude                                                  # im Adbot-Ordner; dann /start
```

Befehle in Claude Code: `/start` · `/verbinden` · `/trennen` · `/analyse` · `/kampagne` · `/bericht` · `/optimieren` · `/hilfe`.
Polecenia po polsku (Entwurf): `/zacznij` · `/polacz` · `/odlacz` · `/analiza` · `/kampania` · `/raport` · `/optymalizuj` · `/pomoc`.

### Der geerbte Orchestrator

Unter den Adbot-Befehlen liegt der allgemeine Orchestrator von Claude Ads: `/ads` (als eigenständiger Skill) bzw. `/claude-ads:ads` (bei Installation als Plugin).
Er bietet Audits aus Exporten und Planungs-Workflows für fortgeschrittene Nutzer; für den Alltag nutzt du die Adbot-Befehle oben.

## Wie es aufgebaut ist

- **Zahlen deterministisch, Deutung durch KI.** Ein täglicher Wächter (`claude_ads_core/watch.py`) prüft ohne KI; die KI deutet nur auf Abruf.
- **Eigenes Konto, eigenes Google-Cloud-Projekt.** Es gibt keinen gemeinsamen Zugang. Developer-Tokens sind seit 2026-09-09 abgeschafft (`ads/references/google-auth-und-zugriff.md`).
- **Cockpit:** eine lokale HTML-Datei ohne Netzwerk (`python -m claude_ads_core cockpit build`).
- **Sicherheit:** nur lesend; kein Löschen; Kampagnen nur als pausierter Google-Ads-Editor-Entwurf; Zugangsdaten nie im Repository.
- **Quellen statt Behauptungen:** Plattformaussagen stehen mit Datum im Quellen- und Claim-Register (`control-plane/manifests/`).

Entwicklung und Regeln für Agenten: `AGENTS.md`, `CLAUDE.md`. Tests: `python -m pytest -q`.

## Umgebungsvariablen (nur Namen)

`GOOGLE_PROJECT_ID`, `GOOGLE_APPLICATION_CREDENTIALS`, `GOOGLE_ADS_LOGIN_CUSTOMER_ID` (nur bei Verwaltungskonto),
`ADBOT_PROFILE_DIR`, `ADBOT_LANG`; `GOOGLE_ADS_DEVELOPER_TOKEN`/`DEVELOPER_TOKEN` sind **veraltet und optional**.

## Herkunft und Lizenz

Adbot baut auf **Claude Ads v2** von AgriciDaniel auf (`https://github.com/AgriciDaniel/claude-ads`, MIT-Lizenz). Lizenz: `LICENSE`.
Drittanbieter-Hinweise: `THIRD_PARTY_NOTICES.md`. Die 12-Plattform-Auditfunktionen des Ursprungs bleiben im Code, werden aber hier nicht
beworben; unterstützt ist **Google Ads**.
