from opentelemetry import metrics, trace
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.trace import TracerProvider

from askpolis.main import app  # noqa: F401


def test_telemetry_providers_configured() -> None:
    assert isinstance(trace.get_tracer_provider(), TracerProvider)
    assert isinstance(metrics.get_meter_provider(), MeterProvider)
