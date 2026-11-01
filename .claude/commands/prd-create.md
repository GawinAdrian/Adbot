---
description: PRD (Product Requirements Document) für Adbot von Grund auf erstellen — das strategische Gesamtbild
argument-hint: [optional: Fokus/Vision in 1-2 Sätzen, z.B. "Selbstbedienungs-Ads-Assistent für kleine Unternehmen in DE und PL"]
---

# PRD erstellen: Adbot

## Fokus

$ARGUMENTS

## Anweisungen

Du erstellst ein vollständiges **PRD (Product Requirements Document)** für **Adbot**.
Das PRD ist das zentrale Wahrheitsdokument — es beschreibt WAS gebaut wird, WARUM und in welchem ZUSTAND es ist.

**⚠️ In dieser Phase wird KEIN Code geschrieben. Nur Analyse, Recherche und Dokumentation.**

**Unterschied PRP vs. PRD:**
- **PRP** = Product Requirements Prompt — Plan für EIN Feature (taktisch, für Claude Code)
- **PRD** = Product Requirements Document — Gesamtbild des PRODUKTS (strategisch, für Menschen + AI)

## 🔤 Sprach-Regel

Das PRD wird auf **Deutsch** mit echten Umlauten (`ä ö ü ß`) geschrieben. Code-Bezeichner bleiben ASCII.

---

## Phase 1: Bestandsaufnahme

### 1a. Codebase verstehen

```bash
ls -1
git log --oneline -20
cat pyproject.toml
python3 -c "import json;d=json.load(open('control-plane/manifests/capability-manifest.json'));[print(p['platform'],[(c['id'],c['mode'],c['status']) for c in p['capabilities']]) for p in d['platforms']]"
```

Lies: `CLAUDE.md`, `AGENTS.md`, `README.md`, `ads/SKILL.md`, `control-plane/README.md`,
`control-plane/PRODUCT_BOUNDARIES.md`, `control-plane/RELEASE_REQUIREMENTS.md`,
`ls skills/ agents/ claude_ads_core/ claude_ads_core/adapters/`.

Identifiziere ehrlich:
- Was existiert **wirklich** (Code + Fixtures + Tests) vs. was nur als Skill-Text beschrieben ist
- Capability-Modi pro Plattform (`export-read` / `live-read` / `draft-write` / `live-write`) und Status
- Was die Upstream-Basis (claude-ads) bewusst NICHT verspricht (`PRODUCT_BOUNDARIES.md`)

### 1b. Wiki/Docs als Wahrheitsquelle

```bash
ls docs/wiki/ 2>/dev/null && echo "Wiki vorhanden — als primäre Quelle nutzen"
ls docs/PRPs/ docs/PRDs/ 2>/dev/null
```

### 1c. Externer Kontext (Adbot-spezifisch)

- Google Ads: eigenes Konto je Nutzerin (eigenes Google-Cloud-Projekt, kein gemeinsamer OAuth-Client); optional Zugriff über ein Verwaltungskonto
- Anbindungsweg: offizieller Google Ads MCP (read-only, GAQL). Schreibzugriff = eigener, gegateter Pfad
- Prüfe mit WebSearch bei Bedarf: aktuelle Google Ads API Version, MCP-Server-Stand, Access-Level

---

## Phase 2: User-Interview (kurz, groß denken)

Frage gezielt — **maximal 3-5 Fragen**, nutze AskUserQuestion:

1. **Mandanten & Ziel:** Nur eigene Konten der Nutzerin oder auch Konten Dritter (Agentur-Betrieb)?
2. **Plattform-Reihenfolge:** Google zuerst — dann Meta? Welche Plattformen in 12 Monaten?
3. **Autonomie-Grad:** Nur Vorschläge, Vorschläge mit 1-Klick-Freigabe, oder autonome Änderungen innerhalb von Leitplanken?
4. **Oberfläche:** Nur Claude Code / CLI, oder Dashboard (Web-App), Reports per Mail, Slack?
5. **Monetarisierung/Reichweite:** Internes Tool, Produkt, Open Source?

---

## Phase 3: PRD schreiben

