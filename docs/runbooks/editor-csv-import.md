# Runbook: Kampagnen-Entwurf als Google-Ads-Editor-CSV importieren

**Stand:** 2026-08-27 · **Quelle der Spalten:** `google-ads-editor-csv-columns-official`

`claude_ads_core.editor_export` schreibt einen freigegebenen Entwurf (Kampagne, Anzeigengruppen,
Keywords, Responsive Search Ads) als Import-CSV. Es ist ein **Draft-Write**: keine API, kein Konto wird
berührt. Jede Kampagne wird `Paused` exportiert.

## Ablauf

1. Creative-Brief und Media-Plan sind vom Operator freigegeben (`human_review: approved`).
2. CSV erzeugen (Beispiel):
   ```python
   from claude_ads_core.editor_export import EditorCampaign, EditorAdGroup, EditorKeyword, EditorResponsiveSearchAd, write_editor_csv
   write_editor_csv([campaign], ".claude-ads/tenants/<tenant>/runs/<run>/google-editor-draft.csv")
   ```
3. Google Ads Editor → Konto herunterladen → *Konto → Importieren → Aus Datei* → CSV wählen.
4. Vorschau prüfen: Spaltenzuordnung, Standorte (der Editor fragt ggf. nach der Zuordnung von
   „Location“-Texten zu Ziel-IDs), Sprachen, Gebotsstrategie.
5. Änderungen im Editor prüfen, **noch nicht posten**. Erst nach Freigabe des Operators posten.
6. Kampagne bleibt pausiert; Aktivierung erfolgt bewusst im Konto nach Tracking-Check.

## Negativ-Keywords (Kampagnenebene)

`EditorCampaign.negative_keywords` nimmt `EditorNegativeKeyword(text, match_type, evidence_ref)` an. Ohne
`evidence_ref` (Suchbegriffsbericht, Formular-Review …) bricht der Writer ab – Boundary aus `skills/ads-google`.
Zeilen erhalten `Match type = Campaign negative` (Quelle `google-ads-editor-csv-columns-official`, CLM-0212);
die Match-Form steckt in der Keyword-Notation: `wort` (weitgehend), `"wort"` (passend), `[wort]` (genau).
Beim Import die Vorschau prüfen: Der Editor muss die Zeilen als Kampagnen-Negatives erkennen.

## Bewusste Grenzen

- Negatives nur mit Evidenz; Anzeigengruppen-Negatives werden nicht erzeugt.
- Keine Anzeigenerweiterungen/Assets, keine Zielgruppen, keine Conversion-Aktionen – Folgeschritte im Konto.
- Zeichenlimits für Headlines/Descriptions werden nicht hier, sondern gegen die aktuelle Spezifikation
  (`ads/references/google-creative-specs.md`, Source-ID) geprüft.
