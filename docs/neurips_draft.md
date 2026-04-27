# NeurIPS Draft Scaffold

*Last updated: 2026-04-27*
*Owner: Alex Xin (writing shepherd; section co-authoring under discussion for
Apr 28 team sync)*
*Issue: `#5`*

This doc is the live draft scaffold for the NeurIPS 2026 Datasets & Benchmarks
paper lane. It used to live alongside the failure-analysis scaffold inside
PR `#124`; on 2026-04-27 each issue (`#35`, `#64`, `#36`, `#5`) was split into
its own PR so the four lanes can ship independently. This file is not the
final paper — it is the canonical writing surface for:

- section skeletons
- stable claims we can already support
- figure / table slots
- draft prose that should later move into Overleaf cleanly

## Working title

**SmartGridBench: MCP-Based Industrial Agent Benchmarking for Smart Grid Transformer Operations**

Fallback if we want a more systems-forward title later:

**Protocol and Orchestration Effects in Industrial Agent Benchmarking for Smart Grid Operations**

## One-paragraph paper claim

We extend AssetOpsBench with a Smart Grid transformer-maintenance benchmark,
expose its industrial tool surface through MCP-backed Smart Grid servers, and
study how orchestration and protocol choices affect benchmark usability,
latency, and evaluation quality. The core paper story stays disciplined: the
transport experiment compares direct tool calls against MCP baseline and one
chosen optimized MCP bundle, while the orchestration experiment compares the
shared AaT MCP-baseline cell against Plan-Execute and, if evidence remains
clean, an optional Verified PE follow-on. PE-family mitigations such as
Self-Ask should be presented as measured follow-on improvements rather than
quietly folded into the baseline comparison.

## Draft abstract

Draft paragraph:

We present SmartGridBench, a Smart Grid transformer-maintenance extension of
AssetOpsBench designed to evaluate industrial agents that must combine
telemetry inspection, failure diagnosis, degradation forecasting, and
maintenance planning. The benchmark exposes four tool domains through
MCP-backed Smart Grid servers and keeps one benchmark-facing artifact contract
across direct-tool, MCP, and orchestration conditions. We use this extension to
study two questions that are usually conflated: what latency cost MCP
standardization introduces relative to direct tool calls, and how orchestration
choices such as Agent-as-Tool and Plan-Execute affect benchmark behavior when
transport is held fixed. The core study therefore separates transport
comparison (`A/B/C`) from orchestration comparison (`B/Y`, with optional `Z`)
rather than running an uncontrolled full matrix. Beyond baseline comparison, we
also treat failure analysis as a first-class benchmark artifact: committed runs
already expose recurring answer/tool inconsistency and wrapper-level accounting
failures, which motivates a measurable mitigation lane for PE-family methods.
This framing keeps the paper honest about what is already proven, while still
showing how protocol design, orchestration structure, and evidence discipline
interact in industrial-agent benchmarking.

## Working contribution list

Current contribution wording that stays inside what the repo can already
support:

1. a Smart Grid transformer-maintenance extension to AssetOpsBench with
   MCP-backed IoT, FMSR, TSFM, and WO tool domains
2. a benchmark-facing artifact contract that keeps benchmark outputs, WandB
   runs, and profiling references joinable across conditions
3. an explicit two-axis evaluation design separating transport overhead
   (`A/B/C`) from orchestration behavior (`B/Y`, optional `Z`)
4. an evidence-backed failure-analysis and mitigation lane for PE-family runs

## Contribution paragraph draft

Draft paragraph:

Our intended contribution is not just a new Smart Grid dataset slice. The paper
contributes a benchmark extension, a protocol-aware systems comparison, and an
artifact discipline for failure analysis. SmartGridBench adds a transformer
maintenance domain to AssetOpsBench, keeps its tool surface usable through both
direct and MCP-mediated access paths, and records comparable benchmark artifacts
across orchestration conditions. This lets the study separate protocol cost
from orchestration behavior while also treating failure analysis and mitigation
as first-class benchmark outputs instead of post-hoc debugging notes.

