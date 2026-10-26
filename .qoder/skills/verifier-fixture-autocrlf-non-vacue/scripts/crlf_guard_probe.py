#!/usr/bin/env python3
"""Build a genuine CRLF checkout and prove a CR-stripping guard by bytes.

The probe never touches an existing repository: it creates a disposable one,
forces core.autocrlf through the environment, commits an LF blob, then restores
the worktree with `rm` + `git checkout -- .` so Git performs the conversion.

The fixture lives under ~/.qoder/tmp/fixture-autocrlf-probe-* unless --workdir
is given; a failed cleanup emits RESIDUE and turns PASS into FAIL, so the
script never claims CLEANED=1 while the directory survives.

Output is ASCII KEY=VALUE plus a final RESULT line. Exit codes: 0 PASS,
1 FAIL (an assertion did not hold), 2 ERROR (bad input or environment).
"""

import argparse
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path

KEY_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.-]*$")
VALUE_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


def emit(key, value):
    print(f"{key}={value}")


def emit_result(name, reason=None):
    if reason:
        emit("REASON", reason)
    print(f"RESULT {name}")


def run(cmd, cwd, env):
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
    )


def isolated_env(home):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["HOME"] = str(home)
    env["XDG_CONFIG_HOME"] = str(home / ".config")
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["GIT_CONFIG_GLOBAL"] = str(home / ".gitconfig-isolated")
    env["GIT_CONFIG_COUNT"] = "1"
    env["GIT_CONFIG_KEY_0"] = "core.autocrlf"
    env["GIT_CONFIG_VALUE_0"] = "true"
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GIT_AUTHOR_NAME"] = "crlf-probe"
    env["GIT_AUTHOR_EMAIL"] = "crlf-probe@example.invalid"
    env["GIT_COMMITTER_NAME"] = "crlf-probe"
    env["GIT_COMMITTER_EMAIL"] = "crlf-probe@example.invalid"
    return env


def _force_remove(func, target, exc):
    try:
        os.chmod(target, stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)
    except OSError:
        pass
    try:
        func(target)
    except OSError:
        pass


def remove_tree(path):
    """Delete the fixture despite read-only Git loose objects; True when gone."""
    for _ in range(3):
        try:
            if sys.version_info >= (3, 12):
                shutil.rmtree(path, onexc=_force_remove)
            else:
                shutil.rmtree(path, onerror=lambda f, p, e: _force_remove(f, p, e[1]))
        except OSError:
            pass
        if not path.exists():
            return True
        time.sleep(0.2)
    return False


def first_value(data, key):
    prefix = f"{key}: ".encode()
    for line in data.split(b"\n"):
        if line.startswith(prefix):
            return line[len(prefix):]
    return None


