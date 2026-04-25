# Apr 21, 2026 | HPML Final Project - Team 13 Sync

Attendees: [Alex Xin](mailto:wax1@columbia.edu), [Akshat Bhandari](mailto:ab6174@columbia.edu), [Tanisha Rathod](mailto:tr2828@columbia.edu), [Aaron Fan](mailto:af3623@columbia.edu)

Sources: Notion `Team check-in #4` page `HPML Final Project - Team 13 Sync @Tuesday 6:15 PM (EDT)`, Google Drive Meet chat for `2026/04/21 18:15 EDT`, and both local Meet caption tracks for the matching recording (`Recording-en-1.vtt`, `Recording-en-asr.vtt`).

## Overview

This call converted the Apr 16 / Apr 20 repo cleanup into a W4 execution contract. The team had merged the main proof and scaffold PR wave, but the meeting evidence was clear that the project still needed real experiment captures rather than more planning language.

The main decision was to treat [#25](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/25) as the next execution gate: one clean Experiment 1 run should prove that PyTorch profiling, WandB logging, and NVIDIA / GPU utilization capture are all producing the expected artifacts. The team also used the call to surface practical Insomnia risks around CUDA consistency, model revision consistency, storage placement, and terminal/session hygiene.

## Summary

- **Repo / board status discussed during the call:**
  - the Apr 20-21 PR wave had made PE, Self-Ask PE, Verified PE, notebook scaffolds, server hardening, judge logs, and benchmark harness evidence much more concrete
  - [#25](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/25) remained the key Experiment 1 capture gate
  - Akshat still expected to push remaining open issue work from the previous week by Apr 21 or Apr 22
  - [#111](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/111) remained a last-mile Insomnia script / docs reconciliation item, not a broad design blocker

- **Experiment 1 discussion:**
  - Akshat proposed using [#25](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/25) as a practical validation run rather than waiting for polished benchmark numbers
  - that one run should check whether PyTorch profiling, WandB logging, and NVIDIA / GPU capture produce the expected metrics
  - live repo state after reconciliation: [#7](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/7), [#27](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/27), [#37](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/37), and [#59](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/59) were closed, but [#25](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/25) itself was still open

- **Experiment 2 discussion:**
  - the team moved from "is the scaffolding present?" to "can the missing AaT / ReAct path actually run?"
  - the follow-up work should keep Notebook 03 honest about which orchestration arms have real captures versus staged scaffolding

- **Insomnia / reproducibility discussion:**
  - CUDA version variability across Insomnia allocations was called out as a risk to record, even if the current shared environment smooths over much of it
  - the team should standardize model runtime, model name, and model revision / checkpoint where possible
  - no training checkpoints are expected for this project; the storage concern is mostly model downloads, generated artifacts, logs, and avoiding login-node disk pressure
  - `tmux` / session helpers are acceptable for keeping login sessions usable, but compute-heavy work must stay on Slurm compute allocations

- **Model / scope discussion:**
  - the team questioned whether the 7B / 8B local model lane is enough for the final claim
  - the working default remains local 8B as the main run grid, with 70B as selective spot-check evidence rather than a full duplicated experiment matrix
  - this should be kept as an advisor / final-story question rather than silently expanding scope

## Decisions / Status

### Decided during the call

- Use [#25](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/25) as the immediate proof run for Experiment 1 instrumentation readiness.
- Treat the first [#25](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/25) pass as an artifact / metrics-production validation, not as final benchmark interpretation.
- Keep CUDA version, model runtime, model revision, and storage location visible in run artifacts and docs.
- Use Slurm jobs / `sbatch` for real compute work; use `tmux` or watch helpers only for session persistence and monitoring.
- Plan the next team sync for Tuesday, Apr 28, around final evidence readiness and final-week cut lines.

### Resolved later in post-call planning

- **[#50](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/50) Knowledge Plugin artifact** - closed on Apr 23 by PR [#122](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/pull/122). This means the PS B standards artifact is no longer a planning gap, though generated-scenario authoring / validation still need proof.
- **[#111](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/111) Insomnia setup reconciliation** - closed after PR [#125](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/pull/125) landed the final HF CLI fix and the shared Insomnia checkout was verified on `main@b480604`.
- **[#104](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/104) Agent-as-Tool runner** - closed by PR [#126](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/pull/126), and Aaron subsequently landed the direct/MCP AaT runner stack. The remaining evidence gate moved to [#25](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/25): successful Cell A / Cell B smoke and capture proof.
- **[#112](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/pull/112) older Copilot draft** - closed on Apr 21 without merge and is no longer the canonical path for benchmark-smoke evidence.
- **[#7](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/7), [#27](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/27), [#37](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/37), and [#59](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/59)** - are closed. The remaining risk is whether [#25](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/25) produces one coherent capture set that ties those pieces together.

## Action Items

See the live [GitHub Project](https://github.com/orgs/HPML6998-S26-Team13/projects/1/views/1) for canonical task tracking. This list reflects the meeting evidence plus the Apr 24 repo state.

- [ ] Aaron: land / prove [#25](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/25) with one coherent capture set that shows PyTorch profiling, WandB logging, and NVIDIA / GPU utilization artifacts.
- [ ] Alex / team: keep draft PRs [#123](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/pull/123) / [#124](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/pull/124) grounded in real capture readiness; do not let Notebook 02 / 03 or paper text imply final evidence before [#25](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/25) has actual artifacts.
- [ ] Team: decide by Apr 28 whether local 8B plus selective 70B spot-checks is enough for the final story, or whether an advisor question / explicit limitation is needed.
- [x] Tanisha: close the structured standards artifact for [#50](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/50) via PR [#122](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/pull/122).
- [x] Shared infra: close [#111](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/111) via PR [#125](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/pull/125).
- [x] Aaron / Alex: land the core [#104](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/104) AaT runner path; remaining smoke/capture evidence is tracked under [#25](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/25).

## Notes

- The Drive chat artifact for this meeting contained only one side link; the substantive meeting content came from the Notion summary/transcript and the two Meet caption tracks.
- The Apr 21 planning docs were originally written for the regular 2:45 PM slot, but the recorded meeting source is the 6:15 PM EDT Team check-in #4.
- The cleanest Apr 28 conversation is evidence-first: what is runnable, what has committed artifacts, what remains draft-only, and what must be cut if it is still not real.