Speichere als: `docs/PRDs/PRD_Adbot.md`

### PRD-Template

```markdown
# Product Requirements Document: Adbot
## [Untertitel — eine Zeile]

**Version:** 1.0
**Erstellt:** [Datum]
**Letzte Aktualisierung:** [Datum]
**Autor:** [Name/Team]
**Status:** [Early Development / Beta / Production]

---

## Executive Summary
[2-3 Sätze: Was ist das Produkt, für wen, warum?]

### Vision (12 Monate)
[Das große Bild: Von „Audit aus CSV-Export" zu „Ads-Betriebssystem, das plant, erstellt, überwacht, optimiert"]

### Repository-Struktur
[Verzeichnisse mit kurzer Beschreibung]

### Kern-Features
| Feature | Status | Beschreibung |
|---------|--------|--------------|
| [Feature] | ✅ Live / 🔨 In Arbeit / ⬜ Geplant | [Kurz] |

### Plattform-/Capability-Matrix
| Plattform | export-read | live-read | draft-write | live-write | Quelle |
|-----------|-------------|-----------|-------------|------------|--------|

### Infrastruktur-Status
| Service | Provider | Status |
|---------|----------|--------|

---

## Aktueller Stand
### 1. [Komponente] — [Status]
**Pfad:** `[Verzeichnis]` · **Tech Stack:** [...]
[Module/Skills/Adapter als Tabelle — was existiert, Status, Test-Evidenz]

---

## Mandanten & Konten
| Mandant | Plattform | Konto-ID | Rolle | Anbindung |
|---------|-----------|----------|-------|-----------|
(keine Secrets — nur IDs und Anbindungsart)

---

## Geplante Features
### A. [Feature Name]
**Priorität:** ★★★ / ★★ / ★
**Ziel:** [1-2 Sätze]
| Komponente | Kategorie | Beschreibung |
|------------|-----------|--------------|

---

## Betriebsmodell: Planen → Erstellen → Überwachen → Optimieren
[Pro Phase: Input, Skill/Agent, Output, Freigabe-Gate, Rollback]

## Sicherheits- & Mutations-Modell
[Read-only Default, Mutation-Gate (Preview/Approval/Idempotenz/Verify/Audit/Rollback), Budget-Ceilings, Approver]

## Technischer Stack
| Bereich | Technologie | Beschreibung |
|---------|-------------|-------------|

## Datenmodell / Persistenz
[State-Verzeichnis, Schemas in claude_ads_core/schemas, ggf. DB]

## Externe Services & APIs
| Service | Zweck | Env Vars (nur Namen) | Access-Level |
|---------|-------|----------------------|--------------|

---

## Roadmap: Meilensteine
### ✅ Abgeschlossen
| Meilenstein | Zeitraum | Status |
### M1 … Mn
| Task | Kategorie | Aufwand | Status |

## PRP-Referenz
| PRP | Feature | Status |

## Risiken & Offene Fragen
```

---

## Phase 4: Qualitätsprüfung

1. ✅ **Vollständigkeit:** Jedes existierende Feature mit korrektem Status
2. ✅ **Korrektheit:** Tech Stack, Pfade, Env-Var-Namen stimmen mit Code/Manifesten überein
3. ✅ **Status-Ehrlichkeit:** Nichts „Live" was nur Skill-Prosa ist — Capability-Manifest ist maßgeblich
4. ✅ **Roadmap-Realismus:** Meilensteine nach Abhängigkeiten sortiert (Read-Zugriff vor Write-Pfad)
5. ✅ **Keine Secrets:** keine Tokens, keine Client-Daten, keine absoluten lokalen Pfade
6. ✅ **Alleinstehend:** Ein neuer Entwickler versteht das Produkt aus dem PRD

---

## Phase 5: Output

- PRD-Pfad, Version, Abschnitte
- Anzahl Features (Live / In Arbeit / Geplant)
- Empfehlung: erste 3 PRPs in Reihenfolge
- Falls kein Wiki: `/rebuild-docs` empfehlen

**Nächster Schritt:** `/01-plan [Feature]` oder `/prd-update`
