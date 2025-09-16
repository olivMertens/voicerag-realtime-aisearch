"""
OpenTelemetry configuration for tracking tool calls and model usage
"""
import os
import time
import json
from typing import Dict, Any, Optional, List
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.aiohttp_client import AioHttpClientInstrumentor
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.trace.status import Status, StatusCode
from opentelemetry.semconv.trace import SpanAttributes
import logging

logger = logging.getLogger("telemetry")

class TelemetryCollector:
    def __init__(self):
        self.tracer = None
        self.meter = None
        self.tool_calls: List[Dict[str, Any]] = []
        self.model_calls: List[Dict[str, Any]] = []
        self._setup_telemetry()
    
    def _setup_telemetry(self):
        """Setup OpenTelemetry with OTLP exporters"""
        # Resource information
        resource = Resource.create({
            "service.name": "maif-maaf-voice-assistant",
            "service.version": "1.0.0",
            "service.instance.id": "backend-instance"
        })
        
        # Setup tracer
        trace.set_tracer_provider(TracerProvider(resource=resource))
        self.tracer = trace.get_tracer(__name__)
        
        # Setup OTLP exporter (can be configured to send to Azure Monitor, Jaeger, etc.)
        otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
        
        try:
            span_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
            span_processor = BatchSpanProcessor(span_exporter)
            trace.get_tracer_provider().add_span_processor(span_processor)
            logger.info(f"✅ OpenTelemetry configured with OTLP endpoint: {otlp_endpoint}")
        except Exception as e:
            logger.warning(f"⚠️ OTLP exporter not available: {e}")
        
        # Setup metrics
        try:
            metric_reader = PeriodicExportingMetricReader(
                OTLPMetricExporter(endpoint=otlp_endpoint),
                export_interval_millis=10000  # Export every 10 seconds
            )
            metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=[metric_reader]))
            self.meter = metrics.get_meter(__name__)
        except Exception as e:
            logger.warning(f"⚠️ Metrics not available: {e}")
            
        # Instrument HTTP clients
        HTTPXClientInstrumentor().instrument()
        AioHttpClientInstrumentor().instrument()
    
    def trace_tool_call(self, tool_name: str, args: Dict[str, Any], duration: Optional[float] = None):
        """Trace a tool call with its parameters"""
        with self.tracer.start_as_current_span(f"tool_call.{tool_name}") as span:
            span.set_attributes({
                SpanAttributes.RPC_METHOD: tool_name,
                "tool.name": tool_name,
                "tool.args": json.dumps(args, default=str)[:1000],  # Limit size
                "component": "tool_execution"
            })
            
            if duration:
                span.set_attribute("tool.duration_ms", duration * 1000)
            
            # Store for UI
            tool_call = {
                "id": span.get_span_context().span_id,
                "tool_name": tool_name,
                "args": args,
                "timestamp": time.time(),
                "duration": duration,
                "status": "completed" if duration else "running"
            }
            self.tool_calls.append(tool_call)
            
            # Keep only last 50 calls
            if len(self.tool_calls) > 50:
                self.tool_calls = self.tool_calls[-50:]
            
            return span
    
    def trace_model_call(self, model_name: str, operation: str, tokens_used: Optional[int] = None, 
                        latency: Optional[float] = None, cost: Optional[float] = None):
        """Trace AI model calls"""
        with self.tracer.start_as_current_span(f"ai_model.{operation}") as span:
            span.set_attributes({
                "ai.model.name": model_name,
                "ai.operation": operation,
                "component": "ai_model"
            })
            
            if tokens_used:
                span.set_attribute("ai.usage.tokens", tokens_used)
            if latency:
                span.set_attribute("ai.latency_ms", latency * 1000)
            if cost:
                span.set_attribute("ai.cost_usd", cost)
            
            # Store for UI
            model_call = {
                "id": span.get_span_context().span_id,
                "model_name": model_name,
                "operation": operation,
                "tokens_used": tokens_used,
                "latency": latency,
                "cost": cost,
                "timestamp": time.time(),
                "status": "completed"
            }
            self.model_calls.append(model_call)
            
            # Keep only last 50 calls
            if len(self.model_calls) > 50:
                self.model_calls = self.model_calls[-50:]
            
            return span
    
    def trace_search_operation(self, query: str, results_count: int, search_type: str = "hybrid"):
        """Trace search operations"""
        with self.tracer.start_as_current_span(f"search.{search_type}") as span:
            span.set_attributes({
                "search.query": query[:200],  # Limit query size
                "search.type": search_type,
                "search.results_count": results_count,
                "component": "search"
            })
            return span
    
    def get_telemetry_data(self) -> Dict[str, Any]:
        """Get current telemetry data for UI"""
        return {
            "tool_calls": self.tool_calls[-10:],  # Last 10 for UI
            "model_calls": self.model_calls[-10:],  # Last 10 for UI
            "stats": {
                "total_tool_calls": len(self.tool_calls),
                "total_model_calls": len(self.model_calls),
                "avg_tool_duration": sum(call.get("duration", 0) for call in self.tool_calls) / len(self.tool_calls) if self.tool_calls else 0,
                "avg_model_latency": sum(call.get("latency", 0) for call in self.model_calls) / len(self.model_calls) if self.model_calls else 0
            }
        }

# Global telemetry instance
telemetry = TelemetryCollector()