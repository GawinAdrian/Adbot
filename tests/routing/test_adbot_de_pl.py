"""Deterministic guards for the German/Polish assistant: routing, behavior pack, and command files."""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

STOP = {"a", "an", "and", "or", "the", "to", "for", "from", "with", "our", "my", "of", "in", "on", "use"}
COMMANDS = ("start", "analyse", "kampagne", "bericht", "optimieren", "hilfe", "verbinden", "trennen")


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9+]+", text.lower()) if len(t) > 1 and t not in STOP}


def _score(prompt: str, description: str) -> int:
    return len(_tokens(prompt) & _tokens(description))


def _load(repo_root: Path, name: str) -> list[dict]:
    return json.loads((repo_root / "evals" / name).read_text(encoding="utf-8"))


def test_assistant_wins_german_and_polish_routing_cases(skill_descriptions, repo_root):
    cases = _load(repo_root, "adbot-routing-de-pl.json")
    assert len(cases) >= 12
    assert {c["id"].split("-")[0] for c in cases} == {"de", "pl"}
    failures = []
    for case in cases:
        expected = _score(case["prompt"], skill_descriptions[case["expected_skill"]])
        if expected < 2:
            failures.append(f"{case['id']}: weak score {expected}")
        for forbidden in case["forbidden_skills"]:
            other = _score(case["prompt"], skill_descriptions[forbidden])
            if other >= expected:
                failures.append(f"{case['id']}: {forbidden} scores {other} >= {expected}")
    assert not failures, "\n".join(failures)


def test_behavior_pack_is_well_formed_and_covers_both_languages(skill_descriptions, repo_root):
    cases = _load(repo_root, "adbot-behavior-de-pl.json")
    ids = [c["id"] for c in cases]
    assert len(ids) == len(set(ids)) and len(cases) >= 12
    assert {i.split("-")[0] for i in ids} == {"de", "pl"}
    for case in cases:
        assert case["expected_skill"] in skill_descriptions
        assert case["risk"] in {"P0", "P1", "P2", "normal"}
        assert case["comparison"] == "with_skill_vs_baseline"
        assert case["required_behaviors"] and case["forbidden_behaviors"]
        assert not set(case["required_behaviors"]) & set(case["forbidden_behaviors"])
    assert sum(c["risk"] == "P0" for c in cases) >= 6


def test_skill_states_every_hard_stop_the_behavior_pack_depends_on(repo_root):
    text = (repo_root / "skills" / "ads-assistent" / "SKILL.md").read_text(encoding="utf-8").lower()
    for phrase in ("permanent deletion", "token, key, password", "search terms report", "different windows", "mutation gate",
                   "never", "briefing gate", "confirm"):
        assert phrase in text, phrase


@pytest.mark.parametrize("name", COMMANDS)
def test_command_files_are_guided_safe_and_language_aware(repo_root, name):
    text = (repo_root / ".claude" / "commands" / f"{name}.md").read_text(encoding="utf-8")
    assert text.startswith("---\ndescription: ")
    assert "settings show" in text and "`language`" in text, f"{name}: no language rule"
    lowered = text.lower()
    # every command states at least one concrete prohibition of its own
    assert re.search(r"(niemals|nie |nicht |nichts |keine |kein |ohne )", lowered), f"{name}: no stated prohibition"
    if name not in {"verbinden", "trennen", "hilfe"}:
        assert "prozesskarten.md" in text or "kadenz-und-regeln.md" in text, f"{name}: no process card"
    if name == "hilfe":
        assert "docs/<sprache>/00-overview.md" in text
    # nothing may ask the user to hand over sign-in data
    assert not re.search(r"(schick|sende|paste|wklej)\w* .*(passwort|schlüssel|client\.json)", lowered)


def test_process_cards_cover_all_processes_in_both_languages(repo_root):
    text = (repo_root / "ads" / "references" / "prozesskarten.md").read_text(encoding="utf-8")
    for heading in ("## Start", "## Connect / Disconnect", "## Analyse", "## Campaign", "## Report", "## Optimise", "## Help"):
        assert heading in text
    assert "DE:" in text and "PL:" in text
    assert re.search(r"[ąęłńóśźż]", text) and re.search(r"[äöüß]", text)


PL_COMMANDS = {
    "zacznij": "start", "polacz": "verbinden", "odlacz": "trennen", "analiza": "analyse",
    "kampania": "kampagne", "raport": "bericht", "optymalizuj": "optimieren", "pomoc": "hilfe",
}


@pytest.mark.parametrize("pl_name,de_name", sorted(PL_COMMANDS.items()))
def test_polish_commands_mirror_the_german_ones(repo_root, pl_name, de_name):
    commands = repo_root / ".claude" / "commands"
    pl = (commands / f"{pl_name}.md").read_text(encoding="utf-8")
    de = (commands / f"{de_name}.md").read_text(encoding="utf-8")
    assert pl.startswith("---\ndescription: ") and re.search(r"[ąćęłńóśźż]", pl)
    assert "settings show" in pl and "`language`" in pl
    assert re.search(r"(nigdy|nie |niczego|żadn|bez )", pl.lower()), f"{pl_name}: no stated prohibition"
    # same process card / document references as the German command
    for ref in re.findall(r"`((?:ads|docs|scripts)/[^`<> ]+)`", de):
        if ref.startswith("docs/de/"):
            ref = ref.replace("docs/de/", "docs/pl/")
        if ref.startswith("docs/<sprache>/"):
            ref = ref.replace("<sprache>", "pl")
        assert ref in pl or ref.replace("docs/pl/", "docs/de/") in pl, f"{pl_name}: missing {ref}"
    assert ("argument-hint" in de) == ("argument-hint" in pl)
    assert not re.search(r"(wyślij|wyslij|wklej)\w* .*(hasł|klucz|client\.json)", pl.lower())
