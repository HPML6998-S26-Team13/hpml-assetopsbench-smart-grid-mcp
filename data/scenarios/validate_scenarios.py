import csv
import json
from pathlib import Path

REQUIRED_KEYS = {
    "id",
    "type",
    "text",
    "category",
    "characteristic_form",
    "expected_tools",
    "domain_tags",
}
ALLOWED_TYPES = {"IoT", "FMSR", "TSFM", "WO", "Multi"}
CANONICAL_TOOLS = {
    "IoT": {
        "iot.list_assets",
        "iot.get_asset_metadata",
        "iot.list_sensors",
        "iot.get_sensor_readings",
    },
    "FMSR": {
        "fmsr.list_failure_modes",
        "fmsr.search_failure_modes",
        "fmsr.get_sensor_correlation",
        "fmsr.get_dga_record",
        "fmsr.analyze_dga",
    },
    "TSFM": {
        "tsfm.get_rul",
        "tsfm.forecast_rul",
        "tsfm.detect_anomalies",
        "tsfm.trend_analysis",
    },
    "WO": {
        "wo.list_fault_records",
        "wo.get_fault_record",
        "wo.create_work_order",
        "wo.list_work_orders",
        "wo.update_work_order",
        "wo.estimate_downtime",
    },
}
ALL_CANONICAL_TOOLS = set().union(*CANONICAL_TOOLS.values())
TOOL_TO_DOMAIN = {
    tool: domain for domain, tools in CANONICAL_TOOLS.items() for tool in tools
}


def load_valid_asset_ids(asset_csv: Path) -> set[str]:
    with asset_csv.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return {row["transformer_id"] for row in reader if row.get("transformer_id")}


def validate_file(path: Path, valid_asset_ids: set[str]) -> list[str]:
    errors: list[str] = []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"{path.name}: invalid JSON ({exc})"]

    missing = REQUIRED_KEYS.difference(payload.keys())
    if missing:
        errors.append(f"{path.name}: missing required keys {sorted(missing)}")

    if "id" in payload and not isinstance(payload["id"], str):
        errors.append(f"{path.name}: 'id' must be a string")

    if "type" in payload:
        type_value = payload["type"]
        if not isinstance(type_value, str):
            errors.append(f"{path.name}: 'type' must be a string")
        elif type_value not in ALLOWED_TYPES:
            errors.append(f"{path.name}: 'type' must be one of {sorted(ALLOWED_TYPES)}")

    for field in ["text", "category", "characteristic_form"]:
        if field in payload and not isinstance(payload[field], str):
            errors.append(f"{path.name}: '{field}' must be a string")

    if "expected_tools" in payload:
        tools = payload["expected_tools"]
        if not isinstance(tools, list) or not tools:
            errors.append(f"{path.name}: 'expected_tools' must be a non-empty list")
        else:
            non_strings = [tool for tool in tools if not isinstance(tool, str)]
            if non_strings:
                errors.append(f"{path.name}: all expected tools must be strings")
            unknown = [
                tool
                for tool in tools
                if isinstance(tool, str) and tool not in ALL_CANONICAL_TOOLS
            ]
            if unknown:
                errors.append(
                    f"{path.name}: unknown expected_tools {sorted(set(unknown))}"
                )

    if "domain_tags" in payload:
        domain_tags = payload["domain_tags"]
        if not isinstance(domain_tags, list) or not domain_tags:
            errors.append(f"{path.name}: 'domain_tags' must be a non-empty list")
        else:
            invalid_tags = [
                tag
                for tag in domain_tags
                if not isinstance(tag, str) or tag not in CANONICAL_TOOLS
            ]
            if invalid_tags:
                errors.append(
                    f"{path.name}: invalid domain_tags {sorted(set(map(str, invalid_tags)))}"
                )

    if "asset_id" in payload:
        asset_id = payload["asset_id"]
        if not isinstance(asset_id, str):
            errors.append(f"{path.name}: 'asset_id' must be a string")
        elif asset_id not in valid_asset_ids:
            errors.append(f"{path.name}: unknown asset_id '{asset_id}'")

    if errors:
        return errors

    scenario_type = payload["type"]
    domain_tags = payload["domain_tags"]
    tools = payload["expected_tools"]
    tool_domains = {TOOL_TO_DOMAIN[tool] for tool in tools}

    if scenario_type != "Multi":
        if domain_tags != [scenario_type]:
            errors.append(
                f"{path.name}: single-domain scenarios must use domain_tags ['{scenario_type}']"
            )
        disallowed = [
            tool for tool in tools if tool not in CANONICAL_TOOLS[scenario_type]
        ]
        if disallowed:
            errors.append(
                f"{path.name}: {scenario_type} scenarios may only use {scenario_type} tools, found {sorted(set(disallowed))}"
            )
    else:
        if len(domain_tags) < 2:
            errors.append(
                f"{path.name}: Multi scenarios must declare at least 2 domain_tags"
            )
        if len(tool_domains) < 2:
            errors.append(
                f"{path.name}: Multi scenarios must reference tools from at least 2 domains"
            )
        missing_domains = [tag for tag in domain_tags if tag not in tool_domains]
        if missing_domains:
            errors.append(
                f"{path.name}: expected_tools do not cover domain_tags {sorted(missing_domains)}"
            )
        extra_domains = sorted(
            domain for domain in tool_domains if domain not in domain_tags
        )
        if extra_domains:
            errors.append(
                f"{path.name}: expected_tools reference domains not declared in domain_tags: {extra_domains}"
            )

    return errors


def main() -> int:
    root = Path(__file__).resolve().parent
    negatives_root = root / "negative_checks"
    asset_csv = root.parent / "processed" / "asset_metadata.csv"
    scenario_files = sorted(
        [p for p in root.glob("*.json") if p.name.lower() != "schema.json"]
    )
    if not negatives_root.is_dir():
        print(f"ERROR: negative_checks/ directory not found at {negatives_root}")
        return 1

    negative_files = sorted(negatives_root.glob("*.json"))

    if not negative_files:
        print(f"ERROR: no .json fixtures found in {negatives_root}")
        return 1

    if not asset_csv.exists():
        print(f"ERROR: missing asset metadata file: {asset_csv}")
        return 1

    valid_asset_ids = load_valid_asset_ids(asset_csv)
    all_errors: list[str] = []
    seen_ids: dict[str, str] = {}

    for scenario in scenario_files:
        all_errors.extend(validate_file(scenario, valid_asset_ids))
        try:
            payload = json.loads(scenario.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        scenario_id = payload.get("id")
        if isinstance(scenario_id, str):
            previous = seen_ids.get(scenario_id)
            if previous is not None:
                all_errors.append(
                    f"Duplicate scenario id '{scenario_id}' in {scenario.name} and {previous}"
                )
            else:
                seen_ids[scenario_id] = scenario.name

    negative_failures: list[str] = []
    for scenario in negative_files:
        fixture_errors = validate_file(scenario, valid_asset_ids)
        if not fixture_errors:
            negative_failures.append(
                f"{scenario.name}: expected validation failure, but fixture passed"
            )

    if all_errors:
        print("Scenario validation failed:")
        for err in all_errors:
            print(f"- {err}")
        return 1

    if negative_failures:
        print("Negative-check validation failed:")
        for err in negative_failures:
            print(f"- {err}")
        return 1

    print(
        f"Validation passed for {len(scenario_files)} scenario files and {len(negative_files)} negative fixtures."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
