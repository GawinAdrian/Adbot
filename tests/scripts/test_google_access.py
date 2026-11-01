"""Tests for Adbot's token-optional Google access scripts.

Covers scripts/adbot_env.py, scripts/gaql_via_api.py, scripts/keyword_ideas_via_api.py and
the scripts/google_ads_mcp.sh wrapper.  No network access and no Google client library needed.
"""
from __future__ import annotations

import enum
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import adbot_env  # noqa: E402
import gaql_via_api  # noqa: E402
import keyword_ideas_via_api  # noqa: E402

WRAPPER = SCRIPTS_DIR / "google_ads_mcp.sh"
FAKE_TOKEN = "fake-token-value-for-redaction-test"


# ---------------------------------------------------------------- adbot_env


def test_parse_env_text_reads_allowed_keys_only_and_last_wins():
    text = "# c\nGOOGLE_PROJECT_ID=first\nOTHER=x\nGOOGLE_PROJECT_ID='second'\nGOOGLE_ADS_DEVELOPER_TOKEN=\n"
    assert adbot_env.parse_env_text(text) == {"GOOGLE_PROJECT_ID": "second"}


def test_client_config_omits_token_when_not_set():
    config = adbot_env.build_client_config({})
    assert "developer_token" not in config
    assert config["use_application_default_credentials"] is True


def test_client_config_passes_legacy_token_and_login_id_through():
    config = adbot_env.build_client_config({"DEVELOPER_TOKEN": FAKE_TOKEN}, "1122334455")
    assert config["developer_token"] == FAKE_TOKEN
    assert config["login_customer_id"] == "1122334455"


def test_load_env_prefers_environment_then_profile_then_repo_env(tmp_path):
    profile = tmp_path / "profile"
    profile.mkdir()
    (profile / "env").write_text("GOOGLE_PROJECT_ID=from-profile\nGOOGLE_ADS_LOGIN_CUSTOMER_ID=1122334455\n")
    (tmp_path / ".env").write_text("GOOGLE_PROJECT_ID=from-repo\nGOOGLE_APPLICATION_CREDENTIALS=/x/adc.json\n")
    environ = {"ADBOT_PROFILE_DIR": str(profile), "GOOGLE_APPLICATION_CREDENTIALS": "from-environment"}
    loaded = adbot_env.load_env(tmp_path, environ)
    assert environ["GOOGLE_PROJECT_ID"] == "from-profile"
    assert environ["GOOGLE_APPLICATION_CREDENTIALS"] == "from-environment"
    assert sorted(loaded) == ["GOOGLE_ADS_LOGIN_CUSTOMER_ID", "GOOGLE_PROJECT_ID"]
    assert all("=" not in name and "profile" not in name for name in loaded)  # names only, no values


def test_missing_credentials_fail_loudly(tmp_path):
    with pytest.raises(adbot_env.CredentialsError, match="credentials file missing"):
        adbot_env.adc_path({}, home=tmp_path)
    with pytest.raises(adbot_env.CredentialsError, match="GOOGLE_PROJECT_ID"):
        adbot_env.require_project({})


def test_adc_path_returns_existing_file(tmp_path):
    adc = tmp_path / "adc.json"
    adc.write_text("{}")
    assert adbot_env.adc_path({"GOOGLE_APPLICATION_CREDENTIALS": str(adc)}) == adc


# ------------------------------------------------------------- gaql_via_api


def test_build_query_happy_path():
    query = gaql_via_api.build_query(
        "campaign", ["campaign.id", "metrics.cost_micros"],
        ["segments.date DURING LAST_7_DAYS"], ["metrics.cost_micros DESC"], 10,
    )
    assert query == (
        "SELECT campaign.id, metrics.cost_micros FROM campaign "
        "WHERE segments.date DURING LAST_7_DAYS ORDER BY metrics.cost_micros DESC LIMIT 10"
    )


@pytest.mark.parametrize(
    "kwargs",
    [
        {"resource": "campaign; DROP", "fields": ["campaign.id"]},
        {"resource": "campaign", "fields": []},
        {"resource": "campaign", "fields": ["campaign"]},
        {"resource": "campaign", "fields": ["campaign.id; x"]},
        {"resource": "campaign", "fields": ["campaign.id"], "conditions": ["a = 1; SELECT 2"]},
        {"resource": "campaign", "fields": ["campaign.id"], "conditions": ["a = 1\nOR b = 2"]},
        {"resource": "campaign", "fields": ["campaign.id"], "order_by": ["x; y"]},
        {"resource": "campaign", "fields": ["campaign.id"], "limit": 0},
    ],
)
def test_build_query_rejects_unsafe_parts(kwargs):
    with pytest.raises(gaql_via_api.QueryError):
        gaql_via_api.build_query(**kwargs)


class _Status(enum.IntEnum):
    ENABLED = 2


def test_extract_row_converts_enums_int64_and_floats():
    row = SimpleNamespace(
        campaign=SimpleNamespace(id=222000111, status=_Status.ENABLED, name="Beispiel"),
        metrics=SimpleNamespace(cost_micros=28750000, conversions=1.5, clicks=0),
    )
    out = gaql_via_api.extract_row(
        row, ["campaign.id", "campaign.status", "campaign.name", "metrics.cost_micros",
              "metrics.conversions", "metrics.clicks"],
    )
    assert out == {
        "campaign.id": "222000111", "campaign.status": "ENABLED", "campaign.name": "Beispiel",
        "metrics.cost_micros": "28750000", "metrics.conversions": 1.5,
        "metrics.clicks": "0",  # zero is kept, never dropped as "missing"
    }


def test_extract_row_unknown_field_fails_loudly():
    with pytest.raises(AttributeError):
        gaql_via_api.extract_row(SimpleNamespace(campaign=SimpleNamespace()), ["campaign.id"])


