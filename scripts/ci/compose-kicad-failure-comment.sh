#!/usr/bin/env bash
# Emits a markdown body for a PR comment when KiCad design checks fail.
# Reads uploaded JSON reports under ARTIFACTS_DIR (from download-artifact).
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

echo "### KiCad design checks failed"
echo ""
echo "Workflow run: $RUN_URL"
echo ""
echo "| Check | Outcome |"
echo "| --- | --- |"
echo "| ERC (schematic) | \`${erc_result}\` |"
echo "| DRC (default) | \`${drc_result}\` |"
echo "| DRC (fab rules) | \`${fab_drc_result}\` |"
echo ""
echo "#### Details from report files (when present)"
echo ""

print_erc_excerpt() {
	local file_path="$1"
	local board
	board=$(basename "$(dirname "$file_path")")
	local count
	count=$(jq -r '[.sheets[]? | .violations[]?] | length' "$file_path" 2>/dev/null || echo "0")
	echo "##### ERC — \`$board\`"
	if [ "$count" = "0" ] || [ -z "$count" ]; then
		echo "_No \`violations\` in JSON, or file unreadable. See the ERC job log._"
		echo ""
		return 0
	fi
	echo "- Violations in report: **$count**"
	local show
	show=10
	if [ "$count" -gt "$show" ]; then
		jq -r --argjson lim "$show" '
			[.sheets[]? | .violations[]?] | .[0:$lim][]
			| "- (" + .severity + ") " + .type + " — " + .description
		' "$file_path" 2>/dev/null || echo "- _Could not list violations (parse error)._"
		local extra
		extra=$((count - show))
		echo "- _… and $extra more_"
	else
		jq -r '
			[.sheets[]? | .violations[]?][]
			| "- (" + .severity + ") " + .type + " — " + .description
		' "$file_path" 2>/dev/null || echo "- _Could not list violations (parse error)._"
	fi
	echo ""
}

print_drc_default_excerpt() {
	local file_path="$1"
	local board
	board=$(basename "$(dirname "$file_path")")
	local n_v n_u n_s
	n_v=$(jq '(.violations // []) | length' "$file_path" 2>/dev/null || echo 0)
	n_s=$(jq '(.schematic_parity // []) | length' "$file_path" 2>/dev/null || echo 0)
	n_u=$(jq '(.unconnected_items // []) | length' "$file_path" 2>/dev/null || echo 0)
	echo "##### DRC (default) — \`$board\`"
	if [ "$n_v" = "0" ] && [ "$n_s" = "0" ] && [ "$n_u" = "0" ]; then
		echo "_No DRC \`violations\` in JSON, or file unreadable. See the DRC job log._"
		echo ""
		return 0
	fi
	echo "- violations: **$n_v**, schematic_parity: **$n_s**, unconnected_items: **$n_u**"
	local total
	total=$(jq '[(.violations // [])[]?, (.schematic_parity // [])[]?, (.unconnected_items // [])[]?] | length' "$file_path" 2>/dev/null || echo 0)
	local show
	show=10
	if [ "$total" -gt "$show" ]; then
		jq -r --argjson lim "$show" '[(.violations // [])[]?, (.schematic_parity // [])[]?, (.unconnected_items // [])[]?] | .[0:$lim][]
			| "- (" + .severity + ") " + .type + " — " + .description' "$file_path" 2>/dev/null || echo "- _Could not list DRC items (parse error)._"
		local extra
		extra=$((total - show))
		echo "- _… and $extra more_"
	else
		jq -r '[(.violations // [])[]?, (.schematic_parity // [])[]?, (.unconnected_items // [])[]?][]
			| "- (" + .severity + ") " + .type + " — " + .description' "$file_path" 2>/dev/null || echo "- _Could not list DRC items (parse error)._"
	fi
	echo ""
}

print_fab_excerpt() {
	local file_path="$1"
	local board
	board=$(basename "$(dirname "$file_path")")
	local name
	name=$(basename "$file_path" .json)
	local n
	n=$(jq '(.violations // []) | length' "$file_path" 2>/dev/null || echo 0)
	echo "##### Fab DRC — \`$board\` / \`$name\`"
	if [ "$n" = "0" ]; then
		echo "_No \`violations\` in JSON, or file unreadable. See the fab-drc job log._"
		echo ""
		return 0
	fi
	echo "- violations in report: **$n**"
	local show
	show=10
	if [ "$n" -gt "$show" ]; then
		jq -r --argjson lim "$show" '(.violations // []) | .[0:$lim][]
			| "- (" + .severity + ") " + .type + " — " + .description' "$file_path" 2>/dev/null || echo "- _Could not list violations (parse error)._"
		local extra
		extra=$((n - show))
		echo "- _… and $extra more_"
	else
		jq -r '(.violations // [])[] | "- (" + .severity + ") " + .type + " — " + .description' "$file_path" 2>/dev/null || echo "- _Could not list violations (parse error)._"
	fi
	echo ""
}

erc_files=()
while IFS= read -r f; do
	[ -n "$f" ] && erc_files+=("$f")
done < <(find "$ARTIFACTS_DIR" -name 'erc.json' -type f 2>/dev/null | sort)

if [ "${#erc_files[@]}" -eq 0 ]; then
	echo "_No \`erc.json\` artifacts found (job may have failed before upload)._"
	echo ""
else
	for f in "${erc_files[@]}"; do
		print_erc_excerpt "$f"
	done
fi

drc_def_files=()
while IFS= read -r f; do
	[ -n "$f" ] && drc_def_files+=("$f")
done < <(find "$ARTIFACTS_DIR" -name 'drc-default.json' -type f 2>/dev/null | sort)

if [ "${#drc_def_files[@]}" -eq 0 ]; then
	echo "_No \`drc-default.json\` artifacts found._"
	echo ""
else
	for f in "${drc_def_files[@]}"; do
		print_drc_default_excerpt "$f"
	done
fi

# Fab: drc-<fab>.json but not drc-default.json
fab_files=()
while IFS= read -r f; do
	[ -n "$f" ] && fab_files+=("$f")
done < <(find "$ARTIFACTS_DIR" -name 'drc-*.json' ! -name 'drc-default.json' -type f 2>/dev/null | sort)

if [ "${#fab_files[@]}" -eq 0 ]; then
	echo "_No fab \`drc-*.json\` artifacts found._"
	echo ""
else
	for f in "${fab_files[@]}"; do
		print_fab_excerpt "$f"
	done
fi

echo ""
echo "— _Comment from workflow \`KiCad Design Checks\` (updates on the next run)._"
