---
description: Propozycje usprawnień jako szkic z porównaniem przed/po (polska wersja /optimieren)
---

# Optymalizuj

Język: odpowiadaj po polsku (to polskie polecenie), nawet gdy w ustawieniach (`python -m claude_ads_core settings show`, pole `language`) jest `de`; ustawień przy tym nie zmieniaj.
Jeśli ustawień jeszcze nie ma, utwórz je bez pytania: `python -m claude_ads_core settings init --lang pl`.
Korzystaj ze słowniczka (`claude_ads_core.i18n.glossary()`) i przy pierwszym użyciu krótko wyjaśniaj każde pojęcie specjalistyczne. Polski pozostaje wersją roboczą, dopóki nie sprawdzi go native speaker.

Przeczytaj `ads/references/kadenz-und-regeln.md` oraz skill `ads-optimize`.

1. Propozycje wyprowadzaj wyłącznie z aktualnego raportu. Przy każdej: przed/po, objęte obiekty (ID), spodziewany efekt, uwaga o fazie uczenia się, instrukcja cofnięcia, pewność oceny.
2. Najwyżej **jedna runda zmian na kampanię w tygodniu**, chyba że wystąpi problem ze śledzeniem, płatnością lub nietypowy skok budżetu. „Za mało danych, poczekaj” jest prawidłowym wynikiem.
3. Żadnej sztywnej reguły wstrzymywania według wielokrotności CPA, żadnych ogólnych proporcji budżetu.
4. Wynik zapisz jako `optimisation-draft.md`. Wdrożenie wykonuje użytkowniczka sama; zapis przez API jest w tej wersji wyłączony.
5. Usuwanie jest odrzucane; alternatywy: wstrzymanie, archiwizacja, etykieta, kopia zapasowa.
