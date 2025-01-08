FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

ENV PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

ENV HF_HOME=/app/models

FROM base AS builder

RUN pip install --no-compile --no-cache-dir poetry==1.8.5

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN poetry install --only main --no-root && \
    rm -rf $POETRY_CACHE_DIR

FROM base AS model

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

RUN pip install --no-cache-dir "huggingface_hub[cli]"
RUN huggingface-cli download "jinaai/jina-embeddings-v3" --exclude "onnx/*" --exclude "*.onnx"
RUN huggingface-cli download "jinaai/xlm-roberta-flash-implementation" --exclude "onnx/*" --exclude "*.onnx"

# This is a hack because jina-embeddings-v3 is referencing a custom xlm-roberta model and downloads it once
# This workaround triggers the fetching and the model is stored in the cache
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('jinaai/jina-embeddings-v3', local_files_only=True, trust_remote_code=True)"

FROM base AS runtime

ENV HF_HUB_OFFLINE=1
ENV TRANSFORMERS_OFFLINE=1

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}
COPY --from=model ${HF_HOME} ${HF_HOME}

WORKDIR /app

COPY src/ ./
