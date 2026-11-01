"""The cadence document must state exactly the thresholds the watcher uses."""
from __future__ import annotations

import re
from pathlib import Path

from claude_ads_core import watch

DOC = Path(__file__).resolve().parents[2] / "ads" / "references" / "kadenz-und-regeln.md"
CONSTANTS = (
    "PACING_WINDOW_DAYS", "PACING_CAPPED_RATIO", "PACING_UNDER_RATIO", "PACING_OVER_RATIO", "CONVERSION_WINDOW_DAYS",
    "MIN_CLICKS_FOR_CONVERSION_RULES", "MIN_CLICKS_FOR_NO_CONVERSION", "MIN_PREVIOUS_CONVERSIONS_FOR_DROP", "DATA_GAP_DAYS",
)


def _documented() -> dict[str, str]:
    rows = re.findall(r"^\| `([A-Z_]+)` \| ([0-9.]+) \|", DOC.read_text(encoding="utf-8"), flags=re.M)
    return dict(rows)


def test_every_constant_is_documented_with_the_code_value():
    documented = _documented()
    assert set(documented) == set(CONSTANTS)
    for name in CONSTANTS:
        assert float(documented[name]) == float(getattr(watch, name)), name


def test_document_is_honest_about_its_status():
    text = DOC.read_text(encoding="utf-8")
    assert "not platform facts" in text and "at most one change round" in text.lower()
    assert "mutate" not in text.lower()
