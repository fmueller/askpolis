#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
checker="$script_dir/check-author.sh"

fail() {
  printf 'FAIL: %s\n' "$*" >&2
  exit 1
}

assert_accepts() {
  local identity="$1"
  if ! output="$(bash "$checker" "$identity" 2>&1)"; then
    fail "$identity was rejected: $output"
  fi
}

assert_rejects() {
  local identity="$1"
  if output="$(bash "$checker" "$identity" 2>&1)"; then
    fail "$identity was accepted"
  fi
  if [[ "$output" != *"agent identity"* ]]; then
    fail "$identity did not report the policy: $output"
  fi
}

assert_accepts 'Felix Müller <felix@fmueller.io>'
assert_accepts 'Amparo Ruiz <amparo@example.com>'
assert_accepts 'Bottger Lang <bottger@example.com>'

assert_rejects 'Amp <amp@ampcode.com>'
assert_rejects 'Someone <someone@ampcode.com>'
assert_rejects 'Claude <noreply@anthropic.com>'
assert_rejects 'Claude Opus 5 <claude@example.com>'
assert_rejects 'Cursor Agent <agent@cursor.com>'
assert_rejects 'github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com>'
assert_rejects 'dependabot[bot] <49699333+dependabot[bot]@users.noreply.github.com>'
assert_rejects 'Build Bot <build@example.com>'
assert_rejects 'Someone <agent@example.com>'
assert_rejects 'Someone <bot@example.com>'
assert_rejects 'GitHub Actions <github-actions@github.com>'
assert_rejects 'Renovate <renovate@whitesourcesoftware.com>'
assert_rejects 'Buildkite <buildkite@example.com>'

if output="$(GIT_AUTHOR_NAME=Person GIT_AUTHOR_EMAIL=person@example.com \
  GIT_COMMITTER_NAME=Amp GIT_COMMITTER_EMAIL=amp@ampcode.com bash "$checker" 2>&1)"; then
  fail "an agent committer was accepted with a human author"
fi
[[ "$output" == *"agent identity"* ]] || fail "missing committer policy diagnostic: $output"

printf 'author checks passed\n'
