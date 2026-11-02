# 04 · Pierwsza analiza

> **Wersja robocza:** tekst wymaga sprawdzenia przez osobę, dla której polski jest językiem ojczystym.

**Stan na:** 2026-11-01

**Polecenie:** `/analiza` · **Wynik:** plik w folderze `.adbot/runs/…` · **Niczego nie zmienia** na Twoim koncie

## Przypadek A: masz już kampanie

Adbot odczytuje kampanie, grupy reklam, słowa kluczowe, wyszukiwane hasła, konwersje i budżet (tylko do odczytu), podaje okres, strefę czasową i walutę
oraz przedstawia **najwyżej trzy priorytety**. Każdy ma uzasadnienie, pewność wypowiedzi i kolejny krok. Brakujące dane i sprzeczności są wymienione otwarcie.

**Pytania, które Adbot może zadać:** Co jest dla Ciebie sukcesem (telefon, formularz, zakup)? Czy ostatnio były duże zmiany?

## Przypadek B: nie masz jeszcze kampanii

Adbot bada Twoją **stronę** (zrozumiałość, strona docelowa, drogi kontaktu), **rynek i konkurencję**, możliwe **słowa kluczowe** i sprawdza, czy jest
**śledzenie konwersji**. Mówi wprost, czego bez historii nie da się wiedzieć.

**Pomysły na słowa kluczowe:** Przez interfejs są dostępne tylko przy dostępie „Basic” Twojego projektu Google Cloud. Bez Basic eksportujesz w Google Ads z Planera słów kluczowych
plik CSV i przekazujesz go Adbotowi; on go odczytuje.

## Tak poznasz, że się udało

- Na końcu Adbot podaje plik wynikowy i kolejny krok.
- Nie podaje liczb bez jednostki, okresu i źródła.
- Nie podaje wykluczających słów kluczowych, dopóki nie dostarczysz raportu wyszukiwanych haseł.

## Gdy coś nie działa

`python -m claude_ads_core doctor --lang pl --online` pokazuje, czy połączenie działa. Zobacz instrukcję 09.
