# 08 · Codzienny strażnik: konfiguracja i usuwanie

> **Wersja robocza:** tekst wymaga sprawdzenia przez osobę, dla której polski jest językiem ojczystym.

**Stan na:** 2026-11-01

**Co robi:** Codziennie skrypt odczytuje (tylko do odczytu) ostatnie 14 dni i sprawdza: zużycie budżetu, czy reklamy nadal działają, konwersje, odrzucone reklamy, wiek danych.
**Bez AI i bez kosztów.** Wynikiem jest sygnalizator w kokpicie. Reguły i progi: `ads/references/kadenz-und-regeln.md`.

## Wymagania

Konto jest połączone (`doctor` pokazuje „połączone”) i wybrano aktywne konto (`/start` lub `python -m claude_ads_core settings set --account 1234567890`).

## Jednorazowo ręcznie

```bash
python scripts/run_daily_watch.py --dry-run     # pokazuje tylko polecenia
python scripts/run_daily_watch.py               # odczytuje i analizuje
python -m claude_ads_core cockpit build --watch-result .adbot/runs/<przebieg>/watch-result.json
```

## Codziennie automatycznie

```bash
python scripts/schedule_watch.py --dry-run      # pokazuje, co by się stało
python scripts/schedule_watch.py --time 07:30   # konfiguracja
python scripts/schedule_watch.py --remove       # usunięcie (można wykonać wielokrotnie)
```

Mac: zadanie w tle (launchd) dla Twojego użytkownika. Windows: zaplanowane zadanie „AdbotWatch”. Dzienniki (Mac): `~/.config/adbot/logs`.

**Gdy komputer o tej porze jest wyłączony:** kolejny przebieg uzupełni brakujące dni; do tego czasu kokpit pokazuje „Dane mają X dni”.
Wyłączenie bez usuwania: `python -m claude_ads_core settings set --watch off`.

## Czego strażnik nigdy nie robi

Nie zmienia Twojego konta, niczego nie usuwa i zapisuje tylko w nowych folderach w `.adbot/runs/`. Formalny plik `monitoring-bundle.json` powstaje tylko wtedy, gdy potwierdzisz
szyfrowanie dysku (instrukcja 01).

## Gdy coś nie działa

Zobacz instrukcję 09. Najpierw sprawdź `python -m claude_ads_core doctor --online`.
