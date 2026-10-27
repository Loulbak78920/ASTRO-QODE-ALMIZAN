#!/usr/bin/env python3
"""Read-only GitHub repository and owner probe.

Reads a stored credential through `git credential fill`, queries GitHub REST
with GET only, and either classifies why `git push` / `git ls-remote` reports
"Repository not found" or discovers owners where the account can create private
repositories. The token is never printed or written to disk.

Exit codes: 0 definitive (REPO_EXISTS or ABSENT_CONFIRMED) or at least one owner
candidate, 1 inconclusive/negative or no candidate, 2 usage or environment error.
"""

import argparse
import json
import os
import subprocess
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen

API = "https://api.github.com"
API_HOST = "api.github.com"
USER_AGENT = "qoder-skill-probe/1.0"
MAX_PAGES = 10

DEFINITIVE = {"REPO_EXISTS", "ABSENT_CONFIRMED"}
DISCOVERY_HINT = (
    "run --list-owners to find an owner you can create under, "
    "then ask the user to confirm owner and visibility."
)


def configure_stdio():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def parse_repo_url(url):
    raw = (url or "").strip()
    if raw.startswith("git@"):
        host, _, path = raw[4:].partition(":")
    elif "://" in raw:
        parts = urlsplit(raw)
        host = parts.hostname or ""
        path = parts.path
    else:
        raise ValueError("unsupported URL form; expected https://github.com/{owner}/{repo}")
    if host.lower() != "github.com":
        raise ValueError(f"unsupported host: {host or 'none'}")
    path = path.strip("/")
    if path.endswith(".git"):
        path = path[:-4]
    segments = [segment for segment in path.split("/") if segment]
    if len(segments) != 2:
        raise ValueError("expected exactly one owner and one repository name")
    return segments[0], segments[1]


def read_credential():
    payload = "protocol=https\nhost=github.com\n\n"
    env = dict(os.environ)
    env["GIT_TERMINAL_PROMPT"] = "0"
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
    except (OSError, subprocess.SubprocessError) as exc:
        return None, None, f"git credential fill unavailable: {exc.__class__.__name__}"
    if proc.returncode != 0:
        return None, None, f"git credential fill exit {proc.returncode}"
    username = None
    password = None
    for line in proc.stdout.splitlines():
        if line.startswith("username=") and username is None:
            username = line.split("=", 1)[1]
        elif line.startswith("password=") and password is None:
            password = line.split("=", 1)[1]
    if not password:
        return username, None, "credential helper returned no password"
    return username, password, None


def api_get(target, token, timeout):
    url = target if target.startswith("http") else API + target
    request = Request(
        url,
        headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": USER_AGENT,
        },
        method="GET",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8", "replace")
            return response.status, response.headers, json.loads(body) if body.strip() else None
    except HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        try:
            data = json.loads(body) if body.strip() else None
        except json.JSONDecodeError:
            data = None
        return exc.code, exc.headers, data


def next_link(headers):
    link = headers.get("Link") if headers else None
    if not link:
        return None
    for part in link.split(","):
        if 'rel="next"' not in part:
            continue
        start = part.find("<")
        end = part.find(">")
        if start == -1 or end <= start:
            continue
        candidate = part[start + 1 : end]
        if urlsplit(candidate).hostname == API_HOST:
            return candidate
    return None


def api_list(path, token, timeout):
    items = []
    pages = 0
    url = API + path
    while url and pages < MAX_PAGES:
        status, headers, data = api_get(url, token, timeout)
        if status != 200 or not isinstance(data, list):
            return status, items, False
        items.extend(item for item in data if isinstance(item, dict))
        pages += 1
        url = next_link(headers)
    return 200, items, url is None


def rate_remaining(headers):
    try:
        return int(headers.get("X-RateLimit-Remaining"))
    except (TypeError, ValueError):
        return None


