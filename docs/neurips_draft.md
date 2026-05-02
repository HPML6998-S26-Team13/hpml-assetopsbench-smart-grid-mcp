# NeurIPS Draft Scaffold

*Last updated: 2026-05-02*
*Owner: Alex Xin (writing shepherd; section co-authoring under discussion for
Apr 28 team sync)*
*Issues: `#5`, `#39`, `#47`, `#48`; class-report back-port tracked in `#40`*

This doc is the live draft scaffold for the NeurIPS 2026 Datasets & Benchmarks
paper lane. It used to live alongside the failure-analysis scaffold inside
PR `#124`; on 2026-04-27 each issue (`#35`, `#64`, `#36`, `#5`) was split into
its own PR so the four lanes can ship independently. This file is not the
final paper — it is the canonical writing surface for:

- section skeletons
- stable claims we can already support
- figure / table slots
- draft prose that should later move into Overleaf cleanly

Companion conversion surface: `docs/final_report_backport_scaffold.md`.
Submission control surface: `docs/neurips_submission_packet.md`.

## May 2 submission status

The NeurIPS lane is now a live submission lane rather than only a paper
scaffold. The Overleaf project at
https://www.overleaf.com/project/69f5a380e638a31066dc0bd1 has ingested the
official NeurIPS 2026 template package from the NeurIPS CFP and is configured
for anonymous Evaluations & Datasets submission mode
(`\usepackage[eandd]{neurips_2026}`). The remaining LaTeX gate is visual
compile proof in Overleaf plus completion of the NeurIPS checklist.

Deadline posture from the final-week plan:

| Deliverable | Deadline |
|---|---|
| NeurIPS abstract | 2026-05-04 23:59 AOE |
| NeurIPS full paper | 2026-05-06 23:59 AOE |
| Class presentation | 2026-05-07 15:00 ET |
| Class final report | 2026-05-08 23:59 ET |

Writing stance: use the current six-trial captures and failure taxonomy as
paper-backed evidence now; promote additional scenario counts, mitigation
reruns, or 70B/context-window appendix evidence only after those artifacts are
on canonical history or explicitly labeled as pending/appendix.

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

Draft paragraph to transfer into Overleaf:

Industrial-agent benchmarks under-cover Smart Grid transformer diagnostics and
maintenance, even though these workflows require exactly the kind of multi-tool
reasoning that industrial LLM agents are expected to perform: telemetry
inspection, fault diagnosis, degradation forecasting, and work-order planning.
We present SmartGridBench, a Smart Grid transformer-maintenance extension of
AssetOpsBench that adds transformer scenarios, public-data-backed asset
records, and four tool domains exposed through the Model Context Protocol
(MCP). The benchmark is designed to make two usually conflated systems choices
measurable: the transport cost of MCP relative to direct tool invocation, and
the behavioral effect of orchestration strategies such as Agent-as-Tool,
Plan-Execute, and Verified Plan-Execute when the tool surface is held fixed.
Current artifacts show a runnable end-to-end benchmark path with committed
scenario outputs, profiling links, Weights & Biases runs, LLM-as-judge scores,
and failure-taxonomy exports. Preliminary six-trial captures show that MCP
standardization introduces measurable overhead in direct comparisons, that
persistent optimized MCP sessions can reduce steady-state latency but do not by
themselves improve answer quality, and that PE-family mitigations such as
Self-Ask and verification can materially change judged quality. We also treat
scenario realism, generated-scenario circularity, and failure accounting as
first-class benchmark artifacts rather than post-hoc notes. SmartGridBench
therefore contributes both a new industrial benchmark domain and an auditable
systems study of protocol and orchestration choices in tool-using agents.

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
| AaT Cell A/B canonical captures exist on the same scenario set, same model, same job | `benchmarks/cell_A_direct/summary.json` and `benchmarks/cell_B_mcp_baseline/summary.json` from job `8979314` (PR `#130`); 6 scenarios per side, `Llama-3.1-8B-Instruct`, scenario set `smartgrid_multi_domain` (hash `ca66cd16…2691e48`); both sides hit `success_rate=1.0`, `failure_count=0`, `tool_error_count=0` | safe now as a paired one-job baseline |
| PE-family failures show recurring correctness/accounting issues worth classifying | `docs/failure_taxonomy_evidence.md`, committed Y/Z artifacts, `docs/validation_log.md` | safe now |
| Official NeurIPS 2026 submission surface exists | Overleaf project `69f5a380e638a31066dc0bd1`, commit `7e361de`, official `neurips_2026` package and `checklist.tex` | safe now |
| Scenario corpus is on track for the 30-scenario floor | `team13/main` has 11 main scenarios; PR #156 adds 10 hand-crafted scenarios; generator-accepted scenarios still pending | pending; do not present 30 as complete until merged/validated |
| Indicative AaT MCP transport overhead (Cell B − Cell A) on the canonical scenario set | job `8979314` paired summaries: latency mean `+1.20s` (`+9.8%`), wall-clock total `+7.17s` (`+9.8%`), tool-call mean `+0.17` (`+5.0%`), zero tool errors | safe now as one-job, six-scenario evidence; **not** safe as a final transport-overhead distribution |
| Full transport result across `A/B/C` | final comparable captures under `benchmarks/cell_A_direct/`, `cell_B_mcp_baseline/`, `cell_C_mcp_optimized/` with repeat trials and judge data | partial: one-job A/B pair exists from `8979314`; first Cell C capture/judge set exists from `9071639`; final 5-trial matched rerun still missing |
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
- `Y + Self-Ask + missing-evidence detection guard`
- `Z + Self-Ask + missing-evidence detection guard`
- if time allows after those rows exist, a bounded missing-evidence
  retry/replan recovery rung on the same two family lanes

