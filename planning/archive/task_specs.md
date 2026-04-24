# SmartGridBench Task Specs

*Archived companion to [task_tracker.md](./task_tracker.md). Last updated: April 9, 2026. Current canonical task state now lives in the GitHub Project and issue bodies.*

This document removes ambiguity from the open work in the tracker. Every task here has:

- one primary owner
- a concrete interpretation of the title
- specific deliverables
- a checkable definition of done
- explicit coordination / handoff notes

## GitHub planning model

The GitHub project now uses four planning layers at once:

- `Iteration` = the weekly slice when the child task should be worked
- `Parent issue / workstream` = the long-lived stream the task belongs to
- `Milestone` = the delivery gate the task contributes to
- child issue body = the execution-level specification for the owner

The current workstream parents are:

- `#69` - `WS1 Serving, observability, and experiment plumbing`
- `#70` - `WS2 Scenarios and evaluation harness`
- `#71` - `WS3 MCP server hardening and benchmark integration`
- `#72` - `WS4 MCP overhead profiling and optimization (Experiment 1)`
- `#73` - `WS5 Orchestration comparison and failure analysis (Experiment 2)`
- `#74` - `WS6 Problem Statement B - scenario generation extension`
- `#75` - `WS7 Runbook and reproducibility`
- `#76` - `WS8 Writing and final delivery`

The current delivery-gate milestones are:

- `M1 Proposal finalized, mid-point report submitted`
- `M2 Team repo public`
- `M3 Foundation and stack ready`
- `M4 Experiment 1 completed (MCP overhead)`
- `M5 Experiment 2 + failure analysis completed`
- `M6 Problem Statement B evaluation ready`
- `M7 Final paper / report / deck ready`

## Global rules

- A task is not done just because code exists locally. It is done when it is merged into the canonical repo or otherwise independently verified.
- When a task depends on another person's artifact, the owner should still make progress on everything they can do before the dependency lands.
- If a task naturally produces documentation, the owner should commit the documentation in the same PR / push rather than treating docs as somebody else's follow-up.
- When a task says "coordinate with X", that means: read the relevant files, sync on interface assumptions in writing, and hand off a concrete artifact. It does **not** mean the two people co-own the same ticket.
- Before this document was archived, task titles and issue bodies were kept aligned with the corresponding entry here. GitHub issue bodies are now canonical.

## Cross-cutting active work

### #5 — NeurIPS 2026 paper — draft in NeurIPS format first, then back-port to IEEE final report
- **Owner:** Alex
- **What this means:** Own the live paper-writing stream now, rather than waiting until W5. The working draft should be structured in NeurIPS Datasets & Benchmarks format first, then adapted into the class IEEE report template once the core story is stable.
- **Deliverables:** Active outline, section skeletons, key claims / figures list, and ongoing draft text in the canonical writing surface.
- **Done when:** The writing effort has moved beyond kickoff into a real draft that the W5 report / abstract / full-paper tasks can build from directly.
- **Dependencies:** Inputs from Tanisha, Akshat, and Aaron arrive later as content briefs, experiment results, and factual corrections.
- **Coordination:** Keep teammates on factual-input duty, not prose ownership. Ask for missing facts in bullet-list form so the final voice stays unified.

## W2 — Immediate recovery and foundation

### #56 — Replay local Smart Grid scenario files onto the org repo `main` branch and push first batch
- **Owner:** Akshat
- **What this means:** Recover the scenario JSONs and any helper files that currently exist only on your local machine or old branch history, then replay them onto the canonical team repo history.
- **Deliverables:** Scenario files under [data/scenarios/](../../data/scenarios), with stable filenames and at least one commit on canonical history.
- **Done when:** The files are visible on the org repo `main` branch, filenames follow repo convention, and Alex can review the actual scenario count from the repo.
- **Coordination:** Use the current canonical repo state as base. If local history is messy, cherry-pick or manually reapply; do not block on preserving old branch shape.

