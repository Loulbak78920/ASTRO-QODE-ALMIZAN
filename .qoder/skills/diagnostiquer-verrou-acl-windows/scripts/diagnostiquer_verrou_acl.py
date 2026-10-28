#!/usr/bin/env python3
"""Triage en lecture seule d'un refus d'ecriture Windows (attribut R vs ACE DENY)."""

import argparse
import json
import os
import re
import stat
import subprocess
import sys

RIGHTS = {
    "DE": "delete", "DC": "delete_child", "WDAC": "write_dac", "WO": "write_owner",
    "S": "synchronize", "WD": "write_data", "AD": "append_data", "WEA": "write_ea",
    "WA": "write_attributes", "REA": "read_ea", "RA": "read_attributes",
    "X": "execute", "RD": "read_data", "RC": "read_control",
    "AS": "access_system_security", "MA": "maximum_allowed",
}
SIMPLE = {
    "F": ["delete", "read_control", "write_dac", "write_owner", "synchronize", "write_data",
          "append_data", "write_ea", "execute", "read_ea", "read_attributes", "write_attributes"],
    "M": ["delete", "read_control", "synchronize", "write_data", "append_data",
          "write_ea", "execute", "read_ea", "read_attributes", "write_attributes"],
    "W": ["synchronize", "write_data", "append_data", "write_ea", "write_attributes"],
}
MSYS_PATH = re.compile(r"^/([A-Za-z])/(.*)$")


def ascii_safe(value):
    return str(value).encode("ascii", "replace").decode("ascii")


def normalize_path(raw):
    match = MSYS_PATH.match(raw)
    if match:
        return match.group(1).upper() + ":\\" + match.group(2).replace("/", "\\")
    return os.path.abspath(raw)


def chain(path):
    nodes = [path]
    current = path if os.path.isdir(path) else os.path.dirname(path)
    while True:
        parent = os.path.dirname(current)
        if parent == current:
            break
        nodes.append(parent)
        current = parent
    return nodes


def decode_mask(raw):
    rights = []
    for token in raw.split(","):
        token = token.strip()
        if not token or token == "N":
            continue
        rights.extend(SIMPLE.get(token) or [RIGHTS.get(token, token.lower())])
    return rights


def parse_aces(output, path):
    aces = []
    for line in output.splitlines():
        rest = line.strip()
        if not rest:
            continue
        if rest.lower().startswith(path.lower()):
            rest = rest[len(path):].strip()
        cut = rest.rfind(":(")
        if cut < 0:
            continue
        principal, tags = rest[:cut].strip(), rest[cut + 1:]
        groups = re.findall(r"\(([^)]*)\)", tags)
        if not groups:
            continue
        kind = next((i for i, g in enumerate(groups) if g in ("DENY", "ALLOW")), None)
        if kind is None:
            # icacls n'imprime pas "(ALLOW)" : le dernier groupe porte le masque.
            ace_kind, mask, flags = "ALLOW", groups[-1], groups[:-1]
        else:
            ace_kind = groups[kind]
            mask = groups[kind + 1] if kind + 1 < len(groups) else ""
            flags = groups[:kind]
        aces.append({
            "principal": principal,
            "kind": ace_kind,
            "rights": decode_mask(mask),
            "mask": mask,
            "inherited": "I" in flags,
            "inherit_only": "IO" in flags,
            "container": "OI" in flags or "CI" in flags,
            "source": path,
        })
    return aces


