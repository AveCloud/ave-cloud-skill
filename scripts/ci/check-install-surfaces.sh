#!/usr/bin/env bash

set -euo pipefail

REPO_URL="https://github.com/AveCloud/ave-cloud-skill"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

overall_status=0
pass_count=0
fail_count=0

check_client() {
  local client_name="$1"
  shift

  local client_failed=0
  local check_type=""
  local rel_path=""
  local abs_path=""
  local messages=()
  local message=""

  while [[ "$#" -gt 0 ]]; do
    check_type="$1"
    rel_path="$2"
    shift 2

    abs_path="${REPO_ROOT}/${rel_path}"

    if [[ ! -f "${abs_path}" ]]; then
      messages+=("missing: ${rel_path}")
      client_failed=1
      continue
    fi

    if [[ "${check_type}" == "install_doc" ]] && ! grep -Fq "${REPO_URL}" "${abs_path}"; then
      messages+=("missing repo URL in: ${rel_path}")
      client_failed=1
    fi
  done

  if [[ "${client_failed}" -eq 0 ]]; then
    printf 'PASS %s\n' "${client_name}"
    pass_count=$((pass_count + 1))
    return
  fi

  printf 'FAIL %s\n' "${client_name}"
  for message in "${messages[@]}"; do
    printf '  %s\n' "${message}"
  done

  fail_count=$((fail_count + 1))
  overall_status=1
}

check_client \
  "Claude Code" \
  file ".claude-plugin/plugin.json" \
  file ".claude-plugin/marketplace.json"

check_client \
  "Codex" \
  install_doc ".codex/INSTALL.md" \
  install_doc ".codex/INSTALL.zh-CN.md"

check_client \
  "Cursor" \
  file ".cursor-plugin/plugin.json"

check_client \
  "OpenCode" \
  install_doc ".opencode/INSTALL.md" \
  install_doc ".opencode/INSTALL.zh-CN.md"

check_client \
  "OpenClaw" \
  install_doc ".openclaw/INSTALL.md" \
  install_doc ".openclaw/INSTALL.zh-CN.md"

printf '\nFinal summary: %d passed, %d failed\n' "${pass_count}" "${fail_count}"

if [[ "${overall_status}" -eq 0 ]]; then
  printf 'Install surface validation PASSED\n'
else
  printf 'Install surface validation FAILED\n'
fi

exit "${overall_status}"
