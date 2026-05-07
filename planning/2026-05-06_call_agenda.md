---
status: active-reference
scope: team-repo planning
owner: Team 13
canonical: true
---

# Team 13 Final-Submission Sync - May 6, 2026

*Goal: align on what is done, what is landing, and what remains before the final submission deadlines.*

## Deadline Snapshot

- NeurIPS full paper: Wednesday 2026-05-06 23:59 AOE, about Thursday 2026-05-07 08:00 ET.
- Class presentation: Thursday 2026-05-07, 3:00 PM ET.
- CourseWorks final package: Friday 2026-05-08, 23:59 ET.

## Agenda

### 1. What Is Complete

- Scenario floor is complete: 31 top-level benchmark scenarios are on main.
- Final evidence artifacts are on main: post-PR175 summaries, mitigation before/after CSV, manual judge audit, runbook/infra brief, token-throughput guardrails, and deadline config universe.
- NeurIPS artifact package is published: reviewer artifact, Croissant metadata, code snapshot, and submission packet links are recorded.
- The PS B generator work is framed correctly as methodology/candidate evidence, not benchmark corpus evidence.

### 2. Merge-Ready Final PR Wave

- PR #183: L3 v1 plus bantipatel20 DGA report card.
- PR #189: failure-evidence audit table.
- PR #191: generated-scenario disposition table.
- Treat these as merge-ready for meeting purposes. Do not spend call time reopening review minutiae unless a true blocker appears.

### 3. In Progress Before NeurIPS Full Submit

- Final PDF/checklist pass: figures, tables, captions, references, appendix links, artifact URLs, anonymized author block, OpenReview metadata, and final PDF checksum.
- Final PII/anonymity scrub over the exact uploaded PDF and submission sources.
- Final paper wording: mitigation is mixed; generated scenarios are candidate/methodology evidence; 70B results need explicit per-cell sample counts.

### 4. Class Deliverables After NeurIPS

- Back-port NeurIPS paper to the IEEE class report.
- Finalize presentation deck for Thursday 2026-05-07.
- Finish CourseWorks package: root README, deliverables directory, report PDF, deck/PDF, W&B/dashboard links, license, pinned environment, and AI-use disclosure.

### 5. Team Ownership Check

- Alex: NeurIPS final submit, class report back-port, CourseWorks package, final deck integration.
- Aaron: runbook/reproducibility facts, infra/profiling/serving facts, dashboard/run-link sanity.
- Akshat: L3/report-card PR, failure-evidence audit PR, generated-scenario disposition PR.
- Tanisha: methodology/data-pipeline wording, PS B framing, AOB/upstream package support if time allows.

## Decisions

1. **Late compute evidence policy:** Do we let new raw compute results change the main paper today?
   - Recommendation: no. Use only validated, pulled, judged, and paper-integrated evidence for the main NeurIPS claims. Anything still running can be appendix/future-work material after validation.
2. **Final PR wave policy:** Do PR #183/#189/#191 need discussion before merge?
   - Recommendation: no, unless a new Critical/High blocker appears. Treat them as landing and move meeting time to submission readiness.
3. **AOB upstream timing:** Do we try to open the IBM upstream PR before the NeurIPS full-paper deadline?
   - Recommendation: only if the package is already assembled. Do not let it delay NeurIPS full-paper upload or Thursday presentation prep.
