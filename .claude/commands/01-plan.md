---
description: Feature planen und PRP erstellen für Adbot
argument-hint: [Feature-Beschreibung in 1-2 Sätzen]
---

# Feature-Planung: PRP erstellen

## Feature

$ARGUMENTS

## Anweisungen

Du erstellst einen vollständigen **PRP (Product Requirements Prompt)** für dieses Feature.
Der PRP muss so detailliert sein, dass ein anderer Claude Code Agent ihn ohne Kontext umsetzen kann.

**⚠️ In dieser Phase wird KEIN Code geschrieben. Nur Analyse und Planung.**

---

## 🔤 SPRACH-REGEL (NICHT VERHANDELBAR)

Der gesamte PRP wird auf **Deutsch** mit **echten Umlauten** geschrieben: `ä ö ü Ä Ö Ü ß` — niemals `ae/oe/ue/ss` als Ersatz.
Einzige Ausnahme: Variablen-, Funktions-, Datei- und Schema-Namen im Code bleiben ASCII.

---

## Phase 1: Kontext laden

1. `CLAUDE.md`, `AGENTS.md` — Repo-Regeln
2. `ads/SKILL.md` — Conductor-Contract
3. **Wiki-Docs** (`docs/wiki/`, falls vorhanden — alle lesen)
4. **PRD**: `docs/PRDs/PRD_Adbot.md`
5. `control-plane/PRODUCT_BOUNDARIES.md` + `control-plane/manifests/capability-manifest.json`
6. **Bestehende PRPs**: `ls docs/PRPs/` — existiert schon ein PRP für dieses Feature?

## Phase 1b: Bestandsaufnahme — Was darf NICHT kaputt gehen?

1. **Welche bestehenden Skills/Adapter/Schemas berührt das Feature?** (gemeinsame Dateien, Contracts, Fixtures)
2. **Welche Manifeste sind betroffen?** (`capability-manifest.json`, `claim-ledger.json`, `source-ledger.json`, `control-registry.json`)
   → Neue Capabilities MÜSSEN im Manifest mit `implementation_paths`, `fixture_paths`, `test_paths` erscheinen.
3. **Gibt es manuelle Schritte?** (Developer-Token, OAuth-Client, MCP-Registrierung, Env-Variablen)
   → Als eigener Schritt mit Done-Kriterien + Verifikations-Befehl im PRP.
4. **Mutationen?** Wenn das Feature Account-Änderungen ermöglicht: Mutation-Gate (Preview → Approval → Apply idempotent → Verify → Audit → Rollback) ist Pflicht, Default bleibt read-only.

Diese Liste kommt in den PRP unter "## Bestehende Funktionen (NICHT anfassen)".

## Phase 2: Codebase-Analyse

### 2a. Ähnliche Implementierungen finden

```bash
ls claude_ads_core/ claude_ads_core/adapters/ claude_ads_core/schemas/v1/
ls skills/ agents/
ls tests/core/ tests/fixtures/
```

Referenz-Patterns: `claude_ads_core/adapters/base.py` (Capability-Protokoll), `native_export.py` (fail-closed Normalisierung), `tests/core/test_adapters.py`.

### 2b. Betroffene Dateien identifizieren

Pro Datei: vollständiger Pfad, relevante Zeilen, bestehende Patterns (Naming, Fehlerbehandlung, Contract-Validierung).

### 2c. Abhängigkeiten prüfen

- Neue Libraries? → `pyproject.toml`, `requirements*.txt` (+ `.lock` mit Hashes!)
- Neue Env-Variablen? → nur Namen dokumentieren, nie Werte
- Neue Schemas? → `claude_ads_core/schemas/v1/` + Fixture + Test
- Neue Plattform-Claims? → `source-ledger.json` + `claim-ledger.json`

## Phase 3: Externe Recherche (bei Bedarf)

Offizielle Doku (Google Ads API, MCP-Server, Meta Marketing API …) per WebFetch/Context7 lesen; Version und Datum notieren, damit die Quelle im Source-Ledger registriert werden kann.

## Phase 4: PRP erstellen

Speichere als: `docs/PRPs/PRP_[Feature_Name].md`

```markdown
# PRP: [Feature Name]

## Status: DRAFT
**Erstellt:** [Datum]
**Priorität:** P0/P1/P2/P3

## Ziel
[2-3 Sätze]

## User Story
Als [Benutzertyp] möchte ich [Aktion] damit [Nutzen]

## Bestehende Funktionen (NICHT anfassen)
[Liste + wie man verifiziert, dass sie nach der Implementierung noch funktionieren]

## Scope
### In Scope
### Out of Scope

## Betroffene Dateien
### Bestehende Dateien (ändern)
| Datei | Änderung | Relevante Zeilen |
### Neue Dateien (erstellen)
| Datei | Zweck |

## Technischer Plan
### Schritt 1: [Name]
**Dateien:** … · **Was:** … · **Pattern-Referenz:** …
**Done-Kriterien:**
- [ ] [Testbare Bedingung]
- [ ] [Validierung: pytest grün / Schema valide]
### Schritt 2 …

## Manifest-/Contract-Änderungen
[capability-manifest, claim-ledger, source-ledger, Schemas — oder "Keine"]

## Sicherheit & Mutationen
[read-only? Wenn Writes: Gate-Schritte, Ceilings, Approver, Rollback]

## Env-Variablen (nur Namen)
[oder "Keine"]

## Testing-Strategie
- Unit Tests: …  · Fixture-Tests: … · Manueller Test: …

## Validierung
```bash
.venv/bin/python -m pytest -q
python3 -m claude_ads_core --version
```

## Risiken & Offene Fragen
```

## Phase 5: Bestätigung

1. ✅ PRP gespeichert, alle Dateien mit Pfaden/Zeilen referenziert
2. ✅ Jeder Schritt hat testbare Done-Kriterien
3. ✅ Manifest-Änderungen und Mutations-Gate berücksichtigt
4. ✅ Keine Secrets, keine absoluten lokalen Pfade
5. ✅ Umlaut-Selbstcheck:

```bash
grep -nE '\b(Aenderung|aendern|fuer|moechte|muessen|Pruefe|waehrend|Schluessel|naechst|moeglich|ueber|Ueber|loeschen|koennen|zurueck|groesser)\b' docs/PRPs/PRP_[Name].md
```

**Zusammenfassung:** PRP-Pfad · Komplexität (Low/Medium/High) · Anzahl Dateien · Hauptrisiken · **Context Reset empfohlen?** (Ja bei ≥5 Schritten — `/02-execute` erzeugt dann `docs/handoffs/HANDOFF_[Name].md`)

**Nächster Schritt:** `/02-execute docs/PRPs/PRP_[Name].md`
