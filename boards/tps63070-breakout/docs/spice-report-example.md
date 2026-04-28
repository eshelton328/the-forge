# SPICE regression report (example)

> **Example artifact** — structure for Phase 1 (schematic / netlist) automated runs. Numbers are illustrative; replace with real `ngspice` outputs once wired.



## Run metadata


| Field             | Value                                           |
| ----------------- | ----------------------------------------------- |
| Workflow          | `.github/workflows/spice.yml` (hypothetical)    |
| Trigger           | Pull request `#123` / push to `simulate-ci`     |
| Commit            | `a1b2c3d4`                                      |
| Compared baseline | `main` @ `9f8e7d6c` (committed report snapshot) |
| Generated         | `2026-04-27T18:42:00Z`                          |
| Simulator         | ngspice 43 (batch)                              |
| Netlist source    | `tps63070-breakout.kicad_sch` → exported SPICE  |


## Executive summary


| Suite                            | Passed | Failed | Skipped |
| -------------------------------- | ------ | ------ | ------- |
| Phase 1 — schematic/regulator    | 5      | 0      | 1       |
| Phase 2 — post-layout parasitics | —      | —      | 4       |


**Result:** ✅ **PASS** (Phase 1). Phase 2 not run—no extraction netlist present.

---

## Phase 1 — Schematic-only tests

These gates compare simulated quantities to **limits** stored in-repo (YAML/JSON beside the runner). They validate **circuit intent** on exported netlist + models, **not** PCB parasitics.

### Test matrix


| ID  | Case                                 | Metric                      | Limit                    | Simulated   | Status                         |
| --- | ------------------------------------ | --------------------------- | ------------------------ | ----------- | ------------------------------ |
| S1  | Startup transient                    | Overshoot V_{\mathrm{OUT}}  | ≤ 450 mV                 | 310 mV      | ✅                              |
| S2  | Load step 50%→100%                   | Undershoot V_{\mathrm{OUT}} | ≥ −200 mV                | −120 mV     | ✅                              |
| S3  | Line step 12 V→14 V V_{\mathrm{IN}}  | \Delta V_{\mathrm{OUT}}     | ± 50 mV                  | +18 mV      | ✅                              |
| S4  | DC load sweep 0→2 A V_{\mathrm{OUT}} | Regulation                  | ≈ 3.3 V ±100 mV          | 3.28–3.32 V | ✅                              |
| S5  | Quiescent (EN high, light load)      | I_{\mathrm{IN}}             | ≤ 5 mA (model-dependent) | 3.8 mA      | ✅                              |
| S6  | AC loop phase margin *(if modeled)*  | PM @ f_{\mathrm{c}}         | ≥ 45°                    | —           | ⊘ Skip (no small-signal model) |


### Delta vs baseline on `main`


| ID  | Metric     | Baseline (`main`) | This run | \Delta |
| --- | ---------- | ----------------- | -------- | ------ |
| S1  | Overshoot  | 298 mV            | 310 mV   | +12 mV |
| S2  | Undershoot | −115 mV           | −120 mV  | −5 mV  |


*PR comment bots can summarize: “within tolerance; S1 slightly worse but inside limit.”*

---

## Phase 2 — Post-layout parasitic *(not exercised this run)*


| ID  | Case              | Metric                         | Limit             | Notes                      |
| --- | ----------------- | ------------------------------ | ----------------- | -------------------------- |
| P1  | Hot loop ESL      | Ripple @ switch node           | TBD vs extraction | Requires extracted netlist |
| P2  | PDN impedance     | |Z| vs frequency               | < target curve    | Solver + extraction        |
| P3  | Bulk cap ESL path | \Delta ripple V_{\mathrm{OUT}} | vs Phase 1        | Compare phases             |


All Phase 2 rows **skipped** — no parasitic-augmented netlist passed to CI.

---

## Artifact locations


| Artifact                   | Description                                    |
| -------------------------- | ---------------------------------------------- |
| `ngspice-stdout.log`       | Full batch log (attached to workflow run)      |
| `plots/*.pdf` *(optional)* | Startup / load-step plots for human review     |
| `spice-report.md` *(this)* | Checked-in snapshot for PR diff against `main` |


---

## Suggested README integration (conceptual)

Put a **single line + link** on `README`, not full tables:

```markdown
**SPICE regression (Phase 1):** [latest snapshot](docs/spice-report.md) — last branch run: ✅ pass @ `main`
```

Workflow on PR:

1. Run ngspice; generate `boards/.../docs/spice-report.md` from template + measurements.
2. Fail job if limits violated.
3. Optional: `**git diff**` committed `docs/spice-report.md` on `**main**` → post diff to PR, or attach “vs main” metrics from step above—without committing until merge.

Alternatively keep **committed** report fresh only on merges to `**main`** (bot or policy), and PR compares working tree report to `**main**`’s saved file inside the CI step.

---

## Footer (optional machine-readable)

```
REPORT_VERSION=1
SPICE_SUITE=phase1-tps63070-example
GIT_SHA=a1b2c3d4
BASELINE_SHA=9f8e7d6c
PASS=true
EXIT_CODE=0
```

