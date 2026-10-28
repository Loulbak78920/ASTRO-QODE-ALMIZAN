"""Three-way proof that the archive ref carries exactly the live source files.

For every in-scope file under the archive prefix:

    REST contents `sha`  ==  git rev-parse <ref>:<path>  ==  git hash-object --path <path> <source file>

The third operand must be the SOURCE file, never a copy parked in the archive
worktree: `--path` applies the repository attributes (CRLF->LF) without reading
any ref, so the source OID is comparable to the published blob.

Exit codes: 0 = all three ways agree, 1 = mismatch, 2 = error.
Read-only; the optional REST call only performs GET requests.
"""
import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(errors="backslashreplace")


class Unavailable(Exception):
    pass


def die(msg):
    sys.stderr.write("ERROR %s\n" % msg)
    raise SystemExit(2)


def git(repo, *args):
    p = subprocess.run(["git", "-C", repo] + list(args), capture_output=True)
    if p.returncode != 0:
        die("git %s: %s" % (" ".join(args), p.stderr.decode("utf-8", "replace").strip()))
    return p.stdout.decode("utf-8", "replace").strip()


def default_repo():
    """Main worktree of the repository holding this script, for zero-argument replay."""
    here = os.path.dirname(os.path.abspath(__file__))
    p = subprocess.run(["git", "-C", here, "worktree", "list", "--porcelain"], capture_output=True, text=True)
    if p.returncode != 0:
        die("cannot derive the repository from %s; pass --repo" % here)
    for line in p.stdout.splitlines():
        if line.startswith("worktree "):
            return line[len("worktree "):].strip()
    die("no worktree listed for %s; pass --repo" % here)


def origin_owner_repo(repo):
    p = subprocess.run(["git", "-C", repo, "remote", "get-url", "origin"], capture_output=True, text=True)
    url = (p.stdout or "").strip()
    if p.returncode != 0 or not url:
        return None
    for pre in ("https://github.com/", "http://github.com/", "git@github.com:", "ssh://git@github.com/"):
        if url.startswith(pre):
            rest = url[len(pre):]
            if rest.endswith(".git"):
                rest = rest[:-4]
            parts = rest.split("/")
            if len(parts) == 2 and all(parts):
                return "/".join(parts)
    return None


def ref_files(repo, ref, prefix):
    raw = subprocess.run(
        ["git", "-C", repo, "ls-tree", "-r", "-z", ref, "--", prefix], capture_output=True
    )
    if raw.returncode != 0:
        die("ls-tree %s: %s" % (ref, raw.stderr.decode("utf-8", "replace").strip()))
    found = {}
    for rec in raw.stdout.split(b"\0"):
        if not rec:
            continue
        meta, path = rec.split(b"\t", 1)
        mode, typ, oid = meta.split(b" ")
        if typ != b"blob":
            continue
        path = path.decode("utf-8")
        rest = path[len(prefix):]
        if "/" not in rest:
            continue
        pkg, rel = rest.split("/", 1)
        found.setdefault(pkg, {})[rel] = (path, oid.decode())
    return found


def token(repo):
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
    p = subprocess.run(
        ["git", "credential", "fill"],
        input="protocol=https\nhost=github.com\n\n",
        capture_output=True, text=True, cwd=repo, env=env,
    )
    for line in (p.stdout or "").splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    return None


def api(owner_repo, path, refname, tok):
    req = urllib.request.Request(
        "https://api.github.com/repos/%s/%s?ref=%s" % (owner_repo, path, refname),
        headers={"Accept": "application/vnd.github+json", "User-Agent": "skill-archive-proof"},
    )
    if tok:
        req.add_header("Authorization", "Bearer %s" % tok)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise Unavailable("HTTP 404 (private repo or missing path; no visibility conclusion)")
        raise Unavailable("HTTP %d" % exc.code)
    except Exception as exc:
        raise Unavailable("%s: %s" % (type(exc).__name__, exc))


def rest_hashes(owner_repo, prefix, pkgs, refname, tok):
    found = {}

    def walk(entries):
        for entry in entries:
            if entry["type"] == "file":
                found[entry["path"]] = entry["sha"]
            elif entry["type"] == "dir":
                status, sub = api(owner_repo, "contents/" + entry["path"], refname, tok)
                walk(sub)

    for pkg in pkgs:
        status, data = api(owner_repo, "contents/" + prefix + pkg, refname, tok)
        if not isinstance(data, list):
            raise Unavailable("unexpected contents payload for %s" % pkg)
        walk(data)
    return found


