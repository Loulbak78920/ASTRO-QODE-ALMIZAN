#!/usr/bin/env python3
"""Harnais isole pour le flux de publication isolee d'un Skill.

Construit une fixture jetable sous ~/.qoder/tmp : origin nu local, clone source
occupe et sale sur une branche non main, second clone pour avancer le remote,
puis clone isole. Reutilise le verificateur d'archive reel en lecture seule.

Codes de sortie : 0 PASS, 1 FAIL, 2 usage ou environnement.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HOME = Path.home()
TMP_ROOT = HOME / ".qoder" / "tmp"
DEFAULT_VERIFIER = (
    HOME
    / ".qoder"
    / "skills"
    / "publier-skill-qoder-vers-depot-git"
    / "scripts"
    / "verifier_archive_skill.py"
)
SKILL_NAME = "fake-skill"
MERGE_BRANCH = f"merge/skill-{SKILL_NAME}"
EXPECTED_FILES = ["SKILL.md", "references/note.md", "scripts/tool.py"]
ORIGIN_REF = "refs/remotes/origin/main"
CLEANUP_PREFIX = "publish-fake-skill."
FIXTURE_PREFIX = "isolated-publish-"
GIT_TIMEOUT = 120
VERIFIER_TIMEOUT = 120
COMMIT_IDENTITY = (
    "user.name=Isolated Publish Test",
    "user.email=isolated-publish@example.invalid",
    "commit.gpgsign=false",
)


class Failure(Exception):
    pass


def ascii_text(value: object) -> str:
    return str(value).encode("ascii", "backslashreplace").decode("ascii")


def configure_stdout() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")
        except (AttributeError, ValueError):
            pass


def file_url(path: Path) -> str:
    # With MSYS_NO_PATHCONV=1, git keeps file:///C:/... as /C:/... and fails;
    # the two-slash form file://C:/... is resolved correctly.
    return "file://" + path.resolve().as_posix()


def git(repo: Path, *args: str) -> tuple[int, str]:
    env = dict(os.environ)
    env["LC_ALL"] = "C"
    env["GIT_TERMINAL_PROMPT"] = "0"
    # MSYS_NO_PATHCONV / MSYS2_ARG_CONV_EXCL make git resolve file:///C:/ as
    # /C:/... and break local clones (rc=128). Only the verifier needs them.
    cmd = ["git", "-C", str(repo), *args]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=GIT_TIMEOUT,
            env=env,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 128, ascii_text(exc)
    output = "\n".join(
        part.strip() for part in (proc.stdout, proc.stderr) if part and part.strip()
    )
    return proc.returncode, output.strip()


def must_git(repo: Path, *args: str) -> str:
    code, output = git(repo, *args)
    if code != 0:
        label = args[0] if args else ""
        raise Failure(f"git {label} rc={code}: {ascii_text(output)}")
    return output.strip()


def rev(repo: Path, *args: str) -> str:
    lines = must_git(repo, "rev-parse", *args).splitlines()
    if not lines:
        raise Failure(f"rev-parse returned nothing for {args!r}")
    return lines[0].strip()


def rev_lines(repo: Path, *args: str) -> list[str]:
    return [
        line.strip()
        for line in must_git(repo, "rev-parse", *args).splitlines()
        if line.strip()
    ]


def git_status(repo: Path, short: bool = False) -> str:
    mode = "-sb" if short else "--porcelain=v1"
    return must_git(repo, "--no-optional-locks", "status", mode)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.replace("\r\n", "\n").encode("utf-8"))


def configure_fixture(repo: Path) -> None:
    for key, value in (
        ("user.name", "Isolated Publish Test"),
        ("user.email", "isolated-publish@example.invalid"),
        ("core.autocrlf", "false"),
        ("commit.gpgsign", "false"),
    ):
        must_git(repo, "config", key, value)


def commit_with_identity(repo: Path, message: str) -> None:
    args: list[str] = []
    for item in COMMIT_IDENTITY:
        args.extend(["-c", item])
    must_git(repo, *args, "commit", "-m", message)


def repo_state(repo: Path) -> dict[str, str]:
    return {
        "branch": rev(repo, "--abbrev-ref", "HEAD"),
        "head": rev(repo, "HEAD"),
        "origin": rev(repo, ORIGIN_REF),
    }


def source_state(repo: Path) -> dict[str, str]:
    state = repo_state(repo)
    state["status"] = git_status(repo)
    state["base_hash"] = sha256_file(repo / "base.txt")
    state["untracked_hash"] = sha256_file(repo / "untracked.txt")
    state["local_main"] = rev(repo, "refs/heads/main")
    state["local_origin"] = rev(repo, ORIGIN_REF)
    return state


def assert_eq(name: str, got: object, expected: object) -> None:
    if got != expected:
        raise Failure(f"{name}: expected {expected!r}, got {got!r}")
    print(f"  ok {name}: {got!r}")


def assert_clean(repo: Path, name: str) -> None:
    status = git_status(repo)
    if status:
        raise Failure(f"{name}: worktree not clean: {ascii_text(status)}")
    print(f"  ok {name} clean:")


def assert_refs_unchanged(repo: Path, before: dict[str, str], name: str) -> None:
    after = repo_state(repo)
    if after != before:
        raise Failure(f"{name}: refs moved: before={before} after={after}")
    print(f"  ok {name}: refs unchanged")


def expect_guard(
    name: str, rc: int, output: str, expected_rc: int, expected_output: str
) -> None:
    got = output.strip()
    if rc != expected_rc or got != expected_output:
        raise Failure(
            f"{name}: expected rc={expected_rc} {expected_output!r}, "
            f"got rc={rc} {ascii_text(got)!r}"
        )
    print(f"  ok {name}: rc={rc} {expected_output}")


def setup_fixture(root: Path) -> tuple[Path, Path, Path]:
    origin = root / "origin.git"
    work = root / "work"
    other = root / "other"

    must_git(root, "init", "--bare", "--initial-branch=main", str(origin))
    must_git(root, "clone", "--quiet", file_url(origin), str(work))
    configure_fixture(work)

    write_lf(work / "base.txt", "base\n")
    must_git(work, "add", "base.txt")
    commit_with_identity(work, "base")
    must_git(work, "push", "-u", "origin", "main")

    must_git(work, "switch", "-c", "skill/occupied")
    write_lf(work / "base.txt", "base modified\n")
    write_lf(work / "untracked.txt", "untracked\n")

    must_git(root, "clone", "--quiet", file_url(origin), str(other))
    configure_fixture(other)
    return origin, work, other


def make_fake_skill(root: Path) -> Path:
    source = root / "fake-skill"
    write_lf(
        source / "SKILL.md",
        "---\nname: fake-skill\ndescription: Fixture only.\n---\n\n# Fake Skill\n\nFixture.\n",
    )
    write_lf(source / "references" / "note.md", "# Note\n\nFixture reference.\n")
    write_lf(source / "scripts" / "tool.py", "#!/usr/bin/env python3\nprint('fixture')\n")
    return source


def copy_skill(source: Path, dest: Path) -> list[str]:
    skill_file = source / "SKILL.md"
    if not skill_file.is_file():
        raise Failure(f"SKILL.md missing from {ascii_text(source)}")
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "SKILL.md").write_bytes(skill_file.read_bytes())
    copied = ["SKILL.md"]

    for dirname in ("references", "scripts"):
        base = source / dirname
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(source)
            if any(part in {".git", "__pycache__"} for part in rel.parts):
                continue
            if path.suffix.lower() in {".pyc", ".pyo"}:
                continue
            target = dest / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(path.read_bytes())
            copied.append(rel.as_posix())
    return sorted(copied)


def cache_in_archive(dest: Path) -> list[str]:
    found: list[str] = []
    for path in dest.rglob("*"):
        if path.name == "__pycache__" or path.suffix.lower() in {".pyc", ".pyo"}:
            found.append(path.relative_to(dest).as_posix())
    return sorted(found)


def run_verifier(
    verifier: Path,
    source: Path,
    repo: Path,
    mode: str,
    ref: str | None = None,
) -> tuple[int, str]:
    cmd = [
        sys.executable,
        str(verifier),
        "--source",
        str(source),
        "--repo",
        str(repo),
        "--from",
        mode,
    ]
    if ref:
        cmd.extend(["--ref", ref])
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env["LC_ALL"] = "C"
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=VERIFIER_TIMEOUT,
            env=env,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 128, ascii_text(exc)
    output = "\n".join(
        part.strip() for part in (proc.stdout, proc.stderr) if part and part.strip()
    )
    return proc.returncode, output.strip()


def verify_archive(
    verifier: Path,
    source: Path,
    repo: Path,
    mode: str,
    label: str,
    ref: str | None = None,
) -> None:
    rc, output = run_verifier(verifier, source, repo, mode, ref)
    ok_count = len(re.findall(r"^OK\s", output, flags=re.MULTILINE))
    if rc != 0 or "RESULT PASS" not in output or ok_count != len(EXPECTED_FILES):
        raise Failure(
            f"{label}: verifier rc={rc} ok={ok_count}\n{ascii_text(output)}"
        )
    print(f"  ok {label} rc={rc} PASS ({ok_count}/{len(EXPECTED_FILES)} OK)")


def create_isolated(work: Path) -> tuple[Path, Path]:
    url = must_git(work, "remote", "get-url", "origin")
    if not url:
        raise Failure("origin URL unreadable")
    tmp = Path(tempfile.mkdtemp(prefix=CLEANUP_PREFIX, dir=str(TMP_ROOT)))
    repo = tmp / "repo"
    must_git(tmp, "clone", "--branch", "main", "--single-branch", url, str(repo))
    for key in ("core.autocrlf", "user.name", "user.email"):
        code, _ = git(repo, "config", "--local", "--get", key)
        if code == 0:
            raise Failure(f"isolated clone has local config {key}")

    assert_eq("isolated branch", rev(repo, "--abbrev-ref", "HEAD"), "main")
    heads = rev_lines(repo, "HEAD", "origin/main")
    if len(heads) != 2:
        raise Failure(f"isolated clone: expected 2 hashes, got {heads!r}")
    assert_eq("isolated HEAD == origin/main", heads[0], heads[1])
    assert_clean(repo, "isolated")
    print(f"  isolated remote: {url}")
    return tmp, repo


def align_main(repo: Path) -> str:
    must_git(repo, "fetch", "origin")
    heads = rev_lines(repo, "HEAD", "origin/main")
    if len(heads) != 2:
        raise Failure(f"align main: expected 2 hashes, got {heads!r}")
    assert_eq("aligned HEAD == origin/main", heads[0], heads[1])
    return heads[0]


def create_merge_branch(repo: Path) -> None:
    must_git(repo, "switch", "-c", MERGE_BRANCH, "origin/main")
    assert_eq("merge branch", rev(repo, "--abbrev-ref", "HEAD"), MERGE_BRANCH)


def commit_archive(repo: Path) -> str:
    rel_dest = f".qoder/skills/{SKILL_NAME}"
    must_git(
        repo,
        "add",
        "--",
        f"{rel_dest}/SKILL.md",
        f"{rel_dest}/references",
        f"{rel_dest}/scripts",
    )
    commit_with_identity(repo, f"feat(skills): ajouter le Skill {SKILL_NAME}")
    commit_hash = rev(repo, "HEAD")
    committed = [
        line
        for line in must_git(
            repo, "show", "--name-only", "--pretty=format:", "HEAD"
        ).splitlines()
        if line
    ]
    expected = [f"{rel_dest}/{rel}" for rel in EXPECTED_FILES]
    assert_eq("commit files", sorted(committed), sorted(expected))
    assert_clean(repo, "after commit")
    return commit_hash


def guard(
    repo: Path,
    branch: str,
    head: str,
    origin: str,
    fetch: bool = False,
    short: bool = False,
) -> tuple[int, str]:
    if fetch:
        code, output = git(repo, "fetch", "origin")
        if code != 0:
            return 1, f"ERROR fetch: {ascii_text(output)}"

    current_branch = rev(repo, "--abbrev-ref", "HEAD")
    current_head = rev(repo, "HEAD")
    current_origin = rev(repo, ORIGIN_REF)

    if short:
        if current_head != head[:7]:
            return 1, f"STOP_HEAD head={current_head[:7]}"
        return 0, "CONTINUE"

    if current_branch != branch:
        return 1, f"STOP_BRANCH branch={current_branch}"
    if current_head != head:
        return 1, f"STOP_HEAD head={current_head}"
    if current_origin != origin:
        return 1, f"STOP_ORIGIN origin={current_origin}"
    if git_status(repo):
        return 1, "STOP_DIRTY"
    return 0, "CONTINUE"


def remote_head(repo: Path) -> str:
    output = must_git(repo, "ls-remote", "origin", "refs/heads/main")
    fields = output.split()
    if not fields:
        raise Failure("ls-remote returned no hash")
    return fields[0]


def pre_push_guard(repo: Path, head: str, origin: str) -> tuple[int, str]:
    code, output = git(repo, "fetch", "origin")
    if code != 0:
        return 1, f"ERROR fetch: {ascii_text(output)}"
    current_branch = rev(repo, "--abbrev-ref", "HEAD")
    if current_branch != "main":
        return 1, f"STOP_BRANCH branch={current_branch}"
    current_head = rev(repo, "HEAD")
    if current_head != head:
        return 1, f"STOP_HEAD head={current_head}"
    current_origin = rev(repo, ORIGIN_REF)
    if current_origin != origin:
        return 1, f"STOP_ORIGIN origin={current_origin}"
    current_remote = remote_head(repo)
    if current_remote != origin:
        return 1, f"STOP_REMOTE remote={current_remote}"
    return 0, "CONTINUE"


def advance_remote(other: Path) -> str:
    write_lf(other / "remote.txt", "remote\n")
    must_git(other, "add", "remote.txt")
    commit_with_identity(other, "remote advance")
    must_git(other, "push", "origin", "main")
    return rev(other, "HEAD")


def recover_archive(
    repo: Path, source: Path, verifier: Path, origin: str
) -> str:
    must_git(repo, "switch", "main")
    must_git(repo, "merge", "--ff-only", "origin/main")
    assert_eq("main aligned", rev(repo, "HEAD"), origin)
    must_git(repo, "switch", "-C", MERGE_BRANCH, "origin/main")
    assert_eq("recreated merge branch", rev(repo, "--abbrev-ref", "HEAD"), MERGE_BRANCH)

    dest = repo / ".qoder" / "skills" / SKILL_NAME
    copied = copy_skill(source, dest)
    assert_eq("recopied files", copied, EXPECTED_FILES)
    assert_eq("no cache after recovery", cache_in_archive(dest), [])
    verify_archive(verifier, source, repo, "worktree", "verifier after recovery")

    recovery_commit = commit_archive(repo)
    return recovery_commit


def cleanup_allowed(path: Path) -> bool:
    resolved = path.resolve()
    base = TMP_ROOT.resolve()
    return resolved.parent == base and resolved.name.startswith(CLEANUP_PREFIX)


def force_rmtree(path: Path) -> None:
    if not path.exists():
        return
    for attempt in range(3):
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                for name in filenames + dirnames:
                    target = Path(dirpath) / name
                    try:
                        os.chmod(target, stat.S_IWRITE | stat.S_IREAD)
                    except OSError:
                        pass
            try:
                os.chmod(path, stat.S_IWRITE | stat.S_IREAD)
            except OSError:
                pass
            shutil.rmtree(path)
            return
        except OSError:
            if attempt == 2:
                raise
            time.sleep(0.5)


def cleanup_clone(path: Path) -> tuple[int, str]:
    if not cleanup_allowed(path):
        return 1, f"REFUS {path}"
    try:
        force_rmtree(path)
    except OSError as exc:
        return 1, f"ERROR cleanup {ascii_text(exc)}"
    if path.exists():
        return 1, f"ERROR cleanup remains {path}"
    return 0, f"REMOVED {path}"


def assert_source_untouched(before: dict[str, str], work: Path, new_commit: str) -> None:
    after = source_state(work)
    checks = (
        ("branch", "original branch"),
        ("head", "original HEAD"),
        ("origin", "original origin/main"),
        ("status", "original status"),
        ("base_hash", "original modified file hash"),
        ("untracked_hash", "original untracked file hash"),
        ("local_main", "original local main"),
        ("local_origin", "original local origin/main"),
    )
    for key, label in checks:
        assert_eq(label, after[key], before[key])

    code, _ = git(work, "cat-file", "-e", new_commit)
    if code == 0:
        raise Failure("original clone contains the new commit")
    print("CHECK original clone untouched and new commit absent")


def cleanup_fixture(root: Path, isolated_tmp: Path | None, keep: bool) -> bool:
    if keep:
        print("CLEANUP skipped (--keep)")
        print(f"KEEP fixture root: {root}")
        if isolated_tmp is not None and isolated_tmp.exists():
            print(f"KEEP isolated clone: {isolated_tmp}")
        return True

    healthy = True
    if isolated_tmp is not None and isolated_tmp.exists():
        rc, output = cleanup_clone(isolated_tmp)
        if rc != 0:
            print(f"FAIL cleanup isolated clone: {ascii_text(output)}")
            healthy = False
    if root.exists():
        try:
            force_rmtree(root)
        except OSError as exc:
            print(f"FAIL cleanup root: {ascii_text(exc)}")
            healthy = False
    if healthy and not root.exists() and (
        isolated_tmp is None or not isolated_tmp.exists()
    ):
        print("CLEANUP root and isolated clone absent")
        return True
    print("CLEANUP FAILED")
    return False


def run(verifier: Path, keep: bool) -> int:
    try:
        TMP_ROOT.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        print(f"ERROR temp root: {ascii_text(exc)}")
        return 2

    root = Path(tempfile.mkdtemp(prefix=FIXTURE_PREFIX, dir=str(TMP_ROOT)))
    isolated_tmp: Path | None = None
    status = 1
    verifier_hash = sha256_file(verifier)
    print(f"Fixture root: {root}")
    print(f"Verifier: {verifier}")
    print(f"Verifier sha256: {verifier_hash}")

    try:
        origin, work, other = setup_fixture(root)
        baseline = source_state(work)
        print("STEP 0 original clone occupied and dirty")
        print("  " + baseline["status"].replace("\n", " | "))

        source = make_fake_skill(root)
        isolated_tmp, isolated = create_isolated(work)
        print(f"  isolated clone: {isolated}")

        base_origin = align_main(isolated)
        create_merge_branch(isolated)

        dest = isolated / ".qoder" / "skills" / SKILL_NAME
        copied = copy_skill(source, dest)
        print("  ok copy rc: 0")
        assert_eq("copied files", copied, EXPECTED_FILES)
        assert_eq("no cache in archive", cache_in_archive(dest), [])
        verify_archive(verifier, source, isolated, "worktree", "verifier worktree")

        commit_hash = commit_archive(isolated)
        print("STEP 5 commit", commit_hash)

        before = repo_state(isolated)
        rc, output = guard(
            isolated, MERGE_BRANCH, commit_hash, base_origin, short=True
        )
        expect_guard(
            "short-hash false stop",
            rc,
            output,
            1,
            f"STOP_HEAD head={commit_hash[:7]}",
        )
        assert_refs_unchanged(isolated, before, "short-hash guard")
        assert_clean(isolated, "short-hash guard")

        must_git(isolated, "switch", "main")
        before = repo_state(isolated)
        rc, output = guard(isolated, MERGE_BRANCH, commit_hash, base_origin)
        expect_guard(
            "branch-drift token", rc, output, 1, "STOP_BRANCH branch=main"
        )
        assert_refs_unchanged(isolated, before, "branch-drift guard")
        assert_clean(isolated, "branch-drift guard")
        must_git(isolated, "switch", MERGE_BRANCH)

        dirty = isolated / "dirty.txt"
        write_lf(dirty, "dirty\n")
        before = repo_state(isolated)
        rc, output = guard(isolated, MERGE_BRANCH, commit_hash, base_origin)
        expect_guard("dirty token", rc, output, 1, "STOP_DIRTY")
        assert_refs_unchanged(isolated, before, "dirty guard")
        if not dirty.exists():
            raise Failure("dirty guard removed the dirty file")
        dirty.unlink()
        assert_clean(isolated, "worktree clean again")

        new_origin = advance_remote(other)
        print("  ok origin/main advanced:", new_origin)
        rc, output = guard(
            isolated, MERGE_BRANCH, commit_hash, base_origin, fetch=True
        )
        expect_guard(
            "origin-drift token",
            rc,
            output,
            1,
            f"STOP_ORIGIN origin={new_origin}",
        )
        after = repo_state(isolated)
        assert_eq("branch after origin drift", after["branch"], MERGE_BRANCH)
        assert_eq("HEAD after origin drift", after["head"], commit_hash)
        assert_eq("origin updated by fetch", after["origin"], new_origin)
        assert_clean(isolated, "origin-drift guard")

        print("STEP recovery: align main, recreate branch, recopy, recommit")
        recovery_commit = recover_archive(isolated, source, verifier, new_origin)
        print("STEP 5b recovery commit", recovery_commit)

        rc, output = guard(
            isolated, MERGE_BRANCH, recovery_commit, new_origin
        )
        expect_guard("full pre-merge guard", rc, output, 0, "CONTINUE")

        must_git(isolated, "switch", "main")
        assert_eq("main before merge", rev(isolated, "HEAD"), new_origin)
        merge_output = must_git(isolated, "merge", "--ff-only", MERGE_BRANCH)
        if "Fast-forward" not in merge_output:
            raise Failure(
                f"fast-forward expected, got {ascii_text(merge_output)}"
            )
        print("  ok fast-forward")
        assert_eq("main after ff", rev(isolated, "HEAD"), recovery_commit)
        assert_eq("branch after ff", rev(isolated, "--abbrev-ref", "HEAD"), "main")
        status_short = git_status(isolated, short=True)
        if "[ahead 1]" not in status_short:
            raise Failure(f"status ahead 1 expected, got {ascii_text(status_short)}")
        print("  ok status ahead 1")

        rc, output = pre_push_guard(isolated, recovery_commit, new_origin)
        expect_guard("pre-push guard", rc, output, 0, "CONTINUE")
        push_output = must_git(isolated, "push", "origin", "main")
        if "main -> main" not in push_output:
            raise Failure(f"push line expected, got {ascii_text(push_output)}")
        print("  ok push line")
        assert_eq("remote main after push", remote_head(isolated), recovery_commit)
        verify_archive(
            verifier,
            source,
            isolated,
            "remote",
            "remote verifier",
            ref="origin/main",
        )

        must_git(isolated, "branch", "-d", MERGE_BRANCH)
        print("  ok branch deleted")
        assert_eq("final branch", rev(isolated, "--abbrev-ref", "HEAD"), "main")
        final_status = git_status(isolated, short=True)
        if not final_status.startswith("## main...origin/main") or "ahead" in final_status:
            raise Failure(f"final status unexpected: {ascii_text(final_status)}")
        print(f"  ok final status: {final_status}")

        print("STEP 9 isolated clone ready for cleanup")
        rc, output = cleanup_clone(root)
        if rc != 1 or "REFUS" not in output:
            raise Failure(f"cleanup guard accepted the fixture root: {output}")
        print("  ok cleanup refusal rc=1 REFUS")
        rc, output = cleanup_clone(isolated_tmp)
        if rc != 0 or "REMOVED" not in output:
            raise Failure(f"cleanup guard rejected the isolated clone: {output}")
        if isolated_tmp.exists():
            raise Failure("isolated clone still exists after cleanup")
        print("  ok cleanup accepted rc=0 REMOVED")
        print("STEP 9b isolated clone removed by guarded rm -rf")

        assert_source_untouched(baseline, work, recovery_commit)
        status = 0
    except Failure as exc:
        print(f"FAIL {ascii_text(exc)}")
        status = 1
    except Exception as exc:
        print(f"ERROR unexpected {type(exc).__name__}: {ascii_text(exc)}")
        status = 1
    finally:
        cleaned = cleanup_fixture(root, isolated_tmp, keep)
        if not cleaned:
            status = 1

    if status == 0:
        print(
            "RESULT PASS isolated publication flow "
            "(clone, SHA-256, guards, ff, push, remote verify, cleanup)"
        )
    else:
        print("RESULT FAIL isolated publication flow")
    return status


def main(argv: list[str] | None = None) -> int:
    configure_stdout()
    parser = argparse.ArgumentParser(
        description="Harnais isole pour le flux de publication isolee d'un Skill."
    )
    parser.add_argument(
        "--verifier",
        default=str(DEFAULT_VERIFIER),
        help="verificateur d'archive a executer en lecture seule",
    )
    parser.add_argument(
        "--keep",
        action="store_true",
        help="conserver la fixture et le clone isole pour diagnostic",
    )
    args = parser.parse_args(argv)

    if shutil.which("git") is None:
        print("ERROR git not found in PATH")
        return 2
    if not sys.executable:
        print("ERROR python executable not found")
        return 2
    verifier = Path(args.verifier).expanduser().resolve()
    if not verifier.is_file():
        print(f"ERROR verifier not found: {ascii_text(verifier)}")
        return 2
    return run(verifier, args.keep)


if __name__ == "__main__":
    raise SystemExit(main())
