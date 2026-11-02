# Adbot

[Deutsch](README.md) · **Polski**

Reklama w Google dla małych firm – analiza, planowanie, przygotowanie wstrzymanego szkicu kampanii i monitorowanie.
Po **polsku i po niemiecku**, z instrukcjami krok po kroku.

Adbot działa z [Claude Code](https://claude.com/claude-code) i odczytuje **Twoje własne** konto Google Ads wyłącznie w trybie do odczytu.
Niczego na Twoim koncie nie zmienia, niczego nie usuwa i nie publikuje żadnej kampanii – to robisz Ty sam(a).

> **Status:** wczesna wersja, prywatna. Polskie teksty to **wersja robocza** i czekają na sprawdzenie przez native speakera.
> Projekt nie zgłasza gotowości do wydania (zob. `control-plane/RELEASE_REQUIREMENTS.md`).

## Zacznij tutaj

| | Polski | Deutsch |
|---|---|---|
| Przegląd | [docs/pl/00-overview.md](docs/pl/00-overview.md) | [docs/de/00-overview.md](docs/de/00-overview.md) |
| Instalacja | [docs/pl/01-install.md](docs/pl/01-install.md) | [docs/de/01-install.md](docs/de/01-install.md) |
| Połącz konto Google | [docs/pl/02-connect.md](docs/pl/02-connect.md) | [docs/de/02-connect.md](docs/de/02-connect.md) |
| Odłącz konto | [docs/pl/03-disconnect.md](docs/pl/03-disconnect.md) | [docs/de/03-disconnect.md](docs/de/03-disconnect.md) |
| Analiza | [docs/pl/04-analysis.md](docs/pl/04-analysis.md) | [docs/de/04-analysis.md](docs/de/04-analysis.md) |
| Pierwsza kampania | [docs/pl/05-first-campaign.md](docs/pl/05-first-campaign.md) | [docs/de/05-first-campaign.md](docs/de/05-first-campaign.md) |
| Kokpit i raport | [docs/pl/06-cockpit-report.md](docs/pl/06-cockpit-report.md) | [docs/de/06-cockpit-report.md](docs/de/06-cockpit-report.md) |
| Zatwierdzanie i cofanie | [docs/pl/07-approvals-undo.md](docs/pl/07-approvals-undo.md) | [docs/de/07-approvals-undo.md](docs/de/07-approvals-undo.md) |
| Codzienny strażnik | [docs/pl/08-watcher.md](docs/pl/08-watcher.md) | [docs/de/08-watcher.md](docs/de/08-watcher.md) |
| Rozwiązywanie problemów | [docs/pl/09-troubleshooting.md](docs/pl/09-troubleshooting.md) | [docs/de/09-troubleshooting.md](docs/de/09-troubleshooting.md) |
| Słowniczek i dane | [docs/pl/10-glossary-privacy.md](docs/pl/10-glossary-privacy.md) | [docs/de/10-glossary-privacy.md](docs/de/10-glossary-privacy.md) |

## Szybki start

```bash
python3 -m venv .venv && source .venv/bin/activate     # Windows: py -m venv .venv ; .venv\Scripts\Activate.ps1
python -m claude_ads_core doctor --lang pl              # lub --lang de
claude                                                  # w folderze Adbota; potem /zacznij
```

Polecenia w Claude Code: `/zacznij` · `/polacz` · `/odlacz` · `/analiza` · `/kampania` · `/raport` · `/optymalizuj` · `/pomoc`.
Każde z nich ma niemiecki odpowiednik: `/start` · `/verbinden` · `/trennen` · `/analyse` · `/kampagne` · `/bericht` · `/optimieren` · `/hilfe`.

### Odziedziczony orkiestrator

Pod poleceniami Adbota działa ogólny orkiestrator Claude Ads: `/ads` (jako samodzielny skill) lub `/claude-ads:ads` (po instalacji jako wtyczka).
Oferuje audyty na podstawie eksportów i procesy planowania dla zaawansowanych użytkowników; na co dzień korzystasz z powyższych poleceń Adbota.

## Jak to jest zbudowane

- **Liczby deterministyczne, interpretacja przez AI.** Codzienny strażnik (`claude_ads_core/watch.py`) sprawdza konto bez AI; AI interpretuje wyniki tylko na życzenie.
- **Własne konto, własny projekt Google Cloud.** Nie ma wspólnego dostępu. Tokeny programisty (developer token) zostały zniesione 2026-09-09 (`ads/references/google-auth-und-zugriff.md`).
- **Kokpit:** lokalny plik HTML bez dostępu do sieci (`python -m claude_ads_core cockpit build`).
- **Bezpieczeństwo:** tylko odczyt; bez usuwania; kampanie wyłącznie jako wstrzymany szkic Google Ads Editor; dane logowania nigdy w repozytorium.
- **Źródła zamiast twierdzeń:** informacje o platformie są zapisane z datą w rejestrze źródeł i twierdzeń (`control-plane/manifests/`).

Rozwój i reguły dla agentów: `AGENTS.md`, `CLAUDE.md`. Testy: `python -m pytest -q`.

## Zmienne środowiskowe (tylko nazwy)

`GOOGLE_PROJECT_ID`, `GOOGLE_APPLICATION_CREDENTIALS`, `GOOGLE_ADS_LOGIN_CUSTOMER_ID` (tylko dla konta menedżerskiego),
`ADBOT_PROFILE_DIR`, `ADBOT_LANG`; `GOOGLE_ADS_DEVELOPER_TOKEN`/`DEVELOPER_TOKEN` są **przestarzałe i opcjonalne**.

## Pochodzenie i licencja

Adbot bazuje na **Claude Ads v2** autorstwa AgriciDaniel (`https://github.com/AgriciDaniel/claude-ads`, licencja MIT). Licencja: `LICENSE`.
Informacje o komponentach zewnętrznych: `THIRD_PARTY_NOTICES.md`. Funkcje audytu 12 platform z oryginału pozostają w kodzie, ale nie są tu promowane;
obsługiwany jest **Google Ads**.
