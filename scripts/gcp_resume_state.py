#!/usr/bin/env python3
"""Resume-state helpers for SmartGridBench GCP fallback runs.

The shell runner owns process orchestration. This helper owns the fiddly,
testable parts of resume: trial classification, latency-row dedupe, atomic
finalization, and manifest events.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _posix(path: Path | str) -> str:
    return Path(path).as_posix()


def _norm(path: Path | str) -> str:
    return os.path.normpath(_posix(path))


def _shell_bool(value: bool) -> str:
    return "1" if value else "0"


def _emit_shell(values: dict[str, Any]) -> None:
    for key, value in values.items():
        print(f"{key}={shlex.quote(str(value))}")


def _load_json_object(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    if not path.exists():
        return None, "missing_json"
    try:
        if path.stat().st_size == 0:
            return None, "zero_byte_json"
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None, "invalid_json"
    except OSError as exc:
        return None, f"read_error:{exc}"
    if not isinstance(payload, dict):
        return None, "non_object_json"
    return payload, None


def _scenario_payload(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"scenario is not a JSON object: {path}")
    return payload


def _scenario_basename(path: Path) -> str:
    return path.stem


def _step_failed(step: dict[str, Any]) -> bool:
    if step.get("success") is False:
        return True
    if step.get("error"):
        return True
    response = step.get("response")
    return isinstance(response, dict) and bool(response.get("error"))


def derive_success(data: dict[str, Any]) -> bool | None:
    raw = data.get("success")
    if isinstance(raw, bool):
        return raw
    steps = data.get("history") or data.get("trajectory") or []
    if not steps and not data.get("answer"):
        return None
    for step in steps:
        if isinstance(step, dict) and _step_failed(step):
            return False
    return bool(data.get("answer"))


def _scenario_id_matches(
    payload: dict[str, Any],
    scenario: dict[str, Any],
) -> bool:
    embedded = payload.get("scenario")
    if not isinstance(embedded, dict):
        return True
    expected_id = scenario.get("id")
    actual_id = embedded.get("id")
    return not expected_id or not actual_id or expected_id == actual_id


def _latency_records(latency_file: Path) -> list[dict[str, Any]]:
    if not latency_file.exists():
        return []
    records: list[dict[str, Any]] = []
    for line in latency_file.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            records.append(payload)
    return records


def _record_matches_identity(
    record: dict[str, Any],
    scenario_file: Path,
    trial_index: int,
    output_path: Path,
) -> bool:
    if int(record.get("trial_index", -1)) != int(trial_index):
        return False
    output = record.get("output_path")
    if output and _norm(output) != _norm(output_path):
        return False
    scenario = record.get("scenario_file")
    return not scenario or _norm(scenario) == _norm(scenario_file)


def _matching_latency_rows(
    records: list[dict[str, Any]],
    scenario_file: Path,
    trial_index: int,
    output_path: Path,
) -> list[dict[str, Any]]:
    return [
        record
        for record in records
        if _record_matches_identity(record, scenario_file, trial_index, output_path)
    ]


def _rows_conflict(rows: list[dict[str, Any]]) -> bool:
    if len(rows) < 2:
        return False
    normalized = {
        json.dumps(row, sort_keys=True, separators=(",", ":")) for row in rows
    }
    return len(normalized) > 1


def _candidate_trial_paths(
    run_dir: Path,
    scenario_file: Path,
    trial_index: int,
    output_path: Path,
) -> list[Path]:
    run_label = f"{_scenario_basename(scenario_file)}_run{trial_index:02d}.json"
    candidates = [output_path]
    candidates.extend(sorted(run_dir.glob(f"*_{run_label}")))
    seen: set[str] = set()
    deduped: list[Path] = []
    for candidate in candidates:
        key = str(candidate)
        if key not in seen:
            deduped.append(candidate)
            seen.add(key)
    return deduped


def classify_trial(
    *,
    run_dir: Path,
    scenario_file: Path,
    trial_index: int,
    output_path: Path,
    latency_file: Path,
    require_latency: bool,
) -> dict[str, Any]:
    scenario = _scenario_payload(scenario_file)
    latency_records = _latency_records(latency_file)
    incomplete_reasons: list[str] = []
    saw_candidate = False

    for candidate in _candidate_trial_paths(
        run_dir, scenario_file, trial_index, output_path
    ):
        if not candidate.exists():
            continue
        saw_candidate = True
        payload, error = _load_json_object(candidate)
        if error is not None or payload is None:
            incomplete_reasons.append(error or "invalid_json")
            continue
        if not _scenario_id_matches(payload, scenario):
            incomplete_reasons.append("scenario_identity_conflict")
            continue
        success = derive_success(payload)
        if success is None:
            incomplete_reasons.append("success_not_derivable")
            continue
        rows = _matching_latency_rows(
            latency_records, scenario_file, trial_index, candidate
        )
        if require_latency:
            if not rows:
                incomplete_reasons.append("missing_latency")
                continue
            if _rows_conflict(rows):
                incomplete_reasons.append("duplicate_conflicting_latency")
                continue
        return {
            "state": "complete_success" if success else "complete_failure",
            "complete": True,
            "success": success,
            "output_path": _posix(candidate),
            "reason": "terminal_trial",
            "latency_rows": len(rows),
        }

    stdout_candidates = [
        path
        for path in run_dir.glob(
            f"*_{_scenario_basename(scenario_file)}_run{trial_index:02d}.json.stdout"
        )
        if path.exists()
    ]
    if stdout_candidates and not saw_candidate:
        incomplete_reasons.append("dangling_stdout")

    return {
        "state": "incomplete",
        "complete": False,
        "success": False,
        "output_path": _posix(output_path),
        "reason": ",".join(sorted(set(incomplete_reasons))) or "missing_json",
        "latency_rows": 0,
    }


def _sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_manifest_event(
    *,
    manifest_file: Path,
    state: str,
    scenario_file: Path,
    trial_index: int,
    output_path: Path,
    run_name: str,
    reason: str = "",
    batch_id: str = "",
    latency_seconds: float | None = None,
    return_code: int | None = None,
    started_at: str = "",
    finished_at: str = "",
    extra: dict[str, Any] | None = None,
) -> None:
    manifest_file.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "schema_version": 1,
        "batch_id": batch_id or None,
        "run_name": run_name,
        "event": "trial_resume_state",
        "state": state,
        "reason": reason or None,
        "scenario_file": _posix(scenario_file),
        "scenario_basename": _scenario_basename(scenario_file),
        "trial_index": int(trial_index),
        "output_path": _posix(output_path),
        "latency_seconds": latency_seconds,
        "return_code": return_code,
        "started_at": started_at or None,
        "finished_at": finished_at or _now_iso(),
        "compute_provider": os.environ.get("SMARTGRID_COMPUTE_PROVIDER"),
        "compute_zone": os.environ.get("SMARTGRID_COMPUTE_ZONE"),
        "compute_instance": os.environ.get("SMARTGRID_COMPUTE_INSTANCE"),
        "gpu_type": os.environ.get("GPU_TYPE"),
    }
    if extra:
        payload.update(extra)
    with manifest_file.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, sort_keys=True) + "\n")


def preserve_incomplete_output(output_path: Path) -> Path | None:
    if not output_path.exists():
        return None
    suffix = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    preserved = output_path.with_name(f"{output_path.name}.incomplete.{suffix}")
    output_path.replace(preserved)
    return preserved


def _apply_final_answer_guards(payload: dict[str, Any]) -> None:
    try:
        from scripts.mitigation_guards import (  # type: ignore
            apply_explicit_fault_risk_adjudication,
            apply_missing_evidence_final_answer_guard,
            env_flag_enabled,
        )
    except ImportError:
        return
    apply_missing_evidence_final_answer_guard(
        payload,
        enabled=env_flag_enabled(os.environ.get("ENABLE_MISSING_EVIDENCE_GUARD")),
    )
    if "fault_risk_adjudication" not in payload:
        apply_explicit_fault_risk_adjudication(
            payload,
            enabled=env_flag_enabled(
                os.environ.get("ENABLE_EXPLICIT_FAULT_RISK_ADJUDICATION")
            ),
        )


def _upsert_latency_row(
    *,
    latency_file: Path,
    scenario_file: Path,
    trial_index: int,
    output_path: Path,
    latency_seconds: float,
) -> None:
    records = [
        row
        for row in _latency_records(latency_file)
        if not _record_matches_identity(row, scenario_file, trial_index, output_path)
    ]
    records.append(
        {
            "scenario_file": _posix(scenario_file),
            "trial_index": int(trial_index),
            "latency_seconds": latency_seconds,
            "output_path": _posix(output_path),
        }
    )
    latency_file.parent.mkdir(parents=True, exist_ok=True)
    tmp = latency_file.with_suffix(latency_file.suffix + ".tmp")
    tmp.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )
    tmp.replace(latency_file)


def finalize_trial(
    *,
    scenario_file: Path,
    trial_index: int,
    temp_output: Path,
    output_path: Path,
    latency_file: Path,
    manifest_file: Path,
    run_name: str,
    batch_id: str,
    start_epoch: float,
    end_epoch: float,
    return_code: int,
) -> dict[str, Any]:
    payload, error = _load_json_object(temp_output)
    if error is not None or payload is None:
        write_manifest_event(
            manifest_file=manifest_file,
            state="incomplete",
            scenario_file=scenario_file,
            trial_index=trial_index,
            output_path=output_path,
            run_name=run_name,
            reason=error or "invalid_json",
            batch_id=batch_id,
            return_code=return_code,
        )
        return {
            "state": "incomplete",
            "success": False,
            "reason": error or "invalid_json",
        }

    scenario = _scenario_payload(scenario_file)
    payload["scenario"] = scenario
    _apply_final_answer_guards(payload)
    success = derive_success(payload)
    if success is None:
        write_manifest_event(
            manifest_file=manifest_file,
            state="incomplete",
            scenario_file=scenario_file,
            trial_index=trial_index,
            output_path=output_path,
            run_name=run_name,
            reason="success_not_derivable",
            batch_id=batch_id,
            return_code=return_code,
        )
        return {
            "state": "incomplete",
            "success": False,
            "reason": "success_not_derivable",
        }
    payload["success"] = success

    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_output.write_text(
        json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8"
    )
    original_hash = _sha256(output_path)
    temp_hash = _sha256(temp_output)
    temp_output.replace(output_path)
    divergent: bool | None
    if original_hash is None:
        divergent = None
    else:
        divergent = original_hash != temp_hash
    latency_seconds = float(end_epoch) - float(start_epoch)
    _upsert_latency_row(
        latency_file=latency_file,
        scenario_file=scenario_file,
        trial_index=trial_index,
        output_path=output_path,
        latency_seconds=latency_seconds,
    )
    state = "complete_success" if success else "complete_failure"
    write_manifest_event(
        manifest_file=manifest_file,
        state=state,
        scenario_file=scenario_file,
        trial_index=trial_index,
        output_path=output_path,
        run_name=run_name,
        reason="trial_executed",
        batch_id=batch_id,
        latency_seconds=latency_seconds,
        return_code=return_code,
        extra={
            "original_output_sha256": original_hash,
            "final_output_sha256": temp_hash,
            "divergent": divergent,
        },
    )
    return {"state": state, "success": success, "reason": "trial_executed"}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    status = sub.add_parser("trial-status-shell")
    status.add_argument("--run-dir", required=True, type=Path)
    status.add_argument("--scenario-file", required=True, type=Path)
    status.add_argument("--trial-index", required=True, type=int)
    status.add_argument("--output-path", required=True, type=Path)
    status.add_argument("--latency-file", required=True, type=Path)
    status.add_argument("--require-latency", action="store_true")

    preserve = sub.add_parser("preserve-incomplete")
    preserve.add_argument("--output-path", required=True, type=Path)
    preserve.add_argument("--manifest-file", required=True, type=Path)
    preserve.add_argument("--scenario-file", required=True, type=Path)
    preserve.add_argument("--trial-index", required=True, type=int)
    preserve.add_argument("--run-name", required=True)
    preserve.add_argument("--batch-id", default="")
    preserve.add_argument("--reason", default="rerun_preserved_incomplete")

    finalize = sub.add_parser("finalize-trial-shell")
    finalize.add_argument("--scenario-file", required=True, type=Path)
    finalize.add_argument("--trial-index", required=True, type=int)
    finalize.add_argument("--temp-output", required=True, type=Path)
    finalize.add_argument("--output-path", required=True, type=Path)
    finalize.add_argument("--latency-file", required=True, type=Path)
    finalize.add_argument("--manifest-file", required=True, type=Path)
    finalize.add_argument("--run-name", required=True)
    finalize.add_argument("--batch-id", default="")
    finalize.add_argument("--start-epoch", required=True, type=float)
    finalize.add_argument("--end-epoch", required=True, type=float)
    finalize.add_argument("--return-code", required=True, type=int)

    event = sub.add_parser("manifest-event")
    event.add_argument("--manifest-file", required=True, type=Path)
    event.add_argument("--state", required=True)
    event.add_argument("--scenario-file", required=True, type=Path)
    event.add_argument("--trial-index", required=True, type=int)
    event.add_argument("--output-path", required=True, type=Path)
    event.add_argument("--run-name", required=True)
    event.add_argument("--reason", default="")
    event.add_argument("--batch-id", default="")
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    if args.command == "trial-status-shell":
        result = classify_trial(
            run_dir=args.run_dir,
            scenario_file=args.scenario_file,
            trial_index=args.trial_index,
            output_path=args.output_path,
            latency_file=args.latency_file,
            require_latency=args.require_latency,
        )
        _emit_shell(
            {
                "RESUME_STATE": result["state"],
                "RESUME_COMPLETE": _shell_bool(bool(result["complete"])),
                "RESUME_SUCCESS": _shell_bool(bool(result["success"])),
                "RESUME_OUTPUT_PATH": result["output_path"],
                "RESUME_REASON": result["reason"],
            }
        )
        return
    if args.command == "preserve-incomplete":
        preserved = preserve_incomplete_output(args.output_path)
        if preserved is not None:
            write_manifest_event(
                manifest_file=args.manifest_file,
                state="incomplete",
                scenario_file=args.scenario_file,
                trial_index=args.trial_index,
                output_path=preserved,
                run_name=args.run_name,
                reason=args.reason,
                batch_id=args.batch_id,
            )
        return
    if args.command == "finalize-trial-shell":
        result = finalize_trial(
            scenario_file=args.scenario_file,
            trial_index=args.trial_index,
            temp_output=args.temp_output,
            output_path=args.output_path,
            latency_file=args.latency_file,
            manifest_file=args.manifest_file,
            run_name=args.run_name,
            batch_id=args.batch_id,
            start_epoch=args.start_epoch,
            end_epoch=args.end_epoch,
            return_code=args.return_code,
        )
        _emit_shell(
            {
                "FINAL_STATE": result["state"],
                "FINAL_SUCCESS": _shell_bool(bool(result["success"])),
                "FINAL_REASON": result["reason"],
            }
        )
        return
    if args.command == "manifest-event":
        write_manifest_event(
            manifest_file=args.manifest_file,
            state=args.state,
            scenario_file=args.scenario_file,
            trial_index=args.trial_index,
            output_path=args.output_path,
            run_name=args.run_name,
            reason=args.reason,
            batch_id=args.batch_id,
        )
        return
    raise AssertionError(args.command)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"gcp_resume_state: ERROR: {exc}", file=sys.stderr)
        raise
