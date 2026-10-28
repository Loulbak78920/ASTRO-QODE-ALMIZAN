"""Read-only drift inventory: local Skill sources vs an archive ref.

Scope = SKILL.md, references/**, scripts/**. Local blob OIDs are computed with
the CRLF->LF normalization used by the archive's text attributes, so a CRLF
worktree file compares equal to its LF blob.

Exit codes: 0 = no drift, 1 = drift (DIFF, MISSING or EXTRA), 2 = error.
Never writes to either tree.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(errors="backslashreplace")


def die(msg):
    sys.stderr.write("ERROR %s\n" % msg)
    raise SystemExit(2)


def git(repo, *args):
    p = subprocess.run(["git", "-C", repo] + list(args), capture_output=True)
    if p.returncode != 0:
        die("git %s: %s" % (" ".join(args), p.stderr.decode("utf-8", "replace").strip()))
    return p.stdout


def blob_oid(path):
    with open(path, "rb") as fh:
        data = fh.read()
    if b"\r\n" in data:
        data = data.replace(b"\r\n", b"\n")
    h = hashlib.sha1()
    h.update(b"blob %d\0" % len(data))
    h.update(data)
    return h.hexdigest()


def in_scope(rel):
    return rel == "SKILL.md" or rel.startswith("references/") or rel.startswith("scripts/")


def local_files(root):
    found = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in (".git", "__pycache__", ".qoder"))
        for fn in sorted(filenames):
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, root).replace("\\", "/")
            if in_scope(rel):
                found[rel] = (full, blob_oid(full))
    return found


def archive_index(repo, ref, prefix):
    raw = git(repo, "ls-tree", "-r", "-z", ref, "--", prefix)
    index = {}
    for rec in raw.split(b"\0"):
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
        name, rel = rest.split("/", 1)
        index.setdefault(name, {})[rel] = oid.decode()
    return index


def main():
    ap = argparse.ArgumentParser(description="Read-only drift inventory between a Skill source root and an archive ref.")
    ap.add_argument("--repo", required=True, help="archive Git clone")
    ap.add_argument("--src", required=True, help="local skills root (contains <pkg>/SKILL.md)")
    ap.add_argument("--prefix", default=".qoder/skills/", help="archive directory prefix (default: .qoder/skills/)")
    ap.add_argument("--ref", default="origin/main", help="archive ref (default: origin/main)")
    ap.add_argument("--json", action="store_true", help="emit one JSON object")
    args = ap.parse_args()

    repo = os.path.abspath(args.repo)
    src = os.path.abspath(args.src)
    prefix = args.prefix if args.prefix.endswith("/") else args.prefix + "/"
    if not os.path.isdir(src):
        die("source root not found: %s" % src)

    ref_oid = git(repo, "rev-parse", args.ref).decode().strip()
    archived = archive_index(repo, args.ref, prefix)

    local_names = []
    no_skillmd = []
    for name in sorted(os.listdir(src)):
        root = os.path.join(src, name)
        if not os.path.isdir(root):
            continue
        if os.path.isfile(os.path.join(root, "SKILL.md")):
            local_names.append(name)
        else:
            no_skillmd.append(name)

    drift = []
    same = 0
    extra_only = 0
    only_local = []
    counts = {"diff": 0, "missing": 0, "extra": 0, "compared": 0}
    for name in local_names:
        if name not in archived:
            only_local.append(name)
            continue
        counts["compared"] += 1
        local = local_files(os.path.join(src, name))
        arc = archived[name]
        diffs, missing, extra = [], [], []
        for rel, (full, oid) in sorted(local.items()):
            if rel not in arc:
                extra.append((rel, oid))
            elif oid != arc[rel]:
                diffs.append((rel, oid, arc[rel]))
        for rel in sorted(arc):
            if rel not in local:
                missing.append((rel, arc[rel]))
        if diffs or missing or extra:
            extra_only += 1 if (extra and not diffs and not missing) else 0
            drift.append((name, diffs, missing, extra))
        else:
            same += 1
        counts["diff"] += len(diffs)
        counts["missing"] += len(missing)
        counts["extra"] += len(extra)

    only_archive = sorted(set(archived) - set(local_names))

    if args.json:
        doc = {
            "repo": repo, "src": src, "ref": args.ref, "ref_oid": ref_oid,
            "counts": {
                "drift_packages": len(drift), "same_packages": same,
                "compared_packages": counts["compared"], "files_diff": counts["diff"],
                "files_missing": counts["missing"], "files_extra": counts["extra"],
                "extra_only_packages": extra_only, "local_only_packages": len(only_local),
                "archive_only_packages": len(only_archive),
                "local_dirs_without_skillmd": len(no_skillmd),
            },
            "packages": [
                {
                    "name": name,
                    "diffs": [{"rel": r, "local": l[:8], "archive": a[:8]} for r, l, a in diffs],
                    "missing": [{"rel": r, "archive": a[:8]} for r, a in missing],
                    "extra": [{"rel": r, "local": l[:8]} for r, l in extra],
                }
                for name, diffs, missing, extra in drift
            ],
            "local_only": only_local,
            "archive_only": only_archive,
            "local_dirs_without_skillmd": no_skillmd,
        }
        sys.stdout.write(json.dumps(doc, ensure_ascii=True, indent=2) + "\n")
        return 0 if not drift else 1

    print("ARCHIVE_REF %s %s" % (args.ref, ref_oid))
    print("SCOPE_DRIFT_PACKAGES %d" % len(drift))
    print("SCOPE_DRIFT_FILES diff=%d missing=%d extra=%d" % (counts["diff"], counts["missing"], counts["extra"]))
    print("SCOPE_EXTRA_ONLY_PACKAGES %d" % extra_only)
    print("SCOPE_SAME_PACKAGES %d / %d" % (same, counts["compared"]))
    print("LOCAL_ONLY_PACKAGES %d" % len(only_local))
    print("ARCHIVE_ONLY_PACKAGES %d" % len(only_archive))
    print("LOCAL_DIRS_WITHOUT_SKILLMD %d" % len(no_skillmd))
    print("-" * 60)
    for name, diffs, missing, extra in drift:
        print("PACKAGE %s" % name)
        for rel, lok, rok in diffs:
            print("  DIFF    %s  local=%s archive=%s" % (rel, lok[:8], rok[:8]))
        for rel, rok in missing:
            print("  MISSING %s  archive=%s" % (rel, rok[:8]))
        for rel, lok in extra:
            print("  EXTRA   %s  local=%s" % (rel, lok[:8]))
    print("-" * 60)
    print("LOCAL_ONLY %s" % (" ".join(only_local) if only_local else "(none)"))
    print("ARCHIVE_ONLY %s" % (" ".join(only_archive) if only_archive else "(none)"))
    return 0 if not drift else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as exc:
        die("%s: %s" % (type(exc).__name__, exc))
