#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

PASS_COUNT=0
FAIL_COUNT=0
OVERALL_STATUS=0

run_check() {
  local name="$1"
  shift

  if "$@"; then
    printf 'PASS: %s\n' "$name"
    PASS_COUNT=$((PASS_COUNT + 1))
  else
    printf 'FAIL: %s\n' "$name"
    FAIL_COUNT=$((FAIL_COUNT + 1))
    OVERALL_STATUS=1
  fi
}

check_json_validation() {
  local failed=0
  local file
  local files=(
    ".claude-plugin/plugin.json"
    ".claude-plugin/marketplace.json"
    ".cursor-plugin/plugin.json"
  )

  for file in "${files[@]}"; do
    if [[ ! -f "$file" ]]; then
      printf '  Missing JSON file: %s\n' "$file"
      failed=1
      continue
    fi

    if ! python3 -m json.tool "$file" >/dev/null 2>&1; then
      printf '  Malformed JSON: %s\n' "$file"
      failed=1
    fi
  done

  if (( failed != 0 )); then
    return 1
  fi

  return 0
}

check_openai_yaml_exists() {
  local failed=0
  local found=0
  local skill_dir

  while IFS= read -r skill_dir; do
    found=1
    if [[ ! -f "$skill_dir/agents/openai.yaml" ]]; then
      printf '  Missing agents/openai.yaml: %s\n' "$skill_dir/agents/openai.yaml"
      failed=1
    fi
  done < <(find skills -mindepth 1 -maxdepth 1 -type d | sort)

  if (( found == 0 )); then
    printf '  No skill directories found under skills/\n'
    failed=1
  fi

  if (( failed != 0 )); then
    return 1
  fi

  return 0
}

extract_json_versions() {
  local file="$1"

  python3 - "$file" <<'PY'
import json
import sys

path = sys.argv[1]

with open(path, "r", encoding="utf-8") as handle:
    data = json.load(handle)

def walk(node):
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "version" and isinstance(value, str):
                print(value)
            walk(value)
    elif isinstance(node, list):
        for item in node:
            walk(item)

walk(data)
PY
}

check_version_consistency() {
  local failed=0
  local expected_version=""
  local mismatch=0
  local skill_file
  local json_file
  local version
  local json_versions
  local -a entries=()

  while IFS= read -r skill_file; do
    version="$(awk '
      /^version:[[:space:]]*/ {
        sub(/^version:[[:space:]]*/, "", $0)
        gsub(/^["'"'"']|["'"'"']$/, "", $0)
        print $0
        exit
      }
    ' "$skill_file")"

    if [[ -z "$version" ]]; then
      printf '  Missing version line in %s\n' "$skill_file"
      failed=1
      continue
    fi

    entries+=("$skill_file=$version")
    if [[ -z "$expected_version" ]]; then
      expected_version="$version"
    elif [[ "$version" != "$expected_version" ]]; then
      mismatch=1
    fi
  done < <(find skills -type f -name SKILL.md | sort)

  for json_file in \
    ".claude-plugin/plugin.json" \
    ".claude-plugin/marketplace.json" \
    ".cursor-plugin/plugin.json"; do
    if [[ ! -f "$json_file" ]]; then
      printf '  Missing JSON file for version check: %s\n' "$json_file"
      failed=1
      continue
    fi

    if ! json_versions="$(extract_json_versions "$json_file")"; then
      printf '  Unable to parse version fields from %s\n' "$json_file"
      failed=1
      continue
    fi

    if [[ -z "$json_versions" ]]; then
      printf '  No version field found in %s\n' "$json_file"
      failed=1
      continue
    fi

    while IFS= read -r version; do
      [[ -z "$version" ]] && continue
      entries+=("$json_file=$version")
      if [[ -z "$expected_version" ]]; then
        expected_version="$version"
      elif [[ "$version" != "$expected_version" ]]; then
        mismatch=1
      fi
    done <<< "$json_versions"
  done

  if ((${#entries[@]} == 0)); then
    printf '  No version declarations were found in SKILL.md or plugin JSON files\n'
    failed=1
  fi

  if (( mismatch != 0 )); then
    printf '  Version mismatch detected:\n'
    for version in "${entries[@]}"; do
      printf '  %s\n' "$version"
    done
    failed=1
  fi

  if (( failed != 0 )); then
    return 1
  fi

  return 0
}

check_bilingual_pairs() {
  local failed=0
  local pair
  local english_file
  local chinese_file
  local pairs=(
    "README.md|README.zh-CN.md"
    "AGENTS.md|AGENTS.zh-CN.md"
    "skills/README.md|skills/README.zh-CN.md"
    ".openclaw/INSTALL.md|.openclaw/INSTALL.zh-CN.md"
    ".codex/INSTALL.md|.codex/INSTALL.zh-CN.md"
    ".opencode/INSTALL.md|.opencode/INSTALL.zh-CN.md"
  )

  for pair in "${pairs[@]}"; do
    english_file="${pair%%|*}"
    chinese_file="${pair#*|}"

    if [[ ! -f "$english_file" ]]; then
      printf '  Missing file: %s\n' "$english_file"
      failed=1
    fi

    if [[ ! -f "$chinese_file" ]]; then
      printf '  Missing file: %s\n' "$chinese_file"
      failed=1
    fi
  done

  if (( failed != 0 )); then
    return 1
  fi

  return 0
}

check_credential_leak() {
  local failed=0
  local file
  local credential_hits=""
  local pattern='(^|[[:space:]])(export[[:space:]]+)?AVE_[A-Z0-9_]*(API|SECRET|ACCESS|PRIVATE|TOKEN|KEY)[A-Z0-9_]*[[:space:]]*[:=][[:space:]]*["'"'"'"'"'"'"'"'"'][A-Za-z0-9]{20,}["'"'"'"'"'"'"'"'"']'
  local -a files=()

  while IFS= read -r file; do
    files+=("$file")
  done < <(find . -path './.git' -prune -o -type f -print | sort)

  if ((${#files[@]} > 0)); then
    credential_hits="$(grep -nE -I "$pattern" "${files[@]}" || true)"
  fi

  if [[ -n "$credential_hits" ]]; then
    printf '  Potential credential leak(s) found:\n'
    while IFS= read -r file; do
      [[ -z "$file" ]] && continue
      printf '  %s\n' "$file"
    done <<< "$credential_hits"
    failed=1
  fi

  if (( failed != 0 )); then
    return 1
  fi

  return 0
}

run_check "JSON VALIDATION" check_json_validation
run_check "OPENAI.YAML EXISTS" check_openai_yaml_exists
run_check "VERSION CONSISTENCY" check_version_consistency
run_check "BILINGUAL PAIRS" check_bilingual_pairs
run_check "CREDENTIAL LEAK" check_credential_leak

printf '\n'
if (( OVERALL_STATUS == 0 )); then
  printf 'FINAL SUMMARY: PASS (%d checks passed)\n' "$PASS_COUNT"
else
  printf 'FINAL SUMMARY: FAIL (%d passed, %d failed)\n' "$PASS_COUNT" "$FAIL_COUNT"
fi

exit "$OVERALL_STATUS"
