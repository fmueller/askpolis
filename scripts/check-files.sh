#!/usr/bin/env bash
# Keep the old file-hygiene checks without the pre-commit framework or its venvs.
# Lefthook runs this inside Poetry, so the pinned checker CLIs are on PATH.
set -euo pipefail
(( $# )) || exit 0

status=0
check() {
    "$@" || status=1
}

# Git excludes binary files; -z preserves whitespace in names. Empty files need
# no whitespace repair. Run fixers sequentially so they cannot race each other.
mapfile -d '' text_files < <(git grep -Ilz -e '' -- "$@" || true)
if ((${#text_files[@]})); then
    check end-of-file-fixer "${text_files[@]}"
    check mixed-line-ending --fix=lf "${text_files[@]}"
    check trailing-whitespace-fixer "${text_files[@]}"
fi
for file in "$@"; do
    [[ -f "$file" && ! -L "$file" ]] || continue
    case "$file" in
        *.toml) check check-toml "$file" ;;
        *.yaml | *.yml) check check-yaml "$file" ;;
        *.json) check pretty-format-json --autofix --indent=2 "$file" ;;
    esac
    case "$file" in
        */tests/*.py) check name-tests-test "$file" ;;
    esac
done
exit "$status"
