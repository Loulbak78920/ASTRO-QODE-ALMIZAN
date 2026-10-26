#!/usr/bin/env python3
"""Read-only content verification for path:line citations in Markdown files."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import unquote

EXIT_OK = 0
EXIT_FAIL = 1
EXIT_USAGE = 2

TEXT_EXT = r"(?:md|py|json|txt|ya?ml|csv|html)"
REL_PATH = r"(?:\.{1,2}/)*(?:[A-Za-z0-9_.-]+/)*[A-Za-z0-9_.-]+?\." + TEXT_EXT

FILE_URL_RE = re.compile(
    r"file://(?P<path>[^)\s`'\"<>]+?)#L(?P<start>\d+)(?:-L?(?P<end>\d+))?"
)
REL_FRAG_RE = re.compile(
    r"(?<![A-Za-z0-9_./:-])(?P<path>" + REL_PATH + r")#L(?P<start>\d+)(?:-L?(?P<end>\d+))?"
)
ABS_RE = re.compile(
    r"(?<![A-Za-z0-9_./:-])(?P<path>[A-Za-z]:/(?:[^)\s`'\"<>]+/)*[^)\s`'\"<>/]+?\."
    + TEXT_EXT
    + r"):(?P<start>\d+)(?:-(?P<end>\d+))?"
)
REL_RE = re.compile(
    r"(?<![A-Za-z0-9_./:-])(?P<path>" + REL_PATH + r"):(?P<start>\d+)(?:-(?P<end>\d+))?"
)
SHORT_RE = re.compile(
    r"(?<![A-Za-z0-9_.-])(?P<skill>[a-z0-9][a-z0-9-]+)\s+SKILL\.md:(?P<start>\d+)(?:-(?P<end>\d+))?"
)

STATUS_MATCH = "MATCH"
STATUS_DRIFT = "DRIFT"
STATUS_MISSING = "MISSING"
STATUS_READ = "READ"
STATUS_AMBIGUOUS = "AMBIGUOUS"
STATUS_UNREADABLE = "UNREADABLE"


@dataclass
class Citation:
    source_line: int
    raw: str
    kind: str
    path_text: str
    start: int
    end: int
    resolved: Path | None = None
    reason: str = ""
    candidates: list[Path] = field(default_factory=list)
    status: str = ""
    detail: str = ""
    now_at: list[int] = field(default_factory=list)
    expectation: dict | None = None


@dataclass
class Snapshot:
    path: Path
    sha256: str
    size: int
    mtime_ns: int
    lines: list[str]


def configure_stdout() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def norm(text: str, ignore_case: bool) -> str:
    value = re.sub(r"\s+", " ", text).strip()
    return value.casefold() if ignore_case else value


def parse_citations(text: str, installed: set[str]) -> list[Citation]:
    citations: list[Citation] = []
    patterns = (
        ("file_url", FILE_URL_RE, None),
        ("rel_frag", REL_FRAG_RE, None),
        ("abs", ABS_RE, None),
        ("rel", REL_RE, None),
        ("short", SHORT_RE, "skill"),
    )
    for lineno, line in enumerate(text.splitlines(), 1):
        scan = line.replace("`", " ")
        occupied: list[tuple[int, int]] = []
        for kind, regex, skill_group in patterns:
            for match in regex.finditer(scan):
                if any(match.start() < end and start < match.end() for start, end in occupied):
                    continue
                if skill_group:
                    skill = match.group(skill_group)
                    if skill not in installed:
                        continue
                    path_text = f"{skill}/SKILL.md"
                else:
                    path_text = match.group("path")
                    if kind in ("rel", "rel_frag") and "/" not in path_text:
                        continue
                start = int(match.group("start"))
                end = int(match.group("end") or start)
                if end < start:
                    start, end = end, start
                occupied.append((match.start(), match.end()))
                citations.append(
                    Citation(
                        source_line=lineno,
                        raw=match.group(0).strip(),
                        kind=kind,
                        path_text=path_text,
                        start=start,
                        end=end,
                    )
                )
    citations.sort(key=lambda c: (c.source_line, c.start))
    return citations


def installed_names(roots: list[Path]) -> set[str]:
    names: set[str] = set()
    for root in roots:
        if not root.is_dir():
            continue
        for child in root.iterdir():
            if child.is_dir() and (child / "SKILL.md").is_file():
                names.add(child.name)
    return names


def resolve_path(path_text: str, citing: Path, workspace: Path | None,
                 roots: list[Path]) -> tuple[Path | None, str, list[Path]]:
    if path_text.startswith("file://"):
        path_text = path_text[len("file://"):]
    path_text = unquote(path_text)
    if re.match(r"^/[A-Za-z]:/", path_text):
        path_text = path_text[1:]

    raw_path = Path(path_text)
    if raw_path.is_absolute():
        return (raw_path, "" if raw_path.is_file() else "file_not_found", [])

    parts = raw_path.as_posix().split("/")
    if len(parts) == 2 and parts[1] == "SKILL.md":
        matches = [root / parts[0] / "SKILL.md" for root in roots
                   if (root / parts[0] / "SKILL.md").is_file()]
        if len(matches) > 1:
            return (None, "ambiguous_skill_name", matches)
        if len(matches) == 1:
            return (matches[0], "", [])

    candidates: list[Path] = [citing.parent / raw_path]
    if workspace is not None:
        candidates.append(workspace / raw_path)
    candidates.extend(root / raw_path for root in roots)
    for candidate in candidates:
        if candidate.is_file():
            return (candidate, "", [])
    return (None, "file_not_found", candidates)


def read_snapshot(path: Path) -> Snapshot:
    data = path.read_bytes()
    text = data.decode("utf-8-sig")
    return Snapshot(
        path=path,
        sha256=hashlib.sha256(data).hexdigest(),
        size=len(data),
        mtime_ns=path.stat().st_mtime_ns,
        lines=text.splitlines(),
    )


def find_occurrences(lines: list[str], needle: str, ignore_case: bool) -> list[int]:
    normalized = norm(needle, ignore_case)
    if not normalized:
        return []
    hits = [index + 1 for index, line in enumerate(lines)
            if normalized in norm(line, ignore_case)]
    if hits:
        return hits
    words = len(normalized.split(" "))
    for index in range(len(lines)):
        for span in range(2, min(words + 3, len(lines) - index + 1)):
            joined = " ".join(lines[index:index + span])
            if normalized in norm(joined, ignore_case):
                hits.append(index + 1)
                break
    return hits


def load_expectations(path: Path) -> list[dict]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read expectations: {exc}") from exc
    if not isinstance(payload, list):
        raise ValueError("expectations must be a JSON array")
    result: list[dict] = []
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            raise ValueError(f"expectation #{index} is not an object")
        cite = item.get("cite")
        contains = item.get("contains")
        if not isinstance(cite, str) or not cite.strip():
            raise ValueError(f"expectation #{index} has no cite")
        if not isinstance(contains, str) or not contains.strip():
            raise ValueError(f"expectation #{index} has no contains")
        result.append({"cite": cite.strip(), "contains": contains.strip()})
    return result


def parse_single_cite(text: str) -> tuple[str, int, int] | None:
    scan = text.replace("`", " ")
    for kind, regex, skill_group in (
        ("file_url", FILE_URL_RE, None),
        ("rel_frag", REL_FRAG_RE, None),
        ("abs", ABS_RE, None),
        ("rel", REL_RE, None),
        ("short", SHORT_RE, "skill"),
    ):
        match = regex.search(scan)
        if not match:
            continue
        if skill_group:
            path_text = f"{match.group(skill_group)}/SKILL.md"
        else:
            path_text = match.group("path")
            if kind in ("rel", "rel_frag") and "/" not in path_text:
                continue
        start = int(match.group("start"))
        end = int(match.group("end") or start)
        if end < start:
            start, end = end, start
        return (path_text, start, end)
    return None


def truncate(text: str, limit: int) -> str:
    flat = re.sub(r"\s+", " ", text).strip()
    if limit > 0 and len(flat) > limit:
        return flat[: limit - 1] + "…"
    return flat


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify path:line citations against their cited text (read-only)."
    )
    parser.add_argument("doc", help="citing Markdown file or Skill directory")
    parser.add_argument("--workspace", default=None,
                        help="root for relative paths (default: current directory)")
    parser.add_argument("--skills-root", action="append", default=[],
                        help="skills root for skill-name/ path forms; repeatable")
    parser.add_argument("--expect-file", default=None,
                        help="JSON array of {cite, contains} expectations")
    parser.add_argument("--strict", action="store_true",
                        help="READ citations and zero citations fail the run")
    parser.add_argument("--ignore-case", action="store_true",
                        help="case-insensitive substring matching")
    parser.add_argument("--max-text", type=int, default=240,
                        help="max printed characters per cited range (0 = all)")
    args = parser.parse_args()

    doc = Path(args.doc)
    if doc.is_dir():
        doc = doc / "SKILL.md"
    if not doc.is_file():
        print(f"RESULT USAGE\nERROR citing document not found: {doc}")
        print("EXIT=2")
        return EXIT_USAGE

    workspace = Path(args.workspace) if args.workspace else Path.cwd()
    roots = [Path(item) for item in args.skills_root]
    if not roots:
        roots = [Path.home() / ".qoder" / "skills", workspace / ".qoder" / "skills"]

    try:
        doc_bytes = doc.read_bytes()
        doc_text = doc_bytes.decode("utf-8-sig")
    except (OSError, UnicodeDecodeError) as exc:
        print(f"RESULT USAGE\nERROR cannot read citing document: {exc}")
        print("EXIT=2")
        return EXIT_USAGE
    doc_sha = hashlib.sha256(doc_bytes).hexdigest()

    installed = installed_names(roots)
    citations = parse_citations(doc_text, installed)

    for citation in citations:
        resolved, reason, candidates = resolve_path(
            citation.path_text, doc, workspace, roots
        )
        citation.resolved = resolved
        citation.reason = reason
        citation.candidates = candidates

    try:
        expectations = load_expectations(Path(args.expect_file)) if args.expect_file else []
    except ValueError as exc:
        print(f"RESULT USAGE\nERROR {exc}")
        print("EXIT=2")
        return EXIT_USAGE

    unmatched_expectations: list[dict] = []
    used_expectations: set[int] = set()
    for expectation in expectations:
        parsed = parse_single_cite(expectation["cite"])
        if parsed is None:
            print(f"RESULT USAGE\nERROR cannot parse expectation cite: {expectation['cite']}")
            print("EXIT=2")
            return EXIT_USAGE
        path_text, start, end = parsed
        resolved, reason, _ = resolve_path(path_text, doc, workspace, roots)
        expectation["_parsed"] = (
            resolved, reason, start, end, Path(path_text).as_posix()
        )

    for citation in citations:
        cite_path = Path(citation.path_text).as_posix()
        for index, expectation in enumerate(expectations):
            if index in used_expectations:
                continue
            resolved, reason, start, end, path_norm = expectation["_parsed"]
            same_path = (
                resolved is not None
                and citation.resolved is not None
                and resolved.resolve() == citation.resolved.resolve()
            ) or (
                resolved is None
                and citation.resolved is None
                and reason == citation.reason
                and path_norm == cite_path
            )
            if same_path and start <= citation.start <= end:
                citation.expectation = expectation
                used_expectations.add(index)
                break

    for index, expectation in enumerate(expectations):
        if index not in used_expectations:
            unmatched_expectations.append(expectation)

    snapshots: dict[str, Snapshot] = {}
    unreadable: list[tuple[Path, str]] = []
    for citation in citations:
        if citation.resolved is None:
            continue
        key = str(citation.resolved.resolve())
        if key in snapshots:
            continue
        try:
            snapshots[key] = read_snapshot(citation.resolved)
        except (OSError, UnicodeDecodeError) as exc:
            unreadable.append((citation.resolved, str(exc)))

    for citation in citations:
        if citation.resolved is None:
            citation.status = (
                STATUS_AMBIGUOUS if citation.reason == "ambiguous_skill_name" else STATUS_MISSING
            )
            citation.detail = citation.reason
            continue
        snapshot = snapshots.get(str(citation.resolved.resolve()))
        if snapshot is None:
            citation.status = STATUS_UNREADABLE
            citation.detail = "cannot read cited file"
            continue
        total = len(snapshot.lines)
        if citation.start < 1 or citation.end > total:
            citation.status = STATUS_MISSING
            citation.detail = f"line_out_of_range total={total}"
            continue
        range_text = "\n".join(snapshot.lines[citation.start - 1:citation.end])
        if citation.expectation is None:
            citation.status = STATUS_READ
            citation.detail = "no_expectation"
            continue
        needle = citation.expectation["contains"]
        if norm(needle, args.ignore_case) in norm(range_text, args.ignore_case):
            citation.status = STATUS_MATCH
            citation.detail = f"contains={truncate(needle, 80)}"
        else:
            citation.status = STATUS_DRIFT
            citation.now_at = find_occurrences(snapshot.lines, needle, args.ignore_case)
            citation.detail = "text_not_found" if not citation.now_at else "text_moved"

    unstable: list[tuple[Path, str, str]] = []
    for key, snapshot in snapshots.items():
        try:
            current = hashlib.sha256(Path(key).read_bytes()).hexdigest()
        except OSError as exc:
            unstable.append((Path(key), snapshot.sha256, f"unreadable: {exc}"))
            continue
        if current != snapshot.sha256:
            unstable.append((Path(key), snapshot.sha256, current))

    try:
        doc_after = hashlib.sha256(doc.read_bytes()).hexdigest()
    except OSError:
        doc_after = "unreadable"
    doc_changed = doc_after != doc_sha

    counts = {
        STATUS_MATCH: 0, STATUS_DRIFT: 0, STATUS_MISSING: 0,
        STATUS_READ: 0, STATUS_AMBIGUOUS: 0, STATUS_UNREADABLE: 0,
    }
    for citation in citations:
        counts[citation.status] = counts.get(citation.status, 0) + 1

    print(f"DOC: {doc}")
    print(f"DOC_SHA256: {doc_sha}")
    print(f"ROOTS: {', '.join(str(root) for root in roots)}")
    print(f"CITATIONS: {len(citations)}")
    for index, citation in enumerate(citations, 1):
        line = (
            f"CITATION {index:03d} | source=L{citation.source_line} | kind={citation.kind} "
            f"| cite={citation.raw} | lines={citation.start}-{citation.end} "
            f"| status={citation.status}"
        )
        if citation.resolved is not None:
            line += f" | resolved={citation.resolved}"
        if citation.detail:
            line += f" | detail={citation.detail}"
        if citation.now_at:
            line += f" | now_at={','.join('L' + str(item) for item in citation.now_at[:5])}"
        if citation.candidates:
            line += f" | candidates={'; '.join(str(item) for item in citation.candidates[:4])}"
        print(line)
        if citation.resolved is not None and citation.start >= 1:
            snapshot = snapshots.get(str(citation.resolved.resolve()))
            if snapshot is not None and citation.end <= len(snapshot.lines):
                text = "\n".join(snapshot.lines[citation.start - 1:citation.end])
                print(f"  TEXT: {truncate(text, args.max_text)}")
    for expectation in unmatched_expectations:
        print(f"EXPECTATION | cite={expectation['cite']} | status=NOT_IN_DOC")
    for path, sha, current in unstable:
        print(f"HASH_CHANGED | path={path} | before={sha} | after={current}")
    if doc_changed:
        print(f"HASH_CHANGED | path={doc} | before={doc_sha} | after={doc_after}")
    for path, snapshot in sorted(snapshots.items()):
        print(
            f"HASH | path={snapshot.path} | sha256={snapshot.sha256} "
            f"| size={snapshot.size} | mtime_ns={snapshot.mtime_ns} "
            f"| lines={len(snapshot.lines)}"
        )
    for path, error in unreadable:
        print(f"UNREADABLE | path={path} | error={truncate(error, 160)}")

    failures = (
        counts[STATUS_DRIFT] + counts[STATUS_MISSING] + counts[STATUS_AMBIGUOUS]
        + counts[STATUS_UNREADABLE] + len(unmatched_expectations)
        + len(unstable) + (1 if doc_changed else 0)
    )
    if args.strict:
        failures += counts[STATUS_READ] + (1 if not citations else 0)

    print(
        "SUMMARY "
        f"total={len(citations)} match={counts[STATUS_MATCH]} drift={counts[STATUS_DRIFT]} "
        f"missing={counts[STATUS_MISSING]} read={counts[STATUS_READ]} "
        f"ambiguous={counts[STATUS_AMBIGUOUS]} unreadable={counts[STATUS_UNREADABLE]} "
        f"not_in_doc={len(unmatched_expectations)} unstable={len(unstable) + (1 if doc_changed else 0)} "
        f"strict={'yes' if args.strict else 'no'}"
    )

    if unreadable:
        print("RESULT USAGE")
        print("EXIT=2")
        return EXIT_USAGE
    if failures:
        print("RESULT FAIL")
        print(f"EXIT={EXIT_FAIL}")
        return EXIT_FAIL
    print("RESULT PASS")
    print(f"EXIT={EXIT_OK}")
    return EXIT_OK


if __name__ == "__main__":
    configure_stdout()
    sys.exit(main())
