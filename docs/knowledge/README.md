---
title: Generated Scenario Knowledge
slug: readme
type: index
status: canonical
created: 2026-05-07
updated: 2026-05-07
owner: Team 13
scope: team-repo
canonical: true
---

# Generated Scenario Knowledge

Support data and authoring contracts for generated Smart Grid scenarios.

## Canonical Files

- [`generated_scenario_authoring_and_ground_truth.md`](generated_scenario_authoring_and_ground_truth.md) — no-hint authoring contract, ground-truth rules, and promotion expectations.
- [`scenario_generation_support.json`](scenario_generation_support.json) — structured scenario-family support data consumed by `scripts/generate_scenarios.py`.
- [`generated_scenario_template.json`](generated_scenario_template.json) — annotated JSON template for generated candidate scenarios.

Generated scenario candidates are not canonical benchmark scenarios until promoted into `data/scenarios/` and validated by `data/scenarios/validate_scenarios.py`.