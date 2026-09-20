# Guidelines for AI Agents

## Project Structure

- `backend/`: the backend consisting of an API and background processing jobs
- `data/`: Datasets for backup and future use
- `demo/`: demo webapp using the backend to generate a simple demo website
- `docs/`: general project documentation, also technical notes
- `infrastructure/`: Kubernetes infrastructure configurations and settings for supporting tools
- `website/`: project website

## Commit Messages and PRs

- Use concise commit messages describing what changed and why.
- Use conventional commits and put the respective first-level directory in parentheses, e.g.:
  - `feat(backend): add feature xyz`
  - `refactor(backend): move files to domain folder xyz`
  - `feat(website): add info page`
  - `docs(data): improve docs about data from report xyz`
  - `chore: cleanup files in mono repository`
- Add a blank line and a descriptive body wrapped at 72 characters. Generated
  merge, revert, fixup, and squash messages are exempt from formatting rules.
- Never include agent attribution, co-author trailers, or thread/session IDs or
  links in commit messages. Both author and committer must be human identities.
- Install Lefthook before committing: `bash scripts/install-hooks.sh` from the
  repository root after installing backend dependencies. See `lefthook.yml`
  and `scripts/check-*.sh` for the enforced policy and its regression tests.
- Summarize important modifications in the PR description.
