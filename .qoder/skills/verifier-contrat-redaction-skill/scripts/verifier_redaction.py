"""Read-only delivery-gate checks for a skill draft; never writes."""

import argparse
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("FAIL pyyaml: not installed")
    sys.exit(2)

FRONTMATTER = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n", re.S)
APPROX_TIME = re.compile(r"(?<![\d:])\d{1,2}:\d{2}(?::\d{1,2})?[xX](?![\w])")


def decode_needle(text):
    out = []
    i = 0
    while i < len(text):
        if (
            text[i] == "\\"
            and i + 5 < len(text)
            and text[i + 1] == "u"
            and re.fullmatch(r"[0-9a-fA-F]{4}", text[i + 2:i + 6])
        ):
            out.append(chr(int(text[i + 2:i + 6], 16)))
            i += 6
        elif text[i] == "\\" and i + 1 < len(text) and text[i + 1] == "n":
            out.append("\n")
            i += 2
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def split_needle(spec):
    path, sep, needle = spec.partition("=")
    if not sep or not path or not needle:
        raise ValueError("expected FILE=NEEDLE")
    return path, decode_needle(needle)


def read_text(path):
    return path.read_text(encoding="utf-8")


def measure_description(path):
    raw = read_text(path)
    if raw.startswith("---"):
        match = FRONTMATTER.match(raw)
        if not match:
            raise ValueError("frontmatter block not closed")
        data = yaml.safe_load(match.group(1)) or {}
        if not isinstance(data, dict) or not isinstance(data.get("description"), str):
            raise ValueError("no string description in frontmatter")
        value = data["description"]
    else:
        value = raw.rstrip("\r\n")
    length = len(value)
    newlines = value.count("\n") + value.count("\r")
    ok = length <= 1024 and newlines == 0 and bool(value.strip())
    print(f"DESC_LEN {length}")
    print(f"DESC_INNER_NEWLINES {newlines}")
    print("DESC_1024_LIMIT 1024")
    print(f"DESC_OK {'yes' if ok else 'no'}")
    return ok


def check_package(skill_dir, failures, approx_exclude=()):
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        print("FAIL skill-dir: SKILL.md missing")
        failures.append("skill-dir")
        return
    text = read_text(skill_md)
    match = FRONTMATTER.match(text)
    if not match:
        print("FAIL frontmatter: not found")
        failures.append("frontmatter")
        return
    try:
        data = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError as exc:
        print(f"FAIL frontmatter: yaml error ({type(exc).__name__})")
        failures.append("frontmatter")
        return
    if not isinstance(data, dict):
        print("FAIL frontmatter: not a mapping")
        failures.append("frontmatter")
        return

    name = data.get("name")
    description = data.get("description")
    desc_len = len(description) if isinstance(description, str) else -1
    desc_lines = (description.count("\n") + description.count("\r")) + 1 if isinstance(description, str) else 0
    body_lines = len(text[match.end():].splitlines())
    files = sorted(
        str(p.relative_to(skill_dir)).replace("\\", "/")
        for p in skill_dir.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts
    )

    print(f"NAME {name}")
    print(f"NAME_MATCH {'yes' if name == skill_dir.resolve().name else 'no'}")
    print(f"DESC_LEN {desc_len}")
    print(f"DESC_LINES {desc_lines}")
    print(f"BODY_LINES {body_lines}")
    print(f"FILES {len(files)}")
    print("FILE_LIST " + ",".join(files))

    if name != skill_dir.resolve().name:
        failures.append("name")
    if not isinstance(description, str) or not description.strip() or desc_lines != 1 or desc_len > 1024:
        failures.append("description")
    if body_lines >= 500:
        failures.append("body")

    hits = 0
    excluded = set()
    for item in approx_exclude:
        rel_item = str(Path(item).as_posix())
        excluded.add(rel_item[2:] if rel_item.startswith("./") else rel_item)
    for path in sorted(p for p in skill_dir.rglob("*.md") if p.is_file()):
        rel = str(path.relative_to(skill_dir)).replace("\\", "/")
        if rel in excluded:
            print(f"APPROX_TIME_SKIPPED {rel}")
            continue
        for lineno, line in enumerate(read_text(path).splitlines(), 1):
            for found in APPROX_TIME.finditer(line):
                hits += 1
                print(f"APPROX_TIME_HIT {rel}:{lineno}:{found.start() + 1} len={len(found.group(0))}")
    print(f"APPROX_TIME_HITS {hits}")
    if hits:
        failures.append("approx-time")

    caches = [str(p) for p in skill_dir.rglob("*") if p.name == "__pycache__" or p.suffix == ".pyc"]
    print(f"CACHE_HITS {len(caches)}")
    if caches:
        failures.append("cache")


def run_assertion(spec, kind, skill_dir, failures):
    try:
        rel, needle = split_needle(spec)
    except ValueError:
        print("FAIL assertion: expected FILE=NEEDLE")
        failures.append(kind)
        return
    path = Path(rel)
    if not path.is_absolute() and skill_dir is not None:
        path = skill_dir / rel
    if not path.is_file():
        print(f"FAIL {kind.upper()} file={rel} reason=not-found")
        failures.append(kind)
        return
    hits = read_text(path).count(needle)
    if kind == "count":
        ok = hits >= 1
    else:
        ok = hits == 0
    print(f"{kind.upper()} file={rel} hits={hits} ok={'yes' if ok else 'no'}")
    if not ok:
        failures.append(kind)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Read-only delivery-gate checks for a skill draft.")
    parser.add_argument("--desc-file", help="candidate description: plain text or a YAML frontmatter file")
    parser.add_argument("--skill-dir", help="written skill package to inspect")
    parser.add_argument("--count", action="append", default=[], metavar="FILE=NEEDLE", help="assert at least one hit")
    parser.add_argument("--zero", action="append", default=[], metavar="FILE=NEEDLE", help="assert zero hits")
    parser.add_argument("--approx-exclude", action="append", default=[], metavar="REL", help="skip a file in the approximate-time scan")
    args = parser.parse_args(argv)

    if not (args.desc_file or args.skill_dir or args.count or args.zero):
        parser.error("give at least one of --desc-file, --skill-dir, --count, --zero")

    failures = []
    if args.desc_file:
        print(f"CHECK desc-file {args.desc_file}")
        try:
            if not measure_description(Path(args.desc_file)):
                failures.append("description")
        except (OSError, ValueError, yaml.YAMLError) as exc:
            print(f"FAIL desc-file: {type(exc).__name__}")
            failures.append("description")

    if args.skill_dir:
        skill_dir = Path(args.skill_dir)
        print(f"CHECK package {args.skill_dir}")
        if not skill_dir.is_dir():
            print("FAIL skill-dir: not a directory")
            failures.append("skill-dir")
        else:
            check_package(skill_dir, failures, args.approx_exclude)

    base = Path(args.skill_dir) if args.skill_dir else None
    for spec in args.count:
        run_assertion(spec, "count", base, failures)
    for spec in args.zero:
        run_assertion(spec, "zero", base, failures)

    print(f"FAILURES {len(failures)}")
    print(f"RESULT {'PASS' if not failures else 'FAIL'}")
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
