#!/usr/bin/env bash
# Start the official Google Ads MCP server with credentials from the environment, the profile
# file ($ADBOT_PROFILE_DIR/env) or the local .env.  Both files are git-ignored; this script
# never prints secret values.
#
# A developer token is OPTIONAL: Google sunset developer tokens on 2026-09-09 and the current
# MCP server no longer needs one.  If you still have one set, it is passed through unchanged.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# Read only the keys we need (never source a file: unrelated lines may not be shell-safe).
# Existing environment values win; the profile file is read before the repository .env.
load_env_key() {
  local key="$1" value file
  for file in "${ADBOT_PROFILE_DIR:+$ADBOT_PROFILE_DIR/env}" "$ROOT/.env"; do
    [ -n "$file" ] && [ -f "$file" ] || continue
    value="$( { grep -E "^${key}=" "$file" || true; } | tail -n1 | cut -d= -f2- | sed -e 's/^["'"'"']//' -e 's/["'"'"']$//' -e 's/[[:space:]]*$//')"
    if [ -n "$value" ] && [ -z "${!key:-}" ]; then
      export "$key=$value"
    fi
  done
}
for key in GOOGLE_PROJECT_ID GOOGLE_ADS_DEVELOPER_TOKEN DEVELOPER_TOKEN GOOGLE_ADS_LOGIN_CUSTOMER_ID GOOGLE_APPLICATION_CREDENTIALS; do
  load_env_key "$key"
done
export PATH="$HOME/.local/bin:$PATH"
# Optional legacy token: export it only when the user provided one.
token="${GOOGLE_ADS_DEVELOPER_TOKEN:-${DEVELOPER_TOKEN:-}}"
if [ -n "$token" ]; then export GOOGLE_ADS_DEVELOPER_TOKEN="$token"; fi
# Only set login-customer-id when the caller provides one (needed solely for manager-account access).
if [ -n "${GOOGLE_ADS_LOGIN_CUSTOMER_ID:-}" ]; then export GOOGLE_ADS_LOGIN_CUSTOMER_ID; fi
export GOOGLE_CLOUD_PROJECT="${GOOGLE_CLOUD_PROJECT:-${GOOGLE_PROJECT_ID:-}}"
export GOOGLE_APPLICATION_CREDENTIALS="${GOOGLE_APPLICATION_CREDENTIALS:-$HOME/.config/gcloud/application_default_credentials.json}"
if [ -z "${GOOGLE_PROJECT_ID:-}" ]; then
  echo "google_ads_mcp: GOOGLE_PROJECT_ID is not set (add it to \$ADBOT_PROFILE_DIR/env or $ROOT/.env)" >&2
  exit 2
fi
if [ ! -f "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
  echo "google_ads_mcp: credentials file missing: $GOOGLE_APPLICATION_CREDENTIALS (run gcloud auth application-default login)" >&2
  exit 2
fi
# ADBOT_DRY_RUN=1 stops before starting the server (used by tests and 'doctor').
if [ "${ADBOT_DRY_RUN:-0}" = "1" ]; then
  echo "google_ads_mcp: configuration ok (dry run)"
  exit 0
fi
# NOTE: this runs whatever is at the head of the upstream repository on the day it starts. The "read-only"
# statement (CLM-0210, CLM-0219) is a statement about that server at the date it was checked; pin a reviewed
# tag or commit here (git+https://...@<ref>) before relying on it for anything beyond reading.
exec pipx run --spec git+https://github.com/googleads/google-ads-mcp.git google-ads-mcp "$@"