### #57 — Replay local benchmark / harness README work onto the org repo `main` branch and push
- **Owner:** Akshat
- **What this means:** Recover the benchmark / harness instructions claimed on the Apr 7 call and land them in the repo in the correct location.
- **Deliverables:** A repo-tracked benchmark / harness doc or script set, likely under [benchmarks/](../../benchmarks), [docs/](../../docs), or [scripts/](../../scripts), not only in private notes.
- **Done when:** Another teammate can read the pushed artifact and understand how to invoke the harness without relying on call memory.
- **Coordination:** Keep the instructions aligned with Aaron's serving setup and Alex's experiment design language.

### #3 — Run one existing benchmark scenario end-to-end on the canonical stack
- **Owner:** Akshat
- **What this means:** Prove that the harness runs in the current team repo state, not only on a personal checkout, by executing one existing benchmark scenario from start to finish.
- **Deliverables:** Working invocation instructions, any required config / adapter code, and a short evidence note or log snippet showing a successful run.
- **Done when:** A run succeeds on canonical history and the invocation path is documented in-repo.
- **Dependencies:** Tanisha's MCP interfaces and Aaron's serving path if using the self-hosted Llama route.
- **Coordination:** Surface any MCP interface assumptions explicitly so Tanisha can harden to the real harness contract.

### #4 — Draft first 5-10 Smart Grid transformer scenarios and commit them to the canonical repo
- **Owner:** Akshat
- **What this means:** Land the first reviewable scenario batch in-repo so the team can critique realism, coverage, and formatting.
- **Deliverables:** 5-10 scenario JSON files plus any validation helper or notes needed to understand them.
- **Done when:** The files are pushed, reviewable, and tied to real `asset_id` / `transformer_id` values from the processed data.
- **Coordination:** Alex reviews for benchmark coverage; Dhaval-facing realism questions can wait for the follow-up validation task below.

### #6 — Successful first Insomnia A6000 vLLM serve smoke test for Llama-3.1-8B-Instruct
- **Owner:** Aaron
- **What this means:** Move from "scripts written" to "environment actually works on Insomnia".
- **Deliverables:** Successful run of [setup_insomnia.sh](../../scripts/setup_insomnia.sh), [vllm_serve.sh](../../scripts/vllm_serve.sh), and [test_inference.sh](../../scripts/test_inference.sh), plus captured job output / notes.
- **Done when:** The model serves on Insomnia, the smoke test completes successfully, and the exact invocation path is documented in-repo.
- **Coordination:** Share the tested path with Alex and Akshat so they can build experiment and harness flows on top of the real environment rather than guessed commands.

### #58 — Validate all four MCP servers with the benchmark Llama path, not only Claude Desktop
- **Owner:** Tanisha
- **What this means:** Prove the MCP servers work in the actual benchmark stack, not just through Claude Desktop manual prompting.
- **Deliverables:** One documented test path from the benchmark Llama setup to the MCP servers, with at least one successful end-to-end example.
- **Done when:** The team has evidence that the servers can be called from the benchmark LLM path and not only the Claude `/mcp` workflow.
- **Dependencies:** Aaron's serving path or Akshat's harness path, depending on where the integration is wired first.
- **Coordination:** If interface changes are needed for the benchmark LLM path, document them before hardening all four servers.

## W2 — Foundation backlog

### #8 — Generic Slurm experiment template for benchmark jobs
- **Owner:** Aaron
- **What this means:** Create the reusable job template for experiment cells, not only the one-off serving job.
- **Deliverables:** A job script or template that accepts config inputs, launches the required stack, runs the harness, and writes logs / artifacts predictably.
- **Done when:** Alex can duplicate the template for experiment cells without inventing a new operational pattern.
- **Coordination:** Align output locations with Alex's analysis notebooks and Akshat's harness expectations.

