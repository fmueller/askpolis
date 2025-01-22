#!/bin/bash
set -o errexit
set -o pipefail
set -o nounset

export OTEL_PYTHON_LOG_CORRELATION=true
export OTEL_PYTHON_LOG_LEVEL=info
export OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED=true

alembic upgrade head

opentelemetry-instrument \
    --traces_exporter otlp_proto_grpc \
    --metrics_exporter otlp_proto_grpc \
    --logs_exporter otlp_proto_grpc \
    uvicorn askpolis.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --no-access-log
