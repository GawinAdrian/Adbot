"""Repository hygiene: no client data, secrets, or local paths in tracked files.

The checks use pattern classes only (no list of client names).  Placeholders
that are allowed must be listed explicitly so that a new, real-looking ID or
address fails the test and forces a conscious decision.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

ID_SHAPE = re.compile(r"\b\d{3}-\d{3}-\d{4}\b|\b\d{10}\b")
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
ABS_PATH = re.compile(r"/Users/[A-Za-z0-9._-]+|C:\\Users\\[A-Za-z0-9._-]+")
SECRET = re.compile(
    r"21st_sk_[0-9a-f]{16,}|sk-[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_-]{20,}|"
    r"ghp_[A-Za-z0-9]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|"
    r"refresh_token[\"']?\s*[:=]\s*[\"'][A-Za-z0-9/_-]{20,}"
)

# Explicit placeholders and non-ID numbers (epoch timestamps, loopback as int).
ALLOWED_IDS = frozenset(
    {"1234567890", "1122334455", "9999999999", "123-456-7890", "112-233-4455",
     "1783728000", "2130706433"}
)
ALLOWED_EMAIL = re.compile(
    r"(@example\.[a-z]+$|\.(test|invalid|example)$|^noreply@|"
    r"@users\.noreply\.github\.com$|^security@|^support@|@python\.org$)"
)
# Third-party author metadata and deliberate fake credentials in redaction tests.
EMAIL_SKIP_PREFIXES = (
    "control-plane/dependency-", "control-plane/manifests/dependency-",
    "control-plane/schemas/",
)
FAKE_CREDENTIAL_FILES = frozenset(
    {"tests/scripts/test_url_utils.py", "tests/core/test_reporting.py"}
)
ID_SKIP_PREFIXES = (
    "control-plane/dependency-", "control-plane/manifests/dependency-",
    "control-plane/schemas/", "requirements",
)
TEXT_SUFFIXES = {
    ".md", ".py", ".json", ".txt", ".toml", ".yml", ".yaml", ".sh", ".ps1",
    ".cff", ".csv", ".html", ".cfg",
}
FORBIDDEN_TRACKED = re.compile(
    r"(^|/)(\.env(\..*)?|Kunden/.*|kunden/.*|\.claude-ads/.*|\.adbot/.*|"
    r".*Transkript.*|credentials\.json|client_secret.*\.json|service-account\.json)$"
)


def _tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "-z"],
        capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        pytest.skip("not a git checkout")
    return [p for p in result.stdout.split("\0") if p]


def _lines(rel: str):
    path = ROOT / rel
    if path.suffix.lower() not in TEXT_SUFFIXES or not path.is_file():
        return
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return
    yield from enumerate(text.splitlines(), 1)


def test_no_forbidden_files_are_tracked():
    bad = [p for p in _tracked_files() if FORBIDDEN_TRACKED.search(p)
           and not p.endswith(".env.example")]
    assert not bad, f"forbidden tracked files: {bad}"


def test_no_secrets_or_absolute_local_paths():
    findings = []
    for rel in _tracked_files():
        for lineno, line in _lines(rel):
            if rel not in FAKE_CREDENTIAL_FILES and SECRET.search(line):
                findings.append(f"{rel}:{lineno}: secret pattern")
            if rel != "tests/repo/test_no_client_data.py" and ABS_PATH.search(line):
                findings.append(f"{rel}:{lineno}: absolute local path")
    assert not findings, "\n".join(findings)


def test_no_unexpected_email_addresses():
    findings = []
    for rel in _tracked_files():
        if rel.startswith(EMAIL_SKIP_PREFIXES) or rel in FAKE_CREDENTIAL_FILES:
            continue
        for lineno, line in _lines(rel):
            for match in EMAIL.finditer(line):
                if not ALLOWED_EMAIL.search(match.group(0)):
                    findings.append(f"{rel}:{lineno}: e-mail address")
    assert not findings, "\n".join(findings)


def test_no_unexpected_account_id_shapes():
    findings = []
    for rel in _tracked_files():
        if rel.startswith(ID_SKIP_PREFIXES) or rel == "tests/repo/test_no_client_data.py":
            continue
        for lineno, line in _lines(rel):
            for match in ID_SHAPE.finditer(line):
                if match.group(0) not in ALLOWED_IDS:
                    findings.append(f"{rel}:{lineno}: account-id-like number")
    assert not findings, "\n".join(findings)
