# 02 · Połączenie konta Google

> **Wersja robocza:** tekst wymaga sprawdzenia przez osobę, dla której polski jest językiem ojczystym.

**Stan na:** 2026-11-01 · **Czas:** ok. 30–45 minut, jednorazowo · **Kto:** najlepiej razem z osobą znającą się na IT
**Źródła:** `ads/references/google-auth-und-zugriff.md` (dokumentacja Google z 29/30.10.2026)

## O co chodzi

Adbot odczytuje dane Twojego konta Google Ads, aby móc je analizować i planować. W tym celu potrzebuje logowania, którego
udzielasz **Ty sam(a)** w Google. Każda użytkowniczka ma **własny projekt Google Cloud** i **własne konto Google**; nie ma wspólnego dostępu.

**Dwie zasady bezpieczeństwa:**
1. Hasła, klucze i pliki logowania wpisujesz **Ty**. Nigdy nie wysyłaj ich na czat ani do Claude.
2. Adbot niczego nie zmienia na Twoim koncie, dopóki wyraźnie się na to nie zgodzisz. Logowanie służy tylko do **odczytu**.

**Tokenu programisty (developer token) już nie potrzebujesz:** Google zlikwidował je 9 września 2026 r.

> **Uwaga:** Nazwy w konsoli Google czasem się zmieniają. Jeśli pozycja menu nazywa się inaczej, wybierz tę o podobnym znaczeniu. Zrzuty ekranu zostaną dodane.

## Krok 1 · Utwórz projekt Google Cloud

1. Otwórz <https://console.cloud.google.com> i zaloguj się kontem Google, którego używasz też w Google Ads.
2. U góry kliknij wybór projektu → **Nowy projekt** → nazwa np. `adbot-mojafirma` → **Utwórz**.
3. Zapisz **identyfikator projektu** (jest pod nazwą; wygląda np. tak: `adbot-mojafirma-123456`).

**Tak poznasz, że się udało:** u góry konsoli widać nazwę projektu.

## Krok 2 · Włącz Google Ads API

1. Menu → **Interfejsy API i usługi** → **Biblioteka**.
2. Wyszukaj **Google Ads API** → kliknij → **Włącz**.

**Udało się:** strona pokazuje, że interfejs API jest włączony.

## Krok 3 · Skonfiguruj ekran zgody

1. **Interfejsy API i usługi** → **Ekran zgody OAuth**.
2. Wybierz typ użytkownika **Zewnętrzny** (dla kont prywatnych) → nazwa aplikacji np. `Adbot`, Twój adres e-mail jako adres pomocy i kontaktowy.
3. W **zakresach (scopes)** dodaj: `https://www.googleapis.com/auth/adwords`
4. W **użytkownikach testowych** wpisz własne konto Google.

**Ważne – zasada 7 dni:** Dopóki ekran ma status **„Testing”**, logowanie wygasa po **7 dniach** (informacja Google). Wtedy raz w tygodniu trzeba zalogować się
ponownie (powtórz krok 5). Można przełączyć na **„In production”**, ale według Google może to wymagać weryfikacji aplikacji.
Na początek wystarczy „Testing”.

**Warto wiedzieć:** Zakres `adwords` z punktu widzenia Google pozwala także zmieniać konto; na przeczytanych stronach Google nie wymieniono zakresu wyłącznie do odczytu. To, że Adbot tylko odczytuje, zapewnia sam Adbot (brak wywołań zapisu w kodzie, zabezpieczone testami) – nie samo logowanie.

## Krok 4 · Utwórz klienta OAuth (aplikacja komputerowa)

1. **Interfejsy API i usługi** → **Dane logowania** → **Utwórz dane logowania** → **Identyfikator klienta OAuth**.
2. Typ aplikacji **Aplikacja komputerowa** (Desktop app), nazwa `Adbot Desktop` → **Utwórz**.
3. **Pobierz plik JSON** i zapisz jako:
   - Mac: `~/.config/google-ads/client.json`
   - Windows: `%USERPROFILE%\.config\google-ads\client.json`

   Folder `.config` może wymagać wcześniejszego utworzenia. Ten plik jest tajny i **nie** należy go umieszczać w repozytorium.

**Udało się:** plik `client.json` leży w podanym miejscu.

## Krok 5 · Zaloguj się

Najpierw zainstaluj narzędzie wiersza poleceń Google Cloud (patrz instrukcja 01). Następnie w terminalu:

```bash
gcloud auth application-default login \
  --scopes https://www.googleapis.com/auth/adwords,https://www.googleapis.com/auth/cloud-platform \
  --client-id-file="$HOME/.config/google-ads/client.json"
```

W systemie Windows (PowerShell): `--client-id-file="$env:USERPROFILE\.config\google-ads\client.json"`

Otworzy się okno przeglądarki: wybierz konto, zezwól na dostęp. Plik logowania zostanie zapisany w folderze Google Cloud
(`application_default_credentials.json`).

**Udało się:** w terminalu pojawia się informacja, że dane uwierzytelniające zostały zapisane.

## Krok 6 · Utwórz profil

```bash
mkdir -p ~/.config/adbot/standard
printf 'GOOGLE_PROJECT_ID=TWOJ-IDENTYFIKATOR-PROJEKTU\n' > ~/.config/adbot/standard/env
python -m claude_ads_core settings init --lang pl
```

Zastąp `TWOJ-IDENTYFIKATOR-PROJEKTU` identyfikatorem z kroku 1. (Windows: utwórz folder `%USERPROFILE%\.config\adbot\standard`, a w nim plik `env` w edytorze tekstu.)
Konto wybierzesz potem w poleceniu `/start`.

## Krok 7 · Sprawdź

```bash
python -m claude_ads_core doctor --lang pl --online
```

**Tak wygląda „wszystko dobrze”:** wszystkie wiersze mają `✔`, na końcu jest „Twoje konto Google jest połączone.”, a przy kontroli online „Google Ads jest dostępny i odpowiada.”

## Gdy coś nie działa

| Komunikat | Znaczenie | Co zrobić |
|---|---|---|
| „Nie znaleziono logowania Google” | brak kroku 5 lub plik został usunięty | powtórz krok 5 |
| „Logowanie Google wygasło lub zostało cofnięte” | np. zasada 7 dni | powtórz krok 5 |
| „To logowanie nie ma uprawnień do wybranego konta” | złe konto Google | zaloguj się kontem, które jest właścicielem konta Ads |
| „Identyfikator projektu Google Cloud nie jest ustawiony” | brak kroku 6 | sprawdź plik `env` |
| Komunikat o poziomie dostępu (np. „explorer access”) | funkcja wymaga dostępu „Basic”, np. pomysły na słowa kluczowe przez API | odczyt danych konta działa i tak; dla pomysłów na słowa kluczowe zobacz instrukcję 04 (droga przez CSV) |

Więcej w rozwiązywaniu problemów (instrukcja 09). Odłączanie opisuje instrukcja 03.
