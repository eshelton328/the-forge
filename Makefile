# circuit-forge — local KiCad checks
#
# One board at a time: set BOARD (directory name under boards/), or rely on
# default BOARD. Nothing here loops all boards unless you use `make check-all`.
# Examples:
#   make check                      # same as BOARD=$(DEFAULT_BOARD)
#   make drc BOARD=feather-datalogger
#   make list-boards

DEFAULT_BOARD := s3-dev-board
BOARD         ?= $(DEFAULT_BOARD)
BOARD_DIR    := boards/$(BOARD)
SCH          := $(BOARD_DIR)/$(BOARD).kicad_sch
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

.PHONY: help versions erc drc fab-drc check clean list-boards check-all

help:
	@echo "circuit-forge — KiCad local checks (one board per command)"
	@echo ""
	@echo "  BOARD=$(DEFAULT_BOARD)   # current default; override: make drc BOARD=name"
	@echo ""
	@echo "  make list-boards      Show directories under boards/"
	@echo "  make check            ERC + DRC + multi-fab DRC for ONE board"
	@echo "  make erc                Electrical Rules Check (schematic)"
	@echo "  make drc                Design Rules Check (board, project rules)"
	@echo "  make fab-drc            DRC with JLCPCB + PCBWay fab-rules/"
	@echo "  make clean              Remove report JSON for that board"
	@echo "  make versions           Print kicad-cli version"
	@echo "  make check-all          Run make check for every board (optional sweep)"
	@echo ""
	@echo "  make drc BOARD=other   Point at boards/other/other.kicad_*"
	@echo "  KICAD_CLI=...  make     Override kicad-cli path"
	@echo ""

list-boards:
	@echo "Boards (use BOARD=<name>):"
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
	$(KICAD_CLI) pcb drc --exit-code-violations --refill-zones \
		--format json -o $(DRC_JSON) \
		$(PCB)
	@echo "OK: DRC — report: $(DRC_JSON)"

fab-drc: $(PCB) $(BOARD_DIR)/board.yml
	$(FAB_SCRIPT) $(BOARD_DIR)
	@echo "OK: multi-fab DRC (see drc-*.json under $(BOARD_DIR))"

check: erc drc fab-drc
	@echo ""
	@echo "All checks passed for $(BOARD)."

clean:
	rm -f $(ERC_JSON) $(DRC_JSON) $(BOARD_DIR)/drc-*.json

# Run the full check sequence for each subdirectory of boards/ (for release prep / CI-like local runs)
check-all:
	@set -e; for d in boards/*/; do \
		b=$$(basename "$$d"); \
		test -f "$$d/$$b.kicad_pcb" || { echo "skip: $$b (no $$b.kicad_pcb)"; continue; }; \
		echo "========== check: $$b =========="; \
		$(MAKE) check BOARD=$$b; \
	done; \
	echo "check-all: all boards passed."
