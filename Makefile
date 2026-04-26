# circuit-forge — local KiCad checks
# Usage: make check
#        make BOARD=my-board erc drc fab-drc

BOARD        ?= s3-dev-board
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

.PHONY: help versions erc drc fab-drc check clean

help:
	@echo "circuit-forge — KiCad local checks"
	@echo ""
	@echo "  make check            ERC + DRC + multi-fab DRC (default board: $(BOARD))"
	@echo "  make erc                Electrical Rules Check (schematic)"
	@echo "  make drc                Design Rules Check (board, project rules)"
	@echo "  make fab-drc            DRC against JLCPCB + PCBWay rule sets"
	@echo "  make clean              Remove report JSON under boards/<board>/"
	@echo "  make versions           Print kicad-cli version"
	@echo ""
	@echo "  make BOARD=other-board <target>   Run against another board"
	@echo "  KICAD_CLI=/path/to/kicad-cli make   Override CLI location"
	@echo ""

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