### #7 — Profiling capture wrappers — PyTorch Profiler around benchmark runs
- **Owner:** Aaron
- **What this means:** Author the capture layer that wraps experiment runs with PyTorch Profiler.
- **Deliverables:** Script(s) or wrapper code that emits profiler traces for the benchmark run path.
- **Done when:** A benchmark run can produce profiler trace artifacts in a known location with documented invocation.
- **Coordination:** Alex consumes the emitted trace files for analysis, so output paths and file format should be stable and documented.

### #59 — Profiling capture wrappers — Nsight / `nvidia-smi` / GPU utilization collection
- **Owner:** Aaron
- **What this means:** Add GPU-level observability beyond PyTorch-only traces.
- **Deliverables:** Nsight invocation notes if applicable, plus lightweight GPU utilization capture such as `nvidia-smi` snapshots or logs tied to each run.
- **Done when:** Every benchmark cell can produce GPU utilization evidence alongside profiler traces.
- **Coordination:** Keep the capture lightweight enough that it does not destabilize the main run path.

## W2 — MCP server hardening tasks

Shared expectations for all four hardening tasks:
- add input validation and failure-path handling
- verify the server reads the Smart Grid data correctly from the processed CSVs
- ensure the tool outputs are stable enough for harness consumption
- add tests or at minimum reproducible smoke checks
- document any assumptions the harness or orchestration layer must obey

### #9 — Complete IoT MCP server hardening + tests + harness contract
- **Owner:** Tanisha
- **Focus:** Asset metadata and sensor-reading retrieval.
- **Done when:** The IoT server can serve benchmark requests reliably and its return shape is documented / test-covered.

### #10 — Complete TSFM MCP server hardening + tests + harness contract
- **Owner:** Tanisha
- **Focus:** `get_rul`, `forecast_rul`, `detect_anomalies`, `trend_analysis`.
- **Done when:** Forecasting / anomaly outputs are stable, documented, and usable in the benchmark path.

### #11 — Complete FMSR MCP server hardening + tests + harness contract
- **Owner:** Tanisha
- **Focus:** Failure-mode lookup, sensor correlation, DGA record retrieval, Rogers Ratio analysis.
- **Done when:** The FMSR path is stable enough for multi-tool scenarios and tested on representative DGA examples.

### #12 — Complete WO MCP server hardening + tests + harness contract
- **Owner:** Tanisha
- **Focus:** Work-order CRUD, downtime estimates, and maintenance-action outputs.
- **Done when:** The WO server behaves predictably in the benchmark path and is ready for the architecture review below.

### #13 — WO server architecture review against Dhaval's “WO agent is a coding agent” guidance
- **Owner:** Tanisha
- **What this means:** Decide whether the current WO tools are architecturally aligned with the upstream "coding agent" idea or whether they need a redesign.
- **Deliverables:** A short design note and, if needed, a follow-up implementation task list.
- **Done when:** The team has a documented decision: keep current CRUD-style tools or pivot toward code-execution-style tools.
- **Coordination:** Alex uses this decision in the paper / project framing; Akshat needs to know the final tool shape for scenario design.

## W2 — Scenario and eval tasks

### #15 — Reach 15+ validated Smart Grid scenarios in the canonical repo
- **Owner:** Akshat
- **What this means:** Grow from the first scenario batch to the W2 target of at least 15 reviewable scenarios in-repo.
- **Deliverables:** 15+ scenario files covering meaningful Smart Grid maintenance flows.
- **Done when:** The repo count reaches at least 15 validated scenarios and Alex can use them as the experiment set.

### #16 — Validate Smart Grid scenario format against AssetOpsBench schema and conventions
- **Owner:** Akshat
- **What this means:** Prove the scenarios are structurally compatible with the upstream benchmark, not just plausible JSON.
- **Deliverables:** Validation script, command, or documented procedure plus a pass result.
- **Done when:** The team has a reproducible way to check scenario validity and the current scenario set passes it.

### #60 — Real-world scenario validation plan
- **Owner:** Akshat
- **What this means:** Convert "these look benchmark-valid" into "these map to believable transformer maintenance situations".
- **Deliverables:** A short note mapping scenario families to industrial use cases and listing open realism questions for Dhaval.
- **Done when:** Alex can send or discuss a concrete realism-validation list with Dhaval rather than asking a vague question.

