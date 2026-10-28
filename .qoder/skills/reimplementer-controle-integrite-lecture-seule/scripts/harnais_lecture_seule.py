#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Harnais hors installation pour le comparateur d'integrite en lecture seule.

Le fixture est cree dans un repertoire temporaire, jamais dans l'installation.
Il verifie la matrice des codes de sortie, la precedence PERTE > DERIVE >
CHURN > OK, le mode --strict, la lecture tolerante du journal, l'absence de
__pycache__, et surtout qu'aucun fichier du fixture n'a change apres les runs.

Usage :
  py -3 -B harnais_lecture_seule.py [--script CHEMIN]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PASS = 0
FAIL = 0


def emit(texte: str) -> None:
    sys.stdout.write(texte.encode("ascii", "backslashreplace").decode("ascii") + "\n")


def check(nom: str, condition: bool, detail: str = "") -> None:
    global PASS, FAIL
    if condition:
        PASS += 1
        emit(f"PASS {nom}" + (f" | {detail}" if detail else ""))
    else:
        FAIL += 1
        emit(f"FAIL {nom}" + (f" | {detail}" if detail else ""))


def write(chemin: Path, texte: str) -> None:
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(texte, encoding="utf-8")


def fingerprint(base: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for p in sorted(base.rglob("*")):
        if p.is_file():
            out[p.relative_to(base).as_posix()] = hashlib.sha256(
                p.read_bytes()
            ).hexdigest()
    return out


def run(
    base: Path,
    script: Path,
    *args: str,
    plan: Path | None = None,
    env_extra: dict[str, str] | None = None,
) -> tuple[int, str, str]:
    plan_path = plan or (base / "plan.json")
    cmd = [
        sys.executable,
        "-B",
        str(script),
        "--plan",
        str(plan_path),
        "--base",
        str(base),
        *args,
    ]
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "ascii"
    if env_extra:
        env.update(env_extra)
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
        env=env,
    )
    return proc.returncode, proc.stdout, proc.stderr


def ascii_ok(texte: str) -> bool:
    try:
        texte.encode("ascii")
        return True
    except UnicodeEncodeError:
        return False


PLAN = {
    "zones": [
        {
            "name": "code",
            "live_root": "live/src",
            "ref_roots": ["ref/src"],
            "include": ["**/*.py"],
            "exclude_dirs": ["__pycache__", ".git"],
            "exclude_globs": ["_verify_*.py"],
            "policy": "blocking",
        },
        {
            "name": "data",
            "live_root": "live/data",
            "ref_roots": ["ref/data"],
            "include": ["*.json"],
            "exclude_dirs": ["__pycache__"],
            "exclude_globs": [],
            "policy": "churn",
        },
    ],
    "journal": {
        "path": "live/logs/events.jsonl",
        "key_field": "cle",
        "phase_field": "phase",
        "phase_value": "guerison",
        "ok_field": "ok",
        "churn_prefixes": ["data/"],
    },
}


