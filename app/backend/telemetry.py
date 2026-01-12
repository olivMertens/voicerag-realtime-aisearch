"""
Azure Monitor OpenTelemetry configuration for tracking tool calls and model usage
Compatible with Application Insights and Microsoft Foundry
"""
import os
import time
import json
import logging
from typing import Dict, Any, Optional, List
from opentelemetry import trace
from opentelemetry.trace.status import Status, StatusCode
from opentelemetry.semconv.trace import SpanAttributes

# Global telemetry data storage
_tool_calls: List[Dict[str, Any]] = []
_model_calls: List[Dict[str, Any]] = []
_azure_monitor_configured: bool = False

logger = logging.getLogger("telemetry")

def setup_azure_monitor():
    """
    Setup Azure Monitor OpenTelemetry integration with Microsoft Foundry compatibility.
    This should be called once at application startup.
    """
    try:
        from azure.monitor.opentelemetry import configure_azure_monitor
        
        # Check for connection string or instrumentation key
        connection_string = os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING")
        instrumentation_key = os.environ.get("APPINSIGHTS_INSTRUMENTATIONKEY")
        
        if not connection_string and not instrumentation_key:
            logger.warning("⚠️ No Application Insights connection string or instrumentation key found")
            logger.info("💡 Expected environment variables: APPLICATIONINSIGHTS_CONNECTION_STRING or APPINSIGHTS_INSTRUMENTATIONKEY")
            return False
        
        # Log which configuration we're using (for debugging)
        if connection_string:
            logger.info(f"✅ Using APPLICATIONINSIGHTS_CONNECTION_STRING: {connection_string[:50]}...")
        elif instrumentation_key:
            logger.info(f"✅ Using APPINSIGHTS_INSTRUMENTATIONKEY: {instrumentation_key[:10]}...")
        
        # Configure Azure Monitor with enhanced settings for Microsoft Foundry
        try:
            configure_azure_monitor(
                logger_name="insurance_voice_assistant",
                connection_string=connection_string if connection_string else None,
                # Enable additional features for Microsoft Foundry
                enable_live_metrics=True,
                # Sample rate for performance (1.0 = 100% sampling)
                sampling_rate=1.0
            )
            logger.info("✅ Azure Monitor configured successfully")
        except Exception as config_error:
            logger.error(f"❌ Azure Monitor configuration failed: {config_error}")
            return False
        
        # Try to instrument HTTP libraries for API calls tracing
        try:
            from opentelemetry.instrumentation.requests import RequestsInstrumentor
            from opentelemetry.instrumentation.urllib3 import URLLib3Instrumentor
            
            RequestsInstrumentor().instrument()
            URLLib3Instrumentor().instrument()
            
            # Try to instrument httpx if available
            try:
                from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
                HTTPXClientInstrumentor().instrument()
            except ImportError:
                pass  # httpx instrumentation not available, skip
            
            logger.info("✅ HTTP instrumentation enabled")
        except Exception as e:
            logger.warning(f"⚠️ HTTP instrumentation failed: {e}")
        
        # Set custom resource attributes for Microsoft Foundry
        try:
            from opentelemetry.sdk.resources import Resource
            from opentelemetry import trace
            
            # Get Microsoft Foundry project information from environment
            ai_foundry_project = os.environ.get("AZURE_AI_FOUNDRY_PROJECT_NAME", "contoso-insurance-assistant")
            ai_foundry_hub = os.environ.get("AZURE_AI_FOUNDRY_HUB_NAME", "")
            deployment_env = os.environ.get("RUNNING_IN_PRODUCTION", "false")
            
            resource_attributes = {
                "service.name": "contoso-voice-assistant",
                "service.version": "1.0.0",
                "service.namespace": "insurance",
                "deployment.environment": "production" if deployment_env.lower() == "true" else "development",
                "ai.system": "azure_openai_realtime",
                "ai.foundry.enabled": "true"
            }
            
            # Add Microsoft Foundry specific attributes if available
            if ai_foundry_project:
                resource_attributes["ai.foundry.project"] = ai_foundry_project
                resource_attributes["ai.foundry.project.name"] = ai_foundry_project
            
            if ai_foundry_hub:
                resource_attributes["ai.foundry.hub"] = ai_foundry_hub
                resource_attributes["ai.foundry.hub.name"] = ai_foundry_hub
            
            # Add Azure resource information
            resource_group = os.environ.get("AZURE_RESOURCE_GROUP", "")
            if resource_group:
                resource_attributes["azure.resource_group"] = resource_group
            
            resource = Resource.create(resource_attributes)
            logger.info(f"✅ Microsoft Foundry resource attributes set: {ai_foundry_project}")
            
        except Exception as e:
            logger.warning(f"⚠️ Resource attributes setup failed: {e}")
        
        logger.info("✅ Azure Monitor OpenTelemetry configured for Microsoft Foundry")
        global _azure_monitor_configured
        _azure_monitor_configured = True
        return True
        
    except ImportError as e:
        logger.warning(f"⚠️ Azure Monitor OpenTelemetry not available: {e}")
        logger.info("💡 Install with: pip install azure-monitor-opentelemetry")
        return False
    except Exception as e:
        logger.error(f"❌ Failed to setup Azure Monitor: {e}")
        logger.exception("Full error details:")
        return False

