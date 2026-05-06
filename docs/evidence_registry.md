# Evidence Registry

*Last updated: 2026-05-05*

`results/metrics/evidence_registry.csv` is the machine-readable gate for
paper-facing evidence. It records each imported or known-problem cohort as
paper-grade, diagnostic, superseded, or invalid. Tables, notebooks, and paper
claims should include only rows where `include_in_paper=true`.

## Status Values

| Status | Meaning | Paper use |
|---|---|---|
| `paper_grade` | Complete raw JSON, latency, and judge evidence on the current clean floor. | Include. |
| `paper_grade_candidate` | Newly captured row awaiting artifact and provenance validation. | Exclude until promoted. |
| `diagnostic` | Useful for debugging or historical interpretation, but not claim-grade. | Exclude. |
| `superseded` | Valid enough to preserve, but replaced by a newer clean cohort. | Exclude. |
| `invalid_tooling` | Tooling or environment contamination means the row is not model evidence. | Exclude. |
| `obsolete` | Retained only because older docs or logs may reference it. | Exclude. |

`paper_grade_candidate` is intentionally excluded by default. Promote it to
`paper_grade` only after raw trajectory counts, latency rows, judge rows, and
provenance have all been validated.

## Current Paper-Grade Set

The current paper-grade floor is PR #175 merged over PR #180:
`team13/main@1913c6e4703425f735d8cb8297cb890ba66bbeff`.

The registry currently marks 37 row groups as paper-grade:

- 31-scenario 8B core: `A`, `B`, `C`, `Y`, `YS`, `Z`, `ZS`
- 15-scenario 8B follow-on/extra: `YS_TP`, `ZS_TP`, `D`, `ZSD`
- 15-scenario 8B mitigation ladder:
  `YS_BASELINE`, `YS_GUARD`, `YS_REPAIR`, `YS_ADJ`,
  `ZS_BASELINE`, `ZS_GUARD`, `ZS_REPAIR`, `ZS_ADJ`
- 15-scenario hosted WatsonX 70B rows:
  `A70B`, `B70B`, `C70B`, `Y70B`, `YS70B`, `Z70B`, `ZS70B`

The included rows total 2,420 raw trajectory JSON files and 2,420 judge rows.

## Known Exclusions

The registry intentionally keeps non-paper rows visible instead of deleting
them. This avoids reusing stale coordination notes or VM-local artifacts by
accident.

Current explicit exclusions include:

- pre-PR173/final-six mitigation diagnostic rows from
  `mitigation_final6_4tier_a100_20260503T121709Z`
- legacy final-six A100 matrix rows predating the post-PR175 31-scenario core
- post-PR180 rows superseded by the post-PR175 clean-floor corpus
- the post-PR179 mitigation run affected by the
  `plan_execute_self_ask_runner.py` relative-import failure
- hosted-70B batches affected by missing WatsonX alias environment variables or
  missing `python` on `PATH`

Do not expunge invalid rows unless they contain secrets or accidental large
junk. Preserve raw provenance, mark the row status, and add `superseded_by`
when a clean rerun exists.

## Filtering Rule

For any paper table or figure, first filter:

```python
registry = pd.read_csv("results/metrics/evidence_registry.csv")
include = registry["include_in_paper"].astype(str).str.lower().eq("true")
paper_runs = set(registry.loc[include, "run_name"])
```

Then join `results/metrics/scenario_scores.jsonl` by the full `run_name` plus
the full `trajectory_file` path. Do not join by basename; some cells collide.
Use a CSV-aware parser such as pandas, Python `csv`, or `csvkit`; `awk -F','`
will misparse quoted fields in this registry.

Hosted WatsonX 70B summary rows in `gcp_post175_70b_summary.csv` aggregate
CPU-client captures and top-ups. They do not carry harness-side vLLM latency
counts, so `latency_count` is intentionally blank for that summary.

Before any Croissant or dataset-package upload, run a PII/path grep over the
allow-listed export bundle. The committed logs in this PR scrub GCP operator
home/cache prefixes to placeholders, and package scripts should preserve that
scrubbed form rather than rebuilding from VM-local logs.

For this artifact family, the minimum grep should include:
`/home/wax|/Users/wax|wax1@|/insomnia001/home/wax1`.
