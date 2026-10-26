#!/usr/bin/env bash
# Reproducibility preflight for a Windows/Git Bash autocrlf fixture.
# Read-only with respect to Skills: all work happens in a disposable temp root.
# ASCII output only (avoids cp1252 console failures on Windows).

set -u

PASS=0
FAIL=0
SKIP=0

pass() { PASS=$((PASS + 1)); echo "CHECK $1=PASS"; }
fail() { FAIL=$((FAIL + 1)); echo "CHECK $1=FAIL expected=[$2] got=[$3]"; }
skip() { SKIP=$((SKIP + 1)); echo "CHECK $1=SKIP $2"; }

if ! command -v git >/dev/null 2>&1; then
  echo "SETUP_FAIL git not found"
  echo "RESULT FAIL"
  exit 2
fi
if ! command -v od >/dev/null 2>&1; then
  echo "SETUP_FAIL od not found"
  echo "RESULT FAIL"
  exit 2
fi

ROOT_PARENT="${TMPDIR:-$HOME/.qoder/tmp}"
mkdir -p "$ROOT_PARENT" || { echo "SETUP_FAIL cannot create $ROOT_PARENT"; echo "RESULT FAIL"; exit 2; }
TMP="$ROOT_PARENT/fixture-autocrlf-$$-$(date +%s)"
mkdir -p "$TMP" || { echo "SETUP_FAIL cannot create $TMP"; echo "RESULT FAIL"; exit 2; }

cleanup() {
  if [ "${KEEP:-0}" = "1" ]; then
    echo "KEPT=$TMP"
  else
    rm -rf "$TMP"
    echo "CLEANED=$TMP"
  fi
}
trap cleanup EXIT

export GIT_CONFIG_COUNT=1
export GIT_CONFIG_KEY_0=core.autocrlf
export GIT_CONFIG_VALUE_0=true
export GIT_AUTHOR_NAME=fixture
export GIT_AUTHOR_EMAIL=fixture@example.invalid
export GIT_COMMITTER_NAME=fixture
export GIT_COMMITTER_EMAIL=fixture@example.invalid

echo "GIT_VERSION=$(git --version)"
HOST_AUTOCRLF="$(git config --get core.autocrlf 2>/dev/null || echo UNSET)"
echo "HOST_AUTOCRLF=$HOST_AUTOCRLF"

# --- Check 0: the env block overrides the host configuration -----------------
EFF="$(git config --get core.autocrlf 2>/dev/null || echo UNSET)"
if [ "$EFF" = "true" ]; then
  pass env_override
else
  fail env_override true "$EFF"
fi

# --- Check 1: rm + checkout produces CRLF and a clean status -----------------
mkdir -p "$TMP/t1"
(
  cd "$TMP/t1" || exit 1
  git init -q -b main .
  printf -- '---\nname: demo\ndescription: x\n---\n' > SKILL.md
  git add SKILL.md 2>/dev/null
  git commit -qm seed
  rm SKILL.md
  git checkout -- . 2>/dev/null
) || { echo "SETUP_FAIL t1"; echo "RESULT FAIL"; exit 2; }

T1="$TMP/t1"
EOL="$(git -C "$T1" ls-files --eol -- SKILL.md 2>/dev/null)"
case "$EOL" in
  *"i/lf"*"w/crlf"*) pass checkout_eol_i_lf_w_crlf ;;
  *) fail checkout_eol_i_lf_w_crlf "i/lf w/crlf" "$EOL" ;;
esac
HEX="$(od -An -tx1 "$T1/SKILL.md" 2>/dev/null | tr -d ' \n')"
case "$HEX" in
  *0d0a*) pass checkout_bytes_crlf ;;
  *) fail checkout_bytes_crlf "0d0a present" "absent" ;;
esac
ST="$(git -C "$T1" status --porcelain 2>/dev/null)"
if [ -z "$ST" ]; then
  pass checkout_status_clean
else
  fail checkout_status_clean "empty" "$ST"
fi

# --- Check 2: raw byte rewrite leaves a stale stat cache ---------------------
mkdir -p "$TMP/t2"
(
  cd "$TMP/t2" || exit 1
  git init -q -b main .
  printf 'a\nb\n' > f.txt
  git add f.txt 2>/dev/null
  git commit -qm t
  printf 'a\r\nb\r\n' > f.txt
) || { echo "SETUP_FAIL t2"; echo "RESULT FAIL"; exit 2; }

T2="$TMP/t2"
ST2="$(git -C "$T2" status --porcelain 2>/dev/null)"
if [ "$ST2" = " M f.txt" ]; then
  pass raw_rewrite_status_M
else
  fail raw_rewrite_status_M " M f.txt" "$ST2"
fi
git -C "$T2" diff --quiet 2>/dev/null
DQ=$?
if [ "$DQ" -eq 0 ]; then
  pass raw_rewrite_diff_quiet_0
else
  fail raw_rewrite_diff_quiet_0 0 "$DQ"
fi
git -C "$T2" update-index --refresh >/dev/null 2>&1
RF=$?
if [ "$RF" -eq 1 ]; then
  pass raw_rewrite_refresh_needs_update
else
  fail raw_rewrite_refresh_needs_update 1 "$RF"
fi
ST2B="$(git -C "$T2" status --porcelain 2>/dev/null)"
if [ "$ST2B" = " M f.txt" ]; then
  pass raw_rewrite_status_still_M
else
  fail raw_rewrite_status_still_M " M f.txt" "$ST2B"
fi
git -C "$T2" add f.txt 2>/dev/null
ST2C="$(git -C "$T2" status --porcelain 2>/dev/null)"
if [ -z "$ST2C" ]; then
  pass raw_rewrite_add_clears_cache
else
  fail raw_rewrite_add_clears_cache "empty" "$ST2C"
fi

# --- Check 3: which extractor preserves the trailing CR ----------------------
RAW="$(sed -n 's/^name:[[:space:]]*//p' "$T1/SKILL.md" | head -1)"
if [ "${#RAW}" -eq 4 ] && [ "$RAW" = "demo" ]; then
  pass msys_sed_strips_cr
else
  fail msys_sed_strips_cr "len=4 value=demo" "len=${#RAW} value=$RAW"
fi

if command -v py >/dev/null 2>&1; then
  LEN_L="$(cd "$T1" && PYTHONIOENCODING=utf-8 py -3 -c 'import sys; b=open("SKILL.md","rb").read().split(b"\n")[1].split(b":",1)[1].lstrip(b" "); print(len(b))' 2>/dev/null)"
  if [ "$LEN_L" = "5" ]; then
    pass py_lstrip_preserves_cr
  else
    fail py_lstrip_preserves_cr 5 "$LEN_L"
  fi
  LEN_S="$(cd "$T1" && PYTHONIOENCODING=utf-8 py -3 -c 'import sys; b=open("SKILL.md","rb").read().split(b"\n")[1].split(b":",1)[1].lstrip(b" ").strip(); print(len(b))' 2>/dev/null)"
  if [ "$LEN_S" = "4" ]; then
    pass py_strip_eats_cr
  else
    fail py_strip_eats_cr 4 "$LEN_S"
  fi
else
  skip py_lstrip_preserves_cr "py not found"
  skip py_strip_eats_cr "py not found"
fi

echo "SUMMARY PASS=$PASS FAIL=$FAIL SKIP=$SKIP"
if [ "$FAIL" -eq 0 ]; then
  echo "RESULT PASS"
  exit 0
fi
echo "RESULT FAIL"
exit 1
