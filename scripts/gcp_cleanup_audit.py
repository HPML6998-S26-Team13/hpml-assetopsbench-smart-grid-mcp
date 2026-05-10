#!/usr/bin/env python3
"""Read-only GCP fallback cleanup audit for Issue #91 closeout."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

DEFAULT_REGIONS = (
    "us-central1",
    "us-east1",
    "us-east4",
    "us-west1",
    "us-west3",
    "us-west4",
)

RESOURCE_COMMANDS = {
    "instances": ("compute", "instances", "list"),
    "disks": ("compute", "disks", "list"),
    "snapshots": ("compute", "snapshots", "list"),
    "routers": ("compute", "routers", "list"),
    "addresses": ("compute", "addresses", "list"),
}

QUOTA_MARKERS = (
    "A100",
    "GPU",
    "CPUS",
    "DISKS",
    "SSD",
    "ADDRESSES",
)

DEFAULT_GCLOUD_TIMEOUT_SECONDS = 120

Runner = Callable[..., subprocess.CompletedProcess[str]]


def _utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def _split_csv(values: Sequence[str] | None) -> list[str]:
    if not values:
        return list(DEFAULT_REGIONS)
    out: list[str] = []
    for value in values:
        out.extend(part.strip() for part in value.split(",") if part.strip())
    return out or list(DEFAULT_REGIONS)


def _resource_leaf(value: str | None) -> str:
    if not value:
        return ""
    return value.rstrip("/").rsplit("/", 1)[-1]


def _gcloud_command(
    args: Sequence[str],
    *,
    project: str,
    account: str | None,
) -> list[str]:
    command = ["gcloud", *args]
    command.append(f"--project={project}")
    if account:
        command.append(f"--account={account}")
    command.extend(["--format=json", "--quiet"])
    return command


def _run_json(
    command: list[str], runner: Runner, *, timeout_seconds: int
) -> dict[str, Any]:
    try:
        result = runner(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "ok": False,
            "command": command,
            "items": [],
            "error": f"gcloud timed out after {timeout_seconds}s: {exc}",
        }
    if result.returncode != 0:
        return {
            "ok": False,
            "command": command,
            "items": [],
            "error": (result.stderr or result.stdout or "").strip(),
        }
    stdout = (result.stdout or "").strip()
    try:
        payload = json.loads(stdout) if stdout else []
    except json.JSONDecodeError as exc:
        return {
            "ok": False,
            "command": command,
            "items": [],
            "error": f"invalid JSON from gcloud: {exc}",
        }
    return {"ok": True, "command": command, "items": payload, "error": ""}


def _interesting_quotas(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        quotas = payload.get("quotas") or []
    elif isinstance(payload, list):
        quotas = payload
    else:
        quotas = []
    out = []
    for quota in quotas:
        metric = str(quota.get("metric") or quota.get("quotaId") or "")
        if any(marker in metric.upper() for marker in QUOTA_MARKERS):
            out.append(quota)
    return out


def collect_audit(
    *,
    project: str,
    account: str | None = None,
    regions: Sequence[str] = DEFAULT_REGIONS,
    runner: Runner = subprocess.run,
    dry_run: bool = False,
    timeout_seconds: int = DEFAULT_GCLOUD_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    audit: dict[str, Any] = {
        "schema_version": 1,
        "generated_at": _utc_now(),
        "project": project,
        "account": account,
        "regions": list(regions),
        "dry_run": dry_run,
        "resources": {},
        "quota_preferences": {},
        "quota_snapshot": {"global": {}, "regions": {}},
    }

    for name, base in RESOURCE_COMMANDS.items():
        command = _gcloud_command(base, project=project, account=account)
        audit["resources"][name] = (
            {"ok": True, "command": command, "items": [], "error": ""}
            if dry_run
            else _run_json(command, runner, timeout_seconds=timeout_seconds)
        )

    routers = audit["resources"]["routers"]
    nat_entries: list[dict[str, Any]] = []
    if routers["ok"]:
        for router in routers["items"]:
            router_name = router.get("name")
            region = _resource_leaf(router.get("region"))
            if not router_name or not region:
                continue
            command = _gcloud_command(
                (
                    "compute",
                    "routers",
                    "nats",
                    "list",
                    "--router",
                    router_name,
                    "--region",
                    region,
                ),
                project=project,
                account=account,
            )
            result = (
                {"ok": True, "command": command, "items": [], "error": ""}
                if dry_run
                else _run_json(command, runner, timeout_seconds=timeout_seconds)
            )
            nat_entries.append({"router": router_name, "region": region, **result})
        audit["resources"]["router_nats"] = {
            "ok": all(entry["ok"] for entry in nat_entries),
            "command": routers["command"],
            "commands": [entry["command"] for entry in nat_entries],
            "items": nat_entries,
            "error": "; ".join(
                entry["error"] for entry in nat_entries if entry.get("error")
            ),
        }
    else:
        audit["resources"]["router_nats"] = {
            "ok": False,
            "command": routers["command"],
            "commands": [],
            "items": [],
            "error": f"routers list failed; router NAT audit skipped: {routers.get('error')}",
        }

    preference_command = _gcloud_command(
        ("beta", "quotas", "preferences", "list"),
        project=project,
        account=account,
    )
    audit["quota_preferences"] = (
        {"ok": True, "command": preference_command, "items": [], "error": ""}
        if dry_run
        else _run_json(preference_command, runner, timeout_seconds=timeout_seconds)
    )

    global_command = _gcloud_command(
        ("compute", "project-info", "describe"),
        project=project,
        account=account,
    )
    global_result = (
        {"ok": True, "command": global_command, "items": {}, "error": ""}
        if dry_run
        else _run_json(global_command, runner, timeout_seconds=timeout_seconds)
    )
    audit["quota_snapshot"]["global"] = {
        **global_result,
        "items": _interesting_quotas(global_result["items"]),
    }

    for region in regions:
        command = _gcloud_command(
            ("compute", "regions", "describe", region),
            project=project,
            account=account,
        )
        result = (
            {"ok": True, "command": command, "items": {}, "error": ""}
            if dry_run
            else _run_json(command, runner, timeout_seconds=timeout_seconds)
        )
        audit["quota_snapshot"]["regions"][region] = {
            **result,
            "items": _interesting_quotas(result["items"]),
        }

    return audit


def _quota_line(quota: dict[str, Any]) -> str:
    metric = quota.get("metric") or quota.get("quotaId") or "unknown"
    usage = quota.get("usage")
    limit = quota.get("limit")
    if usage is not None or limit is not None:
        return f"{metric}: usage={usage} limit={limit}"
    return str(metric)


def render_text(audit: dict[str, Any]) -> str:
    lines = [
        f"GCP cleanup audit project={audit['project']} account={audit.get('account') or '(active gcloud account)'}",
        f"generated_at={audit['generated_at']} dry_run={audit['dry_run']}",
    ]

    for name in ("instances", "disks", "snapshots", "routers", "addresses"):
        result = audit["resources"][name]
        items = result.get("items") or []
        status = "ok" if result.get("ok") else "ERROR"
        lines.append(f"{name}: {len(items)} [{status}]")
        if not result.get("ok"):
            lines.append(f"  error: {result.get('error')}")
            continue
        for item in items:
            region_or_zone = _resource_leaf(item.get("zone") or item.get("region"))
            suffix = f" ({region_or_zone})" if region_or_zone else ""
            lines.append(f"  - {item.get('name', '<unnamed>')}{suffix}")

    nat_result = audit["resources"]["router_nats"]
    nat_count = sum(
        len(entry.get("items") or []) for entry in nat_result.get("items") or []
    )
    lines.append(
        f"router_nats: {nat_count} [{'ok' if nat_result.get('ok') else 'ERROR'}]"
    )
    for entry in nat_result.get("items") or []:
        for nat in entry.get("items") or []:
            lines.append(
                f"  - {nat.get('name', '<unnamed>')} ({entry['region']}/{entry['router']})"
            )
        if not entry.get("ok"):
            lines.append(
                f"  error {entry['region']}/{entry['router']}: {entry.get('error')}"
            )

    preferences = audit["quota_preferences"]
    lines.append(
        f"quota_preferences: {len(preferences.get('items') or [])} [{'ok' if preferences.get('ok') else 'ERROR'}]"
    )
    if not preferences.get("ok"):
        lines.append(f"  error: {preferences.get('error')}")

    global_quotas = audit["quota_snapshot"]["global"]
    lines.append(f"global_quota_snapshot: {len(global_quotas.get('items') or [])}")
    for quota in global_quotas.get("items") or []:
        lines.append(f"  - {_quota_line(quota)}")

    for region, result in audit["quota_snapshot"]["regions"].items():
        lines.append(
            f"regional_quota_snapshot {region}: {len(result.get('items') or [])}"
        )
        if not result.get("ok"):
            lines.append(f"  error: {result.get('error')}")
            continue
        for quota in result.get("items") or []:
            lines.append(f"  - {_quota_line(quota)}")

    return "\n".join(lines) + "\n"


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read-only cleanup/cost audit for SmartGridBench GCP fallback projects."
    )
    parser.add_argument("--project", required=True, help="GCP project id to audit.")
    parser.add_argument("--account", help="Optional gcloud account to use.")
    parser.add_argument(
        "--regions",
        action="append",
        help="Comma-separated quota regions to snapshot. Defaults to known fallback regions.",
    )
    parser.add_argument(
        "--out", type=Path, help="Optional path for the JSON audit artifact."
    )
    parser.add_argument(
        "--json", action="store_true", help="Print JSON instead of text."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Record the read-only gcloud commands without executing them; "
            "--out still writes the dry-run audit JSON."
        ),
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    audit = collect_audit(
        project=args.project,
        account=args.account,
        regions=_split_csv(args.regions),
        dry_run=args.dry_run,
    )
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(
            json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    if args.json:
        print(json.dumps(audit, indent=2, sort_keys=True))
    else:
        print(render_text(audit), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
