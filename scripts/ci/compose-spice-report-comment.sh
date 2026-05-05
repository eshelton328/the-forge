#!/usr/bin/env bash
# Emit markdown for a sticky PR comment summarizing SPICE runs (spice-checks workflow).
# Reads spice-report.metrics.json files under ARTIFACTS_DIR (from download-artifact).
#
# Env (optional):
#   GITHUB_RUN_URL — link shown at top
#   SPICE_BOARD_RESULT — needs.spice-board.result (success|failure|skipped)
#   SPICE_FIXTURE_RESULT — needs.spice-fixture.result
#   SPICE_DETECT_BOARDS — JSON array from detect-spice.outputs.boards
#   SPICE_RUN_FIXTURE — detect-spice.outputs.run_fixture (true|false)

set -euo pipefail

ROOT="${1:-spice-ci-artifacts}"
if [ -n "${GITHUB_RUN_URL:-}" ]; then
  RUN_URL="$GITHUB_RUN_URL"
elif [ -n "${GITHUB_SERVER_URL:-}" ] && [ -n "${GITHUB_REPOSITORY:-}" ] && [ -n "${GITHUB_RUN_ID:-}" ]; then
  RUN_URL="${GITHUB_SERVER_URL}/${GITHUB_REPOSITORY}/actions/runs/${GITHUB_RUN_ID}"
else
  RUN_URL="(set GITHUB_RUN_URL)"
fi

board_res="${SPICE_BOARD_RESULT:-unknown}"
fix_res="${SPICE_FIXTURE_RESULT:-unknown}"
detect_boards="${SPICE_DETECT_BOARDS:-[]}"
run_fix="${SPICE_RUN_FIXTURE:-false}"

result_cell() {
  case "$1" in
    success) echo "✅ pass" ;;
    failure) echo "❌ failed" ;;
    skipped) echo "_skipped_" ;;
    *) echo "_$1_" ;;
  esac
}

echo "### SPICE simulation"
echo ""
echo "[View this workflow run]($RUN_URL)"
echo ""

if [ "$detect_boards" = "[]" ] && [ "$run_fix" != "true" ]; then
  echo "_No SPICE runs for this diff: no opt-in \`sim.yml\` boards in scope and the RC fixture was not triggered._"
  echo ""
  echo "_Updated by **SPICE simulation** on each push._"
  exit 0
fi

echo "#### Workflow jobs"
echo ""
echo "| Job | Result |"
echo "|:----|:-------|"
echo "| \`spice-board\` | $(result_cell "$board_res") |"
echo "| \`spice-fixture\` | $(result_cell "$fix_res") |"
echo ""

if [ ! -d "$ROOT" ]; then
  mkdir -p "$ROOT"
fi

met_files=()
while IFS= read -r f; do
  [ -n "$f" ] && met_files+=("$f")
done < <(find "$ROOT" -name 'spice-report.metrics.json' -type f 2>/dev/null | sort || true)

if [ "${#met_files[@]}" -eq 0 ]; then
  echo "_No \`spice-report.metrics.json\` files were found in artifacts._"
  echo "If a job failed before ngspice finished, open the workflow run and inspect job logs or the \`spice-boards\` / \`spice-fixture-report\` artifacts."
  echo ""
  echo "_Updated by **SPICE simulation** on each push._"
  exit 0
fi

for jsonf in "${met_files[@]}"; do
  section_title=""
  if [[ "$jsonf" == *"/rc_divider/"* ]] || [[ "$jsonf" == *"rc_divider"* ]]; then
    section_title="RC divider fixture"
  else
    section_title="$(basename "$(dirname "$jsonf")")"
  fi

  echo "#### \`$section_title\`"
  echo ""

  overall=$(jq -r '.pass // false' "$jsonf" 2>/dev/null || echo "false")
  gen_at=$(jq -r '.generated_at // "—"' "$jsonf" 2>/dev/null || echo "—")
  schema=$(jq -r '.metrics_schema_version // "—"' "$jsonf" 2>/dev/null || echo "—")

  if [ "$overall" = "true" ]; then
    echo "**Overall:** ✅ PASS · schema v${schema} · generated \`$gen_at\`"
  else
    echo "**Overall:** ❌ FAIL · schema v${schema} · generated \`$gen_at\`"
  fi
  echo ""

  echo "| Scenario | Measure | Value | Bounds | Result |"
  echo "|:---------|:--------|:------|:-------|:-------|"
  jq -r '
    (.measures // [])[]
    | (
        if (.bounds_min == null and .bounds_max == null) then "—"
        elif (.bounds_min != null and .bounds_max != null) then "min \(.bounds_min), max \(.bounds_max)"
        elif (.bounds_min != null) then "min \(.bounds_min)"
        else "max \(.bounds_max)" end
      ) as $b
    | (if .passed == true then "PASS" elif .passed == false then "FAIL" else "—" end) as $r
    | "| \(.scenario_id) | \(.display_title // .measure_id) | \(.value_str // "—") | \($b) | **\($r)** |"
  ' "$jsonf" 2>/dev/null || echo "| _error_ | _could not parse measures_ | — | — | — |"

  echo ""
  echo "<details>"
  echo "<summary>Full markdown report (excerpt)</summary>"
  echo ""
  rep="${jsonf%.metrics.json}.md"
  if [ -f "$rep" ]; then
    echo '```'
    head -n 40 "$rep"
    lines=$(wc -l < "$rep" | tr -d "[:space:]")
    if [ "${lines:-0}" -gt 40 ] 2>/dev/null; then
      echo "…"
    fi
    echo '```'
  else
    echo "_No \`spice-report.md\` next to metrics in this artifact layout._"
  fi
  echo "</details>"
  echo ""
  echo "---"
  echo ""
done

echo "Full netlists and reports are available under workflow artifacts (**\`spice-boards\`**, **\`spice-fixture-report\`**)."
echo ""
echo "_Updated by **SPICE simulation** on each push._"
