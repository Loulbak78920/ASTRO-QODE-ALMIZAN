#!/usr/bin/env python3
"""Compare une page HTML d'origine et sa copie PROTO_ de layout.

Controle que seule la structure a change : script inline identique,
adresses 0x identiques, noeuds de texte identiques, balises equilibrees,
et original inchange par rapport a une empreinte enregistree.
"""

import argparse
import hashlib
import json
import os
import re
import sys
from collections import Counter

VOID_ELEMENTS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}

STYLE_RE = re.compile(r"<style\b[^>]*>.*?</style\s*>", re.IGNORECASE | re.DOTALL)
SCRIPT_RE = re.compile(r"<script\b[^>]*>(.*?)</script\s*>", re.IGNORECASE | re.DOTALL)
COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
TAG_RE = re.compile(r"<(/)?([A-Za-z][A-Za-z0-9:-]*)([^>]*)>", re.DOTALL)
ADDRESS_RE = re.compile(r"\b0x[0-9a-fA-F]{40}\b")


def configure_stdout():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
        sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")
    except AttributeError:
        pass


def fail_usage(message):
    print("ERROR: " + message, file=sys.stderr)
    sys.exit(2)


def read_html(path):
    try:
        with open(path, "rb") as handle:
            raw = handle.read()
    except OSError as exc:
        fail_usage("cannot read {}: {}".format(path, exc.strerror))
    try:
        return raw, raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        fail_usage("not valid UTF-8: {} ({})".format(path, exc.reason))


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def strip_style_script(html):
    html = STYLE_RE.sub(" ", html)
    html = SCRIPT_RE.sub(" ", html)
    return COMMENT_RE.sub(" ", html)


def extract_scripts(html):
    return [m.group(1) for m in SCRIPT_RE.finditer(html)]


def extract_addresses(html):
    return Counter(m.lower() for m in ADDRESS_RE.findall(strip_style_script(html)))


def extract_text_nodes(html):
    body = strip_style_script(html)
    nodes = []
    for part in re.split(r"<[^>]+>", body):
        part = re.sub(r"\s+", " ", part).strip()
        if part:
            nodes.append(part)
    return Counter(nodes)


def tag_errors(html):
    body = strip_style_script(html)
    stack = []
    errors = []
    for match in TAG_RE.finditer(body):
        closing, name, rest = match.group(1), match.group(2).lower(), match.group(3)
        if name in VOID_ELEMENTS or rest.rstrip().endswith("/"):
            continue
        if not closing:
            stack.append(name)
            continue
        if stack and stack[-1] == name:
            stack.pop()
            continue
        errors.append("unexpected </{}>".format(name))
        if name in stack:
            while stack and stack[-1] != name:
                stack.pop()
            if stack:
                stack.pop()
    if stack:
        errors.append("unclosed {}".format(", ".join(stack[:5])))
    return errors


def describe(value):
    text = json.dumps(value, ensure_ascii=True)
    return text if len(text) <= 160 else text[:157] + "..."


def print_counter_diff(label, original, prototype, limit=5):
    keys = sorted(set(original) | set(prototype))
    shown = 0
    for key in keys:
        left = original.get(key, 0)
        right = prototype.get(key, 0)
        if left == right:
            continue
        print("  {} original x{} / prototype x{}: {}".format(
            label, left, right, describe(key)))
        shown += 1
        if shown >= limit:
            remaining = sum(
                1 for k in keys if original.get(k, 0) != prototype.get(k, 0)
            ) - shown
            if remaining > 0:
                print("  ... {} autre(s) ecart(s)".format(remaining))
            break


def record_baseline(path, baseline_path):
    raw, _ = read_html(path)
    stat = os.stat(path)
    payload = {
        "original": os.path.abspath(path),
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "sha256": sha256(raw),
    }
    parent = os.path.dirname(os.path.abspath(baseline_path))
    if parent and not os.path.isdir(parent):
        fail_usage("baseline directory does not exist: " + parent)
    with open(baseline_path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=True, indent=2) + "\n")
    print("Baseline written: {}".format(baseline_path))
    print("  size={} mtime_ns={} sha256={}".format(
        payload["size"], payload["mtime_ns"], payload["sha256"]))
    sys.exit(0)


