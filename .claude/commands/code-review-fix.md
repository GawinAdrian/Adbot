---
description: Issues aus einem Code Review beheben
argument-hint: [Pfad zur Review-Datei oder Issue-Beschreibung]
---

# Code Review Fix

**Code Review**: $ARGUMENTS

Falls das Review eine Datei ist, zuerst vollständig lesen. Behebe die Issues einzeln, priorisiert (CRITICAL → LOW).

Für jeden Fix:
1. Erkläre, was falsch war
2. Zeige den Fix
3. Ergänze/aktualisiere Tests zur Verifizierung

Nach allen Fixes: `/03-validate` ausführen. Dann `/05-commit`.
