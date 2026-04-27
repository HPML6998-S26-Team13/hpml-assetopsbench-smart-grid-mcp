"""Link profiling capture artifacts to the benchmark run's WandB run.

The benchmark runner (``scripts/run_experiment.sh``) writes ``wandb_run_url``
into ``benchmarks/cell_<X>/raw/<run-id>/{meta,summary,config}.json`` after the
benchmark finishes. This script takes a matched pair of:

- a benchmark run dir (``benchmarks/cell_<X>/raw/<run-id>/``)
- a profiling capture dir (``profiling/traces/<run-id>/``)

and attaches the profiling artifacts to the same WandB run by resuming it via
the run ID parsed from ``wandb_run_url``. Also parses ``nvidia_smi.csv`` for
summary stats (mean / max GPU util, mean / max memory, duration) and writes
them into the run's summary so Alex's notebooks can query them without
re-parsing the CSV.

Intended invocation (from ``capture_around.sh`` or a follow-up Slurm step):

    python3 profiling/scripts/log_profiling_to_wandb.py \\
        --benchmark-run-dir benchmarks/cell_A_direct/raw/<run-id> \\
        --profiling-dir profiling/traces/<run-id>

The script is a no-op (exit 0 with a warning) if the benchmark dir lacks a
``wandb_run_url``, e.g. for local dry runs without WandB enabled. This lets
the capture wrapper call it unconditionally.
"""

from __future__ import annotations

import argparse
import json
import logging
import pathlib
import re
import sys
from typing import Optional

log = logging.getLogger("log_profiling_to_wandb")


def _parse_run_id_from_url(url: str) -> Optional[tuple[str, str, str]]:
    """Return (entity, project, run_id) from a WandB run URL, or None."""
    match = re.match(r"https?://(?:[^/]+/)?([^/]+)/([^/]+)/runs/([^/?#]+)", url.strip())
    if not match:
        return None
    return match.group(1), match.group(2), match.group(3)


def _summarize_nvidia_smi(csv_path: pathlib.Path) -> dict[str, float]:
    """Compute summary stats from the nvidia-smi sampler CSV."""
    try:
        import pandas as pd
    except ImportError:
        log.warning("pandas not installed; skipping nvidia-smi summary.")
        return {}

    if not csv_path.exists():
        return {}

    # The sampler writes columns with spaces and units, e.g.
    # " utilization.gpu [%]", " memory.used [MiB]". Strip whitespace + units.
    def _normalize_col(c: str) -> str:
        c = c.strip()
        c = re.sub(r"\s*\[[^\]]+\]", "", c)
        c = c.replace(".", "_").replace(" ", "_")
        return c

    df = pd.read_csv(csv_path)
    df.columns = [_normalize_col(c) for c in df.columns]

    stats: dict[str, float] = {}

    def _numeric(col: str):
        if col not in df.columns:
            return None
        # strip trailing unit strings that slipped through ("65 %", "3245 MiB")
        series = (
            df[col]
            .astype(str)
            .str.extract(r"([-+]?\d*\.?\d+)", expand=False)
            .astype(float)
        )
        return series

    util = _numeric("utilization_gpu")
    if util is not None and not util.empty:
        stats["profiling/gpu_util_mean"] = float(util.mean())
        stats["profiling/gpu_util_max"] = float(util.max())

    mem_util = _numeric("utilization_memory")
    if mem_util is not None and not mem_util.empty:
        stats["profiling/mem_util_mean"] = float(mem_util.mean())

    mem_used = _numeric("memory_used")
    if mem_used is not None and not mem_used.empty:
        stats["profiling/gpu_mem_used_mib_mean"] = float(mem_used.mean())
        stats["profiling/gpu_mem_used_mib_max"] = float(mem_used.max())

    power = _numeric("power_draw")
    if power is not None and not power.empty:
        stats["profiling/power_draw_w_mean"] = float(power.mean())
        stats["profiling/power_draw_w_max"] = float(power.max())

    stats["profiling/nvidia_smi_samples"] = int(len(df))
    return stats


