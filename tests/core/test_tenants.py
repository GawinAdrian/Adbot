from __future__ import annotations

import copy
import json
import os
from pathlib import Path

import pytest

from claude_ads_core.cli import main
from claude_ads_core.contracts import validate_contract
from claude_ads_core.tenants import TenantError, TenantRegistry, run_scopes


@pytest.fixture()
def tenant_profile(repo_root: Path) -> dict:
    fixtures = json.loads((repo_root / "tests/fixtures/workflows/valid-artifacts.json").read_text(encoding="utf-8"))
    return copy.deepcopy(fixtures["tenant-profile"])


def _second_tenant(profile: dict) -> dict:
    other = copy.deepcopy(profile)
    other["tenant_id"] = "second-tenant"
    other["display_name"] = "Second Tenant"
    other["accounts"] = [{"platform": "meta", "account_id": "act_demo", "role": "client", "login_customer_id": None, "connection": "none"}]
    return other


def test_fixture_validates_as_contract_and_registry_roundtrips(tmp_path: Path, tenant_profile: dict):
    validate_contract("tenant-profile", tenant_profile)
    registry = TenantRegistry(tmp_path / "tenants")
    path = registry.register(tenant_profile)
    assert path == tmp_path / "tenants" / "demo-tenant" / "profile.json"
    assert oct(path.stat().st_mode & 0o777) == "0o600"
    assert registry.load("demo-tenant") == tenant_profile
    assert [p["tenant_id"] for p in registry.list()] == ["demo-tenant"]
    assert registry.resolve_account("google", "demo-account")["tenant_id"] == "demo-tenant"
    assert registry.run_directory("demo-tenant", "run-001") == tmp_path / "tenants" / "demo-tenant" / "runs" / "run-001"
    assert run_scopes("demo-tenant") == ["tenant:demo-tenant"]


def test_accounts_are_unique_across_tenants(tmp_path: Path, tenant_profile: dict):
    registry = TenantRegistry(tmp_path)
    registry.register(tenant_profile)
    clash = _second_tenant(tenant_profile)
    clash["accounts"].append({"platform": "google", "account_id": "demo-account", "role": "client", "login_customer_id": None, "connection": "none"})
    with pytest.raises(TenantError, match="already belongs to tenant demo-tenant"):
        registry.register(clash)
    registry.register(_second_tenant(tenant_profile))
    assert [p["tenant_id"] for p in registry.list()] == ["demo-tenant", "second-tenant"]
    with pytest.raises(TenantError, match="no tenant owns"):
        registry.resolve_account("tiktok", "missing")


def test_overwrite_requires_non_decreasing_updated_at(tmp_path: Path, tenant_profile: dict):
    registry = TenantRegistry(tmp_path)
    newer = copy.deepcopy(tenant_profile)
    newer["updated_at"] = "2026-08-01T00:00:00Z"
    registry.register(newer)
    with pytest.raises(TenantError, match="older than the registered profile"):
        registry.register(tenant_profile)
    newer["display_name"] = "Renamed"
    registry.register(newer)
    assert registry.load("demo-tenant")["display_name"] == "Renamed"


@pytest.mark.parametrize(
    "mutate, message",
    [
        (lambda p: p.__setitem__("tenant_id", "Demo Tenant"), "invalid format"),
        (lambda p: p.__setitem__("updated_at", "2026-01-01T00:00:00Z"), "must not precede"),
        (lambda p: p["accounts"].append(dict(p["accounts"][0])), "duplicates google account"),
        (lambda p: p["ceilings"].__setitem__("max_objects_per_approval", 0), "must be >= 1"),
        (lambda p: p["ceilings"].__setitem__("currency", "eur"), "invalid format"),
        (lambda p: p.__setitem__("privacy_class", "confidential"), "must match"),
        (lambda p: p.__setitem__("unexpected", True), "unknown field"),
        (lambda p: p["business"].__setitem__("website", "http://insecure.example"), "invalid format"),
    ],
)
def test_invalid_profiles_fail_closed(tenant_profile: dict, mutate, message: str):
    mutate(tenant_profile)
    with pytest.raises(TenantError, match=message):
        TenantRegistry.validate(tenant_profile)


def test_symlinked_root_and_unsafe_ids_are_rejected(tmp_path: Path, tenant_profile: dict):
    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "link"
    os.symlink(real, link)
    with pytest.raises(TenantError, match="symlink"):
        TenantRegistry(link).register(tenant_profile)
    registry = TenantRegistry(real)
    with pytest.raises(TenantError, match="lowercase slug"):
        registry.load("../escape")
    with pytest.raises(TenantError, match="path-safe"):
        registry.run_directory("demo-tenant", "../run")


def test_cli_tenant_commands_are_machine_readable(tmp_path: Path, tenant_profile: dict, capsys):
    source = tmp_path / "profile.json"
    source.write_text(json.dumps(tenant_profile), encoding="utf-8")
    root = tmp_path / "state"
    assert main(["tenant", "validate", str(source)]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "valid"
    assert main(["tenant", "register", str(source), "--root", str(root)]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "registered"
    assert main(["tenant", "list", "--root", str(root)]) == 0
    listed = json.loads(capsys.readouterr().out)
    assert listed["tenants"][0]["accounts"][0]["account_id"] == "demo-account"
    assert main(["tenant", "resolve", "--platform", "google", "--account-id", "demo-account", "--root", str(root)]) == 0
    assert json.loads(capsys.readouterr().out)["tenant_id"] == "demo-tenant"
    assert main(["tenant", "show", "missing-tenant", "--root", str(root)]) != 0