## Claim ledger

Use this table to keep the draft aligned with what the repo can actually prove.

| Claim | Current evidence | Status |
|---|---|---|
| Smart Grid benchmark extension exists with four tool domains over a shared asset key | `mcp_servers/`, `docs/data_pipeline.tex`, processed data and scenarios in repo | safe now |
| Benchmark-facing PE-family path exists on canonical history | `docs/validation_log.md`, `benchmarks/cell_Y_plan_execute/`, `benchmarks/cell_Z_hybrid/` | safe now |
| Experiment design cleanly separates transport from orchestration | `docs/experiment_matrix.md`, `docs/execution_plan.md`, config surfaces | safe now |
| AaT Cell A/B runner surface exists and can emit canonical smoke artifacts | `docs/validation_log.md`, jobs `8962310` and `8969519`; upstream parity jobs `8970383`, `8970468` | safe now as smoke proof |
| PE-family failures show recurring correctness/accounting issues worth classifying | `docs/failure_analysis_scaffold.md`, committed Y/Z artifacts, `docs/validation_log.md` | safe now |
| Full transport result across `A/B/C` | final comparable captures under `benchmarks/cell_A_direct/`, `cell_B_mcp_baseline/`, `cell_C_mcp_optimized/` | blocked; A/B smoke exists |
| Final orchestration comparison across shared `B/Y` anchor | final comparable shared-cell artifacts plus judge outputs | blocked |

## Section scaffold

### 1. Introduction

Draft goal:

- motivate Smart Grid transformer maintenance as an industrial-agent benchmark
  gap
- motivate MCP as a real systems choice with overhead, not just a tooling detail
- motivate the AaT vs PE tension using Dhaval's framing: benchmark performance
  versus enterprise predictability

Draft paragraph:

Industrial-agent benchmarks still under-cover Smart Grid transformer
diagnostics and maintenance workflows, even though transformers are a natural
fit for multi-tool maintenance agents that must retrieve telemetry, diagnose
fault patterns, forecast degradation, and initiate repair actions. At the same
time, industrial-agent evaluations often treat the tool interface as a fixed
implementation detail rather than a measurable systems variable. Our project
addresses both gaps by extending AssetOpsBench with a Smart Grid benchmark lane
and by measuring how protocol and orchestration choices shape runtime behavior
and benchmark usability.

Draft paragraph:

That separation matters because enterprise deployment practice and benchmark
performance do not necessarily reward the same design. Agent-as-Tool often
looks strongest as a benchmark baseline because iterative tool use gives it a
built-in reflection loop, while Plan-Execute remains attractive in production
settings that value predictable intermediate structure and inspectable plans.
The paper therefore treats transport and orchestration as distinct experimental
axes and reserves PE-family reasoning enhancements for an explicit follow-on
mitigation lane rather than quietly moving the baseline.

Draft paragraph:

This positioning also makes the paper more defensible as a datasets-and-
benchmarks submission. We are not claiming a new frontier model or a universal
agent recipe. We are claiming that benchmark design choices at the protocol,
runner, and evidence-accounting layers materially shape what conclusions an
industrial-agent benchmark can support. The Smart Grid domain gives that claim a
concrete operational setting where multi-tool reasoning, maintenance urgency,
and artifact traceability all matter at once.

### 1.5 Related Work Positioning

Short positioning note for later expansion:

- AssetOpsBench gives the upstream industrial benchmark structure
- MCP turns tool access into an explicit protocol/systems choice
- SmartGridBench's differentiator is not just a new domain, but a benchmark
  design that measures protocol cost, orchestration behavior, and failure
  analysis under one artifact contract

### 2. Benchmark Extension

Stable claims already supported:

