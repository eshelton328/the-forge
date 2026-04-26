#!/usr/bin/env bash
# Emits a markdown PR comment summarizing KiCad design check results.
# Reads JSON reports under ARTIFACTS_DIR (from download-artifact).
# Expects: ERC_RESULT, DRC_RESULT, FAB_DRC_RESULT, and optionally GITHUB_RUN_URL.

set -euo pipefail

ARTIFACTS_DIR="${1:-ci-artifacts}"
if [ -n "${GITHUB_RUN_URL:-}" ]; then
  RUN_URL="$GITHUB_RUN_URL"
elif [ -n "${GITHUB_SERVER_URL:-}" ] && [ -n "${GITHUB_REPOSITORY:-}" ] && [ -n "${GITHUB_RUN_ID:-}" ]; then
  RUN_URL="${GITHUB_SERVER_URL}/${GITHUB_REPOSITORY}/actions/runs/${GITHUB_RUN_ID}"
else
  RUN_URL="(not in CI — set GITHUB_RUN_URL)"
fi

erc_result="${ERC_RESULT:-unknown}"
drc_result="${DRC_RESULT:-unknown}"
fab_drc_result="${FAB_DRC_RESULT:-unknown}"

if [ ! -d "$ARTIFACTS_DIR" ]; then
  ARTIFACTS_DIR="/tmp/empty-kicad-artifacts"
  mkdir -p "$ARTIFACTS_DIR"
fi

# download-artifact@v4 names subdirectories after the artifact.
# Strip the known prefix to recover the board name.
board_from_artifact_dir() {
  local dir_name="$1" prefix="$2"
  echo "${dir_name#"$prefix"}"
}

plural() { [ "$1" -ne 1 ] && echo s || true; }

# "N errors, M warnings" with severity icons, or "pass"
format_counts() {
  local errors="$1" warnings="$2" parts=""
  if [ "$errors" -gt 0 ]; then
    parts="🔴 ${errors} error$(plural "$errors")"
  fi
  if [ "$warnings" -gt 0 ]; then
    [ -n "$parts" ] && parts+=", "
    parts+="🟡 ${warnings} warning$(plural "$warnings")"
  fi
  [ -z "$parts" ] && echo "pass" || echo "$parts"
}

count_errors() {
  jq -r "[$1 | select(.severity == \"error\")] | length" "$2" 2>/dev/null || echo 0
}

count_warnings() {
  jq -r "[$1 | select(.severity == \"warning\")] | length" "$2" 2>/dev/null || echo 0
}

