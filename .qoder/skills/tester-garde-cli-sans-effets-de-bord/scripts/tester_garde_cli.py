#!/usr/bin/env python3
"""Fixture A/B hors production pour un pre-controle CLI et la non-fuite de secret.

Le script cible est copie dans un repertoire jetable, puis importe dans un processus
enfant avec subprocess.run, urllib.request.urlopen et socket remplaces par des espions.
Deux scenarios identiques sauf le drapeau de confirmation sont compares : nombre exact
d'appels, code de sortie, marqueur attendu et absence du jeton sentinelle.

Le script ne modifie pas la cible, n'utilise aucun identifiant reel et ne contacte
aucun reseau.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import io
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

sys.dont_write_bytecode = True

CHILD_PREFIX = "CHILD "
SENTINEL_DEFAULT = "SECRET_FIXTURE_TOKEN"
DENY = "deny"
ALLOW = "allow"
GIT_NAMES = {"git", "git.exe", "git.cmd", "git.bat"}

UNSUPPORTED_CALL_PREFIXES = (
    "subprocess.Popen",
    "subprocess.check_output",
    "subprocess.check_call",
    "subprocess.call",
    "os.system",
    "os.popen",
    "os.execv",
    "os.execve",
    "os.spawnv",
    "os.spawnve",
    "os.startfile",
)
UNSUPPORTED_MODULES = {"requests", "httpx", "aiohttp", "urllib3"}
TOP_LEVEL_WRITES = {
    "os.remove",
    "os.rename",
    "os.replace",
    "os.mkdir",
    "os.makedirs",
    "os.rmdir",
    "shutil.rmtree",
    "shutil.copy",
    "shutil.copyfile",
    "shutil.move",
    "load_dotenv",
}
WRITE_METHODS = {"write_text", "write_bytes", "unlink", "mkdir", "rename", "replace"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def dotted(node: ast.AST) -> str:
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        return ".".join(reversed(parts))
    return ""


class ModuleLevelCalls(ast.NodeVisitor):
    """Collect calls that execute during import (module and class bodies)."""

    def __init__(self) -> None:
        self.calls: list[ast.Call] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        return

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        return

    def visit_Lambda(self, node: ast.Lambda) -> None:
        return

    def visit_Call(self, node: ast.Call) -> None:
        self.calls.append(node)
        self.generic_visit(node)


def preflight(tree: ast.Module) -> tuple[list[str], list[str]]:
    unsupported: list[str] = []
    writes: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in UNSUPPORTED_MODULES:
                    unsupported.append(f"import {alias.name}")
        elif isinstance(node, ast.ImportFrom) and node.module:
            root = node.module.split(".")[0]
            if root in UNSUPPORTED_MODULES:
                unsupported.append(f"from {node.module} import ...")
        elif isinstance(node, ast.Call):
            name = dotted(node.func)
            if name.startswith(UNSUPPORTED_CALL_PREFIXES):
                unsupported.append(f"{name}()")

    collector = ModuleLevelCalls()
    for statement in tree.body:
        collector.visit(statement)

    for call in collector.calls:
        name = dotted(call.func)
        if name in TOP_LEVEL_WRITES:
            writes.append(f"{name}()")
        elif isinstance(call.func, ast.Attribute) and call.func.attr in WRITE_METHODS:
            writes.append(f".{call.func.attr}()")
        elif name == "open":
            mode = None
            if len(call.args) >= 2 and isinstance(call.args[1], ast.Constant):
                mode = call.args[1].value
            for keyword in call.keywords:
                if keyword.arg == "mode" and isinstance(keyword.value, ast.Constant):
                    mode = keyword.value.value
            if isinstance(mode, str) and any(flag in mode for flag in "wax+"):
                writes.append(f"open(mode={mode!r})")

    return unsupported, writes


def scrub(text: str, sentinel: str) -> str:
    text = text.replace(sentinel, "<redacted>")
    text = " | ".join(line.strip() for line in text.splitlines() if line.strip())
    if len(text) > 500:
        text = text[:497] + "..."
    return text.encode("ascii", "backslashreplace").decode("ascii")


def child_env() -> dict[str, str]:
    env = dict(os.environ)
    for name in ("GITHUB_TOKEN", "GH_TOKEN", "GIT_ASKPASS", "SSH_ASKPASS"):
        env.pop(name, None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    env["GIT_TERMINAL_PROMPT"] = "0"
    return env


def run_child(opts: argparse.Namespace) -> int:
    sentinel = opts.sentinel
    counts = {"proc": 0, "git": 0, "urlopen": 0, "socket": 0}
    executions: list[str] = []

    class FakeCompleted:
        def __init__(self, command: object) -> None:
            self.args = command
            self.returncode = 0
            self.stdout = f"username=fixture-user\npassword={sentinel}\n"
            self.stderr = ""

        def check_returncode(self) -> None:
            return None

    def fake_run(command, *args, **kwargs):
        counts["proc"] += 1
        tokens = command if isinstance(command, (list, tuple)) else [command]
        text = " ".join(str(token) for token in tokens)
        executions.append(text)
        first = Path(str(tokens[0])).name.lower() if tokens else ""
        if first in GIT_NAMES:
            counts["git"] += 1
        return FakeCompleted(command)

    def fake_urlopen(request, *args, **kwargs):
        counts["urlopen"] += 1
        raise urllib.error.URLError("fixture-network-blocked")

    def blocked_socket(*args, **kwargs):
        counts["socket"] += 1
        raise OSError("fixture-socket-blocked")

    subprocess.run = fake_run
    urllib.request.urlopen = fake_urlopen
    socket.socket = blocked_socket
    socket.create_connection = blocked_socket

    import_error: BaseException | None = None
    module = None
    captured = io.StringIO()
    with redirect_stdout(captured), redirect_stderr(captured):
        try:
            spec = importlib.util.spec_from_file_location("fixture_target", opts.script)
            if spec is None or spec.loader is None:
                raise ImportError(f"cannot load {opts.script}")
            module = importlib.util.module_from_spec(spec)
            sys.modules["fixture_target"] = module
            spec.loader.exec_module(module)
        except BaseException as exc:  # noqa: BLE001 - measured in the child
            import_error = exc

    import_proc = counts["proc"]
    import_net = counts["urlopen"] + counts["socket"]

    if import_error is not None:
        line = (
            f"{CHILD_PREFIX}scenario={opts.scenario} exit=0 proc={counts['proc']} "
            f"git={counts['git']} net={import_net} urlopen={counts['urlopen']} "
            f"socket={counts['socket']} import_proc={import_proc} import_net={import_net} "
            f"marker=na leak=no argv_leak=no phase=import exc={type(import_error).__name__}"
        )
        print(line)
        print(f"EXCERPT {scrub(captured.getvalue() + ' ' + repr(import_error), sentinel)}")
        return 4

    if opts.api_root and hasattr(module, opts.api_root_attr):
        setattr(module, opts.api_root_attr, opts.api_root)

    entry = getattr(module, opts.entry, None)
    if not callable(entry):
        print(
            f"{CHILD_PREFIX}scenario={opts.scenario} exit=0 proc={counts['proc']} "
            f"git={counts['git']} net={'0'} urlopen=0 socket=0 import_proc={import_proc} "
            f"import_net={import_net} marker=na leak=no argv_leak=no phase=import exc=MissingEntry"
        )
        return 4

    sys.argv = [Path(opts.script).name] + list(opts.argv)
    run_error: BaseException | None = None
    code = 0
    with redirect_stdout(captured), redirect_stderr(captured):
        try:
            result = entry()
            code = 0 if result is None else int(result)
        except SystemExit as exc:
            if exc.code is None:
                code = 0
            elif isinstance(exc.code, int):
                code = exc.code
            else:
                code = 1
        except BaseException as exc:  # noqa: BLE001 - measured in the child
            run_error = exc
            code = 99

    output = captured.getvalue()
    leak = sentinel in output
    argv_leak = any(sentinel in str(token) for token in sys.argv)
    if not opts.marker:
        marker = "na"
    else:
        marker = "yes" if opts.marker in output else "no"
    network_calls = counts["urlopen"] + counts["socket"]
    phase = "run" if run_error is not None else "none"
    exception = type(run_error).__name__ if run_error is not None else "none"

    line = (
        f"{CHILD_PREFIX}scenario={opts.scenario} exit={code} proc={counts['proc']} "
        f"git={counts['git']} net={network_calls} urlopen={counts['urlopen']} "
        f"socket={counts['socket']} import_proc={import_proc} import_net={import_net} "
        f"marker={marker} leak={'yes' if leak else 'no'} "
        f"argv_leak={'yes' if argv_leak else 'no'} phase={phase} exc={exception}"
    )
    print(line)
    for execution in executions[:3]:
        print(f"EXEC {scrub(execution, sentinel)}")
    print(f"EXCERPT {scrub(output, sentinel)}")
    return 0


def snapshot_cache(script: Path) -> set[str]:
    cache_dir = script.parent / "__pycache__"
    if not cache_dir.is_dir():
        return set()
    return {path.name for path in cache_dir.iterdir() if path.is_file()}


def parse_child(stdout: str) -> dict[str, str]:
    line = None
    for candidate in stdout.splitlines():
        if candidate.startswith(CHILD_PREFIX):
            line = candidate[len(CHILD_PREFIX):]
    if line is None:
        raise RuntimeError("sortie enfant sans ligne CHILD")
    fields: dict[str, str] = {}
    for token in line.split():
        if "=" in token:
            key, value = token.split("=", 1)
            fields[key] = value
    required = {"scenario", "exit", "proc", "git", "net", "import_proc", "import_net",
                "marker", "leak", "argv_leak", "phase", "exc"}
    missing = required - fields.keys()
    if missing:
        raise RuntimeError(f"champs enfant manquants: {sorted(missing)}")
    return fields


def call_child(opts, scenario: str, marker: str, work: Path, copy_path: Path,
               argv: list[str], timeout: int) -> tuple[dict[str, str], str]:
    command = [
        sys.executable,
        "-B",
        str(Path(__file__).resolve()),
        "--child",
        "--scenario",
        scenario,
        "--script",
        str(copy_path),
        "--entry",
        opts.entry,
        "--sentinel",
        opts.sentinel,
        "--api-root-attr",
        opts.api_root_attr,
        "--api-root",
        opts.api_root,
        "--marker",
        marker,
        "--argv",
    ] + list(argv)
    completed = subprocess.run(
        command,
        cwd=str(work),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        env=child_env(),
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"enfant {scenario} code={completed.returncode} "
            f"stderr={scrub(completed.stderr, opts.sentinel)}"
        )
    return parse_child(completed.stdout), completed.stdout


def run_parent(opts: argparse.Namespace) -> int:
    script = opts.script
    if not script.is_file():
        print(f"RESULT FAIL setup=script-absent path={script}")
        return 2
    if script.suffix.lower() != ".py":
        print(f"RESULT FAIL setup=script-non-python path={script}")
        return 2
    if not opts.argv:
        print("RESULT FAIL setup=argv-vide (placer --argv en dernier)")
        return 2

    try:
        source = script.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except (OSError, UnicodeDecodeError, SyntaxError) as exc:
        print(f"RESULT FAIL setup=lecture-ou-syntaxe {type(exc).__name__}: {exc}")
        return 2

    unsupported, writes = preflight(tree)
    if writes:
        print(f"RESULT FAIL setup=effet-de-bord-au-import {sorted(set(writes))}")
        return 2
    if unsupported and not opts.allow_unsupported:
        print(f"RESULT FAIL setup=api-non-espionnee {sorted(set(unsupported))}")
        print("NOTE utiliser --allow-unsupported seulement si l'entree testee ne les atteint pas")
        return 2
    if unsupported:
        print(f"WARN api-non-espionnee {sorted(set(unsupported))}")

    digest_before = sha256_file(script)
    size_before = script.stat().st_size
    cache_before = snapshot_cache(script)
    print(f"FIXTURE target={script}")
    print(f"FIXTURE sha256={digest_before} size={size_before}")
    print("PREFLIGHT OK ast.parse + aucun effet de bord de niveau module")

    base = Path.home() / ".qoder" / "tmp"
    try:
        base.mkdir(parents=True, exist_ok=True)
        work = Path(tempfile.mkdtemp(prefix="tester-garde-cli-", dir=str(base)))
    except OSError:
        work = Path(tempfile.mkdtemp(prefix="tester-garde-cli-"))
    print(f"FIXTURE work={work}")

    checks: list[tuple[bool, str]] = []

    def check(name: str, expected: object, actual: object) -> None:
        ok = expected == actual
        checks.append((ok, name))
        print(f"CHECK {name} expected={expected} actual={actual} {'OK' if ok else 'FAIL'}")

    def check_min(name: str, minimum: int, actual: int) -> None:
        ok = actual >= minimum
        checks.append((ok, name))
        print(f"CHECK {name} min={minimum} actual={actual} {'OK' if ok else 'FAIL'}")

    result = 2
    try:
        copy_path = work / "target_cli.py"
        shutil.copyfile(script, copy_path)
        copy_digest = sha256_file(copy_path)
        if copy_digest != digest_before:
            print(f"RESULT FAIL setup=copie-divergente source={digest_before} copie={copy_digest}")
            return 2

        deny_flag = list(opts.argv)
        allow_flag = list(opts.argv) + opts.allow_flag_list

        print(f"RUN scenario={DENY} argv={scrub(' '.join(deny_flag), opts.sentinel)}")
        deny, deny_raw = call_child(opts, DENY, opts.deny_marker, work, copy_path,
                                    deny_flag, opts.timeout)
        print(deny_raw.rstrip())
        check("deny.exit", opts.expect_deny_exit, int(deny["exit"]))
        check("deny.proc", opts.expect_deny_git, int(deny["proc"]))
        check("deny.git", opts.expect_deny_git, int(deny["git"]))
        check("deny.net", opts.expect_deny_net, int(deny["net"]))
        check("deny.import_proc", 0, int(deny["import_proc"]))
        check("deny.import_net", 0, int(deny["import_net"]))
        check("deny.marker", "yes" if opts.deny_marker else "na", deny["marker"])
        check("deny.leak", "no", deny["leak"])
        check("deny.argv_leak", "no", deny["argv_leak"])
        check("deny.phase", "none", deny["phase"])

        deny_ok = all(ok for ok, _ in checks)
        if not deny_ok:
            print(f"SKIP scenario={ALLOW} motif=refus-non-conforme (aucun credential simule)")
        else:
            print(f"RUN scenario={ALLOW} argv={scrub(' '.join(allow_flag), opts.sentinel)}")
            allow, allow_raw = call_child(opts, ALLOW, opts.allow_marker, work, copy_path,
                                          allow_flag, opts.timeout)
            print(allow_raw.rstrip())
            check("allow.git", opts.expect_allow_git, int(allow["git"]))
            check("allow.net", opts.expect_allow_net, int(allow["net"]))
            check("allow.import_proc", 0, int(allow["import_proc"]))
            check("allow.import_net", 0, int(allow["import_net"]))
            check("allow.marker", "yes" if opts.allow_marker else "na", allow["marker"])
            check("allow.leak", "no", allow["leak"])
            check("allow.argv_leak", "no", allow["argv_leak"])
            check("allow.phase", "none", allow["phase"])
            if opts.expect_allow_exit is None:
                print(f"INFO allow.exit={allow['exit']} (non asserte; chemin de succes bloque)")
            else:
                check("allow.exit", opts.expect_allow_exit, int(allow["exit"]))
            check_min("diff.git", int(deny["git"]) + 1, int(allow["git"]))
            check_min("diff.net", int(deny["net"]) + 1, int(allow["net"]))

        after_digest = sha256_file(script)
        check("target.sha256", digest_before, after_digest)
        new_cache = snapshot_cache(script) - cache_before
        check("target.cache", set(), new_cache)
        work_cache = sorted(str(path) for path in work.rglob("*.pyc"))
        check("work.cache", [], work_cache)

        failed = [name for ok, name in checks if not ok]
        print(f"SUMMARY checks={len(checks)} failed={len(failed)}")
        if failed:
            print(f"RESULT FAIL {failed}")
            result = 1
        else:
            print("RESULT PASS")
            result = 0
        return result
    except subprocess.TimeoutExpired:
        print(f"RESULT FAIL setup=timeout apres {opts.timeout}s")
        return 2
    except (OSError, RuntimeError) as exc:
        print(f"RESULT FAIL setup={scrub(str(exc), opts.sentinel)}")
        return 2
    finally:
        if work.exists():
            if opts.keep:
                print(f"KEPT work={work}")
            else:
                shutil.rmtree(work, ignore_errors=True)
                print(f"CLEANUP removed={not work.exists()}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tester_garde_cli.py",
        description=(
            "Fixture A/B hors production : prouve qu'un pre-controle CLI refuse avant "
            "tout sous-processus et tout acces reseau, sans fuite de jeton."
        ),
        epilog=(
            "Placer --argv en dernier. Exemple : "
            "py -3 tester_garde_cli.py --script C:/.../cli.py --deny-marker REFUSED "
            "--argv create --repo owner/repo --head fixture --title Fixture"
        ),
    )
    parser.add_argument("--script", type=Path, required=True, help="script Python cible")
    parser.add_argument("--argv", nargs=argparse.REMAINDER, default=[],
                        help="arguments du scenario refuse (doit rester en dernier)")
    parser.add_argument("--allow-flag", default="--yes",
                        help="drapeau ajoute au scenario autorise (forme --allow-flag=--force)")
    parser.add_argument("--entry", default="main", help="fonction d'entree du module cible")
    parser.add_argument("--sentinel", default=SENTINEL_DEFAULT,
                        help="jeton fictif recherche dans les sorties et argv")
    parser.add_argument("--api-root-attr", default="API_ROOT",
                        help="attribut du module remplace vers une URL locale non ecoutee")
    parser.add_argument("--api-root", default="http://127.0.0.1:9",
                        help="valeur de l'attribut reseau (port 9 ferme)")
    parser.add_argument("--deny-marker", default="", help="marqueur attendu dans le refus")
    parser.add_argument("--allow-marker", default="", help="marqueur attendu dans le chemin autorise")
    parser.add_argument("--expect-deny-exit", type=int, default=2)
    parser.add_argument("--expect-deny-git", type=int, default=0)
    parser.add_argument("--expect-deny-net", type=int, default=0)
    parser.add_argument("--expect-allow-exit", type=int, default=None)
    parser.add_argument("--expect-allow-git", type=int, default=1)
    parser.add_argument("--expect-allow-net", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=90)
    parser.add_argument("--keep", action="store_true", help="conserver le repertoire jetable")
    parser.add_argument("--allow-unsupported", action="store_true",
                        help="avertir au lieu d'echouer sur Popen, os.system ou requests")
    parser.add_argument("--child", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--scenario", choices=(DENY, ALLOW), default=DENY,
                        help=argparse.SUPPRESS)
    parser.add_argument("--marker", default="", help=argparse.SUPPRESS)
    return parser


def main(argv: list[str] | None = None) -> int:
    opts = build_parser().parse_args(argv)
    try:
        opts.allow_flag_list = opts.allow_flag.split()
        opts.argv = list(opts.argv)
        if opts.child:
            return run_child(opts)
        return run_parent(opts)
    except KeyboardInterrupt:
        print("RESULT FAIL setup=interrupted")
        return 2


if __name__ == "__main__":
    sys.exit(main())
