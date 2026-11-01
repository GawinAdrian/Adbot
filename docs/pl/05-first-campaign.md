# 05 · Pierwsza kampania: brief, szkic, import

> **Wersja robocza:** tekst wymaga sprawdzenia przez osobę, dla której polski jest językiem ojczystym.

**Stan na:** 2026-11-01

**Polecenie:** `/kampagne` · **Wynik:** szkic CSV, **wszystko wstrzymane** · **Publikujesz tylko Ty**

## 1. Brief (każdą informację potwierdzasz Ty)

Adbot pyta o pięć rzeczy i prosi o **wyraźne potwierdzenie**. Bez potwierdzenia szkic nie powstaje:

1. **Cel:** telefony, zapytania czy sprzedaż?
2. **Budżet dzienny** z walutą: ile reklama może kosztować najwyżej dziennie?
3. **Region lub promień.**
4. **Definicja konwersji:** co jest sukcesem (np. wysłany formularz, rozmowa dłuższa niż określony czas)?
5. **Oferta i strona** (`https://…`).

## 2. Plan i szkic

Adbot pokazuje scenariusze zamiast obietnic (z jawnymi założeniami), słowa kluczowe według intencji wyszukiwania, teksty reklam ze sprawdzonymi limitami znaków.
**Wykluczające słowa kluczowe** dodaje tylko wtedy, gdy dostarczysz raport wyszukiwanych haseł z uzasadnieniem. Szkic jest zapisany jako plik CSV dla
Google Ads Editor. **Każda kampania jest wstrzymana.**

## 3. Import do Google Ads Editor

1. Otwórz Google Ads Editor i **pobierz** swoje konto.
2. Menu *Konto → Importuj → Z pliku* → wybierz plik CSV. (Nazwy w interfejsie mogą się różnić.)
3. **Sprawdź podgląd:** przypisanie kolumn, **lokalizacje** (Editor może zapytać o przypisanie nazwy miejsca), **języki**, strategię ustalania stawek, budżet dzienny.
4. Obejrzyj zmiany w Editorze. **Jeszcze nie publikuj („Opublikuj”).**
5. Dopiero gdy wszystko się zgadza i **śledzenie konwersji działa**: opublikuj i świadomie **włącz** kampanię.

Uwaga: szkic podaje język i kraj po angielsku (np. „Polish”, „Poland”). Przy pierwszym imporcie sprawdź w podglądzie, czy Editor przypisał je poprawnie.

## Gdy coś nie działa

- Editor zgłasza błąd w wierszu: podaj komunikat Adbotowi; poprawi szkic.
- Miejsce nie zostało rozpoznane: wybierz je ręcznie w Editorze.
- Więcej: instrukcja 09 oraz runbook `docs/runbooks/editor-csv-import.md`.
