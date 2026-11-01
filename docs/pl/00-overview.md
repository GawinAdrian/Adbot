# 00 · Przegląd: co robi Adbot, a czego nie robi

> **Wersja robocza:** tekst wymaga sprawdzenia przez osobę, dla której polski jest językiem ojczystym.

**Stan na:** 2026-11-01 · Wszystkie instrukcje są po niemiecku (`docs/de`) i po polsku (`docs/pl`) pod tymi samymi nazwami plików.

## Czym jest Adbot

Adbot pomaga zrozumieć i zbudować **Twoją własną reklamę w Google**. Piszesz zwykłym językiem polskim lub niemieckim, Adbot odczytuje dane Twojego konta Google Ads,
analizuje je i przygotowuje propozycje.

| Chcesz … | Polecenie | Instrukcja |
|---|---|---|
| wszystko skonfigurować | `/start` | 01, 02 |
| połączyć / odłączyć konto Google | `/verbinden`, `/trennen` | 02, 03 |
| sprawdzić, jak stoją reklamy | `/analyse` | 04 |
| przygotować pierwszą kampanię | `/kampagne` | 05 |
| zobaczyć raport tygodniowy i przegląd | `/bericht` | 06 |
| dostać propozycje usprawnień | `/optimieren` | 07 |
| uruchomić codzienną kontrolę automatycznie | – | 08 |
| zajrzeć, gdy coś nie działa | `/hilfe` | 09, 10 |

(Nazwy poleceń są niemieckie, ale rozmowa toczy się w języku z Twoich ustawień.)

## Trzy zasady bezpieczeństwa

1. **Dane logowania wpisujesz Ty sam(a).** Haseł, kluczy i plików logowania nigdy nie wysyłasz na czat.
2. **Nic się nie zmienia bez Twojego wyraźnego „tak”.** W tej wersji Adbot tworzy kampanie tylko jako **wstrzymany szkic**. Import i publikację wykonujesz Ty.
3. **Nic nie jest usuwane.** Adbot wstrzymuje, archiwizuje lub tworzy kopię; trwałe usuwanie odrzuca.

## Czego Adbot nie robi

- Nie gwarantuje wyników (żadnych „50 zapytań miesięcznie”). Liczby to scenariusze z jawnymi założeniami.
- Nie udziela porad prawnych. Pytania o impressum, ochronę danych czy zgody wyjaśniasz z wykwalifikowaną osobą.
- Sam nie zmienia konta. Zapis przez interfejs jest w tej wersji wyłączony.
- Nie wystawia „oceny kondycji” konta. Wskazuje najwyżej trzy priorytety z uzasadnieniem.

## Jak to współpracuje

**Liczby** pochodzą ze skryptu (codziennie, bez AI, bez kosztów). **Interpretacja i propozycje** pochodzą z AI, gdy uruchomisz `/bericht` lub `/analyse`.
Wszystko trafia jako pliki do folderu `.adbot/` na Twoim komputerze.
