#!/usr/bin/env python3
"""Read-only audit of backticked cross-skill references in a SKILL.md."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

NAME_RE = re.compile(r"^[a-z0-9-]+$")
HYPHEN_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)+$")
EXTERNAL_RE = re.compile(r"^[a-z0-9-]+:[a-z0-9:-]+$")
UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
)
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SPAN_RE = re.compile(r"`([^`\n]+)`")
FENCE_RE = re.compile(r"^\s*```")

# Common hyphenated command tokens; these are candidates by shape but not skills.
COMMAND_TOKENS = {
    "ls-remote",
    "ls-tree",
    "ls-files",
    "rev-parse",
    "hash-object",
    "show-ref",
    "show-toplevel",
    "show-branch",
    "merge-base",
    "is-ancestor",
    "rev-list",
    "symbolic-ref",
    "for-each-ref",
    "cat-file",
    "update-ref",
    "commit-tree",
    "read-tree",
    "write-tree",
    "check-ignore",
    "check-attr",
    "check-ref-format",
    "sparse-checkout",
    "fast-export",
    "fast-import",
    "filter-branch",
    "cherry-pick",
    "name-rev",
    "pack-refs",
    "prune-packed",
    "unpack-objects",
    "verify-pack",
    "count-objects",
    "update-server-info",
    "send-email",
    "request-pull",
    "format-patch",
    "multi-pack-index",
    "commit-graph",
    "diff-tree",
    "diff-index",
    "diff-files",
    "update-index",
    "merge-file",
    "merge-tree",
    "credential-cache",
    "credential-store",
    "credential-wincred",
    "pack-objects",
    "index-pack",
}

STATUS_ORDER = (
    "LIVE",
    "SHADOWED",
    "BUILTIN",
    "MISSING",
    "BROKEN",
    "EXTERNAL",
    "FENCED",
    "SELF",
    "NON_SKILL",
    "CANDIDATE",
    "IGNORED",
)


def ascii_text(value: object) -> str:
    return str(value).encode("ascii", "backslashreplace").decode("ascii")


def collect_spans(text: str) -> tuple[list[tuple[int, str, bool]], bool]:
    spans: list[tuple[int, str, bool]] = []
    in_fence = False
    for lineno, line in enumerate(text.splitlines(), 1):
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        for match in SPAN_RE.finditer(line):
            name = match.group(1).strip()
            if name:
                spans.append((lineno, name, in_fence))
    return spans, in_fence


def build_registry(root: Path, label: str) -> dict[str, list[tuple[str, Path]]]:
    registry: dict[str, list[tuple[str, Path]]] = {}
    for child in sorted(root.iterdir()):
        if child.is_dir() and NAME_RE.fullmatch(child.name):
            registry.setdefault(child.name, []).append((label, child))
    return registry


def classify(
    name: str,
    self_name: str,
    registry: dict[str, list[tuple[str, Path]]],
    builtin: set[str],
    ignore: set[str],
    expect: set[str],
) -> tuple[str | None, list[tuple[str, Path]]]:
    if name == self_name:
        return "SELF", []
    paths = registry.get(name)
    if paths:
        if any(not (path / "SKILL.md").is_file() for _, path in paths):
            return "BROKEN", paths
        if len({path.resolve() for _, path in paths}) > 1:
            return "SHADOWED", paths
        return "LIVE", paths
    if name in builtin:
        return "BUILTIN", []
    if name in ignore:
        return "IGNORED", []
    if name in expect:
        return "MISSING", []
    if UUID_RE.fullmatch(name) or DATE_RE.fullmatch(name) or name in COMMAND_TOKENS:
        return "NON_SKILL", []
    if EXTERNAL_RE.fullmatch(name):
        return "EXTERNAL", []
    if HYPHEN_NAME_RE.fullmatch(name):
        return "CANDIDATE", []
    return None, []


def collect_refs(
    text: str,
    self_name: str,
    registry: dict[str, list[tuple[str, Path]]],
    builtin: set[str],
    ignore: set[str],
    expect: set[str],
) -> tuple[dict[str, dict[str, object]], bool]:
    spans, unterminated = collect_spans(text)
    refs: dict[str, dict[str, object]] = {}
    for lineno, name, in_fence in spans:
        status, paths = classify(name, self_name, registry, builtin, ignore, expect)
        if status is None:
            continue
        entry = refs.setdefault(
            name,
            {"status": status, "paths": paths, "lines": [], "fenced_lines": []},
        )
        target = entry["fenced_lines"] if in_fence else entry["lines"]
        target.append(lineno)
    return refs, unterminated


def format_lines(lines: object) -> str:
    return ",".join(str(number) for number in sorted(set(lines)))


def format_paths(paths: object) -> str:
    return "; ".join(
        f"{label}={ascii_text(path)}" for label, path in paths  # type: ignore[union-attr]
    )


def parse_csv(value: str) -> set[str]:
    return {item.strip() for item in value.split(",") if item.strip()}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Read-only audit of backticked cross-skill references in a SKILL.md."
        )
    )
    parser.add_argument("skill_dir", type=Path, help="directory containing SKILL.md")
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path.cwd(),
        help="workspace root used to locate .qoder/skills (default: cwd)",
    )
    parser.add_argument(
        "--user-root",
        type=Path,
        default=None,
        help="user-level skills root (default: ~/.qoder/skills)",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=None,
        help="project-level skills root (default: <workspace>/.qoder/skills)",
    )
    parser.add_argument(
        "--builtin",
        default="",
        help="comma-separated CLI built-in or plugin names from the current session",
    )
    parser.add_argument(
        "--ignore",
        default="",
        help="comma-separated confirmed non-skill tokens to ignore",
    )
    parser.add_argument(
        "--expect",
        default="",
        help=(
            "comma-separated owner references that must resolve; an unresolved "
            "expected name is reported as MISSING"
        ),
    )
    args = parser.parse_args(argv)

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    builtin = parse_csv(args.builtin)
    ignore = parse_csv(args.ignore)
    expect = parse_csv(args.expect)
    overlap = sorted(expect & ignore)
    if overlap:
        print(f"FAIL --expect and --ignore overlap: {', '.join(overlap)}")
        return 2

    skill_dir = args.skill_dir.expanduser().resolve()
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        print(f"FAIL SKILL.md not found: {ascii_text(skill_md)}")
        return 2

    user_root = (
        args.user_root.expanduser().resolve()
        if args.user_root is not None
        else (Path.home() / ".qoder" / "skills").resolve()
    )
    if not user_root.is_dir():
        print(f"FAIL user root not found: {ascii_text(user_root)}")
        return 2

    project_explicit = args.project_root is not None
    if project_explicit:
        project_root = args.project_root.expanduser().resolve()
        if not project_root.is_dir():
            print(f"FAIL project root not found: {ascii_text(project_root)}")
            return 2
    else:
        workspace = args.workspace.expanduser().resolve()
        candidate = (workspace / ".qoder" / "skills").resolve()
        project_root = candidate if candidate.is_dir() else None

    roots: list[tuple[str, Path]] = [("user", user_root)]
    if project_root is not None:
        if project_root != user_root:
            roots.append(("project", project_root))
        else:
            print("WARN project root equals user root; counted once")

    registry: dict[str, list[tuple[str, Path]]] = {}
    try:
        for label, root in roots:
            for name, paths in build_registry(root, label).items():
                registry.setdefault(name, []).extend(paths)
    except OSError as exc:
        print(f"FAIL cannot enumerate skill roots: {ascii_text(exc)}")
        return 2

    try:
        text = skill_md.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        print(f"FAIL cannot read SKILL.md: {ascii_text(exc)}")
        return 2

    refs, unterminated = collect_refs(
        text,
        skill_dir.name,
        registry,
        builtin,
        ignore,
        expect,
    )

    print(f"Target: {ascii_text(skill_md)}")
    print(f"Self: {skill_dir.name}")
    print("Roots:")
    for label, root in roots:
        print(f"  {label}: {ascii_text(root)}")
    if project_root is None:
        print("  project: absent (checked user root only)")
    print("References:")

    counts = {status: 0 for status in STATUS_ORDER}
    for name, entry in sorted(refs.items()):
        lines = entry["lines"]
        fenced_lines = entry["fenced_lines"]
        status = str(entry["status"])
        paths = entry["paths"]
        if lines:
            counts[status] += 1
            detail = f" [{format_paths(paths)}]" if paths else ""
            print(f"  {status} {name} lines={format_lines(lines)}{detail}")
        elif fenced_lines and status in ("MISSING", "BROKEN", "CANDIDATE"):
            counts["FENCED"] += 1
            print(
                f"  FENCED {name} lines={format_lines(fenced_lines)} "
                "(not counted; verify whether it is an example)"
            )

    if not any(counts.values()):
        print("  (no unresolved backticked skill names)")
        print("SUMMARY: no unresolved backticked skill names")
    else:
        summary = " ".join(
            f"{status.lower()}={counts[status]}"
            for status in STATUS_ORDER
            if counts[status]
        )
        print(f"SUMMARY: {summary}")
    if unterminated:
        print("WARN unterminated fenced block; later lines were treated as fenced")

    failed = counts["MISSING"] + counts["BROKEN"]
    if failed:
        print("RESULT FAIL")
        return 1
    if counts["CANDIDATE"]:
        print("REVIEW: classify each CANDIDATE with --expect or --ignore")
        print("RESULT REVIEW")
        return 1
    print("RESULT PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
