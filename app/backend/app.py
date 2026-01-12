import logging
import os
import time
from pathlib import Path
from aiohttp import web
from azure.core.credentials import AzureKeyCredential
from azure.identity import AzureDeveloperCliCredential, DefaultAzureCredential
from dotenv import load_dotenv
from ragtools import attach_rag_tools

    # Import telemetry and setup Azure Monitor
try:
    from telemetry import setup_azure_monitor, get_telemetry_data, telemetry
    azure_monitor_configured = False
except ImportError:
    telemetry = None
    azure_monitor_configured = False

# Import conversation logger
try:
    from conversation_logger import conversation_logger
except ImportError:
    conversation_logger = None

# Import chat handler for GPT-4o Audio API
try:
    from chat_handler import chat_handler
except ImportError:
    chat_handler = None
    logging.warning("Chat handler not available")

from rtmt import RTMiddleTier

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("voicerag")


RUNNING_IN_PRODUCTION = os.getenv("RUNNING_IN_PRODUCTION", "false").lower() == "true"
HOST = "0.0.0.0" if RUNNING_IN_PRODUCTION else "localhost"
PORT = 8000

async def create_app():
    global azure_monitor_configured
    
    if not os.environ.get("RUNNING_IN_PRODUCTION"):
        logger.info("Running in development mode, loading from .env file")
        load_dotenv()

    # Setup Azure Monitor OpenTelemetry if not already configured
    if not azure_monitor_configured:
        try:
            azure_monitor_configured = setup_azure_monitor()
            if azure_monitor_configured:
                logger.info("✅ Azure Monitor OpenTelemetry integration enabled")
            else:
                logger.warning("⚠️ Azure Monitor not configured - telemetry will use local storage only")
        except Exception as e:
            logger.warning(f"⚠️ Failed to setup Azure Monitor: {e}")
            logger.exception("Full telemetry setup error:")

    llm_key = os.environ.get("AZURE_OPENAI_API_KEY")
    search_key = os.environ.get("AZURE_SEARCH_API_KEY")
    logger.info("Loading environment variables:")
    for key, value in os.environ.items():
        logger.info(f"{key}: {value}")

    credential = None
    if not llm_key or not search_key:
        if tenant_id := os.environ.get("AZURE_TENANT_ID"):
            logger.info("Using AzureDeveloperCliCredential with tenant_id %s", tenant_id)
            credential = AzureDeveloperCliCredential(tenant_id=tenant_id, process_timeout=60)
        else:
            logger.info("Using DefaultAzureCredential")
            credential = DefaultAzureCredential()
    llm_credential = AzureKeyCredential(llm_key) if llm_key else credential
    search_credential = AzureKeyCredential(search_key) if search_key else credential
    
    app = web.Application()
    rtmt = RTMiddleTier(
        credentials=llm_credential,
        endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        deployment=os.environ["AZURE_OPENAI_REALTIME_DEPLOYMENT"],
        voice_choice=os.environ.get("AZURE_OPENAI_REALTIME_VOICE_CHOICE") or "alloy",
        transcription_language=os.environ.get("AZURE_OPENAI_REALTIME_TRANSCRIPTION_LANGUAGE", "auto")
        )
    rtmt.system_message = """You are a professional and caring insurance advisor for Contoso Insurance.

CRITICAL MANDATORY RULE: You MUST ALWAYS use the 'search' tool FIRST before answering ANY insurance-related question. NO exceptions.

WORKFLOW FOR EVERY RESPONSE:
1. ALWAYS call 'search' tool first with relevant keywords from the user's question
2. Wait for search results from the knowledge base
3. Use 'report_grounding' tool to cite sources with confidence level and summary
4. Then provide your response based ONLY on the retrieved information

AVAILABLE TOOLS - USE THEM:
- 'search': Search the knowledge base (MANDATORY for all insurance questions)
- 'report_grounding': Cite information sources (MANDATORY after search) - includes confidence level and summary for UI display
- 'get_policies': Check insurance policies
- 'get_claims': Check declared claims
- 'get_agencies': Find local agencies
- 'get_contact_info': Get Contoso contact information

BEHAVIOR GUIDELINES:
- Respond in the same language as the user (French or English)
- Professional, reassuring, and empathetic tone like a real insurance advisor
- Always use formal address ("vous" in French, formal tone in English)
- Keep responses concise and clear for audio listening
- Never mention file names, sources, or technical keys in audio responses
- Cover relevant insurance domains based on the user's question and the knowledge base content
- For claims declaration, direct to official channels (mobile apps, phone numbers)
- Be precise about coverage, deductibles, and compensation terms
- If information is not in knowledge base, say so clearly and refer to human advisor

EXAMPLE MANDATORY WORKFLOW:
User: "Quels sont les délais pour déclarer un sinistre (vol, vandalisme, catastrophe naturelle) ?"
1. I MUST call search("Contoso délais déclaration vol vandalisme catastrophe naturelle habitation")
2. I MUST call report_grounding with:
   - sources: [list of chunk IDs actually used]
   - confidence_level: "high" (if sources are comprehensive and relevant)
    - summary: "Délais de déclaration (vol, vandalisme, catastrophe naturelle) d'après les sources du knowledge base"
3. Then provide answer based on retrieved information

GROUNDING BEST PRACTICES:
- Use confidence_level: "high" for official policy documents, "medium" for general info, "low" for partial matches
- Provide helpful summary describing what information was extracted
- Only include sources that were actually used in your response
- The UI will display these sources to help users verify information

REMEMBER: NEVER answer insurance questions without using the 'search' tool first. This is MANDATORY."""


    attach_rag_tools(rtmt,
        credentials=search_credential,
        search_endpoint=os.environ.get("AZURE_SEARCH_ENDPOINT"),
        search_index=os.environ.get("AZURE_SEARCH_INDEX"),
        semantic_configuration=os.environ.get("AZURE_SEARCH_SEMANTIC_CONFIGURATION") or "default",
        identifier_field=os.environ.get("AZURE_SEARCH_IDENTIFIER_FIELD") or "chunk_id",
        content_field=os.environ.get("AZURE_SEARCH_CONTENT_FIELD") or "chunk",
        embedding_field=os.environ.get("AZURE_SEARCH_EMBEDDING_FIELD") or "text_vector",
        title_field=os.environ.get("AZURE_SEARCH_TITLE_FIELD") or "title",
        use_vector_query=(os.environ.get("AZURE_SEARCH_USE_VECTOR_QUERY") == "true") or True
        )

    rtmt.attach_to_app(app, "/realtime")
    
    # Add telemetry endpoint
    async def telemetry_handler(request):
        try:
            data = get_telemetry_data()
            return web.json_response(data)
        except Exception as e:
            return web.json_response({"error": f"Telemetry error: {str(e)}"}, status=503)
    
    # Add telemetry diagnostics endpoint
    async def telemetry_diagnostics_handler(request):
        try:
            from telemetry import verify_telemetry_setup
            diagnostics = verify_telemetry_setup()
            return web.json_response(diagnostics)
        except Exception as e:
            return web.json_response({"error": f"Diagnostics error: {str(e)}", "working": False}, status=500)
    
    # Add telemetry test endpoint to force trace creation
    async def telemetry_test_handler(request):
        try:
            from telemetry import trace_tool_call, trace_model_call, get_tracer
            import time
            
            # Create test traces
            logger.info("Creating test traces for debugging...")
            
            # Test tool call
            trace_tool_call(
                "test_tool", 
                {"test_param": "test_value", "timestamp": time.time()}, 
                duration=0.123,
                response={"status": "success", "message": "Test trace from deployed app"},
                response_size=100
            )
            
            # Test model call
            trace_model_call(
                "gpt-4o",
                "test_completion",
                tokens_used=50,
                latency=0.456,
                cost=0.001,
                prompt="Test prompt from deployed app",
                response="Test response from deployed app"
            )
            
            # Test manual span creation
            tracer = get_tracer()
            with tracer.start_as_current_span("manual_test_span") as span:
                span.set_attributes({
                    "test.type": "manual_verification",
                    "test.environment": "azure_container_app",
                    "test.timestamp": time.time(),
                    "app.deployment": "azure"
                })
                logger.info("Manual test span created")
            
            return web.json_response({
                "success": True,
                "message": "Test traces created successfully",
                "traces_sent": 3,
                "timestamp": time.time()
            })
        except Exception as e:
            logger.exception("Error creating test traces")
            return web.json_response({
                "success": False,
                "error": str(e),
                "timestamp": time.time()
            }, status=500)
    
    app.router.add_get('/api/telemetry', telemetry_handler)
    app.router.add_get('/api/telemetry/diagnostics', telemetry_diagnostics_handler)
    app.router.add_post('/api/telemetry/test', telemetry_test_handler)
    
    # Add GPT-4o Audio chat endpoint
    if chat_handler:
        app.router.add_post('/api/chat', chat_handler.handle_chat)
    
    # Add conversation logging endpoints
    if conversation_logger:
        async def list_conversations_handler(request):
            try:
                sessions = conversation_logger.list_sessions()
                return web.json_response({"sessions": sessions})
            except Exception as e:
                return web.json_response({"error": str(e)}, status=500)
        
        async def get_conversation_handler(request):
            try:
                session_id = request.match_info['session_id']
                history = conversation_logger.get_session_history(session_id)
                if history:
                    return web.json_response(history)
                else:
                    return web.json_response({"error": "Session not found"}, status=404)
            except Exception as e:
                return web.json_response({"error": str(e)}, status=500)
        
        app.router.add_get('/api/conversations', list_conversations_handler)
        app.router.add_get('/api/conversations/{session_id}', get_conversation_handler)
    
    # Add user transcript logging handler  
    async def user_transcript_handler(request):
        """Handle user speech-to-text transcript logging"""
        try:
            data = await request.json()
            
            # Log the user transcript
            log_entry = {
                "timestamp": data.get("timestamp", time.time()),
                "type": data.get("type", "user_question"),
                "transcript": data.get("transcript", ""),
                "session_id": data.get("session_id", "default"),
                "source": "speech_to_text"
            }
            
            # Log to conversation logger if available
            if conversation_logger:
                try:
                    conversation_logger.log_conversation(
                        session_id=log_entry["session_id"],
                        role="user",
                        content=log_entry["transcript"],
                        metadata={
                            "source": "speech_to_text",
                            "timestamp": log_entry["timestamp"]
                        }
                    )
                except Exception as e:
                    logger.warning(f"Failed to log to conversation logger: {e}")
            
            # Log to standard logger as well
            logger.info(f"🎤 User transcript: [{log_entry['session_id']}] {log_entry['transcript']}")
            
            return web.json_response({"status": "success", "logged": True})
            
        except Exception as e:
            logger.error(f"User transcript handler error: {e}")
            return web.json_response({"error": f"Failed to log transcript: {str(e)}"}, status=500)
    
    # Add voice settings handler
    async def voice_settings_handler(request):
        """Handle voice preference updates for both Realtime and GPT-Audio"""
        try:
            data = await request.json()
            new_voice = data.get("voice", "alloy")
            mode = data.get("mode", "both")  # "text", "realtime", or "both"
            
            # Validate voice choice - all 10 GPT-Audio voices
            valid_voices = ["alloy", "ash", "ballad", "cedar", "coral", "echo", "marin", "sage", "shimmer", "verse"]
            if new_voice not in valid_voices:
                return web.json_response(
                    {"error": f"Invalid voice. Must be one of: {', '.join(valid_voices)}"},
                    status=400
                )
            
            updated_services = {}
            
            # Update RTMiddleTier voice choice (for Realtime API)
            if mode in ["realtime", "both"] and hasattr(rtmt, 'voice_choice'):
                rtmt.voice_choice = new_voice
                logger.info(f"🎵 Realtime API voice updated to: {new_voice}")
                updated_services["realtime_api"] = True
            
            # Update chat handler voice preference (for GPT-Audio)
            if mode in ["text", "both"] and chat_handler and hasattr(chat_handler, 'voice_choice'):
                chat_handler.voice_choice = new_voice
                logger.info(f"🎵 GPT-Audio voice updated to: {new_voice}")
                updated_services["gpt_audio"] = True
            
            return web.json_response({
                "success": True,
                "voice": new_voice,
                "mode": mode,
                "message": f"Voice updated to {new_voice} for {mode} mode(s)",
                "updated": updated_services
            })
            
        except Exception as e:
            logger.error(f"Voice settings error: {e}")
            return web.json_response(
                {"error": f"Voice update failed: {str(e)}"},
                status=500
            )
    
    # Register routes
    app.router.add_post('/api/user-transcript', user_transcript_handler)
    app.router.add_post('/api/voice-settings', voice_settings_handler)
    async def conversations_list_handler(request):
        try:
            if conversation_logger:
                sessions = conversation_logger.list_sessions()
                return web.json_response({"sessions": sessions})
            else:
                return web.json_response({"error": "Conversation logger not available"}, status=503)
        except Exception as e:
            return web.json_response({"error": f"Conversation list error: {str(e)}"}, status=500)
    
    async def conversation_detail_handler(request):
        try:
            session_id = request.match_info.get('session_id')
            if conversation_logger and session_id:
                history = conversation_logger.get_session_history(session_id)
                if history:
                    return web.json_response(history)
                else:
                    return web.json_response({"error": "Session not found"}, status=404)
            else:
                return web.json_response({"error": "Invalid request"}, status=400)
        except Exception as e:
            return web.json_response({"error": f"Conversation detail error: {str(e)}"}, status=500)
    
    async def user_transcript_handler(request):
        """Handle user speech-to-text transcript logging"""
        try:
            data = await request.json()
            
            # Log the user transcript
            log_entry = {
                "timestamp": data.get("timestamp", time.time()),
                "type": data.get("type", "user_question"),
                "transcript": data.get("transcript", ""),
                "session_id": data.get("session_id", "default"),
                "source": "speech_to_text"
            }
            
            # Log to conversation logger if available
            if conversation_logger:
                try:
                    conversation_logger.log_conversation(
                        session_id=log_entry["session_id"],
                        role="user",
                        content=log_entry["transcript"],
                        metadata={
                            "source": "speech_to_text",
                            "timestamp": log_entry["timestamp"]
                        }
                    )
                except Exception as e:
                    logger.warning(f"Failed to log to conversation logger: {e}")
            
            # Log to standard logger as well
            logger.info(f"🎤 User transcript: [{log_entry['session_id']}] {log_entry['transcript']}")
            
            return web.json_response({"status": "success", "logged": True})
            
        except Exception as e:
            logger.error(f"User transcript handler error: {e}")
            return web.json_response({"error": f"Failed to log transcript: {str(e)}"}, status=500)
    
    async def voice_settings_handler(request):
        """Handle voice preference updates for both Realtime and GPT-Audio"""
        try:
            data = await request.json()
            new_voice = data.get("voice", "alloy")
            
            # Validate voice choice - all 10 GPT-Audio voices
            valid_voices = ["alloy", "ash", "ballad", "cedar", "coral", "echo", "marin", "sage", "shimmer", "verse"]
            if new_voice not in valid_voices:
                return web.json_response(
                    {"error": f"Invalid voice. Must be one of: {', '.join(valid_voices)}"},
                    status=400
                )
            
            # Update RTMiddleTier voice choice (for Realtime API)
            if hasattr(rtmt, 'voice_choice'):
                rtmt.voice_choice = new_voice
                logger.info(f"🎵 Realtime API voice updated to: {new_voice}")
            
            # Update chat handler voice preference (for GPT-Audio)
            if chat_handler and hasattr(chat_handler, 'voice_choice'):
                chat_handler.voice_choice = new_voice
                logger.info(f"🎵 GPT-Audio voice updated to: {new_voice}")
            
            return web.json_response({
                "success": True,
                "voice": new_voice,
                "message": f"Voice updated to {new_voice}",
                "updated": {
                    "realtime_api": hasattr(rtmt, 'voice_choice'),
                    "gpt_audio": chat_handler and hasattr(chat_handler, 'voice_choice')
                }
            })
            
        except Exception as e:
            logger.error(f"Voice settings error: {e}")
            return web.json_response(
                {"error": f"Voice update failed: {str(e)}"},
                status=500
            )
    
    app.router.add_get('/api/conversations', conversations_list_handler)
    app.router.add_get('/api/conversations/{session_id}', conversation_detail_handler)
    app.router.add_post('/api/user-transcript', user_transcript_handler)
    app.router.add_post('/api/voice-settings', voice_settings_handler)
    
    current_directory = Path(__file__).parent
    app.add_routes([web.get('/', lambda _: web.FileResponse(current_directory / 'static/index.html'))])
    app.router.add_static('/', path=current_directory / 'static', name='static')
    return app


if __name__ == "__main__":
    host = HOST
    port = 8000
    app = create_app()
    web.run_app(app, host=host, port=port)
