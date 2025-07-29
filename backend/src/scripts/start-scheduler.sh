#!/bin/bash
set -o errexit
set -o nounset

export OTEL_PYTHON_LOG_CORRELATION=true
export OTEL_PYTHON_LOG_LEVEL=info
export OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED=true

container_id=$(cat /proc/self/cgroup | grep docker | cut -d'/' -f3 | head -n 1)
export OTEL_RESOURCE_ATTRIBUTES="container.id=${container_id},${OTEL_RESOURCE_ATTRIBUTES:-}"

if [ "${ASKPOLIS_DEV:-false}" = "true" ]; then
    watchfiles --filter python "\
        opentelemetry-instrument \
            --traces_exporter otlp_proto_grpc \
            --metrics_exporter otlp_proto_grpc \
            --logs_exporter otlp_proto_grpc \
            celery -A askpolis.celery:app beat \
            --loglevel=info" /app/src
else
    opentelemetry-instrument \
        --traces_exporter otlp_proto_grpc \
        --metrics_exporter otlp_proto_grpc \
        --logs_exporter otlp_proto_grpc \
        celery -A askpolis.celery:app beat \
        --loglevel=info
fi
