# Auto-scenario generation runbook (`#2`)

*Last updated: 2026-04-28*
*Owner: Aaron Fan (af3623)*
*Issue: [`#2`](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/2). Scale-up follow-on: [`#68`](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/68).*

How to produce a candidate Smart Grid scenario batch from `scripts/generate_scenarios.py`. Companion to:

- [`docs/knowledge/scenario_generation_support.json`](knowledge/scenario_generation_support.json) — family matrix + templates the generator consumes
- [`docs/knowledge/generated_scenario_authoring_and_ground_truth.md`](knowledge/generated_scenario_authoring_and_ground_truth.md) — no-hint contract + ground-truth schema the generator must satisfy
- [`docs/knowledge/generated_scenario_template.json`](knowledge/generated_scenario_template.json) — annotated scenario template
- [`docs/ps_b_evaluation_methodology.md`](ps_b_evaluation_methodology.md) — Akshat's validation rubric for the resulting batch

## What the generator does

```
support data + family matrix + handcrafted corpus
            │
            ▼
   build_prompt(family, axes, ctx)        ← inlines the no-hint rules
            │
            ▼
   call_llm(prompt, model)                ← LiteLLM → WatsonX (default) or local vLLM
            │
            ▼
   parse_response → attach_provenance → nearest_handcrafted
            │
            ▼
   validate_scenario (in-memory, via data/scenarios/validate_scenarios.py)
            │
   ┌────────┴────────┐
   ▼                 ▼
SGT-GEN-NNN.json   invalid/SGT-GEN-NNN.json   ← split by validation outcome
            │
            ▼
   batch_manifest.json (provenance roll-up)
```

## Output layout

```
data/scenarios/generated/<batch_id>/
    SGT-GEN-001.json            ← schema-clean scenarios, one per file
    SGT-GEN-002.json
    ...
    invalid/                    ← scenarios that failed the validator (with the error list)
        SGT-GEN-NNN.json        ← {"scenario": ..., "errors": [...]}
    prompts/                    ← exact prompts sent (one per scenario, for reproducibility)
        family_<FAMILY>_001.txt
    raw_responses/              ← raw LLM outputs before parsing (for debugging)
        family_<FAMILY>_001.json
    batch_manifest.json         ← model, temperature, seed, knowledge_plugin_version,
                                  list of emitted scenario IDs
```

`SGT-GEN-NNN.json` follows the canonical scenario schema (`id`, `type`, `text`, `category`, `characteristic_form`, `asset_id`, `expected_tools`, `domain_tags`, `difficulty`, `ground_truth`) plus two **nested** blocks required by [`docs/knowledge/generated_scenario_template.json`](knowledge/generated_scenario_template.json):

- **`provenance`** — nested object with `source_type=generated`, `generator_prompt_version`, `knowledge_plugin_version` (sha256 prefix of the support file), `generation_model`, `generation_date`, `batch_id`, `manual_cleanup` (and `cleanup_notes` if `manual_cleanup=true`).
- **`nearest_handcrafted_comparator`** — nested object with `scenario_id`, `scenario_file` (repo-relative path), `similarity_basis`, `novelty_note`, optional `nearest_match_weak`.

The generator's in-memory validator enforces both nested blocks and explicitly rejects the legacy top-level shape (e.g. `source_type` at the top level, or the wrong field name `nearest_handcrafted`). A scenario lands in the valid output path only if it passes both the canonical scenario schema **and** the generated-scenario contract; otherwise it lands under `<batch_id>/invalid/` with the validator's error list.

The validator (`data/scenarios/validate_scenarios.py`) intentionally only globs the top level of `data/scenarios/` (`*.json`), so a generated batch sitting under `data/scenarios/generated/` does **not** affect the team's CI gate. Generated scenarios must pass the team gate before being promoted into `data/scenarios/`.

## Prerequisites

- `litellm` in the active Python env. On Insomnia: `.venv-insomnia/bin/python` already has it (per `requirements-insomnia.txt`). Locally: `uv pip install -r requirements-insomnia.txt`.
- WatsonX credentials in `$REPO_ROOT/.env` (or exported in shell):
  ```
  WATSONX_API_KEY=...
  WATSONX_PROJECT_ID=...
  WATSONX_URL=https://us-south.ml.cloud.ibm.com
  ```
  (Setup: [`docs/reference/watsonx_access.md`](reference/watsonx_access.md).)

## Common invocations

### Dry run (no LLM call) — inspect prompts before spending credits

```bash
python scripts/generate_scenarios.py \
    --dry-run \
    --family FMSR_DGA_DIAGNOSIS \
    --n 1 \
    --batch-id dryrun_$(date +%Y%m%d) \
    --seed 42
```

Writes the assembled prompt(s) under `data/scenarios/generated/<batch_id>/prompts/` and a manifest with the invocation record. Use this to read what we're about to ask the model before spending credits.

### Single-family smoke (1 scenario, contract-clean)

```bash
python scripts/generate_scenarios.py \
    --family FMSR_DGA_DIAGNOSIS \
    --n 1 \
    --batch-id smoke_$(date +%Y%m%d) \
    --seed 42
```

Defaults: `--model watsonx/meta-llama/llama-3-3-70b-instruct`, `--temperature 0.7`. Costs roughly one Llama-3.3-70B chat completion at ≤1500 output tokens.

### First reviewable batch (one per family, 5 scenarios total)

The CLI uses a single global `--n`, so build a multi-family batch by passing every family in **one invocation**:

```bash
python scripts/generate_scenarios.py \
    --family FMSR_DGA_DIAGNOSIS \
    --family TSFM_RUL_FORECAST \
    --family WO_CREATION \
    --family IOT_SENSOR_ANALYSIS \
    --family MULTI_DOMAIN_INCIDENT \
    --n 1 \
    --batch-id first_review_$(date +%Y%m%d) \
    --seed 42
```

