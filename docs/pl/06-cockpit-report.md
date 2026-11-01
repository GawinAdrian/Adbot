# 06 · Kokpit i raport tygodniowy

> **Wersja robocza:** tekst wymaga sprawdzenia przez osobę, dla której polski jest językiem ojczystym.

**Stan na:** 2026-11-01

**Polecenie:** `/bericht` · **Wynik:** `cockpit.html` i raport tygodniowy · **Niczego nie zmienia** na Twoim koncie

## Otwieranie kokpitu

`/bericht` buduje przegląd i podaje ścieżkę pliku `cockpit.html` (w folderze ostatniego przebiegu w `.adbot/runs/`).
Dwukrotne kliknięcie otwiera plik w przeglądarce. Strona to **plik lokalny**: przy otwarciu nie są wysyłane żadne dane.

Samodzielnie: `python -m claude_ads_core cockpit build --watch-result .adbot/runs/<przebieg>/watch-result.json`

## Jak go czytać (od góry do dołu)

1. **Sygnalizator** – Zielony: nic do zrobienia. Żółty: proszę rzucić okiem. Czerwony: trzeba wkrótce działać. Szary: za mało danych. Kolor jest zawsze podany także tekstem.
2. **Co się wydarzyło?** – jedno zdanie i do pięciu komunikatów, każdy z kolejnym krokiem.
3. **Kluczowe liczby** – ostatnie 7 dni w porównaniu z 7 dniami wcześniej, każda liczba z objaśnieniem.
4. **Najważniejsze zalecenia** – najwyżej trzy, z porównaniem przed/po, nakładem pracy, ryzykiem i pewnością. „Poczekać na więcej danych” to często właściwa odpowiedź.
5. **Czeka na Twoje zatwierdzenie** i **Dziennik zmian** – co jest otwarte i co zmieniono.
6. **Luki i uwagi** – czego Adbot nie mógł odczytać (np. status płatności) lub gdy dane są stare.

## Rytm tygodniowy

Domyślnie: **poniedziałek**. Zmiana: `python -m claude_ads_core settings set --weekday friday` (lub `--report monthly`).
Analizę tygodniową uruchamiasz sam(a) poleceniem `/bericht`; strażnik działa codziennie sam (instrukcja 08).

## Gdy coś nie działa

- „Dane mają X dni”: komputer był wyłączony lub pobieranie się nie udało → instrukcja 08.
- Strona jest pusta: nie ma jeszcze przebiegu; instrukcja 08, sekcja „Jednorazowo ręcznie”.
