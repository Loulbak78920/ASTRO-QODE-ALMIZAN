#!/usr/bin/env python3
"""Pre-qualify local references in a SKILL.md with the installed skill-file-qa validator."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import re
import sys
from pathlib import Path
from urllib.parse import unquote

# Importing the validator must not create __pycache__ inside another skill.
sys.dont_write_bytecode = True

DEFAULT_VALIDATOR = (
    Path.home() / ".qoder" / "skills" / "skill-file-qa" / "scripts" / "validate_skill.py"
)
REQUIRED_API = ("LINK_RE", "SPAN_RE", "RESOURCE_PREFIXES", "normalize_ref",
                "looks_like_inline_ref", "collect_refs")


def ascii_text(value: object) -> str:
    return str(value).encode("ascii", "backslashreplace").decode("ascii")


def load_validator(path: Path):
    if not path.is_file():
        raise RuntimeError(f"validator not found: {ascii_text(path)}")
    spec = importlib.util.spec_from_file_location("skill_file_qa_validator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load validator: {ascii_text(path)}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    missing = [name for name in REQUIRED_API if not hasattr(module, name)]
    if missing:
        raise RuntimeError(f"validator API changed, missing: {', '.join(missing)}")
    return module


def reason_for_none(token: str) -> str:
    ref = token.strip()
    if ref.startswith("<") and ref.endswith(">"):
        ref = ref[1:-1]
    if not ref:
        return "empty"
    if "://" in ref:
        return "url"
    if ref.startswith("#"):
        return "anchor"
    if ref.startswith("mailto:"):
        return "mailto"
    core = ref.split("#", 1)[0]
    core = re.sub(r":\d+(?:-\d+)?$", "", core)
    core = unquote(core).strip().rstrip(".,;")
    while core.startswith("./"):
        core = core[2:]
    if not core:
        return "empty"
    if core.startswith("/"):
        return "absolute_posix"
    if core.startswith("~"):
        return "home"
    if core.startswith("$"):
        return "variable"
    if core.startswith(".."):
        return "parent"
    if re.match(r"^[A-Za-z]:", core):
        return "windows_absolute"
    return "unmatched_normalize"


def classify(module, raw: str, is_span: bool) -> tuple[str | None, str | None]:
    token = raw.strip()
    if is_span:
        if any(ch.isspace() or ch in "<>{}*?=" for ch in token):
            return None, "shape"
        if "#" in token:
            return None, "anchor"
        if not module.looks_like_inline_ref(token):
            ref = module.normalize_ref(token)
            if ref is None:
                return None, reason_for_none(token)
            if "/" not in ref:
                return None, "no_slash"
            return None, "unknown_extension"
    ref = module.normalize_ref(token)
    if ref is None:
        return None, reason_for_none(token)
    return ref, None


def collect_refs(module, text: str) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    counted: dict[str, set[str]] = {}
    skipped: dict[str, set[str]] = {}
    for raw in module.LINK_RE.findall(text):
        token = raw.split()[0] if raw.split() else raw
        ref, why = classify(module, token, False)
        kind = "link"
        if ref is None:
            skipped.setdefault(why or "unknown", set()).add(token)
        else:
            counted.setdefault(ref, set()).add(kind)
    for raw in module.SPAN_RE.findall(text):
        ref, why = classify(module, raw, True)
        kind = "span"
        if ref is None:
            skipped.setdefault(why or "unknown", set()).add(raw.strip())
        else:
            counted.setdefault(ref, set()).add(kind)
    expected = set(module.collect_refs(text))
    if set(counted) != expected:
        extra = sorted(set(counted) - expected)
        absent = sorted(expected - set(counted))
        raise RuntimeError(
            f"contract mismatch with validator: extra={extra} absent={absent}"
        )
    return counted, skipped


def resolve(ref: str, bases: list[tuple[str, Path]]) -> str | None:
    for label, base in bases:
        if (base / ref).exists():
            return label
    return None


def scan_reference_files(module, skill_dir: Path, workspace: Path) -> list[tuple[str, int, str, str | None]]:
    found = []
    root = skill_dir / "references"
    if not root.is_dir():
        return found
    for path in sorted(root.rglob("*.md")):
        rel = path.relative_to(skill_dir).as_posix()
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        for lineno, line in enumerate(text.splitlines(), 1):
            for raw in module.SPAN_RE.findall(line):
                ref, _why = classify(module, raw, True)
                if ref is None:
                    continue
                bases = [
                    ("reference-dir", path.parent),
                    ("skill", skill_dir),
                    ("workspace", workspace),
                ]
                found.append((rel, lineno, ref, resolve(ref, bases)))
    return found


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Qualify local references of a SKILL.md before skill-file-qa."
    )
    parser.add_argument("skill_dir", type=Path)
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--validator", type=Path, default=DEFAULT_VALIDATOR)
    parser.add_argument("--scan-references", action="store_true")
    parser.add_argument("--strict-references", action="store_true")
    parser.add_argument("--show-skipped", action="store_true")
    args = parser.parse_args(argv)

    skill_dir = args.skill_dir.expanduser().resolve()
    workspace = args.workspace.expanduser().resolve()
    validator = args.validator.expanduser().resolve()
    if not skill_dir.is_dir():
        print(f"FAIL  skill directory not found: {ascii_text(skill_dir)}")
        return 2
    if not workspace.is_dir():
        print(f"FAIL  workspace not found: {ascii_text(workspace)}")
        return 2

    try:
        module = load_validator(validator)
    except Exception as exc:
        print(f"FAIL  {ascii_text(exc)}")
        return 2

    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        print(f"FAIL  SKILL.md not found in {ascii_text(skill_dir)}")
        return 2
    raw = skill_md.read_bytes()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        print(f"FAIL  SKILL.md is not valid UTF-8: {ascii_text(exc)}")
        return 2

    digest = hashlib.sha256(validator.read_bytes()).hexdigest()
    print(f"VALIDATOR {ascii_text(validator)} size={validator.stat().st_size} sha256={digest}")
    print(f"SKILL {ascii_text(skill_dir.name)}")
    print(f"WORKSPACE {ascii_text(workspace)}")
    if raw.startswith(b"\xef\xbb\xbf"):
        print("WARN  SKILL.md starts with a UTF-8 BOM; validator will FAIL the frontmatter")

    try:
        counted, skipped = collect_refs(module, text)
    except RuntimeError as exc:
        print(f"FAIL  {ascii_text(exc)}")
        return 2

    missing = 0
    for ref in sorted(counted):
        scope = resolve(ref, [("skill", skill_dir), ("workspace", workspace)])
        kinds = ",".join(sorted(counted[ref]))
        if scope:
            print(f"COUNTED {ascii_text(ref)} RESOLVED {scope} via {kinds}")
        else:
            print(f"COUNTED {ascii_text(ref)} MISSING via {kinds}")
            missing += 1

    for why in sorted(skipped):
        tokens = sorted(skipped[why])
        if args.show_skipped:
            for token in tokens:
                print(f"SKIPPED {ascii_text(token)} {why}")
        else:
            sample = ", ".join(tokens[:3])
            more = f", +{len(tokens) - 3}" if len(tokens) > 3 else ""
            print(f"SKIPPED {len(tokens)} {why}: {ascii_text(sample)}{more}")

    manual_missing = 0
    if args.scan_references:
        for rel, lineno, ref, scope in scan_reference_files(module, skill_dir, workspace):
            if scope:
                print(f"MANUAL {rel}:{lineno} {ascii_text(ref)} RESOLVED {scope}")
            else:
                print(f"MANUAL {rel}:{lineno} {ascii_text(ref)} MISSING")
                manual_missing += 1
        print(f"MANUAL_SUMMARY references files checked, missing={manual_missing}")

    print(
        "SUMMARY "
        f"counted={len(counted)} resolved={len(counted) - missing} missing={missing} "
        f"skipped={sum(len(v) for v in skipped.values())}"
    )
    failed = missing > 0 or (args.strict_references and manual_missing > 0)
    print("QUALIFIER FAIL" if failed else "QUALIFIER PASS")
    return 1 if failed else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(2)
    except Exception as exc:
        print(f"FAIL  qualifier error: {ascii_text(exc)}")
        sys.exit(2)
