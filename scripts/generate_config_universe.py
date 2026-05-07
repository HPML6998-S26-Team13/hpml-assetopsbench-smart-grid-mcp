#!/usr/bin/env python3
"""Generate tracked SmartGridBench experiment config cohorts.

This script is intentionally broad. The paper evidence registry decides which
runs graduate to claim-grade evidence; this generator makes the experimental
space reproducible before scarce compute or hosted access disappears.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_ROOT = ROOT / "configs" / "config_universe"
GENERATED_ROOT = OUT_ROOT / "generated"
COHORT_ROOT = OUT_ROOT / "cohorts"
CATALOG_PATH = OUT_ROOT / "catalog.tsv"

JUDGE_MODEL = "watsonx/meta-llama/llama-4-maverick-17b-128e-instruct-fp8"
WATSONX_70B_MODEL = "watsonx/meta-llama/llama-3-3-70b-instruct"

FINAL6 = [
    "data/scenarios/multi_01_end_to_end_fault_response.json",
    "data/scenarios/multi_02_dga_to_workorder_pipeline.json",
    "data/scenarios/fmsr_04_dga_full_diagnostic_chain.json",
    "data/scenarios/iot_04_load_current_overload_check.json",
    "data/scenarios/tsfm_02_hotspot_temp_anomaly.json",
    "data/scenarios/wo_04_fault_record_downtime_update.json",
]


@dataclass(frozen=True)
class ScenarioSet:
    key: str
    name: str
    files: tuple[str, ...]
    scope: str


@dataclass(frozen=True)
class Method:
    label: str
    source: str
    cell: str
    family: str
    group: str
    description: str
    overrides: dict[str, str] = field(default_factory=dict)
    hosted_70b: bool = False
    pe_family: bool = False


@dataclass(frozen=True)
class ConfigItem:
    cohort: str
    label: str
    source: str
    cell: str
    family: str
    scenario_set: ScenarioSet
    trials: int
    description: str
    overrides: dict[str, str]
    tags: tuple[str, ...]

    @property
    def rel_path(self) -> Path:
        safe_label = self.label.lower().replace("+", "p").replace("/", "_")
        return (
            Path("configs")
            / "config_universe"
            / "generated"
            / self.cohort
            / f"{safe_label}.env"
        )


def scenario_files(pattern: str) -> tuple[str, ...]:
    return tuple(
        sorted(
            path.relative_to(ROOT).as_posix()
            for path in (ROOT / "data" / "scenarios").glob(pattern)
        )
    )


def scenario_sets() -> dict[str, ScenarioSet]:
    all31 = tuple(
        sorted(
            path.relative_to(ROOT).as_posix()
            for path in (ROOT / "data" / "scenarios").glob("*.json")
            if path.is_file()
        )
    )
    return {
        "smoke1": ScenarioSet(
            "smoke1",
            "smartgrid_smoke1_v1",
            ("data/scenarios/multi_01_end_to_end_fault_response.json",),
            "smoke_single",
        ),
        "final6": ScenarioSet(
            "final6", "smartgrid_final6_v1", tuple(FINAL6), "mixed_final6"
        ),
        "all31": ScenarioSet("all31", "smartgrid_all31_v1", all31, "all31_canonical"),
        "generated5": ScenarioSet(
            "generated5",
            "smartgrid_generated_review5_20260503",
            scenario_files("generated/first_review_20260503/SGT-GEN-*.json"),
            "generated_review",
        ),
        "multi7": ScenarioSet(
            "multi7",
            "smartgrid_multi7_v1",
            scenario_files("multi_*.json"),
            "multi_domain",
        ),
        "fmsr7": ScenarioSet(
            "fmsr7",
            "smartgrid_fmsr7_v1",
            tuple(
                sorted(
                    scenario_files("fmsr_*.json") + scenario_files("aob_fmsr_*.json")
                )
            ),
            "fmsr",
        ),
        "iot6": ScenarioSet(
            "iot6", "smartgrid_iot6_v1", scenario_files("iot_*.json"), "iot"
        ),
        "tsfm5": ScenarioSet(
            "tsfm5", "smartgrid_tsfm5_v1", scenario_files("tsfm_*.json"), "tsfm"
        ),
        "wo6": ScenarioSet(
            "wo6", "smartgrid_wo6_v1", scenario_files("wo_*.json"), "wo"
        ),
    }


def model_optimized_overrides(context_len: int = 8192) -> dict[str, str]:
    return {
        "MODEL_ID": "openai/Llama-3.1-8B-Instruct-int8",
        "MODEL_PROVIDER": "vllm",
        "SERVING_STACK": "insomnia_vllm",
        "QUANTIZATION_MODE": "compressed-tensors-int8-bf16-fp8kv",
        "MAX_MODEL_LEN": str(context_len),
        "MAX_TOKENS": "1024",
        "LAUNCH_VLLM": "1",
        "VLLM_MODEL_PATH": "models/Llama-3.1-8B-Instruct-int8",
        "VLLM_SERVED_MODEL_NAME": "Llama-3.1-8B-Instruct-int8",
        "VLLM_DTYPE": "bfloat16",
        "VLLM_STARTUP_TIMEOUT": "1200",
        "EXTRA_VLLM_ARGS": "--quantization compressed-tensors --kv-cache-dtype fp8 --enable-prefix-caching",
        "AAT_MCP_CLIENT_TIMEOUT_SECONDS": "120",
    }


def hosted_70b_overrides() -> dict[str, str]:
    return {
        "MODEL_ID": WATSONX_70B_MODEL,
        "MODEL_PROVIDER": "watsonx",
        "SERVING_STACK": "watsonx_api",
        "QUANTIZATION_MODE": "provider_managed_fp8",
        "LAUNCH_VLLM": "0",
        "TORCH_PROFILE": "0",
        "ENABLE_WANDB": "0",
        "WANDB_MODE": "offline",
        "EXTRA_VLLM_ARGS": "",
        "AAT_MCP_SERVER_LAUNCH_MODE": "uv",
        "AAT_MCP_CLIENT_TIMEOUT_SECONDS": "180",
        "AAT_PARALLEL_TOOL_CALLS": "false",
        "PLAN_EXECUTE_REPO_LOCAL": "1",
        "JUDGE_MODEL": JUDGE_MODEL,
    }


def pe_method(
    label: str,
    source: str,
    cell: str,
    description: str,
    *,
    transport: bool = False,
    model_optimized: bool = False,
) -> Method:
    overrides: dict[str, str] = {}
    if transport:
        overrides.update(
            {
                "MCP_MODE": "optimized",
                "PLAN_EXECUTE_REPO_LOCAL": "1",
                "AAT_MCP_CLIENT_TIMEOUT_SECONDS": "120",
            }
        )
    if model_optimized:
        overrides.update(model_optimized_overrides())
    return Method(
        label=label,
        source=source,
        cell=cell,
        family="config_universe_local8b",
        group="pe_family",
        description=description,
        overrides=overrides,
        hosted_70b=not model_optimized,
        pe_family=True,
    )


def local_methods() -> list[Method]:
    methods = [
        Method(
            "AT_I",
            "configs/aat_direct.env",
            "AT_I",
            "config_universe_local8b",
            "aat",
            "AaT direct Python tools",
            hosted_70b=True,
        ),
        Method(
            "AT_M",
            "configs/aat_mcp_baseline.env",
            "AT_M",
            "config_universe_local8b",
            "aat",
            "AaT MCP baseline transport",
            hosted_70b=True,
        ),
        Method(
            "AT_T",
            "configs/aat_mcp_optimized.env",
            "AT_T",
            "config_universe_local8b",
            "aat",
            "AaT optimized MCP transport plus prefix caching",
            hosted_70b=True,
        ),
        Method(
            "AT_D",
            "configs/aat_mcp_model_optimized.env",
            "AT_D",
            "config_universe_local8b",
            "aat",
            "AaT optimized MCP plus local INT8/BF16/fp8KV serving",
        ),
    ]

    y = "configs/experiment2/exp2_cell_Y_pe_mcp_baseline.env"
    ys = "configs/experiment2/exp2_cell_Y_pe_self_ask_mcp_baseline.env"
    z = "configs/experiment2/exp2_cell_Z_verified_pe_mcp_baseline.env"
    zs = "configs/experiment2/exp2_cell_Z_verified_pe_self_ask_mcp_baseline.env"

    methods.extend(
        [
            pe_method("PE_M", y, "PE_M", "Plan-Execute MCP baseline"),
            pe_method(
                "PE_S_M", ys, "PE_S_M", "Plan-Execute plus Self-Ask on MCP baseline"
            ),
            pe_method(
                "PE_T",
                y,
                "PE_T",
                "Plan-Execute optimized MCP transport",
                transport=True,
            ),
            pe_method(
                "PE_S_T",
                ys,
                "PE_S_T",
                "Plan-Execute plus Self-Ask with optimized MCP transport",
                transport=True,
            ),
            pe_method(
                "PE_D",
                y,
                "PE_D",
                "Plan-Execute with local INT8/BF16/fp8KV serving",
                model_optimized=True,
            ),
            pe_method(
                "PE_S_D",
                ys,
                "PE_S_D",
                "Plan-Execute plus Self-Ask with local INT8/BF16/fp8KV serving",
                model_optimized=True,
            ),
            pe_method(
                "PE_TD",
                y,
                "PE_TD",
                "Plan-Execute optimized MCP plus local INT8/BF16/fp8KV serving",
                transport=True,
                model_optimized=True,
            ),
            pe_method(
                "PE_S_TD",
                ys,
                "PE_S_TD",
                "Plan-Execute plus Self-Ask, optimized MCP, and local INT8/BF16/fp8KV serving",
                transport=True,
                model_optimized=True,
            ),
            pe_method("V_M", z, "V_M", "Verified PE MCP baseline"),
            pe_method(
                "V_S_M", zs, "V_S_M", "Verified PE plus Self-Ask on MCP baseline"
            ),
            pe_method(
                "V_T", z, "V_T", "Verified PE optimized MCP transport", transport=True
            ),
            pe_method(
                "V_S_T",
                zs,
                "V_S_T",
                "Verified PE plus Self-Ask with optimized MCP transport",
                transport=True,
            ),
            pe_method(
                "V_D",
                z,
                "V_D",
                "Verified PE with local INT8/BF16/fp8KV serving",
                model_optimized=True,
            ),
            pe_method(
                "V_S_D",
                zs,
                "V_S_D",
                "Verified PE plus Self-Ask with local INT8/BF16/fp8KV serving",
                model_optimized=True,
            ),
            pe_method(
                "V_TD",
                z,
                "V_TD",
                "Verified PE optimized MCP plus local INT8/BF16/fp8KV serving",
                transport=True,
                model_optimized=True,
            ),
            pe_method(
                "V_S_TD",
                zs,
                "V_S_TD",
                "Verified PE plus Self-Ask, optimized MCP, and local INT8/BF16/fp8KV serving",
                transport=True,
                model_optimized=True,
            ),
        ]
    )
    return methods


MITIGATION_RUNGS: tuple[tuple[str, str, dict[str, str]], ...] = (
    ("BASELINE", "no mitigation flags", {}),
    ("GUARD", "missing-evidence detector only", {"ENABLE_MISSING_EVIDENCE_GUARD": "1"}),
    (
        "REPAIR",
        "missing-evidence detector plus retry/replan repair",
        {
            "ENABLE_MISSING_EVIDENCE_GUARD": "1",
            "ENABLE_MISSING_EVIDENCE_REPAIR": "1",
            "MISSING_EVIDENCE_REPAIR_MAX_ATTEMPTS": "2",
            "MISSING_EVIDENCE_REPAIR_MAX_ATTEMPTS_PER_TARGET": "1",
        },
    ),
    (
        "ADJ",
        "repair plus explicit fault/risk adjudication",
        {
            "ENABLE_MISSING_EVIDENCE_GUARD": "1",
            "ENABLE_MISSING_EVIDENCE_REPAIR": "1",
            "ENABLE_EXPLICIT_FAULT_RISK_ADJUDICATION": "1",
            "MISSING_EVIDENCE_REPAIR_MAX_ATTEMPTS": "2",
            "MISSING_EVIDENCE_REPAIR_MAX_ATTEMPTS_PER_TARGET": "1",
        },
    ),
)


def shell_quote(value: str) -> str:
    escaped = (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("$", "\\$")
        .replace("`", "\\`")
    )
    return f'"{escaped}"'


def write_config(item: ConfigItem) -> None:
    out_path = ROOT / item.rel_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    experiment_name = f"{item.cohort}_{item.label}".lower()
    experiment_name = experiment_name.replace("+", "p").replace("/", "_")
    merged = {
        "EXPERIMENT_NAME": experiment_name,
        "EXPERIMENT_CELL": item.cell,
        "EXPERIMENT_FAMILY": item.family,
        "SCENARIO_SET_NAME": item.scenario_set.name,
        "SCENARIOS_GLOB": " ".join(item.scenario_set.files),
        "TRIALS": str(item.trials),
        "SCENARIO_DOMAIN_SCOPE": item.scenario_set.scope,
        "CONTRIBUTING_EXPERIMENTS": ",".join(item.tags),
        "TORCH_PROFILE": "0",
        "SMARTGRID_RESUME_REQUIRE_LATENCY": "1",
    }
    merged.update(item.overrides)

    lines = [
        "# Generated by scripts/generate_config_universe.py. Do not edit by hand.",
        f"# Cohort: {item.cohort}",
        f"# Row: {item.label}",
        f"# Description: {item.description}",
        f"source {item.source}",
        "",
    ]
    for key in sorted(merged):
        lines.append(f"{key}={shell_quote(merged[key])}")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def add_method_configs(
    items: list[ConfigItem],
    *,
    cohort: str,
    methods: list[Method],
    scenario_set: ScenarioSet,
    trials: int,
    tags: tuple[str, ...],
    hosted_70b: bool = False,
) -> None:
    for method in methods:
        overrides = dict(method.overrides)
        family = method.family
        cell = method.cell
        label = method.label
        description = method.description
        if hosted_70b:
            if not method.hosted_70b:
                continue
            overrides.update(hosted_70b_overrides())
            family = "config_universe_watsonx70b"
            cell = f"{method.cell}70B"
            label = f"{method.label}70B"
            description = f"Hosted WatsonX 70B variant of {method.description}"
        items.append(
            ConfigItem(
                cohort=cohort,
                label=label,
                source=method.source,
                cell=cell,
                family=family,
                scenario_set=scenario_set,
                trials=trials,
                description=description,
                overrides=overrides,
                tags=tags,
            )
        )


def add_mitigation_configs(
    items: list[ConfigItem],
    *,
    cohort: str,
    methods: list[Method],
    scenario_set: ScenarioSet,
    trials: int,
    hosted_70b: bool = False,
) -> None:
    for method in methods:
        if not method.pe_family:
            continue
        if hosted_70b and not method.hosted_70b:
            continue
        base_overrides = dict(method.overrides)
        family = "config_universe_mitigation"
        cell_prefix = method.cell
        label_prefix = method.label
        description_prefix = method.description
        if hosted_70b:
            base_overrides.update(hosted_70b_overrides())
            family = "config_universe_watsonx70b_mitigation"
            cell_prefix = f"{method.cell}70B"
            label_prefix = f"{method.label}70B"
            description_prefix = f"Hosted WatsonX 70B variant of {method.description}"
        for rung, rung_desc, rung_overrides in MITIGATION_RUNGS:
            overrides = dict(base_overrides)
            overrides.update(rung_overrides)
            label = f"{label_prefix}_{rung}"
            items.append(
                ConfigItem(
                    cohort=cohort,
                    label=label,
                    source=method.source,
                    cell=f"{cell_prefix}_{rung}",
                    family=family,
                    scenario_set=scenario_set,
                    trials=trials,
                    description=f"{description_prefix}; mitigation rung {rung}: {rung_desc}",
                    overrides=overrides,
                    tags=(
                        "config_universe",
                        "failure_mitigation",
                        "full_cross_product",
                    ),
                )
            )


def add_context_configs(
    items: list[ConfigItem],
    *,
    cohort: str,
    methods: list[Method],
    scenario_set: ScenarioSet,
    trials: int,
) -> None:
    for method in methods:
        for context_len in (8192, 16384, 32768):
            overrides = dict(method.overrides)
            overrides["MAX_MODEL_LEN"] = str(context_len)
            if "int8" in overrides.get("MODEL_ID", ""):
                overrides.update(model_optimized_overrides(context_len))
            label = f"{method.label}_{context_len // 1024}K"
            items.append(
                ConfigItem(
                    cohort=cohort,
                    label=label,
                    source=method.source,
                    cell=f"{method.cell}_{context_len // 1024}K",
                    family="config_universe_context_ablation",
                    scenario_set=scenario_set,
                    trials=trials,
                    description=f"{method.description}; context-window ablation at {context_len}",
                    overrides=overrides,
                    tags=("config_universe", "context_ablation", "full_cross_product"),
                )
            )


def add_repair_depth_configs(
    items: list[ConfigItem],
    *,
    cohort: str,
    methods: list[Method],
    scenario_set: ScenarioSet,
    trials: int,
) -> None:
    selected = {
        method.label
        for method in methods
        if method.label in {"PE_S_M", "PE_S_T", "V_S_M", "V_S_T"}
    }
    for method in methods:
        if method.label not in selected:
            continue
        for attempts in (1, 2, 3):
            for rung in ("REPAIR", "ADJ"):
                overrides = dict(method.overrides)
                overrides.update(
                    {
                        "ENABLE_MISSING_EVIDENCE_GUARD": "1",
                        "ENABLE_MISSING_EVIDENCE_REPAIR": "1",
                        "MISSING_EVIDENCE_REPAIR_MAX_ATTEMPTS": str(attempts),
                        "MISSING_EVIDENCE_REPAIR_MAX_ATTEMPTS_PER_TARGET": "1",
                    }
                )
                if rung == "ADJ":
                    overrides["ENABLE_EXPLICIT_FAULT_RISK_ADJUDICATION"] = "1"
                label = f"{method.label}_{rung}_R{attempts}"
                items.append(
                    ConfigItem(
                        cohort=cohort,
                        label=label,
                        source=method.source,
                        cell=f"{method.cell}_{rung}_R{attempts}",
                        family="config_universe_repair_depth_ablation",
                        scenario_set=scenario_set,
                        trials=trials,
                        description=f"{method.description}; {rung.lower()} with {attempts} repair attempts",
                        overrides=overrides,
                        tags=("config_universe", "mitigation_repair_depth_ablation"),
                    )
                )


def add_temperature_configs(
    items: list[ConfigItem],
    *,
    cohort: str,
    methods: list[Method],
    scenario_set: ScenarioSet,
    trials: int,
) -> None:
    selected = {"AT_I", "AT_M", "AT_T", "PE_M", "PE_S_M", "V_M", "V_S_M"}
    for method in methods:
        if method.label not in selected:
            continue
        for temp in ("0.2", "0.7"):
            overrides = dict(method.overrides)
            overrides["TEMPERATURE"] = temp
            label = f"{method.label}_TEMP{temp.replace('.', '')}"
            items.append(
                ConfigItem(
                    cohort=cohort,
                    label=label,
                    source=method.source,
                    cell=f"{method.cell}_T{temp.replace('.', '')}",
                    family="config_universe_decoding_ablation",
                    scenario_set=scenario_set,
                    trials=trials,
                    description=f"{method.description}; decoding temperature {temp}",
                    overrides=overrides,
                    tags=("config_universe", "decoding_ablation"),
                )
            )


def build_items() -> list[ConfigItem]:
    sets = scenario_sets()
    methods = local_methods()
    items: list[ConfigItem] = []

    add_method_configs(
        items,
        cohort="local_smoke1x1_full",
        methods=methods,
        scenario_set=sets["smoke1"],
        trials=1,
        tags=("config_universe", "smoke", "local8b"),
    )
    add_method_configs(
        items,
        cohort="local_all31x5_full",
        methods=methods,
        scenario_set=sets["all31"],
        trials=5,
        tags=("config_universe", "local8b", "full_cross_product"),
    )
    add_method_configs(
        items,
        cohort="local_generated5x5_full",
        methods=methods,
        scenario_set=sets["generated5"],
        trials=5,
        tags=("config_universe", "local8b", "generated_scenarios"),
    )
    for key in ("multi7", "fmsr7", "iot6", "tsfm5", "wo6"):
        add_method_configs(
            items,
            cohort=f"local_{key}_5x_full",
            methods=methods,
            scenario_set=sets[key],
            trials=5,
            tags=("config_universe", "local8b", "domain_slice"),
        )
    add_mitigation_configs(
        items,
        cohort="mitigation_all31x5_full",
        methods=methods,
        scenario_set=sets["all31"],
        trials=5,
    )
    add_mitigation_configs(
        items,
        cohort="mitigation_generated5x5_full",
        methods=methods,
        scenario_set=sets["generated5"],
        trials=5,
    )
    add_context_configs(
        items,
        cohort="context_all31x3_full",
        methods=methods,
        scenario_set=sets["all31"],
        trials=3,
    )
    add_repair_depth_configs(
        items,
        cohort="repair_depth_all31x3",
        methods=methods,
        scenario_set=sets["all31"],
        trials=3,
    )
    add_temperature_configs(
        items,
        cohort="decoding_all31x3",
        methods=methods,
        scenario_set=sets["all31"],
        trials=3,
    )
    add_method_configs(
        items,
        cohort="watsonx70b_smoke1x1_full",
        methods=methods,
        scenario_set=sets["smoke1"],
        trials=1,
        tags=("config_universe", "smoke", "watsonx70b"),
        hosted_70b=True,
    )
    add_method_configs(
        items,
        cohort="watsonx70b_all31x5_full",
        methods=methods,
        scenario_set=sets["all31"],
        trials=5,
        tags=("config_universe", "watsonx70b", "full_cross_product"),
        hosted_70b=True,
    )
    add_method_configs(
        items,
        cohort="watsonx70b_generated5x5_full",
        methods=methods,
        scenario_set=sets["generated5"],
        trials=5,
        tags=("config_universe", "watsonx70b", "generated_scenarios"),
        hosted_70b=True,
    )
    add_mitigation_configs(
        items,
        cohort="watsonx70b_mitigation_all31x5_full",
        methods=methods,
        scenario_set=sets["all31"],
        trials=5,
        hosted_70b=True,
    )
    add_mitigation_configs(
        items,
        cohort="watsonx70b_mitigation_generated5x5_full",
        methods=methods,
        scenario_set=sets["generated5"],
        trials=5,
        hosted_70b=True,
    )
    return items


def clear_generated() -> None:
    for root in (GENERATED_ROOT, COHORT_ROOT):
        if root.exists():
            for path in sorted(root.rglob("*"), reverse=True):
                if path.is_file():
                    path.unlink()
                elif path.is_dir():
                    path.rmdir()
        root.mkdir(parents=True, exist_ok=True)


def write_catalog(items: list[ConfigItem]) -> None:
    CATALOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CATALOG_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(
            [
                "cohort",
                "label",
                "config",
                "runtime_family",
                "scenario_set",
                "scenario_count",
                "trials",
                "expected_trajectories",
                "source",
                "cell",
                "description",
                "tags",
            ]
        )
        for item in sorted(items, key=lambda i: (i.cohort, i.label)):
            writer.writerow(
                [
                    item.cohort,
                    item.label,
                    item.rel_path.as_posix(),
                    item.family,
                    item.scenario_set.name,
                    len(item.scenario_set.files),
                    item.trials,
                    len(item.scenario_set.files) * item.trials,
                    item.source,
                    item.cell,
                    item.description,
                    ",".join(item.tags),
                ]
            )


def write_cohorts(items: list[ConfigItem]) -> None:
    by_cohort: dict[str, list[ConfigItem]] = {}
    for item in items:
        by_cohort.setdefault(item.cohort, []).append(item)
    for cohort, cohort_items in sorted(by_cohort.items()):
        path = COHORT_ROOT / f"{cohort}.tsv"
        with path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter="\t")
            writer.writerow(["label", "config"])
            for item in sorted(cohort_items, key=lambda i: i.label):
                writer.writerow([item.label, item.rel_path.as_posix()])


def write_readme(items: list[ConfigItem]) -> None:
    by_cohort: dict[str, list[ConfigItem]] = {}
    for item in items:
        by_cohort.setdefault(item.cohort, []).append(item)
    lines = [
        "# Config Universe",
        "",
        "Generated SmartGridBench experiment configs for opportunistic compute waves.",
        "The evidence registry, not this directory, decides which completed runs are paper-grade.",
        "",
        "Materialize the per-row `.env` files locally on a VM with:",
        "",
        "```bash",
        "python3 scripts/generate_config_universe.py",
        "```",
        "",
        "This writes ignored files under `configs/config_universe/generated/`. The",
        "tracked source of truth is the generator plus this directory's `catalog.tsv` and",
        "`cohorts/*.tsv` manifests. Each cohort TSV has the existing two-column runner",
        "shape: `label` and `config`, and the `config` paths resolve after local",
        "materialization.",
        "",
        "Check that the tracked manifests are fresh with:",
        "",
        "```bash",
        "python3 scripts/generate_config_universe.py --check",
        "```",
        "",
        "`--check` regenerates in place before comparing tracked manifests. If it",
        "fails, run the generator normally and inspect the resulting diff.",
        "",
        "## Cohorts",
        "",
        "| Cohort | Rows | Expected trajectories | Notes |",
        "|---|---:|---:|---|",
    ]
    for cohort, cohort_items in sorted(by_cohort.items()):
        expected = sum(
            len(item.scenario_set.files) * item.trials for item in cohort_items
        )
        note = {
            "local_smoke1x1_full": "one-scenario local 8B smoke for every local method row",
            "local_all31x5_full": "full local 8B method cross-product over the canonical scenario set",
            "local_generated5x5_full": "local 8B method cross-product over the latest reviewed generated-scenario batch",
            "mitigation_all31x5_full": "4-tier mitigation ladder crossed with every PE-family local method",
            "mitigation_generated5x5_full": "4-tier mitigation ladder over the latest reviewed generated-scenario batch",
            "context_all31x3_full": "8K/16K/32K context ablations for every local method row",
            "repair_depth_all31x3": "repair/adjudication depth ablation on the main Self-Ask PE-family rows",
            "decoding_all31x3": "temperature ablation on core local rows",
            "watsonx70b_smoke1x1_full": "one-scenario hosted-70B smoke for every hosted-compatible method row",
            "watsonx70b_all31x5_full": "hosted-70B all-31 core/transport PE-family expansion",
            "watsonx70b_generated5x5_full": "hosted-70B method cross-product over the latest reviewed generated-scenario batch",
            "watsonx70b_mitigation_all31x5_full": "hosted-70B mitigation ladder for hosted-compatible PE-family rows",
            "watsonx70b_mitigation_generated5x5_full": "hosted-70B mitigation ladder over the latest reviewed generated-scenario batch",
        }.get(cohort, "")
        if (
            cohort.startswith("local_")
            and cohort.endswith("_5x_full")
            and "_all31" not in cohort
            and "_generated" not in cohort
        ):
            note = "local 8B method cross-product on one canonical domain slice"
        lines.append(f"| `{cohort}` | {len(cohort_items)} | {expected} | {note} |")
    lines.extend(
        [
            "",
            "## Guardrails",
            "",
            "- Run `local_smoke1x1_full` or `watsonx70b_smoke1x1_full` before a new family if access or runner state changed.",
            "- Preserve raw run directories. Promote only after pullback, count validation, judge rows, and registry review.",
            "- Hosted WatsonX rows require fresh credentials plus all aliases: `WATSONX_APIKEY`, `WATSONX_API_KEY`, `WX_API_KEY`, `WATSONX_PROJECT_ID`, `WX_PROJECT_ID`, `WATSONX_URL`, `WX_URL`.",
            "- D/TD local rows require the INT8 model path and FlashInfer build dependencies on the VM.",
            "",
        ]
    )
    (OUT_ROOT / "README.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="regenerate in place and fail if tracked catalog/cohort docs are stale",
    )
    args = parser.parse_args()

    before: dict[Path, str] = {}
    if args.check and OUT_ROOT.exists():
        for path in OUT_ROOT.rglob("*"):
            if path.is_relative_to(GENERATED_ROOT):
                continue
            if path.is_file():
                before[path.relative_to(ROOT)] = path.read_text(encoding="utf-8")

    items = build_items()
    clear_generated()
    for item in items:
        write_config(item)
    write_cohorts(items)
    write_catalog(items)
    write_readme(items)

    if args.check:
        after = {
            path.relative_to(ROOT): path.read_text(encoding="utf-8")
            for path in OUT_ROOT.rglob("*")
            if path.is_file() and not path.is_relative_to(GENERATED_ROOT)
        }
        if before != after:
            print(
                "ERROR: config-universe tracked manifests are stale. "
                "Run scripts/generate_config_universe.py."
            )
            return 1

    print(f"generated {len(items)} configs in {GENERATED_ROOT.relative_to(ROOT)}")
    print(f"wrote catalog: {CATALOG_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
