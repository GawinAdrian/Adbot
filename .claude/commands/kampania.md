---
description: Zaplanuj pierwszą kampanię i przygotuj wstrzymany szkic w Google Ads Editor (polska wersja /kampagne)
---

# Kampania

Język: odpowiadaj po polsku (to polskie polecenie), nawet gdy w ustawieniach (`python -m claude_ads_core settings show`, pole `language`) jest `de`; ustawień przy tym nie zmieniaj.
Jeśli ustawień jeszcze nie ma, utwórz je bez pytania: `python -m claude_ads_core settings init --lang pl`.
Korzystaj ze słowniczka (`claude_ads_core.i18n.glossary()`) i przy pierwszym użyciu krótko wyjaśniaj każde pojęcie specjalistyczne. Polski pozostaje wersją roboczą, dopóki nie sprawdzi go native speaker.

Przeczytaj kartę „Campaign” w `ads/references/prozesskarten.md`, `docs/runbooks/editor-csv-import.md` oraz skille `ads-plan`, `ads-budget`, `ads-keywords`, `ads-copy`.

1. **Brama briefu:** zapytaj o cel, dzienny budżet z walutą, region/promień, definicję konwersji, ofertę i stronę internetową i **poproś użytkowniczkę o potwierdzenie**. Jej zgodę zapisz **dosłownie** jako `confirmation_quote`, walutę konta z odczytanych danych przekaż jako `account_currency` i wywołaj `claude_ads_core.briefing.validate_briefing`; bez potwierdzenia lub przy innej walucie nie powstaje żaden szkic.
2. Plan ze scenariuszami zamiast obietnic; wpływ budżetu podawaj w złotych lub euro. Żadnych gwarancji.
3. Słowa kluczowe według intencji wyszukiwania, reklamy ze sprawdzonymi limitami znaków, wykluczenia **tylko** z raportem wyszukiwanych haseł i kontrolą nadmiernego blokowania.
4. Szkic wygeneruj przez `claude_ads_core.editor_export` (`briefing_to_campaign` → `write_editor_csv`). Wszystkie kampanie **wstrzymane**.
5. Podsumowanie prostym językiem: co przygotowano, ile to kosztuje maksymalnie dziennie, co sprawdzić przed publikacją. Import i publikację wykonuje użytkowniczka (`docs/pl/05-first-campaign.md`).

Adbot niczego nie publikuje na koncie.
