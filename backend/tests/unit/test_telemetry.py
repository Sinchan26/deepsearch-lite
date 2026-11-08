from app.telemetry import Telemetry
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter


def test_payload_free_instrumentation():
    spans = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(spans))
    reader = InMemoryMetricReader()
    meter = MeterProvider(metric_readers=[reader])
    telemetry = Telemetry(provider, meter)
    telemetry.terminal("cancelled", 2.5)
    recorded = spans.get_finished_spans()
    assert len(recorded) == 1
    assert dict(recorded[0].attributes) == {"run.status": "cancelled"}
    data = reader.get_metrics_data()
    metrics = data.resource_metrics[0].scope_metrics[0].metrics
    assert {m.name for m in metrics} == {"research.runs.terminal", "research.run.duration"}
    for metric in metrics:
        for point in metric.data.data_points:
            assert dict(point.attributes) == {"run.status": "cancelled"}
    provider.shutdown()
    meter.shutdown()
