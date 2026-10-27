#!/usr/bin/env python3
"""Read-only verifier for a backed-up and removed local directory.

Modes:
  compare : source and backup must match (file counts, content hash,
            SKILL.md hash, git HEAD/status/commits).
  absent  : source must be gone, the backup must remain valid, and no
            same-name copy may remain under the scanned skills roots.

The script never writes to the source, the backup, or the skills roots.
Exit codes: 0 = PASS, 1 = invariant failure, 2 = usage/environment error.
"""

import argparse
import hashlib
import os
import subprocess
import sys
from pathlib import Path

EXIT_PASS = 0
EXIT_FAIL = 1
EXIT_USAGE = 2


class UsageError(Exception):
    pass


class CheckFailed(Exception):
    pass


def safe(value):
    text = str(value)
    try:
        text.encode("ascii")
        return text
    except UnicodeEncodeError:
        return ascii(text)


def emit(key, value):
    print("{}={}".format(key, safe(value)))


def fail(message):
    print("FAIL {}".format(safe(message)))


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_link_like(path):
    if os.path.islink(path):
        return True
    isjunction = getattr(os.path, "isjunction", None)
    return bool(isjunction and isjunction(path))


def find_link_like(root):
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        for name in list(dirnames) + list(filenames):
            candidate = os.path.join(dirpath, name)
            if is_link_like(candidate):
                return candidate
        dirnames[:] = [name for name in dirnames if not is_link_like(os.path.join(dirpath, name))]
    return None


def walk_files(root):
    files = []
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        for name in filenames:
            files.append(Path(dirpath) / name)
    return files


def rel_posix(path, root):
    return path.relative_to(root).as_posix()


def content_hash(root):
    root = Path(root)
    digest = hashlib.sha256()
    files = sorted(walk_files(root), key=lambda item: rel_posix(item, root))
    for path in files:
        rel = rel_posix(path, root)
        if rel == ".git" or rel.startswith(".git/"):
            continue
        size = path.stat().st_size
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(size).encode("ascii"))
        digest.update(b"\0")
        digest.update(bytes.fromhex(sha256_file(path)))
        digest.update(b"\n")
    return digest.hexdigest()


def skill_hash(root):
    candidate = Path(root) / "SKILL.md"
    if not candidate.is_file():
        return None
    return sha256_file(candidate)


def git_run(path, *args):
    env = os.environ.copy()
    env.update(
        {
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_OPTIONAL_LOCKS": "0",
            "MSYS_NO_PATHCONV": "1",
            "MSYS2_ARG_CONV_EXCL": "*",
        }
    )
    command = ["git", "-C", str(path), "-c", "core.quotepath=false"] + list(args)
    try:
        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
        )
    except FileNotFoundError:
        raise UsageError("git executable not found")


def git_info(root):
    root = Path(root)
    info = {
        "present": (root / ".git").exists(),
        "head": "NA",
        "commits": "NA",
        "clean": "NA",
        "error": "",
    }
    if not info["present"]:
        return info

    head = git_run(root, "rev-parse", "--verify", "HEAD")
    if head.returncode == 0 and head.stdout.strip():
        info["head"] = head.stdout.strip()

    count = git_run(root, "rev-list", "--count", "HEAD")
    if count.returncode == 0 and count.stdout.strip():
        info["commits"] = count.stdout.strip().splitlines()[0]

    status = git_run(root, "status", "--porcelain=v1")
    if status.returncode == 0:
        info["clean"] = "yes" if status.stdout.strip() == "" else "no"
    else:
        info["error"] = (status.stderr or status.stdout).strip()

    return info


def norm(path):
    return os.path.normcase(os.path.realpath(str(path)))


def is_within(child, parent):
    try:
        return os.path.commonpath([norm(child), norm(parent)]) == norm(parent)
    except ValueError:
        return False


def require_directory(path, label):
    if not os.path.lexists(str(path)):
        raise UsageError("{} does not exist".format(label))
    if is_link_like(path):
        raise CheckFailed("{} is a symbolic link or junction".format(label))
    if not os.path.isdir(path):
        raise UsageError("{} is not a directory".format(label))