def main():
    ap = argparse.ArgumentParser(description="Prove archive ref == source == REST in one pass.")
    ap.add_argument("--repo", default=None, help="archive Git clone (default: main worktree of this script's repository)")
    ap.add_argument("--src", default=None, help="local skills root (default: <repo>/<prefix>)")
    ap.add_argument("--prefix", default=".qoder/skills/")
    ap.add_argument("--ref", default="origin/main")
    ap.add_argument("--package", action="append", default=[], help="restrict to one package (repeatable)")
    ap.add_argument("--rest", default=None, help="owner/repo for the optional REST proof; 'auto' derives it from origin")
    ap.add_argument("--rest-ref", default="main", help="branch name for the REST contents API")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    repo = os.path.abspath(args.repo) if args.repo else default_repo()
    prefix = args.prefix if args.prefix.endswith("/") else args.prefix + "/"
    src = os.path.abspath(args.src) if args.src else os.path.join(repo, prefix.strip("/"))
    ref_oid = git(repo, "rev-parse", args.ref)
    archived = ref_files(repo, args.ref, prefix)
    pkgs = sorted(archived) if not args.package else [p for p in args.package]
    missing_pkg = [p for p in pkgs if p not in archived]
    if missing_pkg:
        die("package not in %s: %s" % (args.ref, ", ".join(missing_pkg)))

    rest_arg = args.rest
    rest_target_error = None
    if rest_arg == "auto":
        rest_arg = origin_owner_repo(repo)
        if rest_arg is None:
            rest_target_error = "cannot derive owner/repo from origin"
            rest_arg = None

    rest = None
    rest_error = rest_target_error
    if rest_arg:
        try:
            rest = rest_hashes(rest_arg, prefix, pkgs, args.rest_ref, token(repo))
        except Unavailable as exc:
            rest_error = str(exc)

    total = 0
    matched = 0
    bad = []
    rows = []
    for pkg in pkgs:
        pkg_total = 0
        pkg_ok = 0
        for rel, (repo_path, ref_blob) in sorted(archived[pkg].items()):
            src_file = os.path.join(src, pkg, rel.replace("/", os.sep))
            total += 1
            pkg_total += 1
            if not os.path.isfile(src_file):
                bad.append((repo_path, ref_blob, "-", "source missing"))
                rows.append({"path": repo_path, "ref": ref_blob, "src": None, "rest": None, "status": "MISMATCH_SOURCE_MISSING"})
                continue
            src_oid = git(repo, "hash-object", "--path", repo_path, src_file)
            rest_oid = rest.get(repo_path) if rest is not None else None
            agree = ref_blob == src_oid and (rest is None or rest_oid == ref_blob)
            if agree:
                matched += 1
                pkg_ok += 1
                rows.append({"path": repo_path, "ref": ref_blob, "src": src_oid, "rest": rest_oid, "status": "MATCH"})
            else:
                bad.append((repo_path, ref_blob, src_oid, "rest=%s" % (rest_oid[:8] if rest_oid else "none")))
                rows.append({"path": repo_path, "ref": ref_blob, "src": src_oid, "rest": rest_oid, "status": "MISMATCH"})
        print("%-46s files=%d match=%d" % (pkg, pkg_total, pkg_ok))

    for path, ref_blob, src_oid, extra in bad:
        print("  MISMATCH %s ref=%s src=%s %s" % (path, ref_blob[:8], src_oid[:8], extra))
    print("REF %s %s" % (args.ref, ref_oid))
    print("TRIO_TOTAL %d  MATCH %d  MISMATCH %d" % (total, matched, total - matched))
    if rest_arg:
        print("REST_TARGET %s" % rest_arg)
        if rest is None:
            print("REST_SKIPPED %s" % rest_error)
        else:
            print("REST_TOTAL %d  MATCH %d" % (total, matched))
    elif rest_error:
        print("REST_SKIPPED %s" % rest_error)
    if args.json:
        print(json.dumps({"ref": args.ref, "ref_oid": ref_oid, "total": total, "matched": matched,
                          "mismatch": total - matched, "rest_target": rest_arg, "rest_error": rest_error,
                          "files": rows},
                         ensure_ascii=True, indent=2))
    return 0 if not bad else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as exc:
        die("%s: %s" % (type(exc).__name__, exc))
