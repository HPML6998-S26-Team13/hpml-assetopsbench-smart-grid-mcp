import csv
import json
from pathlib import Path

REQUIRED_KEYS = {"id", "type", "text", "category", "characteristic_form"}
ALLOWED_TYPES = {"", "IoT", "FMSR", "TSFM", "WO"}


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

    if "asset_id" in payload:
        asset_id = payload["asset_id"]
        if not isinstance(asset_id, str):
            errors.append(f"{path.name}: 'asset_id' must be a string")
        elif asset_id not in valid_asset_ids:
            errors.append(f"{path.name}: unknown asset_id '{asset_id}'")

    return errors


def main() -> int:
    root = Path(__file__).resolve().parent
    asset_csv = root.parent / "processed" / "asset_metadata.csv"
    scenario_files = sorted(
        [p for p in root.glob("*.json") if p.name.lower() != "schema.json"]
    )

    if not asset_csv.exists():
        print(f"ERROR: missing asset metadata file: {asset_csv}")
        return 1

    valid_asset_ids = load_valid_asset_ids(asset_csv)
    all_errors: list[str] = []

    for scenario in scenario_files:
        all_errors.extend(validate_file(scenario, valid_asset_ids))

    if all_errors:
        print("Scenario validation failed:")
        for err in all_errors:
            print(f"- {err}")
        return 1

    print(f"Validation passed for {len(scenario_files)} scenario files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
