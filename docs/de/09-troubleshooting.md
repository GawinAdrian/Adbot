# 09 · Fehlerbehebung und häufige Fragen

**Stand:** 2026-11-01

Zuerst immer: `python -m claude_ads_core doctor --lang de --online`

## Meldungen von `doctor`

| Meldung | Bedeutung | Was tun |
|---|---|---|
| Python … ist zu alt | Version unter 3.11 | Neuere Version installieren (Anleitung 01) |
| Werkzeug uv / Google-Cloud-Werkzeug fehlt | Hinweis, nicht kritisch | Installieren, wenn du direkt Daten abrufen bzw. dich verbinden willst |
| Keine gültigen Einstellungen | `/start` noch nicht gelaufen | `/start` oder `python -m claude_ads_core settings init --lang de` |
| Google-Cloud-Projekt-ID nicht eingetragen | Datei `env` im Profil fehlt | Anleitung 02, Schritt 6 |
| Keine Google-Anmeldung gefunden | nicht verbunden | Anleitung 02, Schritt 5 |
| Anmeldedatei nicht lesbar/unvollständig | beschädigt | Trennen (03), dann neu verbinden (02) |
| Anmeldung abgelaufen oder widerrufen | z. B. 7-Tage-Regel im Testmodus | Anleitung 02, Schritt 5 wiederholen |
| Keine Berechtigung für das Konto | falsches Google-Konto, oder eine Verwaltungskonto-ID ist gesetzt, obwohl du direkten Zugriff hast | Mit dem Konto anmelden, dem das Ads-Konto gehört; die Verwaltungskonto-ID nur bei Zugriff über ein Verwaltungskonto setzen |
| Festplattenverschlüsselung nicht bestätigt | Hinweis | Anleitung 01 |

## Weitere Meldungen

| Meldung | Bedeutung | Was tun |
|---|---|---|
| „explorer access“ / „not allowed for use with explorer access“ | Keyword-Ideen per Schnittstelle brauchen „Basic“-Zugriff | Basic für dein Cloud-Projekt beantragen oder Keyword-Planner-CSV nutzen |
| „returned no rows“ | keine Daten im Zeitraum | Zeitraum prüfen; **nicht** als „0 € Ausgaben“ lesen |
| Cockpit zeigt Grau | zu wenig Daten | abwarten; mehr Klicks nötig |

## Häufige Fragen

**Kostet Adbot etwas?** Adbot selbst ist freie Software (MIT-Lizenz). Kosten entstehen für deinen Claude-Zugang und natürlich für deine Werbung bei Google.

**Kann Adbot meine Kampagne selbst veröffentlichen?** Nein, nicht in dieser Version. Du importierst den Entwurf und veröffentlichst selbst (Anleitung 05).

**Wie oft schaut Adbot aufs Konto?** Täglich der Wächter (ohne KI), wöchentlich die Deutung (wenn du `/bericht` startest), monatlich die Tiefenanalyse. Details: `ads/references/kadenz-und-regeln.md`.

**Warum empfiehlt Adbot manchmal nichts?** Bei wenigen Klicks sind Zahlen Zufall. „Abwarten“ ist dann die ehrliche Antwort.

**Ich habe mehrere Konten.** Pro Nutzerin ein Profil; das aktive Konto wählst du mit `settings set --account`.
