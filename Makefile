# the-forge — local KiCad checks
#
# One board at a time. Pick the board in either form:
#   make drc BOARD=my-board
#   make drc my-board
# (Second form: second word = board name; also works for erc, fab-drc, check, clean.)
# Nothing loops all boards unless you use `make check-all`.

DEFAULT_BOARD     := esp32s3-devkit
MAKE_GOAL_1       := $(word 1,$(MAKECMDGOALS))
MAKE_GOAL_2       := $(word 2,$(MAKECMDGOALS))
BOARD_TAKES_GOAL2 := erc drc fab-drc check clean validate board-images

ifeq ($(words $(MAKECMDGOALS)),2)
  ifneq ($(filter $(MAKE_GOAL_1),$(BOARD_TAKES_GOAL2)),)
    # `make drc esp32s3-devkit` — second "target" is really the board name
    override BOARD := $(MAKE_GOAL_2)
    BOARD_NOOP     := $(MAKE_GOAL_2)
  endif
endif

BOARD        ?= $(DEFAULT_BOARD)
BOARD_DIR    := boards/$(BOARD)
SCH          := $(BOARD_DIR)/$(BOARD).kicad_sch
# Pinned image — keep digest in sync with .github/workflows/pr-checks.yml
KICAD_IMAGE  ?= kicad/kicad:10.0@sha256:feb600e931ca7ad8ae684566131edbea32218cb90ab54bb2ea0944cee257eea6
PCB          := $(BOARD_DIR)/$(BOARD).kicad_pcb
FAB_SCRIPT   := scripts/run-drc-all-fabs.sh

# Prefer kicad-cli on PATH; on macOS fall back to the default .app bundle location
ifndef KICAD_CLI
  KICAD_CLI := $(shell command -v kicad-cli 2>/dev/null)
  ifeq ($(KICAD_CLI),)
    ifeq ($(shell uname -s),Darwin)
      KICAD_CLI := /Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli
    else
      KICAD_CLI := kicad-cli
    endif
  endif
endif

ERC_JSON     := $(BOARD_DIR)/erc.json
DRC_JSON     := $(BOARD_DIR)/drc-default.json

# Consume the second goal so `make drc my-board` does not look for a missing rule
ifdef BOARD_NOOP
.PHONY: $(BOARD_NOOP)
$(BOARD_NOOP):
	@:
endif

.PHONY: help versions erc drc fab-drc check clean list-boards check-all validate validate-all update-readmes board-images sim-fixture sim-export-board sim-board

help:
	@echo "the-forge — KiCad local checks (one board per command)"
	@echo ""
	@echo "  default BOARD: $(DEFAULT_BOARD)"
	@echo ""
	@echo "  make list-boards      Show board names (folders under boards/)"
	@echo "  make check            ERC + DRC + multi-fab DRC for ONE board"
	@echo "  make erc|drc|fab-drc|check|clean   — same, one board at a time"
	@echo "  make versions"
	@echo "  make validate         Board-level checks (checks.yml)"
	@echo "  make validate-all     Run \`make validate\` for every board"
	@echo "  make board-images     Generate docs/ images (schematic, PCB, 3D)"
	@echo "  make update-readmes   Regenerate validation summaries in board READMEs"
	@echo "  make check-all        Run \`make check\` for every board"
	@echo "  make sim-fixture      Run ngspice smoke (sim/fixtures/rc_divider) — requires ngspice on PATH"
	@echo "  make sim-export-board Export KiCad schematic → sim/kicad_export.cir (Docker + KICAD_IMAGE)"
	@echo "  make sim-board        Export + ngspice for BOARD (default tps63070-breakout) — Docker + ngspice"
	@echo ""
	@echo "  Choose the board in either way:"
	@echo "    make drc BOARD=name"
	@echo "    make drc name              # name = second word (short form)"
	@echo ""
	@echo "  KICAD_CLI=...  make          Override kicad-cli path"
	@echo ""

