# Guidelines for Codex

## Project Structure
- `backend/`: Python API, data processing, and tests using Poetry
- `data/`, `docs/`, and `website/`: additional assets and documentation

## Development Workflow
1. Ensure Python **3.12** is used.
2. Install dependencies with `poetry install` from within `backend/`.
3. Run pre-commit on changed files:
   ```bash
   pre-commit run --files <paths>
   ```
   This will apply `ruff` formatting and linting.
4. Type check with:
   ```bash
   poetry run mypy .
   ```
5. Run tests:
   - Unit tests: `poetry run pytest -v -m unit`
   - Integration tests: `poetry run pytest -v -m integration`
   - End-to-end tests: `poetry run pytest -v -m e2e`

If tests fail due to missing containers or network limits, mention this in the PR summary.

## Contribution Notes
- Keep line length under **120** characters and use double quotes for strings.
- Update `pyproject.toml` and `poetry.lock` together when adding dependencies.
- Document relevant changes in `README.md` or under `docs/` when applicable.
- When creating the PR summary or answer, cite lines using the `F:<path>` format as instructed by the system.
