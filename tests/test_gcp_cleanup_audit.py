from __future__ import annotations

import json
import subprocess
from pathlib import Path

from scripts import gcp_cleanup_audit


class FakeGcloud:
    def __init__(self) -> None:
        self.commands: list[list[str]] = []

    def __call__(self, command, **kwargs):
        self.commands.append(list(command))
        joined = " ".join(command)
        if "compute instances list" in joined:
            payload = [
                {
                    "name": "smartgrid-a100-demo",
                    "zone": "https://www.googleapis.com/compute/v1/projects/p/zones/us-east1-b",
                }
            ]
        elif "compute disks list" in joined:
            payload = [{"name": "smartgrid-a100-demo", "zone": "zones/us-east1-b"}]
        elif "compute snapshots list" in joined:
            payload = [{"name": "smartgrid-a100-snapshot"}]
        elif "compute routers list" in joined:
            payload = [
                {
                    "name": "smartgrid-nat-router",
                    "region": "https://www.googleapis.com/compute/v1/projects/p/regions/us-central1",
                }
            ]
        elif "compute routers nats list" in joined:
            payload = [{"name": "smartgrid-nat"}]
        elif "compute addresses list" in joined:
            payload = [{"name": "smartgrid-static-ip", "region": "regions/us-central1"}]
        elif "beta quotas preferences list" in joined:
            payload = [{"name": "projects/p/locations/global/quotaPreferences/a100"}]
        elif "compute project-info describe" in joined:
            payload = {
                "quotas": [{"metric": "GPUS_ALL_REGIONS", "usage": 1.0, "limit": 1.0}]
            }
        elif "compute regions describe" in joined:
            payload = {
                "quotas": [
                    {
                        "metric": "PREEMPTIBLE_NVIDIA_A100_GPUS",
                        "usage": 1.0,
                        "limit": 1.0,
                    },
                    {"metric": "CPUS", "usage": 4.0, "limit": 72.0},
                    {"metric": "UNRELATED", "usage": 0.0, "limit": 999.0},
                ]
            }
        else:
            raise AssertionError(f"unexpected command: {joined}")
        return subprocess.CompletedProcess(command, 0, json.dumps(payload), "")


def test_collect_audit_lists_cost_resources_and_router_nats() -> None:
    fake = FakeGcloud()

    audit = gcp_cleanup_audit.collect_audit(
        project="p",
        account="user@example.com",
        regions=["us-central1"],
        runner=fake,
    )

    assert audit["resources"]["instances"]["items"][0]["name"] == "smartgrid-a100-demo"
    assert audit["resources"]["router_nats"]["command"][:4] == [
        "gcloud",
        "compute",
        "routers",
        "list",
    ]
    assert audit["resources"]["router_nats"]["commands"][0][:4] == [
        "gcloud",
        "compute",
        "routers",
        "nats",
    ]
    assert audit["resources"]["router_nats"]["items"][0]["region"] == "us-central1"
    assert (
        audit["resources"]["router_nats"]["items"][0]["items"][0]["name"]
        == "smartgrid-nat"
    )
    assert audit["quota_preferences"]["items"][0]["name"].endswith("/a100")
    assert audit["quota_snapshot"]["global"]["items"][0]["metric"] == "GPUS_ALL_REGIONS"
    assert [
        q["metric"] for q in audit["quota_snapshot"]["regions"]["us-central1"]["items"]
    ] == [
        "PREEMPTIBLE_NVIDIA_A100_GPUS",
        "CPUS",
    ]
    assert any(
        "--account=user@example.com" in command
        for cmd in fake.commands
        for command in cmd
    )


def test_render_text_surfaces_resource_counts_and_quota_lines() -> None:
    audit = gcp_cleanup_audit.collect_audit(
        project="p",
        regions=["us-central1"],
        runner=FakeGcloud(),
    )

    text = gcp_cleanup_audit.render_text(audit)

    assert "instances: 1 [ok]" in text
    assert "router_nats: 1 [ok]" in text
    assert "quota_preferences: 1 [ok]" in text
    assert "GPUS_ALL_REGIONS: usage=1.0 limit=1.0" in text


def test_main_writes_json_artifact_in_dry_run(tmp_path: Path, capsys) -> None:
    out = tmp_path / "audit.json"

    rc = gcp_cleanup_audit.main(
        [
            "--project",
            "p",
            "--regions",
            "us-central1",
            "--dry-run",
            "--json",
            "--out",
            str(out),
        ]
    )

    printed = json.loads(capsys.readouterr().out)
    written = json.loads(out.read_text(encoding="utf-8"))
    assert rc == 0
    assert printed["dry_run"] is True
    assert written["resources"]["instances"]["command"][:4] == [
        "gcloud",
        "compute",
        "instances",
        "list",
    ]


def test_run_json_surfaces_failed_process_and_invalid_json() -> None:
    failed = gcp_cleanup_audit._run_json(
        ["gcloud", "bad"],
        lambda command, **kwargs: subprocess.CompletedProcess(
            command, 1, "", "permission denied"
        ),
        timeout_seconds=10,
    )
    invalid = gcp_cleanup_audit._run_json(
        ["gcloud", "bad-json"],
        lambda command, **kwargs: subprocess.CompletedProcess(command, 0, "{", ""),
        timeout_seconds=10,
    )

    assert failed == {
        "ok": False,
        "command": ["gcloud", "bad"],
        "items": [],
        "error": "permission denied",
    }
    assert invalid["ok"] is False
    assert invalid["command"] == ["gcloud", "bad-json"]
    assert "invalid JSON from gcloud" in invalid["error"]


def test_run_json_surfaces_timeout() -> None:
    def timeout_runner(command, **kwargs):
        raise subprocess.TimeoutExpired(command, timeout=kwargs["timeout"])

    result = gcp_cleanup_audit._run_json(
        ["gcloud", "slow"], timeout_runner, timeout_seconds=3
    )

    assert result["ok"] is False
    assert result["command"] == ["gcloud", "slow"]
    assert "timed out after 3s" in result["error"]


def test_router_nat_status_follows_router_list_failure() -> None:
    def failing_routers(command, **kwargs):
        joined = " ".join(command)
        if "compute routers list" in joined:
            return subprocess.CompletedProcess(
                command, 1, "", "router permission denied"
            )
        if "compute routers nats list" in joined:
            raise AssertionError("NAT commands should be skipped when routers fail")
        if (
            "compute project-info describe" in joined
            or "compute regions describe" in joined
        ):
            return subprocess.CompletedProcess(
                command, 0, json.dumps({"quotas": []}), ""
            )
        return subprocess.CompletedProcess(command, 0, "[]", "")

    audit = gcp_cleanup_audit.collect_audit(
        project="p",
        regions=["us-central1"],
        runner=failing_routers,
    )

    router_nats = audit["resources"]["router_nats"]
    assert router_nats["ok"] is False
    assert router_nats["command"][:4] == ["gcloud", "compute", "routers", "list"]
    assert router_nats["commands"] == []
    assert router_nats["items"] == []
    assert "router permission denied" in router_nats["error"]
