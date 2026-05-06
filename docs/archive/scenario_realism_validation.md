# Smart Grid Scenario Realism Validation Note

*Created: 2026-04-10*  
*Last updated: 2026-04-11*  
*Owner: Alex Xin*

*Archived: 2026-05-05 — superseded by `docs/scenarios_021_030_grounding.md` (canonical scenario grounding for SGT-021..SGT-030 via PR #175) and `docs/dga_realism_statistical_validation.md` (canonical DGA realism methodology). Issue #60 closed; the early-Apr realism note is preserved as historical context for the validation framework's evolution.*

This note is the concrete realism-validation pack for issue #60. Its job is to
turn "these scenarios are structurally valid" into a short, reviewable set of
real-world transformer-maintenance questions for Dhaval.

## What is already validated

The current scenario batch has already passed the repo's structural checks:

- scenario JSON files are present under `data/scenarios/`
- schema-required fields are populated
- `expected_tools` names now match the current MCP tool registry
- representative scenarios exist across all four tool domains plus multi-domain
  end-to-end flows

That means the remaining question is not format correctness. The remaining
question is whether the tasks read like believable transformer operations and
maintenance work.

## Representative scenario pack

Use this small pack for mentor review.

### 1. FMSR diagnosis from DGA

- File: `data/scenarios/fmsr_01_dga_fault_mode_diagnosis.json`
- Current task: use the latest DGA record for transformer `T-012`, identify the
  most likely fault mode, and explain the top two candidate failure mechanisms.
- Real-world use case: maintenance engineer or reliability engineer reviews a
  fresh oil analysis report and maps gas evidence to likely transformer fault
  classes before escalation or inspection.

### 2. TSFM remaining useful life / maintenance-window decision

- File: `data/scenarios/tsfm_01_rul_forecast_maintenance_window.json`
- Current task: forecast remaining useful life for transformer `T-016` and say
  whether it can safely operate for the next 180 days without major
  maintenance.
- Real-world use case: planner or asset manager uses condition signals and
  degradation estimates to decide whether a unit can remain in service through
  the next operating window.

### 3. Work-order creation after repeated fault indicators

- File: `data/scenarios/wo_02_corrective_order_after_fault.json`
- Current task: create a corrective work order for transformer `T-017` with
  emergency or high priority depending on safety risk.
- Real-world use case: operations or maintenance team converts abnormal
  condition evidence into a prioritized field action with explicit tasks.

### 4. Multi-domain end-to-end incident response

- File: `data/scenarios/multi_01_end_to_end_fault_response.json`
- Current task: inspect recent sensor behavior, infer probable fault mode,
  estimate 30-day risk, and produce a maintenance recommendation for transformer
  `T-015`.
- Real-world use case: condensed incident-response workflow from alert review to
  diagnosis to short-horizon risk assessment to action recommendation.

## Research findings (2026-04-11)

Independent research against IEEE/IEC standards and utility practice literature
answered most of the original realism questions. Full research artifact:
`deep-research-runs/20260411_014354_smart-grid-transformer-o-m-realism-validation/report.md`

### 1. DGA diagnosis: single sample vs trend

**Finding:** A single sample is not sufficient for fault diagnosis. Both
IEEE C57.104-2019 and IEC 60599 require trending.

IEEE C57.104-2019 uses a four-condition status framework (Condition 1-4). A
single sample determines the current condition status, but the standard is
explicit that the recommended actions at every level above Condition 1 include
evaluating the **rate of gas generation** across multiple samples.

IEC 60599 ratio methods (Duval Triangle, Rogers) can classify fault type from a
single sample, but trending is needed to assess severity and progression.

**Realistic workflow is two-phase:**
1. Condition screening (can use latest sample): gas levels vs thresholds
2. Fault diagnosis (requires trend): rate of change + ratio methods + baseline comparison

**Scenario implication:** `fmsr_01` should add 3-5 historical DGA samples and
make trend evaluation part of the task, or explicitly frame itself as "initial
condition assessment" rather than "fault mode diagnosis."

### 2. Maintenance decision horizons

**Finding:** Decision horizons are condition-dependent, not fixed.

| Urgency | Typical Horizon | When Used |
|---------|----------------|-----------|
| Emergency | Hours to days | Condition 4, active faults, protection trips |
| Short-term corrective | 1-4 weeks | Condition 3, confirmed fault |
| Medium-term planned | 1-6 months | Condition 2 trending upward |
| Long-term capital | 1-5 years | Health index fleet planning |

Horizons vary by fault class (thermal faults allow months; active arcing demands
days), asset criticality (345kV metro feeder vs 69kV distribution), loading
season (summer peak compresses horizons), and spare availability (large power
transformers have 12-24 month lead times).

**Scenario implication:** 180-day window is realistic for a Condition 2 unit in
a low-loading season. 30-day risk horizon is realistic for Condition 3 post-
investigation. Consider making the horizon condition-specific rather than fixed.

### 3. Work order minimum fields

**Finding:** A realistic corrective WO has 12-15 fields across four sections.

**Header:** WO number, priority code, work type (inspection / corrective /
emergency), equipment ID, location, requester.

**Planning:** Crew type, estimated duration, outage requirement (live-line /
planned / forced / none), switching/isolation procedure, LOTO requirements.

**Execution:** Task steps, safety/PPE requirements, materials and parts, special
equipment.

**Completion:** Findings, parts consumed, follow-up flag, updated condition data.

Key distinction: for inspection and corrective work, scope is known before the
outage. For emergency, the first task is "isolate and make safe" and detailed
scope is determined after de-energization.

**Scenario implication:** `wo_02` should specify work order type and include at
minimum: priority, equipment ID, work type, crew type, outage requirement, LOTO
reference, task steps, and safety notes.

### 4. Operating context

**Finding:** Three factors are must-haves; the rest are enrichments.

| Factor | Criticality |
|--------|------------|
| Asset criticality / load served | Must-have |
| Spare transformer availability | Must-have |
| Current loading % and season | Must-have |
| Voltage class | Strongly desirable |
| Outage cost ($/hour) | Strongly desirable |
| Substation configuration (redundant vs radial) | Desirable |
| Crew/switching coordination | Desirable |
| Regulatory/environmental | Desirable |

**Scenario implication:** `multi_01` should add asset criticality tier, spare
availability, and current loading percentage. These three alone materially
change the recommendation.

### 5. Emergency vs high priority triggers

**Finding:** Emergency triggers are protection-device operations and Condition 4.
High priority triggers are Condition 3 with adverse trend.

**Emergency (hours):** Condition 4 gas levels, Buchholz relay alarm/trip, sudden
pressure relay operation, active arcing/discharge, oil leak with safety hazard,
visible external damage, cooling system total failure, unexplained protection
trip.

**High/urgent (days to weeks):** Condition 3 with rising trend, rapid rate of
gas generation (>2x normal interval), high moisture in oil (>30 ppm), abnormal
temperature rise, cooling system partial failure, LTC anomaly, insulation
degradation.

**Scenario implication:** `wo_02` should replace "emergency or high depending on
safety risk" with explicit trigger conditions. This makes priority determination
a reasoning task rather than a subjective judgment.

---

## Recommended scenario changes

| Scenario | Current Gap | Recommended Fix |
|----------|------------|-----------------|
| `fmsr_01` | "Latest DGA record" -- no trend | Add 3-5 historical samples; make trend evaluation part of the task |
| `tsfm_01` | Fixed 180-day horizon | Keep 180 days but add loading context and criticality tier |
| `wo_02` | "Emergency or high depending on safety risk" | Specify explicit trigger conditions; add minimum WO fields |
| `multi_01` | Missing operating context | Add asset criticality tier, spare availability, current loading % |
| All | No condition screening vs diagnosis distinction | Frame as separate sub-tasks where applicable |

---

## Remaining questions for Dhaval

The research narrowed the original five questions to three that require domain
expert confirmation. These feed issue #63.

1. **Rate-of-change thresholds.** IEEE C57.104 leaves the specific rate-of-gas-
   generation threshold to the utility. Common practice suggests >2x the
   previous interval's rate triggers escalation. Is that a reasonable default
   for our benchmark, or does Dhaval's team use a different threshold?

2. **Health index composition.** For the RUL scenarios, should we model a
   specific health index formula (DGA + oil quality + loading + age), or is it
   sufficient to provide the HI score as a given input?

3. **Work order field names.** Should our WO output fields mimic a specific
   CMMS (Maximo, SAP PM), or use generic field names? Utilities customize
   heavily, so generic may be more appropriate for a benchmark.

## Intended outcome

The research findings above are sufficient to start improving scenario
parameters now. Dhaval's answers to the three remaining questions will refine
thresholds and field naming for the next scenario batch.
