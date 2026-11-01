---
description: Alle noqa/type:ignore/pragma-Kommentare finden, begründen und Auflösung empfehlen
---

Finde alle `noqa`, `type: ignore`, `pragma: no cover` und ähnliche Unterdrückungen in `claude_ads_core/`, `scripts/`, `tests/`, untersuche warum sie existieren und gib Empfehlungen.

Erstelle den Report: `.agents/reports/ignore-comments-report-{YYYY-MM-DD}.md` (Verzeichnis anlegen, ist nicht getrackt).

Pro Kommentar:

**Warum es existiert:** {Erklärung}

**Optionen:**
1. {Option} — Effort: Low/Medium/High · Breaking: Ja/Nein · Impact: …
2. {Option} — …

**Tradeoffs:** …

**Empfehlung:** {Remove | Keep | Refactor} — {Begründung}