def classify(
    repo_status,
    owner_status,
    owner_type,
    scopes,
    membership_role,
    membership_state,
    org_complete,
    visible_complete,
    authed_login,
    owner,
    same_owner,
    other_owner,
    rate_left,
):
    if repo_status == 200:
        return "REPO_EXISTS", "Do not create. Point origin at this URL and push the dedicated branch."
    if repo_status == 403 and rate_left == 0:
        return "RATE_LIMITED", "Wait for the quota reset; do not conclude on repository existence."
    if owner_status == 404:
        return "OWNER_NOT_FOUND", "Check the owner spelling; do not create."
    if repo_status == 403:
        return "FORBIDDEN", "Insufficient rights; do not create, request access."
    if same_owner:
        return "INCONSISTENT", "Listed in /user/repos but direct GET failed; inspect token and repository state."
    if repo_status != 404:
        return "UNKNOWN", f"Unexpected HTTP {repo_status}; collect more evidence, do not create."
    if other_owner:
        return "WRONG_OWNER", "A same-name repository exists under another owner; ask which one to target."
    if scopes is not None and "repo" not in scopes:
        return "NO_REPO_SCOPE", "Token lacks the repo scope; renew the credential, do not create."
    if owner_type == "Organization":
        if membership_role == "admin" and org_complete:
            return "ABSENT_CONFIRMED", "Ask for confirmation, then create the private repository and push the branch."
        if membership_state == "active" or membership_role in ("admin", "member"):
            return "ABSENT_LIKELY", "Ask the user to confirm absence or provide an admin token before creating."
        return "NO_VISIBILITY", "Cannot prove absence; " + DISCOVERY_HINT
    if owner_type == "User":
        if authed_login and authed_login.lower() == owner.lower() and visible_complete:
            return "ABSENT_CONFIRMED", "Ask for confirmation, then create the private repository and push the branch."
        return "NO_VISIBILITY", "Private repositories of another user are invisible; " + DISCOVERY_HINT
    return "NO_VISIBILITY", "Owner type unknown; " + DISCOVERY_HINT


def load_identity(timeout):
    username, token, credential_error = read_credential()
    if not token:
        return {
            "token": None,
            "credential_user": username,
            "token_present": False,
            "auth_http": None,
            "authed_login": None,
            "scopes": None,
            "classification": "NO_CREDENTIAL",
            "next": credential_error or "run git credential fill interactively once",
        }
    status, headers, data = api_get("/user", token, timeout)
    login = data.get("login") if isinstance(data, dict) else None
    scopes_header = headers.get("X-OAuth-Scopes") if headers else None
    scopes = [item.strip() for item in scopes_header.split(",") if item.strip()] if scopes_header else None
    if status != 200 or not login:
        return {
            "token": token,
            "credential_user": username,
            "token_present": True,
            "auth_http": status,
            "authed_login": None,
            "scopes": scopes,
            "classification": "AUTH_INVALID",
            "next": "The credential helper does not yield a valid token; fix authentication first.",
        }
    return {
        "token": token,
        "credential_user": username,
        "token_present": True,
        "auth_http": status,
        "authed_login": login,
        "scopes": scopes,
        "classification": None,
        "next": None,
    }


def print_identity_failure(identity, as_json):
    result = {
        "mode": "OWNER_DISCOVERY",
        "credential_user": identity["credential_user"],
        "token_present": identity["token_present"],
        "auth_http": identity["auth_http"],
        "classification": identity["classification"],
        "next": identity["next"],
    }
    if as_json:
        print(json.dumps(result, ensure_ascii=False))
        return
    print(f"CREDENTIAL_USER: {identity['credential_user'] or 'none'}")
    print(f"TOKEN_PRESENT: {'yes' if identity['token_present'] else 'no'}")
    if identity["auth_http"] is not None:
        print(f"AUTH_HTTP: {identity['auth_http']}")
    print(f"CLASSIFICATION: {identity['classification']}")
    print(f"NEXT: {identity['next']}")