### #17 — 6-dimension LLM-as-Judge scoring in eval harness
- **Owner:** Akshat
- **What this means:** Implement the rubric dimensions from the AssetOpsBench paper in the harness path you own.
- **Deliverables:** Judge invocation path, scoring output format, and documented rubric dimensions in-repo.
- **Done when:** A benchmark run can emit structured judge scores across all six dimensions.

### #18 — First Smart Grid scenario runs end-to-end through MCP with trajectory artifact captured
- **Owner:** Akshat
- **What this means:** Move from "the harness can run something" to "one of our Smart Grid scenarios actually runs all the way through the MCP stack and leaves behind a trajectory artifact."
- **Deliverables:** Successful Smart Grid trajectory artifact, invocation command, and a short note on what worked / failed.
- **Done when:** The team has one canonical "it works" trajectory to build experiments from.
- **Dependencies:** Aaron's serving path, Tanisha's hardened MCP interfaces, Alex's orchestration / logging setup as needed.

### #20 — First judge-scored trajectory lands with logs / artifacts using Maverick-17B
- **Owner:** Akshat
- **What this means:** Connect a real Smart Grid trajectory artifact to the judge model and prove that scoring produces reusable artifacts, not just a console success message.
- **Deliverables:** One successful judge run on a real trajectory, with recorded score output and saved logs / artifacts.
- **Done when:** Judge scoring is no longer theoretical and the output format is ready for experiment use and later notebook analysis.

## W2 — Experiment plumbing

### #14 — WandB metrics schema definition for servers, trajectories, and experiment cells
- **Owner:** Alex
- **What this means:** Decide exactly what gets logged, with stable field names.
- **Deliverables:** A written metrics schema covering scenario metadata, orchestration mode, MCP mode, latency, token usage, judge scores, and hardware context.
- **Done when:** Aaron, Tanisha, and Akshat can instrument against a single agreed schema.

### #61 — WandB instrumentation in MCP servers and agent pipeline
- **Owner:** Alex
- **What this means:** Wire logging into the relevant code paths so experiment runs actually emit useful metrics.
- **Deliverables:** Repo changes that log the agreed metrics into WandB or into an intermediate format that feeds WandB.
- **Done when:** The first experiment logs contain the intended fields from the schema.

### #22 — Wire Agent-as-Tool orchestration to the team's MCP servers
- **Owner:** Alex
- **What this means:** Get the AaT path running against the team's Smart Grid MCP stack.
- **Deliverables:** Working orchestration path, config / invocation, and notes on any adapters needed.
- **Done when:** AaT can run on the team's MCP servers as a real experiment condition.

### #62 — Wire Plan-Execute orchestration to the team's MCP servers
- **Owner:** Alex
- **What this means:** Get the PE path running against the same MCP stack for apples-to-apples comparison.
- **Deliverables:** Working orchestration path, config / invocation, and notes on any adapters needed.
- **Done when:** PE can run on the team's MCP servers as a real experiment condition.

### #63 — Follow up with Dhaval on hybrid orchestration novelty and Smart Grid scenario realism / validation criteria
- **Owner:** Alex
- **What this means:** Close the two open mentor questions from the Apr 7 discussion.
- **Deliverables:** Email or message to Dhaval covering hybrid novelty and scenario realism, plus a saved response or documented non-response.
- **Done when:** The team has enough signal to either proceed with Hybrid or keep it out of scope, and to validate scenario realism with a concrete mentor answer.

### #19 — Each team member sync the org repo `main` branch, install `ibm-watsonx-ai` into `.venv`, and run the verify script locally
- **Owner:** Team
- **What this means:** Every teammate aligns local repos and confirms basic WatsonX access locally.
- **Deliverables:** Per-person local confirmation, not just "someone else can run it".
- **Done when:** Each teammate has acknowledged successful local setup or surfaced a concrete blocker.

