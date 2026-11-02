---
description: Odłącz konto Google od Adbota (krok po kroku) (polska wersja /trennen)
argument-hint: [opcjonalnie: de|pl]
---

# Odłącz konto Google

Język: odpowiadaj po polsku (to polskie polecenie), nawet gdy w ustawieniach (`python -m claude_ads_core settings show`, pole `language`) jest `de`; ustawień przy tym nie zmieniaj.
Jeśli ustawień jeszcze nie ma, utwórz je bez pytania: `python -m claude_ads_core settings init --lang pl`.
Korzystaj ze słowniczka (`claude_ads_core.i18n.glossary()`) i przy pierwszym użyciu krótko wyjaśniaj każde pojęcie specjalistyczne. Polski pozostaje wersją roboczą, dopóki nie sprawdzi go native speaker.
Jeśli podano `$ARGUMENTS`, użyj tego języka zamiast polskiego.

## Zasady (bez wyjątków)

- Odłączenie **nigdy** nie zmienia konta Google Ads ani kampanii. Odbiera tylko Adbotowi dostęp.
- Usuwanie plików (plik logowania, profil, `.adbot/`) tylko po **wyraźnym** potwierdzeniu użytkowniczki i z uwagą, że nie da się tego cofnąć.
- Kroki w Google (strona uprawnień, usunięcie projektu) użytkowniczka wykonuje sama w przeglądarce.

## Przebieg

1. Przeczytaj `docs/pl/03-disconnect.md` (po niemiecku `docs/de/03-disconnect.md`) i krótko wyjaśnij trzy poziomy.
2. Zapytaj, czego użytkowniczka chce: tylko odłączyć (poziom 1 i 2, zalecane), dodatkowo usunąć projekt w chmurze (poziom 3) oraz czy dane lokalne zachować, czy usunąć.
3. Poziom 1: wyjaśnij, że `gcloud auth application-default revoke` usuwa lokalny plik logowania; użytkowniczka wykonuje to sama (prefiks `!`).
4. Poziom 2: wskaż <https://myaccount.google.com/permissions>, tam wybierz aplikację „Adbot” (lub nadaną nazwę) i „Usuń dostęp”.
5. Poziom 3 tylko na wyraźne życzenie, również wykonywany przez użytkowniczkę.
6. Sprawdzenie: `python -m claude_ads_core doctor`. Oczekiwany wynik: komunikat o niepołączonym koncie Google. Potwierdź wynik rzeczywistym tekstem z wyjścia polecenia.
7. Przypomnij o ponownym połączeniu przez `/polacz`.
