#!/usr/bin/env bash
set -euo pipefail

source_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT
repo="$tmp_dir/repo with spaces"
mkdir -p "$repo/backend" "$repo/scripts"
git init -q "$repo"
cp "$source_root/lefthook.yml" "$repo/"
cp "$source_root"/scripts/*.sh "$repo/scripts/"
cp "$source_root/backend/pyproject.toml" "$repo/backend/"
ln -s "$source_root/backend/.venv" "$repo/backend/.venv"
cd "$repo"
git config user.name Fixture
git config user.email fixture@example.com
git config commit.gpgsign false
mkdir "$tmp_dir/external-hooks"
printf 'preserve me\n' > "$tmp_dir/external-hooks/pre-commit"
git config core.hooksPath "$tmp_dir/external-hooks"

bash scripts/install-hooks.sh
bash scripts/install-hooks.sh
[[ "$(cat "$tmp_dir/external-hooks/pre-commit")" == 'preserve me' ]]
[[ "$(git config --local core.hooksPath)" == "$repo/.git/hooks" ]]
for hook in pre-commit commit-msg pre-push; do
    [[ -x ".git/hooks/$hook" ]]
done

# Exercise installed hooks, not just their scripts. Keep the fixture small so
# the full-project type check and unit tests are tested separately in AskPolis.
printf 'hello\n' > 'note with spaces.txt'
git add 'note with spaces.txt'
git commit -qm $'docs: add a note\n\nExplain the note.'
printf 'hello  \r\n' > 'note with spaces.txt'
git add 'note with spaces.txt'
if git commit -qm $'docs: update a note\n\nExplain the change.'; then
    echo 'FAIL: file hygiene accepted whitespace and CRLF' >&2
    exit 1
fi
[[ "$(cat 'note with spaces.txt')" == hello ]]
git add 'note with spaces.txt'
printf 'another note\n' > other.txt
git add other.txt
if git commit -qm 'invalid message' > "$tmp_dir/message.log" 2>&1; then
    echo 'FAIL: installed commit-msg hook accepted an invalid message' >&2
    exit 1
fi
grep -q 'Conventional Commit' "$tmp_dir/message.log"

# A redirected pre-push protocol must reach the scanner and terminate.
clean_head="$(git rev-parse HEAD)"
git -c core.hooksPath="$tmp_dir/no-hooks" commit -qm $'docs: bad attribution\n\nCo-Authored-By: Bot <bot@example.com>'
if printf 'refs/heads/main %s refs/heads/main %s\n' "$(git rev-parse HEAD)" "$clean_head" \
    | timeout 10 poetry -P backend run lefthook run pre-push --command message-policy > "$tmp_dir/push.log" 2>&1; then
    echo 'FAIL: Lefthook accepted attributed history' >&2
    exit 1
fi
grep -q 'automated-attribution' "$tmp_dir/push.log" || { cat "$tmp_dir/push.log"; exit 1; }

# Lefthook hides unstaged hunks from fixers and restores them afterward.
printf 'staged line\n' > partial.txt
git add partial.txt
printf 'unfinished line  \n' >> partial.txt
worktree_before="$(git hash-object partial.txt)"
index_before="$(git rev-parse :partial.txt)"
poetry -P backend run lefthook run pre-commit --command file-hygiene
[[ "$(git hash-object partial.txt)" == "$worktree_before" ]]
[[ "$(git rev-parse :partial.txt)" == "$index_before" ]]

printf 'hook integration checks passed\n'
