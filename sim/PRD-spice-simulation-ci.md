# PRD: Schematic and layout-aware SPICE simulation in CI

Tracking issue: https://github.com/eshelton328/the-forge/issues/43

---

## Problem Statement

Hardware designs in this repository are validated with ERC, DRC, fab rules, and YAML-driven board checks, but there is no automated, repeatable way to run ngspice against a design, enforce numerical limits, and produce reviewable reports in CI. The team wants a single roadmap that starts with schematic-accurate simulation and converges on including PCB-relevant effects via a versioned parasitic overlay, without redesigning the pipeline at each step. Today, discussion and partial planning exist, but there is no end-to-end runner, no per-board opt-in contract, and no CI job that exports a netlist and fails loudly (while merge policy remains relaxed until confidence is high).

## Solution

Provide a shared simulation pipeline that: (1) regenerates the Spice netlist from the canonical KiCad schematic in CI; (2) always includes a board-local overlay file (stub first) so parasitic evolution is explicit in version control; (3) references vendor device models from a central, documented library store; (4) runs ngspice in batch mode, evaluates configured measures against limits, emits a human-readable report and optional machine-readable footer; (5) integrates with pull-request workflows using the same “which boards changed” detection philosophy as existing checks; (6) targets a sustainable toolchain where KiCad tooling and ngspice are pinned together in a derived container image for long-term reproducibility, while allowing a shorter bootstrap path if needed.

## User Stories

1. As a **board designer**, I want simulation runs tied to my schematic export, so that **what CI simulates matches what I edit in KiCad**.
2. As a **board designer**, I want a **checked-in parasitic overlay stub** that is always included, so that **when I add series L/R/C for hot loops, reviewers see a clear diff**.
3. As a **maintainer**, I want **one orchestration entry point** per board run, so that **adding boards does not fork copy-pasted scripts**.
4. As a **maintainer**, I want **vendor Spice models stored in-repo with provenance**, so that **runs are reproducible and offline**.
5. As a **contributor**, I want **clear failure output** when a limit is exceeded, so that **I fix the schematic or limits without guessing**.
6. As a **contributor**, I want **reports uploaded as CI artifacts**, so that **I can inspect plots and logs without running locally**.
7. As a **repo owner**, I want **simulation failures to surface as failed jobs**, so that **PRs visibly break when limits fail**.
8. As a **repo owner**, I want **merge-blocking to remain optional initially**, so that **flaky vendor models do not stall unrelated layout work**.
9. As a **reviewer**, I want **a markdown summary** comparable to baseline metrics, so that **I can judge regressions at a glance**.
10. As a **reviewer**, I want optional **comparison to a baseline from the default branch**, so that **small metric drift is surfaced**.
11. As a **CI operator**, I want **board detection extended for shared Spice assets**, so that **touching shared models re-runs all boards that depend on them**.
12. As a **CI operator**, I want **boards without a simulation config skipped**, so that ** unrelated designs pay no cost**.
13. As a **developer on a laptop**, I want **documented commands** mirroring CI, so that **I reproduce failures locally**.
14. As a **future layout engineer**, I want **the same simulation driver** regardless of parasitic richness, so that **I advance from empty overlay to extraction-backed decks without rewriting CI**.
15. As a **security-conscious maintainer**, I want **documented license posture** for vendor models, so that **redistribution and CI use stay defensible**.
16. As a **release manager**, I want **pinned tool versions** recorded in the report, so that **debugging “works on my machine” is rare**.
17. As a **test author**, I want **measure evaluation isolated from ngspice binary details**, so that **unit tests stay fast and deterministic**.
18. As a **test author**, I want **golden log fixtures** for parsers, so that **refactors don’t silently break thresholds**.
19. As a **DX engineer**, I want **a path to a single Docker image** that contains both KiCad CLI and ngspice, so that **local and CI environments converge**.
20. As a **power-supply designer**, I want **transient scenarios** (startup, load step) captured as data, so that **I tune limits per product without code changes**.
21. As a **power-supply designer**, I want **optional plots** in artifacts, so that **I visually confirm ringing and ripple when numbers look borderline**.
22. As a **digital designer**, I want **the system to ignore my board until I add a sim config**, so that **I’m not forced into analog simulation prematurely**.
23. As a **monorepo maintainer**, I want **deep modules** behind simple interfaces (assemble deck → run → evaluate → report), so that **changes localize and tests stay meaningful**.
24. As a **new hire**, I want **architecture docs beside the tooling**, so that **I onboard without tribal knowledge**.
25. As a **future SI engineer**, I want **extraction-backed overlays** to drop into the same overlay hook, so that **we don’t adopt a second parallel Spice pipeline**.
26. As a **budget-conscious maintainer**, I want **CI time bounded** similarly to existing checks, so that **simulation rows don’t dominate every PR**.
27. As an **auditor**, I want **machine-readable footers or sidecar metrics**, so that **downstream dashboards could ingest pass/fail** later.
28. As a **tech lead**, I want **explicit out-of-scope boundaries** (EMI sign-off, full-field extraction suites), so that **expectations stay realistic**.
29. As a **support engineer**, I want **links from board readme to latest report**, so that **field questions trace back to automated evidence**.
30. As a **library curator**, I want **deduplicated vendor libs**, so that **multiple boards reference one canonical model**.

