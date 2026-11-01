# 03 · Odłączenie konta Google

> **Wersja robocza:** tekst wymaga sprawdzenia przez osobę, dla której polski jest językiem ojczystym.

**Stan na:** 2026-11-01 · **Czas:** ok. 10 minut · **Kto:** Ty sam(a)
**Źródła:** `ads/references/google-auth-und-zugriff.md`

W każdej chwili możesz odebrać Adbotowi dostęp. Są **trzy poziomy**; poziomy 1 i 2 warto wykonać zawsze.
Twoje konto Google Ads i kampanie pozostają przy tym bez zmian.

## Poziom 1 · Usuń lokalne logowanie

```bash
gcloud auth application-default revoke
```

Polecenie usuwa lokalny plik logowania na Twoim komputerze (według dokumentacji Google). Dokumentacja nie mówi, czy dostęp jest przy tym
cofany także po stronie Google – dlatego potrzebny jest poziom 2.

## Poziom 2 · Cofnij dostęp w Google

1. Otwórz <https://myaccount.google.com/permissions> (zalogowany na swoje konto Google).
2. Znajdź aplikację o nazwie nadanej na ekranie zgody (np. `Adbot`).
3. Wybierz **Usuń dostęp**.

## Poziom 3 (opcjonalnie) · Usuń projekt Cloud

Tylko jeśli nie chcesz już nigdy używać Adbota: konsola Google Cloud → **IAM i administracja** → **Ustawienia** → **Zamknij**.
Konsola pokazuje tam terminy. Potem znika też identyfikator projektu; do ponownego użycia potrzebny jest nowy projekt (instrukcja 02).

## Dane lokalne: zachować czy usunąć?

- **Zachować (zalecane):** raporty i ustawienia pozostają w folderze `.adbot/` i w `~/.config/adbot/standard`. Możesz później połączyć konto ponownie.
- **Usunąć:** usuń oba foldery samodzielnie w menedżerze plików. **Tego nie można cofnąć.** Najpierw zapisz raporty, które jeszcze są Ci potrzebne.

## Sprawdź

```bash
python -m claude_ads_core doctor --lang pl
```

**Tak wygląda „odłączone”:** `✖ Nie znaleziono logowania Google …` a na końcu „Twoje konto Google nie jest połączone.”

Ponowne połączenie: instrukcja 02.
