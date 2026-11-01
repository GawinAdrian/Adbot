"""German and Polish guides must stay in step: same files, same structure, real diacritics, working references."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from claude_ads_core.i18n import catalog_meta, glossary

ROOT = Path(__file__).resolve().parents[2]
DE, PL = ROOT / "docs" / "de", ROOT / "docs" / "pl"
EXPECTED = ["00-overview", "01-install", "02-connect", "03-disconnect", "04-analysis", "05-first-campaign",
            "06-cockpit-report", "07-approvals-undo", "08-watcher", "09-troubleshooting", "10-glossary-privacy"]
ASCII_SUBSTITUTES = ("Aenderung", "fuer ", "moechte", "muessen", "waehrend", "Schluessel", "naechst", "ueber", "loeschen",
                     "koennen", "zurueck", "Pruefung", "Loesch", "Massnahme", "Gueltig")
BACKTICK = re.compile(r"`([^`\n]+)`")
PATH_ROOTS = ("docs/", "ads/", "scripts/", "claude_ads_core/", "skills/", "control-plane/")


def _read(base: Path, name: str) -> str:
    return (base / f"{name}.md").read_text(encoding="utf-8")


def test_both_languages_have_exactly_the_expected_files():
    assert sorted(p.stem for p in DE.glob("*.md")) == EXPECTED
    assert sorted(p.stem for p in PL.glob("*.md")) == EXPECTED


@pytest.mark.parametrize("name", EXPECTED)
def test_structure_matches_between_languages(name):
    de, pl = _read(DE, name), _read(PL, name)
    assert len(re.findall(r"^## ", de, flags=re.M)) == len(re.findall(r"^## ", pl, flags=re.M)), name
    assert de.count("```") == pl.count("```"), f"{name}: code blocks differ"
    # the commands a guide shows must be identical in both languages
    de_cmds = [c for c in BACKTICK.findall(de) if c.startswith(("python ", "gcloud ", "/"))]
    pl_cmds = [c for c in BACKTICK.findall(pl) if c.startswith(("python ", "gcloud ", "/"))]
    normalise = lambda items: sorted(re.sub(r"<[^>]+>", "<X>", re.sub(r"--lang (de|pl)", "--lang X", c)) for c in items)
    assert normalise(de_cmds) == normalise(pl_cmds), name


@pytest.mark.parametrize("name", EXPECTED)
def test_german_uses_umlauts_and_polish_uses_diacritics(name):
    de, pl = _read(DE, name), _read(PL, name)
    for bad in ASCII_SUBSTITUTES:
        assert bad not in de, f"{name}: {bad!r}"
    assert re.search(r"[ąćęłńóśźż]", pl), f"{name}: no Polish diacritics"


def test_german_guides_use_real_umlauts_overall():
    text = " ".join(_read(DE, n) for n in EXPECTED)
    assert text.count("ü") > 20 and text.count("ä") > 10


@pytest.mark.parametrize("language", ("de", "pl"))
@pytest.mark.parametrize("name", EXPECTED)
def test_referenced_paths_and_slash_commands_exist(language, name):
    text = _read(DE if language == "de" else PL, name)
    for token in BACKTICK.findall(text):
        if token.startswith(PATH_ROOTS) and " " not in token and "<" not in token and "*" not in token:
            assert (ROOT / token.rstrip("/")).exists(), f"{language}/{name}: missing {token}"
        match = re.fullmatch(r"/([a-z]+)", token)
        if match:
            assert (ROOT / ".claude" / "commands" / f"{match.group(1)}.md").is_file(), f"{language}/{name}: no command {token}"


@pytest.mark.parametrize("language", ("de", "pl"))
@pytest.mark.parametrize("name", EXPECTED)
def test_every_guide_has_a_date_and_names_a_way_to_check(language, name):
    text = _read(DE if language == "de" else PL, name)
    assert re.search(r"\*\*(Stand|Stan na):\*\*", text)
    if name != "10-glossary-privacy":  # a reference page, not a procedure
        assert re.search(r"python -m claude_ads_core|python scripts/|`/[a-z]+`|python3 ", text), f"{language}/{name}: no command shown"


def test_connect_and_disconnect_end_with_a_check_line():
    for base in (DE, PL):
        assert "doctor" in _read(base, "02-connect") and "doctor" in _read(base, "03-disconnect")


def test_polish_guides_are_marked_as_draft_while_the_catalog_is():
    draft = catalog_meta("pl")["review_status"] == "entwurf"
    for name in EXPECTED:
        assert ("Wersja robocza" in _read(PL, name)) == draft, name


def test_glossary_table_contains_every_term_in_both_guides():
    for term in glossary()["terms"]:
        assert f"**{term['de']}**" in _read(DE, "10-glossary-privacy"), term["id"]
        assert f"**{term['pl']}**" in _read(PL, "10-glossary-privacy"), term["id"]


def test_guides_never_ask_for_secrets_in_chat():
    for base in (DE, PL):
        text = " ".join(_read(base, n) for n in EXPECTED).lower()
        assert "curl" in text and "irm" in text  # the install guide warns against pipe-to-shell
        assert "refresh_token" not in text and "client_secret" not in text