### #21 — Set up WandB project with initial experiment logs
- **Owner:** Team
- **What this means:** Move from "WandB workspace exists" to "our code is sending meaningful project runs there".
- **Deliverables:** At least one real run with the agreed naming / metadata conventions.
- **Done when:** The team can open WandB and inspect real SmartGridBench experiment logs, not just an empty project shell.

## W3 — Experimental design and profiling

### #23 — Hybrid orchestration prototype implementation
- **Owner:** Alex
- **What this means:** Implement the PE + reflection-checkpoint idea if and only if Dhaval greenlights novelty.
- **Deliverables:** A runnable hybrid orchestration path plus a short design note on where reflection checkpoints happen.
- **Done when:** Hybrid is a runnable experiment condition or is explicitly deferred based on mentor feedback.

### #24 — Self-Ask integration (~10 LOC) in all 3 orchestrations
- **Owner:** Alex
- **What this means:** Add the clarification / self-check behavior consistently across AaT, PE, and Hybrid if Hybrid is active.
- **Deliverables:** Code changes and a short note on how the hook triggers.
- **Done when:** All active orchestration modes include the same self-ask behavior and the change is documented.

### #25 — Run Experiment 1 profiling captures (Direct vs MCP-baseline vs MCP-optimized) and publish raw artifacts for analysis
- **Owner:** Aaron
- **What this means:** Execute the capture side of the MCP-overhead experiment and leave Alex clean raw data to analyze.
- **Deliverables:** Raw profiler / GPU artifacts per condition, with config metadata and run identifiers.
- **Done when:** Alex has enough raw material to compute the MCP-overhead comparison without rerunning capture himself.

### #26 — Notebook 02: latency analysis — MCP overhead experiment design, parsing, and writeup
- **Owner:** Alex
- **What this means:** Own the analysis side of Experiment 1.
- **Deliverables:** Notebook, figures, and interpretation of the three-condition overhead comparison.
- **Done when:** The team has publication-ready latency analysis for the MCP-overhead story.

### #27 — Integrate WandB logging into profiling pipeline
- **Owner:** Aaron
- **What this means:** Ensure the capture pipeline automatically emits the profiling metadata Alex needs.
- **Deliverables:** Profiling runs linked to WandB runs with stable metadata.
- **Done when:** Capture artifacts and WandB runs correspond cleanly for the same experiment cell.

### #28 — First WandB experiment logs live
- **Owner:** Team
- **What this means:** The first end-to-end experiment has visible logs in WandB.
- **Done when:** The team can open a run and inspect real fields, traces, and metadata from the SmartGridBench stack.

### #50 — Knowledge Plugin: encode IEC 60599 + IEEE C57 transformer engineering standards as a structured knowledge document the scenario-gen LLM can consume
- **Owner:** Tanisha
- **What this means:** Convert the transformer-engineering standards into a structured artifact the PS B generator can actually use, rather than leaving the guidance as scattered notes.
- **Deliverables:** Repo-tracked standards artifact, a short note on its structure, and clear instructions for how the generator should consume it.
- **Done when:** Aaron can point the generation pipeline at the artifact and produce candidate scenarios without asking Tanisha to paraphrase the standards live.
- **Coordination:** Align the artifact format with Aaron before finalizing it, and keep the representation citation-friendly so Alex can reuse the same facts in the paper.

### #2 — Auto-scenario generation prototype — first generated Smart Grid scenario batch from Kaggle data + Knowledge Plugin
- **Owner:** Aaron
- **What this means:** Build the first real PS B generation path from structured data plus domain guidance into reviewable candidate scenarios.
- **Deliverables:** Runnable generation path, first candidate batch, and notes on prompt / filter assumptions.
- **Done when:** The team can inspect a first generated scenario batch and rerun the prototype from repo-tracked instructions.
- **Dependencies:** Tanisha's Knowledge Plugin is the preferred guidance source, but Aaron should still scaffold the pipeline and data flow before that artifact is fully polished.
- **Coordination:** Hand the generated batch to Akshat for validation and keep provenance / prompt metadata explicit so Alex can define the evaluation methodology against the real prototype.

