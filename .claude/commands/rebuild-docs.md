---
description: Wiki-Dokumentation (docs/wiki/) vollständig neu aufbauen oder auditieren — nach großen Änderungen, langen Pausen oder beim ersten Aufbau
---

# Task: Full Documentation Rebuild

`docs/wiki/` ist entweder leer (Erstaufbau) oder stark veraltet. Vollständiges Audit und Neuschreiben wo nötig.

## Schritt 1: Ist-Zustand

1. Alle vorhandenen Wiki-Docs lesen, `last_updated` notieren
2. `git log --oneline --since="<ältestes last_updated>" -- ':!docs/' ':!*.md'` (bei Erstaufbau: gesamte History überfliegen)
3. Für jedes Modul den aktuellen Code lesen: `ads/`, `skills/*/SKILL.md`, `agents/`, `claude_ads_core/` (inkl. `adapters/`, `schemas/v1/`), `control-plane/` (README, Boundaries, Manifeste), `scripts/`, `tests/`, `evals/`, `.claude/commands/`
4. Vergleichen: Was sagen Docs vs. was tut der Code

## Schritt 2: Lücken

Neue/entfernte Skills, Adapter, Schemas; geänderte Capability-Status; neue Env-Var-Namen; neue externe Anbindungen (MCP-Server); geänderte Architektur.

## Schritt 3: Docs schreiben / neu schreiben

Nummerierungsschema (beim Erstaufbau anlegen):

| Datei | Inhalt |
|-------|--------|
| `01_overview.md` | Produkt, Mission (planen/erstellen/überwachen/optimieren), Features, Tech Stack, Repo-Struktur |
| `02_architecture.md` | Conductor/Worker-Modell, Datenfluss Export/MCP → Normalisierung → Scoring → Report, Mutation-Gate |
| `03_skills.md` | `/ads` Orchestrator + alle `skills/` mit Zweck und Referenzen |
| `04_core.md` | `claude_ads_core`: Schemas, Adapter, Scoring, Reporting, CLI |
| `05_control_plane.md` | Manifeste, Ledger, Boundaries, Release-Gates, Safety-Policy |
| `06_platforms.md` | Capability-Matrix pro Plattform (aus Manifest generiert), Anbindungswege |
| `07_integrations.md` | Externe Services: Google Ads MCP, weitere APIs, Env-Var-Namen, Access-Level |
| `08_tenants.md` | Mandanten/Konten (nur IDs + Anbindungsart, keine Secrets) |
| `09_development.md` | Dev-Setup, Tests, Commands (`.claude/commands/`), Workflow PRD → PRP → Execute |
| `10_operations.md` | Monitoring-/Optimierungs-Betrieb, Freigaben, Rollback, Audit-Records |

Frontmatter pro Datei:
```yaml
---
last_updated: YYYY-MM-DD
covers: [pfad/1, pfad/2]
---
```
Struktur: Frontmatter → Kurzfassung → Inhalt → `## Update-Hinweise` (was beim Ändern dieses Bereichs zu aktualisieren ist).

## Schritt 4: Fehlende Docs
Neue große Komponente → neues `docs/wiki/XX_name.md` mit gleicher Struktur.

## Schritt 5: Genauigkeit verifizieren
Kritische Fakten (Counts, Schema-Versionen, Env-Var-Namen, Konto-IDs) gegen Code/Manifeste prüfen; Unsicheres mit `> ⚠️ Bitte verifizieren:` markieren.

## Regeln
- Code VOR dem Schreiben lesen — Genauigkeit vor Geschwindigkeit
- Keine Secrets, keine Kundendaten, keine absoluten lokalen Pfade
- Counts aus Manifesten ableiten (`capability-manifest.json`, `product-manifest.json`)
- Nummerierung beibehalten, `Update-Hinweise` erhalten
