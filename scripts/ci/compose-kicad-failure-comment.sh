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

# "N errors, M warnings" with severity icons, or "pass"
format_counts() {
	local errors="$1" warnings="$2" parts=""
	if [ "$errors" -gt 0 ]; then
		parts="🔴 ${errors} error$([ "$errors" -ne 1 ] && echo s || true)"
	fi
	if [ "$warnings" -gt 0 ]; then
		[ -n "$parts" ] && parts+=", "
		parts+="🟡 ${warnings} warning$([ "$warnings" -ne 1 ] && echo s || true)"
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

SUMMARY_FILE=$(mktemp)
DETAILS_FILE=$(mktemp)
trap 'rm -f "$SUMMARY_FILE" "$DETAILS_FILE"' EXIT

# ===========================================================================
#  ERC
# ===========================================================================
erc_files=()
while IFS= read -r f; do
	[ -n "$f" ] && erc_files+=("$f")
done < <(find "$ARTIFACTS_DIR" -name 'erc.json' -type f 2>/dev/null | sort)

if [ "${#erc_files[@]}" -eq 0 ]; then
	echo "| ERC | — | $(result_label "$erc_result") |" >> "$SUMMARY_FILE"
else
	for f in "${erc_files[@]}"; do
		artifact_dir=$(basename "$(dirname "$f")")
		board=$(board_from_artifact_dir "$artifact_dir" "erc-")

		all='.sheets[]? | .violations[]?'
		errors=$(count_errors "$all" "$f")
		warnings=$(count_warnings "$all" "$f")
		total=$((errors + warnings))

		echo "| ERC | \`$board\` | $(format_counts "$errors" "$warnings") |" >> "$SUMMARY_FILE"

		if [ "$total" -gt 0 ]; then
			{
				echo "---"
				echo ""
				echo "<details>"
				echo "<summary><strong>ERC</strong> (${board}) — $(format_counts "$errors" "$warnings")</summary>"
				echo ""
				print_grouped "$f" '[.sheets[]? | .violations[]?]'
				echo "</details>"
				echo ""
			} >> "$DETAILS_FILE"
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

if [ "${#drc_def_files[@]}" -eq 0 ]; then
	echo "| DRC | — | $(result_label "$drc_result") |" >> "$SUMMARY_FILE"
else
	for f in "${drc_def_files[@]}"; do
		artifact_dir=$(basename "$(dirname "$f")")
		board=$(board_from_artifact_dir "$artifact_dir" "drc-default-")

		all='(.violations // [])[]?, (.schematic_parity // [])[]?, (.unconnected_items // [])[]?'
		errors=$(count_errors "$all" "$f")
		warnings=$(count_warnings "$all" "$f")
		total=$((errors + warnings))

		echo "| DRC | \`$board\` | $(format_counts "$errors" "$warnings") |" >> "$SUMMARY_FILE"

		if [ "$total" -gt 0 ]; then
			n_v=$(jq '(.violations // []) | length' "$f" 2>/dev/null || echo 0)
			n_s=$(jq '(.schematic_parity // []) | length' "$f" 2>/dev/null || echo 0)
			n_u=$(jq '(.unconnected_items // []) | length' "$f" 2>/dev/null || echo 0)

			{
				echo "---"
				echo ""
				echo "<details>"
				echo "<summary><strong>DRC</strong> (${board}) — $(format_counts "$errors" "$warnings")</summary>"
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
			} >> "$DETAILS_FILE"
		fi
	done
fi

# ===========================================================================
#  Fab DRC
# ===========================================================================
fab_files=()
while IFS= read -r f; do
	[ -n "$f" ] && fab_files+=("$f")
done < <(find "$ARTIFACTS_DIR" -name 'drc-*.json' ! -name 'drc-default.json' -type f 2>/dev/null | sort)

if [ "${#fab_files[@]}" -eq 0 ]; then
	echo "| Fab DRC | — | $(result_label "$fab_drc_result") |" >> "$SUMMARY_FILE"
else
	for f in "${fab_files[@]}"; do
		artifact_dir=$(basename "$(dirname "$f")")
		board=$(board_from_artifact_dir "$artifact_dir" "drc-fabs-")
		fab_name=$(basename "$f" .json)
		fab_name="${fab_name#drc-}"

		all='(.violations // [])[]?'
		errors=$(count_errors "$all" "$f")
		warnings=$(count_warnings "$all" "$f")
		total=$((errors + warnings))

		echo "| Fab: ${fab_name} | \`$board\` | $(format_counts "$errors" "$warnings") |" >> "$SUMMARY_FILE"

		if [ "$total" -gt 0 ]; then
			{
				echo "---"
				echo ""
				echo "<details>"
				echo "<summary><strong>Fab DRC: ${fab_name}</strong> (${board}) — $(format_counts "$errors" "$warnings")</summary>"
				echo ""
				print_grouped "$f" '[(.violations // [])[]?]'
				echo "</details>"
				echo ""
			} >> "$DETAILS_FILE"
		fi
	done
fi

# ===========================================================================
#  Assemble final output
# ===========================================================================
echo "### KiCad Design Checks"
echo ""
echo "[View workflow run]($RUN_URL)"
echo ""
echo "| Check | Board | Result |"
echo "|:------|:------|:-------|"
cat "$SUMMARY_FILE"

if [ -s "$DETAILS_FILE" ]; then
	echo ""
	cat "$DETAILS_FILE"
fi

echo ""
echo "---"
echo "_Updated by **KiCad Design Checks** on each push._"
