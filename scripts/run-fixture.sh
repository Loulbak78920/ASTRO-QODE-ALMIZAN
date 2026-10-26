#!/usr/bin/env bash
# Disposable fixture for the "HEAD moved between review and commit" case.
# Path 1 (positive): adopt the existing commit after "nothing to commit".
# Path 2 (negative): same --stat but different OID must stop before push.
# No network, no live repository access, ASCII output only.
set -u
export LC_ALL=C

KEEP=0
case "${1:-}" in
  "") ;;
  --keep) KEEP=1 ;;
  -h|--help)
    printf 'usage: %s [--keep]\n' "$0"
    printf 'Runs both fixture paths in a fresh temp dir; removes it unless --keep.\n'
    exit 0
    ;;
  *)
    printf 'ERROR unknown option: %s\n' "$1" >&2
    exit 2
    ;;
esac

PASSED=0
FAILED=0
ROOT=""
CLEANED=0

cleanup() {
  [ "$CLEANED" -eq 1 ] && return 0
  CLEANED=1
  if [ -n "$ROOT" ] && [ -d "$ROOT" ] && [ -f "$ROOT/.fixture-marker" ]; then
    if [ "$KEEP" -eq 1 ]; then
      printf 'KEPT %s\n' "$ROOT"
      return 0
    fi
    rm -rf -- "$ROOT" 2>/dev/null \
      || { chmod -R u+w "$ROOT" 2>/dev/null; rm -rf -- "$ROOT" 2>/dev/null; }
  fi
}
trap cleanup EXIT

die() {
  printf 'ERROR %s\n' "$1" >&2
  exit 2
}

ok()  { PASSED=$((PASSED + 1)); printf 'PASS  %s\n' "$1"; }
bad() { FAILED=$((FAILED + 1)); printf 'FAIL  %s\n' "$1"; }
eq()  { if [ "$2" = "$3" ]; then ok "$1"; else bad "$1 (expected '$2', got '$3')"; fi; }
ne()  { if [ "$2" != "$3" ]; then ok "$1"; else bad "$1 (both '$2')"; fi; }

command -v git >/dev/null 2>&1 || die "git not found"
command -v sha256sum >/dev/null 2>&1 || die "sha256sum not found"

ROOT=$(mktemp -d "${TMPDIR:-/tmp}/commit-race-fixture.XXXXXX") \
  || die "mktemp failed"
: > "$ROOT/.fixture-marker" || die "cannot write fixture marker"
printf 'Fixture: %s\n' "$ROOT"
cd "$ROOT" || die "cannot enter fixture"

git -c init.defaultBranch=main init -q --bare origin.git >/dev/null 2>&1 \
  || die "git init failed"
git clone -q origin.git work >/dev/null 2>&1 || die "clone work failed"
git clone -q origin.git peer >/dev/null 2>&1 || die "clone peer failed"
for repo in work peer; do
  git -C "$repo" config user.name "Fixture" || die "config user.name failed"
  git -C "$repo" config user.email "fixture@example.invalid" || die "config user.email failed"
  git -C "$repo" config core.autocrlf true || die "config core.autocrlf failed"
  git -C "$repo" config commit.gpgsign false || die "config commit.gpgsign failed"
done
git -C work checkout -q -B main 2>/dev/null || true

{
  printf -- '---\r\n'
  printf 'name: fixture\r\n'
  printf 'description: Disposable fixture.\r\n'
  printf -- '---\r\n'
  printf '\r\n'
  printf '# Fixture\r\n'
  printf '\r\n'
  printf 'Baseline line for the concurrent-commit fixture.\r\n'
} > work/SKILL.md || die "cannot write baseline"
git -C work add SKILL.md || die "add baseline failed"
git -C work commit -q -m "chore: fixture baseline" || die "baseline commit failed"
git -C work push -q -u origin main >/dev/null 2>&1 || die "baseline push failed"
git -C origin.git symbolic-ref HEAD refs/heads/main || die "symbolic-ref failed"
git -C peer fetch -q origin main || die "peer fetch failed"
git -C peer checkout -q -B main FETCH_HEAD || die "peer checkout failed"
printf 'Baseline: origin/main %s\n' "$(git -C work rev-parse --short HEAD)"

# --- Path 1: another session commits the reviewed index ---
NONCE="$(date +%s)-$$"
printf 'RACE-REVIEWED-%s\r\n' "$NONCE" >> work/SKILL.md || die "append failed"
git -C work add SKILL.md || die "add reviewed failed"
reviewed_oid=$(git -C work rev-parse ":SKILL.md") || die "index OID failed"
worktree_oid=$(git -C work hash-object --path=SKILL.md SKILL.md) \
  || die "hash-object failed"
eq "index OID equals filtered worktree OID" "$reviewed_oid" "$worktree_oid"

worktree_sha=$(sha256sum work/SKILL.md | cut -d' ' -f1)
blob_sha=$(git -C work show :SKILL.md | sha256sum | cut -d' ' -f1)
ne "autocrlf: worktree SHA-256 differs from blob SHA-256" \
  "$worktree_sha" "$blob_sha"
