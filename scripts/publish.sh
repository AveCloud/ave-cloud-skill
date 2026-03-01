#!/usr/bin/env bash
# Publish ave-cloud skill to clawhub.ai
# Usage: ./scripts/publish.sh [--version VERSION] [--changelog CHANGELOG]
# Auth:  export CLAWHUB_TOKEN="clh_xxxx"  (from clawhub.ai → Settings → API Tokens)

set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILL_SLUG="ave-cloud"
SKILL_NAME="AVE Cloud Data API"
SKILL_VERSION="1.0.0"
SKILL_CHANGELOG=""

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --version)  SKILL_VERSION="$2"; shift 2 ;;
    --changelog) SKILL_CHANGELOG="$2"; shift 2 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

# Check Node.js
if ! command -v node &>/dev/null; then
  echo "Error: Node.js >=20 is required. Install from https://nodejs.org" >&2
  exit 1
fi

NODE_MAJOR=$(node -e "process.stdout.write(process.version.slice(1).split('.')[0])")
if [[ "$NODE_MAJOR" -lt 20 ]]; then
  echo "Error: Node.js >=20 required (found v${NODE_MAJOR})" >&2
  exit 1
fi

# Install clawhub CLI if missing
if ! command -v clawhub &>/dev/null; then
  echo "Installing clawhub CLI..."
  npm install -g clawhub
fi

# Authenticate
if [[ -n "${CLAWHUB_TOKEN:-}" ]]; then
  echo "Using CLAWHUB_TOKEN from environment."
else
  # Check if already logged in via config
  CONFIG_PATH="${CLAWHUB_CONFIG_PATH:-$HOME/Library/Application Support/clawhub/config.json}"
  if [[ ! -f "$CONFIG_PATH" ]]; then
    echo "No CLAWHUB_TOKEN set and no config found."
    echo "Run: export CLAWHUB_TOKEN=\"clh_xxxx\"  (get token from clawhub.ai → Settings → API Tokens)"
    echo "Or run: clawhub login"
    exit 1
  fi
fi

# Build publish command
PUBLISH_ARGS=(
  publish "$SKILL_DIR"
  --slug "$SKILL_SLUG"
  --name "$SKILL_NAME"
  --version "$SKILL_VERSION"
)
if [[ -n "$SKILL_CHANGELOG" ]]; then
  PUBLISH_ARGS+=(--changelog "$SKILL_CHANGELOG")
fi

echo "Publishing ${SKILL_SLUG} v${SKILL_VERSION} to clawhub.ai..."
clawhub "${PUBLISH_ARGS[@]}"
echo "Done. View at: https://clawhub.ai/skills/${SKILL_SLUG}"
