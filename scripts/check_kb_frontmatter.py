#!/usr/bin/env python3
"""Validate knowledge-base and retro/incident frontmatter without PyYAML.

The KB convention at docs/knowledge-base/reference/knowledge-base-convention.md
defines a structured frontmatter schema for KB entries, retrospectives, and
incident reports. This checker enforces that schema so deploy/pre-push catches
schema drift before content lands.

Scope:
- docs/knowledge-base/{reference,decisions,learnings,qa}/**/*.md
- docs/retrospectives/*.md
- docs/incidents/*.md

Rules implemented (per convention § Validator):
1. Required fields: title, slug, type, status, created, updated, owner, scope.
2. type ∈ {reference, decision, learning, qa, retrospective, incident}.
3. status ∈ {draft, live, canonical, superseded, archived}.
4. slug matches filename topic portion (after date prefix, before .md).
   Exceptions: decisions/<domain>.md, _index.md, lessons.md, open-questions.md
   use bare filename without date prefix.
5. created is a valid ISO date; created <= updated.
6. scope=project requires project field; scope=global forbids project field.
7. tags are lowercase kebab-case (warn-only on unregistered tags).
8. project-sources, when present, is a list of lowercase-kebab project slugs.
9. At most one canonical:true per (project, topic, type) tuple.
10. For decisions/* files: metadata.high_water_mark is an int matching the
    highest DEC-<DOM>-<N> heading in the file.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

# Files to scan by default. Relative to repo root.
DEFAULT_GLOBS = (
    "docs/knowledge-base/*.md",  # root-level sink files (e.g., _index.md)
    "docs/knowledge-base/reference/**/*.md",
    "docs/knowledge-base/decisions/**/*.md",
    "docs/knowledge-base/learnings/**/*.md",
    "docs/knowledge-base/qa/**/*.md",
    "docs/retrospectives/*.md",
    "docs/incidents/*.md",
)

# Schema vocab.
VALID_TYPES = {"reference", "decision", "learning", "qa", "retrospective", "incident"}
VALID_STATUSES = {"draft", "live", "canonical", "superseded", "archived"}
VALID_SCOPES = {"task", "project", "initiative", "global"}
REQUIRED_FIELDS = (
    "title",
    "slug",
    "type",
    "status",
    "created",
    "updated",
    "owner",
    "scope",
)

# Sink filenames that do NOT need a date prefix.
SINK_FILENAMES = {
    "_index.md",
    "lessons.md",
    "open-questions.md",
    "knowledge-base-convention.md",  # the convention itself (meta-doc)
}

# Files in decisions/ also skip the date-prefix rule (one-file-per-domain).
DECISIONS_DIR_PARTS = ("knowledge-base", "decisions")

KEY_RE = re.compile(r"^([A-Za-z0-9_-]+):(?:[ \t]*(.*))?$")
DATE_PREFIX_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})_(.+)\.md$")
ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
KEBAB_TAG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
PROJECT_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DEC_HEADING_RE = re.compile(r"^##\s+\[DEC-([A-Z]{3})-(\d+)\]")
FRONTMATTER_MARKER_RE = re.compile(r"^(?:---|\.\.\.)[ \t]*\r?$")


@dataclass
class ValidationError:
    path: Path
    line: int
    message: str
    is_warning: bool = False

    def render(self, root: Path) -> str:
        try:
            rel = self.path.relative_to(root)
        except ValueError:
            rel = self.path
        prefix = "warning" if self.is_warning else "error"
        return f"{rel}:{self.line}: {prefix}: {self.message}"


@dataclass
class ParsedFile:
    path: Path
    data: dict[str, Any] = field(default_factory=dict)
    body_lines: list[str] = field(default_factory=list)
    errors: list[ValidationError] = field(default_factory=list)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="Repository root")
    parser.add_argument(
        "--strict-tags",
        action="store_true",
        help="Promote unregistered-tag warnings to errors",
    )
    parser.add_argument(
        "--signatures",
        action="store_true",
        help=(
            "Emit one line-number-stripped '<rel>\\t<message>' signature per hard-"
            "error OCCURRENCE (duplicate-preserving, deterministically sorted) to "
            "stdout, then exit 0 even when errors exist (only internal failures exit "
            "non-zero). Stable key for the no-regression occurrence diff."
        ),
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help=(
            "Optional paths (files OR directories — a directory expands to its "
            "*.md). Defaults to KB + retros + incidents under --root."
        ),
    )
    return parser.parse_args(argv)


def coerce_scalar(value: str) -> Any:
    """Coerce a YAML-ish scalar to a Python value.

    Handles quoted strings, inline lists, and booleans. Anything else stays
    a string.
    """
    value = value.strip()
    if not value:
        return ""
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [part.strip().strip('"').strip("'") for part in inner.split(",")]
    if value.lower() in ("true", "yes"):
        return True
    if value.lower() in ("false", "no"):
        return False
    try:
        return int(value)
    except ValueError:
        pass
    return value


def _real_yaml_error(text: str) -> str | None:
    """Validate frontmatter against a REAL YAML parser. The subset parser below
    accepts YAML-invalid scalars such as `title: Foo: Bar`, so a real parser is
    needed to fail-close on them. Tries PyYAML, then Ruby/Psych; returns an error
    string when NO real parser is available, since a silently-absent parser would
    let invalid frontmatter pass (the exact failure this guard exists to prevent).
    Returns None when the text is valid YAML."""
    try:
        import yaml  # type: ignore

        try:
            yaml.safe_load(text)
            return None
        except yaml.YAMLError as e:  # pragma: no cover - message varies
            return f"invalid YAML (PyYAML): {str(e).splitlines()[0]}"
    except ImportError:
        pass
    import shutil
    import subprocess

    if shutil.which("ruby"):
        # Permit Date so unquoted ISO dates (created:/updated:) parse, while
        # genuine structure errors (e.g. `title: Foo: Bar`) still raise a
        # Psych::Exception. Mirrors verify_kb_migration.py's yaml-valid gate.
        ruby = (
            "begin; require 'date'; "
            "YAML.safe_load(STDIN.read, permitted_classes: [Date]); "
            "rescue Psych::Exception => e; STDERR.puts e.class; exit 1; end"
        )
        p = subprocess.run(
            ["ruby", "-ryaml", "-e", ruby],
            input=text,
            text=True,
            capture_output=True,
        )
        if p.returncode != 0:
            first = (p.stderr or "Psych error").strip().splitlines()[0] or "Psych error"
            return f"invalid YAML (Ruby/Psych): {first}"
        return None
    return "no real YAML parser available (PyYAML/Ruby) — failing closed"


def parse_frontmatter(
    path: Path, lines: list[str], offset: int
) -> tuple[dict[str, Any], list[ValidationError]]:
    """Parse a small YAML-like frontmatter subset.

    Supports:
    - top-level scalars
    - top-level mappings (one level deep)
    - block lists under a top-level or nested key
    - inline lists ([a, b, c])
    """
    data: dict[str, Any] = {}
    errors: list[ValidationError] = []
    current_parent: str | None = None
    current_list_key: tuple[str | None, str] | None = None

    for index, raw_line in enumerate(lines, start=offset):
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if raw_line.startswith("\t"):
            errors.append(ValidationError(path, index, "tabs are not allowed"))
            continue

        # Indented line
        if raw_line.startswith(" "):
            # List item under current list key
            if current_list_key is not None and stripped.startswith("- "):
                parent, key = current_list_key
                item = stripped[2:].strip()
                if parent:
                    target = data[parent][key]
                    if not isinstance(target, list):
                        # Promote the placeholder dict to a list on first
                        # block-list item (nested case).
                        data[parent][key] = []
                        target = data[parent][key]
                else:
                    target = data[key]
                    if not isinstance(target, list):
                        # Promote the placeholder dict to a list on first
                        # block-list item (top-level case).
                        data[key] = []
                        target = data[key]
                target.append(coerce_scalar(item))
                continue

            # Nested key under current parent
            if current_parent is None or not isinstance(data.get(current_parent), dict):
                errors.append(
                    ValidationError(path, index, "indented field has no mapping parent")
                )
                continue
            nested = raw_line.strip()
            match = KEY_RE.match(nested)
            if not match:
                errors.append(ValidationError(path, index, "malformed nested field"))
                continue
            key, value = match.groups()
            value = value or ""
            if value.strip():
                data[current_parent][key] = coerce_scalar(value)
                current_list_key = None
            else:
                data[current_parent][key] = []
                current_list_key = (current_parent, key)
            continue

        # Top-level line
        match = KEY_RE.match(raw_line)
        if not match:
            errors.append(ValidationError(path, index, "malformed top-level field"))
            current_parent = None
            current_list_key = None
            continue

        key, value = match.groups()
        value = value or ""
        if value.strip():
            data[key] = coerce_scalar(value)
            current_parent = None
            current_list_key = None
        else:
            # Empty value: could be a mapping parent or a list parent.
            # We don't know yet — wait for the next line. Default to dict; if
            # the next non-empty line is `- foo`, we'll convert to list.
            data[key] = {}
            current_parent = key
            current_list_key = (None, key)

    # Convert any empty-dict parents that ended up as lists (via the
    # current_list_key mechanism) into actual lists.
    for k, v in list(data.items()):
        if v == {} and current_list_key == (None, k):
            data[k] = []
    # Fail-closed real-YAML check: the subset parser above accepts some
    # YAML-invalid scalars (e.g. unquoted `: ` in a title); a real parser rejects
    # them. Run it on the raw frontmatter so direct/--signatures invocations can't
    # green-light invalid frontmatter.
    yerr = _real_yaml_error("\n".join(lines))
    if yerr:
        errors.append(ValidationError(path, offset, yerr))
    return data, errors


def extract_frontmatter(
    path: Path, text: str
) -> tuple[list[str], list[str], list[ValidationError]]:
    """Split file into frontmatter lines + body lines.

    Returns (frontmatter_lines, body_lines, errors).
    """
    if text.startswith("﻿"):
        text = text[1:]
    lines = text.splitlines()
    if not lines or not re.match(r"^---[ \t]*\r?$", lines[0]):
        return (
            [],
            lines,
            [ValidationError(path, 1, "missing opening frontmatter fence")],
        )
    closing: int | None = None
    for index, line in enumerate(lines[1:], start=2):
        if FRONTMATTER_MARKER_RE.match(line):
            closing = index
            break
    if closing is None:
        return [], [], [ValidationError(path, 1, "missing closing frontmatter fence")]
    frontmatter = lines[1 : closing - 1]
    body = lines[closing:]
    return frontmatter, body, []


def parse_file(path: Path) -> ParsedFile:
    text = path.read_text(encoding="utf-8")
    parsed = ParsedFile(path=path)
    frontmatter_lines, body_lines, fm_errors = extract_frontmatter(path, text)
    parsed.errors.extend(fm_errors)
    parsed.body_lines = body_lines
    if not frontmatter_lines:
        return parsed
    data, parse_errors = parse_frontmatter(path, frontmatter_lines, 2)
    parsed.data = data
    parsed.errors.extend(parse_errors)
    return parsed


# ----- Schema validation rules -----


def topic_slug_from_filename(filename: str) -> tuple[str | None, str]:
    """Return (date_prefix_or_None, topic_slug) from a filename.

    For `2026-05-20_foo.md` returns (`2026-05-20`, `foo`).
    For `foundation.md` returns (None, `foundation`).
    """
    match = DATE_PREFIX_RE.match(filename)
    if match:
        return match.group(1), match.group(2)
    return None, filename.rsplit(".", 1)[0]


def is_sink_file(path: Path) -> bool:
    return path.name in SINK_FILENAMES


def is_decisions_file(path: Path, root: Path) -> bool:
    try:
        rel = path.relative_to(root)
    except ValueError:
        return False
    parts = rel.parts
    # Match e.g. docs/knowledge-base/decisions/foundation.md
    return any(parts[i : i + 2] == DECISIONS_DIR_PARTS for i in range(len(parts) - 1))


def validate_schema(
    parsed: ParsedFile, root: Path, known_tags: set[str], strict_tags: bool
) -> None:
    path = parsed.path
    data = parsed.data
    if not data:
        return

    # 1. Required fields.
    for key in REQUIRED_FIELDS:
        if key not in data or data[key] in (None, "", {}, []):
            parsed.errors.append(
                ValidationError(path, 2, f"missing required field `{key}`")
            )

    # 2. type vocabulary.
    type_value = str(data.get("type") or "")
    if type_value and type_value not in VALID_TYPES:
        parsed.errors.append(
            ValidationError(
                path,
                2,
                f"`type: {type_value}` not in vocabulary {sorted(VALID_TYPES)}",
            )
        )

    # 3. status vocabulary.
    status_value = str(data.get("status") or "")
    if status_value and status_value not in VALID_STATUSES:
        parsed.errors.append(
            ValidationError(
                path,
                2,
                f"`status: {status_value}` not in vocabulary {sorted(VALID_STATUSES)}",
            )
        )

    # 4. slug matches filename topic portion.
    slug_value = str(data.get("slug") or "")
    date_prefix, topic_from_filename = topic_slug_from_filename(path.name)
    if slug_value:
        if is_sink_file(path) or is_decisions_file(path, root):
            # Sink files and decisions/<domain>.md: slug should match bare
            # filename stem (no date prefix expected).
            expected = path.stem
            if slug_value != expected:
                parsed.errors.append(
                    ValidationError(
                        path,
                        2,
                        f"`slug: {slug_value}` does not match filename stem `{expected}`",
                    )
                )
        else:
            if slug_value != topic_from_filename:
                parsed.errors.append(
                    ValidationError(
                        path,
                        2,
                        f"`slug: {slug_value}` does not match filename topic `{topic_from_filename}`",
                    )
                )
            # Also enforce that non-exception files have a date prefix.
            if date_prefix is None:
                parsed.errors.append(
                    ValidationError(
                        path,
                        1,
                        f"file `{path.name}` missing required date prefix (YYYY-MM-DD_)",
                    )
                )

    # 5. Date sanity. created valid ISO; created <= updated.
    created_value = str(data.get("created") or "")
    updated_value = str(data.get("updated") or "")
    created_date: date | None = None
    updated_date: date | None = None
    if created_value:
        if not ISO_DATE_RE.match(created_value):
            parsed.errors.append(
                ValidationError(
                    path, 2, f"`created: {created_value}` is not a valid ISO date"
                )
            )
        else:
            try:
                created_date = date.fromisoformat(created_value)
            except ValueError:
                parsed.errors.append(
                    ValidationError(
                        path,
                        2,
                        f"`created: {created_value}` is not a valid calendar date",
                    )
                )
    if updated_value:
        if not ISO_DATE_RE.match(updated_value):
            parsed.errors.append(
                ValidationError(
                    path, 2, f"`updated: {updated_value}` is not a valid ISO date"
                )
            )
        else:
            try:
                updated_date = date.fromisoformat(updated_value)
            except ValueError:
                parsed.errors.append(
                    ValidationError(
                        path,
                        2,
                        f"`updated: {updated_value}` is not a valid calendar date",
                    )
                )
    if created_date and updated_date and created_date > updated_date:
        parsed.errors.append(
            ValidationError(
                path,
                2,
                f"`created` ({created_value}) is after `updated` ({updated_value})",
            )
        )

    # 6. scope/project invariant.
    scope_value = str(data.get("scope") or "")
    project_value = data.get("project")
    if scope_value and scope_value not in VALID_SCOPES:
        parsed.errors.append(
            ValidationError(
                path,
                2,
                f"`scope: {scope_value}` not in vocabulary {sorted(VALID_SCOPES)}",
            )
        )
    if scope_value == "project" and not project_value:
        parsed.errors.append(
            ValidationError(path, 2, "`scope: project` requires a `project` field")
        )
    if scope_value == "global" and project_value:
        parsed.errors.append(
            ValidationError(
                path,
                2,
                "`scope: global` forbids the `project` field (got "
                f"`project: {project_value}`)",
            )
        )
    # 6b. project, when present, must be a lowercase-kebab slug — same contract as
    # project-sources. An uppercase/mixed-case value (e.g. `Qurrhea`) silently keys
    # the doc into a different project bucket than the rest of the KB, breaking
    # grouping, parent-KB rollups, and the canonical (project, slug, type) check.
    if project_value and not PROJECT_SLUG_RE.match(str(project_value)):
        parsed.errors.append(
            ValidationError(
                path,
                2,
                f"`project: {project_value}` is not a lowercase-kebab slug "
                "(e.g. `qurrhea`, `gcp-spot-runner`)",
            )
        )

    # 7. tags kebab-case + warn-only on unregistered.
    tags = data.get("tags")
    if isinstance(tags, list):
        for tag in tags:
            tag_str = str(tag)
            if not KEBAB_TAG_RE.match(tag_str):
                parsed.errors.append(
                    ValidationError(
                        path,
                        2,
                        f"tag `{tag_str}` is not lowercase kebab-case",
                    )
                )
                continue
            if known_tags and tag_str not in known_tags:
                parsed.errors.append(
                    ValidationError(
                        path,
                        2,
                        f"tag `{tag_str}` not registered in convention § Tag vocabulary",
                        is_warning=not strict_tags,
                    )
                )

    # 8. project-sources, when present, is a list of lowercase-kebab project
    #    slugs (parent-KB provenance; see convention § Parent and child KBs).
    if "project-sources" in data:
        project_sources = data.get("project-sources")
        if not isinstance(project_sources, list):
            parsed.errors.append(
                ValidationError(
                    path,
                    2,
                    "`project-sources` must be a list of project slugs "
                    f"(got {type(project_sources).__name__})",
                )
            )
        else:
            for source in project_sources:
                source_str = str(source)
                if not PROJECT_SLUG_RE.match(source_str):
                    parsed.errors.append(
                        ValidationError(
                            path,
                            2,
                            f"`project-sources` entry `{source_str}` is not a "
                            "lowercase kebab-case project slug",
                        )
                    )

    # 10. decisions/<domain>.md: high_water_mark check.
    if is_decisions_file(path, root):
        metadata = data.get("metadata")
        if not isinstance(metadata, dict):
            parsed.errors.append(
                ValidationError(
                    path,
                    2,
                    "decisions file missing `metadata.high_water_mark`",
                )
            )
        else:
            hwm = metadata.get("high_water_mark")
            if not isinstance(hwm, int):
                parsed.errors.append(
                    ValidationError(
                        path,
                        2,
                        f"`metadata.high_water_mark` must be int (got {type(hwm).__name__}: {hwm!r})",
                    )
                )
            else:
                # Scan body for highest DEC heading; compare.
                max_n = 0
                for body_line in parsed.body_lines:
                    m = DEC_HEADING_RE.match(body_line)
                    if m:
                        n = int(m.group(2))
                        if n > max_n:
                            max_n = n
                if max_n != hwm:
                    parsed.errors.append(
                        ValidationError(
                            path,
                            2,
                            f"`metadata.high_water_mark` is {hwm} but highest DEC heading is {max_n}",
                        )
                    )


def validate_canonical_uniqueness(
    files: list[ParsedFile],
) -> list[ValidationError]:
    """Rule 9: at most one canonical:true per (project, topic, type) tuple."""
    errors: list[ValidationError] = []
    by_key: dict[tuple[str, str, str], Path] = {}
    for parsed in files:
        data = parsed.data
        if not data:
            continue
        if not data.get("canonical"):
            continue
        slug = str(data.get("slug") or "")
        type_val = str(data.get("type") or "")
        project = str(data.get("project") or "")  # empty for scope=global
        key = (project, slug, type_val)
        existing = by_key.get(key)
        if existing is not None:
            errors.append(
                ValidationError(
                    parsed.path,
                    2,
                    f"duplicate `canonical: true` for (project={project!r}, "
                    f"topic={slug!r}, type={type_val!r}); also set in {existing}",
                )
            )
        else:
            by_key[key] = parsed.path
    return errors


# ----- Tag vocabulary discovery -----


def load_known_tags(root: Path) -> set[str]:
    """Read the convention doc and extract the registered tag vocabulary.

    Scans the `## Registered tags` subsection of the convention doc for
    backtick-wrapped kebab-case tokens. Those tags are the "registered"
    set; any tag not in this set produces a warn-only error (kebab-case
    enforcement still runs independently). `--strict-tags` promotes the
    warnings to hard errors.

    The check is opt-in: the convention doc must explicitly add a
    `## Registered tags` subsection (or H3 `### Registered tags` inside
    `## Tag vocabulary`) before the warning fires. Until that section
    exists, the registered-tag check is dormant by design — the
    `## Tag vocabulary` prose contains illustrative backticks
    (`agents`, `mcp`, etc.) that are examples, not a closed list, so
    they should not gate warnings. Returns empty set when no registered
    list is found, which disables the registered-tag warning entirely.
    """
    convention = (
        root / "docs" / "knowledge-base" / "reference" / "knowledge-base-convention.md"
    )
    if not convention.exists():
        return set()
    text = convention.read_text(encoding="utf-8")
    # Match either `## Registered tags` or `### Registered tags` headers;
    # stop at the next heading of equal or shallower depth (or EOF).
    section_re = re.compile(
        r"^(#{2,3}) Registered tags\s*$(.*?)(?=^#{1,3} |\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = section_re.search(text)
    if not match:
        return set()
    section = match.group(2)
    return {token for token in re.findall(r"`([a-z0-9]+(?:-[a-z0-9]+)*)`", section)}


# ----- Default path discovery -----


def default_paths(root: Path) -> list[Path]:
    paths: set[Path] = set()
    for pattern in DEFAULT_GLOBS:
        for match in root.glob(pattern):
            if match.is_file() and match.suffix == ".md":
                paths.add(match.resolve())
    return sorted(paths)


# ----- Main -----


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    root = args.root.resolve()
    if args.paths:
        paths = []
        for p in args.paths:
            rp = p.resolve()
            if rp.is_dir():
                paths.extend(
                    sorted(f.resolve() for f in rp.rglob("*.md") if f.is_file())
                )
            else:
                paths.append(rp)
    else:
        paths = default_paths(root)

    if not paths:
        print("check_kb_frontmatter: no KB or retro/incident files found")
        return 0

    known_tags = load_known_tags(root)
    parsed_files: list[ParsedFile] = []
    for path in paths:
        parsed = parse_file(path)
        validate_schema(parsed, root, known_tags, args.strict_tags)
        parsed_files.append(parsed)

    # Cross-file rule.
    canonical_errors = validate_canonical_uniqueness(parsed_files)

    all_errors: list[ValidationError] = []
    for parsed in parsed_files:
        all_errors.extend(parsed.errors)
    all_errors.extend(canonical_errors)

    if args.signatures:
        # Occurrence-preserving (no dedup), line-number-stripped, deterministically
        # sorted signatures of hard errors. Exit 0 even for a red repo — only an
        # uncaught internal failure exits non-zero. This is the stable key for the
        # no-regression occurrence diff (see kb-phase3 migration § 8).
        occurrences: list[str] = []
        for e in all_errors:
            if e.is_warning:
                continue
            try:
                rel = e.path.relative_to(root)
            except ValueError:
                rel = e.path
            occurrences.append(f"{rel}\t{e.message}")
        for line in sorted(occurrences):
            print(line)
        return 0

    hard_errors = [e for e in all_errors if not e.is_warning]
    warnings = [e for e in all_errors if e.is_warning]

    for error in all_errors:
        print(error.render(root), file=sys.stderr)

    n = len(paths)
    if hard_errors:
        print(
            f"check_kb_frontmatter: {len(hard_errors)} error(s), "
            f"{len(warnings)} warning(s) across {n} file(s)",
            file=sys.stderr,
        )
        return 1
    print(
        f"check_kb_frontmatter: validated {n} file(s) " f"({len(warnings)} warning(s))"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
