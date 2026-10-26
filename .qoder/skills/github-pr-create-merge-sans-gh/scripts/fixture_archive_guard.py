#!/usr/bin/env python3
"""Disposable fixture for the Step 2 bis archive guard.

The guard block is extracted verbatim from SKILL.md at runtime, so this fixture
cannot silently drift from the documented procedure. Four cases run in a
temporary directory:

  positive-crlf         real CRLF checkout, rc=0 + ARCHIVE_UPDATE, no DIFF_SKILL
  negative-diff-skill   rc=2 + DIFF_SKILL
  negative-main-only    rc=2 + MAIN_ONLY_STOP
  negative-source-dirty rc=2 + SOURCE_DIRTY_STOP; a no-DIFF_SKILL check alone
                        would pass here, which is the hollow-assertion trap

No network and no credentials are used. The real Skill directory is only read
(SKILL.md). All fixture repositories live under a temporary directory removed
unless --keep is passed.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

DEFAULT_SKILL_MD = Path(__file__).resolve().parent.parent / "SKILL.md"
GUARD_HEADING = "## Étape 2 bis"
REQUIRED_TOKENS = (
    "tr -d '\\r'",
    "ARCHIVE_UPDATE",
    "DIFF_SKILL",
    "MAIN_ONLY_STOP",
    "SOURCE_DIRTY_STOP",
)


class FixtureError(RuntimeError):
    pass


def normalize(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "")


def tail(proc: subprocess.CompletedProcess, limit: int = 1200) -> str:
    text = normalize((proc.stdout or "") + (proc.stderr or ""))
    return text[-limit:]


def run(cmd: Sequence[str], cwd: Path, env: Dict[str, str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        list(cmd),
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def git(args: Sequence[str], cwd: Path, env: Dict[str, str], check: bool = True) -> subprocess.CompletedProcess:
    proc = run(["git", *args], cwd, env)
    if check and proc.returncode != 0:
        raise FixtureError("git %s failed rc=%s: %s" % (" ".join(args), proc.returncode, tail(proc)))
    return proc


def require_tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise FixtureError("%s not found in PATH" % name)
    return path


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def extract_block(skill_md: Path) -> Tuple[str, str]:
    if not skill_md.is_file():
        raise FixtureError("SKILL.md not found: %s" % skill_md)
    text = skill_md.read_text(encoding="utf-8", errors="strict")
    start = text.find(GUARD_HEADING)
    if start < 0:
        raise FixtureError("heading not found: %s" % GUARD_HEADING)
    fence = "```bash"
    fence_at = text.find(fence, start)
    if fence_at < 0:
        raise FixtureError("bash fence not found after Step 2 bis")
    line_end = text.find("\n", fence_at + len(fence))
    if line_end < 0:
        raise FixtureError("unterminated bash fence opening")
    close_at = text.find("```", line_end + 1)
    if close_at < 0:
        raise FixtureError("unterminated bash fence")
    block = text[line_end + 1:close_at]
    missing = [token for token in REQUIRED_TOKENS if token not in block]
    if missing:
        raise FixtureError("block missing token(s): %s" % ", ".join(missing))
    return block, hashlib.sha256(block.encode("utf-8")).hexdigest()


def make_env() -> Dict[str, str]:
    env = os.environ.copy()
    env["GIT_CONFIG_COUNT"] = "1"
    env["GIT_CONFIG_KEY_0"] = "core.autocrlf"
    env["GIT_CONFIG_VALUE_0"] = "true"
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["LC_ALL"] = "C"
    for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY"):
        env.pop(key, None)
    return env


def msys_path(path: Path) -> str:
    text = path.as_posix()
    if len(text) >= 2 and text[1] == ":":
        return "/" + text[0].lower() + text[2:]
    return text


def init_repo(path: Path, env: Dict[str, str]) -> None:
    path.mkdir(parents=True, exist_ok=True)
    git(["init", "-q", "-b", "main"], path, env)
    git(["config", "user.name", "Fixture"], path, env)
    git(["config", "user.email", "fixture@example.invalid"], path, env)


def write_pkg(root: Path, name: str, extra_main_only: bool = False) -> None:
    write_text(root / "SKILL.md", "---\nname: %s\n---\n\n# Demo\n" % name)
    write_text(root / "references/note.md", "note\n")
    write_text(root / "scripts/tool.py", "print('fixture')\n")
    if extra_main_only:
        write_text(root / "references/legacy.md", "legacy\n")


def build_case(
    case_dir: Path,
    env: Dict[str, str],
    base_name: str,
    source_name: str,
    extra_main_only: bool,
    source_dirty: bool,
    crlf: bool,
) -> Tuple[Path, Path]:
    base = case_dir / "base"
    init_repo(base, env)
    write_pkg(base / ".qoder/skills/demo", base_name, extra_main_only)
    git(["add", ".qoder/skills/demo"], base, env)
    git(["commit", "-q", "-m", "fixture base"], base, env)

    origin = case_dir / "origin.git"
    git(["init", "--bare", "-q", origin.as_posix()], case_dir, env)
    git(["config", "uploadpack.allowFilter", "true"], origin, env)
    git(["symbolic-ref", "HEAD", "refs/heads/main"], origin, env)
    git(["push", "-q", origin.as_uri(), "main:main"], base, env)

    source = case_dir / "source"
    init_repo(source, env)
    write_pkg(source, source_name)
    git(["add", "SKILL.md", "references", "scripts"], source, env)
    git(["commit", "-q", "-m", "fixture source"], source, env)

    if source_dirty:
        with open(source / "SKILL.md", "a", encoding="utf-8", newline="\n") as fh:
            fh.write("\n<!-- dirty -->\n")

    if crlf:
        (source / "SKILL.md").unlink()
        git(["checkout", "--", "."], source, env)
        eol = git(["ls-files", "--eol", "SKILL.md"], source, env).stdout
        status = git(["status", "--porcelain"], source, env).stdout
        raw = (source / "SKILL.md").read_bytes()
        if "w/crlf" not in eol:
            raise FixtureError("CRLF checkout not observed: %s" % eol.strip())
        if status.strip():
            raise FixtureError("CRLF checkout left a dirty status: %s" % status.strip())
        if b"name: demo\r\n" not in raw:
            raise FixtureError("CRLF bytes not found on the name: line")

    return origin, source


def run_guard(
    case_dir: Path,
    source: Path,
    origin: Path,
    block: str,
    env: Dict[str, str],
    bash: str,
) -> Tuple[int, str]:
    script = case_dir / "guard-block.sh"
    write_text(script, block)
    case_env = env.copy()
    case_env.update(
        {
            "REMOTE_URL": origin.as_uri(),
            "BASE": "main",
            "BRANCH": "main",
            "NOM": "demo",
            "SOURCE": msys_path(source),
            "TMPDIR": msys_path(case_dir),
        }
    )
    proc = run([bash, str(script)], case_dir, case_env)
    output = normalize((proc.stdout or "") + "\n" + (proc.stderr or ""))
    return proc.returncode, output


def check_positive(rc: int, output: str) -> List[str]:
    reasons = []
    if rc != 0:
        reasons.append("rc=%s expected=0" % rc)
    for token in ("ARCHIVE_UPDATE", "MAIN_NAME=demo", "SRC_NAME=demo"):
        if token not in output:
            reasons.append("missing=%s" % token)
    for token in ("DIFF_SKILL", "MAIN_ONLY_STOP", "SOURCE_DIRTY_STOP"):
        if token in output:
            reasons.append("unexpected=%s" % token)
    return reasons


def check_negative(rc: int, output: str, expected: Sequence[str], forbidden: Sequence[str]) -> List[str]:
    reasons = []
    if rc != 2:
        reasons.append("rc=%s expected=2" % rc)
    for token in expected:
        if token not in output:
            reasons.append("missing=%s" % token)
    for token in forbidden:
        if token in output:
            reasons.append("unexpected=%s" % token)
    return reasons


def force_rmtree(path: Path) -> None:
    if not path.exists():
        return
    for item in [path, *path.rglob("*")]:
        try:
            os.chmod(item, 0o700 if item.is_dir() else 0o600)
        except OSError:
            pass
    shutil.rmtree(path, ignore_errors=True)
    if path.exists():
        for item in [path, *path.rglob("*")]:
            try:
                os.chmod(item, 0o700 if item.is_dir() else 0o600)
            except OSError:
                pass
        shutil.rmtree(path, ignore_errors=True)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the Step 2 bis archive guard in disposable local repositories.",
    )
    parser.add_argument("--skill-md", type=Path, default=DEFAULT_SKILL_MD, help="SKILL.md to extract the guard block from")
    parser.add_argument("--keep", action="store_true", help="keep the fixture root for inspection")
    args = parser.parse_args(argv)

    root = None
    try:
        block, block_sha = extract_block(args.skill_md)
        print("SKILL_MD %s" % args.skill_md)
        print("BLOCK_SHA256 %s" % block_sha)
        bash = require_tool("bash")
        require_tool("git")
        env = make_env()
        root = Path(tempfile.mkdtemp(prefix="gh-pr-guard-"))
        print("FIXTURE_ROOT %s" % root.as_posix())

        cases = (
            (
                "positive-crlf",
                dict(base_name="demo", source_name="demo", extra_main_only=False, source_dirty=False, crlf=True),
                "positive",
            ),
            (
                "negative-diff-skill",
                dict(base_name="demo-base", source_name="demo", extra_main_only=False, source_dirty=False, crlf=False),
                "negative",
            ),
            (
                "negative-main-only",
                dict(base_name="demo", source_name="demo", extra_main_only=True, source_dirty=False, crlf=False),
                "negative",
            ),
            (
                "negative-source-dirty",
                dict(base_name="demo", source_name="demo", extra_main_only=False, source_dirty=True, crlf=False),
                "negative",
            ),
        )

        passed = 0
        failed = 0
        for name, spec, kind in cases:
            case_dir = root / name
            case_dir.mkdir()
            try:
                origin, source = build_case(case_dir, env, **spec)
                rc, output = run_guard(case_dir, source, origin, block, env, bash)
                if kind == "positive":
                    reasons = check_positive(rc, output)
                    extra = " crlf=w/crlf status=clean name_guard=ok" if not reasons else ""
                elif name == "negative-diff-skill":
                    reasons = check_negative(
                        rc,
                        output,
                        ("DIFF_SKILL", "MAIN_NAME=demo-base", "SRC_NAME=demo"),
                        ("MAIN_ONLY_STOP",),
                    )
                    extra = ""
                elif name == "negative-main-only":
                    reasons = check_negative(
                        rc,
                        output,
                        ("MAIN_ONLY_STOP", "MAIN_ONLY references/legacy.md"),
                        ("DIFF_SKILL",),
                    )
                    extra = ""
                else:
                    reasons = check_negative(
                        rc,
                        output,
                        ("SOURCE_DIRTY_STOP",),
                        ("DIFF_SKILL",),
                    )
                    extra = " hollow=no-DIFF_SKILL-alone-would-pass"
                if reasons:
                    failed += 1
                    print("CASE %s FAIL %s" % (name, "; ".join(reasons)))
                    print("  OUTPUT_TAIL %s" % output[-800:].replace("\n", " | "))
                else:
                    passed += 1
                    print("CASE %s PASS rc=%s %s%s" % (name, rc, kind, extra))
            except FixtureError as exc:
                failed += 1
                print("CASE %s FAIL %s" % (name, exc))

        print("RESULT PASS=%s FAIL=%s" % (passed, failed))
        return 0 if failed == 0 else 1
    except FixtureError as exc:
        print("ERROR %s" % exc)
        return 2
    except Exception as exc:  # no traceback: keep stdout actionable
        print("ERROR %s: %s" % (type(exc).__name__, exc))
        return 2
    finally:
        if root is not None and root.exists():
            if args.keep:
                print("KEPT %s" % root.as_posix())
            else:
                force_rmtree(root)
                print("CLEANED")


if __name__ == "__main__":
    sys.exit(main())
