#!/usr/bin/env python3
"""Backfill KB frontmatter onto reference docs prior to the Phase 3 move.

Dependency-free (stdlib only). Per file, if the file already has a leading
``---`` frontmatter block it is left untouched (idempotent). Otherwise the
8 required fields plus ``project``/``canonical`` are derived and a frontmatter
block is prepended:

    title    -- first ``# `` H1 heading, else the filename stem titleized
    slug     -- filename stem (no date prefix yet; pre-move bare name).
                Post-move the file is renamed ``<created>_<stem>.md`` and the
                validator matches ``slug`` to the topic portion after the date
                prefix, so the bare stem is the correct slug.
    type     -- reference
    status   -- live
    created  -- git first-commit ISO date for the path (oldest --follow line)
    updated  -- git last-commit ISO date (newest --follow line)
    owner    -- --owner (default "Alex Xin")
    scope    -- project   (requires a project field per the validator)
    project  -- --project (default: canonical repo basename)
    canonical-- true

The ``created`` date is ALSO the filename date prefix used by the dated
``git mv`` step, so prefix and ``created:`` are single-sourced and cannot
diverge.

Default is dry-run (prints the proposed block). ``--apply`` writes in place.
Run from anywhere; paths are resolved as given.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

OWNER = "Alex Xin"


def _slugify(value: str) -> str:
    """Lowercase-kebab slug — the contract for ``project:`` (and project-sources).
    A repo basename like ``Qurrhea`` or ``IXQT`` stamps an uppercase project value
    that keys the doc into a different bucket than the rest of the KB; slugifying
    keeps every entry in one project. Applied to both the default and an explicit
    ``--project`` so the field is always a valid slug."""
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "unknown"


def _default_project() -> str:
    """Project slug default = slugified CANONICAL repo basename, derived from the
    git-common-dir parent so it is correct from the root checkout OR a linked
    worktree. (show-toplevel would return the worktree directory name and stamp
    wrong ``project:`` metadata, e.g. ``agt-kb-phase3-xrepo`` instead of the repo.)"""
    common = subprocess.run(
        ["git", "rev-parse", "--git-common-dir"], text=True, capture_output=True
    ).stdout.strip()
    return _slugify(Path(common).resolve().parent.name) if common else "unknown"


def git_dates(path: Path) -> tuple[str, str]:
    """Return (created, updated) ISO dates from ``git log --follow``.

    Oldest commit date = created; newest = updated. Falls back to today if the
    file is not yet tracked (should not happen for the migration set).
    """
    out = subprocess.run(
        ["git", "log", "--follow", "--format=%ad", "--date=short", "--", str(path)],
        text=True,
        capture_output=True,
    ).stdout.splitlines()
    dates = [ln.strip() for ln in out if ln.strip()]
    if not dates:
        raise SystemExit(f"no git history for {path}; refusing to invent dates")
    return dates[-1], dates[0]  # oldest (created), newest (updated)


def derive_title(text: str, stem: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return stem.replace("-", " ").replace("_", " ").title()


def has_frontmatter(text: str) -> bool:
    return text.lstrip("﻿").startswith("---")


_YAML_BOOL = {"true", "false", "yes", "no", "on", "off", "y", "n"}
_YAML_NULL = {"null", "none", "~"}
_NUM_RE = re.compile(
    r"^[-+]?(\d[\d_]*(\.\d*)?|\.\d+)([eE][-+]?\d+)?$|^[-+]?0[xXoObB][0-9a-fA-F_]+$"
)
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")


def yaml_scalar(v: str) -> str:
    """Return a YAML-safe **string** scalar: double-quote (and escape) when leaving
    the value bare would either fail to parse OR type-shift it away from a string.
    Catches `: ` (mapping ambiguity, e.g. "Coordination Agent Wakeup: Desktop vs CLI"),
    leading indicator chars, AND bare values YAML would read as bool/null/number/date
    (`true`, `no`, `null`, `~`, `42`, `2026-01-01`). Clean prose passes through bare."""
    needs = (
        v == ""
        or v != v.strip()
        or v[0] in "!&*[]{}|>%@`\"'#,?:-"
        or ": " in v
        or v.endswith(":")
        or " #" in v
        or v.lower() in _YAML_BOOL
        or v.lower() in _YAML_NULL
        or bool(_NUM_RE.match(v))
        or bool(_DATE_RE.match(v))
    )
    if needs:
        return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return v


def build_block(path: Path, owner: str, project: str) -> str:
    text = path.read_text(encoding="utf-8")
    stem = path.stem
    created, updated = git_dates(path)
    title = derive_title(text, stem)
    return (
        "---\n"
        f"title: {yaml_scalar(title)}\n"
        f"slug: {stem}\n"
        "type: reference\n"
        "status: live\n"
        f"created: {created}\n"
        f"updated: {updated}\n"
        f"owner: {owner}\n"
        "scope: project\n"
        f"project: {project}\n"
        "canonical: true\n"
        "---\n\n"
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("paths", nargs="+", type=Path)
    ap.add_argument(
        "--apply", action="store_true", help="write in place (default: dry-run)"
    )
    ap.add_argument(
        "--project",
        default=_default_project(),
        help="project: frontmatter value (default: repo basename)",
    )
    ap.add_argument("--owner", default=OWNER, help="owner: frontmatter value")
    args = ap.parse_args()
    # Enforce the lowercase-kebab project-slug contract on an explicit --project too
    # (e.g. `--project Qurrhea` -> `qurrhea`), so the field is always a valid slug.
    args.project = _slugify(args.project)

    skipped, written, proposed = [], [], []
    for p in args.paths:
        if not p.is_file():
            print(f"skip (not a file): {p}", file=sys.stderr)
            continue
        text = p.read_text(encoding="utf-8")
        if has_frontmatter(text):
            skipped.append(p)
            continue
        block = build_block(p, args.owner, args.project)
        if args.apply:
            p.write_text(block + text, encoding="utf-8")
            written.append(p)
        else:
            proposed.append((p, block))

    if proposed:
        for p, block in proposed:
            print(f"# === {p} ===")
            print(block, end="")
    print(
        f"\n{'APPLIED' if args.apply else 'DRY-RUN'}: "
        f"{len(written) if args.apply else len(proposed)} to write, "
        f"{len(skipped)} skipped (already have frontmatter).",
        file=sys.stderr,
    )
    if skipped:
        print("skipped: " + ", ".join(p.name for p in skipped), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
