#!/usr/bin/env bash
# Read-only outside the disposable fixture; writes only under ~/.qoder/tmp.
set -u

usage() {
  printf 'usage: %s [--target <skill-dir>]\n' "$0" >&2
}

TARGET=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --target)
      [ "$#" -ge 2 ] || { usage; exit 2; }
      TARGET=$2
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      usage
      exit 2
      ;;
  esac
done

if [ -n "$TARGET" ]; then
  [ -f "$TARGET/SKILL.md" ] || { printf 'target missing SKILL.md: %s\n' "$TARGET" >&2; exit 2; }
fi

PASS=0
FAIL=0

ok() { # name actual expected
  if [ "$2" = "$3" ]; then
    PASS=$((PASS + 1))
    printf 'PASS %s\n' "$1"
  else
    FAIL=$((FAIL + 1))
    printf 'FAIL %s | expected=[%s] actual=[%s]\n' "$1" "$3" "$2"
  fi
}

okc() { # name haystack needle
  case "$2" in
    *"$3"*) PASS=$((PASS + 1)); printf 'PASS %s\n' "$1" ;;
    *) FAIL=$((FAIL + 1)); printf 'FAIL %s | missing=[%s] actual=[%s]\n' "$1" "$3" "$2" ;;
  esac
}

mkdir -p "$HOME/.qoder/tmp"
WORK=$(mktemp -d "$HOME/.qoder/tmp/triage-fixture.XXXXXX") || {
  printf 'cannot create fixture root\n' >&2
  exit 2
}
printf 'WORK=%s\n' "$WORK"

cleanup() {
  [ -e "$WORK" ] || return 0
  chmod -R u+w "$WORK" 2>/dev/null || true
  rm -rf "$WORK" 2>/dev/null || true
}
trap 'cleanup' EXIT

write_skill() { # dir name body
  mkdir -p "$1"
  printf -- '---\nname: %s\ndescription: "fixture"\n---\n\n%s\n' "$2" "$3" > "$1/SKILL.md"
}