def inspect(path):
    if not os.path.exists(path):
        return {"error": "path_not_found", "path": path}
    attributes = getattr(os.stat(path), "st_file_attributes", 0)
    readonly = bool(attributes & stat.FILE_ATTRIBUTE_READONLY)
    is_dir = os.path.isdir(path)
    nodes = chain(path)
    aces, errors = [], []
    for node in nodes:
        try:
            proc = subprocess.run(["icacls", node], capture_output=True)
        except FileNotFoundError:
            return {"error": "icacls_not_found", "path": path}
        if proc.returncode != 0:
            errors.append({"path": node, "returncode": proc.returncode})
            continue
        text = proc.stdout.decode("oem", "replace") if proc.stdout else ""
        aces.extend(parse_aces(text, node))
    denied = [a for a in aces if a["kind"] == "DENY" and not a["inherit_only"]]
    applying = [a for a in denied if a["source"] == path or a["container"]]
    rights = sorted({r for a in applying for r in a["rights"]})
    allows_full = any(a["kind"] == "ALLOW" and "F" in a["mask"]
                      and a["principal"] in {d["principal"] for d in applying} for a in aces)
    if applying:
        verdict, action, code = "STOP_DENY", "ask_user_before_takeown_or_icacls", 10
    elif readonly:
        verdict, action, code = "ATTRIBUTE_ONLY", "clearing_the_read_only_attribute_is_safe", 0
    else:
        verdict, action, code = "NO_DENY_FOUND", "proceed", 0
    return {
        "target": path, "kind": "dir" if is_dir else "file", "readonly": readonly,
        "ancestors_checked": len(nodes), "denied_applying": applying,
        "all_denied_same_tree": denied, "denied_rights": rights,
        "allow_full_coexists": allows_full, "icacls_errors": errors,
        "can_write_data": not any(r in rights for r in ("write_data", "append_data")),
        "can_write_attributes": "write_attributes" not in rights,
        "can_edit_acl": not any(r in rights for r in ("write_dac", "write_owner")),
        "can_delete": not any(r in rights for r in ("delete", "delete_child")),
        "verdict": verdict, "action": action, "code": code,
    }


def render(report):
    lines = ["TOOL acl-verrou/1", "TARGET " + ascii_safe(report["target"]),
             "TARGET_KIND " + report["kind"],
             "READONLY_ATTR " + str(report["readonly"]),
             "ANCESTORS_CHECKED " + str(report["ancestors_checked"])]
    for ace in report["denied_applying"]:
        lines.append("ACE DENY principal=%s mask=%s rights=%s scope=%s inherited=%s source=%s" % (
            ascii_safe(ace["principal"]), ace["mask"], ",".join(ace["rights"]),
            "container" if ace["container"] else "object",
            "yes" if ace["inherited"] else "no", ascii_safe(ace["source"])))
    lines += ["ALLOW_F_COEXISTS " + ("yes" if report["allow_full_coexists"] else "no"),
              "DENY_RIGHTS " + (",".join(report["denied_rights"]) or "none"),
              "CAN_WRITE_DATA " + str(report["can_write_data"]),
              "CAN_WRITE_ATTRIB " + str(report["can_write_attributes"]),
              "CAN_EDIT_ACL " + str(report["can_edit_acl"]),
              "CAN_DELETE " + str(report["can_delete"])]
    for err in report["icacls_errors"]:
        lines.append("ICACLS_ERROR path=%s rc=%s" % (ascii_safe(err["path"]), err["returncode"]))
    lines += ["VERDICT " + report["verdict"], "ACTION " + report["action"]]
    return lines


def main():
    parser = argparse.ArgumentParser(
        description="Diagnostic en lecture seule: attribut lecture seule ou ACE DENY Windows.")
    parser.add_argument("path", help="fichier ou dossier a diagnostiquer")
    parser.add_argument("--json", action="store_true", help="sortie JSON")
    args = parser.parse_args()
    report = inspect(normalize_path(args.path))
    if "error" in report:
        print("ERROR " + ascii_safe(report["error"]))
        print("TARGET " + ascii_safe(report["path"]))
        return 2
    if args.json:
        print(json.dumps({k: v for k, v in report.items() if k != "code"},
                         ensure_ascii=True, indent=2))
    else:
        for line in render(report):
            print(line)
    return report["code"]


if __name__ == "__main__":
    sys.exit(main())