Draft paragraph:

Dhaval's lecture gives the right framing for these follow-ons. Agent-as-Tool is
the benchmark-winning default because reflection makes it self-correcting, but
IBM still favors Plan-Execute as the structured enterprise baseline because it
is easier to inspect and reason about operationally. That makes PE-family
mitigations scientifically useful: they are not a retreat from the benchmark
story, but a way to ask whether a more enterprise-aligned orchestration can
recover some of the quality gap through bounded reasoning and systems fixes.
The mitigation ladder should not be presented as a new full experiment grid.
The clean paper framing is baseline PE-family behavior, then a truthfulness
guard that detects unsupported finalization, then an optional recovery rung
that gives the runner one bounded chance to repair missing evidence before
final answer or work-order creation.

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

### Current results snapshot for first full draft

Use this table as the first Overleaf results skeleton. It is paper-useful now,
but every caption should call it a six-trial first-capture summary unless final
matched reruns replace it.

| Cell | Meaning | Run | Trials | p50 latency | p95 latency | Judge mean | Judge pass |
|---|---|---|---:|---:|---:|---:|---:|
| `A` / `AT-I` | AaT direct Python tools | `8979314_aat_direct` | 6 | 12.15s | 17.29s | 0.167 | 1/6 |
| `B` / `AT-M` | AaT MCP baseline | `8979314_aat_mcp_baseline` | 6 | 13.09s | 16.27s | 0.278 | 2/6 |
| `C` / `AT-TP` | AaT optimized MCP transport + prefix cache | `9071639_aat_mcp_optimized` | 6 | 7.40s | 47.93s | 0.167 | 0/6 |
| `Y` / `PE-M` | Plan-Execute MCP baseline | `8998340_exp2_cell_Y_pe_mcp_baseline` | 6 | 52.06s | 116.32s | 0.111 | 0/6 |
| `Z` / `V-M` | Verified PE MCP baseline | `8998342_exp2_cell_Z_verified_pe_mcp_baseline` | 6 | 119.64s | 152.36s | 0.639 | 4/6 |
| `YS` / `PE-S-M` | Plan-Execute + Self-Ask | `8998341_exp2_cell_Y_pe_self_ask_mcp_baseline` | 6 | 59.00s | 83.20s | 0.444 | 3/6 |
| `ZS` / `V-S-M` | Verified PE + Self-Ask | `8998343_exp2_cell_Z_verified_pe_self_ask_mcp_baseline` | 6 | 33.78s | 58.03s | 0.833 | 5/6 |

Draft sentence:

Across the first six-trial evidence set, optimized persistent MCP sessions
reduced steady-state AaT latency but did not improve judged answer quality,
while PE-family variants showed that clarification and verification can matter
more for semantic quality than transport alone. The strongest current
PE-family row is Verified PE + Self-Ask (`ZS`), with mean judge score `0.833`
and `5/6` judge-pass, but it should be framed as a follow-on mitigation lane
rather than the vanilla orchestration baseline.

### Preliminary Experiment 1 numbers (one job, six scenarios)

The first canonical transport-overhead measurement is now committed. PR
`#130` produced the paired Cell A and Cell B captures from a single Slurm
job (`8979314`) on `Llama-3.1-8B-Instruct`, running 6 scenarios per side
over the canonical scenario set `smartgrid_multi_domain` (hash
`ca66cd16…2691e48`). Both sides hit `success_rate=1.0` with zero tool
errors. Pairing the two summaries gives the first concrete (Cell B −
Cell A) row:

| Metric | Cell A (direct) | Cell B (MCP baseline) | Δ (B − A) | Δ % |
|---|---:|---:|---:|---:|
| `wall_clock_seconds_total` | 73.13 | 80.30 | +7.17 | +9.8% |
| `latency_seconds_mean` | 12.19 | 13.38 | +1.20 | +9.8% |
| `latency_seconds_p50` | 11.47 | 12.91 | +1.44 | +12.6% |
| `latency_seconds_p95` | 18.57 | 16.65 | −1.92 | −10.3% |
| `tool_call_count_total` | 20 | 21 | +1 | +5.0% |
| `tool_call_count_mean` | 3.33 | 3.50 | +0.17 | +5.0% |
| `tool_error_count` | 0 | 0 | 0 | n/a |

Draft sentence (paper-safe wording, calibrated to "one job, six
scenarios" — do not promote to "AaT MCP transport overhead is X%" until
repeat captures land):