- Smart Grid transformer domain added on top of AssetOpsBench
- four tool domains: IoT, FMSR, TSFM, WO
- public-safe processed data path exists
- scenario realism and duplication concerns are explicitly documented

Figure / table slots:

- table: Smart Grid tool domains and their functions
- table: scenario families and coverage

Draft paragraph:

The benchmark extension is built from five public transformer-related datasets
reconciled onto a shared synthetic `transformer_id` key so the four tool
domains can operate over the same asset within one scenario trajectory. This
lets Smart Grid tasks preserve the multi-domain structure that makes
AssetOpsBench interesting: one agent can inspect telemetry, diagnose fault
evidence, estimate degradation risk, and recommend maintenance actions for a
single transformer rather than solving isolated one-tool subtasks.

Draft paragraph:

We treat scenario realism as a benchmark-design problem, not a decorative
appendix. The current scenario pack already passes structural validation, and
the realism review explicitly documents where single-sample DGA diagnosis,
maintenance horizons, work-order fields, and operating-context assumptions need
to be constrained to stay defensible. That discipline matters because the paper
is not just shipping tasks; it is claiming a benchmark extension that other
researchers can trust.

### 2.5 Scenario construction and realism controls

Draft paragraph:

Scenario construction follows a realism-first rule: every multi-domain task must
name a transformer, preserve cross-tool consistency through the shared asset
key, and stay inside documented operational bounds for DGA interpretation,
loading, urgency, and work-order fields. This matters especially for Problem
Statement B follow-ons, where automatically generated scenarios could otherwise
recycle domain language without preserving operational coherence. The repo
therefore treats realism validation and circularity handling as part of the
benchmark contract rather than an afterthought.

### 3. System Design

This section should explain:

- MCP server architecture
- direct adapter path for Experiment 1 Cell A
- shared AaT runner path for Cells A/B and upstream parity proof
- shared benchmark runner and artifact layout
- WandB and profiling linkage

Draft paragraph:

The system keeps one benchmark-facing artifact contract across conditions.
`scripts/run_experiment.sh` writes cell-level `config.json` and `summary.json`
plus run-scoped raw artifacts under `benchmarks/cell_<X>/raw/<run-id>/`. This
shared layout lets transport and orchestration experiments reuse the same
analysis surfaces, WandB joins, and profiling back-references instead of
inventing per-method logging formats.

Draft paragraph:

The runtime stack intentionally separates benchmark plumbing from orchestration
logic. Plan-Execute, PE + Self-Ask, and Verified PE all write into the same
artifact layout, while the Agent-as-Tool lane now uses a shared runner for Cell
A direct tools and Cell B MCP servers. The Cell A/B smoke proofs and upstream
AOB runner parity proofs show that this path can execute against the Smart Grid
tool surface and emit the canonical artifact shape. This split is important for
the paper because it keeps logging and reproducibility stable even when
orchestration implementations evolve.

Draft paragraph:

That common artifact contract is one of the paper's quiet systems contributions.
Without it, transport experiments, orchestration experiments, and mitigation
reruns would each tend to invent their own logging shape, making it impossible
to join scenario-level evidence, judge outputs, and profiling bundles later.
By forcing all lanes through one benchmark-facing directory and metadata shape,
the repo turns "can we compare these conditions honestly?" into a tractable
question instead of a manual forensics exercise.

### 4. Experimental Design

Keep the matrix explicit and small.

#### Experiment 1: MCP overhead

- `A`: AaT + direct tools
- `B`: AaT + MCP baseline
- `C`: AaT + MCP optimized

Interpretation:

- `B - A` measures MCP transport overhead
- `C - A` measures residual cost after optimization

#### Experiment 2: orchestration comparison

- `B`: AaT + MCP baseline
- `Y`: Plan-Execute + MCP baseline
- optional `Z`: Verified PE + MCP baseline

Important scope sentence for the paper:

