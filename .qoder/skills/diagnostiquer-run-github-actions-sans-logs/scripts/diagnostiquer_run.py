#!/usr/bin/env python3
"""Read-only diagnosis for a GitHub Actions run that never started.

Subcommand:
  run   report run/job state, log-blob availability and check-run annotations

Options:
  --repo owner/name   target repository (required)
  --run-id N          workflow run id (required)
  --anonymous         ignore stored credentials (reproduces the anonymous trap)
  --out-dir DIR       save raw API payloads as evidence copies

Exit codes:
  0  no-step stall reproduced AND cause text read from an annotation
  1  no-step stall reproduced but cause unproven, or a runner did start
  2  usage, repository, run or API error

Never clones, commits, pushes or prints a credential.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

USER_AGENT = "diagnostiquer-run-github-actions-sans-logs/1.0"
API = "https://api.github.com"
JSON_ACCEPT = "application/vnd.github+json"
BILLING_PHRASE = "account is locked due to a billing issue"


def emit(*parts):
    text = " ".join(str(part) for part in parts)
    sys.stdout.write(text.encode("ascii", "backslashreplace").decode("ascii") + "\n")
    sys.stdout.flush()


def fail(message, code=2):
    emit("ERROR", message)
    return code


def normalize_repo(value):
    v = value.strip()
    if v.startswith("git@"):
        match = re.match(r"git@github\.com:(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?$", v)
    else:
        match = re.match(
            r"(?:https?://github\.com/)?(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?/?$", v
        )
    if not match:
        return None, None
    return match.group("owner"), match.group("repo")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def fetch(url, accept=JSON_ACCEPT, token=None, follow=True, read_cap=None):
    handlers = [] if follow else [NoRedirect()]
    opener = urllib.request.build_opener(*handlers)
    headers = {"User-Agent": USER_AGENT, "Accept": accept}
    if token:
        headers["Authorization"] = "Bearer " + token
    request = urllib.request.Request(url, headers=headers)
    try:
        with opener.open(request, timeout=30) as response:
            body = response.read(read_cap) if read_cap else response.read()
            return response.status, dict(response.headers), body, None
    except urllib.error.HTTPError as exc:
        try:
            body = exc.read(read_cap) if read_cap else exc.read()
        except Exception:
            body = b""
        return exc.code, dict(exc.headers), body, None
    except Exception as exc:
        return None, {}, b"", "%s: %s" % (type(exc).__name__, exc)


def as_json(body):
    try:
        return json.loads(body.decode("utf-8")), None
    except Exception as exc:
        return None, "%s: %s" % (type(exc).__name__, exc)


def read_credential():
    """Return a token from the configured helper, or None. Never printed."""
    payload = "protocol=https\nhost=github.com\n\n"
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
    try:
        proc = subprocess.run(
            ["git", "-c", "credential.interactive=never", "credential", "fill"],
            input=payload,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            timeout=30,
        )
    except Exception as exc:
        return None, "%s: %s" % (type(exc).__name__, exc)
    if proc.returncode != 0:
        return None, "git credential fill exit %s" % proc.returncode
    for line in proc.stdout.splitlines():
        if line.startswith("password="):
            value = line[len("password=") :].strip()
            if value:
                return value, None
    return None, "no password in credential payload"


def save(out_dir, name, payload):
    if not out_dir or payload is None:
        return
    os.makedirs(out_dir, exist_ok=True)
    target = os.path.join(out_dir, name)
    with open(target, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def api_get(url, token, out_dir=None, name=None):
    status, headers, body, error = fetch(url, token=token)
    if error:
        return None, "network %s" % error, status
    data, parse_error = as_json(body)
    if parse_error:
        snippet = body.decode("utf-8", "replace")[:200]
        return None, "http %s unparsable (%s) %s" % (status, parse_error, snippet), status
    if status != 200:
        detail = ""
        if isinstance(data, dict):
            detail = str(data.get("message") or "")
        return None, "http %s %s" % (status, detail[:160]), status
    save(out_dir, name or "payload.json", data)
    return data, None, status


def log_availability(repo_api, job_id, token, out_dir):
    """Report whether a log blob exists, without downloading a real archive."""
    url = "%s/actions/jobs/%s/logs" % (repo_api, job_id)
    status, headers, _body, error = fetch(url, token=token, follow=False)
    emit("LOGS_HTTP", status if status is not None else "ERR", "(token)" if token else "(anonymous)")
    if error:
        emit("LOGS_ERROR", error)
        return "unknown"
    if status in (301, 302, 303, 307, 308):
        location = headers.get("Location") or headers.get("location")
        if not location:
            emit("LOGS_BLOB", "redirect-without-location")
            return "unknown"
        blob_status, _blob_headers, blob_body, blob_error = fetch(
            location, accept="*/*", follow=False, read_cap=4096
        )
        if blob_error:
            emit("LOGS_BLOB_HTTP", "ERR")
            emit("LOGS_BLOB", "unknown")
            return "unknown"
        emit("LOGS_BLOB_HTTP", blob_status)
        code = re.search(rb"<Code>([^<]+)</Code>", blob_body)
        if code:
            emit("LOGS_BLOB_CODE", code.group(1).decode("ascii", "replace"))
        if blob_body.lstrip().startswith(b"PK"):
            emit("LOGS_BLOB", "zip-present")
            return "present"
        if blob_status == 404:
            emit("LOGS_BLOB", "absent")
            return "absent"
        emit("LOGS_BLOB", "unknown")
        return "unknown"
    if status == 200:
        emit("LOGS_BLOB", "zip-present")
        return "present"
    if status == 403:
        emit("LOGS_BLOB", "forbidden-anonymous" if not token else "forbidden")
        return "forbidden"
    emit("LOGS_BLOB", "unknown")
    return "unknown"


def annotation_messages(annotations):
    messages = []
    for item in annotations:
        text = str(item.get("message") or "").replace("\r", " ").replace("\n", " ")
        messages.append((item.get("annotation_level"), text))
    return messages


def cmd_run(args):
    owner, repo = normalize_repo(args.repo)
    if not owner:
        return fail("REPO_INVALID %s" % args.repo)

    token, token_error = (None, "anonymous mode")
    if not args.anonymous:
        token, token_error = read_credential()
    emit("AUTH", "yes" if token else "no")
    if token_error:
        emit("AUTH_DETAIL", token_error)

    repo_api = "%s/repos/%s/%s" % (API, owner, repo)

    run, error, _status = api_get(
        "%s/actions/runs/%s" % (repo_api, args.run_id), token, args.out_dir, "run.json"
    )
    if error:
        return fail("FETCH run %s" % error)

    jobs_payload, error, _status = api_get(
        "%s/actions/runs/%s/jobs?per_page=100" % (repo_api, args.run_id),
        token,
        args.out_dir,
        "jobs.json",
    )
    if error:
        return fail("FETCH jobs %s" % error)

    head_sha = run.get("head_sha") or ""
    emit("RUN", run.get("id"), run.get("name"), head_sha[:7], run.get("status"), run.get("conclusion"))
    emit("CREATED", run.get("created_at"))
    emit("UPDATED", run.get("updated_at"))
    emit("ATTEMPT", run.get("run_attempt"))
    emit("HTML_URL", run.get("html_url"))

    jobs = jobs_payload.get("jobs") or []
    any_steps = False
    jobs_without_steps = []
    for job in jobs:
        steps = job.get("steps") or []
        if steps:
            any_steps = True
        else:
            jobs_without_steps.append(job)
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
            "COMPLETED",
            job.get("completed_at"),
        )

    log_state = "unknown"
    if jobs:
        log_state = log_availability(repo_api, jobs[0].get("id"), token, args.out_dir)

    checks, check_error, _status = (None, "no jobs", None)
    if jobs and head_sha:
        checks, check_error, _status = api_get(
            "%s/commits/%s/check-runs?per_page=100" % (repo_api, head_sha),
            token,
            args.out_dir,
            "checks.json",
        )

    annotations = []
    annotations_count = None
    anon_count = None
    if checks:
        for check in checks.get("check_runs") or []:
            output = check.get("output") or {}
            emit(
                "CHECK",
                check.get("id"),
                check.get("name"),
                check.get("status"),
                check.get("conclusion"),
                "ANNOTATIONS_COUNT",
                output.get("annotations_count"),
            )
        for job in jobs:
            match = None
            for check in checks.get("check_runs") or []:
                if str(check.get("id")) == str(job.get("id")) or check.get("name") == job.get("name"):
                    match = check
                    break
            if not match:
                continue
            output = match.get("output") or {}
            annotations_count = output.get("annotations_count")
            annotations_url = output.get("annotations_url") or (
                "%s/check-runs/%s/annotations" % (repo_api, match.get("id"))
            )
            payload, fetch_error, _status = api_get(
                annotations_url, token, args.out_dir, "annotations.json"
            )
            if fetch_error:
                emit("ANNOTATIONS_FETCH", fetch_error)
            elif isinstance(payload, list):
                annotations = payload
            if token:
                anon_status, _h, anon_body, anon_error = fetch(annotations_url)
                if anon_error:
                    emit("ANNOTATIONS_ANON_HTTP", "ERR")
                else:
                    emit("ANNOTATIONS_ANON_HTTP", anon_status)
                    anon_data, _ = as_json(anon_body)
                    if isinstance(anon_data, list):
                        anon_count = len(anon_data)
                        emit("ANNOTATIONS_ANON_COUNT", anon_count)
            break

    emit("ANNOTATIONS_COUNT", len(annotations) if annotations else 0)
    if token and anon_count is not None and anon_count != len(annotations):
        emit("ANNOTATIONS_ANON_NOTE", "anonymous %s, authenticated %s" % (anon_count, len(annotations)))
    if annotations_count is not None and len(annotations) != annotations_count:
        emit("ANNOTATIONS_NOTE", "check-run reports %s, endpoint returned %s" % (annotations_count, len(annotations)))

    messages = annotation_messages(annotations)
    for index, (level, text) in enumerate(messages, start=1):
        emit("ANNOTATION", index, level, text)

    hint = "none"
    joined = " ".join(text.lower() for _level, text in messages)
    if BILLING_PHRASE in joined:
        hint = "billing_lock"
    elif "not started" in joined:
        hint = "no-runner-reason"
    elif messages:
        hint = "other"
    emit("CAUSE_HINT", hint)

    if check_error:
        emit("CHECKS_NOTE", check_error)

    if any_steps:
        emit("CLASS", "RUN_HAS_STEPS")
        emit("HINT", "a runner dispatched steps; read job steps and logs instead")
        return 1
    if annotations:
        emit("CLASS", "NO_STEPS_CAUSE_PROVEN")
        if hint == "billing_lock":
            emit("HINT", "account-level billing block proven by annotation; code and YAML are not implicated")
        else:
            emit("HINT", "cause text read from annotation; quote it before concluding")
        return 0
    emit("CLASS", "NO_STEPS_CAUSE_UNPROVEN")
    if log_state == "absent":
        emit(
            "HINT",
            "no log blob and no readable annotation; annotations propagate late, retry the authenticated check-run before naming a cause",
        )
    elif log_state == "forbidden":
        emit(
            "HINT",
            "log access forbidden without credentials; confirm BlobNotFound with a token before claiming the log is absent",
        )
    else:
        emit("HINT", "no step and no readable annotation; rerun with credentials or inspect the check-run later")
    return 1


def build_parser():
    parser = argparse.ArgumentParser(
        description="Read-only diagnosis of a GitHub Actions run that never started."
    )
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="inspect run, job, log blob and check-run annotations")
    run.add_argument("--repo", required=True, help="owner/name or GitHub URL")
    run.add_argument("--run-id", required=True, help="workflow run id")
    run.add_argument(
        "--anonymous",
        action="store_true",
        help="ignore stored credentials and reproduce the anonymous trap",
    )
    run.add_argument("--out-dir", default=None, help="directory for raw JSON evidence copies")
    run.set_defaults(func=cmd_run)
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
