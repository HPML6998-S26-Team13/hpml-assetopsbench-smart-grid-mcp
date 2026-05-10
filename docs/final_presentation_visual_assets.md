---
status: active-draft
scope: final presentation visual asset handoff
owner: Team 13
canonical: true
---

# Final Presentation Visual Assets

Generated: 2026-05-07

This handoff records the team-repo visual assets rendered for the final HPML
presentation. The class deck should prefer workload and result visuals over
project-status visuals.

## Newly Rendered Assets

| Slide use | PNG | SVG | Source |
|---|---|---|---|
| Mitigation before/after | `results/figures/final_deck_mitigation_before_after.png` | `results/figures/final_deck_mitigation_before_after.svg` | `results/metrics/mitigation_before_after.csv` |
| Profiling spot-check table | `results/figures/final_deck_profiling_spotcheck_summary.png` | `results/figures/final_deck_profiling_spotcheck_summary.svg` | `results/metrics/profiling_inventory.csv` |
| Profiling A100 telemetry | `results/figures/final_deck_profiling_nvidia_smi_timeseries.png` | `results/figures/final_deck_profiling_nvidia_smi_timeseries.svg` | `profiling/traces/profile_spotcheck_20260507T0604Z_*_nvidia_smi/nvidia_smi.csv` |
| Artifact lineage | `results/figures/final_deck_artifact_lineage.png` | `results/figures/final_deck_artifact_lineage.svg` | `results/metrics/evidence_registry.csv`, `results/metrics/scenario_scores.jsonl` |

Regenerate with:

```bash
python3 scripts/render_final_deck_visuals.py
```

## W&B Capture Note

The four profiler spot-check rows have W&B run IDs and URLs, but anonymous
browser capture currently lands on a W&B login/404 page. Do not use that
anonymous screenshot in the deck.

If a logged-in browser is available, the best capture targets are:

| Cell | W&B run ID | URL |
|---|---|---|
| AT_M | `9a5ttz8w` | https://wandb.ai/assetopsbench-smartgrid/assetopsbench-smartgrid/runs/9a5ttz8w |
| AT_T | `ig9zgy82` | https://wandb.ai/assetopsbench-smartgrid/assetopsbench-smartgrid/runs/ig9zgy82 |
| PE_S_M | `bb7ude34` | https://wandb.ai/assetopsbench-smartgrid/assetopsbench-smartgrid/runs/bb7ude34 |
| V_S_M | `2kyquhk1` | https://wandb.ai/assetopsbench-smartgrid/assetopsbench-smartgrid/runs/2kyquhk1 |

Fallback for the deck: use
`results/figures/final_deck_profiling_spotcheck_summary.png` plus
`results/figures/final_deck_profiling_nvidia_smi_timeseries.png`. These are
actual local profiler evidence and avoid presenting a login-gated W&B page.

## Usage Cautions

- Treat profiler visuals as observability evidence, not judged task-quality
  evidence.
- Treat mitigation visuals as post-PR175 paper-grade evidence, with the
  #66 wording: mixed effects / selective repair, not universal mitigation lift.
- Do not use the scenario status/progress-bar visual in the class deck. The
  scenario-count point belongs in narration or a compact source/caption line,
  not as a hard-science results visual.
