#!/usr/bin/env python3
"""Create and merge GitHub pull requests with credentials from git credential fill.

Read-only commands: probe, status.
Mutating commands: create, merge (both require --yes).
Only github.com is supported. The token is never printed or written to disk.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API_ROOT = "https://api.github.com"
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


def brief(value, limit=300):
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    return text[:limit].replace("\n", " ")


def refuse(message):
    print(message)
    return 2


def credentials():
    env = dict(os.environ)
    env["GIT_TERMINAL_PROMPT"] = "0"
    try:
        proc = subprocess.run(
            ["git", "credential", "fill"],
            input="protocol=https\nhost=github.com\n\n",
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=30,
            env=env,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"CREDENTIAL_FAIL {type(exc).__name__}: {exc}")
        return None
    if proc.returncode != 0:
        print(f"CREDENTIAL_FAIL exit={proc.returncode}")
        return None
    fields = {}
    for line in proc.stdout.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            fields[key] = value
    user = fields.get("username", "")
    password = fields.get("password", "")
    if not user or not password:
        print("CREDENTIAL_FAIL missing username or password")
        return None
    return user, password


def api(method, path, token, payload=None):
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "qoder-github-pr",
    }
    data = None
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(API_ROOT + path, method=method, headers=headers, data=data)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            raw = response.read().decode("utf-8", "replace")
            return response.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", "replace")
        try:
            body = json.loads(raw)
        except ValueError:
            body = raw
        return exc.code, body
    except urllib.error.URLError as exc:
        return 0, f"NETWORK_FAIL {exc.reason}"


def check_repo(repo):
    if not REPO_RE.match(repo):
        print("REPO_FAIL expected owner/name")
        return False
    return True


def open_pulls(repo, user, head, token):
    query = urllib.parse.urlencode(
        {"state": "open", "head": f"{user}:{head}"}, quote_via=urllib.parse.quote
    )
    status, pulls = api("GET", f"/repos/{repo}/pulls?{query}", token)
    if status != 200:
        print(f"PULLS_FAIL status={status} body={brief(pulls)}")
        return None
    if not isinstance(pulls, list):
        print(f"PULLS_FAIL unexpected body={brief(pulls)}")
        return None
    return pulls


def print_pull(pull):
    base = pull.get("base") or {}
    head = pull.get("head") or {}
    print(f"PR_STATE {pull.get('state')} PR_MERGED {pull.get('merged')} PR_MERGEABLE {pull.get('mergeable')}")
    print(f"PR_BASE {base.get('ref')} PR_HEAD {head.get('ref')} PR_HEAD_SHA {head.get('sha')}")
    print(f"PR_MERGE_COMMIT {pull.get('merge_commit_sha')} PR_URL {pull.get('html_url')}")


def remote_main(repo, base_ref, token):
    encoded = urllib.parse.quote(base_ref, safe="")
    status, ref = api("GET", f"/repos/{repo}/git/ref/heads/{encoded}", token)
    if status != 200:
        print(f"REMOTE_MAIN_FAIL status={status} body={brief(ref)}")
        return None
    sha = ((ref or {}).get("object") or {}).get("sha")
    print(f"REMOTE_MAIN {sha}")
    return sha


def cmd_probe(args):
    if not check_repo(args.repo):
        return 2
    creds = credentials()
    if creds is None:
        return 2
    user, token = creds
    print(f"CREDENTIAL_USER {user}")

    status, repo = api("GET", f"/repos/{args.repo}", token)
    if status != 200:
        print(f"REPO_FAIL status={status} body={brief(repo)}")
        return 2
    perms = repo.get("permissions") or {}
    print(f"REPO {repo.get('full_name')} default={repo.get('default_branch')}")
    print(
        "PERMISSIONS "
        f"admin={perms.get('admin')} maintain={perms.get('maintain')} "
        f"push={perms.get('push')} triage={perms.get('triage')} pull={perms.get('pull')}"
    )
    print(
        "MERGE_METHODS "
        f"merge={repo.get('allow_merge_commit')} "
        f"squash={repo.get('allow_squash_merge')} "
        f"rebase={repo.get('allow_rebase_merge')}"
    )

    pulls = open_pulls(args.repo, user, args.head, token)
    if pulls is None:
        return 2
    print(f"OPEN_PRS {len(pulls)}")
    for pull in pulls:
        base = pull.get("base") or {}
        head = pull.get("head") or {}
        print(
            f"PR {pull.get('number')} {pull.get('html_url')} "
            f"base={base.get('ref')} head_sha={head.get('sha')}"
        )
    return 0


def cmd_create(args):
    if not args.yes:
        return refuse("CREATE_REFUSED add --yes after explicit user authorization")
    if not check_repo(args.repo):
        return 2
    if not args.title.strip():
        return refuse("CREATE_FAIL empty title")
    body = args.body or ""
    if args.body_file:
        try:
            with open(args.body_file, encoding="utf-8") as handle:
                body = handle.read()
        except OSError as exc:
            return refuse(f"CREATE_FAIL body file: {exc}")

    creds = credentials()
    if creds is None:
        return 2
    user, token = creds
    print(f"CREDENTIAL_USER {user}")

    pulls = open_pulls(args.repo, user, args.head, token)
    if pulls is None:
        return 2
    if pulls:
        pull = pulls[0]
        print(f"PR_EXISTING {pull.get('number')} {pull.get('html_url')} state={pull.get('state')}")
    else:
        payload = {"title": args.title, "head": args.head, "base": args.base, "body": body}
        status, pull = api("POST", f"/repos/{args.repo}/pulls", token, payload)
        if status not in (200, 201):
            print(f"PR_CREATE_FAIL status={status} body={brief(pull, 500)}")
            return 2
        if not isinstance(pull, dict):
            print(f"PR_CREATE_FAIL unexpected body={brief(pull)}")
            return 2
        print(f"PR_CREATED {pull.get('number')} {pull.get('html_url')} state={pull.get('state')}")

    base = pull.get("base") or {}
    head = pull.get("head") or {}
    print(f"PR_BASE {base.get('ref')} PR_HEAD {head.get('ref')} SHA {head.get('sha')}")
    return 0


def cmd_merge(args):
    if not args.yes:
        return refuse("MERGE_REFUSED add --yes after explicit user authorization")
    if not check_repo(args.repo):
        return 2
    creds = credentials()
    if creds is None:
        return 2
    user, token = creds
    print(f"CREDENTIAL_USER {user}")

    status, pull = api("GET", f"/repos/{args.repo}/pulls/{args.pr}", token)
    if status != 200:
        print(f"PR_GET_FAIL status={status} body={brief(pull)}")
        return 2
    if not isinstance(pull, dict):
        print(f"PR_GET_FAIL unexpected body={brief(pull)}")
        return 2

    number = pull.get("number")
    if pull.get("merged"):
        print(f"ALREADY_MERGED {number}")
        print_pull(pull)
        base_ref = (pull.get("base") or {}).get("ref")
        if base_ref:
            remote_main(args.repo, base_ref, token)
        return 0
    if pull.get("state") != "open":
        print(f"PR_NOT_OPEN state={pull.get('state')} merged={pull.get('merged')}")
        return 2

    mergeable = None
    for _ in range(15):
        status, check = api("GET", f"/repos/{args.repo}/pulls/{number}", token)
        if status == 200 and isinstance(check, dict):
            mergeable = check.get("mergeable")
            if mergeable is not None:
                print(f"PR_MERGEABLE {mergeable} state={check.get('state')}")
                break
        time.sleep(2)
    if mergeable is None:
        print("MERGEABLE_TIMEOUT after 15 checks")
        return 2
    if mergeable is False:
        print("MERGE_ABORT mergeable=false")
        return 2

    payload = {"merge_method": args.method}
    if args.commit_title:
        payload["commit_title"] = args.commit_title
    status, merged = api("PUT", f"/repos/{args.repo}/pulls/{number}/merge", token, payload)
    merged_ok = status == 200 and isinstance(merged, dict) and merged.get("merged") is True
    print(
        f"MERGE_{args.method.upper()} status={status} "
        f"merged={merged.get('merged') if isinstance(merged, dict) else '?'} "
        f"sha={merged.get('sha') if isinstance(merged, dict) else '?'}"
    )
    if not merged_ok:
        print(f"MERGE_FAIL status={status} message={brief(merged)}")
        return 2
    print(f"MERGE_OK sha={merged.get('sha')}")

    status, final = api("GET", f"/repos/{args.repo}/pulls/{number}", token)
    if status == 200 and isinstance(final, dict):
        print(
            f"PR_FINAL state={final.get('state')} merged={final.get('merged')} "
            f"merge_commit_sha={final.get('merge_commit_sha')} url={final.get('html_url')}"
        )
        base_ref = (final.get("base") or {}).get("ref") or "main"
    else:
        print(f"PR_FINAL_FAIL status={status} body={brief(final)}")
        base_ref = "main"

    main_sha = remote_main(args.repo, base_ref, token)
    if main_sha is None:
        return 2
    match = bool(merged.get("sha")) and merged.get("sha") == main_sha
    print(f"VERIFY_MATCH {str(match).lower()}")
    return 0 if match else 2


def cmd_status(args):
    if not check_repo(args.repo):
        return 2
    creds = credentials()
    if creds is None:
        return 2
    user, token = creds
    print(f"CREDENTIAL_USER {user}")

    status, pull = api("GET", f"/repos/{args.repo}/pulls/{args.pr}", token)
    if status != 200:
        print(f"PR_GET_FAIL status={status} body={brief(pull)}")
        return 2
    if not isinstance(pull, dict):
        print(f"PR_GET_FAIL unexpected body={brief(pull)}")
        return 2
    print_pull(pull)
    base_ref = (pull.get("base") or {}).get("ref")
    if base_ref:
        remote_main(args.repo, base_ref, token)
    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        description="Create, merge and inspect GitHub pull requests without gh."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    probe = sub.add_parser("probe", help="read-only repository, permissions and open PR probe")
    probe.add_argument("--repo", required=True, help="owner/name")
    probe.add_argument("--head", required=True, help="head branch")
    probe.set_defaults(func=cmd_probe)

    create = sub.add_parser("create", help="create a PR, reusing an open PR for the same head")
    create.add_argument("--repo", required=True, help="owner/name")
    create.add_argument("--head", required=True, help="head branch")
    create.add_argument("--base", required=True, help="base branch")
    create.add_argument("--title", required=True, help="PR title")
    body = create.add_mutually_exclusive_group()
    body.add_argument("--body", help="PR body text")
    body.add_argument("--body-file", help="UTF-8 file containing the PR body")
    create.add_argument("--yes", action="store_true", help="confirm explicit authorization")
    create.set_defaults(func=cmd_create)

    merge = sub.add_parser("merge", help="merge a PR after polling mergeable")
    merge.add_argument("--repo", required=True, help="owner/name")
    merge.add_argument("--pr", required=True, type=int, help="PR number")
    merge.add_argument("--method", choices=("rebase", "squash", "merge"), default="rebase")
    merge.add_argument("--commit-title", help="optional commit title")
    merge.add_argument("--yes", action="store_true", help="confirm explicit authorization")
    merge.set_defaults(func=cmd_merge)

    status = sub.add_parser("status", help="read-only PR and main status")
    status.add_argument("--repo", required=True, help="owner/name")
    status.add_argument("--pr", required=True, type=int, help="PR number")
    status.set_defaults(func=cmd_status)
    return parser


def main():
    args = build_parser().parse_args()
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("ABORTED keyboard interrupt")
        return 2
    except Exception as exc:
        print(f"ERROR {type(exc).__name__}: {exc}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
