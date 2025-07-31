#!/bin/bash
set -o errexit
set -o nounset

export OTEL_PYTHON_LOG_CORRELATION=true
export OTEL_PYTHON_LOG_LEVEL=info
export OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED=true

container_id=$(cat /proc/self/cgroup | grep docker | cut -d'/' -f3 | head -n 1)
export OTEL_RESOURCE_ATTRIBUTES="container.id=${container_id},${OTEL_RESOURCE_ATTRIBUTES:-}"

alembic upgrade head

if [ "${ASKPOLIS_DEV:-false}" = "true" ]; then
  opentelemetry-instrument \
      --traces_exporter otlp_proto_grpc \
      --metrics_exporter otlp_proto_grpc \
      --logs_exporter otlp_proto_grpc \
      uvicorn askpolis.main:app \
      --host 0.0.0.0 \
      --port 8000 \
      --no-access-log \
      --reload \
      --reload-dir /app/src
else
  opentelemetry-instrument \
      --traces_exporter otlp_proto_grpc \
      --metrics_exporter otlp_proto_grpc \
      --logs_exporter otlp_proto_grpc \
      uvicorn askpolis.main:app \
      --host 0.0.0.0 \
      --port 8000 \
      --no-access-log
fi