We do not run the full orchestration-by-transport matrix in the core study.
Instead, we hold one variable fixed per experiment so the main claims remain
identifiable: transport varies in Experiment 1 while orchestration varies in
Experiment 2.

Draft paragraph:

This separation is deliberate. Experiment 1 asks what MCP standardization costs
relative to direct tool invocation and how much of that cost one chosen
optimized MCP bundle can recover. Experiment 2 asks how orchestration behavior
changes when transport is held fixed at the shared MCP-baseline condition. By
not multiplying these axes together in the core study, we avoid turning a
class-project benchmark into an underpowered grid search with muddled causal
claims.

### Experimental protocol details

Draft paragraph:

The benchmark protocol should be reported at the `(cell, scenario, model,
trial_index)` level rather than only through aggregate cell summaries. That row
grain is what keeps latency analysis, scenario-level evidence, and any later
judge outputs joinable. The same discipline is especially important for the
shared `B` cell, because it anchors both experiments and therefore must not
quietly drift in scenario set, model, or artifact schema between transport and
orchestration reporting.

### Trial policy

Draft paragraph:

Each benchmark condition is repeated across identical `(cell, scenario, model)`
settings for multiple trials, with the harness recording `trial_index` in the
raw latency and scenario outputs. For first-pass artifact validation, three
trials are enough to prove the chain is real. For the final paper-facing
comparison, five trials should be the default so latency summaries and judge
joins are not resting on one-off execution noise.

### Judge and quality discipline

Draft paragraph:

Execution cleanliness is not enough for the orchestration experiment. A run that
completes without crashing can still be semantically wrong, internally
contradictory, or overconfident relative to its own evidence. The evaluation
plan therefore treats judge scores and trajectory-backed failure classification
as necessary complements to latency and success-rate reporting. Until judge
artifacts are available on the final comparable captures, the paper should keep
quality claims modest and rely on concrete artifact-backed failure patterns
rather than synthetic confidence.

#### Follow-on mitigation lane

These should be described as follow-ons, not core conditions:

- `Y + Self-Ask`
- `Z + Self-Ask`
- if time allows, `Y + Self-Ask + MCP optimized`
- then, if still justified, `Z + Self-Ask + MCP optimized`

Draft paragraph:

Dhaval's lecture gives the right framing for these follow-ons. Agent-as-Tool is
the benchmark-winning default because reflection makes it self-correcting, but
IBM still favors Plan-Execute as the structured enterprise baseline because it
is easier to inspect and reason about operationally. That makes PE-family
mitigations scientifically useful: they are not a retreat from the benchmark
story, but a way to ask whether a more enterprise-aligned orchestration can
recover some of the quality gap through bounded reasoning and systems fixes.

### 5. Evaluation and Analysis Plan

This section should combine:

- task completion metrics
- judge-based quality metrics
- latency / profiling metrics
- failure taxonomy analysis

Figure / table slots:

- figure: Experiment 1 latency comparison
- figure: Experiment 2 success / failure comparison
- table: failure taxonomy with evidence
- figure: mitigation before/after summary

Draft paragraph:

The evaluation plan therefore combines three evidence layers. First, benchmark
completion and latency metrics measure whether a condition runs cleanly and at
what cost. Second, judge and trajectory artifacts capture whether a clean run is
also a believable task solution. Third, the failure-analysis lane classifies
concrete broken runs under a shared taxonomy so mitigation decisions are tied to
named artifacts rather than anecdotal debugging impressions.

Draft paragraph:

This layered view is especially important for enterprise-style agents. A system
that produces an inspectable plan but masks routing failures is not obviously
better than a system that runs fast but occasionally hallucinates the final
maintenance action. The benchmark should therefore report operational cleanliness,
semantic quality, and failure shape together, so readers can see whether a
method is fast, correct, and auditable at the same time or only strong on one
dimension.

### Results-writing discipline

