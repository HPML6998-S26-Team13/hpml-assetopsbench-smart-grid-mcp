# Recovery and Adjudication Mitigation Spec

*Last updated: 2026-05-02*
*Issues: #64, #66, #36, #5*

This doc specifies the two mitigation-ladder rungs that come after
`missing_evidence_final_answer_guard`. It is intentionally implementation-ready
but not yet runnable: no config in this branch should imply that recovery or
adjudication is wired into the runner until the code lands and is tested.

## Scope

The ladder stays on the two PE-family lanes that already have useful baseline
anchors:

| Family lane | Baseline anchor | Why this lane |
|---|---|---|
| `Y + Self-Ask` | `8998341_exp2_cell_Y_pe_self_ask_mcp_baseline` | PE-family baseline with the clarification mitigation but no verifier recovery |
| `Z + Self-Ask` | `8998343_exp2_cell_Z_verified_pe_self_ask_mcp_baseline` | strongest current PE-family lane, already has retry/suffix-replan substrate |

Do not run a full Cartesian grid of cells and mitigations. Each rung answers one
question:

| Rung | Stable name | Question |
|---:|---|---|
| 0 | baseline | what does the family lane do without the mitigation ladder |
| 1 | `missing_evidence_final_answer_guard` | how many clean-looking completions were unsafe because evidence was missing |
| 2 | `missing_evidence_retry_replan_guard` | how many evidence gaps can be repaired inside one trial |
| 3 | `explicit_fault_risk_adjudication_step` | whether the final fault/risk choice improves once deciding evidence exists |

## Rung 2: missing-evidence retry/replan guard

### Intent

Rung 2 turns the rung-1 detector from a terminal accounting gate into a bounded
recovery path. When the same missing-evidence condition is found before final
answer or work-order emission, the runner gets a small, auditable chance to
repair the evidence gap.

This is still one benchmark trial. It does not increase `TRIALS`, and it should
not hide the original evidence failure. The artifact must record both the
trigger and the repair attempt.

### Dependency

`missing_evidence_retry_replan_guard` depends on
`missing_evidence_final_answer_guard`. Treat it as a superset, not an
orthogonal factor:

```text
baseline -> detection guard -> retry/replan recovery
```

Future runtime enforcement should reject the recovery flag unless the detection
guard is also enabled.

### Trigger

Run the missing-evidence detector before finalization and after each
evidence-producing step when practical. Trigger recovery when all are true:

- an evidence tool result is missing, empty, unsuccessful, or untrusted
- the unresolved evidence key is still needed for the final answer or a
  downstream work-order action
- the step is safe to retry or its dependent suffix is safe to replan
- the repair budget has not been exhausted

Do not trigger recovery for valid negative evidence. For example, an empty
`detect_anomalies` result can be a meaningful "no anomaly detected" payload,
not a missing-evidence failure. The detector implementation must distinguish
tool-specific valid-empty results from generic empty/missing records before
this rung becomes runnable.

### Allowed actions

| Action | Use when | Constraint |
|---|---|---|
| `retry_step` | same read-only evidence step likely failed due to transient error, invalid argument, or empty fetch | retry at most once per evidence target |
| `replan_suffix` | repaired evidence changes what dependent downstream steps should do | only replace unexecuted suffix steps |
| `block_finalization` | evidence remains missing after repair budget | emit the same unsafe-finalization block as rung 1 |

Never retry mutating work-order tools. If a work-order action has already been
emitted after a missing-evidence gap, the trial should be marked unsuccessful
and the artifact should identify the unsafe emission rather than attempting to
repair after mutation.

### Budget

Recommended first implementation budget:

| Budget | Value |
|---|---:|
| max attempts per evidence target | 1 |
| max total repair attempts per trial | 2 |
| max suffix replans per trial | reuse Verified PE default, but count detector-driven replans separately |
| mutation retries | 0 |

If the first implementation needs to be simpler, start with one total repair
attempt per trial and only widen after a clean smoke.

### Runner integration

For `Y + Self-Ask`, add a small deterministic recovery loop around the existing
step execution loop in `scripts/plan_execute_self_ask_runner.py`. The loop
should:

- serialize the step result
- call the detector helper against the partial history
- retry the current read-only evidence step once when the detector identifies
  that step as the unresolved source
- otherwise leave the history untouched and allow rung 1 to block finalization

For `Z + Self-Ask`, reuse the existing Verified PE retry/suffix-replan substrate
in `scripts/verified_pe_runner.py`, but drive the decision from deterministic
missing-evidence detection instead of only from the LLM verifier. The artifact
should distinguish verifier-driven recovery from detector-driven recovery.

The shared detector code should live in `scripts/mitigation_guards.py`, with a
public helper that can scan partial histories and return unresolved evidence
hits without mutating the final payload.

### Artifact schema

Add this object to per-trial JSON when recovery is enabled:

```json
{
  "mitigation_repair": {
    "name": "missing_evidence_retry_replan_guard",
    "enabled": true,
    "detector": "missing_evidence_final_answer_guard",
    "triggered": true,
    "attempts": [
      {
        "attempt_index": 1,
        "source_step": 3,
        "tool": "get_sensor_readings",
        "target": {
          "transformer_id": "T-015",
          "sensor_id": "winding_temp_top_c"
        },
        "reason": "empty readings",
        "action": "retry_step",
        "result": "repaired",
        "new_step": 3
      }
    ],
    "repaired": true,
    "final_decision": "continue"
  }
}
```

