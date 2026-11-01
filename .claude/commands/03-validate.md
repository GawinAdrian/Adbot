---
description: Vollständige Validierung (Tests, CLI, Schemas, Secrets-Check) für Adbot
---

# Validate: Adbot

Führe alle Prüfungen der Reihe nach aus und berichte die Ergebnisse.

## 0. Umgebung

```bash
[ -x .venv/bin/python ] && PY=.venv/bin/python || PY=python3
$PY --version
```

Falls kein `.venv`: einmalig anlegen (siehe README „Development"): `python3 -m venv .venv && .venv/bin/python -m pip install --no-deps -e . && .venv/bin/python -m pip install -r requirements-dev.txt`

## 1. Test-Suite

```bash
$PY -m pytest -q
```
**Erwartet:** alle Tests grün

## 2. CLI & Paket

```bash
$PY -m claude_ads_core --version
$PY -m pip check
```

## 3. Installer-Syntax

```bash
bash -n install.sh uninstall.sh
```

## 4. Manifest-Konsistenz (falls Manifeste geändert)

```bash
git diff --name-only HEAD | grep -q "control-plane/manifests" && $PY -m pytest -q tests/audit tests/core/test_control_registry.py tests/core/test_product_status.py
```

## 5. Secrets- & Pfad-Check

```bash
git diff HEAD | grep -nE "/Users/|AIza|ya29\.|refresh_token|developer_token|client_secret" || echo "OK: keine Secrets/absoluten Pfade"
git ls-files --others --exclude-standard | grep -E "\.env|credentials|\.json$" || echo "OK: keine untracked Credential-Dateien"
```

## 6. Summary Report

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 Validierung Adbot
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ✅/❌ Pytest:       X passed
  ✅/❌ CLI:          version OK
  ✅/❌ pip check:    OK
  ✅/❌ Installer:    bash -n OK
  ✅/❌ Manifeste:    OK / nicht betroffen
  ✅/❌ Secrets:      keine gefunden
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Status: ✅ ALL CHECKS PASSED / ❌ VALIDATION FAILED
```

Bei Fehlern: Datei, Zeile, Beschreibung. Bei Erfolg: **Nächster Schritt:** `/04-review` oder `/05-commit`