def load_baseline(baseline_path):
    try:
        with open(baseline_path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except OSError as exc:
        fail_usage("cannot read baseline {}: {}".format(
            baseline_path, exc.strerror))
    except ValueError as exc:
        fail_usage("invalid baseline JSON {}: {}".format(baseline_path, exc))
    for key in ("size", "mtime_ns", "sha256"):
        if key not in payload:
            fail_usage("baseline missing key: " + key)
    return payload


def main():
    parser = argparse.ArgumentParser(
        description="Verifie qu'un prototype HTML ne change que la structure.")
    parser.add_argument("--original", required=True,
                        help="page HTML d'origine (jamais modifiee)")
    parser.add_argument("--prototype",
                        help="copie PROTO_ a comparer")
    parser.add_argument("--baseline",
                        help="JSON d'empreinte de l'original")
    parser.add_argument("--record-baseline",
                        help="ecrire l'empreinte de l'original dans ce JSON")
    args = parser.parse_args()

    if args.record_baseline:
        record_baseline(args.original, args.record_baseline)

    if not args.prototype:
        parser.error("--prototype est requis hors --record-baseline")

    original_raw, original_html = read_html(args.original)
    prototype_raw, prototype_html = read_html(args.prototype)

    failures = 0

    print("FILE original  size={} sha256={}".format(
        len(original_raw), sha256(original_raw)))
    print("FILE prototype size={} sha256={}".format(
        len(prototype_raw), sha256(prototype_raw)))

    if args.baseline:
        baseline = load_baseline(args.baseline)
        stat = os.stat(args.original)
        current = {
            "size": stat.st_size,
            "mtime_ns": stat.st_mtime_ns,
            "sha256": sha256(original_raw),
        }
        diffs = [key for key in current if current[key] != baseline[key]]
        if diffs:
            failures += 1
            print("CHECK original-unchanged FAIL fields=" + ",".join(diffs))
            for key in diffs:
                print("  {} baseline={} current={}".format(
                    key, baseline[key], current[key]))
        else:
            print("CHECK original-unchanged PASS size={} mtime_ns={}".format(
                current["size"], current["mtime_ns"]))
    else:
        print("CHECK original-unchanged SKIP (no --baseline)")

    if original_raw == prototype_raw:
        failures += 1
        print("CHECK differentiated FAIL prototype is byte-identical to original")
    else:
        print("CHECK differentiated PASS")

    original_scripts = extract_scripts(original_html)
    prototype_scripts = extract_scripts(prototype_html)
    if original_scripts != prototype_scripts:
        failures += 1
        print("CHECK scripts FAIL blocks original={} prototype={}".format(
            len(original_scripts), len(prototype_scripts)))
        for index, (left, right) in enumerate(
                zip(original_scripts, prototype_scripts)):
            if left != right:
                print("  block {} differs: original {} / prototype {}".format(
                    index, describe(left), describe(right)))
        if len(original_scripts) != len(prototype_scripts):
            print("  block count differs; remaining blocks not compared")
    else:
        print("CHECK scripts PASS blocks={}".format(len(original_scripts)))

    original_addresses = extract_addresses(original_html)
    prototype_addresses = extract_addresses(prototype_html)
    if original_addresses != prototype_addresses:
        failures += 1
        print("CHECK addresses FAIL occurrences original={} prototype={}".format(
            sum(original_addresses.values()), sum(prototype_addresses.values())))
        print_counter_diff("address", original_addresses, prototype_addresses)
    else:
        print("CHECK addresses PASS occurrences={} unique={}".format(
            sum(original_addresses.values()), len(original_addresses)))

    original_nodes = extract_text_nodes(original_html)
    prototype_nodes = extract_text_nodes(prototype_html)
    if original_nodes != prototype_nodes:
        failures += 1
        print("CHECK text FAIL nodes original={} prototype={}".format(
            sum(original_nodes.values()), sum(prototype_nodes.values())))
        print_counter_diff("text", original_nodes, prototype_nodes)
    else:
        print("CHECK text PASS nodes={}".format(sum(original_nodes.values())))

    original_errors = tag_errors(original_html)
    prototype_errors = tag_errors(prototype_html)
    if original_errors:
        failures += 1
        print("CHECK tags FAIL original unbalanced: " +
              "; ".join(original_errors[:5]))
    if prototype_errors:
        failures += 1
        print("CHECK tags FAIL prototype unbalanced: " +
              "; ".join(prototype_errors[:5]))
    if not original_errors and not prototype_errors:
        print("CHECK tags PASS")

    print("RESULT: " + ("FAIL" if failures else "PASS"))
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    configure_stdout()
    main()
