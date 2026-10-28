"""Copy drifted Skill packages into a delivery worktree and publish one commit each.

The worktree and its branch must already exist, created from origin/main by the
caller. For every package the script copies only SKILL.md, references/** and
scripts/**, proves source stability and copy identity, stages only that package,
commits, then enforces: HEAD^ == origin/main, origin/main is an ancestor, push
HEAD:main, fetch, HEAD == origin/main.

Exit codes: 0 = all packages published (or already identical), 2 = STOP.
Never forces, never rebases, never writes outside the worktree.
"""
import argparse
import hashlib
import os
import shutil
import subprocess
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(errors="backslashreplace")


class Stop(Exception):
    pass


def git(repo, *args, check=True):
    p = subprocess.run(["git", "-C", repo] + list(args), capture_output=True, text=True)
    if check and p.returncode != 0:
        raise Stop("git %s: %s" % (" ".join(args), (p.stderr or p.stdout).strip()[:300]))
    return p


def out(repo, *args):
    return git(repo, *args).stdout.strip()


def in_scope(rel):
    return rel == "SKILL.md" or rel.startswith("references/") or rel.startswith("scripts/")


def enumerate_files(root):
    found = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in (".git", "__pycache__", ".qoder"))
        for fn in sorted(filenames):
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, root).replace("\\", "/")
            if in_scope(rel):
                found[rel] = full
    return found


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def hash_all(root):
    return {rel: sha256(p) for rel, p in enumerate_files(root).items()}


def valid_name(name):
    return bool(name) and "/" not in name and "\\" not in name and name not in (".", "..") and not name.startswith(".")


def registered_worktrees(repo):
    raw = git(repo, "worktree", "list", "--porcelain").stdout
    return [os.path.realpath(line[len("worktree "):]) for line in raw.splitlines() if line.startswith("worktree ")]


def main():
    ap = argparse.ArgumentParser(description="Publish drifted Skill packages from one linked worktree.")
    ap.add_argument("--repo", required=True, help="archive Git clone")
    ap.add_argument("--src", required=True, help="local skills root")
    ap.add_argument("--worktree", required=True, help="linked worktree already created from origin/main")
    ap.add_argument("--branch", required=True, help="delivery branch checked out in the worktree")
    ap.add_argument("--packages", required=True, help="comma-separated package names")
    ap.add_argument("--prefix", default=".qoder/skills/", help="archive directory prefix")
    ap.add_argument("--message", default="docs(skill): actualiser l'archive {pkg}", help="commit message template")
    ap.add_argument("--no-push", action="store_true", help="commit locally, skip push and post-push guard")
    args = ap.parse_args()

    repo = os.path.abspath(args.repo)
    src = os.path.abspath(args.src)
    wt = os.path.abspath(args.worktree)
    prefix = args.prefix if args.prefix.endswith("/") else args.prefix + "/"
    packages = [p.strip() for p in args.packages.split(",") if p.strip()]
    if not packages:
        raise SystemExit("no package given")
    for pkg in packages:
        if not valid_name(pkg):
            raise SystemExit("invalid package name: %r" % pkg)

    wt_real = os.path.realpath(wt)
    if wt_real not in registered_worktrees(repo):
        raise SystemExit("worktree not registered under repo: %s" % wt)

    try:
        if out(wt, "rev-parse", "--abbrev-ref", "HEAD") != args.branch:
            raise Stop("branch mismatch: %s" % out(wt, "rev-parse", "--abbrev-ref", "HEAD"))
        if out(wt, "status", "--porcelain=v1"):
            raise Stop("worktree dirty before start")
        git(wt, "fetch", "origin", "--prune", "-q")
        base = out(wt, "rev-parse", "origin/main")
        head = out(wt, "rev-parse", "HEAD")
        if head != base:
            raise Stop("HEAD %s != origin/main %s" % (head[:12], base[:12]))
        print("BASE %s" % base)

        commits = 0
        files_total = 0
        for pkg in packages:
            src_root = os.path.join(src, pkg)
            if not os.path.isfile(os.path.join(src_root, "SKILL.md")):
                raise Stop("no SKILL.md in source: %s" % src_root)
            dest_root = os.path.join(wt, prefix.strip("/"), pkg)
            dest_real = os.path.realpath(dest_root)
            if not dest_real.startswith(wt_real + os.sep):
                raise Stop("destination escapes worktree: %s" % dest_root)

            pre = hash_all(src_root)
            if os.path.isdir(dest_root):
                shutil.rmtree(dest_root)
            os.makedirs(dest_root, exist_ok=True)
            for rel, full in enumerate_files(src_root).items():
                target = os.path.join(dest_root, rel.replace("/", os.sep))
                os.makedirs(os.path.dirname(target), exist_ok=True)
                shutil.copyfile(full, target)
            post = hash_all(src_root)
            copied = hash_all(dest_root)
            if pre != post:
                raise Stop("source changed during copy: %s" % pkg)
            if pre != copied:
                bad = sorted(set(pre) | set(copied))
                bad = [r for r in bad if pre.get(r) != copied.get(r)]
                raise Stop("copy mismatch: %s %s" % (pkg, ", ".join(bad[:5])))
            print("PKG %-46s files=%2d source_stable=True copy_identical=True" % (pkg, len(pre)))
            files_total += len(pre)

            if out(wt, "diff", "--cached", "--name-only"):
                raise Stop("index not clean before package %s" % pkg)
            git(wt, "add", "--", prefix + pkg)
            staged = [p for p in out(wt, "diff", "--cached", "--name-only").splitlines() if p]
            outside = [p for p in staged if not p.startswith(prefix + pkg + "/")]
            if outside:
                raise Stop("staged out of package %s: %s" % (pkg, outside[:3]))
            if not staged:
                print("SKIP_EMPTY %s (archive already identical)" % pkg)
                continue

            msg = args.message.format(pkg=pkg)
            git(wt, "commit", "-q", "-m", msg)
            head = out(wt, "rev-parse", "HEAD")
            parent = out(wt, "rev-parse", "HEAD^")
            origin = out(wt, "rev-parse", "origin/main")
            if parent != origin:
                raise Stop("parent %s != origin/main %s" % (parent[:12], origin[:12]))
            git(wt, "merge-base", "--is-ancestor", "origin/main", "HEAD")
            if args.no_push:
                print("COMMIT_ONLY %-38s files=%d commit=%s" % (pkg, len(staged), head[:8]))
                commits += 1
                continue
            git(wt, "push", "-q", "origin", "HEAD:main")
            git(wt, "fetch", "origin", "-q")
            if out(wt, "rev-parse", "HEAD") != out(wt, "rev-parse", "origin/main"):
                raise Stop("post-push HEAD != origin/main (foreign push?): %s" % pkg)
            print("OK %-42s files=%d commit=%s" % (pkg, len(staged), head[:8]))
            commits += 1

        print("TOTAL_PACKAGES %d COMMITS %d FILES %d" % (len(packages), commits, files_total))
        print("RESULT PASS")
        return 0
    except Stop as exc:
        print("STOP %s" % exc)
        print("RESULT STOP")
        return 2


if __name__ == "__main__":
    sys.exit(main())
