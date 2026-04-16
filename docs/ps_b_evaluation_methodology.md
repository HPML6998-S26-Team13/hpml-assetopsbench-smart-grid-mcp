# PS B Evaluation Methodology

*Last updated: 2026-04-16*  
*Owner: Alex Xin*  
*Issue: [#51](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/51)*

This note defines how Problem Statement B generated scenarios should be
evaluated against the hand-crafted Smart Grid reference set. Its goal is not to
declare generated scenarios "better" than hand-crafted ones; its goal is to
decide whether the generated batch is publishable, usable in benchmarks, and
defensible in the paper.

## Scope

This methodology applies to:

- the hand-crafted Smart Grid scenarios already tracked in `data/scenarios/`
- the first generated scenario batch produced from the Knowledge Plugin +
  scenario-generation path
- Akshat's validation pass in [#53](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/53)
- Alex's comparative analysis in
  [#52](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/52)

This methodology does not replace:

- structural schema validation
- MCP tool-name validation
- mentor realism review for domain plausibility

Those remain separate gates. This document covers quality comparison and
circularity handling only.

## Evaluation goal

The generated batch should clear a practical bar:

1. it should look meaningfully distinct from the hand-crafted set
2. it should still represent believable transformer-maintenance work
3. it should be benchmark-usable without poisoning the comparison through
   prompt leakage or self-copying

The question is therefore:

> "Does the generated batch add valid, non-trivial benchmark coverage beyond the
> hand-crafted set, under explicit leakage controls?"

## Evaluation units

The unit of evaluation is the individual scenario JSON, not the whole batch.

Each generated scenario is compared against the hand-crafted reference set on
four dimensions:

1. **Task realism** — does the task read like a believable maintenance /
   diagnostic / operations question?
2. **Task novelty** — is it materially different from the nearest hand-crafted
   scenario?
3. **Tool-path validity** — do the expected tools and reasoning structure match
   the task?
4. **Benchmark usefulness** — if kept, would this scenario improve the final
   benchmark rather than duplicate existing coverage?

Batch-level conclusions are then derived from the per-scenario ratings.

## Reference set and candidate set

### Hand-crafted reference set

The hand-crafted set is the current canonical Smart Grid scenario collection in
the top level of `data/scenarios/*.json`. It acts as the comparison baseline,
not as a gold label set in the strict ML sense.

For this methodology:

- use the root scenario JSON files as the reference set
- exclude `data/scenarios/negative_checks/` from nearest-neighbor comparison
- record the exact scenario list or commit hash used for the validation pass

### Candidate generated set

The candidate set is the first generated scenario batch from the PS B pipeline.
Every candidate must carry provenance metadata sufficient to reconstruct:

- generator prompt / prompt template version
- Knowledge Plugin version or hash
- generation model
- generation date / batch ID
- any manual cleanup performed after generation

If provenance is missing, the scenario is not eligible for inclusion in the
comparative analysis.

## Circularity and leakage policy

This is the core requirement for [#51](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/51).

### What could go wrong

The obvious failure mode is circularity:

- we hand-craft scenarios
- we feed those scenarios, or a near-copy of their structure, into the
  generation process
- the generated batch then looks "good" mainly because it copied the reference
  set

That would make the comparison paper-thin.

### Allowed overlap

The generated batch is allowed to share:

- the same four MCP domains
- the same benchmark schema
- the same general transformer-maintenance topic area
- the same public datasets

That is unavoidable and not considered leakage by itself.

### Disallowed leakage

A generated scenario should be rejected if any of the following is true:

- its task wording is a near paraphrase of a hand-crafted scenario
- its expected tool sequence is functionally identical to the nearest
  hand-crafted scenario without adding a different operational context
- its characteristic answer or success criteria mirror a hand-crafted scenario
  with only superficial surface changes
- the generation prompt explicitly exposed the full hand-crafted scenario text
  that it is later being compared against

### Practical controls

Use these controls during generation and validation:

1. **No direct copy prompt.** Do not ask the generator to "rewrite" or
   "paraphrase" existing scenario files.
2. **Prompt at the pattern level.** The generation prompt may describe schema,
   tool affordances, domain concepts, and realism constraints, but should avoid
   handing the full final wording of the evaluation reference set back to the
   model.
   - Do: ask for a multi-domain transformer-maintenance scenario with specific
     schema fields, tool affordances, and realism constraints.
   - Do not: paste a scenario from `data/scenarios/` and ask the model to
     rewrite or paraphrase it.
3. **Nearest-neighbor check.** Every generated scenario gets matched to the most
   similar hand-crafted scenario and explicitly rated for duplication risk.
4. **Label generated scenarios as generated.** Do not merge them into the
   canonical hand-crafted set without provenance labels; later analysis must be
   able to separate sources cleanly.
5. **Document the caveat in the paper.** Even with the controls above, the same
   repo and domain framing still shape both sets. We should call this out as a
   limitation, not pretend the generated set is fully independent.

## Validation workflow

Akshat's validation pass should use the following sequence.

### Stage 0 — Preconditions

Only evaluate a generated scenario if:

- it passes schema validation
- its expected tools map to the current server/tool registry
- provenance metadata is present

If any precondition fails, mark the scenario `reject_structural` and stop.

### Stage 1 — Nearest hand-crafted comparator

For each generated scenario, identify the nearest hand-crafted comparator by:

- primary domain
- operational task type
- expected tool pattern
- asset / fault context

The point is not to compute a numeric embedding score. The point is to force an
explicit human-readable comparison target.

If no hand-crafted scenario is a natural match, choose the closest comparator
across the full reference set and add `nearest_match_weak = true` in the
validator notes.

### Stage 2 — Four-dimension scenario rating

Rate the generated scenario on the dimensions below.

| Dimension | Question | Rating scale |
|---|---|---|
| Realism | Would a transformer engineer / planner / maintenance lead recognize this as plausible work? | `accept`, `borderline`, `reject` |
| Novelty | Is it materially different from the nearest hand-crafted comparator? | `distinct`, `near-duplicate`, `duplicate` |
| Tool-path validity | Do expected tools and reasoning steps actually fit the task? | `good`, `fixable`, `bad` |
| Benchmark usefulness | If added, would it improve coverage or just inflate count? | `keep`, `maybe`, `drop` |

### Stage 3 — Disposition

Map the ratings into one of five outcomes:

| Outcome | Meaning |
|---|---|
| `reject_structural` | Failed Stage 0 preconditions; not rated on the four main dimensions |
| `accept` | Use in later benchmark analysis as a generated scenario |
| `accept_with_edits` | Keep after bounded cleanup (wording, tool list, success criteria) |
| `reject_duplicate` | Too close to a hand-crafted scenario |
| `reject_unusable` | Structurally valid but not benchmark-worthy |

Use the following decision rule so dispositions are reproducible across
reviewers:

1. If Stage 0 failed, set `disposition = reject_structural` and leave the four
   ratings null.
2. Else if `novelty_rating` is `near-duplicate` or `duplicate`, set
   `disposition = reject_duplicate`.
3. Else if `realism_rating = reject`, `tool_path_rating = bad`, or
   `benchmark_usefulness_rating = drop`, set `disposition = reject_unusable`.
4. Else if any of the following is true, set `disposition = accept_with_edits`:
   - `realism_rating = borderline`
   - `tool_path_rating = fixable`
   - `benchmark_usefulness_rating = maybe`
5. Else set `disposition = accept`.

This makes the validator output deterministic even when multiple dimensions are
mixed.

## Acceptance criteria

The generated batch is acceptable for downstream analysis if all of the
following hold:

1. at least **70%** of candidates are `accept` or `accept_with_edits`
2. fewer than **20%** are `reject_duplicate`
3. every kept scenario has a named nearest hand-crafted comparator and a short
   novelty note
4. every kept scenario has an explicit source label: `generated`
5. the write-up includes an explicit circularity caveat

These thresholds are intentionally pragmatic. They are a "good enough to defend
in the paper" bar, not a claim of formal independence.

### Failure path

If a batch misses the acceptance criteria:

1. retain the per-scenario ratings and dispositions; do not quietly discard the
   failed run
2. if there is still a useful accepted subset, Alex may use that subset for
   descriptive analysis only, with the failure called out explicitly
3. if too few scenarios remain to support a meaningful comparison, escalate to
   Alex to decide between:
   - one bounded regeneration pass with stricter anti-duplication prompting, or
   - excluding PS B generated scenarios from the paper's comparative lane

Do not silently treat a failed batch as publishable.

## Comparison dimensions for notebook / paper use

Later analysis should compare hand-crafted versus generated scenarios across:

1. **coverage by domain** — IoT, FMSR, TSFM, WO, multi-domain
2. **coverage by task type** — diagnosis, forecasting, work-order creation,
   end-to-end incident response, etc.
3. **tool-path complexity** — number of tools, single-domain vs multi-domain
4. **realism rating distribution** — how many pass cleanly versus require edits
5. **duplication risk distribution** — how many generated scenarios are too
   close to the hand-crafted set
6. **agent-performance sensitivity** — once benchmarked, whether generated
   scenarios materially differ from hand-crafted ones in completion quality,
   latency, or failure modes

This is the evidence structure Alex can later defend in the paper:

- generated scenarios are not just "more of the same"
- they can be shown as either additive coverage or failed experiments
- both outcomes are publishable if documented honestly

## Required artifact shape

Akshat's validation output should be a machine-readable table or JSONL with at
least these fields:

- `scenario_id`
- `source_type` (`handcrafted` or `generated`)
- `nearest_handcrafted_scenario_id`
- `realism_rating`
- `novelty_rating`
- `tool_path_rating`
- `benchmark_usefulness_rating`
- `disposition`
- `needs_edit` (`true` only when `disposition = accept_with_edits`)
- `validator_notes`
- `provenance_batch_id`

This keeps the validation step reusable for
[#52](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/52)
and the final paper lane.

## Explicit paper caveat

Use some version of this caveat in the paper:

> The generated scenario set is not a fully independent benchmark source. It is
> produced within the same repo, domain framing, and tool schema as the
> hand-crafted Smart Grid set. We therefore treat it as a controlled extension
> of the benchmark rather than an unbiased external test set, and we explicitly
> filter for near-duplicates before including generated scenarios in analysis.

## Handoff summary

This is the concrete rubric to send to Aaron and Akshat before W4 validation:

- generate at the schema/pattern level, not by paraphrasing existing scenarios
- preserve provenance metadata for every generated scenario
- compare each generated scenario against the nearest hand-crafted one
- reject duplicates explicitly
- keep generated scenarios labeled as generated in all later artifacts

That is the minimum standard needed to make PS B defensible instead of
hand-wavy.