def main() -> int:
    ap = argparse.ArgumentParser(description="Harnais du comparateur d'integrite.")
    ap.add_argument(
        "--script",
        default=str(Path(__file__).with_name("controle_integrite_lecture_seule.py")),
        help="chemin du comparateur",
    )
    args = ap.parse_args()
    script = Path(args.script).resolve()
    if not script.is_file():
        emit(f"RESULT FAIL script_absent={script}")
        return 1

    base = Path(tempfile.mkdtemp(prefix="integrite-lecture-seule-"))
    live = base / "live"
    ref = base / "ref"
    journal = live / "logs" / "events.jsonl"
    try:
        write(live / "src" / "foo.py", "X = 1\n")
        write(ref / "src" / "foo.py", "X = 1\n")
        write(live / "data" / "a.json", '{"a": 1}\n')
        write(ref / "data" / "a.json", '{"a": 1}\n')
        write(journal, "")
        write(base / "plan.json", json.dumps(PLAN, ensure_ascii=False, indent=2))
        before = fingerprint(base)

        rc, out, err = run(base, script)
        check("A_baseline_rc0", rc == 0, f"rc={rc}")
        check("A_baseline_result", "RESULT OK" in out)
        check(
            "A_baseline_summary",
            "VERIFIES=2 SAME=2 NOUVEAUX=0 ECARTS=0 PERTES=0 "
            "DERIVES=0 CHURN=0 ILLISIBLES=0"
            in out,
        )
        check("A_ascii", ascii_ok(out) and ascii_ok(err))

        rc, out, _ = run(base, script, "--all")
        check("B_all_same", rc == 0 and out.count("ETAT=SAME") == 2, f"rc={rc}")

        rc, out, _ = run(base, script, "--only", "code:foo.py")
        check("C_only", rc == 0 and "VERIFIES=1 SAME=1" in out, f"rc={rc}")

        rc, out, _ = run(base, script, "--only", "absent.py")
        check(
            "C_only_absent_rc2",
            rc == 2 and "RESULT USAGE only_sans_correspondance" in out,
            f"rc={rc}",
        )

        write(live / "src" / "foo.py", "X = 2\n")
        rc, out, _ = run(base, script)
        check("D_code_diff_rc1", rc == 1, f"rc={rc}")
        check("D_code_diff_line", "CLE=foo.py ETAT=DIFF ZONE=code" in out)
        check("D_code_diff_result", "RESULT DERIVE 1 code=1 churn=0" in out)
        write(live / "src" / "foo.py", "X = 1\n")

        write(live / "data" / "a.json", '{"a": 2}\n')
        rc, out, _ = run(base, script)
        check("E_churn_rc0", rc == 0, f"rc={rc}")
        check("E_churn_result", "RESULT CHURN 1" in out)
        check("E_churn_line", "CLE=a.json ETAT=DIFF ZONE=data" in out)

        rc, out, _ = run(base, script, "--strict")
        check("F_strict_rc1", rc == 1, f"rc={rc}")
        check("F_strict_result", "RESULT DERIVE 1 code=0 churn=1" in out)
        write(live / "data" / "a.json", '{"a": 1}\n')

        write(ref / "src" / "gone.py", "Y = 1\n")
        write(live / "src" / "foo.py", "X = 2\n")
        rc, out, _ = run(base, script)
        check("G_perte_rc1", rc == 1, f"rc={rc}")
        check("G_perte_result", "RESULT PERTE 1" in out)
        check("G_perte_line", "CLE=gone.py ETAT=ABSENT_LIVE ZONE=code" in out)
        check("G_perte_precedence", "RESULT DERIVE" not in out)
        (ref / "src" / "gone.py").unlink()
        write(live / "src" / "foo.py", "X = 1\n")

        write(live / "src" / "new.py", "Z = 1\n")
        rc, out, _ = run(base, script, "--all")
        check("H_new_rc0", rc == 0, f"rc={rc}")
        check("H_new_line", "CLE=new.py ETAT=ABSENT_REF ZONE=code" in out)
        check("H_new_result", "RESULT OK" in out)
        (live / "src" / "new.py").unlink()

        longue = (
            '{"phase":"guerison","ok":true,"cle":"data/big.json",'
            '"t":"2026-01-01T00:00:00Z","pad":"'
            + ("x" * 70000)
            + '"}\n'
        )
        valide1 = (
            '{"phase":"guerison","ok":true,"cle":"data/a.json",'
            '"t":"2026-01-02T00:00:00Z"}\n'
        )
        valide2 = (
            '{"phase":"guerison","ok":true,"cle":"src/foo.py",'
            '"t":"2026-01-03T00:00:00Z"}\n'
        )
        write(journal, longue + valide1 + valide2 + '{"phase": broken\n')
        rc, out, _ = run(
            base,
            script,
            "--journal-lines",
            "5",
            "--since",
            "2026-01-01T00:00:00Z",
        )
        check("I_journal_rc0", rc == 0, f"rc={rc}")
        check(
            "I_journal_counts",
            "JOURNAL_EVENEMENTS=2 JOURNAL_CODE_EVENEMENTS=1" in out,
            out.splitlines()[-2] if out else "",
        )
        rc, out, _ = run(
            base,
            script,
            "--journal-lines",
            "5",
            "--since",
            "2026-01-02T12:00:00Z",
        )
        check(
            "I_journal_since",
            "JOURNAL_EVENEMENTS=1 JOURNAL_CODE_EVENEMENTS=1" in out,
            out.splitlines()[-2] if out else "",
        )
        rc, out, _ = run(
            base, script, "--journal", "absent.jsonl", "--journal-lines", "1"
        )
        check(
            "I_journal_explicit_missing_rc2",
            rc == 2 and "RESULT USAGE journal_absent" in out,
            f"rc={rc}",
        )
        write(journal, "")

        plan_live = json.loads(json.dumps(PLAN))
        plan_live["zones"][0]["live_root"] = "absent"
        chemin_plan = base / "plan_missing_live.json"
        write(chemin_plan, json.dumps(plan_live, ensure_ascii=False, indent=2))
        rc, out, _ = run(base, script, plan=chemin_plan)
        check("J_missing_live_rc2", rc == 2 and "RESULT USAGE" in out, f"rc={rc}")
        chemin_plan.unlink()

        plan_ref = json.loads(json.dumps(PLAN))
        plan_ref["zones"][0]["ref_roots"] = ["absent-ref"]
        chemin_plan = base / "plan_missing_ref.json"
        write(chemin_plan, json.dumps(plan_ref, ensure_ascii=False, indent=2))
        rc, out, _ = run(base, script, plan=chemin_plan)
        check("J_missing_ref_rc2", rc == 2 and "RESULT USAGE" in out, f"rc={rc}")
        chemin_plan.unlink()

        rc, out, err = run(
            base, script, env_extra={"PYTHONIOENCODING": "cp1252"}
        )
        check(
            "K_cp1252",
            rc == 0 and "UnicodeEncodeError" not in err,
            f"rc={rc}",
        )
        check("K_ascii_still", ascii_ok(out))

        apres = fingerprint(base)
        check(
            "L_readonly_tree",
            apres == before,
            f"before={len(before)} after={len(apres)}",
        )
        check(
            "L_no_pycache",
            not any(base.rglob("__pycache__"))
            and not any(script.parent.rglob("__pycache__")),
        )
        check(
            "L_no_pyc",
            not any(script.parent.rglob("*.pyc")),
        )
    finally:
        shutil.rmtree(base, ignore_errors=False)

    emit(f"RESULT {'PASS' if FAIL == 0 else 'FAIL'} pass={PASS} fail={FAIL}")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
