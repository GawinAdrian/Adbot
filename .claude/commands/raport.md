---
description: Odczytaj wynik strażnika i raport tygodniowy, otwórz kokpit (polska wersja /bericht)
---

# Raport

Język: odpowiadaj po polsku (to polskie polecenie), nawet gdy w ustawieniach (`python -m claude_ads_core settings show`, pole `language`) jest `de`; ustawień przy tym nie zmieniaj.
Jeśli ustawień jeszcze nie ma, utwórz je bez pytania: `python -m claude_ads_core settings init --lang pl`.
Korzystaj ze słowniczka (`claude_ads_core.i18n.glossary()`) i przy pierwszym użyciu krótko wyjaśniaj każde pojęcie specjalistyczne. Polski pozostaje wersją roboczą, dopóki nie sprawdzi go native speaker.

Przeczytaj kartę „Report” w `ads/references/prozesskarten.md` oraz `ads/references/kadenz-und-regeln.md`.

1. Wczytaj ostatni wynik strażnika (`python -m claude_ads_core watch --help` pokazuje wywołanie); jeśli jest starszy niż oczekiwano, wskaż to jako lukę w danych.
2. Interpretacja tygodnia: trend względem poprzedniego tygodnia, prawdopodobne przyczyny, **najwyżej trzy rekomendacje** z korzyścią, ryzykiem i pewnością. Przy skąpych danych „poczekaj” jest dopuszczalnym wynikiem.
3. Zbuduj kokpit: `python -m claude_ads_core cockpit build --help`. Podaj ścieżkę do pliku HTML.
4. Niczego nie zmieniaj na koncie.