def test_gaql_script_is_read_only_by_construction():
    source = (SCRIPTS_DIR / "gaql_via_api.py").read_text(encoding="utf-8")
    # The docstring names the rule; code must not reference any mutate service or method.
    code = source.split('"""', 2)[2]
    assert "mutate" not in code.lower()
    assert "search_stream" in code
    assert "OperationService" not in code


def test_gaql_envelope_shape_is_accepted_by_the_live_adapter(tmp_path):
    from claude_ads_core.adapters import GoogleAdsLiveReadAdapter

    fields = ["segments.date", "customer.id", "customer.descriptive_name", "customer.currency_code",
              "campaign.id", "campaign.name", "campaign.status", "campaign.advertising_channel_type",
              "campaign_budget.amount_micros", "metrics.cost_micros", "metrics.conversions"]
    row = SimpleNamespace(
        segments=SimpleNamespace(date="2026-10-01"),
        customer=SimpleNamespace(id=1234567890, descriptive_name="Demo", currency_code="EUR"),
        campaign=SimpleNamespace(id=222000111, name="Beispiel", status=_Status.ENABLED,
                                 advertising_channel_type=_Status.ENABLED),
        campaign_budget=SimpleNamespace(amount_micros=30000000),
        metrics=SimpleNamespace(cost_micros=28750000, conversions=1.5),
    )
    envelope = {
        "schema_version": "1.0.0", "platform": "google", "customer_id": "1234567890",
        "login_customer_id": None, "api_version": "v26", "query_id": "campaign-daily-v1",
        "query": gaql_via_api.build_query("campaign", fields),
        "retrieved_at": "2026-11-01T08:00:00Z",
        "rows": [gaql_via_api.extract_row(row, fields)],
    }
    path = tmp_path / "live.json"
    path.write_text(json.dumps(envelope), encoding="utf-8")
    snapshot = GoogleAdsLiveReadAdapter("1234567890").read_snapshot(path)
    assert snapshot is not None


def test_direct_api_fixture_is_accepted_by_the_live_adapter():
    from claude_ads_core.adapters import GoogleAdsLiveReadAdapter

    fixture = SCRIPTS_DIR.parent / "tests" / "fixtures" / "live_reads" / "google-direct-api-campaign-daily.json"
    snapshot = GoogleAdsLiveReadAdapter("1234567890").read_snapshot(fixture)
    assert snapshot is not None
    payload = json.loads(fixture.read_text(encoding="utf-8"))
    assert payload["login_customer_id"] is None  # direct access, no manager header
    assert any(row["metrics.conversions"] == 0.0 for row in payload["rows"])  # zero is kept


# ------------------------------------------------- keyword script and wrapper


def test_keyword_script_no_longer_demands_a_developer_token(tmp_path, monkeypatch):
    source = (SCRIPTS_DIR / "keyword_ideas_via_api.py").read_text(encoding="utf-8")
    assert "DEVELOPER_TOKEN is not set" not in source
    monkeypatch.setattr(keyword_ideas_via_api, "ROOT", tmp_path)
    for name in adbot_env.ENV_KEYS + ("ADBOT_PROFILE_DIR", "GOOGLE_CLOUD_PROJECT"):
        monkeypatch.delenv(name, raising=False)
    argv = ["--customer", "1234567890", "--keywords", "beispiel", "--geo-target-constants", "2276",
            "--query-id", "q1", "--out", str(tmp_path / "out.json")]
    with pytest.raises(SystemExit) as exc:
        keyword_ideas_via_api.main(argv)
    message = str(exc.value)
    assert "GOOGLE_PROJECT_ID" in message  # asks for the project, not for a token
    assert "TOKEN" not in message


def _run_wrapper(tmp_path, extra_env, *, adc=True):
    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    env = {"PATH": os.environ["PATH"], "HOME": str(home), "ADBOT_DRY_RUN": "1"}
    env.update(extra_env)
    if adc:
        credentials = tmp_path / "adc.json"
        credentials.write_text("{}")
        env.setdefault("GOOGLE_APPLICATION_CREDENTIALS", str(credentials))
    return subprocess.run(["bash", str(WRAPPER)], env=env, capture_output=True, text=True, check=False)


def test_wrapper_starts_without_developer_token(tmp_path):
    result = _run_wrapper(tmp_path, {"GOOGLE_PROJECT_ID": "demo-project"})
    assert result.returncode == 0, result.stderr
    assert "configuration ok" in result.stdout


def test_wrapper_never_prints_secret_values(tmp_path):
    result = _run_wrapper(tmp_path, {"GOOGLE_PROJECT_ID": "demo-project", "DEVELOPER_TOKEN": FAKE_TOKEN})
    assert result.returncode == 0
    assert FAKE_TOKEN not in result.stdout + result.stderr


def test_wrapper_requires_project_and_credentials(tmp_path):
    no_project = _run_wrapper(tmp_path, {})
    assert no_project.returncode == 2
    assert "GOOGLE_PROJECT_ID" in no_project.stderr
    no_adc = _run_wrapper(tmp_path, {"GOOGLE_PROJECT_ID": "demo-project",
                                     "GOOGLE_APPLICATION_CREDENTIALS": str(tmp_path / "missing.json")}, adc=False)
    assert no_adc.returncode == 2
    assert "credentials file missing" in no_adc.stderr


def test_wrapper_reads_profile_env_file(tmp_path):
    profile = tmp_path / "profile"
    profile.mkdir()
    (profile / "env").write_text("GOOGLE_PROJECT_ID=from-profile\n")
    result = _run_wrapper(tmp_path, {"ADBOT_PROFILE_DIR": str(profile)})
    assert result.returncode == 0, result.stderr
