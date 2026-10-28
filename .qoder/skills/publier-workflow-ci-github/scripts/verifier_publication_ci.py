#!/usr/bin/env python3
"""Read-only checks around publishing a GitHub Actions workflow file.

Subcommands:
  refs    show the remote branch OID (git ls-remote)
  guards  list hashFiles() guards in a workflow and whether targets exist
  raw     download the published file and compare it byte-for-byte
  run     show a workflow run/job state and classify scheduler stalls

Never clones, never commits, never pushes.
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

USER_AGENT = "publier-workflow-ci-github/1.0"


def emit(*parts):
    print(*parts)


def normalize_repo(value):
    v = value.strip()
    if v.startswith("git@"):
        m = re.match(r"git@github\.com:(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?$", v)
    else:
        m = re.match(
            r"(?:https?://github\.com/)?(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?/?$",
            v,
        )
    if not m:
        raise SystemExit("REPO_INVALID %s" % value)
    return m.group("owner"), m.group("repo")


def http_get(url, accept, timeout=30):
    req = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT, "Accept": accept}
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read()


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def cmd_refs(args):
    if args.repo.startswith(("git@", "ssh://")):
        remote = args.repo
    else:
        owner, repo = normalize_repo(args.repo)
        remote = "https://github.com/%s/%s.git" % (owner, repo)
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
    proc = subprocess.run(
        ["git", "ls-remote", remote, "refs/heads/" + args.branch],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    if proc.returncode != 0:
        emit("GIT_RC", proc.returncode)
        emit("GIT_STDERR", proc.stderr.strip()[:500])
        return 2
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    if not lines:
        emit("MISSING_BRANCH", args.branch)
        return 1
    oid, ref = lines[0].split()[:2]
    emit("OID", oid)
    emit("REF", ref)
    return 0


GUARD_RE = re.compile(r"hashFiles\s*\(([^)]*)\)")
PATH_RE = re.compile(r"""['"]([^'"]+)['"]""")


def cmd_guards(args):
    workflow = args.workflow
    workflow_abs = (
        workflow if os.path.isabs(workflow) else os.path.join(args.dir, workflow)
    )
    if not os.path.isfile(workflow_abs):
        emit("WORKFLOW_MISSING", workflow_abs)
        return 2
    with open(workflow_abs, encoding="utf-8", errors="replace") as handle:
        text = handle.read()
    total = 0
    for match in GUARD_RE.finditer(text):
        line = text.count("\n", 0, match.start()) + 1
        paths = PATH_RE.findall(match.group(1))
        if not paths:
            emit("GUARD", line, "NO_PATH_PATTERN")
            continue
        for relative in paths:
            target = os.path.join(args.dir, relative)
            state = "PRESENT" if os.path.exists(target) else "ABSENT"
            emit("GUARD", line, relative, state)
            total += 1
    emit("GUARDS_TOTAL", total)
    if total == 0:
        emit("NO_GUARDS")
    return 0


def cmd_raw(args):
    owner, repo = normalize_repo(args.repo)
    path = args.path.lstrip("/")
    url = "https://raw.githubusercontent.com/%s/%s/%s/%s" % (
        owner,
        repo,
        args.branch,
        path,
    )
    try:
        data = http_get(url, "text/plain; charset=utf-8")
    except urllib.error.HTTPError as exc:
        emit("HTTP_ERROR", exc.code, url)
        return 2
    except Exception as exc:  # network, TLS, timeout
        emit("FETCH_ERROR", type(exc).__name__, str(exc)[:200])
        return 2
    emit("REMOTE_URL", url)
    emit("REMOTE_SHA256", sha256_bytes(data))
    emit("REMOTE_BYTES", len(data))
    if not os.path.isfile(args.local):
        emit("LOCAL_MISSING", args.local)
        return 2
    with open(args.local, "rb") as handle:
        local = handle.read()
    emit("LOCAL_SHA256", sha256_bytes(local))
    emit("LOCAL_BYTES", len(local))
    if data == local:
        emit("BYTES_EQUAL yes")
        emit("RESULT MATCH")
        return 0
    emit("BYTES_EQUAL no")
    emit("RESULT MISMATCH")
    return 1


def api_json(owner, repo, suffix):
    url = "https://api.github.com/repos/%s/%s%s" % (owner, repo, suffix)
    try:
        return json.loads(http_get(url, "application/vnd.github+json").decode("utf-8")), None
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")[:300]
        return None, "HTTP %s %s" % (exc.code, body)
    except Exception as exc:
        return None, "%s %s" % (type(exc).__name__, exc)


def cmd_run(args):
    owner, repo = normalize_repo(args.repo)
    run, err = api_json(owner, repo, "/actions/runs/%s" % args.run_id)
    if err:
        emit("FETCH_ERROR", "run", err)
        return 2
    jobs, err = api_json(owner, repo, "/actions/runs/%s/jobs" % args.run_id)
    if err:
        emit("FETCH_ERROR", "jobs", err)
        return 2

    emit(
        "RUN",
        run.get("id"),
        run.get("name"),
        (run.get("head_sha") or "")[:7],
        run.get("status"),
        run.get("conclusion"),
    )
    emit("CREATED", run.get("created_at"))
    emit("UPDATED", run.get("updated_at"))
    emit("URL", run.get("html_url"))

    job_list = jobs.get("jobs") or []
    zero_step_jobs = 0
    any_steps = False
    for job in job_list:
        steps = job.get("steps") or []
        if steps:
            any_steps = True
        else:
            zero_step_jobs += 1
        emit(
            "JOB",
            job.get("id"),
            job.get("name"),
            job.get("status"),
            job.get("conclusion"),
            "STEPS",
            len(steps),
            "STARTED",
            job.get("started_at"),
        )

    status = run.get("status")
    conclusion = run.get("conclusion")
    if status == "completed":
        if conclusion == "success":
            cls = "COMPLETED_SUCCESS"
        elif not job_list or not any_steps:
            cls = "COMPLETED_NO_STEPS"
        else:
            cls = "COMPLETED_FAILURE"
    elif status in ("queued", "waiting", "requested") and job_list and not any_steps:
        cls = "QUEUED_ZERO_STEPS"
    elif status == "in_progress" or any_steps:
        cls = "STARTED"
    else:
        cls = "UNKNOWN"
    emit("CLASS", cls)

    if cls == "QUEUED_ZERO_STEPS":
        emit(
            "HINT",
            "no step dispatched yet; do not report CI green; check account billing/scheduler state",
        )
    elif cls == "COMPLETED_NO_STEPS":
        emit(
            "HINT",
            "run failed without executing one step; scheduler-level block, not proof of a YAML error",
        )
    elif cls in ("COMPLETED_SUCCESS", "COMPLETED_FAILURE", "STARTED"):
        emit("HINT", "runner dispatched; read job steps and logs for the real verdict")
    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        description="Read-only verification for a published GitHub Actions workflow."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    refs = sub.add_parser("refs", help="show remote branch OID")
    refs.add_argument("--repo", required=True)
    refs.add_argument("--branch", default="main")
    refs.set_defaults(func=cmd_refs)

    guards = sub.add_parser("guards", help="list hashFiles guards and target presence")
    guards.add_argument("--dir", required=True, help="clone root")
    guards.add_argument("--workflow", required=True, help="workflow path inside the clone")
    guards.set_defaults(func=cmd_guards)

    raw = sub.add_parser("raw", help="compare published raw file with a local file")
    raw.add_argument("--repo", required=True)
    raw.add_argument("--branch", default="main")
    raw.add_argument("--path", required=True)
    raw.add_argument("--local", required=True)
    raw.set_defaults(func=cmd_raw)

    run = sub.add_parser("run", help="show run/job state and classify scheduler stalls")
    run.add_argument("--repo", required=True)
    run.add_argument("--run-id", required=True)
    run.set_defaults(func=cmd_run)

    return parser


def main(argv=None):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    except Exception:
        pass
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