We observe an indicative AaT MCP transport overhead of approximately 9.8%
on canonical scenario set `smartgrid_multi_domain` from a single paired
Cell A / Cell B capture (Slurm job `8979314`, `Llama-3.1-8B-Instruct`, 6
scenarios per side, `success_rate = 1.0` on both sides, zero tool errors
on either side). The p95 latency reverses sign in this single-job pair,
which we interpret as small-sample noise rather than a stable transport
effect. The final transport-overhead distribution requires repeat captures
plus the still-NULL `mcp_latency_seconds_*` and `tool_latency_seconds_mean`
profiling dims before the paper commits to a quoted overhead number.

Note for the Results section: this row is `partial_export` per the `#36`
status labels. It can be cited in the draft as preliminary evidence but
should not appear in the final results table without paired profiling
samples and repeat trials.

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

Draft paragraph:

The missing-evidence guard is best interpreted as an accounting and safety
mitigation rather than a capability improvement by itself. It can reduce nominal
success rate because unsupported confident completions become explicit failures.
That is still valuable: production-oriented reporting should not count a
maintenance recommendation as successful when the required evidence was absent.
If time permits, the natural next rung is a recovery guard that reuses the same
detector to retry the missing evidence step or replan the dependent suffix before
finalization. We evaluate this as a ladder on `Y + Self-Ask` and `Z + Self-Ask`,
not as every mitigation crossed with every cell.

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
proofs, upstream AaT parity proofs, the first paired AaT Cell A / Cell B
canonical capture (Slurm job `8979314`, `Llama-3.1-8B-Instruct`, scenario set
`smartgrid_multi_domain`, 6 scenarios per side, `success_rate = 1.0` on both
sides, indicative MCP transport overhead approximately 9.8% from this single
paired job), and analysis scaffolds for the Experiment 1 and Experiment 2
notebook lanes. The remaining empirical gap is not whether the stack can run
at all, but whether repeat captures and matched profiling samples land cleanly
enough to promote the indicative one-job overhead to a final transport
distribution and to support the final orchestration comparison.

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
| Experiment 1 latency figure | `results/metrics/notebook02_latency_summary.csv`, `results/metrics/notebook02_mcp_overhead.csv`, and `results/figures/notebook02_latency_comparison.png` from Notebook 02 |
| Experiment 2 orchestration figure | `results/metrics/notebook03_orchestration_comparison.csv` and companion figure from Notebook 03 |
| PE-family follow-on figure | `results/metrics/notebook03_pe_family_follow_on.csv` once Y/Z are both analysis-ready |
| Failure taxonomy table | `results/metrics/failure_evidence_table.csv` from the `docs/failure_analysis_scaffold.md` contract |
| Failure taxonomy count figure | `results/metrics/failure_taxonomy_counts.csv` and `results/figures/failure_taxonomy_counts.svg` |
| Failure stage heatmap | `results/metrics/failure_stage_cell_counts.csv` and `results/figures/failure_stage_cell_heatmap.svg` |
| Mitigation priority table | `results/metrics/mitigation_run_inventory.csv` and `results/figures/mitigation_priority_table.svg` |
| Mitigation before/after figure | `results/metrics/mitigation_before_after.csv` and rendered figure |
| Artifact ledger table | `docs/validation_log.md` plus benchmark `summary.json` / `meta.json` references |

The failure-taxonomy CSV/SVG artifacts are now on `main` via PR #151, so the
draft can cite those paths as repo facts while still labeling the underlying
analysis preliminary.

## Facts we can already say safely

- the repo has a benchmark-facing Plan-Execute path on canonical history
- the repo has local PE + Self-Ask and Verified PE runners with clean smoke
  proofs
- the repo has AaT Cell A/B smoke proofs and upstream parity smoke proofs
- the repo has Notebook 02 / Notebook 03 analysis scaffolds
- the paper lane should treat AaT vs vanilla PE as the honest core comparison
- PE-family mitigations exist, but they should remain follow-on evidence unless
  they earn central status through clean artifacts
- mitigation-ladder testing should use `Y + Self-Ask` and `Z + Self-Ask` first;
  avoid a full cell-by-mitigation permutation grid

## Landed sibling artifact inputs

- PR #151 landed the failure-taxonomy CSV/SVG artifacts on `main`. This draft
  can now use the 35 judge-failed row count and the `18 / 35`
  task-verification-failure headline as preliminary repo-backed facts.

## Draft deliverable status for `#39`

This file is now the active NeurIPS writing surface, not just an abstract note.
It has the title, abstract, contribution list, claim ledger, section scaffold,
draft prose blocks, figure/table slots, artifact map, and teammate fact asks.

What is still missing before `#39` is complete:

- final result paragraphs after the A/B/C and B/Y analysis exports are frozen
- final figure captions tied to the committed figure files
- references formatted in the NeurIPS style
- Overleaf / LaTeX visual compile proof with the 2026 template
- completed NeurIPS checklist answers

## Back-port handoff for `#40`

The class final report should be derived from this NeurIPS surface, not written
as a second independent draft. Use `docs/final_report_backport_scaffold.md` as
the conversion checklist and section map.

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
