# Guidelines for AI Agents

## Project Structure

- `src/askpolis`: main application code
  - The directory structure is oriented on domain slices.
  - `main.py`: contains the FastAPI app
  - `celery.py`: contains the Celery configuration for the worker to process background jobs
- `src/alembic`: database migrations with Alembic
- `tests/unit`: unit tests
- `tests/integration`: integration tests
- `tests/end2end`: end-to-end tests

## Development Workflow

1. Ensure Python **3.12** is used.
2. Install dependencies with `poetry install`.
3. Install pre-commit hooks with `poetry run pre-commit install`.
4. Run pre-commit on changed files:
   ```bash
   poetry run pre-commit run --files <paths>
   ```
   This will apply `ruff` formatting and linting.
5. Run type checks with:
   ```bash
   poetry run mypy .
   ```
6. Run tests:
   - Unit tests: `poetry run pytest -v -m unit`
   - Do not run the `integration` nor the `end2end` tests. Docker is not available. They will fail.

## Code Style

- Keep line length under **120** characters and use double quotes for strings.
- Do not add dependencies. Only use the available libraries.
- Try to add unit tests for changes as you see fit.
- If you add logging code, use the logger from `logging.py`. It adds helper functions to log attributes properly.
