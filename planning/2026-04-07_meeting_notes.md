# Apr 7, 2026 | HPML Final Project - Team 13 Sync

Attendees: [Alex Xin](mailto:wax1@columbia.edu), [Akshat Bhandari](mailto:ab6174@columbia.edu), [Tanisha Rathod](mailto:tr2828@columbia.edu), [Aaron Fan](mailto:af3623@columbia.edu)

### Overview

This call marked the transition from midpoint check-in into execution mode. The team had real technical progress, but the repo and planning surfaces were out of sync with what had been completed locally. Tanisha had the strongest pushed technical progress. Aaron had completed compute planning and started the Insomnia path. Akshat reported meaningful local scenario and harness progress, but it had not landed in the canonical repo yet. Alex was coordinating repo cleanup, planning, and writing.

The main non-technical theme was coordination debt. Too many plans were living in too many places. The team agreed to move to GitHub Projects as the canonical planning surface, and to let Alex force-align the repo first before others piled on more changes. This is now done, with the Project plan and all tasks updated, making use of GitHub's project management capabilities. Going forward, tracker refers to this page:
https://github.com/orgs/HPML6998-S26-Team13/projects/1/views/1

One major technical theme discussed is benchmarking: it is async batch work, not a synchronous everyone-online workflow. That changes how responsibilities should be split. Aaron owns the infra that makes jobs runnable. Tanisha owns server behavior. Akshat owns scenarios and harness execution. Alex owns experiment design, orchestration, and analysis.


### Summary

- **Week 1 recap:**
  - Midpoint report submitted Apr 6
  - WatsonX verified and benchmarked
  - team repo made public
  - Alex emailed Dhaval about Hybrid orchestration idea

- **Status updates:**
  - **Tanisha** — 
    - all four MCP server skeletons implemented on a shared base
    - demonstrated end-to-end through Claude Desktop, including work-order generation
  - **Aaron** — 
    - compute plan complete and committed
    - Insomnia / vLLM environment setup underway
    - live serve proof still pending
  - **Akshat** — 
    - local Smart Grid scenarios drafted
    - scenario format validated programmatically
    - local benchmark system-check run completed
    - local benchmark README written
    - merge conflicts blocking push
  - **Alex** — 
    - midpoint report shipped
    - repo publicization / docs cleanup underway
    - WatsonX setup and benchmarking completed
    - orchestration novelty question sent to Dhaval

- **Paper / writing:**
  - Team agreed to treat NeurIPS 2026 Datasets & Benchmarks as a real target
  - Alex takes lead on writing; write to NeurIPS format first, then back-port to class IEEE report format
  - Tanisha can remain Overleaf admin but no longer expected to handle primary writing, help load-balance

- **Project management / repo workflow:**
  - GitHub Projects becomes the canonical task-tracking surface, thanks Aaron
  - Aaron created new GitHub organization and invited team members
  - New project board available for centralized task tracking
  - New repo + board replaces existing docs / lists
  - Team members: wait for Alex's push before adding on changes

- **Benchmarking / infrastructure:**
  - benchmark smoke test available to verify Watson API connectivity (Akshat)
  - local benchmark README / execution notes written (Akshat)
  - MCP servers still need validation on benchmark Llama path, not only Claude Desktop (Tanisha)

- **Orchestration:**
  - The team revisited Agent-as-Tool vs Plan-Execute from Dhaval's lecture
  - Agent-as-Tool stronger on benchmark performance; Plan-Execute better aligned with IBM's production resource-planning logic
  - Alex proposed Hybrid approach, PE + reflection checkpoints, but dependent on mentor novelty feedback

- **Dataset / scenarios:**
  - Synthetic `transformer_id` join strategy (20 created) working as unifying bridge (for joining) across Kaggle datasets (Tanisha)
  - Scenario generation by imitation of existing AssetOpsBench examples underway (Akshat)
  - Format validation completed programmatically (Akshat)
  - Real-world applicability validation still needed, need to consult with Dhaval (Akshat)
  - Non-open-source dataset can be used for model development but not redistributed; weights and biases usage is acceptable (Tanisha)

- **Problem Statement B / future work:**
  - Discussed Problem Statement B as a future-work lane
  - Intended ownership pattern: Aaron - auto-scenario generation pipeline, Tanisha - Knowledge Plugin, Alex - evaluation methodology, comparison, paper framing, Akshat - scenario validation, finalize
  - Positive sentiment, not yet hard commitment, need to check in after W2

### Decisions captured on the call