def probe(args, workdir):
    repo = workdir / "repo"
    home = workdir / "home"
    repo.mkdir()
    home.mkdir()
    env = isolated_env(home)

    git = shutil.which("git")
    if not git:
        return 2, "ERROR", "GIT_NOT_FOUND"
    if not shutil.which("bash"):
        emit("PIPELINE", "NA")
    emit("WORKDIR", workdir.as_posix())

    for cmd in (["git", "init", "-q", "."],):
        r = run(cmd, repo, env)
        if r.returncode != 0:
            emit("GIT_INIT_RC", r.returncode)
            return 2, "ERROR", "GIT_INIT_FAILED"

    r = run(["git", "config", "--get", "core.autocrlf"], repo, env)
    autocrlf = r.stdout.decode("ascii", "replace").strip()
    emit("AUTOCRLF", autocrlf or "NA")
    if autocrlf != "true":
        return 1, "FAIL", "AUTOCRLF_NOT_INHERITED"

    content = f"---\n{args.key}: {args.value}\ndescription: x\n---\n".encode("ascii")
    (repo / "SKILL.md").write_bytes(content)
    for cmd in (["git", "add", "SKILL.md"], ["git", "commit", "-qm", "base"]):
        r = run(cmd, repo, env)
        if r.returncode != 0:
            emit("GIT_RC", r.returncode)
            return 2, "ERROR", "GIT_COMMIT_FAILED"

    r = run(["git", "ls-files", "--eol", "SKILL.md"], repo, env)
    eol_before = r.stdout.decode("ascii", "replace").strip()
    emit("EOL_BEFORE", eol_before)

    (repo / "SKILL.md").unlink()
    r = run(["git", "checkout", "--", "SKILL.md"], repo, env)
    warnings = int(b"LF will be replaced by CRLF" in r.stderr)
    emit("CHECKOUT_WARNING", warnings)
    if r.returncode != 0:
        emit("CHECKOUT_RC", r.returncode)
        return 2, "ERROR", "CHECKOUT_FAILED"

    r = run(["git", "ls-files", "--eol", "SKILL.md"], repo, env)
    eol_after = r.stdout.decode("ascii", "replace").strip()
    emit("EOL_AFTER", eol_after)

    r = run(["git", "status", "--porcelain"], repo, env)
    status_lines = len([ln for ln in r.stdout.splitlines() if ln.strip()])
    emit("STATUS_LINES", status_lines)

    data = (repo / "SKILL.md").read_bytes()
    has_cr = int(b"\r\n" in data)
    emit("WORKTREE_HAS_CR", has_cr)

    raw = first_value(data, args.key)
    if raw is None:
        return 1, "FAIL", "KEY_LINE_NOT_FOUND"
    value = args.value.encode("ascii")
    guarded = raw.replace(b"\r", b"")
    stripped = raw.strip()
    emit("RAW_REPR", repr(raw))
    emit("RAW_LEN", len(raw))
    emit("UNGUARDED_EQ", int(raw == value))
    emit("GUARDED_REPR", repr(guarded))
    emit("GUARDED_LEN", len(guarded))
    emit("GUARDED_EQ", int(guarded == value))
    emit("BYTES_STRIP_LEN", len(stripped))
    emit("BYTES_STRIP_HIDES_CR", int(stripped == value and raw != value))

    bash = shutil.which("bash")
    if bash:
        r = run([bash, "-c", 'printf "%s" "$MSYSTEM"'], repo, env)
        emit("MSYSTEM", r.stdout.decode("ascii", "replace").strip() or "NA")
        r = run([bash, "-c", f"sed -n 's/^{args.key}: //p' SKILL.md"], repo, env)
        if r.returncode != 0 or not r.stdout:
            emit("PIPELINE", "NA")
        else:
            core = r.stdout.rstrip(b"\n")
            emit("PIPELINE_OUT_LEN", len(r.stdout))
            emit("PIPELINE_CORE_LEN", len(core))
            emit("PIPELINE_HAS_CR", int(b"\r" in core))
            emit("PIPELINE_STRIPS_CR", int(core == value))
        r = run(
            [bash, "-c", f'v="$(sed -n \'s/^{args.key}: //p\' SKILL.md)"; printf "%s" "$v"'],
            repo,
            env,
        )
        if r.returncode == 0:
            emit("CMDSUBST_LEN", len(r.stdout))
            emit("CMDSUBST_HAS_CR", int(b"\r" in r.stdout))
    else:
        emit("PIPELINE", "NA")

    checks = {
        "EOL_AFTER_CRLF": "w/crlf" in eol_after,
        "BASE_STARTED_LF": "w/lf" in eol_before,
        "STATUS_CLEAN": status_lines == 0,
        "WORKTREE_HAS_CR": has_cr == 1,
        "RAW_IS_VALUE_PLUS_CR": raw == value + b"\r",
        "UNGUARDED_DIFFERS": raw != value,
        "GUARDED_EQUALS": guarded == value,
    }
    failed = [name for name, ok in checks.items() if not ok]
    for name, ok in checks.items():
        emit(f"CHECK_{name}", int(ok))
    if failed:
        return 1, "FAIL", "ASSERTION_FAILED:" + ",".join(failed)
    return 0, "PASS", None


def main():
    parser = argparse.ArgumentParser(
        description="Prove a CR/strip guard against a real autocrlf CRLF checkout."
    )
    parser.add_argument("--key", default="name", help="frontmatter key to extract")
    parser.add_argument("--value", default="demo", help="expected value without CR")
    parser.add_argument("--workdir", help="nonexistent directory for the fixture")
    parser.add_argument("--keep", action="store_true", help="keep the fixture")
    args = parser.parse_args()

    if not KEY_RE.match(args.key):
        emit_result("ERROR", "INVALID_KEY")
        return 2
    if not VALUE_RE.match(args.value):
        emit_result("ERROR", "INVALID_VALUE")
        return 2
    if shutil.which("git") is None:
        emit_result("ERROR", "GIT_NOT_FOUND")
        return 2

    created = False
    if args.workdir:
        workdir = Path(args.workdir).resolve()
        if workdir.exists():
            emit_result("ERROR", "WORKDIR_EXISTS")
            return 2
        workdir.mkdir(parents=True)
        created = True
    else:
        root = Path.home() / ".qoder" / "tmp"
        root.mkdir(parents=True, exist_ok=True)
        workdir = Path(tempfile.mkdtemp(prefix="fixture-autocrlf-probe-", dir=root))
        created = True

    code, name, reason = 2, "ERROR", "UNEXPECTED"
    try:
        r = run(["git", "--version"], workdir, os.environ.copy())
        emit("GIT_VERSION", r.stdout.decode("ascii", "replace").strip().replace("git version ", ""))
        code, name, reason = probe(args, workdir)
    except subprocess.TimeoutExpired:
        code, name, reason = 2, "ERROR", "TIMEOUT"
    except OSError as exc:
        emit("OSERROR", type(exc).__name__)
        code, name, reason = 2, "ERROR", "OS_ERROR"

    if created and not args.keep:
        if remove_tree(workdir):
            emit("CLEANED", 1)
        else:
            emit("RESIDUE", workdir.as_posix())
            emit("CLEANED", 0)
            if name == "PASS":
                code, name, reason = 1, "FAIL", "CLEANUP_FAILED"
    elif created:
        emit("KEPT", workdir.as_posix())
        emit("CLEANED", 0)

    emit_result(name, reason)
    return code


if __name__ == "__main__":
    sys.exit(main())