def snapshot(root):
    root = Path(root)
    files = walk_files(root)
    return {
        "files_all": len(files),
        "content_hash": content_hash(root),
        "skill_sha": skill_hash(root),
        "git": git_info(root),
    }


def scan_copies(roots, name):
    matches = []
    for root in roots:
        root = Path(root)
        for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
            rel = os.path.relpath(dirpath, root)
            depth = 0 if rel == "." else len(Path(rel).parts)
            if depth >= 2:
                dirnames[:] = []
                continue
            for directory in dirnames:
                if directory == name:
                    matches.append(str(Path(dirpath) / directory))
    unique = {}
    for match in matches:
        unique[norm(match)] = match
    return sorted(unique.values(), key=lambda value: norm(value))


def match_flag(left, right):
    if left is None and right is None:
        return "NA"
    if left == "NA" and right == "NA":
        return "NA"
    return "yes" if left == right else "no"


def compare_mode(args):
    source = Path(args.source)
    backup = Path(args.backup)

    emit("MODE", "compare")
    emit("SOURCE", source)
    emit("BACKUP", backup)

    require_directory(source, "source")
    require_directory(backup, "backup")
    emit("SOURCE_EXISTS", "yes")
    emit("BACKUP_EXISTS", "yes")

    if norm(source) == norm(backup):
        raise CheckFailed("source and backup are the same path")
    if is_within(backup, source):
        raise CheckFailed("backup is inside source")
    if is_within(source, backup):
        raise CheckFailed("source is inside backup")

    link = find_link_like(source)
    if link is not None:
        raise CheckFailed("source contains a symbolic link or junction: {}".format(link))
    link = find_link_like(backup)
    if link is not None:
        raise CheckFailed("backup contains a symbolic link or junction: {}".format(link))

    src = snapshot(source)
    bak = snapshot(backup)

    emit("SRC_FILES_ALL", src["files_all"])
    emit("BAK_FILES_ALL", bak["files_all"])
    emit("SRC_CONTENT_HASH", src["content_hash"])
    emit("BAK_CONTENT_HASH", bak["content_hash"])
    emit("SRC_SKILL_SHA256", src["skill_sha"] or "NA")
    emit("BAK_SKILL_SHA256", bak["skill_sha"] or "NA")
    emit("SRC_GIT_PRESENT", "yes" if src["git"]["present"] else "no")
    emit("BAK_GIT_PRESENT", "yes" if bak["git"]["present"] else "no")
    emit("SRC_HEAD", src["git"]["head"])
    emit("BAK_HEAD", bak["git"]["head"])
    emit("SRC_COMMITS", src["git"]["commits"])
    emit("BAK_COMMITS", bak["git"]["commits"])
    emit("SRC_STATUS_CLEAN", src["git"]["clean"])
    emit("BAK_STATUS_CLEAN", bak["git"]["clean"])

    files_match = "yes" if src["files_all"] == bak["files_all"] else "no"
    content_match = "yes" if src["content_hash"] == bak["content_hash"] else "no"
    skill_match = match_flag(src["skill_sha"], bak["skill_sha"])
    git_presence_match = "yes" if src["git"]["present"] == bak["git"]["present"] else "no"
    head_match = match_flag(src["git"]["head"], bak["git"]["head"])
    commits_match = match_flag(src["git"]["commits"], bak["git"]["commits"])

    emit("FILES_MATCH", files_match)
    emit("CONTENT_HASH_MATCH", content_match)
    emit("SKILL_SHA256_MATCH", skill_match)
    emit("GIT_PRESENT_MATCH", git_presence_match)
    emit("HEAD_MATCH", head_match)
    emit("COMMITS_MATCH", commits_match)

    failures = []

    def check(condition, message):
        if not condition:
            failures.append(message)

    check(files_match == "yes", "file count differs")
    check(content_match == "yes", "content hash differs")
    check(skill_match in ("yes", "NA"), "SKILL.md hash differs")
    check(git_presence_match == "yes", "git presence differs")
    check(head_match in ("yes", "NA"), "git HEAD differs")
    check(commits_match in ("yes", "NA"), "git commit count differs")
    check(src["git"]["clean"] in ("yes", "NA"), "source worktree is dirty")
    check(bak["git"]["clean"] in ("yes", "NA"), "backup worktree is dirty")
    if src["git"]["error"] or bak["git"]["error"]:
        check(False, "git status failed: {} / {}".format(src["git"]["error"], bak["git"]["error"]))

    for message in failures:
        fail(message)
    return EXIT_PASS if not failures else EXIT_FAIL