def run_owner_discovery(timeout, as_json):
    identity = load_identity(timeout)
    if identity["classification"]:
        print_identity_failure(identity, as_json)
        return 1

    scopes = identity["scopes"]
    if scopes is not None and "repo" not in scopes:
        result = {
            "mode": "OWNER_DISCOVERY",
            "credential_user": identity["credential_user"],
            "token_present": True,
            "authed_login": identity["authed_login"],
            "scopes": scopes,
            "classification": "NO_REPO_SCOPE",
            "next": "The token lacks the repo scope; renew the credential before creating private repositories.",
        }
        if as_json:
            print(json.dumps(result, ensure_ascii=False))
        else:
            print(f"CREDENTIAL_USER: {identity['credential_user'] or 'none'}")
            print("TOKEN_PRESENT: yes")
            print(f"AUTHED_LOGIN: {identity['authed_login']}")
            print("SCOPES: " + ", ".join(scopes))
            print("CLASSIFICATION: NO_REPO_SCOPE")
            print(f"NEXT: {result['next']}")
        return 1

    token = identity["token"]
    authed_login = identity["authed_login"]
    list_status, org_items, org_complete = api_list("/user/orgs?per_page=100", token, timeout)
    if list_status != 200:
        result = {
            "mode": "OWNER_DISCOVERY",
            "error": f"GET /user/orgs returned HTTP {list_status}",
        }
        if as_json:
            print(json.dumps(result, ensure_ascii=False))
        else:
            print(f"ERROR: {result['error']}")
        return 2

    orgs = []
    candidates = [
        {
            "owner": authed_login,
            "kind": "user",
            "can_create_private": True,
            "reason": "authenticated personal account; creation subject to plan limits",
        }
    ]
    for item in org_items:
        login = item.get("login")
        if not login:
            continue
        membership_http, _, membership = api_get(
            f"/user/memberships/orgs/{quote(login, safe='')}", token, timeout
        )
        state = membership.get("state") if isinstance(membership, dict) else None
        role = membership.get("role") if isinstance(membership, dict) else None
        org_http, _, org_data = api_get(f"/orgs/{quote(login, safe='')}", token, timeout)
        can_private = (
            org_data.get("members_can_create_private_repositories")
            if isinstance(org_data, dict)
            else None
        )
        plan = org_data.get("plan") if isinstance(org_data, dict) else None
        plan_private = plan.get("private_repos") if isinstance(plan, dict) else None
        total_private = org_data.get("total_private_repos") if isinstance(org_data, dict) else None
        active = state == "active"
        allowed = role == "admin" or can_private is True
        has_capacity = plan_private is None or total_private is None or total_private < plan_private
        can_create = bool(active and allowed and has_capacity)
        if can_create:
            reason = "admin" if role == "admin" else "members may create private repositories"
        elif not active:
            reason = f"membership state {state or 'unknown'}"
        elif not allowed:
            reason = "not admin and members cannot create private repositories"
        else:
            reason = "private repository quota reached"
        orgs.append(
            {
                "login": login,
                "membership_http": membership_http,
                "membership_state": state,
                "membership_role": role,
                "org_http": org_http,
                "members_can_create_private_repositories": can_private,
                "plan_private_repos": plan_private,
                "total_private_repos": total_private,
                "can_create_private": can_create,
                "reason": reason,
            }
        )
        if can_create:
            candidates.append(
                {
                    "owner": login,
                    "kind": "organization",
                    "can_create_private": True,
                    "reason": reason,
                }
            )

    next_step = (
        "Ask the user to confirm owner and visibility, then probe the chosen URL with --url "
        "and create only after confirmation."
        if candidates
        else "No owner with private-repository creation rights was found; ask for an owner or a credential with rights."
    )
    result = {
        "mode": "OWNER_DISCOVERY",
        "credential_user": identity["credential_user"],
        "token_present": True,
        "authed_login": authed_login,
        "scopes": scopes,
        "personal_owner": authed_login,
        "org_count": len(orgs),
        "org_list_complete": org_complete,
        "orgs": orgs,
        "owner_candidates": candidates,
        "next": next_step,
    }
    if as_json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print("MODE: OWNER_DISCOVERY")
        print(f"AUTHED_LOGIN: {authed_login}")
        print("SCOPES: " + (", ".join(scopes) if scopes else "ABSENT"))
        print(f"PERSONAL_OWNER: {authed_login}")
        print(f"ORG_COUNT: {len(orgs)}")
        print(f"ORG_LIST_COMPLETE: {org_complete}")
        for org in orgs:
            print(f"ORG: {org['login']}")
            print(f"  MEMBERSHIP_HTTP: {org['membership_http']}")
            print(f"  MEMBERSHIP_STATE: {org['membership_state'] or 'N/A'}")
            print(f"  MEMBERSHIP_ROLE: {org['membership_role'] or 'N/A'}")
            print(f"  ORG_HTTP: {org['org_http']}")
            print(
                "  MEMBERS_CAN_CREATE_PRIVATE_REPOSITORIES: "
                f"{org['members_can_create_private_repositories']}"
            )
            print(f"  PLAN_PRIVATE_REPOS: {org['plan_private_repos']}")
            print(f"  TOTAL_PRIVATE_REPOS: {org['total_private_repos']}")
            print(
                f"  CAN_CREATE_PRIVATE: {'yes' if org['can_create_private'] else 'no'}"
                f" ({org['reason']})"
            )
        candidate_text = ", ".join(
            f"{candidate['owner']} ({candidate['kind']}, can_create_private=yes)"
            for candidate in candidates
        )
        print(f"OWNER_CANDIDATES: {candidate_text or 'none'}")
        print(f"NEXT: {next_step}")
    return 0 if candidates else 1