**Decided during the call**
- NeurIPS 2026 Datasets & Benchmarks track is real target, Alex owns paper-writing stream
- Writing will happen in NeurIPS format first, then back-port to IEEE format for the class report
- GitHub Projects to be canonical task-tracking system
- The team waits for Alex's canonical repo push before making more changes

### Resolved later in post-call planning

- **Profiling harness authorship split** — resolved into Aaron owning capture layer, Alex owning experiment design + analysis. Now split in tracker:
    - [#7](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/7) `Profiling capture wrappers — PyTorch Profiler around benchmark runs`
    - [#59](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/59) `Profiling capture wrappers — Nsight / nvidia-smi / GPU utilization collection`
    - [#26](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/26) `Notebook 02: latency analysis — MCP overhead experiment design, parsing, and writeup`
- **Runbook ownership split** — resolved into Aaron owning infra half, Akshat owning the harness / execution half. Now split:
    - [#37](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/37) `Runbook section: infrastructure / serving / Slurm / profiling setup`
    - [#67](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/67) `Runbook section: eval harness / scenario execution / judge reproduction`
    - [#49](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/49) `Runbook final review — verify all experiments are reproducible from doc`
- **Exact MCP hardening / integration split** — resolved into Tanisha owning server hardening / tests / benchmark-path validation, Akshat owning harness-side integration, see: [#9](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/9), [#10](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/10), [#11](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/11), [#12](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/12), [#13](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/13), [#58](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/58), and [#3](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/3)
- **Scenario realism validation** — still open, but now explicitly captured as:
    - [#60](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/60) `Real-world scenario validation plan`
    - [#63](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/63) `Follow up with Dhaval on hybrid orchestration novelty and Smart Grid scenario realism / validation criteria`
- **Hybrid go / no-go** — still open in substance, but now clearly represented by [#63](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/63), [#23](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/23), and [#24](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/24)
- **Problem Statement B scope** — discussed on call as conditional / stretch, then later promoted into committed W3-W5 work, reflected in tracker

### Action Items

See [GitHub project](https://github.com/orgs/HPML6998-S26-Team13/projects/1/views/1) for canonical task tracking and up to date status.

**Immediate follow-up after the call**
- [ ] Akshat: Resolve merge conflicts and push scenarios + harness docs
- [ ] Akshat and Aaron: Clarify runbook split
- [ ] Aaron: Finish Insomnia / vLLM environment setup (or confirm done via GitHub)
- [ ] Tanisha: Validate MCP servers with the benchmark Llama path, not only Claude Desktop
- [x] Alex: Update GitHub Projects from the task tracker, canonicalize the team repo state, and rebalance team load / clarify remaining tasks
- [x] Alex: Take over paper-writing flow and Overleaf writing responsibility
- [ ] Alex: Follow up with Dhaval on Hybrid novelty and scenario realism
- [x] Alex: Move onto GitHub Projects as the canonical task system
- [ ] Team: Repoint local git remote / workflow to the new organization repo

**How these were operationalized in the tracker and GitHub issues**
- [ ] Akshat: [#56](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/56) `Replay local Smart Grid scenario files onto canonical team13/main and push first batch`
- [ ] Akshat: [#57](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/57) `Replay local benchmark / harness README work onto canonical team13/main and push`
- [ ] Akshat: [#3](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/3), [#18](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/18), and [#20](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/20) for the first end-to-end ladder
- [ ] Aaron: [#6](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/6) `Successful first Insomnia A6000 vLLM serve smoke test for Llama-3.1-8B-Instruct`
- [ ] Aaron: [#8](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/8) `Generic Slurm experiment template for benchmark jobs`
- [ ] Aaron: [#7](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/7) and [#59](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/59) for profiling capture wrappers
- [ ] Tanisha: [#58](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/58) plus [#9](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/9)-[#13](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/13)
- [ ] Team: [#19](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/19) `Each team member sync canonical team13/main, install ibm-watsonx-ai into .venv, and run the verify script locally`

### Implications for the tracker

- Local-only work discussed on the call should still be treated as **in progress**, not done, until merged into the canonical repo.
- Ambiguous two-owner tasks from the call have since been split into single-owner issues with explicit coordination notes.
- The failure taxonomy line item was expanded post-call into classification, visualization, mitigation, rerun, and write-up work rather than left as one vague bullet.
- The Apr 7 call should now be read together with the later planning cleanup in the tracker and GitHub project. The meeting notes preserve what was said on the call; the issue system captures the more precise post-call operationalization.
