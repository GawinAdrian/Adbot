# 01 · Instalacja (Mac i Windows)

> **Wersja robocza:** tekst wymaga sprawdzenia przez osobę, dla której polski jest językiem ojczystym.

**Stan na:** 2026-11-01 · **Kto:** osoba znająca się na IT konfiguruje raz · **Czas:** ok. 30 minut

## Czego potrzebujesz

| Co | Po co | Sprawdzenie |
|---|---|---|
| **Dostęp do Claude** (własne konto/abonament lub klucz API) | praca AI odbywa się w Claude Code | koszty i plan ustala Anthropic; sprawdź wcześniej na stronie Anthropic |
| **Claude Code** (terminal lub karta „Code” w aplikacji Claude Desktop, Mac i Windows) | wykonuje `/zacznij`, `/analiza` itd. | wymagania planu dla aplikacji Desktop sprawdź w dokumentacji Anthropic |
| **Python 3.11 lub nowszy** | wykonuje analizę | `python3 --version` (Windows: `py --version`) |
| **uv** | w razie potrzeby pobiera bibliotekę Google | `uv --version` |
| **Narzędzie wiersza poleceń Google Cloud (`gcloud`)** | logowanie do Google | `gcloud --version` |
| **Google Ads Editor** | importuje szkic kampanii | w menu Start lub w Programach |

Narzędzia instaluj ze stron oficjalnych lub menedżerów pakietów (np. Mac: `brew install uv`, `brew install --cask google-cloud-sdk`;
Windows: `winget install astral-sh.uv`). **Nie wykonuj instrukcji, które wymagają `curl … | bash` ani `irm … | iex`.**

## Konfiguracja Adbota

1. Pobierz folder Adbota (klon Git lub pobrane archiwum) i w terminalu przejdź do tego folderu.
2. Utwórz i aktywuj środowisko wirtualne:
   - Mac: `python3 -m venv .venv && source .venv/bin/activate`
   - Windows (PowerShell): `py -m venv .venv`, a potem `.venv\Scripts\Activate.ps1`

   Potem polecenie wszędzie brzmi `python`. Adbot nie potrzebuje dodatkowych pakietów Pythona.
3. Sprawdź: `python -m claude_ads_core --version` pokazuje numer wersji.
4. Uruchom Claude Code w folderze Adbota (terminal: `claude`; aplikacja Desktop: wybierz folder jako projekt).
5. Wpisz `/zacznij`. Polecenia pojawiają się po wpisaniu `/`.

## Sprawdź

```bash
python -m claude_ads_core doctor --lang pl
```

Zaraz po instalacji „Ustawienia”, „Projekt Google Cloud” i „Logowanie Google” są jeszcze czerwone. To prawidłowe; dalej instrukcja 02.

## Szyfrowanie dysku (zalecane)

Raporty zawierają dane Twojego konta. Włącz **FileVault** (Mac) lub **BitLocker** (Windows) i potwierdź to raz:

```bash
python -m claude_ads_core settings set --disk-encryption-attested 2026-11-01
```

(wstaw dzisiejszą datę). Dopiero wtedy codzienny strażnik zapisuje dodatkowo formalny plik raportu `monitoring-bundle.json`. Bez potwierdzenia reszta działa normalnie.

## Usuwanie

Usuń folder po odłączeniu konta Google (instrukcja 03) i usunięciu strażnika (instrukcja 08).