def get_tracer():
    """Get OpenTelemetry tracer for creating spans"""
    return trace.get_tracer("contoso_voice_assistant")

def trace_tool_call(tool_name: str, args: Dict[str, Any], duration: Optional[float] = None, 
                   response: Optional[Any] = None, response_size: Optional[int] = None):
    """Trace a tool call with Microsoft Foundry semantic conventions"""
    tracer = get_tracer()
    
    with tracer.start_as_current_span(f"ai_tool.{tool_name}") as span:
        # Set Microsoft Foundry compatible attributes
        span.set_attributes({
            # Standard semantic conventions
            "operation.name": f"ai_tool.{tool_name}",
            "ai.system": "contoso_voice_assistant",
            "ai.tool.name": tool_name,
            "ai.tool.type": "function",
            
            # Tool-specific attributes
            "tool.name": tool_name,
            "tool.args": json.dumps(args, default=str)[:1000],  # Limit size
            "component": "ai_tool_execution",
            
            # Performance metrics
            "span.kind": "internal"
        })
        
        if duration is not None:
            span.set_attribute("duration_ms", duration * 1000)
            span.set_attribute("ai.tool.duration_ms", duration * 1000)
        
        # Add response details with Microsoft Foundry conventions
        if response is not None:
            if isinstance(response, dict):
                span.set_attribute("ai.tool.response.type", "dict")
                span.set_attribute("ai.tool.response.keys_count", len(response))
                
                # Special handling for search results
                if tool_name == "search" and "sources" in response:
                    sources = response.get("sources", [])
                    if isinstance(sources, list):
                        span.set_attribute("search.results.count", len(sources))
                        span.set_attribute("ai.tool.search.results_found", len(sources))
                
                # Special handling for grounding
                if tool_name == "report_grounding":
                    grounding_info = response.get("grounding_info", {})
                    if isinstance(grounding_info, dict):
                        span.set_attribute("ai.grounding.confidence", grounding_info.get("confidence_level", "unknown"))
                        span.set_attribute("ai.grounding.sources_found", grounding_info.get("found_sources", 0))
                        span.set_attribute("ai.grounding.status", grounding_info.get("status", "unknown"))
                
                response_preview = json.dumps(response, default=str)[:500]
                span.set_attribute("ai.tool.response.preview", response_preview)
                
            elif isinstance(response, list):
                span.set_attribute("ai.tool.response.type", "list")
                span.set_attribute("ai.tool.response.length", len(response))
                if response:
                    first_item_preview = json.dumps(response[0], default=str)[:200]
                    span.set_attribute("ai.tool.response.first_item", first_item_preview)
            else:
                span.set_attribute("ai.tool.response.type", type(response).__name__)
                span.set_attribute("ai.tool.response.preview", str(response)[:500])
        
        if response_size is not None:
            span.set_attribute("ai.tool.response.size_bytes", response_size)
        
        # Mark as successful
        span.set_status(Status(StatusCode.OK))
        
        # Store for UI (fallback if Azure Monitor not available)
        tool_call = {
            "id": f"{span.get_span_context().span_id:016x}",
            "tool_name": tool_name,
            "args": args,
            "response_preview": str(response)[:200] if response is not None else None,
            "timestamp": time.time(),
            "duration": duration,
            "status": "completed" if duration is not None else "running"
        }
        _tool_calls.append(tool_call)
        
        # Keep only last 50 calls
        if len(_tool_calls) > 50:
            _tool_calls[:] = _tool_calls[-50:]
        
        logger.info(
            f"🔧 Tool call traced: {tool_name} (duration: {duration:.3f}s)"
            if duration is not None
            else f"🔧 Tool call started: {tool_name}"
        )
        return span