### #51 — Quality evaluation methodology: LLM-as-Judge against hand-crafted reference set, with circularity handling
- **Owner:** Alex
- **What this means:** Define the PS B evaluation protocol so generated scenarios are assessed against the hand-crafted set with clear circularity and leakage handling.
- **Deliverables:** Written methodology, acceptance criteria, comparison dimensions, and explicit circularity caveats.
- **Done when:** Akshat can apply the methodology during validation and Alex can defend the setup in the paper without hand-waving.
- **Coordination:** Send the concrete rubric to Aaron and Akshat before W4 validation begins so generation and validation use the same standard.

### #77 — NeurIPS abstract outline + title candidates
- **Owner:** Alex
- **What this means:** Turn the paper lane into a concrete abstract plan early, before final prose crunch time.
- **Deliverables:** Candidate title list, abstract outline, and a short note on the central claim / evidence structure.
- **Done when:** The final abstract task in W5 can be executed from a prepared outline rather than drafted from scratch under deadline pressure.
- **Coordination:** Pull only missing factual bullets from teammates; keep final framing ownership with Alex.

## W4 — Optimization, comparison, and failure analysis

### #29 — Apply INT8 quantization via vLLM
- **Owner:** Aaron
- **What this means:** Stand up the quantized serving configuration used for the MCP-optimized condition.
- **Deliverables:** Working INT8 config / invocation and notes on model behavior.
- **Done when:** The quantized serving path is runnable as an experiment condition.

### #30 — KV-cache tuning experiments
- **Owner:** Aaron
- **What this means:** Explore the cache settings that affect latency / memory tradeoffs for the tool-calling workload.
- **Deliverables:** Small sweep results plus the chosen tuned setting for experiments.
- **Done when:** The team has a defensible KV-cache configuration and some evidence for why it was chosen.

### #31 — Batched tool-call scheduling implementation
- **Owner:** Akshat
- **What this means:** Implement the benchmark-side scheduling changes needed for the MCP-optimized condition.
- **Deliverables:** Code changes plus a note describing what was batched and how.
- **Done when:** The MCP-optimized condition is technically real, not just a paper idea.

### #32 — Run Experiment 2 (Orchestration comparison): 3 orchestrations × N multi-domain scenarios on MCP-baseline
- **Owner:** Alex
- **What this means:** Execute the orchestration comparison on the shared MCP-baseline stack.
- **Deliverables:** Run configs, experiment outputs, and clear labeling of AaT vs PE vs Hybrid (if enabled).
- **Done when:** The team has comparable results for the orchestration question.

### #33 — Reach 30+ scenarios
- **Owner:** Akshat
- **What this means:** Expand the scenario set beyond the W2 minimum into the paper-scale benchmark set.
- **Deliverables:** 30+ repo-tracked scenarios with coverage across the needed difficulty / domain combinations.
- **Done when:** Alex can treat the 30+ scenario set as the benchmark corpus for final runs.

### #34 — Notebook 03: orchestration comparison
- **Owner:** Alex
- **What this means:** Analyze and visualize the Experiment 2 results.
- **Deliverables:** Notebook, figures, and interpretation of AaT vs PE vs Hybrid if active.
- **Done when:** The orchestration story is ready for the paper and deck.

### #35 — Failure taxonomy classification + evidence table
- **Owner:** Alex
- **What this means:** Classify observed failures using the Berkeley categories with evidence, not vibes.
- **Deliverables:** Failure table linking concrete failed runs to taxonomy labels.
- **Done when:** Every major failure mode cited in the paper is grounded in a concrete example.

### #64 — Failure taxonomy visuals + mitigation plan
- **Owner:** Alex
- **What this means:** Convert the classification results into figures and an explicit mitigation roadmap.
- **Deliverables:** Visual summaries plus a written list of chosen mitigations and why they were selected.
- **Done when:** The team can explain not only what failed, but what they decided to fix first.

