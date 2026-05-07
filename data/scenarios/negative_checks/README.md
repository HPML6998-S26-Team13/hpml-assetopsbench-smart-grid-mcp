---
status: canonical-index
scope: team-repo
owner: Team 13
canonical: true
---

# data/scenarios/negative_checks/

Invalid scenario fixtures used to verify validator failure modes. These are
canonical test fixtures, not candidate benchmark scenarios.

| File | Status | Purpose |
|---|---|---|
| `invalid_iot_cross_domain_tool.json` | test-fixture | Cross-domain tool misuse check. |
| `invalid_multi_missing_domain_coverage.json` | test-fixture | Missing domain coverage check. |
| `invalid_multi_single_domain_tag.json` | test-fixture | Multi/single-domain tag mismatch check. |
| `invalid_single_wrong_domain_tag.json` | test-fixture | Wrong single-domain tag check. |
| `invalid_unknown_tool.json` | test-fixture | Unknown tool rejection check. |