def main(argv: list[str]) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark-run-dir", required=True, type=pathlib.Path)
    parser.add_argument("--profiling-dir", required=True, type=pathlib.Path)
    parser.add_argument(
        "--artifact-name",
        default=None,
        help="Override for the WandB Artifact name (defaults to profiling-<run-id>).",
    )
    parser.add_argument(
        "--mode",
        default="online",
        help="WandB run mode (online|offline|disabled). Default online.",
    )
    args = parser.parse_args(argv)

    bench_dir: pathlib.Path = args.benchmark_run_dir.resolve()
    prof_dir: pathlib.Path = args.profiling_dir.resolve()

    # Repo root is two parents up from this script: profiling/scripts/ -> repo/.
    # Used to relativize prof_dir before writing it into meta.json so committed
    # artifacts don't leak personal scratch paths like
    # /insomnia001/depts/edu/users/af3623/exp1-clone/profiling/traces/...
    # which break for anyone reading the meta from the team checkout.
    repo_root = pathlib.Path(__file__).resolve().parent.parent.parent
    try:
        prof_dir_for_meta = str(prof_dir.relative_to(repo_root))
    except ValueError:
        prof_dir_for_meta = str(prof_dir)

    if not bench_dir.is_dir():
        log.error("benchmark run dir does not exist: %s", bench_dir)
        return 1
    if not prof_dir.is_dir():
        log.error("profiling dir does not exist: %s", prof_dir)
        return 1

    meta_path = bench_dir / "meta.json"
    if not meta_path.exists():
        log.error("no meta.json in %s", bench_dir)
        return 1

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    run_url = meta.get("wandb_run_url")
    run_id_meta = meta.get("run_id")

    if not run_url:
        log.warning(
            "meta.json has no wandb_run_url (ENABLE_WANDB=0 for that run?); "
            "skipping WandB upload. meta run_id=%s",
            run_id_meta,
        )
        return 0

    parsed = _parse_run_id_from_url(run_url)
    if parsed is None:
        log.error("could not parse WandB run URL: %s", run_url)
        return 1
    entity, project, wandb_run_id = parsed

    try:
        import wandb
    except ImportError:
        log.error("wandb package not installed; cannot upload. Add wandb to the venv.")
        return 1

    stats = _summarize_nvidia_smi(prof_dir / "nvidia_smi.csv")

    artifact_name = args.artifact_name or f"profiling-{run_id_meta or wandb_run_id}"

    log.info(
        "resuming WandB run %s/%s/%s to attach profiling artifact %s",
        entity,
        project,
        wandb_run_id,
        artifact_name,
    )

    run = wandb.init(
        entity=entity,
        project=project,
        id=wandb_run_id,
        resume="allow",
        mode=args.mode,
    )

    # Attach all files under the profiling dir as a single Artifact
    artifact = wandb.Artifact(
        name=artifact_name,
        type="profiling",
        description=(
            f"Profiling capture for benchmark run {run_id_meta}. "
            "Includes nvidia-smi sampler CSV, optional nsys report + stats, "
            "optional PyTorch Profiler traces, and capture_meta.json."
        ),
    )
    for path in sorted(prof_dir.rglob("*")):
        if path.is_file():
            artifact.add_file(str(path), name=str(path.relative_to(prof_dir)))
    run.log_artifact(artifact)

    if stats:
        run.summary.update(stats)

    # Also annotate the run config with where the profiling dir lives so
    # downstream notebooks can find the raw files on disk. Use the
    # repo-root-relative form when possible.
    run.config.update(
        {
            "profiling_dir": prof_dir_for_meta,
            "profiling_artifact": artifact_name,
        },
        allow_val_change=True,
    )

    run.finish()

    # Write the profiling link back into the benchmark run's meta.json so
    # the filesystem record matches what's in WandB. Relative path keeps the
    # committed meta portable across team / personal-scratch checkouts.
    meta["profiling_dir"] = prof_dir_for_meta
    meta["profiling_artifact"] = artifact_name
    if stats:
        meta.setdefault("profiling_summary", {}).update(stats)
    meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    log.info(
        "logged profiling artifact %s and %d summary stat(s)", artifact_name, len(stats)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
