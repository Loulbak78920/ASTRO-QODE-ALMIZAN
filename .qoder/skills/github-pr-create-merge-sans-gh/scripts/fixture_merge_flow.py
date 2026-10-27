#!/usr/bin/env python3
"""Offline fixture for the create and merge paths of github_pr_api.py.

The script under test is copied to a temporary directory and imported by a
child interpreter started with -B. credentials(), api() and time.sleep() are
replaced by queues keyed by request shape, and urlopen()/subprocess.run() are
forbidden, so no network, no credential helper and no GitHub state are used.

Twenty-one assertions mirror the deleted ad-hoc harness of session a374787e
(2026-10-26): merge happy path, squash payload with commit_title, mergeable
false, 15-poll timeout, 405, already merged, closed PR, VERIFY_MATCH false,
create reuse/new/422 and the files-count mismatch. Routing checks /files and
/merge before /pulls/<n>; a naive /pulls/ dispatch would send the files
request to the pull handler.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import io
import os
import shutil
import subprocess
import sys
import tempfile
from collections import deque
from pathlib import Path
from typing import Callable, Dict, List, Sequence, Tuple
from unittest import mock

DEFAULT_SCRIPT = Path(__file__).resolve().parent / "github_pr_api.py"
REPO = "owner/repo"
MERGE_URL = "https://example.invalid/pull/42"
PULL = {
    "number": 42,
    "merged": False,
    "state": "open",
    "base": {"ref": "main"},
    "head": {"ref": "head", "sha": "head-sha"},
    "html_url": MERGE_URL,
}

Result = Tuple[str, str]


class FixtureError(RuntimeError):
    pass


def forbidden(*args, **kwargs):
    raise AssertionError("forbidden network or credential call")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def pyc_set(root: Path) -> set:
    if not root.is_dir():
        return set()
    return {str(path.relative_to(root)) for path in root.rglob("*.pyc")}


def shape(method: str, path: str) -> str:
    base = path.split("?", 1)[0]
    if method == "POST" and base == "/repos/%s/pulls" % REPO:
        return "create"
    if method == "GET" and base == "/repos/%s/pulls" % REPO:
        return "list"
    if method == "GET" and base.startswith("/repos/%s/pulls/" % REPO) and base.endswith("/files"):
        return "files"
    if method == "PUT" and base.startswith("/repos/%s/pulls/" % REPO) and base.endswith("/merge"):
        return "merge"
    if method == "GET" and base.startswith("/repos/%s/pulls/" % REPO):
        tail = base.rsplit("/", 1)[-1]
        if tail.isdigit():
            return "pull"
    if method == "GET" and base.startswith("/repos/%s/git/ref/heads/" % REPO):
        return "ref"
    raise AssertionError("UNROUTED %s %s" % (method, path))


class FakeAPI:
    def __init__(self, routes: Dict[str, Sequence[Tuple[int, object]]]):
        self.routes = {key: deque(values) for key, values in routes.items()}
        self.calls = []  # type: List[dict]
        self.sleeps = []  # type: List[float]

    def api(self, method: str, path: str, token: str, payload=None):
        key = shape(method, path)
        self.calls.append({"method": method, "path": path, "payload": payload})
        queue = self.routes.get(key)
        if not queue:
            raise AssertionError("NO_RESPONSE %s" % key)
        return queue.popleft() if len(queue) > 1 else queue[0]

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)

    def count(self, method: str, suffix: str = "") -> int:
        return sum(
            1
            for call in self.calls
            if call["method"] == method and call["path"].split("?", 1)[0].endswith(suffix)
        )

    def payloads(self, method: str) -> List[object]:
        return [call["payload"] for call in self.calls if call["method"] == method]

    def sequence(self) -> List[str]:
        return [shape(call["method"], call["path"]) for call in self.calls]


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("github_pr_api_under_test", str(path))
    if spec is None or spec.loader is None:
        raise FixtureError("cannot load %s" % path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_scenario(module, routes: Dict[str, Sequence[Tuple[int, object]]], argv: Sequence[str]):
    fake = FakeAPI(routes)
    output = io.StringIO()
    exc = ""
    rc = None
    with mock.patch.object(module, "credentials", return_value=("tester", "token")), \
            mock.patch.object(module, "api", side_effect=fake.api), \
            mock.patch.object(module.time, "sleep", side_effect=fake.sleep), \
            mock.patch.object(module.subprocess, "run", side_effect=forbidden), \
            mock.patch.object(module.urllib.request, "urlopen", side_effect=forbidden):
        try:
            args = module.build_parser().parse_args(list(argv))
            with contextlib.redirect_stdout(output):
                rc = args.func(args)
        except BaseException as err:  # keep stdout actionable, no traceback
            exc = "%s: %s" % (type(err).__name__, err)
    return rc, output.getvalue(), fake, exc


def verdict(label: str, check: Callable[[], str]) -> Result:
    try:
        detail = check()
    except Exception as exc:
        detail = "%s: %s" % (type(exc).__name__, exc)
    return label, detail


def expect(condition: bool, detail: str) -> str:
    return "" if condition else detail


def missing(text: str, tokens: Sequence[str]) -> List[str]:
    return [token for token in tokens if token not in text]


def tail(text: str, limit: int = 400) -> str:
    return text[-limit:].replace("\n", " | ")


def scenario_merge_happy(module) -> List[Result]:
    routes = {
        "pull": [
            (200, dict(PULL, mergeable=None)),
            (200, dict(PULL, mergeable=None)),
            (200, dict(PULL, mergeable=True)),
            (200, dict(PULL, state="closed", merged=True, merge_commit_sha="merge-sha")),
        ],
        "merge": [(200, {"merged": True, "sha": "merge-sha"})],
        "ref": [(200, {"object": {"sha": "merge-sha"}})],
    }
    rc, text, fake, exc = run_scenario(
        module,
        routes,
        ["merge", "--repo", REPO, "--pr", "42", "--method", "rebase", "--yes"],
    )
    tokens = (
        "MERGE_REBASE status=200 merged=True sha=merge-sha",
        "MERGE_OK sha=merge-sha",
        "PR_FINAL state=closed merged=True merge_commit_sha=merge-sha",
        "REMOTE_MAIN merge-sha",
        "VERIFY_MATCH true",
    )
    return [
        verdict("merge happy rc=0", lambda: expect(rc == 0, "rc=%s expected=0 exc=%s" % (rc, exc))),
        verdict(
            "merge happy output",
            lambda: expect(not missing(text, tokens), "missing=%s tail=%s" % (missing(text, tokens), tail(text))),
        ),
        verdict(
            "merge happy payload rebase",
            lambda: expect(
                fake.payloads("PUT") == [{"merge_method": "rebase"}],
                "payload=%r" % (fake.payloads("PUT"),),
            ),
        ),
        verdict(
            "merge happy polling order",
            lambda: expect(
                fake.sequence() == ["pull", "pull", "pull", "merge", "pull", "ref"]
                and fake.count("GET", "/pulls/42") == 4
                and fake.sleeps == [2],
                "sequence=%r pulls=%s sleeps=%r" % (fake.sequence(), fake.count("GET", "/pulls/42"), fake.sleeps),
            ),
        ),
    ]


def scenario_merge_squash(module) -> List[Result]:
    routes = {
        "pull": [
            (200, dict(PULL)),
            (200, dict(PULL, mergeable=True)),
            (200, dict(PULL, state="closed", merged=True, merge_commit_sha="squash-sha")),
        ],
        "merge": [(200, {"merged": True, "sha": "squash-sha"})],
        "ref": [(200, {"object": {"sha": "squash-sha"}})],
    }
    rc, text, fake, exc = run_scenario(
        module,
        routes,
        ["merge", "--repo", REPO, "--pr", "42", "--method", "squash", "--commit-title", "Titre squash", "--yes"],
    )
    return [
        verdict("merge squash rc=0", lambda: expect(rc == 0, "rc=%s expected=0 exc=%s" % (rc, exc))),
        verdict(
            "merge squash payload",
            lambda: expect(
                fake.payloads("PUT") == [{"merge_method": "squash", "commit_title": "Titre squash"}],
                "payload=%r" % (fake.payloads("PUT"),),
            ),
        ),
    ]


def scenario_mergeable_false(module) -> List[Result]:
    routes = {
        "pull": [
            (200, dict(PULL)),
            (200, dict(PULL, mergeable=False)),
        ],
        "merge": [(200, {"merged": True, "sha": "unexpected"})],
    }
    rc, text, fake, exc = run_scenario(
        module, routes, ["merge", "--repo", REPO, "--pr", "42", "--method", "rebase", "--yes"]
    )
    return [
        verdict(
            "mergeable false rc=2",
            lambda: expect(
                rc == 2 and "MERGE_ABORT mergeable=false" in text,
                "rc=%s expected=2 token=%s exc=%s" % (rc, "MERGE_ABORT mergeable=false" in text, exc),
            ),
        ),
        verdict(
            "mergeable false no PUT",
            lambda: expect(fake.count("PUT") == 0, "PUT calls=%s" % fake.count("PUT")),
        ),
    ]


def scenario_timeout(module) -> List[Result]:
    routes = {
        "pull": [
            (200, dict(PULL)),
            (200, dict(PULL, mergeable=None)),
        ],
        "merge": [(200, {"merged": True, "sha": "unexpected"})],
    }
    rc, text, fake, exc = run_scenario(
        module, routes, ["merge", "--repo", REPO, "--pr", "42", "--method", "rebase", "--yes"]
    )
    return [
        verdict(
            "mergeable timeout rc=2",
            lambda: expect(
                rc == 2 and "MERGEABLE_TIMEOUT after 15 checks" in text,
                "rc=%s expected=2 token=%s exc=%s" % (rc, "MERGEABLE_TIMEOUT after 15 checks" in text, exc),
            ),
        ),
        verdict(
            "timeout polls 16",
            lambda: expect(
                fake.count("GET", "/pulls/42") == 16 and fake.sleeps == [2] * 15,
                "pulls=%s sleeps=%s" % (fake.count("GET", "/pulls/42"), len(fake.sleeps)),
            ),
        ),
        verdict(
            "timeout no PUT",
            lambda: expect(fake.count("PUT") == 0, "PUT calls=%s" % fake.count("PUT")),
        ),
    ]


def scenario_merge_405(module) -> List[Result]:
    routes = {
        "pull": [
            (200, dict(PULL)),
            (200, dict(PULL, mergeable=True)),
        ],
        "merge": [(405, {"message": "Merge blocked"})],
    }
    rc, text, fake, exc = run_scenario(
        module, routes, ["merge", "--repo", REPO, "--pr", "42", "--method", "rebase", "--yes"]
    )
    return [
        verdict(
            "merge 405 rc=2",
            lambda: expect(
                rc == 2 and "MERGE_FAIL status=405" in text and "PR_FINAL" not in text,
                "rc=%s expected=2 token=%s final=%s exc=%s"
                % (rc, "MERGE_FAIL status=405" in text, "PR_FINAL" in text, exc),
            ),
        )
    ]


def scenario_already_merged(module) -> List[Result]:
    routes = {
        "pull": [(200, dict(PULL, merged=True, state="closed"))],
        "merge": [(200, {"merged": True, "sha": "unexpected"})],
        "ref": [(200, {"object": {"sha": "main-sha"}})],
    }
    rc, text, fake, exc = run_scenario(
        module, routes, ["merge", "--repo", REPO, "--pr", "42", "--method", "rebase", "--yes"]
    )
    return [
        verdict(
            "already merged rc=0",
            lambda: expect(
                rc == 0 and "ALREADY_MERGED 42" in text and "REMOTE_MAIN main-sha" in text,
                "rc=%s expected=0 tokens=%s exc=%s"
                % (rc, missing(text, ("ALREADY_MERGED 42", "REMOTE_MAIN main-sha")), exc),
            ),
        ),
        verdict(
            "already merged no PUT",
            lambda: expect(fake.count("PUT") == 0, "PUT calls=%s" % fake.count("PUT")),
        ),
    ]


def scenario_closed(module) -> List[Result]:
    routes = {"pull": [(200, dict(PULL, state="closed"))]}
    rc, text, fake, exc = run_scenario(
        module, routes, ["merge", "--repo", REPO, "--pr", "42", "--method", "rebase", "--yes"]
    )
    return [
        verdict(
            "closed rc=2",
            lambda: expect(
                rc == 2 and "PR_NOT_OPEN state=closed merged=False" in text and fake.count("PUT") == 0,
                "rc=%s expected=2 token=%s PUT=%s exc=%s"
                % (rc, "PR_NOT_OPEN state=closed merged=False" in text, fake.count("PUT"), exc),
            ),
        )
    ]


def scenario_verify_mismatch(module) -> List[Result]:
    routes = {
        "pull": [
            (200, dict(PULL)),
            (200, dict(PULL, mergeable=True)),
            (200, dict(PULL, state="closed", merged=True, merge_commit_sha="merge-sha")),
        ],
        "merge": [(200, {"merged": True, "sha": "merge-sha"})],
        "ref": [(200, {"object": {"sha": "other-sha"}})],
    }
    rc, text, fake, exc = run_scenario(
        module, routes, ["merge", "--repo", REPO, "--pr", "42", "--method", "rebase", "--yes"]
    )
    return [
        verdict(
            "verify mismatch rc=2",
            lambda: expect(
                rc == 2 and "MERGE_OK sha=merge-sha" in text and "VERIFY_MATCH false" in text,
                "rc=%s expected=2 tokens=%s exc=%s"
                % (rc, missing(text, ("MERGE_OK sha=merge-sha", "VERIFY_MATCH false")), exc),
            ),
        )
    ]


def scenario_create_existing(module) -> List[Result]:
    routes = {
        "list": [(200, [dict(PULL, number=7, state="open")])],
        "create": [(201, dict(PULL, number=7))],
    }
    rc, text, fake, exc = run_scenario(
        module,
        routes,
        ["create", "--repo", REPO, "--head", "head", "--base", "main", "--title", "Titre", "--body", "Corps", "--yes"],
    )
    return [
        verdict(
            "create existing rc=0",
            lambda: expect(
                rc == 0 and "PR_EXISTING 7" in text,
                "rc=%s expected=0 token=%s exc=%s" % (rc, "PR_EXISTING 7" in text, exc),
            ),
        ),
        verdict(
            "create existing no POST",
            lambda: expect(fake.count("POST") == 0, "POST calls=%s" % fake.count("POST")),
        ),
    ]


def scenario_create_new(module) -> List[Result]:
    routes = {
        "list": [(200, [])],
        "create": [(201, dict(PULL, number=8))],
    }
    payload = {"title": "Titre", "head": "head", "base": "main", "body": "Corps"}
    rc, text, fake, exc = run_scenario(
        module,
        routes,
        ["create", "--repo", REPO, "--head", "head", "--base", "main", "--title", "Titre", "--body", "Corps", "--yes"],
    )
    return [
        verdict(
            "create new rc=0",
            lambda: expect(
                rc == 0 and "PR_CREATED 8" in text and fake.payloads("POST") == [payload],
                "rc=%s expected=0 token=%s payload=%r exc=%s"
                % (rc, "PR_CREATED 8" in text, fake.payloads("POST"), exc),
            ),
        )
    ]


def scenario_create_422(module) -> List[Result]:
    routes = {
        "list": [(200, [])],
        "create": [(422, {"message": "Validation Failed"})],
    }
    rc, text, fake, exc = run_scenario(
        module,
        routes,
        ["create", "--repo", REPO, "--head", "head", "--base", "main", "--title", "Titre", "--yes"],
    )
    return [
        verdict(
            "create 422 rc=2",
            lambda: expect(
                rc == 2 and "PR_CREATE_FAIL status=422" in text,
                "rc=%s expected=2 token=%s exc=%s" % (rc, "PR_CREATE_FAIL status=422" in text, exc),
            ),
        )
    ]


def scenario_files_mismatch(module) -> List[Result]:
    files = [
        {"status": "modified", "filename": "a.md", "additions": 1, "deletions": 1},
        {"status": "modified", "filename": "b.md", "additions": 1, "deletions": 1},
    ]
    routes = {
        "files": [(200, files)],
        "pull": [(200, {"number": 42, "changed_files": 3, "additions": 2, "deletions": 2, "state": "open", "merged": False})],
    }
    rc, text, fake, exc = run_scenario(
        module, routes, ["files", "--repo", REPO, "--pr", "42"]
    )
    tokens = ("FILES 2", "PR_FILES changed=3", "FILES_MISMATCH api_files=2 changed_files=3")
    return [
        verdict(
            "files mismatch rc=2",
            lambda: expect(
                rc == 2 and not missing(text, tokens),
                "rc=%s expected=2 missing=%s sequence=%r exc=%s"
                % (rc, missing(text, tokens), fake.sequence(), exc),
            ),
        )
    ]


def run_all(module) -> List[Result]:
    results = []  # type: List[Result]
    for scenario in (
        scenario_merge_happy,
        scenario_merge_squash,
        scenario_mergeable_false,
        scenario_timeout,
        scenario_merge_405,
        scenario_already_merged,
        scenario_closed,
        scenario_verify_mismatch,
        scenario_create_existing,
        scenario_create_new,
        scenario_create_422,
        scenario_files_mismatch,
    ):
        results.extend(scenario(module))
    return results


def child_main(copy_path: Path) -> int:
    sys.dont_write_bytecode = True
    module = load_module(copy_path)
    results = run_all(module)
    if len(results) != 21:
        print("ERROR case count=%s expected=21" % len(results))
        return 2
    passed = 0
    failed = 0
    for label, detail in results:
        if detail:
            failed += 1
            print("CASE %s FAIL %s" % (label, detail))
        else:
            passed += 1
            print("CASE %s PASS" % label)
    print("RESULT PASS=%s FAIL=%s" % (passed, failed))
    return 0 if failed == 0 else 1


def force_rmtree(path: Path) -> None:
    if not path.exists():
        return
    for item in [path, *path.rglob("*")]:
        try:
            os.chmod(item, 0o700 if item.is_dir() else 0o600)
        except OSError:
            pass
    shutil.rmtree(path, ignore_errors=True)


def main(argv: Sequence[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(
        description="Run the create/merge paths of github_pr_api.py against stubbed HTTP responses.",
    )
    parser.add_argument("--script", type=Path, default=DEFAULT_SCRIPT, help="github_pr_api.py to test (default: sibling script)")
    parser.add_argument("--keep", action="store_true", help="keep the temporary directory for inspection")
    parser.add_argument("--child", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    if args.child is not None:
        try:
            return child_main(args.child)
        except BaseException as exc:
            print("ERROR %s: %s" % (type(exc).__name__, exc))
            return 2

    script = args.script.resolve()
    if not script.is_file():
        print("ERROR script not found: %s" % script)
        return 2

    root = None
    try:
        before_hash = sha256_file(script)
        before_pyc = pyc_set(script.parent)
        print("SCRIPT %s" % script.as_posix())
        print("SCRIPT_SHA256 %s" % before_hash)

        root = Path(tempfile.mkdtemp(prefix="gh-pr-merge-flow-"))
        copy = root / "github_pr_api.py"
        shutil.copy2(script, copy)

        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        proc = subprocess.run(
            [sys.executable, "-B", str(Path(__file__).resolve()), "--child", str(copy)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
            env=env,
        )
        if proc.stdout:
            sys.stdout.write(proc.stdout)
            if not proc.stdout.endswith("\n"):
                sys.stdout.write("\n")
        if proc.stderr:
            print("CHILD_STDERR %s" % tail(proc.stderr, 1200))

        after_hash = sha256_file(script)
        after_pyc = pyc_set(script.parent)
        if after_hash == before_hash:
            print("SOURCE_UNCHANGED %s" % after_hash)
        else:
            print("SOURCE_CHANGED before=%s after=%s" % (before_hash, after_hash))
        added = sorted(after_pyc - before_pyc)
        removed = sorted(before_pyc - after_pyc)
        if not added and not removed:
            print("NO_NEW_CACHE")
        else:
            print("CACHE_LEAK added=%r removed=%r" % (added, removed))

        if proc.returncode == 0 and after_hash == before_hash and not added and not removed:
            return 0
        if proc.returncode in (0, 1):
            return 1
        return 2
    except subprocess.TimeoutExpired:
        print("ERROR child timeout")
        return 2
    except (FixtureError, OSError) as exc:
        print("ERROR %s: %s" % (type(exc).__name__, exc))
        return 2
    finally:
        if root is not None and root.exists():
            if args.keep:
                print("KEPT %s" % root.as_posix())
            else:
                force_rmtree(root)
                print("CLEANED")


if __name__ == "__main__":
    sys.exit(main())
