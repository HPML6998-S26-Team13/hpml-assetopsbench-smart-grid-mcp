#!/usr/bin/env python3
"""Reproducible verification gates for the KB Phase 3 reference-docs migration.

Run from the repo root or any worktree of it:

    python3 scripts/verify_kb_migration.py

Exits non-zero if any gate fails. Each gate is worktree-aware (absolute links
under the canonical repo path are resolved against the current checkout, so the
gates reproduce identically from a feature worktree and from root post-merge),
migrated-leaf-aware (a bare reference is only a failure when a dated version of
that exact doc exists — future/illustrative paths are not migrated docs), and
ignores code-fenced / placeholder examples that never resolved.

Gates:
  1. date-prefix      every non-sink docs/knowledge-base/reference/** file has a
                      YYYY-MM-DD_ leaf equal to its `created:`.
  2. relative-link    every relative INTRA-repo link inside the moved tree
                      resolves, INCLUDING bare same-dir `](sibling.md)` links (the
                      rename retires the bare sibling name); repo-escaping
                      (cross-repo) relative links are skipped (not locally
                      verifiable).
  3. no-bare          no live link to a *migrated* doc keeps a bare (undated) leaf.
  4. external-resolve  every live INLINE Markdown link `](...)` and frontmatter
                      sources:/related: path into the reference tree resolves on
                      disk; repo-escaping (cross-repo) relative links are skipped
                      (not locally verifiable from a worktree), mirroring gate 2.
                      Reference-style link definitions/usages and bare heading
                      anchors are NOT validated (none present in migrated docs).
  5. live-path         a surviving docs/reference/<X> FAILS when X is a this-repo
                      migrated leaf (a real stale nav link to repoint), OR when the
                      file is a live operational PM surface (governance idea-scrape
                      source, tag-manifest scope, initiative-registry cross-ref) —
                      any docs/reference/ survivor there is stale, even a bare dir
                      or glob with no migrated-leaf basename. Historical record
                      (pm/reports, docs/archive), generic migration descriptions,
                      and cross-repo paths are allowed survivors (not failed).
  6. cross-repo-migrated  a live ref to <sibling>/docs/reference/<leaf> FAILS when
                      that sibling repo has itself migrated (its docs/reference/ is
                      gone and it has a docs/knowledge-base/reference/). Resolved
                      against the sibling's real canonical location under the coding
                      parent, so a pointer to a sibling's retired reference doc
                      cannot silently pass as a cross-repo survivor of gates 2/4/5.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys


def _canon_root() -> str:
    """Canonical repo root — correct from the root checkout OR a linked worktree.
    git-common-dir points at the main repo's .git; its parent is the repo root
    (show-toplevel would give the worktree dir, which breaks absolute-link remap
    and cross-repo classification)."""
    common = subprocess.run(
        ["git", "rev-parse", "--git-common-dir"], text=True, capture_output=True
    ).stdout.strip()
    return os.path.dirname(os.path.abspath(common))


CANON = _canon_root()  # canonical repo root (NOT the worktree checkout)
REPO = os.path.basename(CANON)  # repo identity for cross-repo classification
_CODING = os.path.dirname(CANON)  # parent dir holding sibling repos
REF = "docs/knowledge-base/reference"
SINKS = {"_index.md", "lessons.md", "open-questions.md", "knowledge-base-convention.md"}
# Generic surfaces excluded from the migrated-link gates (historical record, the
# convention meta-doc's pedagogical examples). Per-migration plan/spec docs are
# excluded via --migration-doc; docs/archive (where old migration plans land) is
# already covered here. --no-bare-exclude adds bare-leaf carve-outs (future docs).
# pm/reports holds dated, point-in-time PM snapshots: at generation time the path
# WAS docs/reference/, so rewriting them would falsify the historical record —
# frozen like docs/archive/retrospectives/incidents.
EXCL_BASE = [
    ":(exclude)CHANGELOG.md",
    ":(exclude)docs/archive",
    ":(exclude)docs/retrospectives",
    ":(exclude)docs/incidents",
    ":(exclude)docs/research",
    ":(exclude)planning/archive",
    ":(exclude)pm/done.md",
    ":(exclude)pm/reports",
    f":(exclude){REF}/knowledge-base-convention.md",
]
# Live operational PM surfaces: the taxonomy registry (project-taxonomy.yaml
# `reference_docs:` lists + ontology_doc/operating_model keys) DRIVES tooling at
# the reference tree. A surviving bare `docs/reference/` mention here is stale
# operational state even with no migrated leaf basename, so the generic-survivor
# bucket must NOT absolve it — any docs/reference/ mention here is a hard
# live-path failure.
LIVE_PM_SURFACES = ("docs/governance/project-taxonomy.yaml",)
REF_RE = r"[~./A-Za-z0-9_-]*knowledge-base/reference/[A-Za-z0-9_./-]+\.md"


def sh(*args: str) -> str:
    return subprocess.run(list(args), text=True, capture_output=True).stdout


def root() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"], text=True
    ).strip()


def remap(wt: str, p: str) -> str:
    """Absolute links under the canonical repo path resolve against this checkout."""
    if p.startswith(CANON + "/") and not p.startswith(CANON + "/.claude"):
        return wt + p[len(CANON) :]
    return p


def migrated_leaves(wt: str) -> set[str]:
    out = set()
    for m in sh("git", "ls-files", REF).split():
        if not m.endswith(".md"):
            continue
        rel = m[len(REF) + 1 :]
        d, b = os.path.dirname(rel), os.path.basename(rel)
        mm = re.match(r"\d{4}-\d{2}-\d{2}_(.+)", b)
        if mm:
            out.add((d + "/" if d else "") + mm.group(1))
    return out


def gate_date_prefix(wt: str) -> list[str]:
    bad = []
    for f in sh("git", "ls-files", REF).splitlines():
        if not f.endswith(".md"):
            continue
        b = os.path.basename(f)
        if b in SINKS:
            continue
        if not re.match(r"\d{4}-\d{2}-\d{2}_", b):
            bad.append(f"UNDATED: {f}")
            continue
        created = ""
        for line in open(os.path.join(wt, f), encoding="utf-8"):
            if line.startswith("created:"):
                created = line.split(":", 1)[1].strip().strip('"')
                break
        if b.split("_", 1)[0] != created:
            bad.append(f"PREFIX!=created({created}): {f}")
    return bad


def gate_relative_link(wt: str) -> list[str]:
    bad = []
    out = sh("git", "grep", "-noIE", r"\]\(\.\.?/[^)]+\)", "--", REF)
    for ln in out.splitlines():
        f, _, link = ln.split(":", 2)
        rel = link[2:-1].split("#", 1)[0]
        target = os.path.normpath(os.path.join(wt, os.path.dirname(f), rel))
        rel_to_root = os.path.relpath(target, wt)
        if rel_to_root == os.pardir or rel_to_root.startswith(os.pardir + os.sep):
            # cross-repo / external relative link — not locally verifiable (resolves
            # from the repo root but escapes the checkout from a worktree); skip,
            # consistent with the external gate skipping other-repo absolute paths.
            continue
        if not os.path.exists(target):
            bad.append(f"BROKEN: {f} -> {rel}")
    # Bare same-dir links `](sibling.md)` (no ./ or ../ prefix, no slash) are the
    # gate-invisible relink class: the rename retires the bare sibling name, so an
    # un-rewritten `](ontology.md)` silently breaks. Resolve each in the file's own
    # dir. Skip pure-anchor (`](#sec)`) and any link containing a slash (covered
    # above or external).
    bare = sh("git", "grep", "-noIE", r"\]\([A-Za-z0-9_.-]+\.md[^)]*\)", "--", REF)
    for ln in bare.splitlines():
        f, _, link = ln.split(":", 2)
        rel = link[2:-1].split("#", 1)[0]
        if "/" in rel or not rel:
            continue
        if not os.path.exists(os.path.join(wt, os.path.dirname(f), rel)):
            bad.append(f"BROKEN(same-dir): {f} -> {rel}")
    return bad


def gate_no_bare(wt: str, mig: set[str], excl: list[str]) -> list[str]:
    bad = []
    pat = r"knowledge-base/reference/([A-Za-z0-9_-]+/)*[A-Za-z0-9_-]+\.md"
    for ln in sh("git", "grep", "-nIE", pat, "--", *excl).splitlines():
        m = re.search(
            r"knowledge-base/reference/(([A-Za-z0-9_-]+/)*[A-Za-z0-9_-]+\.md)", ln
        )
        rel = m.group(1)
        if re.match(r"\d{4}-\d{2}-\d{2}_", os.path.basename(rel)):
            continue
        if rel in mig:  # bare ref to a doc that WAS migrated -> forgot the date
            bad.append(ln)
    return bad


def gate_external(wt: str, excl: list[str]) -> list[str]:
    def md_targets(f, l):
        l = os.path.expanduser(l) if l.startswith("~") else l
        if l.startswith("/"):
            return [remap(wt, l)]
        if l.startswith("docs/"):
            return [os.path.join(wt, l)]
        return [os.path.normpath(os.path.join(wt, os.path.dirname(f), l))]

    def yaml_targets(f, l):
        l = os.path.expanduser(l) if l.startswith("~") else l
        if l.startswith("/"):
            return [remap(wt, l)]
        return [
            os.path.normpath(os.path.join(wt, l)),
            os.path.normpath(os.path.join(wt, "docs", l)),
            os.path.normpath(os.path.join(wt, os.path.dirname(f), l)),
        ]

    def verifiable(l):
        l = os.path.expanduser(l) if l.startswith("~") else l
        # Absolute paths under the coding parent (this repo OR a sibling) are real
        # on-disk paths and ARE checkable — a typo in a dated cross-repo KB target
        # then fails existence rather than silently passing. Absolute paths outside
        # the coding parent (e.g. /Users/.../data/models/...) stay unverifiable.
        if l.startswith("/"):
            return l.startswith(_CODING + "/")
        return True

    bad = []
    for kind, pat, cand in (
        ("md", r"\]\(" + REF_RE + r"\)", md_targets),
        ("yaml", r"^[ \t]*-[ \t]+" + REF_RE, yaml_targets),
    ):
        for ln in sh("git", "grep", "-nIoE", pat, "--", *excl).splitlines():
            f, _, m = ln.split(":", 2)
            link = m[2:-1] if kind == "md" else re.sub(r"^[ \t]*-[ \t]+", "", m)
            # repo-escaping (cross-repo) relative links — e.g. a frontmatter pointer
            # to another repo's convention doc (`../../../<other-repo>/...`) — climb
            # above the repo root and are not locally verifiable from a worktree
            # checkout; skip them, mirroring gate_relative_link's repo-escape skip.
            if not link.startswith(("/", "~")):
                tgt = os.path.normpath(os.path.join(wt, os.path.dirname(f), link))
                rel = os.path.relpath(tgt, wt)
                if rel == os.pardir or rel.startswith(os.pardir + os.sep):
                    continue
            # placeholder/illustrative leaves that never resolved (doc.md, X.md, etc.)
            if os.path.basename(link) in {"doc.md", "X.md", "architecture.md"}:
                continue
            if verifiable(link) and not any(os.path.exists(t) for t in cand(f, link)):
                bad.append(f"{kind}: {f} -> {link}")
    return bad


def _frontmatters(wt: str) -> list[tuple[str, str]]:
    out = []
    for f in sh("git", "ls-files", REF).splitlines():
        if not f.endswith(".md"):
            continue
        t = open(os.path.join(wt, f), encoding="utf-8").read()
        if t.startswith("---"):
            out.append((f, t.split("---", 2)[1]))
    return out


def gate_yaml_valid(wt: str) -> list[str]:
    """Every migrated reference doc's frontmatter must parse as REAL YAML (catches
    unquoted `: ` in titles, which the stdlib validator's subset parser accepts).
    Tries PyYAML, then Ruby/Psych. **Fails closed** if neither real parser is
    available — the v1 blocker was the subset parser accepting YAML-invalid
    frontmatter, so an absent real parser must NOT silently pass."""
    fms = _frontmatters(wt)
    # parser 1: PyYAML
    try:
        import yaml  # type: ignore

        bad = []
        for f, fm in fms:
            try:
                yaml.safe_load(fm)
            except yaml.YAMLError:
                bad.append(f"{f}: YAMLError (PyYAML)")
        return bad
    except Exception:
        pass
    # parser 2: Ruby/Psych (present on macOS)
    if subprocess.run(["ruby", "--version"], capture_output=True).returncode == 0:
        bad = []
        ruby = (
            "begin; require 'date'; YAML.safe_load(STDIN.read, permitted_classes: [Date]); "
            "rescue Psych::Exception => e; STDERR.puts e.class; exit 1; end"
        )
        for f, fm in fms:
            r = subprocess.run(
                ["ruby", "-ryaml", "-e", ruby], input=fm, text=True, capture_output=True
            )
            if r.returncode != 0:
                bad.append(f"{f}: {r.stderr.strip() or 'Psych error'}")
        return bad
    return [
        "NO REAL YAML PARSER AVAILABLE (install PyYAML or Ruby) — gate fails closed"
    ]


# Live-path token: optional cross-repo absolute prefix (sibling-repos parent dir +
# repo name), then docs/reference/<rel>.
_LIVE_TOKEN = re.compile(
    rf"(?:{re.escape(_CODING)}/([^/]+)/)?docs/reference/([A-Za-z0-9_./-]*)"
)


def gate_live_path(
    wt: str, mig: set[str], excl: list[str]
) -> tuple[list[str], list[str]]:
    """A surviving `docs/reference/<X>` is a FAILURE iff X is a repo-relative
    (not cross-repo) **migrated leaf** — a real stale nav link to a THIS-repo doc
    that should now be the dated KB path — OR the line lives in a LIVE_PM_SURFACES
    file, where ANY docs/reference/ survivor (even a bare dir or glob with no
    migrated-leaf basename) is stale operational state. Generic descriptions (bare
    `docs/reference/`) in other files, future/illustrative leaves, and cross-repo
    (`<coding-parent>/<other>/docs/reference/...`) paths are allowed (returned as
    info, not failures)."""
    fails, allowed = [], []
    for ln in sh("git", "grep", "-n", "docs/reference/", "--", *excl).splitlines():
        fpath = ln.split(":", 1)[0]
        if fpath in LIVE_PM_SURFACES:
            fails.append(ln)  # live operational surface — any survivor is stale
            continue
        stale = False
        for repo, rel in _LIVE_TOKEN.findall(ln):
            if repo and repo != REPO:
                continue  # cross-repo path to another project's docs/reference/
            if rel.rstrip("./") in mig or rel in mig:
                stale = True
                break
        (fails if stale else allowed).append(ln)
    return fails, allowed


# A live ref to `<repo-seg>/docs/reference/<leaf>` where <repo-seg> resolves to a
# real sibling repo under the coding parent.
_XREPO = re.compile(r"([A-Za-z0-9_.-]+)/docs/reference/([A-Za-z0-9_./-]+\.md)")


def gate_cross_repo_migrated(wt: str, excl: list[str]) -> list[str]:
    """A live ref to `<sibling>/docs/reference/<leaf>` is STALE when that sibling
    repo has itself migrated — its `docs/reference/` is gone and it now has a
    `docs/knowledge-base/reference/`. The local resolution gates (2, 4) skip
    cross-repo links as not-worktree-verifiable, so without this check a pointer
    to a sibling's *retired* reference doc passes as a generic allowed survivor.
    This resolves the sibling against its real canonical location under the
    coding parent (deterministic, not worktree-relative), so a migrated-sibling
    pointer cannot silently rot. Siblings that have NOT migrated (still have
    docs/reference/) are not flagged."""
    fails = []
    for ln in sh(
        "git",
        "grep",
        "-nIoE",
        r"[A-Za-z0-9_.-]+/docs/reference/[A-Za-z0-9_./-]+\.md",
        "--",
        *excl,
    ).splitlines():
        f, _, m = ln.split(":", 2)
        mm = _XREPO.search(m)
        if not mm:
            continue
        repo, leaf = mm.group(1), mm.group(2)
        if repo == REPO:
            continue  # same-repo handled by gate-5 / no-bare
        sib = os.path.join(_CODING, repo)
        if not os.path.isdir(sib):
            continue  # path segment is not a real sibling repo
        old = os.path.join(sib, "docs", "reference", leaf)
        kb = os.path.join(sib, "docs", "knowledge-base", "reference")
        if not os.path.exists(old) and os.path.isdir(kb):
            fails.append(f"{f}: {repo}/docs/reference/{leaf} (sibling migrated to KB)")
    return fails


_REF_LINK = re.compile(r"\]\(([^)]*reference/[A-Za-z0-9_./-]+\.md)(?:#[^)]*)?\)")


def gate_live_reference_links(wt: str, excl: list[str]) -> list[str]:
    """Every live Markdown link whose target contains a `reference/<...>.md` segment
    must resolve from its SOURCE file. Closes the migration blind spot where a doc
    OUTSIDE the moved tree still links to a retired `docs/reference` leaf via a bare
    (`reference/x.md`) or relative (`../docs/reference/x.md`) path: gate 2 only scans
    inside the moved tree, and the live-path gate only greps literal `docs/reference/`
    survivors, so a bare `reference/x.md` link silently rots. External (http/absolute)
    and repo-escaping (cross-repo) links are skipped; frozen surfaces are excluded."""
    bad = []
    for ln in sh(
        "git",
        "grep",
        "-nIoE",
        r"\]\([^)]*reference/[A-Za-z0-9_./-]+\.md[^)]*\)",
        "--",
        *excl,
    ).splitlines():
        f, _, m = ln.split(":", 2)
        mm = _REF_LINK.search(m)
        if not mm:
            continue
        link = mm.group(1)
        if link.startswith(("http://", "https://", "/", "~", "mailto:")):
            continue
        tgt = os.path.normpath(os.path.join(wt, os.path.dirname(f), link))
        rel = os.path.relpath(tgt, wt)
        if rel == os.pardir or rel.startswith(os.pardir + os.sep):
            continue  # cross-repo / repo-escaping — not locally verifiable
        if not os.path.exists(tgt):
            bad.append(f"{f}: {link}")
    return bad


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--migration-doc",
        action="append",
        default=[],
        metavar="PATHSPEC",
        help="Migration plan/spec path(s) whose example tokens must not be scanned "
        "by the migrated-link gates. Repeatable; git-pathspec globs.",
    )
    ap.add_argument(
        "--no-bare-exclude",
        action="append",
        default=[],
        metavar="PATH",
        help="Extra path(s) excluded from the no-bare gate (files naming a "
        "not-yet-created, intentionally undated doc). Repeatable.",
    )
    args = ap.parse_args()

    wt = root()
    os.chdir(wt)
    mig = migrated_leaves(wt)
    mig_excl = [f":(exclude){g}" for g in args.migration_doc]
    excl = EXCL_BASE + mig_excl
    no_bare_excl = excl + [f":(exclude){p}" for p in args.no_bare_exclude]
    fails = 0

    for name, hits in (
        ("date-prefix", gate_date_prefix(wt)),
        ("relative-link", gate_relative_link(wt)),
        ("no-bare (migrated-leaf-aware)", gate_no_bare(wt, mig, no_bare_excl)),
        ("external-resolution (worktree-aware)", gate_external(wt, excl)),
        (
            "cross-repo-migrated (sibling retired docs/reference)",
            gate_cross_repo_migrated(wt, excl),
        ),
        (
            "live-reference-links (resolve outside the moved tree)",
            gate_live_reference_links(wt, excl),
        ),
        ("yaml-valid (real YAML parse)", gate_yaml_valid(wt)),
    ):
        if hits:
            fails += 1
            print(f"FAIL {name} ({len(hits)}):")
            for h in hits:
                print("   ", h)
        else:
            print(f"PASS {name}")

    lp_fails, lp_allowed = gate_live_path(wt, mig, excl)
    if lp_fails:
        fails += 1
        print(f"FAIL live-path (stale nav link to a migrated doc) ({len(lp_fails)}):")
        for h in lp_fails:
            print("   ", h)
    else:
        print("PASS live-path (no stale migrated-doc nav links)")
    print(
        f"INFO live-path allowed survivors ({len(lp_allowed)}): "
        "historical record / generic migration description / cross-repo path"
    )
    for h in lp_allowed:
        print("   ", h)

    print(f"\n{'OK — all gates pass' if not fails else f'{fails} gate(s) FAILED'}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
