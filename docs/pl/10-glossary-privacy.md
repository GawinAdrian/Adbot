# 10 · Słowniczek i ochrona danych

> **Wersja robocza:** tekst wymaga sprawdzenia przez osobę, dla której polski jest językiem ojczystym.

**Stan na:** 2026-11-01

## Ochrona danych prostymi słowami

**Gdzie są Twoje dane?** Raporty, ustawienia i wyniki leżą jako pliki **na Twoim komputerze** (`.adbot/` w folderze Adbota oraz `~/.config/adbot/standard`). Nie ma ich w repozytorium.

**Dokąd trafiają dane?**
- Do **Google**: Adbot odczytuje Twoje konto przez interfejs Google (tylko do odczytu).
- Do **Claude (Anthropic)**: wszystko, co pojawi się w rozmowie (np. liczby z raportu, który pokażesz Claude), jest tam przetwarzane. Pokazuj Claude tylko to, co chcesz pokazać.
- **Nie** do osób trzecich przez kokpit: strona jest plikiem lokalnym bez dostępu do sieci.

**Czego nigdy się nie zapisuje:** hasła, klucze i pliki logowania nie trafiają do raportów ani do repozytorium. W profilu jest najwyżej identyfikator projektu.

**Konta innych osób:** jeśli obsługujesz konto klienta lub członka rodziny, przed użyciem wyjaśnij z wykwalifikowaną osobą, czy potrzebna jest umowa powierzenia przetwarzania danych. To **nie jest porada prawna**.

**Usuwanie:** odłącz konto (instrukcja 03) i usuń foldery. Usunięcia nie można cofnąć.

## Słowniczek

| Pojęcie | Niemiecki | Wyjaśnienie |
|---|---|---|
| **Kampania** | Kampagne | Najwyższy poziom w koncie: określa budżet, cel, region i harmonogram. |
| **Grupa reklam** | Anzeigengruppe | Łączy reklamy i słowa kluczowe jednego tematu w ramach kampanii. |
| **Słowo kluczowe** | Keyword | Fraza, przy której reklama ma się wyświetlać. |
| **Wykluczające słowo kluczowe** | Ausschließendes Keyword | Fraza, przy której reklama nie ma się wyświetlać. Ustawiaj tylko na podstawie raportu wyszukiwanych haseł. |
| **Typ dopasowania** | Keyword-Option | Określa, jak dokładnie wyszukiwanie ma pasować do słowa kluczowego (ścisłe, do wyrażenia, przybliżone). |
| **Elastyczna reklama w wyszukiwarce** | Responsive Suchanzeige | Reklama złożona z wielu nagłówków i opisów; Google łączy je automatycznie. |
| **Nagłówek** | Anzeigentitel | Pogrubiona pierwsza linia reklamy. |
| **Opis** | Beschreibung | Tekst objaśniający reklamy. |
| **Wyświetlenie** | Impression | Reklama została wyświetlona jeden raz. |
| **Kliknięcie** | Klick | Ktoś kliknął reklamę. |
| **Współczynnik klikalności (CTR)** | Klickrate (CTR) | Kliknięcia podzielone przez wyświetlenia, w procentach. |
| **Koszt kliknięcia (CPC)** | Kosten pro Klick (CPC) | Średnia cena jednego kliknięcia. |
| **Konwersja** | Conversion | Pożądane działanie, np. telefon, formularz lub zakup. |
| **Współczynnik konwersji** | Conversion-Rate | Odsetek kliknięć, które kończą się konwersją. |
| **Koszt konwersji (CPA)** | Kosten pro Conversion (CPA) | Koszt podzielony przez konwersje: ile kosztuje jedno zapytanie lub zakup. |
| **Zwrot z wydatków na reklamę (ROAS)** | Werbekostenrentabilität (ROAS) | Przychód podzielony przez koszty reklamy. |
| **Budżet dzienny** | Tagesbudget | Średnia kwota, jaką kampania może wydać dziennie. |
| **Strategia ustalania stawek** | Gebotsstrategie | Określa, jak Google licytuje w Twoim imieniu (np. maksymalizacja kliknięć, docelowy CPA). |
| **Wskaźnik jakości** | Qualitätsfaktor | Szacunkowa ocena Google dotycząca jakości słowa kluczowego, reklamy i strony docelowej. |
| **Wyszukiwane hasło** | Suchbegriff | Co użytkownicy faktycznie wpisali w Google. |
| **Strona docelowa** | Zielseite | Strona, na którą użytkownik trafia po kliknięciu. |
| **Zasób** | Asset | Dodatkowy element reklamy, np. połączenie, link do podstrony lub obraz. |
| **Udział w wyświetleniach** | Anteil an möglichen Impressionen | Jak często reklama się wyświetliła w porównaniu z tym, co było możliwe. |
| **Faza uczenia się** | Lernphase | Okres po większych zmianach, w którym system się uczy; wyniki wahają się. |
| **Remarketing** | Remarketing | Reklamy dla osób, które już odwiedziły Twoją stronę. |
| **Kierowanie na lokalizację** | Standort-Targeting | Region lub promień, w którym reklama się wyświetla. |
| **Kierowanie na język** | Sprach-Targeting | Język użytkowników, do których reklama ma docierać. |
| **Harmonogram reklam** | Anzeigenplaner | Dni tygodnia i godziny, w których reklamy są wyświetlane. |
| **Śledzenie konwersji** | Conversion-Tracking | Pomiar tego, które kliknięcia prowadzą do zapytania lub zakupu. |
| **Ostateczny adres URL** | Finale URL | Adres strony, do której prowadzi reklama. |
| **Konto menedżera (MCC)** | Verwaltungskonto (MCC) | Konto zarządzające wieloma kontami Google Ads. |
