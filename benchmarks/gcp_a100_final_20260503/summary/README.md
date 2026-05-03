# GCP A100 Final Evidence Pullback

Pulled from `smartgrid-a100-spot-20260503-0217` in `us-central1-a` on 2026-05-03. VM was a Spot `a2-highgpu-1g` with `NVIDIA A100-SXM4-40GB`; boot disk `autoDelete=false`.

This bundle contains 19 completed rows x 30 trials = 570 trajectory JSONs and 570 judge logs: 9 final matrix rows, 2 optimized-transport follow-ons, and 8 mitigation rows across the 4-tier ladder (`baseline`, `guard`, `repair`, `adjudication`).

The remote checkout was `team13/main@e5e1331` plus VM-side runtime patches captured in `logs/gcp_a100_runtime_patch_20260503T160400Z.diff`.
