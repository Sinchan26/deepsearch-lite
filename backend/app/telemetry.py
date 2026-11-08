from opentelemetry import metrics, trace
from opentelemetry.metrics import MeterProvider
from opentelemetry.trace import TracerProvider

from app.domain.models import TerminalStatus


class Telemetry:
    """Explicit instrumentation avoids request headers, bodies and exception capture."""

    def __init__(
        self, tracer_provider: TracerProvider | None = None, meter_provider: MeterProvider | None = None
    ) -> None:
        self.tracer = (tracer_provider or trace.get_tracer_provider()).get_tracer("deepresearch.foundation")
        meter = (meter_provider or metrics.get_meter_provider()).get_meter("deepresearch.foundation")
        self.runs = meter.create_counter("research.runs.terminal")
        self.duration = meter.create_histogram("research.run.duration", unit="s")

    def terminal(self, status: TerminalStatus, elapsed: float) -> None:
        attributes = {"run.status": status}
        with self.tracer.start_as_current_span("research.terminal", attributes=attributes):
            self.runs.add(1, attributes)
            self.duration.record(max(0, elapsed), attributes)