### #65 — Implement chosen mitigation(s) from failure taxonomy analysis
- **Owner:** Alex
- **What this means:** Turn the taxonomy work into code or pipeline changes.
- **Deliverables:** One or more concrete mitigation changes, such as Self-Ask or orchestration checks.
- **Done when:** The mitigation is live in the stack and ready for rerun.

### #66 — Re-run affected benchmark cells after mitigation and compare before/after
- **Owner:** Alex
- **What this means:** Close the loop by showing the mitigation changed outcomes.
- **Deliverables:** Before/after comparison data and a short written conclusion.
- **Done when:** The paper can cite measured mitigation impact rather than only a proposed fix.

### #36 — Collect before/after profiling data across all metrics
- **Owner:** Alex
- **What this means:** Consolidate the final analysis-ready metrics for the report.
- **Deliverables:** Clean metric set and figure inputs for paper / presentation.
- **Done when:** Final reporting no longer depends on raw log spelunking.

### #37 — Runbook section: infrastructure / serving / Slurm / profiling setup (`docs/runbook.md`)
- **Owner:** Aaron
- **What this means:** Own the infra half of the runbook.
- **Deliverables:** Setup instructions for environment, serving, Slurm jobs, and profiling capture.
- **Done when:** A teammate could reproduce the infra side without asking Aaron for verbal help.

### #67 — Runbook section: eval harness / scenario execution / judge reproduction (`docs/runbook.md`)
- **Owner:** Akshat
- **What this means:** Own the benchmark-execution half of the runbook.
- **Deliverables:** Instructions for scenario files, harness invocation, judge scoring, and output interpretation.
- **Done when:** A teammate could reproduce the harness side without asking Akshat for verbal help.

### #38 — GCP fallback setup instructions — how to spin up A100 instance if Insomnia is down
- **Owner:** Aaron
- **What this means:** Document the emergency fallback path so compute issues do not stall the schedule.
- **Deliverables:** Concrete setup doc with machine type, startup path, env setup, and shutdown guidance.
- **Done when:** The team has a tested or at least mechanically complete fallback path in writing.

### #68 — Auto-scenario generation scale-up — refine pipeline and expand generated scenario set
- **Owner:** Aaron
- **What this means:** Turn the prototype into a larger, cleaner PS B batch by improving prompts, filters, and generation hygiene.
- **Deliverables:** Revised generation path, expanded candidate set, and a short note on what changed from the prototype.
- **Done when:** Akshat has a stable generated batch large enough to validate and land, and the team can plausibly hit the final 50+ scenario target.
- **Dependencies:** W3 prototype, Tanisha's Knowledge Plugin, and Alex's evaluation methodology.
- **Coordination:** Preserve source metadata and generation settings so later comparison work can distinguish hand-authored versus generated scenarios without reconstructing provenance from commit history.

### #53 — Validate auto-generated scenarios against hand-crafted reference set
- **Owner:** Akshat
- **What this means:** Review the generated scenarios against the reference set and the agreed methodology, then decide which ones are good enough to keep.
- **Deliverables:** Accepted / rejected set, notes on key failure patterns, and approved generated scenarios committed to the canonical repo.
- **Done when:** The canonical repo contains an approved generated batch and Alex can cite the validation process concretely.
- **Dependencies:** Aaron's generated batch and Alex's evaluation methodology.
- **Coordination:** Keep accepted generated scenarios clearly labeled as generated so later notebook and paper analysis can separate them from the manual Smart Grid set.

### #52 — Comparative analysis: hand-crafted vs auto-generated scenarios on agent performance, in notebook 04
- **Owner:** Alex
- **What this means:** Analyze how the manual and generated scenario sets differ once the benchmark actually runs on them.
- **Deliverables:** Notebook 04, comparison tables / figures, and a short interpretation of what PS B changes in the evaluation story.
- **Done when:** The team has publication-ready evidence comparing hand-authored and generated scenarios.
- **Dependencies:** Approved generated scenarios, benchmark results on both scenario sources, and provenance labels that identify manual versus generated inputs.
- **Coordination:** Pull missing metadata from Aaron and Akshat in structured form so the notebook logic stays reproducible.

