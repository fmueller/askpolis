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

FROM base AS builder_prebuilt

WORKDIR /app

COPY pyproject.toml poetry.lock ./
# Expect a prebuilt venv tarball in the build context
COPY .venv.tgz /tmp/prebuilt_venv.tgz

# Extract, re-home to image Python, and normalize console scripts
RUN set -euo pipefail; \
    mkdir -p /app/.venv && tar -xzf /tmp/prebuilt_venv.tgz -C /app/.venv; \
    python3 -m venv --upgrade /app/.venv; \
    VENV_BIN="/app/.venv/bin"; \
    if [ -x "${VENV_BIN}/python3" ] && [ ! -e "${VENV_BIN}/python" ]; then ln -s python3 "${VENV_BIN}/python"; fi; \
    PY="$( [ -x "${VENV_BIN}/python" ] && echo "${VENV_BIN}/python" || echo "${VENV_BIN}/python3" )"; \
    for f in "${VENV_BIN}"/*; do \
      [ -f "$f" ] || continue; \
      if head -c 2 "$f" 2>/dev/null | grep -q '^#!'; then \
        sed -i '1s@^#!.*$@#!'"$PY"'@' "$f"; \
        sed -i 's/\r$//' "$f"; \
        chmod +x "$f"; \
      fi; \
    done

FROM base AS builder_poetry

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
    python -m pip freeze | grep -E "(torch|nvidia-|triton)" | xargs -r python -m pip uninstall -y && \
    python -m pip install --index-url https://download.pytorch.org/whl/cpu torch~=2.8.0 && \
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

# Runtime stage using the prebuilt venv
FROM base AS runtime_prebuilt

ENV HF_HUB_CACHE=${HF_HOME}/hub
ENV HF_HUB_OFFLINE=1
ENV TRANSFORMERS_OFFLINE=1

RUN addgroup --system app && adduser --system --ingroup app app

COPY --from=builder_prebuilt --chown=app:app ${VIRTUAL_ENV} ${VIRTUAL_ENV}
COPY --from=model --chown=app:app ${HF_HOME} ${HF_HOME}

WORKDIR /app

COPY --chown=app:app src/ ./
RUN chmod +x ./scripts/*.sh

USER app

# Runtime stage building deps with Poetry inside image
FROM base AS runtime_poetry

ENV HF_HUB_CACHE=${HF_HOME}/hub
ENV HF_HUB_OFFLINE=1
ENV TRANSFORMERS_OFFLINE=1

RUN addgroup --system app && adduser --system --ingroup app app

COPY --from=builder_poetry --chown=app:app ${VIRTUAL_ENV} ${VIRTUAL_ENV}
COPY --from=model --chown=app:app ${HF_HOME} ${HF_HOME}

WORKDIR /app

COPY --chown=app:app src/ ./
RUN chmod +x ./scripts/*.sh

USER app

# Default final image (keeps compatibility with builds that target "runtime" or no target)
FROM runtime_poetry AS runtime
