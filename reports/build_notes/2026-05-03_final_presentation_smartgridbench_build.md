---
status: canonical
scope: team-repo
owner: Team 13
canonical: true
---

# Final Presentation PPTX Draft Build Notes

*Created: 2026-05-03*
*Issue: #44*
*Artifact: `reports/2026-05-03_final_presentation_smartgridbench_draft.pptx`*

This file records the first editable final-presentation PowerPoint draft build.
The PPTX itself is the working deck artifact for subsequent manual edits. The
artifact-tool generation was a one-off build from the current deck scaffold, not
a committed deterministic pipeline.

## Source Inputs

- Story scaffold: `docs/final_presentation_deck.md`
- Production companion: `docs/final_presentation_run_of_show.md`
- Current metrics / figures referenced by slides: `results/metrics/`,
  `results/figures/`, and `docs/experiment_matrix.md`
- Current scenario gate: PR #156 remains open; the deck keeps 30 scenarios as
  the required floor rather than a completed claim.

## Build Command

The draft was generated with the local presentation artifact builder as a
one-off editable PPTX export. Machine-local runtime paths are intentionally
omitted from this public build note.

After generation, the file was moved to:
`reports/2026-05-03_final_presentation_smartgridbench_draft.pptx`.

## Verification

- `git diff --check team13/main...HEAD`
- Artifact-tool build completed: 12 slides.
- `file reports/2026-05-03_final_presentation_smartgridbench_draft.pptx`
  reported `Microsoft PowerPoint 2007+`.
- `unzip -t reports/2026-05-03_final_presentation_smartgridbench_draft.pptx`
  reported no compressed-data errors.
- GitHub `black` check passed on PR #164.

## Layout QA

The local layout checker reported `0 error(s), 7 warning(s)`.

Warnings accepted for this draft:

| Slide | Warning class | Note |
|---:|---|---|
| 1 | bottom padding | Small footer pill text is visually acceptable. |
| 2 | tight text | Card title wraps tightly but remains readable. |
| 7 | tight text | Interpretation box is tight but readable in the rendered preview. |
| 11 | tight text | Artifact-ledger card copy is tight but readable. |
| 12 | bottom padding | Three small closing metric cards have tight label padding: 3 warnings, one per card. |

## Open Build Gates

- Decide whether the final submitted deck keeps this artifact-tool visual
  system or gets converted into the class deck template.
- Re-check Slide 4 after PR #156 and any generated-scenario acceptance path
  settle.
- Promote Slide 10 from mitigation design to quantitative result only if
  before/after mitigation rows land.
- Dry-run against the 10-12 minute target before final submission.
