# Adbot – Repository-Anweisungen

@AGENTS.md

`AGENTS.md` ist der portable Regelvertrag. Dieses Repo ist ein **Selbstbedienungs-Assistent für Google Ads** (Deutsch und Polnisch),
abgeleitet von Claude Ads v2. Einstieg für Nutzerinnen: `README.md` und `docs/de|pl/`. Einstieg für Agenten: `ads/SKILL.md`,
`skills/ads-assistent/SKILL.md`, `ads/references/prozesskarten.md`.

## Architektur

- `skills/ads-assistent/` und `.claude/commands/`: geführte Prozesse (`/start`, `/analyse`, `/kampagne`, `/bericht`, `/optimieren`, `/verbinden`, `/trennen`, `/hilfe`).
- `claude_ads_core/`: deterministische Logik – `watch.py` (Wächter), `cockpit.py` (HTML-Übersicht), `doctor.py` (Diagnose), `briefing.py` (Briefing-Tor),
  `user_settings.py`, `i18n/` (Kataloge DE/PL/EN, Glossar), `editor_export.py` (pausierter Entwurf), Adapter und Verträge.
- `scripts/`: `gaql_via_api.py` (nur lesend), `run_daily_watch.py`, `schedule_watch.py`, `adbot_env.py`.
- `control-plane/`: Manifeste, Quellen- und Claim-Register, Produktgrenzen, Release-Gates (geerbt).
- `docs/de/`, `docs/pl/`: Anleitungen mit gleichen Dateinamen (Test `tests/docs/test_docs_parity.py`).

## Arbeitsregeln

- Antworten und Dialoge in der Sprache der Nutzerin (`settings show` → `language`); Fachbegriffe aus dem Glossar.
- Neue Meldungen in **allen drei** Katalogen (`claude_ads_core/i18n/catalog_*.py`); de und pl brauchen identische Schlüssel.
- Deutsch mit echten Umlauten, Polnisch mit Diakritika; Polnisch bleibt „Entwurf“, bis ein Muttersprachler es geprüft hat.
- Keine Plattformzahl ohne Eintrag in Quellen- und Claim-Register (mit Datum). Schwellen des Wächters sind Produktentscheidungen und stehen in `ads/references/kadenz-und-regeln.md`.
- `pyproject.toml`, Locks und das Dependency-Inventar sind an Release-Prüfungen gebunden: nicht ändern, ohne die Release-Gates bewusst neu aufzusetzen.

## Verifikation

`python -m pytest -q` (bekannte Umgebungsfehler: WeasyPrint-Systembibliothek, ein Lock-Verifier-Test). Leak-Test: `tests/repo/test_no_client_data.py`.
Kein Release-Anspruch ohne `control-plane/RELEASE_REQUIREMENTS.md`.
