---
description: Evidenzbasierte UI-/Report-Evaluierung für Adbot (Playwright/Chrome MCP) — separater Evaluator
argument-hint: [URL, lokaler Pfad einer HTML-/PDF-Ausgabe oder Dashboard-Route]
---

# UI-Evaluierung: Adbot — Evidenzbasierter Evaluator

⚠️ **In einem SEPARATEN Chat ausführen.** Selbstbewertung von UI ist unzuverlässig.

Gilt für: gerenderte Reports (`claude_ads_core/reporting.py`, HTML/PDF), das Dashboard (sobald es existiert), Artifacts.

## Kalibrierung
- Jeder Score braucht Belege (Screenshot, Console, Accessibility-Tree) — keine Meinungen
- Unangepasste Framework-Defaults = „AI Slop" → ≤ 4/10
- Fehlende States (Loading/Error/Empty/No-Data) = unfertig
- Reports: Missing Data, Kontradiktionen, Evidence Coverage müssen SICHTBAR sein (Produkt-Grundsatz)

## 0. Kontext
`docs/BRANDING.md` (falls vorhanden), `docs/wiki/` (Frontend/Reporting), PRP-Done-Kriterien.
Ziel: `$ARGUMENTS` (Datei → im Browser öffnen via `file://`; Route → Basis-URL aus Wiki).

## Layer 1: Datenintegrität (Report-spezifisch)
- Stimmen Zahlen mit dem JSON-Run-Bundle überein? (`claude_ads_core` Validierung)
- Werden Missing Inputs, Contradictions, Unscored Opportunities angezeigt?
- Keine Health-Scores für disabled Profile (fail-closed)?

## Layer 2: Component Audit (Shadcn/MagicUI MCP — nur bei Web-Frontend)
3-5 Kernkomponenten vs. Defaults; Brand-Anpassung, Dark-Mode, Animations-Zweck.

## Layer 3: Visual & UX (Playwright/Chrome MCP)
- Desktop 1440×900 (light/dark), Mobile 375/393/360, Tablet 768 — Screenshots
- Checkliste: kein horizontaler Scroll, Touch-Targets ≥ 44px, Basis-Font ≥ 16px, Tabellen scrollen, Modals passen
- Console-Errors, fehlgeschlagene/langsame Requests
- Interaktion: primäre Aktion sofort verständlich? Accessibility (aria, Keyboard)?

## Bewertung
Design Quality 30% · Originality 25% · Craft 20% · Functionality 25% — jeder Punkt mit Layer-Referenz.

## Output
```
🎨 UI-Evaluierung: [Ziel]
Datenintegrität ✅/❌ · Components X/5 · Desktop ✅/❌ · Dark ✅/❌ · Mobile 375/393/360/768 ✅/❌
Console-Fehler X · Requests fehlgeschlagen X
Design X/10 · Originality X/10 · Craft X/10 · Functionality X/10 → Gesamt X.X/10
```
Priorisierte Issue-Liste `[CRITICAL/HIGH/MEDIUM/LOW]` mit Quelle + Fix.

**Nächster Schritt:** ≥7 → `/05-commit` · <7 → Issues als Input für `/02-execute` (neuer Chat)