def trace_model_call(model_name: str, operation: str, tokens_used: Optional[int] = None, 
                    latency: Optional[float] = None, cost: Optional[float] = None,
                    prompt: Optional[str] = None, response: Optional[str] = None):
    """Trace AI model calls with Azure AI Foundry semantic conventions"""
    tracer = get_tracer()
    
    with tracer.start_as_current_span(f"ai_model.{operation}") as span:
        # Set Azure AI Foundry semantic attributes
        span.set_attributes({
            # Core AI attributes (AI Foundry compatible)
            "ai.system": "azure_openai",
            "ai.model.name": model_name,
            "ai.operation.name": operation,
            "ai.model.provider": "azure",
            "ai.model.type": "chat" if "chat" in operation else "embedding" if "embedding" in operation else "completion",
            
            # Gen AI semantic conventions
            "gen_ai.system": "azure_openai",
            "gen_ai.request.model": model_name,
            "gen_ai.operation.name": operation,
            
            # Standard attributes
            "operation.name": f"ai_model.{operation}",
            "component": "ai_model",
            "span.kind": "client"
        })
        
        # Usage metrics
        if tokens_used:
            span.set_attribute("gen_ai.usage.completion_tokens", tokens_used)
            span.set_attribute("ai.model.tokens.total", tokens_used)
        
        if latency:
            span.set_attribute("duration_ms", latency * 1000)
            span.set_attribute("ai.model.latency_ms", latency * 1000)
        
        if cost:
            span.set_attribute("gen_ai.usage.cost", cost)
            span.set_attribute("ai.model.cost_usd", cost)
        
        # Content attributes (with size limits for performance)
        if prompt:
            prompt_preview = prompt[:300]  # First 300 chars
            span.set_attribute("ai.model.prompt.preview", prompt_preview)
            span.set_attribute("ai.model.prompt.length", len(prompt))
            span.set_attribute("gen_ai.prompt.preview", prompt_preview)
        
        if response:
            response_preview = response[:300]  # First 300 chars
            span.set_attribute("ai.model.completion.preview", response_preview)
            span.set_attribute("ai.model.completion.length", len(response))
            span.set_attribute("gen_ai.completion.preview", response_preview)
        
        # Mark as successful
        span.set_status(Status(StatusCode.OK))
        
        # Store for UI (fallback)
        model_call = {
            "id": f"{span.get_span_context().span_id:016x}",
            "model_name": model_name,
            "operation": operation,
            "tokens_used": tokens_used,
            "latency": latency,
            "cost": cost,
            "prompt_preview": prompt[:100] if prompt else None,
            "response_preview": response[:100] if response else None,
            "timestamp": time.time(),
            "status": "completed"
        }
        _model_calls.append(model_call)
        
        # Keep only last 50 calls
        if len(_model_calls) > 50:
            _model_calls[:] = _model_calls[-50:]
        
        logger.info(f"🤖 Model call traced: {model_name}.{operation} (tokens: {tokens_used}, latency: {latency:.3f}s)" if latency else f"🤖 Model call: {model_name}.{operation}")
        return span

def trace_search_operation(query: str, results_count: int, search_type: str = "hybrid"):
    """Trace Azure AI Search operations with AI Foundry compatibility"""
    tracer = get_tracer()
    
    with tracer.start_as_current_span(f"ai_search.{search_type}") as span:
        span.set_attributes({
            # AI Foundry search attributes
            "ai.system": "azure_ai_search",
            "ai.search.query": query[:200],  # Limit query size
            "ai.search.type": search_type,
            "ai.search.results.count": results_count,
            "ai.search.provider": "azure",
            
            # Standard search attributes
            "search.query": query[:200],
            "search.type": search_type,
            "search.results_count": results_count,
            "search.engine": "azure_cognitive_search",
            
            # Operation attributes
            "operation.name": f"ai_search.{search_type}",
            "component": "azure_search",
            "span.kind": "client"
        })
        
        # Add search quality metrics based on results
        if results_count == 0:
            span.set_attribute("ai.search.quality", "no_results")
            span.set_status(Status(StatusCode.OK, "No results found"))
        elif results_count <= 2:
            span.set_attribute("ai.search.quality", "low")
        elif results_count <= 5:
            span.set_attribute("ai.search.quality", "medium")
        else:
            span.set_attribute("ai.search.quality", "high")
        
        # Mark successful operation
        span.set_status(Status(StatusCode.OK))
        
        logger.info(f"🔍 Search traced: {search_type} query '{query[:50]}...' -> {results_count} results")
        return span

