# Runbook: Mandanten (Tenants) anlegen und pflegen

**Stand:** 2026-08-27

Ein Mandant ist ein validiertes Profil (`tenant-profile` v1) unter `.claude-ads/tenants/<tenant_id>/profile.json`
(git-ignoriert). Es bindet Konten je Plattform an Ziele, KPIs, Budget-Leitplanken, Approver, Reporting und
Datenklasse. Jedes Konto gehört genau einem Mandanten (ein Mandant im Aufbau darf noch keine Konten haben); Läufe liegen unter `.claude-ads/tenants/<tenant_id>/runs/`.

## Voraussetzung: Verschlüsselung

Profile mit Kundendaten sind `confidential`. Der Lifecycle-Contract verlangt dafür verifizierte
Verschlüsselung im Ruhezustand. Auf dem aktuellen Mac ist FileVault **aus** (`fdesetup status`, 2026-08-27).
Vor der Registrierung: Systemeinstellungen → Datenschutz & Sicherheit → FileVault aktivieren, danach
`fdesetup status` → „FileVault is On“. Erst dann `encryption.at_rest` auf `verified` setzen mit
`evidence_refs: ["operator-attestation:filevault-enabled <Datum>"]`. Entwürfe mit `not-applicable`
werden bewusst abgelehnt.

## Onboarding eines neuen Mandanten (< 1 h)

1. Vorlage kopieren: `cp docs/tenants/tenant-profile.template.json .claude-ads/tenant-drafts/<slug>.json`
2. Ausfüllen: Konten (IDs ohne Bindestriche, `login_customer_id` = MCC bei Google-Unterkonten),
   Ziel + Conversion-Definition, KPIs, Ceilings (max. Budgetänderung in % und absolut, max. Objekte je
   Freigabe, verbotene Operationen), Approver, Reporting-Rhythmus, Datenklasse + Lifecycle.
3. Prüfen: `.venv/bin/python -m claude_ads_core tenant validate .claude-ads/tenant-drafts/<slug>.json`
4. Registrieren: `.venv/bin/python -m claude_ads_core tenant register .claude-ads/tenant-drafts/<slug>.json`
5. Kontrolle: `tenant list`, `tenant resolve --platform google --account-id <id>`
6. Danach `/ads setup` für Tracking-Check, Brand-DNA (`brand_profile_ref` nachtragen) und ersten Audit.

## Pflege

- Änderungen immer mit neuem `updated_at` (ältere Stände werden abgelehnt).
- Offboarding: `status: offboarded`, Löschtermin im Lifecycle setzen, Verzeichnis nach Verifikation sicher löschen.
- Konto-Wechsel zwischen Mandanten: erst beim alten Mandanten entfernen, dann beim neuen registrieren.