def absent_mode(args):
    target = Path(args.expect_absent)
    backup = Path(args.backup)
    name = args.name or target.name
    roots = args.skills_root or [
        str(Path.home() / ".qoder" / "skills"),
        str(Path.cwd() / ".qoder" / "skills"),
    ]

    emit("MODE", "absent")
    emit("TARGET", target)
    emit("BACKUP", backup)
    emit("NAME", name)

    require_directory(backup, "backup")
    emit("BACKUP_EXISTS", "yes")

    failures = []
    if os.path.lexists(str(target)):
        emit("TARGET_EXISTS", "yes")
        failures.append("target still exists")
    else:
        emit("TARGET_EXISTS", "no")

    link = find_link_like(backup)
    if link is not None:
        raise CheckFailed("backup contains a symbolic link or junction: {}".format(link))

    bak = snapshot(backup)
    emit("BAK_FILES_ALL", bak["files_all"])
    emit("BAK_CONTENT_HASH", bak["content_hash"])
    emit("BAK_SKILL_SHA256", bak["skill_sha"] or "NA")
    emit("BAK_GIT_PRESENT", "yes" if bak["git"]["present"] else "no")
    emit("BAK_HEAD", bak["git"]["head"])
    emit("BAK_COMMITS", bak["git"]["commits"])
    emit("BAK_STATUS_CLEAN", bak["git"]["clean"])

    if bak["files_all"] == 0:
        failures.append("backup is empty")
    if bak["git"]["present"] and bak["git"]["head"] == "NA":
        failures.append("backup git HEAD is not readable")
    if bak["git"]["clean"] == "no":
        failures.append("backup worktree is dirty")
    if bak["git"]["error"]:
        failures.append("backup git status failed: {}".format(bak["git"]["error"]))

    existing_roots = []
    for root in roots:
        root_path = Path(root)
        if not root_path.exists():
            raise UsageError("skills root does not exist: {}".format(root))
        existing_roots.append(str(root_path))
    emit("SCANNED_ROOTS", len(existing_roots))

    copies = scan_copies(existing_roots, name)
    emit("REMAINING_COPIES", len(copies))
    for copy in copies:
        emit("REMAINING_COPY", copy)
    if copies:
        failures.append("same-name copies remain")

    for message in failures:
        fail(message)
    return EXIT_PASS if not failures else EXIT_FAIL


def build_parser():
    parser = argparse.ArgumentParser(
        description="Read-only verification of a local directory backup and removal."
    )
    parser.add_argument("--source", help="source directory to compare with the backup")
    parser.add_argument("--backup", required=True, help="backup directory")
    parser.add_argument(
        "--expect-absent",
        help="path that must no longer exist (post-removal mode)",
    )
    parser.add_argument("--name", help="directory name to scan under the skills roots")
    parser.add_argument(
        "--skills-root",
        action="append",
        default=[],
        help="skills root to scan; repeatable",
    )
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if bool(args.source) == bool(args.expect_absent):
        parser.error("choose exactly one of --source or --expect-absent")

    try:
        if args.source:
            result = compare_mode(args)
        else:
            result = absent_mode(args)
    except UsageError as error:
        print("ERROR={}".format(safe(error)))
        print("RESULT FAIL")
        return EXIT_USAGE
    except CheckFailed as error:
        fail(str(error))
        print("RESULT FAIL")
        return EXIT_FAIL
    except OSError as error:
        print("ERROR={}".format(safe(error)))
        print("RESULT FAIL")
        return EXIT_USAGE

    if result == EXIT_PASS:
        print("RESULT PASS")
    else:
        print("RESULT FAIL")
    return result


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="backslashreplace")
    sys.exit(main())