def get_telemetry_data() -> Dict[str, Any]:
    """Get current telemetry data for UI"""
    try:
        ui_limit = int(os.environ.get("TELEMETRY_UI_LIMIT", "50"))
    except ValueError:
        ui_limit = 50
    ui_limit = max(10, min(ui_limit, 200))
    return {
        "tool_calls": _tool_calls[-ui_limit:],
        "model_calls": _model_calls[-ui_limit:],
        "stats": {
            "total_tool_calls": len(_tool_calls),
            "total_model_calls": len(_model_calls),
            "avg_tool_duration": sum(call.get("duration", 0) for call in _tool_calls) / len(_tool_calls) if _tool_calls else 0,
            "avg_model_latency": sum(call.get("latency", 0) for call in _model_calls) / len(_model_calls) if _model_calls else 0
        }
    }

def verify_telemetry_setup() -> Dict[str, Any]:
    """
    Verify telemetry configuration and return diagnostic information.
    This function helps debug telemetry issues.
    """
    diagnostics = {
        "azure_monitor_configured": _azure_monitor_configured,
        "connection_string_found": False,
        "instrumentation_key_found": False,
        "environment_variables": {},
        "ai_foundry_config": {},
        "errors": []
    }
    
    try:
        # Check environment variables
        connection_string = os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING")
        instrumentation_key = os.environ.get("APPINSIGHTS_INSTRUMENTATIONKEY")
        
        diagnostics["connection_string_found"] = bool(connection_string)
        diagnostics["instrumentation_key_found"] = bool(instrumentation_key)
        
        if connection_string:
            # Only show first and last few characters for security
            masked_conn = f"{connection_string[:20]}...{connection_string[-10:]}" if len(connection_string) > 30 else connection_string
            diagnostics["environment_variables"]["APPLICATIONINSIGHTS_CONNECTION_STRING"] = masked_conn
        
        if instrumentation_key:
            masked_key = f"{instrumentation_key[:8]}...{instrumentation_key[-4:]}" if len(instrumentation_key) > 12 else instrumentation_key
            diagnostics["environment_variables"]["APPINSIGHTS_INSTRUMENTATIONKEY"] = masked_key
        
        # Check AI Foundry configuration
        ai_foundry_vars = [
            "AZURE_AI_FOUNDRY_PROJECT_NAME",
            "AZURE_AI_FOUNDRY_HUB_NAME", 
            "AZURE_RESOURCE_GROUP",
            "RUNNING_IN_PRODUCTION"
        ]
        
        for var in ai_foundry_vars:
            value = os.environ.get(var)
            if value:
                diagnostics["ai_foundry_config"][var] = value
        
        # Try to import Azure Monitor
        try:
            from azure.monitor.opentelemetry import configure_azure_monitor
            diagnostics["azure_monitor_available"] = True
        except ImportError as e:
            diagnostics["azure_monitor_available"] = False
            diagnostics["errors"].append(f"Azure Monitor not available: {e}")
        
        # Check if telemetry is working
        if connection_string or instrumentation_key:
            try:
                # Try to create a test trace
                tracer = get_tracer()
                with tracer.start_as_current_span("telemetry_test") as span:
                    span.set_attribute("test.status", "success")
                    span.set_attribute("test.timestamp", time.time())
                    diagnostics["test_trace_created"] = True
            except Exception as e:
                diagnostics["test_trace_created"] = False
                diagnostics["errors"].append(f"Failed to create test trace: {e}")
        
        logger.info(f"🔍 Telemetry diagnostics completed: {len(diagnostics['errors'])} errors found")
        
    except Exception as e:
        diagnostics["errors"].append(f"Diagnostic check failed: {e}")
    
    return diagnostics

# Deprecated: Keep for backward compatibility
class TelemetryCollector:
    """Deprecated: Use module-level functions instead"""
    def __init__(self):
        pass  # No warning needed - we'll remove the calls
        
    def trace_tool_call(self, tool_name: str, args: Dict[str, Any], duration: Optional[float] = None,
                       response: Optional[Any] = None, response_size: Optional[int] = None):
        return trace_tool_call(tool_name, args, duration, response, response_size)
    
    def trace_model_call(self, model_name: str, operation: str, tokens_used: Optional[int] = None, 
                        latency: Optional[float] = None, cost: Optional[float] = None,
                        prompt: Optional[str] = None, response: Optional[str] = None):
        return trace_model_call(model_name, operation, tokens_used, latency, cost, prompt, response)
    
    def trace_search_operation(self, query: str, results_count: int, search_type: str = "hybrid"):
        return trace_search_operation(query, results_count, search_type)
    
    def get_telemetry_data(self) -> Dict[str, Any]:
        return get_telemetry_data()

# Global telemetry instance for backward compatibility (no duplication)
telemetry = TelemetryCollector()