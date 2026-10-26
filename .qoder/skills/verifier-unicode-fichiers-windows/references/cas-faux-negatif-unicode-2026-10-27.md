# Case: false negative on a Unicode marker (2026-10-27)

Source session: `f0fb0e02-dce6-49e7-84a7-dac4eae7e589` (2026-10-26).
Project JSONL: `C:/Users/Administrateur/.qoder/projects/C--Users-Administrateur-Desktop-IMAM8MAHDI/f0fb0e02-dce6-49e7-84a7-dac4eae7e589.jsonl`, line 120.
Snapshot fields: `cold`, `revision 0`, `hasMoreBefore=false`, one user turn, no user correction.

All text below is transcribed in ASCII. Non-ASCII characters appear as `\uXXXX` escapes; U+FFFD is written as `<U+FFFD>`.

## 1. The failing command (verbatim, from JSONL line 120)

```text
t="C:/Users/Administrateur/.qoder/skills/skill-staged-delivery"; echo "=== FILES ==="; ... ; py -3 - <<'PY'
from pathlib import Path
p=Path(r"C:/Users/Administrateur/.qoder/skills/skill-staged-delivery/SKILL.md")
b=p.read_bytes(); t=b.decode("utf-8")
...
markers = [
 "Distinguer les deux compteurs",
 "Cible cr\u00e9e par une autre session pendant le pr\u00e9flight",
 "Contr\u00f4le du 2026-10-26 (session de mise \u00e0 jour)",
]
for m in markers: print("count", t.count(m), "|", m)
for h in ["## Objectif","## Quand l'utiliser","## Contrat non n\u00e9gociable","## Proc\u00e9dure \u2014 \u00e9tape 1","## Proc\u00e9dure \u2014 \u00e9tape 2","## Erreurs et correctifs","## Checklist","## Ressources","## Provenance"]:
    print("header", t.count(h), "|", h)
PY
```

Key observation: the marker source is pure ASCII (`\u00e9` escapes), so no stdin decoding step can alter it. The second marker contains exactly one `\u00e9`.

## 2. The failing output (verbatim, U+FFFD marked)

```text
count 1 | Distinguer les deux compteurs
count 0 | Cible cr<U+FFFD>e par une autre session pendant le pr<U+FFFD>flight
count 1 | Contr<U+FFFD>le du 2026-10-26 (session de mise <U+FFFD> jour)
header 1 | ## Objectif
header 1 | ## Contrat non n<U+FFFD>gociable
...
```

The file line, read separately, is:

```text
| Cible cr\u00e9\u00e9e par une autre session pendant le pr\u00e9flight | ...
```

File: two `\u00e9`. Marker: one `\u00e9`. Therefore `count 0` is the correct result for a wrong marker, not evidence that the edit failed.

## 3. Reproduction on 2026-10-27

Environment: Python 3.14.7; `chcp` reports code page 850; `sys.stdin.encoding` = `cp1252`; `sys.stdout.encoding` = `cp1252`; `PYTHONUTF8` unset; `sys.flags.utf8_mode` = 0; Bash `LANG=C.UTF-8`.

Fixture: `target.txt` = 36 bytes, `Cible cr 303 251 303 251 e par une autre session\n`.

### A. Literal accented source through a heredoc

```bash
py -3 - <<'PY'
import sys
s = "Cible cr\u00e9\u00e9e"
print("STDIN_ENC", sys.stdin.encoding, "STDOUT_ENC", sys.stdout.encoding)
print("LEN", len(s), "ASCII", ascii(s))
print("TEXT", s)
PY
```

Observed:

```text
STDIN_ENC cp1252 STDOUT_ENC cp1252
LEN 11 ASCII 'Cible cr\xe9\xe9e'
TEXT Cible cr<U+FFFD><U+FFFD>e
```

`LEN 11` proves the source was decoded as UTF-8: a cp1252 decode of the UTF-8 bytes would give 14 characters. The U+FFFD appears only in the printed text, i.e. on the stdout side.

### B. Typo versus exact marker (ASCII escapes)

```bash
py -3 - <<'PY'
from pathlib import Path
t = Path("target.txt").read_text(encoding="utf-8")
for m in ["Cible cr\u00e9e", "Cible cr\u00e9\u00e9e"]:
    print("COUNT", t.count(m), "MARKER", ascii(m))
PY
```

Observed:

```text
COUNT 0 MARKER 'Cible cr\xe9e'
COUNT 1 MARKER 'Cible cr\xe9\xe9e'
```

### C. Independent channel (Git Bash, raw UTF-8)

```bash
grep -nF "$(printf '%b' 'Cible cr\xc3\xa9\xc3\xa9e')" target.txt
```

`\xc3\xa9` is the UTF-8 encoding of U+00E9. Do not pass `\u00e9` to `grep`: it is four literal characters there, not an accent.

Observed (ASCII transcription of the raw UTF-8 output):

```text
1:Cible cr\u00e9\u00e9e par une autre session
GREP_RC=0
```

### D. cp1252-encoded source through stdin

```bash
printf 's = "Cible cr\xe9\xe9e"\nprint(ascii(s))\n' | py -3 -
```

Observed:

```text
SyntaxError: Non-UTF-8 code starting with '\xe9' in file <stdin> on line 1, but no encoding declared
rc=1
```

So the input side fails loudly, it does not silently mangle.

### E. Validator on a wrongly named copy

```bash
mkdir -p wrong-name && cp .../skill-staged-delivery/SKILL.md wrong-name/SKILL.md
py -3 .../skill-file-qa/scripts/validate_skill.py wrong-name --workspace ... --stable-seconds 0
```

Observed:

```text
FAIL name: 'skill-staged-delivery' does not match directory 'wrong-name'
Summary: 8 pass, 1 fail, 0 warn
RESULT FAIL
rc=1
```

## 4. Classification

- REPRODUCED: a one-character missing accent yields `count 0`; the exact marker yields `count 1`; `grep -n` returns the line and exit 0.
- REPRODUCED: a literal UTF-8 source read from stdin is decoded as UTF-8 (`LEN 11`), while the printed text is corrupted on the cp1252 stdout side (U+FFFD).
- REPRODUCED: a cp1252-encoded source is rejected with `SyntaxError: Non-UTF-8 code` and exit 1.
- REPRODUCED: `validate_skill.py` reports `FAIL name` when the directory differs from `name`, exit 1.
- REFUTED: "the heredoc source was decoded as cp1252 and the marker literal was mangled before comparison". The historical command was pure ASCII escapes, and the reproduction shows UTF-8 source decoding on this machine. The mangled display is an output-side artifact.
- UNVERIFIED: other Python versions, other ANSI code pages, PowerShell invocation, and the exact historical stdout bytes (only U+FFFD is observable in the transcript).

## 5. Boundary

This case documents an assertion method, not the semantics of the content being asserted. `count 1` proves the substring exists; it does not prove the surrounding sentence is correct, and it does not replace reading the line.

## 6. Control

- Target: `C:/Users/Administrateur/.qoder/skills/verifier-unicode-fichiers-windows/SKILL.md`
- Size: 9215 bytes; lines: 128; SHA-256: `7913670ec33cc49ee320862859e5aaaa9f6ff3a3bacd32493a907e76cb4afd22`
- mtime: 2026-10-27T00:17:14+01:00
- This case file is pure ASCII; SKILL.md is not. SKILL.md's fingerprint is recorded here because it changes whenever SKILL.md changes.
