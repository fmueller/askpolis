FROM python:3.12.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

ENV PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

ENV HF_HOME=/app/models
ENV ASKPOLIS_DEV=false
ENV PYTHONPATH=/app/src

FROM base AS builder

RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-compile --no-cache-dir poetry==2.1.3

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN poetry install --only main --no-root && \
    rm -rf $POETRY_CACHE_DIR

FROM base AS model

ARG DISABLE_HUGGINGFACE_DOWNLOAD=false
RUN pip install --no-cache-dir huggingface_hub[cli]==0.32.4
RUN if [ "$DISABLE_HUGGINGFACE_DOWNLOAD" != "true" ]; then \
        huggingface-cli download "BAAI/bge-m3" --exclude "onnx/*" --exclude "*.onnx" && \
        huggingface-cli download "BAAI/bge-reranker-v2-m3" --exclude "onnx/*" --exclude "*.onnx"; \
    else \
        echo "Skipping Hugging Face model download because DISABLE_HUGGINGFACE_DOWNLOAD is true" && \
        mkdir -p /app/models; \
    fi

FROM base AS runtime

ENV HF_HUB_CACHE=${HF_HOME}/hub
ENV HF_HUB_OFFLINE=1
ENV TRANSFORMERS_OFFLINE=1

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}
COPY --from=model ${HF_HOME} ${HF_HOME}

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app

COPY src/ ./
RUN chmod +x ./scripts/*.sh && chown -R app:app /app

USER app