If repair fails, keep `triggered=true`, `repaired=false`, and
`final_decision="block_finalization"`.

### Metrics

Populate these columns in `mitigation_before_after.csv` once runnable:

- `mitigation_guard_triggered`
- `mitigation_guard_blocked_final_answer`
- `mitigation_guard_blocked_work_order`
- `repair_attempt_count`
- `repair_success_rate`
- `supported_success_after_repair_rate`
- `tool_call_count_mean`
- `latency_seconds_mean`
- `judge_pass_rate`

The primary success metric is `supported_success_after_repair_rate`: a repair
only counts when the final answer is supported by the repaired evidence and the
judge row passes. A run that simply flips `success=true` without judge support
is not a mitigation win.

## Rung 3: explicit fault/risk adjudication step

### Intent

Rung 3 addresses the smaller but paper-important pattern where the runner has
some evidence but the final fault or risk choice is under-justified. It should
force the runner to name the deciding evidence, compare plausible alternatives,
and refuse to finalize when the evidence does not support a specific choice.

This rung is downstream of evidence detection and repair. It should not run
before rung 1 is active, and it should usually wait until rung 2 has at least
one measured row.

### Trigger

Run adjudication before final answer or work-order emission when any are true:

- multiple fault/risk labels are plausible from the collected evidence
- DGA, sensor trend, anomaly, RUL, or fault-record evidence points in different
  directions
- the planned work order depends on a fault/risk choice
- the final answer contains a fault/risk recommendation without citing the
  deciding tool evidence

If deciding evidence is missing, adjudication should not invent an answer. It
should return `refuse_due_missing_evidence` and rely on rung 1 or rung 2 to
record the missing-evidence failure.

### Output contract

Add this object to per-trial JSON when adjudication is enabled:

```json
{
  "fault_risk_adjudication": {
    "name": "explicit_fault_risk_adjudication_step",
    "enabled": true,
    "selected_fault_id": "FM-006",
    "selected_risk_level": "high",
    "deciding_evidence": [
      {
        "tool": "analyze_dga",
        "step": 2,
        "field": "diagnosis",
        "value": "thermal fault"
      }
    ],
    "alternatives_considered": [
      {
        "fault_id": "FM-001",
        "reason_rejected": "DGA diagnosis did not match partial-discharge evidence"
      }
    ],
    "missing_evidence": [],
    "decision": "finalize"
  }
}
```

Required invariants:

- `decision="finalize"` requires at least one `deciding_evidence` item.
- every deciding evidence item must cite a concrete tool and history step.
- every rejected alternative needs a reason tied to evidence, not prompt prose.
- `decision="refuse_due_missing_evidence"` requires non-empty
  `missing_evidence`.

### Metrics

Primary metric:

- count of `under-constrained fault/risk adjudication` rows after rerun

Secondary metrics:

- judge clarity/justification dimension
- `judge_pass_rate`
- wrong-fault-label count
- work-order consistency with selected fault/risk
- latency and tool-call overhead

### Implementation point

Implement as one pre-finalization helper rather than a free-form prompt edit.
The helper should consume terminal history, candidate fault/risk labels, and
the original question, then produce the structured object above. The final
answer summarizer can use the adjudication object, but the object itself must be
machine-checkable before the natural-language answer is written.

## Reserved config keys

These names are reserved for the future implementation. They should not be used
in runnable configs until the runner consumes them:

| Key | Meaning |
|---|---|
| `ENABLE_MISSING_EVIDENCE_REPAIR` | enables rung 2 recovery; requires `ENABLE_MISSING_EVIDENCE_GUARD=1` |
| `MISSING_EVIDENCE_REPAIR_MAX_ATTEMPTS` | max total detector-driven repair attempts per trial |
| `MISSING_EVIDENCE_REPAIR_MAX_ATTEMPTS_PER_TARGET` | max detector-driven retries per unresolved evidence target |
| `ENABLE_EXPLICIT_FAULT_RISK_ADJUDICATION` | enables rung 3 structured adjudication |

## Verification plan

1. Unit-test detector hits against partial histories without mutating payloads.
2. Unit-test valid-empty evidence exceptions so `detect_anomalies=[]` is not
   treated as missing evidence by default.
3. Smoke `Y + Self-Ask` with recovery disabled and enabled on a tiny scenario
   subset; confirm only the mitigation metadata changes when no gap exists.
4. Smoke `Z + Self-Ask` with a forced missing-evidence fixture; confirm
   detector-driven retry/replan is recorded separately from verifier-driven
   retry/replan.
5. Run the two family lanes on Insomnia only after rung 1 guarded reruns exist.
6. Judge before and after rows, then populate `mitigation_before_after.csv`.

## Promotion rule

Rung 2 becomes paper-usable only after it has at least one matched row against a
detection-only run. Rung 3 becomes paper-usable only after it has at least one
matched row against a recovery run or a clearly justified detection-only run
where all deciding evidence already exists.
