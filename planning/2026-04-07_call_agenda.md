# Team 13 Call -- April 7, 2026 (Tuesday, 2:45 PM ET)

## Agenda (30 min)

**0:00-0:05 -- Week 1 recap**
- Mid-checkpoint submitted (Apr 6)
- Dhaval feedback: liked report, endorsed NeurIPS 2026 submission
- AssetOpsBench fork synced with upstream (48 new commits, src/workflow/ -> src/agent/ rename)
- WatsonX API: registered on Codabench, request posted

**0:05-0:15 -- Status readouts (2-3 min each)**
- Akshat: Evaluation harness status, Smart Grid scenario drafts
- Tanisha: MCP server skeleton progress, dataset integration
- Aaron: Compute plan, Insomnia/GCP environment status
- Alex: Proposal finalized, Overleaf shared with Dhaval, task tracker created

**0:15-0:22 -- Week 2 planning**
- Priority: IoT + TSFM MCP servers functional by Apr 13
- Target: 15+ validated scenarios by Apr 13
- First baseline agent trajectory through MCP
- WandB project setup with initial experiment structure
- Who handles FMSR and WO server implementation?

**0:22-0:27 -- NeurIPS 2026 discussion**
- Datasets & Benchmarks Track: abstract May 4, submission May 6
- Dhaval endorsed it; Akshat noted it's ambitious but doable
- Decision: do we commit to targeting NeurIPS alongside class deliverables?
- If yes: what changes in our timeline? (report becomes paper draft)
- NeurIPS 2026 Overleaf template shared by Alex

**0:27-0:30 -- Logistics**
- WatsonX API key status (blocker for LLM-as-Judge evaluation)
- AssetOpsBench upstream changes -- notable: new VibrationAgent, AgentRunner ABC
- Confirm everyone has synced their fork

---

## Decisions needed

1. NeurIPS 2026: commit or defer?
2. MCP server ownership for FMSR and WO (Akshat? Tanisha?)
3. WatsonX fallback: if API access delayed, do we use local vLLM for judge too?
4. Dataset integration: common `transformer_id` approach -- does this work for all 5 Kaggle datasets?
