#!/usr/bin/env bash
# Start the official Google Ads MCP server with credentials from the local .env.
# The .env is git-ignored; this script never prints secret values.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# Read only the keys we need from .env (never source it: unrelated lines may not be shell-safe).
load_env_key() {
  local key="$1" value
  [ -f "$ROOT/.env" ] || return 0
  value="$( { grep -E "^${key}=" "$ROOT/.env" || true; } | tail -n1 | cut -d= -f2- | sed -e 's/^["'"'"']//' -e 's/["'"'"']$//' -e 's/[[:space:]]*$//')"
  if [ -n "$value" ] && [ -z "${!key:-}" ]; then
    export "$key=$value"
  fi
}
for key in GOOGLE_PROJECT_ID GOOGLE_ADS_DEVELOPER_TOKEN DEVELOPER_TOKEN GOOGLE_ADS_LOGIN_CUSTOMER_ID GOOGLE_APPLICATION_CREDENTIALS; do
  load_env_key "$key"
done
export PATH="$HOME/.local/bin:$PATH"
export GOOGLE_ADS_DEVELOPER_TOKEN="${GOOGLE_ADS_DEVELOPER_TOKEN:-${DEVELOPER_TOKEN:-}}"
# Only set login-customer-id when the caller provides one (needed solely for MCC-linked accounts).
if [ -n "${GOOGLE_ADS_LOGIN_CUSTOMER_ID:-}" ]; then export GOOGLE_ADS_LOGIN_CUSTOMER_ID; fi
export GOOGLE_CLOUD_PROJECT="${GOOGLE_CLOUD_PROJECT:-${GOOGLE_PROJECT_ID:-}}"
export GOOGLE_APPLICATION_CREDENTIALS="${GOOGLE_APPLICATION_CREDENTIALS:-$HOME/.config/gcloud/application_default_credentials.json}"
for var in GOOGLE_PROJECT_ID GOOGLE_ADS_DEVELOPER_TOKEN; do
  if [ -z "${!var:-}" ]; then
    echo "google_ads_mcp: $var is not set (add it to $ROOT/.env)" >&2
    exit 2
  fi
done
if [ ! -f "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
  echo "google_ads_mcp: credentials file missing: $GOOGLE_APPLICATION_CREDENTIALS (run gcloud auth application-default login)" >&2
  exit 2
fi
exec pipx run --spec git+https://github.com/googleads/google-ads-mcp.git google-ads-mcp "$@"
