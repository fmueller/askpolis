# Backend

Tha backend of AskPolis. It contains the main application: the API, analytical backend and scraping of the data.

## Local checks and Git hooks

Use Python 3.12 and Poetry 2.2.1. From the repository root:

```bash
poetry -C "$(pwd)/backend" install
bash scripts/install-hooks.sh
```

Lefthook replaces the pre-commit framework. Its version and checkers are locked
by Poetry; `pre-commit-hooks` remains only as a library of file-hygiene commands.
Installation replaces this repository's hooks and sets a repository-local
`core.hooksPath` pointing to the common Git hooks directory (also for worktrees).
It does not overwrite globally configured hook files. Fresh orbs install these
hooks automatically through `.agents/setup`.

Before commits, hooks check identities, conflict markers, file hygiene, Ruff,
and mypy. Python checks do not auto-fix; file-hygiene fixers require restaging.
Commit messages use Conventional Commits with a descriptive body wrapped at 72
characters. Agent attribution, co-author trailers, and session links are refused.
Before pushes, hooks scan outgoing commit attribution and identities, then run
unit tests. Docker integration and end-to-end tests remain separate.

Run the hooks manually from the repository root:

```bash
poetry -P backend run lefthook run pre-commit
bash scripts/check-commit-msg-test.sh
bash scripts/check-author-test.sh
bash scripts/check-push-messages-test.sh
bash scripts/check-hooks-test.sh
```

## Development with Docker

The Dockerfile supports a development mode used by `compose.yaml`. When the
environment variable `ASKPOLIS_DEV` is set to `true`, the container reloads the
`src` folder on changes.

Start the stack with:

```bash
docker compose up --build
```