Each family generates `--n` scenarios in sequence, all numbered into the same batch as `SGT-GEN-001`...`SGT-GEN-005`. Hand off the result to Akshat for the validation pass under `#53`.

### Adding more scenarios to an existing batch (`--append`)

To keep adding scenarios into the same batch dir across separate invocations — e.g. iterating one family at a time, or topping up after a partial failure — use `--append`. Without it, the script refuses to write into a directory that already contains `SGT-GEN-NNN.json` files (this guards against the "same `--batch-id` overwrites previous output" footgun).

```bash
# First pass — fresh batch dir
python scripts/generate_scenarios.py \
    --family FMSR_DGA_DIAGNOSIS --n 2 \
    --batch-id review_$(date +%Y%m%d) --seed 11

# Later — add more scenarios to the same batch
python scripts/generate_scenarios.py \
    --family WO_CREATION --n 2 \
    --batch-id review_$(date +%Y%m%d) --seed 22 \
    --append
```

The second invocation continues numbering from `SGT-GEN-003` and appends a new entry to `batch_manifest.json:invocations[]` so every contributing pass is recorded. The cumulative `scenarios_emitted` list at the manifest top stays in sync.

### Full PS B coverage target (18 scenarios across 5 families)

The family matrix in `scenario_generation_support.json` calls for 4-4-4-2-4 = 18 scenarios across the five families. The CLI's single global `--n` doesn't allow different counts per family in one invocation, so use one invocation per family + `--append`:

```bash
BATCH=full_$(date +%Y%m%d)
python scripts/generate_scenarios.py --family FMSR_DGA_DIAGNOSIS    --n 4 --batch-id "$BATCH" --seed 1
python scripts/generate_scenarios.py --family TSFM_RUL_FORECAST     --n 4 --batch-id "$BATCH" --seed 2  --append
python scripts/generate_scenarios.py --family WO_CREATION           --n 4 --batch-id "$BATCH" --seed 3  --append
python scripts/generate_scenarios.py --family IOT_SENSOR_ANALYSIS   --n 2 --batch-id "$BATCH" --seed 4  --append
python scripts/generate_scenarios.py --family MULTI_DOMAIN_INCIDENT --n 4 --batch-id "$BATCH" --seed 5  --append
```

This produces `SGT-GEN-001` through `SGT-GEN-018` in one batch dir with five invocation records in the manifest. Different `--seed` per family gives independent template/context selection without rerunning the generator.

## Reading a generated scenario

```bash
jq . data/scenarios/generated/<batch_id>/SGT-GEN-001.json
```

Inspection checklist (mirrors the no-hint contract in `generated_scenario_authoring_and_ground_truth.md`):

1. `text` does not contain tool names (`fmsr.`, `wo.`, `tsfm.`, `iot.`), IEC fault codes, or specific gas concentrations.
2. `text` is under 80 words and asks for a decision, not a tool call.
3. `expected_tools` and `domain_tags` agree with the validator (covered by the in-memory validation pass during generation).
4. `ground_truth.ideal_tool_sequence` is consistent with `expected_tools`.
5. `nearest_handcrafted.scenario_id` is set; if `nearest_match_weak` is true, eyeball whether the scenario is genuinely novel or just unrelated.
6. Provenance fields look right: `source_type=generated`, `generation_model`, `knowledge_plugin_version` matches the current support file's hash.

## Promoting a generated scenario into the canonical set

After Akshat's validation pass (`#53` rubric) clears a scenario:

1. Move the JSON from `data/scenarios/generated/<batch_id>/SGT-GEN-NNN.json` to `data/scenarios/<descriptive_name>.json`.
2. Set `manual_cleanup: true` and add a `cleanup_notes` field listing what was edited.
3. Run `python data/scenarios/validate_scenarios.py` from repo root to confirm the team CI gate passes.
4. Open a PR; reference the source `batch_id` so reviewers can find the original generated artifact.

Do not bulk-merge the entire `data/scenarios/generated/<batch_id>/` directory into `data/scenarios/`. The provenance separation matters for the paper's "generated vs hand-crafted" comparison.

## Iterating on the prompt

The prompt template lives in `scripts/generate_scenarios.py:build_prompt`. The no-hint rules and schema reminder are inlined there (verbatim from `generated_scenario_authoring_and_ground_truth.md` sections 2-3 + section 5). When changing either, bump `PROMPT_VERSION` at the top of the script — that field lands in every emitted scenario's `generator_prompt_version` and in `batch_manifest.json`, so reviewers can tell which version produced a given batch.

Common tweaks:

- **Output drift to JSON-with-markdown-fences.** `parse_response` already strips ``` ```json ``` fences, but if the model starts adding commentary before the JSON, the regex won't catch it. Fix by tightening the schema reminder.
- **Same scenarios across runs.** RNG seed is on `--seed` and controls operational-context / DGA-template selection. Omit `--seed` for variety; pin for reproducibility. The model itself is non-deterministic at `temperature=0.7`.
- **Validator failures.** Check `<batch_id>/invalid/SGT-GEN-NNN.json` — the file contains both the bad scenario and the validator error list. Common causes: tool typos, missing `domain_tags`, asset_id outside T-001..T-020.

## What the prototype does NOT do (deferred to `#68` scale-up)

- Iterative refinement (re-prompting on validation failure)
- Coverage tracking (ensuring fault_code variation across the family)
- Duplicate detection beyond nearest-comparator (no semantic dedup against prior batches)
- Akshat's PS B evaluation pass (`#53`)
- Final paper-ready batch curation (post-Akshat-review)