def main():
    parser = argparse.ArgumentParser(
        description="Read-only probe: does the target GitHub repository exist, and may it be created?"
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--url", help="https://github.com/{owner}/{repo}.git")
    mode.add_argument(
        "--list-owners",
        action="store_true",
        help="list owners where the stored credential can create private repositories",
    )
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--json", action="store_true", help="emit a single JSON object")
    args = parser.parse_args()

    if args.list_owners:
        return run_owner_discovery(args.timeout, args.json)

    try:
        owner, repo = parse_repo_url(args.url)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 2

    identity = load_identity(args.timeout)
    username = identity["credential_user"]
    token = identity["token"]
    if identity["classification"] == "NO_CREDENTIAL":
        result = {
            "url": args.url.strip(),
            "owner": owner,
            "repo": repo,
            "credential_user": username,
            "token_present": False,
            "classification": "NO_CREDENTIAL",
            "next": identity["next"],
        }
        if args.json:
            print(json.dumps(result, ensure_ascii=False))
        else:
            print(f"URL: {result['url']}")
            print(f"CREDENTIAL_USER: {username or 'none'}")
            print("TOKEN_PRESENT: no")
            print("CLASSIFICATION: NO_CREDENTIAL")
            print(f"NEXT: {result['next']}")
        return 1

    if identity["classification"] == "AUTH_INVALID":
        result = {
            "url": args.url.strip(),
            "owner": owner,
            "repo": repo,
            "credential_user": username,
            "token_present": True,
            "auth_http": identity["auth_http"],
            "classification": "AUTH_INVALID",
            "next": identity["next"],
        }
        if args.json:
            print(json.dumps(result, ensure_ascii=False))
        else:
            print(f"CREDENTIAL_USER: {username or 'none'}")
            print("TOKEN_PRESENT: yes")
            print(f"AUTH_HTTP: {identity['auth_http']}")
            print("CLASSIFICATION: AUTH_INVALID")
            print(f"NEXT: {result['next']}")
        return 1

    authed_login = identity["authed_login"]
    scopes = identity["scopes"]

    repo_path = f"/repos/{quote(owner, safe='')}/{quote(repo, safe='')}"
    repo_status, repo_headers, repo_data = api_get(repo_path, token, args.timeout)
    repo_message = repo_data.get("message") if isinstance(repo_data, dict) else None
    rate_left = rate_remaining(repo_headers)

    owner_status, _, owner_data = api_get(f"/users/{quote(owner, safe='')}", token, args.timeout)
    owner_type = owner_data.get("type") if isinstance(owner_data, dict) else None
    owner_public = owner_data.get("public_repos") if isinstance(owner_data, dict) else None

    org_public = org_private = org_can_create = org_can_create_private = org_plan_private = None
    membership_state = membership_role = None
    org_items = []
    org_complete = False
    if owner_type == "Organization":
        _, _, org_data = api_get(f"/orgs/{quote(owner, safe='')}", token, args.timeout)
        if isinstance(org_data, dict):
            org_public = org_data.get("public_repos")
            org_private = org_data.get("total_private_repos")
            org_can_create = org_data.get("members_can_create_repositories")
            org_can_create_private = org_data.get("members_can_create_private_repositories")
            plan = org_data.get("plan")
            org_plan_private = plan.get("private_repos") if isinstance(plan, dict) else None
        _, _, membership = api_get(
            f"/user/memberships/orgs/{quote(owner, safe='')}", token, args.timeout
        )
        if isinstance(membership, dict):
            membership_state = membership.get("state")
            membership_role = membership.get("role")
        _, org_items, org_complete = api_list(
            f"/orgs/{quote(owner, safe='')}/repos?per_page=100&type=all", token, args.timeout
        )

    _, visible_items, visible_complete = api_list(
        "/user/repos?per_page=100&affiliation=owner,collaborator,organization_member",
        token,
        args.timeout,
    )

    def same_name(item):
        return (item.get("name") or "").lower() == repo.lower()

    def item_owner(item):
        return ((item.get("owner") or {}).get("login") or "").lower()

    same_owner = [item for item in visible_items if same_name(item) and item_owner(item) == owner.lower()]
    other_owner = [item for item in visible_items if same_name(item) and item_owner(item) != owner.lower()]
    org_match = [item for item in org_items if same_name(item)]

    classification, next_step = classify(
        repo_status=repo_status,
        owner_status=owner_status,
        owner_type=owner_type,
        scopes=scopes,
        membership_role=membership_role,
        membership_state=membership_state,
        org_complete=org_complete,
        visible_complete=visible_complete,
        authed_login=authed_login,
        owner=owner,
        same_owner=same_owner,
        other_owner=other_owner,
        rate_left=rate_left,
    )

    result = {
        "url": args.url.strip(),
        "owner": owner,
        "repo": repo,
        "credential_user": username,
        "token_present": True,
        "authed_login": authed_login,
        "scopes": scopes,
        "owner_type": owner_type,
        "owner_public_repos": owner_public,
        "membership_state": membership_state,
        "membership_role": membership_role,
        "org_public_repos": org_public,
        "org_total_private_repos": org_private,
        "org_members_can_create_repositories": org_can_create,
        "org_members_can_create_private_repositories": org_can_create_private,
        "org_plan_private_repos": org_plan_private,
        "org_repo_count": len(org_items) if owner_type == "Organization" else None,
        "org_repo_match": org_match[0].get("full_name") if org_match else None,
        "visible_repo_count": len(visible_items),
        "visible_name_match": (
            f"{same_owner[0].get('full_name')} (private={same_owner[0].get('private')})"
            if same_owner
            else None
        ),
        "visible_other_owner": (
            f"{other_owner[0].get('full_name')} (private={other_owner[0].get('private')})"
            if other_owner
            else None
        ),
        "lists_complete": {
            "org": org_complete if owner_type == "Organization" else None,
            "visible": visible_complete,
        },
        "repo_http": repo_status,
        "repo_message": repo_message,
        "rate_remaining": rate_left,
        "classification": classification,
        "next": next_step,
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        def show(key, label):
            value = result.get(key)
            print(f"{label}: {'N/A' if value is None else value}")

        show("url", "URL")
        show("owner", "OWNER")
        show("repo", "REPO")
        show("credential_user", "CREDENTIAL_USER")
        print("TOKEN_PRESENT: yes")
        show("authed_login", "AUTHED_LOGIN")
        print("SCOPES: " + (", ".join(result["scopes"]) if result["scopes"] else "ABSENT"))
        show("owner_type", "OWNER_TYPE")
        show("owner_public_repos", "OWNER_PUBLIC_REPOS")
        show("membership_state", "MEMBERSHIP_STATE")
        show("membership_role", "MEMBERSHIP_ROLE")
        show("org_public_repos", "ORG_PUBLIC_REPOS")
        show("org_total_private_repos", "ORG_TOTAL_PRIVATE_REPOS")
        show("org_members_can_create_repositories", "ORG_MEMBERS_CAN_CREATE_REPOSITORIES")
        show("org_members_can_create_private_repositories", "ORG_MEMBERS_CAN_CREATE_PRIVATE_REPOSITORIES")
        show("org_plan_private_repos", "ORG_PLAN_PRIVATE_REPOS")
        show("org_repo_count", "ORG_REPO_COUNT")
        show("org_repo_match", "ORG_REPO_MATCH")
        show("visible_repo_count", "VISIBLE_REPO_COUNT")
        show("visible_name_match", "VISIBLE_NAME_MATCH")
        show("visible_other_owner", "VISIBLE_OTHER_OWNER")
        print(
            "LISTS_COMPLETE: org={org} visible={visible}".format(
                org=result["lists_complete"]["org"],
                visible=result["lists_complete"]["visible"],
            )
        )
        show("repo_http", "REPO_HTTP")
        show("repo_message", "REPO_MESSAGE")
        show("rate_remaining", "RATE_REMAINING")
        print(f"CLASSIFICATION: {classification}")
        print(f"NEXT: {next_step}")

    return 0 if classification in DEFINITIVE else 1


if __name__ == "__main__":
    configure_stdio()
    try:
        sys.exit(main())
    except URLError as exc:
        print(f"ERROR: network failure: {exc.reason}")
        sys.exit(2)
    except TimeoutError:
        print("ERROR: network timeout")
        sys.exit(2)