eol_line=$(git -C work ls-files --eol -- SKILL.md)
case "$eol_line" in
  *i/lf*w/crlf*) ok "eol: index LF, worktree CRLF" ;;
  *) bad "eol: expected i/lf and w/crlf, got '$eol_line'" ;;
esac
stat_reviewed=$(git -C work diff --cached --stat -- SKILL.md | tail -n 1 | sed 's/^ *//')
printf 'Reviewed: oid=%s stat=%s\n' "$reviewed_oid" "$stat_reviewed"

git -C work -c user.name="Concurrent Session" \
  -c user.email="concurrent@example.invalid" \
  commit -q -m "feat: concurrent commit" || die "concurrent commit failed"
concurrent_head=$(git -C work rev-parse HEAD)
printf 'Concurrent: %s\n' "$concurrent_head"

commit_out=$(git -C work commit -m "feat: reviewed change" 2>&1)
commit_rc=$?
if [ "$commit_rc" -ne 0 ] && printf '%s' "$commit_out" | grep -qF "nothing to commit"; then
  ok "our commit fails with 'nothing to commit'"
else
  bad "our commit: rc=$commit_rc out='$commit_out'"
fi

head_oid=$(git -C work rev-parse "HEAD:SKILL.md") || die "HEAD OID failed"
eq "HEAD OID equals reviewed OID before push" "$reviewed_oid" "$head_oid"
if git -C work grep -qF "RACE-REVIEWED-$NONCE" HEAD -- SKILL.md; then
  ok "reviewed marker present in HEAD"
else
  bad "reviewed marker missing from HEAD"
fi
commits_before=$(git -C work rev-list --count HEAD)
eq "HEAD holds baseline + concurrent commit" "2" "$commits_before"

git -C work push -q origin main >/dev/null 2>&1 || die "push failed"
git -C work fetch -q origin || die "fetch failed"
eq "origin/main OID equals reviewed OID" "$reviewed_oid" \
  "$(git -C work rev-parse origin/main:SKILL.md)"
remote_oid=$(git -C work ls-remote origin refs/heads/main | awk '{print $1}')
eq "ls-remote equals local HEAD" "$(git -C work rev-parse HEAD)" "$remote_oid"
eq "no new commit created during adoption" "$commits_before" \
  "$(git -C work rev-list --count HEAD)"

# --- Path 2: same --stat, different content ---
printf 'RACE-REVIEWED-A-%s\r\n' "$NONCE" >> work/SKILL.md || die "append A failed"
git -C work add SKILL.md || die "add A failed"
reviewed_a=$(git -C work rev-parse ":SKILL.md") || die "index OID A failed"
stat_a=$(git -C work diff --cached --stat -- SKILL.md | tail -n 1 | sed 's/^ *//')
git -C work checkout -q HEAD -- SKILL.md || die "restore failed"
printf 'RACE-CONCURRENT-B-%s\r\n' "$NONCE" >> work/SKILL.md || die "append B failed"
git -C work add SKILL.md || die "add B failed"
git -C work -c user.name="Concurrent Session" \
  -c user.email="concurrent@example.invalid" \
  commit -q -m "feat: concurrent conflicting commit" || die "conflict commit failed"
head_b=$(git -C work rev-parse HEAD)
head_oid_b=$(git -C work rev-parse "HEAD:SKILL.md") || die "HEAD OID B failed"
stat_b=$(git -C work show --stat --format= HEAD -- SKILL.md | tail -n 1 | sed 's/^ *//')

ne "reviewed and HEAD OIDs differ" "$reviewed_a" "$head_oid_b"
eq "stat strings are identical (stat is only a hint)" "$stat_a" "$stat_b"
if git -C work grep -qF "RACE-REVIEWED-A-$NONCE" HEAD -- SKILL.md; then
  bad "reviewed-A marker unexpectedly present in HEAD"
else
  ok "reviewed-A marker absent from HEAD"
fi
if git -C work grep -qF "RACE-CONCURRENT-B-$NONCE" HEAD -- SKILL.md; then
  ok "concurrent-B marker present in HEAD"
else
  bad "concurrent-B marker missing from HEAD"
fi
remote_after=$(git -C work ls-remote origin refs/heads/main | awk '{print $1}')
ne "negative HEAD was not pushed" "$head_b" "$remote_after"
eq "remote still points to adopted commit" "$concurrent_head" "$remote_after"

printf 'Summary: %d passed, %d failed\n' "$PASSED" "$FAILED"
cleanup
if [ "$KEEP" -eq 0 ]; then
  if [ -e "$ROOT" ]; then
    bad "fixture directory still exists after cleanup"
  else
    ok "fixture directory removed"
  fi
fi
if [ "$FAILED" -ne 0 ]; then
  printf 'RESULT FAIL\n'
  exit 1
fi
printf 'RESULT PASS\n'
exit 0
