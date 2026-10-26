#!/usr/bin/env python3
"""Inventaire en lecture seule des refs, branches et objets inaccessibles Git."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

PSEUDO_REFS = (
    "ORIG_HEAD",
    "MERGE_HEAD",
    "CHERRY_PICK_HEAD",
    "REVERT_HEAD",
    "BISECT_START",
    "AUTO_MERGE",
)
ANOMALY_RE = re.compile(
    r"(?i)\b(error|warning|broken|invalid|missing|unable to resolve)\b"
)
CREDENTIAL_RE = re.compile(r"(://)[^/@\s]+@")
MAX_STATUS_LINES = 10
MAX_LOCKS = 10
MAX_ANOMALIES = 10


def git(repo: Path, *args: str, timeout: int = 180) -> tuple[int, str]:
    env = dict(os.environ, GIT_OPTIONAL_LOCKS="0", LC_ALL="C")
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True,
            timeout=timeout,
            env=env,
        )
    except FileNotFoundError:
        return 127, "git introuvable dans PATH"
    except subprocess.TimeoutExpired:
        return 124, f"timeout apres {timeout}s: git {' '.join(args)}"
    out = (proc.stdout + proc.stderr).decode("utf-8", errors="replace").rstrip("\r\n")
    return proc.returncode, out


def mask_url(url: str) -> str:
    return CREDENTIAL_RE.sub(r"\1***@", url)


def is_git_repo(path: Path) -> bool:
    if not path.is_dir():
        return False
    code, _ = git(path, "rev-parse", "--git-dir")
    return code == 0


def discover_repos(root: Path, max_depth: int = 3) -> list[Path]:
    found: list[Path] = []
    root = root.resolve()
    for current, dirs, _files in os.walk(root):
        depth = len(Path(current).relative_to(root).parts)
        if depth >= max_depth:
            dirs[:] = []
        if ".git" in dirs or (Path(current) / ".git").is_file():
            if current != str(root) and is_git_repo(Path(current)):
                found.append(Path(current))
                dirs[:] = [d for d in dirs if d != ".git"]
        dirs[:] = [d for d in dirs if d != ".git"]
    return sorted(found)


def parse_ref_lines(text: str) -> list[dict[str, str]]:
    rows = []
    for line in text.splitlines():
        parts = line.split("\t")
        if len(parts) < 3 or not parts[0].strip():
            continue
        rows.append(
            {
                "name": parts[0].strip(),
                "oid": parts[1].strip(),
                "upstream": parts[2].strip(),
                "track": parts[3].strip() if len(parts) > 3 else "",
            }
        )
    return rows


def parse_worktrees(text: str) -> tuple[list[dict[str, str]], dict[str, str]]:
    entries: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for line in text.splitlines() + [""]:
        if not line.strip():
            if current:
                entries.append(current)
                current = {}
            continue
        key, _, value = line.partition(" ")
        current[key] = value
    by_branch: dict[str, str] = {}
    for entry in entries:
        branch = entry.get("branch", "")
        if branch.startswith("refs/heads/"):
            by_branch[branch[len("refs/heads/") :]] = entry.get("worktree", "")
    return entries, by_branch


def repo_identity(repo: Path) -> Path:
    code, common = git(repo, "rev-parse", "--git-common-dir")
    if code == 0 and common.strip():
        path = Path(common.strip())
        return (path if path.is_absolute() else repo / path).resolve()
    return repo.resolve()


def base_ref(repo: Path, main: str) -> tuple[str, str]:
    for candidate in (f"refs/heads/{main}", f"refs/remotes/origin/{main}"):
        code, _ = git(repo, "rev-parse", "--verify", "--quiet", candidate)
        if code == 0:
            return candidate, candidate
    code, head = git(repo, "rev-parse", "--verify", "HEAD")
    if code == 0:
        return "HEAD", f"HEAD ({main} absent)"
    return "", ""

def classify(repo: Path, ref: str, base: str) -> str:
    if not base or ref == base:
        return "base"
    code, _ = git(repo, "merge-base", "--is-ancestor", ref, base)
    if code == 0:
        return "contenue"
    if code != 1:
        return "inconnue"
    n_code, n_out = git(repo, "rev-list", "--count", f"{base}..{ref}")
    if n_code != 0:
        return "non-contenue"
    return f"non-contenue uniques={n_out}"


def inspect_repo(repo: Path, main: str, max_unreachable: int, skip_fsck: bool) -> bool:
    print(f"=== REPO {repo}")
    code, toplevel = git(repo, "rev-parse", "--show-toplevel")
    if code != 0:
        print(f"  ERREUR: depot illisible: {toplevel}")
        return False
    print(f"  toplevel={toplevel}")

    _, branch = git(repo, "rev-parse", "--abbrev-ref", "HEAD")
    _, head_oid = git(repo, "rev-parse", "HEAD")
    print(f"  branche_courante={branch}")
    print(f"  head={head_oid}")

    code, status = git(repo, "status", "--porcelain=v1")
    status_lines = [line for line in status.splitlines() if line.strip()]
    print(f"  statut={'propre' if not status_lines else f'{len(status_lines)} entree(s)'}")
    for line in status_lines[:MAX_STATUS_LINES]:
        print(f"    {line}")
    if len(status_lines) > MAX_STATUS_LINES:
        print(f"    ... {len(status_lines) - MAX_STATUS_LINES} ligne(s) masquee(s)")

    code_up, upstream_cfg = git(repo, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}")
    resolved = code_up == 0 and upstream_cfg and "@{" not in upstream_cfg
    if not resolved:
        code_merge, merge_ref = git(repo, "config", "--get", f"branch.{branch}.merge")
        code_remote, remote_cfg = git(repo, "config", "--get", f"branch.{branch}.remote")
        if code_merge == 0 and merge_ref.strip():
            short = merge_ref.strip()
            if short.startswith("refs/heads/"):
                short = short[len("refs/heads/") :]
            label = short if code_remote != 0 or remote_cfg == "." else f"{remote_cfg}/{short}"
            print(f"  upstream={label} (ref absente)")
        else:
            print("  upstream=aucun")
    else:
        code_verify, _ = git(repo, "rev-parse", "--verify", "--quiet", upstream_cfg)
        if code_verify == 0:
            _, ahead = git(repo, "rev-list", "--count", f"{upstream_cfg}..HEAD")
            _, behind = git(repo, "rev-list", "--count", f"HEAD..{upstream_cfg}")
            print(f"  upstream={upstream_cfg} ahead={ahead} behind={behind}")
        else:
            print(f"  upstream={upstream_cfg} (ref absente)")

    _, worktree_text = git(repo, "worktree", "list", "--porcelain")
    worktrees, worktree_branches = parse_worktrees(worktree_text)
    print(f"  worktrees={len(worktrees)}")
    for entry in worktrees:
        wt_branch = entry.get("branch", "")
        if wt_branch.startswith("refs/heads/"):
            wt_branch = wt_branch[len("refs/heads/") :]
        print(f"    {entry.get('worktree', '?')} | {entry.get('HEAD', '?')[:7]} | {wt_branch or 'detached'}")

    base, base_label = base_ref(repo, main)
    print(f"  base={base_label}")

    _, local_text = git(
        repo,
        "for-each-ref",
        "--format=%(refname:short)\t%(objectname:short)\t%(upstream:short)\t%(upstream:track)",
        "refs/heads/",
    )
    local_rows = parse_ref_lines(local_text)
    print(f"  branches_locales={len(local_rows)}")
    for row in local_rows:
        flags = []
        if row["name"] == branch:
            flags.append("HEAD")
        if "gone" in row["track"]:
            flags.append("upstream-gone")
        if row["name"] in worktree_branches:
            flags.append("worktree")
        state = classify(repo, f"refs/heads/{row['name']}", base)
        print(
            f"    {row['name']} | {row['oid']} | {state} | "
            f"up={row['upstream'] or '-'} | track={row['track'] or '-'}"
            + (f" | {' '.join(flags)}" if flags else "")
        )

    _, remote_text = git(
        repo,
        "for-each-ref",
        "--format=%(refname:short)\t%(objectname:short)\t%(upstream:short)\t%(upstream:track)",
        "refs/remotes/",
    )
    remote_rows = [
        row
        for row in parse_ref_lines(remote_text)
        if not row["name"].endswith("/HEAD")
    ]
    print(f"  branches_distantes={len(remote_rows)}")
    for row in remote_rows:
        state = classify(repo, f"refs/remotes/{row['name']}", base)
        print(f"    {row['name']} | {row['oid']} | {state}")

    _, tag_text = git(repo, "tag", "--list")
    tags = [line for line in tag_text.splitlines() if line.strip()]
    print(f"  tags={len(tags)}")
    if tags:
        print(f"    {', '.join(tags[:12])}" + (" ..." if len(tags) > 12 else ""))

    git_dir_code, git_dir = git(repo, "rev-parse", "--absolute-git-dir")
    git_dir_path = Path(git_dir) if git_dir_code == 0 else repo / ".git"
    common_code, common_dir = git(repo, "rev-parse", "--git-common-dir")
    if common_code == 0 and common_dir.strip():
        common_path = Path(common_dir.strip())
        if not common_path.is_absolute():
            common_path = repo / common_path
        common_path = common_path.resolve()
    else:
        common_path = git_dir_path
    print(f"  packed_refs={'present' if (common_path / 'packed-refs').is_file() else 'absent'}")

    pseudo = [name for name in PSEUDO_REFS if (git_dir_path / name).is_file()]
    for dirname in ("rebase-merge", "rebase-apply"):
        if (git_dir_path / dirname).is_dir():
            pseudo.append(dirname)
    print(f"  pseudo_refs={', '.join(pseudo) if pseudo else 'aucune'}")
    for name in pseudo:
        target = git_dir_path / name
        value = target.read_text(encoding="ascii", errors="replace").strip()[:12] if target.is_file() else "dir"
        print(f"    {name} -> {value}")

    _, stash = git(repo, "rev-parse", "--verify", "--quiet", "refs/stash")
    namespaces = {}
    for namespace in ("refs/original", "refs/notes", "refs/replace", "refs/bisect", "refs/worktree"):
        _, listing = git(repo, "for-each-ref", "--count=1", namespace)
        namespaces[namespace] = len([x for x in listing.splitlines() if x.strip()])
    ns_text = ", ".join(f"{k}={v}" for k, v in namespaces.items())
    print(f"  stash={'present' if stash.strip() else 'absent'} | {ns_text}")

    lock_roots = [git_dir_path]
    if common_path != git_dir_path.resolve():
        lock_roots.append(common_path)
    locks = sorted({lock.resolve() for root in lock_roots for lock in root.rglob("*.lock")})
    print(f"  locks={len(locks)}")
    for lock in locks[:MAX_LOCKS]:
        print(f"    {lock}")
    if len(locks) > MAX_LOCKS:
        print(f"    ... {len(locks) - MAX_LOCKS} verrou(s) masque(s)")

    _, remotes = git(repo, "remote", "-v")
    if remotes:
        print("  remotes=")
        for line in remotes.splitlines():
            print(f"    {mask_url(line)}")

    if skip_fsck:
        print("  fsck=ignore (--skip-fsck)")
        return True

    code, fsck = git(repo, "fsck", "--full", "--no-reflogs", "--unreachable")
    unreachable: dict[str, list[str]] = {}
    anomalies = []
    for line in fsck.splitlines():
        match = re.match(r"^unreachable (commit|tree|blob|tag) ([0-9a-f]{40,64})$", line.strip())
        if match:
            unreachable.setdefault(match.group(1), []).append(match.group(2))
        elif ANOMALY_RE.search(line) and not line.startswith("Checking "):
            anomalies.append(line.strip())
    total = sum(len(v) for v in unreachable.values())
    print(f"  fsck_exit={code} unreachable={total} ({', '.join(f'{k}={len(v)}' for k, v in sorted(unreachable.items())) or 'aucun'})")
    for anomaly in anomalies[:MAX_ANOMALIES]:
        print(f"    ANOMALIE: {anomaly}")
    if len(anomalies) > MAX_ANOMALIES:
        print(f"    ... {len(anomalies) - MAX_ANOMALIES} anomalie(s) masquee(s)")
    for oid in unreachable.get("commit", [])[:max_unreachable]:
        _, subject = git(repo, "log", "-1", "--format=%h | %ad | %s", "--date=short", oid)
        print(f"    stale commit {subject or oid}")
    if len(unreachable.get("commit", [])) > max_unreachable:
        print(f"    ... {len(unreachable.get('commit', [])) - max_unreachable} commit(s) stale masque(s)")

    _, counts = git(repo, "count-objects", "-vH")
    for line in counts.splitlines():
        print(f"  objects {line.strip()}")
    return True


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        description="Inventaire en lecture seule des refs, branches et objets inaccessibles.",
        epilog="Codes de sortie: 0 tous les depots lus, 2 au moins un depot invalide.",
    )
    parser.add_argument("repos", nargs="*", help="chemins absolus des depots a inspecter")
    parser.add_argument("--main", default="main", help="branche de reference (defaut: main)")
    parser.add_argument(
        "--discover",
        action="append",
        default=[],
        metavar="DIR",
        help="decouvre les depots sous DIR (repetable, profondeur 3)",
    )
    parser.add_argument(
        "--max-unreachable",
        type=int,
        default=10,
        help="nombre de commits inaccessibles detailles (defaut: 10)",
    )
    parser.add_argument(
        "--skip-fsck",
        action="store_true",
        help="ne pas executer fsck (inventaire rapide)",
    )
    args = parser.parse_args()

    targets: list[Path] = []
    for raw in args.repos:
        targets.append(Path(raw).expanduser().resolve())
    for raw in args.discover:
        root = Path(raw).expanduser().resolve()
        if not root.is_dir():
            print(f"ERREUR: repertoire de decouverte introuvable: {root}")
            return 2
        targets.extend(discover_repos(root))

    seen: set[Path] = set()
    unique: list[Path] = []
    for target in targets:
        key = repo_identity(target) if target.is_dir() and is_git_repo(target) else target
        if key not in seen:
            seen.add(key)
            unique.append(target)

    if not unique:
        print("ERREUR: aucun depot fourni (positionnels ou --discover).")
        return 2

    valid = 0
    invalid: list[Path] = []
    for target in unique:
        if is_git_repo(target):
            try:
                if inspect_repo(target, args.main, args.max_unreachable, args.skip_fsck):
                    valid += 1
                else:
                    invalid.append(target)
            except Exception as exc:  # noqa: BLE001 - un depot ne doit pas interrompre les autres
                print(f"  ERREUR: inspection interrompue: {type(exc).__name__}: {exc}")
                invalid.append(target)
        else:
            print(f"=== REPO {target}")
            print("  ERREUR: pas un depot git lisible")
            invalid.append(target)
        print()

    print(f"REPOS lus={valid} invalides={len(invalid)}")
    if invalid:
        print("RESULT PARTIAL" if valid else "RESULT FAIL")
        return 2
    print("RESULT OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