snap() {
  local root=${1%/}
  [ -d "$root" ] || return 0
  find "$root" -mindepth 2 -maxdepth 2 -name SKILL.md -print0 |
    while IFS= read -r -d '' f; do
      rel=${f#"$root"/}
      rel=${rel%/SKILL.md}
      printf '%s|%s|%s\n' "$rel" \
        "$(stat -c '%s' "$f")" \
        "$(sha256sum "$f" | cut -d' ' -f1)"
    done | LC_ALL=C sort
}

state_of() { # key plan_root pre_root
  local key=$1 pl pr
  pl=$(snap "$2" | awk -F'|' -v k="$key" '$1 == k')
  pr=$(snap "$3" | awk -F'|' -v k="$key" '$1 == k')
  if [ -z "$pl" ] && [ -z "$pr" ]; then
    printf 'CREATE\n'
  elif [ -z "$pl" ]; then
    printf 'ADOPT_RACE_APPEARED\n'
  elif [ -z "$pr" ]; then
    printf 'VANISHED\n'
  elif [ "$pl" = "$pr" ]; then
    printf 'UPDATE\n'
  else
    printf 'ADOPT_RACE_CHANGED\n'
  fi
}

files_at_top() {
  find "$1" -maxdepth 1 -type f -printf '%f\n' | LC_ALL=C sort | tr '\n' ' '
}

# ---------- fixtures ----------
for c in update_diff update_mtime appeared changed create vanished same_size; do
  mkdir -p "$WORK/$c/plan" "$WORK/$c/pre"
done

write_skill "$WORK/update_diff/plan/u1" u1 "same body v1"
write_skill "$WORK/update_diff/pre/u1" u1 "same body v1"

write_skill "$WORK/update_mtime/plan/u2" u2 "same body v2"
write_skill "$WORK/update_mtime/pre/u2" u2 "same body v2"
touch -t 202601010101 "$WORK/update_mtime/plan/u2/SKILL.md"
touch -t 202601020202 "$WORK/update_mtime/pre/u2/SKILL.md"

write_skill "$WORK/appeared/pre/a1" a1 "appeared body"
write_skill "$WORK/changed/plan/c1" c1 "body v1"
write_skill "$WORK/changed/pre/c1" c1 "body v2-longer"
write_skill "$WORK/vanished/plan/v1" v1 "vanished body"
write_skill "$WORK/same_size/plan/s1" s1 "body 1111"
write_skill "$WORK/same_size/pre/s1" s1 "body 2222"

# ---------- four states + guard ----------
ok "state.update_diff_roots" "$(state_of u1 "$WORK/update_diff/plan" "$WORK/update_diff/pre")" "UPDATE"
ok "state.update_mtime" "$(state_of u2 "$WORK/update_mtime/plan" "$WORK/update_mtime/pre")" "UPDATE"
ok "state.appeared" "$(state_of a1 "$WORK/appeared/plan" "$WORK/appeared/pre")" "ADOPT_RACE_APPEARED"
ok "state.changed" "$(state_of c1 "$WORK/changed/plan" "$WORK/changed/pre")" "ADOPT_RACE_CHANGED"
ok "state.create" "$(state_of k1 "$WORK/create/plan" "$WORK/create/pre")" "CREATE"
ok "state.vanished" "$(state_of v1 "$WORK/vanished/plan" "$WORK/vanished/pre")" "VANISHED"
ok "state.changed_same_size" "$(state_of s1 "$WORK/same_size/plan" "$WORK/same_size/pre")" "ADOPT_RACE_CHANGED"

# ---------- preconditions: the two regressions must not be vacuous ----------
mtime_plan=$(stat -c '%Y' "$WORK/update_mtime/plan/u2/SKILL.md")
mtime_pre=$(stat -c '%Y' "$WORK/update_mtime/pre/u2/SKILL.md")
if [ "$mtime_plan" != "$mtime_pre" ]; then
  ok "precondition.mtime_differs" "yes" "yes"
else
  ok "precondition.mtime_differs" "no" "yes"
fi

size_plan=$(stat -c '%s' "$WORK/same_size/plan/s1/SKILL.md")
size_pre=$(stat -c '%s' "$WORK/same_size/pre/s1/SKILL.md")
if [ "$size_plan" = "$size_pre" ]; then
  ok "precondition.same_size" "yes" "yes"
else
  ok "precondition.same_size" "no" "yes"
fi

# ---------- cleanliness ----------
mkdir -p "$WORK/clean-target/.git"
write_skill "$WORK/clean-target" clean-target "clean body"
mkdir -p "$WORK/dirty-target"
write_skill "$WORK/dirty-target" dirty-target "dirty body"
printf 'residue\n' > "$WORK/dirty-target/extra.txt"

ok "clean.git_metadata_ignored" "$(files_at_top "$WORK/clean-target")" "SKILL.md "
okc "clean.extra_file_detected" "$(files_at_top "$WORK/dirty-target")" "extra.txt"

# ---------- optional real target ----------
if [ -n "$TARGET" ]; then
  before_sha=$(sha256sum "$TARGET/SKILL.md" | cut -d' ' -f1)
  before_meta=$(stat -c '%s|%Y' "$TARGET/SKILL.md")
  # Exercise the snapshot path without writing to the target.
  snap "$(dirname "$TARGET")" >/dev/null
  after_sha=$(sha256sum "$TARGET/SKILL.md" | cut -d' ' -f1)
  after_meta=$(stat -c '%s|%Y' "$TARGET/SKILL.md")
  ok "target.sha_unchanged" "$after_sha" "$before_sha"
  ok "target.size_mtime_unchanged" "$after_meta" "$before_meta"
fi

# ---------- cleanup and gate ----------
cleanup
if [ -e "$WORK" ]; then
  ok "cleanup.work_removed" "no" "yes"
else
  ok "cleanup.work_removed" "yes" "yes"
fi
trap - EXIT

EXPECTED=12
[ -n "$TARGET" ] && EXPECTED=$((EXPECTED + 2))
TOTAL=$((PASS + FAIL))

printf '\nRESULT PASS=%s FAIL=%s TOTAL=%s EXPECTED=%s\n' "$PASS" "$FAIL" "$TOTAL" "$EXPECTED"
if [ "$FAIL" -ne 0 ] || [ "$PASS" -ne "$EXPECTED" ] || [ "$TOTAL" -ne "$EXPECTED" ]; then
  printf 'GATE FAIL\n'
  exit 1
fi
printf 'GATE PASS\n'
exit 0