## Implementation Decisions

- **Single roadmap**: The end goal is simulation that can incorporate layout effects through the overlay mechanism; early milestones may use schematic-only accuracy while the hooks stay fixed.
- **Canonical netlist source**: CI regenerates the Spice netlist from the KiCad schematic; committed netlists are not the source of truth unless export proves unreliable (escape hatch).
- **Mandatory overlay**: Every opting-in board keeps a tracked overlay stub included unconditionally by the assembler so parasitic edits are always visible in history.
- **Central vendor models**: Vendor libraries live under a dedicated shared area with README documenting origin, version, checksum, and license notes; conditional fetch only if redistribution is forbidden.
- **Orchestrator façade**: One narrow workflow — assemble runnable deck, invoke engine, evaluate measures, emit report — implemented so callers (CLI, CI) stay thin.
- **Netlist assembler module**: Encapsulates export invocation, deterministic ordering of includes (shared models, overlay), and intermediate paths without exposing KiCad/ngspice details to callers.
- **Simulation engine adapter**: Wraps ngspice batch execution, captures logs, surfaces version information; interface allows future engines only if ever needed.
- **Measure evaluator module**: Maps simulator output and declared measures to pass/fail; keeps parsing rules testable without running heavy binaries in unit tests.
- **Report generator module**: Produces markdown suitable for artifacts and optional commit on default branch policy; optional structured footer for tooling.
- **Configuration contract**: Per-board YAML declares scenarios, analysis cards, measures, limits, and output preferences; absence means skip.
- **CI integration**: New workflow job matrix reuses repository patterns for detecting changed boards; shared-asset changes trigger all boards that opt into simulation.
- **Governance**: Jobs fail on limit breach for visibility; branch protection does not require green simulation until promoted intentionally.
- **Toolchain strategy**: Long-term reproducibility favors a derivative container image pinning KiCad tooling together with ngspice; interim split export/sim host steps acceptable as bootstrap toward that image.

## Testing Decisions

- **Good tests** assert **external behavior**: parsed measures meet limits given controlled inputs; invalid configs rejected; golden simulator logs produce expected pass/fail without depending on internal function layout.
- **Modules prioritized for automated tests**: measure evaluation and configuration validation; optional golden-file tests for log parsing stability.
- **Integration tests**: Marked slow or optional — one reference board end-to-end once the pipeline is stable enough to avoid flaky CI.
- **Prior art**: Existing repository tests invoke Python validators via subprocess and discover boards by presence of YAML; follow similar discovery for boards that opt into simulation configuration.

## Out of Scope

- Full electromagnetic or full-chip field solvers bundled with this effort.
- Guaranteed sign-off on EMI or radiated emissions.
- Commercial Allegro-class automated extraction suites as a hard dependency.
- Merge-blocking simulation on first release of the feature (explicitly deferred until governance flips).
- Substituting laboratory validation or certification with simulation alone.

## Further Notes

- Board validation and ERC/DRC patterns in this repository should inform detection and artifact upload style.
- Example human-readable report markdown already exists under a board docs area as a template for report shape only.

**Module / test sign-off (for assignee):** Confirm the five-module split (orchestrator façade, assembler, engine adapter, measure evaluator, report generator) matches team expectations. Default recommendation: **unit-test evaluator + config loading first**; **integration test** after one board is consistently green.
