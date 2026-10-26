#!/usr/bin/env python3
"""Read-only directory fingerprint gate.

Exit codes:
  0  every sample identical (path set, size, mtime_ns, sha256)
  1  a file changed, appeared or disappeared during sampling
  2  usage or environment error

STABLE (0) means no writes were observed inside the sampling window.
It does not mean the writer session ended; confirm runtimeState=cold and
activeTurnId=null before editing.
"""
import argparse
import hashlib
import sys
import time
from pathlib import Path


def emit(text):
    sys.stdout.write(text + "\n")
    sys.stdout.flush()


def snapshot(root):
    rows = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        try:
            data = path.read_bytes()
            mtime_ns = path.stat().st_mtime_ns
        except OSError as exc:
            raise OSError("read failed: %s (%s)" % (ascii(rel), exc.__class__.__name__))
        rows[rel] = (len(data), mtime_ns, hashlib.sha256(data).hexdigest())
    return rows


def aggregate(rows):
    digest = hashlib.sha256()
    for rel in sorted(rows):
        size, mtime_ns, sha = rows[rel]
        digest.update(("%s\0%d\0%d\0%s\n" % (rel, size, mtime_ns, sha)).encode("utf-8"))
    return digest.hexdigest()[:12]


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Read-only directory fingerprint gate. STABLE does not mean the session ended."
    )
    parser.add_argument("directory")
    parser.add_argument("--samples", type=int, default=4)
    parser.add_argument("--interval", type=float, default=6.0)
    args = parser.parse_args(argv)

    if args.samples < 2:
        emit("ERROR samples must be >= 2")
        return 2
    if args.interval < 0:
        emit("ERROR interval must be >= 0")
        return 2

    root = Path(args.directory)
    if not root.is_dir():
        emit("ERROR directory not found: %s" % ascii(str(root)))
        return 2

    first = None
    previous = None
    previous_fp = None
    for index in range(1, args.samples + 1):
        try:
            rows = snapshot(root)
        except OSError as exc:
            emit("RESULT CHANGED reason=%s" % ascii(str(exc)))
            return 1

        fingerprint = aggregate(rows)
        emit("SAMPLE %d files=%d fingerprint=%s" % (index, len(rows), fingerprint))

        if first is None:
            first = rows
        elif fingerprint != previous_fp or rows.keys() != previous.keys():
            added = sorted(set(rows) - set(previous))
            removed = sorted(set(previous) - set(rows))
            modified = sorted(k for k in set(rows) & set(previous) if rows[k] != previous[k])
            emit(
                "RESULT CHANGED at sample %d: added=%d removed=%d modified=%d"
                % (index, len(added), len(removed), len(modified))
            )
            for label, items in (("ADDED", added), ("REMOVED", removed), ("MODIFIED", modified)):
                for item in items[:20]:
                    emit("%s %s" % (label, ascii(item)))
            return 1

        previous = rows
        previous_fp = fingerprint
        if index < args.samples:
            time.sleep(args.interval)

    emit("RESULT STABLE samples=%d files=%d fingerprint=%s"
         % (args.samples, len(first), aggregate(first)))
    emit("NOTE STABLE means no writes in the window; confirm runtimeState=cold and activeTurnId=null before editing.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        emit("ERROR interrupted")
        sys.exit(2)
    except Exception as exc:
        emit("ERROR %s: %s" % (exc.__class__.__name__, ascii(str(exc))))
        sys.exit(2)
