---
description: Konfiguracja Adbota: język, połączenie, firma, konto (polska wersja /start)
---

# Zacznij

Język: odpowiadaj po polsku (to polskie polecenie), nawet gdy w ustawieniach (`python -m claude_ads_core settings show`, pole `language`) jest `de`; ustawień przy tym nie zmieniaj.
Jeśli ustawień jeszcze nie ma, utwórz je bez pytania: `python -m claude_ads_core settings init --lang pl`.
Korzystaj ze słowniczka (`claude_ads_core.i18n.glossary()`) i przy pierwszym użyciu krótko wyjaśniaj każde pojęcie specjalistyczne. Polski pozostaje wersją roboczą, dopóki nie sprawdzi go native speaker.

Przeczytaj kartę „Start” w `ads/references/prozesskarten.md` i postępuj zgodnie z nią:

1. `python -m claude_ads_core doctor`. Jeśli konto nie jest połączone: `/polacz` (instrukcja `docs/pl/02-connect.md`).
2. Krótko zbierz dane firmy (nazwa, strona internetowa, oferta, region). Niczego nie zakładaj ani nie wymyślaj.
3. Wybierz konto: narzędziem MCP `list_accessible_customers` (jeśli połączone) albo użytkowniczka odczytuje 10-cyfrowy identyfikator klienta w Google Ads. Potem `python -m claude_ads_core settings set --account <ID>`.
4. Daj rekomendację: **przypadek A** (konto ma historię) → `/analiza`; **przypadek B** (jeszcze brak kampanii) → `/analiza` (przypadek B), a potem `/kampania`.
5. Podsumowanie: co zostało zrobione, jaki plik powstał, następny krok, odpowiednia instrukcja.

Niczego nie zmieniaj na koncie. Nigdy nie pytaj o dane logowania.