### #68 — Reach 50+ scenarios total in canonical repo (manual + auto-generated)
- **Owner:** Akshat
- **What this means:** Own the final scenario inventory milestone after both the manual Smart Grid work and the approved generated batch are counted together.
- **Deliverables:** Canonical repo scenario count at or above 50, with clear provenance markers for manual versus generated sources.
- **Done when:** Alex can cite the final scenario count cleanly in the paper and the repo structure makes source attribution obvious.
- **Dependencies:** Akshat's manual scenario work and the approved generated batch from the validation task above.
- **Coordination:** Do not merge generated scenarios into the manual set in a way that hides provenance; keep filenames, metadata, or directory structure explicit.

## W5 — Writing and delivery

### #39 — NeurIPS draft — Datasets & Benchmarks Track format
- **Owner:** Alex
- **Done when:** A full paper draft exists in the NeurIPS format with the current results integrated.

### #78 — Class report back-port checklist from NeurIPS draft to IEEE template
- **Owner:** Alex
- **What this means:** Write the conversion checklist before the final report crunch so back-porting from NeurIPS to the class format is mechanical instead of improvisational.
- **Deliverables:** Section-by-section checklist covering what maps directly, what must be shortened, and which figures / tables need alternate formatting.
- **Done when:** The final report task can follow a prepared checklist rather than re-deriving the conversion path from memory.

### #40 — Class final report — back-ported from NeurIPS draft to IEEE template
- **Owner:** Alex
- **Done when:** The class report is generated from the NeurIPS source without drifting content.

### #41 — Content brief: Methodology + Data + MCP server facts, 1-page bullet list
- **Owner:** Tanisha
- **Done when:** Alex has a concise fact pack for the data / server sections, not prose paragraphs to rewrite from scratch.

### #42 — Content brief: Scenarios + Eval + judge facts, 1-page bullet list
- **Owner:** Akshat
- **Done when:** Alex has the factual input needed for the scenario / eval sections.

### #43 — Content brief: Infrastructure + Profiling + serving facts, 1-page bullet list
- **Owner:** Aaron
- **Done when:** Alex has the factual input needed for the infra / profiling sections.

### #44 — Final presentation deck
- **Owner:** Alex
- **Done when:** The class presentation is complete and consistent with the paper / results.

### #45 — WandB dashboard polish
- **Owner:** Team
- **Done when:** The dashboard is presentable and organized for final review.

### #46 — Open-source PR to AssetOpsBench
- **Owner:** Team
- **Done when:** The contribution subset is isolated, cleaned, and proposed upstream.

### #47 — NeurIPS 2026 abstract
- **Owner:** Alex
- **Done when:** The abstract is submitted by the deadline.

### #48 — NeurIPS 2026 full paper submission
- **Owner:** Alex
- **Done when:** The final NeurIPS submission is uploaded by the deadline.

### #49 — Runbook final review — verify all experiments are reproducible from doc
- **Owner:** Team
- **Done when:** At least one teammate other than the original author has sanity-checked the runbook flow.

### #54 — Paper section on Problem Statement B methodology + circularity discussion
- **Owner:** Alex
- **What this means:** Write PS B into the paper as a real extension with methodology, limitations, and circularity discussion, not a vague future-work paragraph.
- **Deliverables:** Paper subsection covering generation setup, validation methodology, comparison results, and circularity caveats.
- **Done when:** The draft can present PS B as committed project work with evidence behind it.
- **Dependencies:** Notebook 04 plus the underlying generation / validation artifacts from W3-W4.
- **Coordination:** Ask Aaron, Akshat, and Tanisha only for factual corrections or missing bullet points; keep final prose ownership with Alex so the paper voice stays unified.
