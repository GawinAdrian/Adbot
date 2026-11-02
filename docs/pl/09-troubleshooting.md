# 09 · Rozwiązywanie problemów i częste pytania

> **Wersja robocza:** tekst wymaga sprawdzenia przez osobę, dla której polski jest językiem ojczystym.

**Stan na:** 2026-11-01

Najpierw zawsze: `python -m claude_ads_core doctor --lang pl --online`

## Komunikaty `doctor`

| Komunikat | Znaczenie | Co zrobić |
|---|---|---|
| Python … jest zbyt stary | wersja poniżej 3.11 | zainstaluj nowszą (instrukcja 01) |
| Brakuje narzędzia uv / narzędzia Google Cloud | uwaga, nie krytyczne | zainstaluj, gdy chcesz bezpośrednio pobierać dane lub łączyć konto |
| Nie znaleziono prawidłowych ustawień | `/zacznij` jeszcze nie był uruchomiony | `/zacznij` lub `python -m claude_ads_core settings init --lang pl` |
| Identyfikator projektu nie jest ustawiony | brak pliku `env` w profilu | instrukcja 02, krok 6 |
| Nie znaleziono logowania Google | konto nie jest połączone | instrukcja 02, krok 5 |
| Plik logowania nieczytelny/niekompletny | uszkodzony | odłącz (03), potem połącz ponownie (02) |
| Logowanie wygasło lub zostało cofnięte | np. zasada 7 dni w trybie testowym | powtórz instrukcję 02, krok 5 |
| Brak uprawnień do konta | złe konto Google lub ustawiony identyfikator konta menedżera, mimo że masz dostęp bezpośredni | zaloguj się kontem będącym właścicielem konta Ads; identyfikator konta menedżera ustawiaj tylko przy dostępie przez konto menedżera |
| Szyfrowanie dysku niepotwierdzone | uwaga | instrukcja 01 |

## Inne komunikaty

| Komunikat | Znaczenie | Co zrobić |
|---|---|---|
| „explorer access” / „not allowed for use with explorer access” | pomysły na słowa kluczowe przez interfejs wymagają dostępu „Basic” | poproś o Basic dla projektu Cloud lub użyj pliku CSV z Planera słów kluczowych |
| „returned no rows” | brak danych w okresie | sprawdź okres; **nie** czytaj tego jako „0 zł wydatków” |
| Kokpit pokazuje szary | za mało danych | poczekaj; potrzeba więcej kliknięć |

## Częste pytania

**Czy Adbot kosztuje?** Sam Adbot jest wolnym oprogramowaniem (licencja MIT). Koszty to Twój dostęp do Claude oraz oczywiście Twoja reklama w Google.

**Czy Adbot może sam opublikować kampanię?** Nie, nie w tej wersji. Importujesz szkic i publikujesz sam(a) (instrukcja 05).

**Jak często Adbot zagląda na konto?** Codziennie strażnik (bez AI), co tydzień interpretacja (gdy uruchomisz `/raport`), co miesiąc analiza pogłębiona. Szczegóły: `ads/references/kadenz-und-regeln.md`.

**Dlaczego Adbot czasem nic nie zaleca?** Przy małej liczbie kliknięć liczby to przypadek. „Poczekać” jest wtedy uczciwą odpowiedzią.

**Mam kilka kont.** Jeden profil na użytkowniczkę; aktywne konto wybierasz poleceniem `settings set --account`.
