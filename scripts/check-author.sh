#!/usr/bin/env bash
# Refuse a commit authored by an agent identity.
#
# The message policy keeps agent attribution out of commit messages, but the
# author and committer headers carry an identity of their own: a commit written
# through an agent runner keeps that runner's name and address unless the
# runner's git config is overridden. GitHub then credits the agent account for
# the change, which is the same claim the forbidden trailers make, expressed in
# the header instead of the body.
#
# The identity is taken from git itself, so the check sees exactly what the
# commit will record, including a GIT_AUTHOR_* override. An explicit
# "Name <email>" argument is accepted for testing.
set -euo pipefail

identity="${1:-}"
if [ -z "$identity" ]; then
  # `git var` renders "Name <email> <timestamp> <zone>"; the trailing stamp is
  # not part of the identity and would only widen what the patterns can hit.
  for header in GIT_AUTHOR_IDENT GIT_COMMITTER_IDENT; do
    bash "${BASH_SOURCE[0]}" "$(git var "$header" | sed -E 's/> [0-9]+ [+-][0-9]{4}$/>/')"
  done
  exit 0
fi

if printf '%s' "$identity" | grep -qiE '<[^>]*@(ampcode\.com|anthropic\.com|openai\.com|cursor\.(com|sh)|devin\.ai)>' \
  || printf '%s' "$identity" | grep -qiE '^(amp|claude|codex|copilot|cursor|devin|agent|bot|github[ -]actions|dependabot|renovate|buildkite)([[:space:]]|<|-)' \
  || printf '%s' "${identity%%<*}" | grep -qiE '\[bot\]|(^|[[:space:]_-])(agent|bot)([[:space:]_-]|$)' \
  || printf '%s' "$identity" | grep -qiE '<(amp|claude|codex|copilot|cursor|devin|agent|bot)(-?agent)?@'; then
  echo "check-author: refusing a commit authored by an agent identity:" >&2
  echo "  $identity" >&2
  echo "set user.name and user.email to a person before committing" >&2
  exit 1
fi
