#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

from opentelemetry import trace
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor,ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.django import DjangoInstrumentor

def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

    resource = Resource(attributes={
        SERVICE_NAME: "AI-Cashier-System"
    })
    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)

    # 1. ยังคงส่งออกหน้าจอ Console ไว้ดู Error
    provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

    # 2. ส่งไป Jaeger ผ่าน HTTP (Port 4318) <-- เปลี่ยนตรงนี้
    # หมายเหตุ: ต้องมี /v1/traces ต่อท้ายสำหรับ HTTP
    try:
        otlp_exporter = OTLPSpanExporter(endpoint="http://localhost:4318/v1/traces")
        provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        print("--- [DEBUG] OTLP HTTP Exporter configured for localhost:4318 ---")
    except Exception as e:
        print(f"--- [ERROR] Setup failed: {e} ---")

    # 3. เริ่มดักจับ
    DjangoInstrumentor().instrument()
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
