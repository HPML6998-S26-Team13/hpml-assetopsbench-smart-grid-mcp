# Team 13 Meeting Notes -- April 7, 2026

*Weekly team sync, 2:45 PM ET.*
*Source of truth: reconciled from the Notion meeting page summary + transcript on Apr 8, 2026.*

## Attendance

- Alex
- Aaron
- Akshat
- Tanisha

## What was shared on the call

### Alex

- Midpoint report was submitted on Apr 6.
- Team repo was made public and project docs were reorganized for public visibility.
- WatsonX setup and benchmarking were completed and documented.
- Email was sent to Dhaval about the Hybrid orchestration idea.
- Alex planned to rebalance work, update the task tracker, and move task management onto GitHub Projects.

### Tanisha

- All four MCP servers were already implemented as skeletons on a shared base.
- The MCP stack was tested end-to-end with Claude Desktop.
- A prompt using all four domains succeeded, including work-order generation.
- Cloud / config setup for MCP testing was already in place.

### Aaron

- The compute plan was completed and committed.
- Insomnia / vLLM environment setup was in progress.
- The setup work was being driven through Cloud Code.

### Akshat

- Smart Grid scenarios had been drafted locally using the team's dataset and AssetOpsBench examples as reference.
- Scenario format had been validated programmatically.
- A benchmark run had been executed locally with Llama 3 70B as a system check.
- A local README / instruction set for running the benchmark had been written.
- Merge conflicts were preventing Akshat from pushing the work at call time.

## Decisions made

### Paper and writing

- The team agreed to pursue the NeurIPS 2026 Datasets & Benchmarks submission as a real target, not just a vague stretch mention.
- Alex takes lead on the paper writing.
- The writing flow is: draft in NeurIPS format first, then back-port to the class IEEE report format.
- Tanisha no longer carries primary paper-writing load; she remains the Overleaf admin / maintainer but is freed to focus on technical work.
- Teammate written contributions should be content briefs / factual inputs, not independent prose sections.

### Project management and repo workflow

- GitHub Projects should become the canonical task-tracking surface.
- Aaron's new GitHub organization / project board should replace scattered task tracking.
- The team should wait for Alex's canonical push before making more repo changes, to avoid multiplying conflicts.

### Problem Statement B / future work

- The team was positive on Problem Statement B as a stretch track.
- The intended ownership pattern discussed on the call was:
  - Aaron: auto-scenario generation pipeline
  - Tanisha: Knowledge Plugin / standards encoding
  - Alex: evaluation methodology + comparative analysis + paper framing
  - Akshat: light validation only if core W2 work is caught up
- This was discussed as conditional / stretch scope, not as immediate W2 core work.

## Important technical takeaways

- Tanisha's MCP work is ahead of plan, but it has only been demonstrated through Claude Desktop so far, not yet through the benchmark Llama path.
- Akshat appears to have more local progress than the repo showed at the time of the call, but that progress was not yet merged.
- The team re-affirmed the async benchmarking model: W2 is coordinated setup, but W3-W4 benchmark runs should be batch jobs rather than people sitting together during runs.
- The Hybrid orchestration idea remained dependent on mentor novelty feedback.

## Decisions that were still not fully made

These remained unresolved at the end of the call and should be treated as open planning items:

1. **Profiling harness authorship split**
   The team did not fully settle the exact boundary between Aaron's capture-layer work and Alex's analysis-layer work.

2. **Runbook ownership split**
   The call acknowledged that Aaron and Akshat both touched the runbook area, but did not define a final split.

3. **Exact MCP hardening / integration split**
   Tanisha clearly owns the MCP servers, but the call did not fully pin down the handoff contract between Tanisha's server work and Akshat's harness work.

4. **Scenario realism validation**
   The team agreed that format validation is not enough and that Dhaval should help validate whether the scenarios look realistic for real-world maintenance use.

5. **Hybrid go / no-go**
   Still pending mentor feedback.

## Action items from the call

### Alex

- Update GitHub Projects from the task tracker.
- Force-push / canonicalize the team repo state.
- Rebalance load across the team and make the remaining tasks clearer.
- Investigate profiling harness and WandB integration ownership.
- Take over paper-writing flow and Overleaf writing responsibility.
- Follow up with Dhaval on Hybrid orchestration and scenario realism.

### Aaron

- Finish Insomnia cluster environment setup.
- Verify what remains in the server-hardening lane versus what is already done.
- Repoint local git remote / workflow to the new organization repo.

### Akshat

- Resolve merge conflicts.
- Push scenarios and benchmark / harness work onto the canonical repo.
- Coordinate with Aaron on the runbook split.

### Tanisha

- Validate the MCP servers with the benchmark Llama path, not only with Claude Desktop.

## Implications for the tracker

- Local-only work discussed on the call should be treated as **in progress**, not done, until merged into the canonical repo.
- Ambiguous two-owner tasks should be split into single-owner tasks with explicit coordination notes.
- The failure taxonomy line item should be expanded into classification, mitigation planning, implementation, and rerun work rather than left as one catch-all bullet.