list-boards:
	@echo "Boards:"
	@for d in boards/*/; do \
		test -d "$$d" || continue; \
		echo "  $$(basename "$$d")"; \
	done
	@echo "(folder name must match the .kicad_pro / .kicad_sch / .kicad_pcb base name)"

versions:
	$(KICAD_CLI) version

erc: $(SCH)
	@command -v "$(KICAD_CLI)" >/dev/null 2>&1 || { echo "kicad-cli not found. Set KICAD_CLI=... or add KiCad to PATH."; exit 1; }
	$(KICAD_CLI) sch erc --exit-code-violations \
		--format json -o $(ERC_JSON) \
		$(SCH)
	@echo "OK: ERC — report: $(ERC_JSON)"

drc: $(PCB)
	@command -v "$(KICAD_CLI)" >/dev/null 2>&1 || { echo "kicad-cli not found. Set KICAD_CLI=... or add KiCad to PATH."; exit 1; }
	$(KICAD_CLI) pcb drc --exit-code-violations --refill-zones --schematic-parity \
		--format json -o $(DRC_JSON) \
		$(PCB)
	@echo "OK: DRC — report: $(DRC_JSON) (incl. schematic parity)"

fab-drc: $(PCB) $(BOARD_DIR)/board.yml
	$(FAB_SCRIPT) $(BOARD_DIR)
	@echo "OK: multi-fab DRC (see drc-*.json under $(BOARD_DIR))"

check: erc drc fab-drc
	@echo ""
	@echo "All checks passed for $(BOARD)."

clean:
	rm -f $(ERC_JSON) $(DRC_JSON) $(BOARD_DIR)/drc-*.json

validate:
	python3 scripts/validate_board.py $(BOARD_DIR)

validate-all:
	@set -e; for d in boards/*/; do \
		b=$$(basename "$$d"); \
		test -f "$$d/checks.yml" || { echo "skip: $$b (no checks.yml)"; continue; }; \
		echo "========== validate: $$b =========="; \
		python3 scripts/validate_board.py "$$d"; \
	done; \
	echo "validate-all: all boards passed."

board-images:
	bash scripts/ci/generate-board-images.sh $(BOARD_DIR)

update-readmes:
	python3 scripts/ci/update-board-readmes.py

# Run the full check sequence for each subdirectory of boards/ (for release prep / CI-like local runs)
# Homebrew dirs are prepended — `make` often runs with a minimal PATH (no `/opt/homebrew/bin`).
sim-fixture:
	@PATH="$$PATH:/opt/homebrew/bin:/usr/local/bin"; \
	command -v ngspice >/dev/null 2>&1 || \
	{ echo "ngspice not found — brew install ngspice or set NGSPICE=/path/to/ngspice"; exit 1; }; \
	PATH="$$PATH:/opt/homebrew/bin:/usr/local/bin"; \
	python3 scripts/sim/run_sim.py --config sim/fixtures/rc_divider/sim.yml --report sim/fixtures/rc_divider/spice-report.md
	@echo OK: Spice fixture report written to sim/fixtures/rc_divider/spice-report.md (+ spice-report.metrics.json)

# KiCad SPICE netlist → boards/<BOARD>/sim/kicad_export.cir (issue #46). Same Docker pattern as ERC in pr-checks.yml.
sim-export-board:
	@set -euo pipefail; \
	command -v docker >/dev/null 2>&1 || { echo "docker required — install Docker or run kicad-cli locally and export by hand"; exit 1; }; \
	docker run --rm \
		--user "$$(id -u):$$(id -g)" \
		-e HOME=/workspace/.kicad-ci-home \
		-v "$$PWD:/workspace" \
		-w /workspace \
		"$(KICAD_IMAGE)" \
		bash -c '\
			source /workspace/scripts/ci/setup-kicad-env.sh && \
			python3 /workspace/scripts/sim/export_kicad_spice.py --board-dir /workspace/$(BOARD_DIR) \
		'

sim-board: sim-export-board
	@PATH="$$PATH:/opt/homebrew/bin:/usr/local/bin"; \
	command -v ngspice >/dev/null 2>&1 || \
	{ echo "ngspice not found — brew install ngspice or set NGSPICE=/path/to/ngspice"; exit 1; }; \
	test -f $(BOARD_DIR)/sim.yml || { echo "no $(BOARD_DIR)/sim.yml — pick a board with sim.yml"; exit 1; }; \
	PATH="$$PATH:/opt/homebrew/bin:/usr/local/bin"; \
	python3 scripts/sim/run_sim.py --config $(BOARD_DIR)/sim.yml --report $(BOARD_DIR)/docs/spice-report.md
	@echo OK: Board spice report written to $(BOARD_DIR)/docs/spice-report.md (+ spice-report.metrics.json)

check-all:
	@set -e; for d in boards/*/; do \
		b=$$(basename "$$d"); \
		test -f "$$d/$$b.kicad_pcb" || { echo "skip: $$b (no $$b.kicad_pcb)"; continue; }; \
		echo "========== check: $$b =========="; \
		$(MAKE) check BOARD=$$b; \
	done; \
	echo "check-all: all boards passed."
