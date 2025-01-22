#!/bin/bash
set -o errexit
set -o nounset

export OTEL_PYTHON_LOG_CORRELATION=true
export OTEL_PYTHON_LOG_LEVEL=info
export OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED=true

opentelemetry-instrument \
    --traces_exporter otlp_proto_grpc \
    --metrics_exporter otlp_proto_grpc \
    --logs_exporter otlp_proto_grpc \
    celery -A askpolis.celery:app worker \
    --loglevel=info \
    --concurrency=1
