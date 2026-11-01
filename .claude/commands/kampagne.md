---
description: Erste Kampagne planen und als pausierten Entwurf (Google Ads Editor) erstellen / Zaplanuj pierwszą kampanię i przygotuj wstrzymany szkic
---

# Kampagne

Sprache: Antworte in der Sprache aus den Einstellungen (`python -m claude_ads_core settings show`, Feld `language`: `de` oder `pl`).
Gibt es keine Einstellungen, frage einmal nach der Sprache und lege sie mit `python -m claude_ads_core settings init --lang <de|pl>` an.
Nutze das Glossar (`claude_ads_core.i18n.glossary()`) für Fachbegriffe und erkläre jeden beim ersten Auftreten kurz.

Lies die Karte „Campaign“ in `ads/references/prozesskarten.md`, `docs/runbooks/editor-csv-import.md` und die Skills `ads-plan`, `ads-budget`, `ads-keywords`, `ads-copy`.

1. **Briefing-Tor:** Ziel, Tagesbudget mit Währung, Region/Umkreis, Conversion-Definition, Angebot und Website erfragen und **von der Nutzerin bestätigen lassen**. Danach `claude_ads_core.briefing.validate_briefing` aufrufen; ohne Bestätigung kein Entwurf.
2. Plan mit Szenarien statt Versprechen; Budget-Wirkung in Euro bzw. Złoty nennen. Keine Garantien.
3. Keywords nach Suchabsicht, Anzeigen mit geprüften Zeichenlimits, Negative **nur** mit Suchbegriffsbericht und Overblocking-Prüfung.
4. Entwurf mit `claude_ads_core.editor_export` erzeugen (`briefing_to_campaign` → `write_editor_csv`). Alle Kampagnen **pausiert**.
5. Zusammenfassung in einfacher Sprache: was wurde vorbereitet, was kostet es höchstens pro Tag, was muss vor dem Veröffentlichen geprüft werden. Import und Veröffentlichung macht die Nutzerin (`docs/<sprache>/05-first-campaign.md`).

Nichts wird durch Adbot im Konto veröffentlicht.