When final numbers land, keep the results section ordered this way:

1. artifact availability and trial coverage
2. core transport comparison
3. core orchestration comparison
4. failure taxonomy summary
5. mitigation before/after follow-on

That order prevents the paper from front-loading mitigation wins before the
baseline matrix is actually established.

### 6. Failure Analysis and Mitigation

Paper promise:

- classify failures with evidence, not impressions
- use the Berkeley categories
- show one mitigation path the repo actually implements and reruns

Draft paragraph:

We treat failure analysis as an evidence-backed benchmark artifact rather than a
pure discussion section. Each major failure mode cited in the paper will be
linked to a concrete run artifact, classified under the Berkeley taxonomy
(specification, inter-agent/orchestration, or task-verification failure), and
paired with an explicit mitigation decision. This keeps the mitigation stream
auditable and separates baseline findings from follow-on repairs.

Draft paragraph:

The first artifact-backed pattern already visible in committed runs is
evidence-resolution failure: the system can retrieve one diagnostic signal,
compute another, and still produce a final answer that never reconciles the
conflict. A second pattern is wrapper-level masking, where routing or semantic
failures can be undercounted if benchmark success accounting trusts the top-level
completion bit too much. These are exactly the kinds of failures that deserve a
benchmark paper treatment because they affect whether downstream conclusions are
trustworthy at all.

Draft paragraph:

This section should stay disciplined about causality. The paper can already say
that recurring task-verification and accounting failures appear in committed
PE-family artifacts. It cannot yet say that any one mitigation closes the gap to
Agent-as-Tool or improves judge quality on the final benchmark set. The right
structure is to show the recurring pattern first, then show only the bounded
before/after reruns that the repo can actually support.

### 7. Reproducibility and Limitations

Must include:

- public-safe processed data path
- scenario realism checks
- circularity caveats for generated-scenario work
- smaller local model choice as a deliberate cost-conscious design

Draft paragraph:

Our experimental design intentionally favors reproducibility and cost control
over maximal scale. The primary benchmark model is a self-hosted
Llama-3.1-8B-Instruct deployment on academic GPU infrastructure, while larger
hosted models are reserved for spot checks rather than a duplicated full-grid
benchmark. This keeps the study operationally realistic for an academic team
while making artifact capture, reruns, and failure diagnosis tractable.

Draft paragraph:

The same honesty rule applies to the current results status. The repo already
proves a benchmark-facing Plan-Execute path, clean PE + Self-Ask and Verified PE
smoke runs, AaT Cell A/B smoke runs, upstream AaT parity against the Smart Grid
MCP servers, and the consumer-side analysis notebooks. What it does not yet
prove is the full A/B/C transport comparison or the final B/Y orchestration
comparison on a stable shared capture set. The draft should say that plainly
and use the merged mitigation lane as follow-on evidence rather than quietly
rewriting the core experiment around the runs that happened to land first.

Draft paragraph:

There is a second limitation specific to the generated-scenario extension. If
Problem Statement B scenarios are generated with knowledge artifacts and then
evaluated by methods that rely on overlapping domain structure, the paper must
disclose the circularity risk clearly. Generated scenarios can still be useful
for coverage expansion and stress testing, but they should not be presented as
an unqualified substitute for the hand-authored benchmark set until the
validation lane is stronger.

### 8. Discussion and conclusion stub

Draft paragraph:

The intended conclusion is modest but useful: protocol design and orchestration
structure are both measurable benchmark variables, and industrial-agent
benchmarks become more trustworthy when they preserve one artifact contract
across those axes and treat failure analysis as part of the benchmark rather
than a side-channel debug log. SmartGridBench is therefore valuable not only as
a new application domain, but as a concrete example of how to keep industrial-
agent evaluation more auditable, more reproducible, and less vulnerable to
clean-looking but weak evidence.

## Current evidence-backed status paragraph

Draft paragraph:

At the time of writing, canonical history already contains the benchmark-facing
Plan-Execute path, the first committed Smart Grid benchmark artifacts, clean
repo-local PE + Self-Ask and Verified PE smoke proofs, AaT Cell A/B smoke
proofs, upstream AaT parity proofs, and analysis scaffolds for the Experiment 1
and Experiment 2 notebook lanes. The remaining empirical gap is not whether the
stack can run at all, but whether the full matched captures land cleanly enough
to support final transport and orchestration comparisons.

## Teammate evidence asks

Keep asks short and factual so teammates can answer quickly:

- Aaron: exact run IDs, config names, artifact paths, and profiling bundle
  locations for the full A/B capture runs once `scripts/run_exp1_ab_capture.sh`
  produces them; the current smoke anchors are `8962310`, `8969519`, `8970383`,
  and `8970468`
- Tanisha: any canonical server-hardening or test evidence we should cite as
  benchmark-infrastructure reliability support
- Akshat: judge-score artifact status, schema confirmation, and scenario-count
  facts that are safe to report in the paper

## Current figure and table list

### Core figures

1. Experiment 1 latency comparison across `A / B / C`
2. Experiment 2 core orchestration comparison across `B / Y`
3. failure taxonomy summary
4. mitigation before/after comparison, with `Z` only as an optional follow-on

### Core tables

1. Smart Grid benchmark extension overview
2. experiment matrix and trial policy
3. failure evidence table
4. reproducibility / artifact ledger

## Figure and table to artifact map

Keep the paper-writing lane tied to concrete repo outputs:

| Paper object | Expected repo source |
|---|---|
| Experiment 1 latency figure | `results/metrics/notebook02_latency_comparison.csv` and companion figure from Notebook 02 |
| Experiment 2 orchestration figure | `results/metrics/notebook03_orchestration_comparison.csv` and companion figure from Notebook 03 |
| PE-family follow-on figure | `results/metrics/notebook03_pe_family_follow_on.csv` once Y/Z are both analysis-ready |
| Failure taxonomy table | `results/metrics/failure_evidence_table.csv` from `docs/failure_analysis_scaffold.md` contract |
| Mitigation before/after figure | `results/metrics/mitigation_before_after.csv` and rendered figure |
| Artifact ledger table | `docs/validation_log.md` plus benchmark `summary.json` / `meta.json` references |

## Facts we can already say safely

- the repo has a benchmark-facing Plan-Execute path on canonical history
- the repo has local PE + Self-Ask and Verified PE runners with clean smoke
  proofs
- the repo has AaT Cell A/B smoke proofs and upstream parity smoke proofs
- the repo has Notebook 02 / Notebook 03 analysis scaffolds
- the paper lane should treat AaT vs vanilla PE as the honest core comparison
- PE-family mitigations exist, but they should remain follow-on evidence unless
  they earn central status through clean artifacts

## Facts we should not over-claim yet

- final quantitative superiority claims before the A/B/C and B/Y artifacts land
- any headline claim that Verified PE is part of the core benchmark comparison
- any claim that generated-scenario PS B is already validated as a main paper
  result

## Teammate fact-bullet asks

Ask teammates for facts in bullet form only.

### From Aaron

- final infra / profiling facts for the benchmark path
- exact optimization knobs that define MCP-optimized, once frozen

### From Tanisha

- concise scope of each Smart Grid MCP server
- any realistic caveats on tool fidelity or server behavior

### From Akshat

- scenario-family coverage summary
- final judge / evaluation facts once stabilized

## Next writing moves

1. turn the section scaffold into Overleaf section headings
2. pull stable architecture / data text from `docs/data_pipeline.tex` and the
   MCP server docs
3. keep Results and Discussion conservative until the main experiment artifacts
   exist
4. land a first complete Methods/Design/Limitations transfer from this file into
   the eventual manuscript surface before waiting on final numbers