# Print violations grouped by type as blockquote-indented nested <details>.
# Errors sort before warnings. Shows up to 5 example violations per type.
# $1 = file, $2 = jq expression that yields an array of violation objects.
print_grouped() {
  local file="$1" jq_expr="$2"
  jq -r "${jq_expr}"'
    | group_by(.type)
    | sort_by(if .[0].severity == "error" then 0 else 1 end)
    | .[]
    | (if .[0].severity == "error" then "🔴"
       elif .[0].severity == "warning" then "🟡"
       else "⚪" end) as $icon
    | (if length == 1 then .[0].severity
       else .[0].severity + "s" end) as $sev
    | "<details>",
      "<summary>\($icon) <b><code>\(.[0].type)</code></b> — \(length) \($sev)</summary>",
      "",
      .[0].description,
      (.[0:5][] | select((.items // []) | length > 0)
        | "- " + ([.items[].description // "(no details)"] | map("`\(.)`") | join(" / "))),
      (if length > 5 then "", "*… and \(length - 5) more*" else empty end),
      "",
      "</details>",
      ""
  ' "$file" 2>/dev/null | sed 's/^/> /' || echo "> _Could not parse violations._"
}

# result_label <result_value>  →  "pass" / "failed (no report)" / "skipped" / …
result_label() {
  case "$1" in
    success) echo "pass" ;;
    failure) echo "_failed (no report)_" ;;
    skipped) echo "_skipped_" ;;
    *)       echo "_${1}_" ;;
  esac
}

TMPDIR_BOARDS=$(mktemp -d)
trap 'rm -rf "$TMPDIR_BOARDS"' EXIT

# Per-board temp files: $TMPDIR_BOARDS/<board>/summary and details
init_board() {
  local board="$1"
  local dir="$TMPDIR_BOARDS/$board"
  mkdir -p "$dir"
  touch "$dir/summary" "$dir/details"
}

# ===========================================================================
#  ERC
# ===========================================================================
erc_files=()
while IFS= read -r f; do
  [ -n "$f" ] && erc_files+=("$f")
done < <(find "$ARTIFACTS_DIR" -name 'erc.json' -type f 2>/dev/null | sort)

if [ "${#erc_files[@]}" -eq 0 ] && [ "$erc_result" != "skipped" ]; then
  : # no fallback row needed in per-board layout
else
  for f in "${erc_files[@]}"; do
    artifact_dir=$(basename "$(dirname "$f")")
    board=$(board_from_artifact_dir "$artifact_dir" "erc-")
    init_board "$board"

    all='.sheets[]? | .violations[]?'
    errors=$(count_errors "$all" "$f")
    warnings=$(count_warnings "$all" "$f")
    total=$((errors + warnings))

    echo "| ERC | $(format_counts "$errors" "$warnings") |" >> "$TMPDIR_BOARDS/$board/summary"

    if [ "$total" -gt 0 ]; then
      {
        echo "<details>"
        echo "<summary><strong>ERC</strong> — $(format_counts "$errors" "$warnings")</summary>"
        echo ""
        print_grouped "$f" '[.sheets[]? | .violations[]?]'
        echo "</details>"
        echo ""
      } >> "$TMPDIR_BOARDS/$board/details"
    fi
  done
fi

# ===========================================================================
#  DRC (default rules)
# ===========================================================================
drc_def_files=()
while IFS= read -r f; do
  [ -n "$f" ] && drc_def_files+=("$f")
done < <(find "$ARTIFACTS_DIR" -name 'drc-default.json' -type f 2>/dev/null | sort)

if [ "${#drc_def_files[@]}" -eq 0 ] && [ "$drc_result" != "skipped" ]; then
  : # no fallback row needed
else
  for f in "${drc_def_files[@]}"; do
    artifact_dir=$(basename "$(dirname "$f")")
    board=$(board_from_artifact_dir "$artifact_dir" "drc-default-")
    init_board "$board"

    all='(.violations // [])[]?, (.schematic_parity // [])[]?, (.unconnected_items // [])[]?'
    errors=$(count_errors "$all" "$f")
    warnings=$(count_warnings "$all" "$f")
    total=$((errors + warnings))

    echo "| DRC | $(format_counts "$errors" "$warnings") |" >> "$TMPDIR_BOARDS/$board/summary"

    if [ "$total" -gt 0 ]; then
      n_v=$(jq '(.violations // []) | length' "$f" 2>/dev/null || echo 0)
      n_s=$(jq '(.schematic_parity // []) | length' "$f" 2>/dev/null || echo 0)
      n_u=$(jq '(.unconnected_items // []) | length' "$f" 2>/dev/null || echo 0)

      {
        echo "<details>"
        echo "<summary><strong>DRC</strong> — $(format_counts "$errors" "$warnings")</summary>"
        echo ""

        if [ "$n_v" -gt 0 ]; then
          echo "> **Violations** ($n_v)"
          echo ">"
          print_grouped "$f" '[(.violations // [])[]?]'
        fi

        if [ "$n_s" -gt 0 ]; then
          echo "> **Schematic parity** ($n_s)"
          echo ">"
          print_grouped "$f" '[(.schematic_parity // [])[]?]'
        fi

        if [ "$n_u" -gt 0 ]; then
          echo "> **Unconnected items** ($n_u)"
          echo ">"
          print_grouped "$f" '[(.unconnected_items // [])[]?]'
        fi

        echo "</details>"
        echo ""
      } >> "$TMPDIR_BOARDS/$board/details"
    fi
  done
fi

# ===========================================================================
#  Fab DRC
# ===========================================================================
fab_files=()
while IFS= read -r f; do
  [ -n "$f" ] && fab_files+=("$f")
done < <(find "$ARTIFACTS_DIR" -name 'drc-fab-*.json' -type f 2>/dev/null | sort)

if [ "${#fab_files[@]}" -eq 0 ] && [ "$fab_drc_result" != "skipped" ]; then
  : # no fallback row needed
else
  for f in "${fab_files[@]}"; do
    artifact_dir=$(basename "$(dirname "$f")")
    board=$(board_from_artifact_dir "$artifact_dir" "drc-fabs-")
    fab_name=$(basename "$f" .json)
    fab_name="${fab_name#drc-fab-}"
    init_board "$board"

    all='(.violations // [])[]?'
    errors=$(count_errors "$all" "$f")
    warnings=$(count_warnings "$all" "$f")
    total=$((errors + warnings))

    echo "| Fab: ${fab_name} | $(format_counts "$errors" "$warnings") |" >> "$TMPDIR_BOARDS/$board/summary"

    if [ "$total" -gt 0 ]; then
      {
        echo "<details>"
        echo "<summary><strong>Fab DRC: ${fab_name}</strong> — $(format_counts "$errors" "$warnings")</summary>"
        echo ""
        print_grouped "$f" '[(.violations // [])[]?]'
        echo "</details>"
        echo ""
      } >> "$TMPDIR_BOARDS/$board/details"
    fi
  done
fi

# ===========================================================================
#  Assemble final output — grouped by board
# ===========================================================================
echo "### KiCad Design Checks"
echo ""
echo "[View workflow run]($RUN_URL)"
echo ""

all_skipped=true
for r in "$erc_result" "$drc_result" "$fab_drc_result"; do
  if [ "$r" != "skipped" ]; then
    all_skipped=false
    break
  fi
done

if [ "$all_skipped" = true ]; then
  echo "KiCad checks were **skipped** — no boards in scope for this diff."
else
  boards=()
  for d in "$TMPDIR_BOARDS"/*/; do
    [ -d "$d" ] && boards+=("$(basename "$d")")
  done
  mapfile -t boards < <(printf '%s\n' "${boards[@]}" | sort)

  if [ "${#boards[@]}" -eq 0 ]; then
    echo "All checks passed — no ERC, DRC, or fab-rule violations found."
  else
    has_issues=false
    for board in "${boards[@]}"; do
      if grep -qE '🔴|🟡' "$TMPDIR_BOARDS/$board/summary" 2>/dev/null; then
        has_issues=true
        break
      fi
    done

    if [ "$has_issues" = false ]; then
      echo "All checks passed — no ERC, DRC, or fab-rule violations found."
    else
      for board in "${boards[@]}"; do
        echo "#### \`${board}\`"
        echo ""
        echo "| Check | Result |"
        echo "|:------|:-------|"
        cat "$TMPDIR_BOARDS/$board/summary"
        echo ""

        if [ -s "$TMPDIR_BOARDS/$board/details" ]; then
          cat "$TMPDIR_BOARDS/$board/details"
        fi

        echo "---"
        echo ""
      done
    fi
  fi
fi

echo "_Updated by **KiCad Design Checks** on each push._"
