#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

# Install into the common Git directory for worktree support.
# Override an inherited hooksPath locally without overwriting its global files.
git config --local core.hooksPath "$(git rev-parse --path-format=absolute --git-common-dir)/hooks"
poetry -P backend run lefthook install --force
