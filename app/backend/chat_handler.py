"""
Chat handler for GPT-4o Audio API - Text-based conversations with RAG tools
Separate from the Realtime API WebSocket handler for voice conversations
"""
import os
import json
import asyncio
import logging
from typing import Dict, List, Any, Optional
from aiohttp import web
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AsyncAzureOpenAI
from ragtools import attach_rag_tools_to_client
from telemetry import telemetry

logger = logging.getLogger("chat_handler")

class ChatHandler:
    """Handles text-based chat using GPT-Audio API"""
    
    def __init__(self):
        # GPT-Audio specific configuration - separate from Realtime API
        self.endpoint = os.environ.get("AZURE_OPENAI_AUDIO_ENDPOINT") or os.environ.get("AZURE_OPENAI_ENDPOINT")
        self.audio_deployment = os.environ.get("AZURE_OPENAI_AUDIO_DEPLOYMENT", "gpt-audio")
        self.embedding_deployment = os.environ.get("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-large")
        self.api_version = os.environ.get("AZURE_OPENAI_AUDIO_API_VERSION", "2025-01-01-preview")
        self.voice_choice = os.environ.get("AZURE_OPENAI_AUDIO_VOICE_CHOICE") or os.environ.get("AZURE_OPENAI_REALTIME_VOICE_CHOICE", "alloy")
        
        # Initialize Azure OpenAI client with GPT-Audio specific credentials
        audio_api_key = os.environ.get("AZURE_OPENAI_AUDIO_API_KEY")
        if audio_api_key:
            self.client = AsyncAzureOpenAI(
                azure_endpoint=self.endpoint,
                api_key=audio_api_key,
                api_version=self.api_version
            )
            logger.info("Using GPT-Audio API key authentication")
        elif "AZURE_OPENAI_API_KEY" in os.environ:
            # Fallback to standard OpenAI key
            self.client = AsyncAzureOpenAI(
                azure_endpoint=self.endpoint,
                api_key=os.environ["AZURE_OPENAI_API_KEY"],
                api_version=self.api_version
            )
            logger.info("Using standard OpenAI API key authentication")
        else:
            # Use managed identity
            token_provider = get_bearer_token_provider(
                DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
            )
            self.client = AsyncAzureOpenAI(
                azure_endpoint=self.endpoint,
                azure_ad_token_provider=token_provider,
                api_version=self.api_version
            )
            logger.info("Using managed identity authentication")
        
        # Attach RAG tools to the client
        self.tools = []
        attach_rag_tools_to_client(self)
        
        logger.info(f"Chat handler initialized with deployment: {self.audio_deployment}")
        logger.info(f"Using API version: {self.api_version}")
        logger.info(f"Available tools: {[tool.get('function', {}).get('name') for tool in self.tools]}")
    
    def add_tool(self, tool_definition: Dict[str, Any]):
        """Add a tool definition for the chat API"""
        self.tools.append(tool_definition)
        logger.info(f"Added tool: {tool_definition.get('function', {}).get('name')}")
    
    async def handle_chat(self, request: web.Request) -> web.Response:
        """Handle POST /api/chat endpoint"""
        try:
            data = await request.json()
            
            # Extract message and conversation history
            user_message = data.get("message", "")
            conversation_history = data.get("history", [])
            generate_audio = data.get("generate_audio", False)
            
            if not user_message.strip():
                return web.json_response(
                    {"error": "Message cannot be empty"}, 
                    status=400
                )
            
            # Build messages for the API
            messages = []
            
            # Add system message
            system_message = self._get_system_message()
            if system_message:
                messages.append({"role": "system", "content": system_message})
            
            # Add conversation history
            for msg in conversation_history[-10:]:  # Keep last 10 messages for context
                if msg.get("role") in ["user", "assistant"]:
                    messages.append({
                        "role": msg["role"],
                        "content": msg.get("content", "")
                    })
            
            # Add current user message
            messages.append({"role": "user", "content": user_message})
            
            # Call GPT-Audio with tools - with audio generation if requested
            start_time = asyncio.get_event_loop().time()
            
            # Build the API call parameters
            api_params = {
                "model": self.audio_deployment,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 2000,
                "stream": False
            }
            
            # Add tools if available
            if self.tools:
                api_params["tools"] = self.tools
                api_params["tool_choice"] = "auto"
            
            # Add audio generation if requested - based on soundboard.py logic
            if generate_audio:
                api_params["modalities"] = ["text", "audio"]
                api_params["audio"] = {
                    "voice": self.voice_choice, 
                    "format": "mp3"  # Using MP3 like in soundboard.py
                }
                logger.info(f"🎵 Generating audio with voice: {self.voice_choice}")
            
            response = await self.client.chat.completions.create(**api_params)
            
            duration = asyncio.get_event_loop().time() - start_time
            
            # Process response
            assistant_message = response.choices[0].message
            
            # Handle tool calls if any
            if assistant_message.tool_calls:
                # Execute tool calls
                tool_results = []
                for tool_call in assistant_message.tool_calls:
                    try:
                        result = await self._execute_tool_call(tool_call)
                        tool_results.append(result)
                    except Exception as e:
                        logger.error(f"Tool call failed: {e}")
                        tool_results.append({
                            "tool_call_id": tool_call.id,
                            "content": f"Tool execution failed: {str(e)}"
                        })
                
                # Add tool results to conversation and get final response
                messages.append(assistant_message.model_dump())
                for result in tool_results:
                    messages.append({
                        "role": "tool",
                        "tool_call_id": result["tool_call_id"],
                        "content": result["content"]
                    })
                
                # Get final response after tool execution - with audio if requested
                final_api_params = {
                    "model": self.audio_deployment,
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 2000,
                    "stream": False
                }
                
                # Add audio generation if requested - using MP3 format
                if generate_audio:
                    final_api_params["modalities"] = ["text", "audio"]
                    final_api_params["audio"] = {
                        "voice": self.voice_choice, 
                        "format": "mp3"
                    }
                    logger.info(f"🎵 Generating final audio with voice: {self.voice_choice}")
                
                final_response = await self.client.chat.completions.create(**final_api_params)
                
                assistant_message = final_response.choices[0].message
            
            # Trace the interaction
            telemetry.trace_model_call(
                model_name=self.audio_deployment,
                operation="chat_completion",
                tokens_used=response.usage.total_tokens if response.usage else None,
                latency=duration,
                prompt=user_message[:200],
                response=assistant_message.content[:200] if assistant_message.content else None
            )
            
            # Prepare response
            response_data = {
                "message": assistant_message.content,
                "role": "assistant",
                "tokens_used": response.usage.total_tokens if response.usage else None,
                "model": self.audio_deployment
            }
            
            # Add audio data if generated - following soundboard.py pattern
            if generate_audio and hasattr(assistant_message, 'audio') and assistant_message.audio:
                if hasattr(assistant_message.audio, 'data') and assistant_message.audio.data:
                    response_data["audio"] = assistant_message.audio.data  # Base64 encoded MP3
                    response_data["audio_format"] = "mp3"
                    
                    # Add transcript if available
                    if hasattr(assistant_message.audio, 'transcript') and assistant_message.audio.transcript:
                        response_data["audio_transcript"] = assistant_message.audio.transcript
                    
                    # Add audio ID for potential conversation continuity
                    if hasattr(assistant_message.audio, 'id') and assistant_message.audio.id:
                        response_data["audio_id"] = assistant_message.audio.id
                    
                    logger.info(f"🎵 Generated MP3 audio response with voice: {self.voice_choice}, size: {len(assistant_message.audio.data)} chars")
                else:
                    logger.warning("🔇 Audio was requested but no audio data found in response")
            elif generate_audio:
                logger.warning("🔇 Audio was requested but assistant_message has no audio attribute")
            
            return web.json_response(response_data)
            
        except Exception as e:
            logger.error(f"Chat handler error: {e}")
            return web.json_response(
                {"error": f"Chat processing failed: {str(e)}"}, 
                status=500
            )
    
    async def _execute_tool_call(self, tool_call) -> Dict[str, Any]:
        """Execute a tool call and return the result"""
        tool_name = tool_call.function.name
        try:
            args = json.loads(tool_call.function.arguments)
        except json.JSONDecodeError:
            args = {}
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Execute the appropriate tool function
            if tool_name == "search":
                from ragtools import _search_tool
                result = await _search_tool(
                    self._search_client,
                    self._search_config["semantic_configuration"],
                    self._search_config["identifier_field"],
                    self._search_config["content_field"],
                    self._search_config["embedding_field"],
                    self._search_config["use_vector_query"],
                    args
                )
                result_content = result.result if hasattr(result, 'result') else str(result)
            
            elif tool_name == "report_grounding":
                from ragtools import _report_grounding_tool
                result = await _report_grounding_tool(
                    self._search_client,
                    self._search_config["identifier_field"],
                    self._search_config["title_field"],
                    self._search_config["content_field"],
                    args
                )
                result_content = json.dumps(result.result) if hasattr(result, 'result') else str(result)
            
            elif tool_name == "get_policies":
                from ragtools import _policy_tool
                result = await _policy_tool(args)
                result_content = json.dumps(result.result) if hasattr(result, 'result') else str(result)
            
            elif tool_name == "get_claims":
                from ragtools import _claims_tool
                result = await _claims_tool(args)
                result_content = json.dumps(result.result) if hasattr(result, 'result') else str(result)
            
            elif tool_name == "get_real_policies":
                from ragtools import _real_policy_tool
                result = await _real_policy_tool(args)
                result_content = json.dumps(result.result) if hasattr(result, 'result') else str(result)
            
            elif tool_name == "get_agencies":
                from ragtools import _agency_tool
                result = await _agency_tool(args)
                result_content = json.dumps(result.result) if hasattr(result, 'result') else str(result)
            
            elif tool_name == "get_contact_info":
                from ragtools import _contact_tool
                result = await _contact_tool(args)
                result_content = json.dumps(result.result) if hasattr(result, 'result') else str(result)
            
            else:
                result_content = f"Unknown tool: {tool_name}"
                
        except Exception as e:
            logger.error(f"Tool execution failed for {tool_name}: {e}")
            result_content = f"Tool execution failed: {str(e)}"
        
        duration = asyncio.get_event_loop().time() - start_time
        
        # Trace the tool call
        telemetry.trace_tool_call(
            tool_name=tool_name,
            args=args,
            duration=duration,
            response={"result": "success" if "failed" not in result_content else "error"},
            response_size=len(result_content)
        )
        
        return {
            "tool_call_id": tool_call.id,
            "content": result_content
        }
    
    def _get_system_message(self) -> str:
        """Get the system message for the chat"""
        return """You are a professional and caring insurance advisor for MAIF and MAAF insurance companies.

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
- 'get_contact_info': Get MAIF/MAAF contact information

BEHAVIOR GUIDELINES:
- Respond in the same language as the user (French or English)
- Professional, reassuring, and empathetic tone like a real insurance advisor
- Always use formal address ("vous" in French, formal tone in English)
- Keep responses concise and clear for text and audio consumption
- Never mention file names, sources, or technical keys in responses
- Cover all MAIF/MAAF domains: auto, home, motorcycle, life insurance, retirement, health
- For claims declaration, direct to official channels (mobile apps, phone numbers)
- Be precise about coverage, deductibles, and compensation terms
- If information is not in knowledge base, say so clearly and refer to human advisor

EXAMPLE MANDATORY WORKFLOW:
User: "What does MAIF auto insurance cover?"
1. I MUST call search("MAIF auto insurance coverage benefits guarantees")
2. I MUST call report_grounding with:
   - sources: [list of chunk IDs actually used]
   - confidence_level: "high" (if sources are comprehensive and relevant)
   - summary: "Coverage details for MAIF auto insurance from official documentation"
3. Then provide answer based on retrieved information

GROUNDING BEST PRACTICES:
- Use confidence_level: "high" for official policy documents, "medium" for general info, "low" for partial matches
- Provide helpful summary describing what information was extracted
- Only include sources that were actually used in your response
- The UI will display these sources to help users verify information

REMEMBER: NEVER answer insurance questions without using the 'search' tool first. This is MANDATORY."""

# Global chat handler instance
chat_handler = ChatHandler()