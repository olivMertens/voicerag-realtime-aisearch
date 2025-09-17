import asyncio
import json
import logging
import os
from enum import Enum
from typing import Any, Callable, Optional

import aiohttp
from aiohttp import web
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

# Import conversation logger
try:
    from conversation_logger import conversation_logger
except ImportError:
    conversation_logger = None

logger = logging.getLogger("voicerag")

class ToolResultDirection(Enum):
    TO_SERVER = 1
    TO_CLIENT = 2

class ToolResult:
    text: str
    destination: ToolResultDirection

    def __init__(self, text: str, destination: ToolResultDirection):
        self.text = text
        self.destination = destination

    def to_text(self) -> str:
        if self.text is None:
            return ""
        return self.text if type(self.text) == str else json.dumps(self.text)

class Tool:
    target: Callable[..., ToolResult]
    schema: Any

    def __init__(self, target: Any, schema: Any):
        self.target = target
        self.schema = schema

class RTToolCall:
    tool_call_id: str
    previous_id: str

    def __init__(self, tool_call_id: str, previous_id: str):
        self.tool_call_id = tool_call_id
        self.previous_id = previous_id

class RTMiddleTier:
    endpoint: str
    deployment: str
    key: Optional[str] = None
    
    # Tools are server-side only for now, though the case could be made for client-side tools
    # in addition to server-side tools that are invisible to the client
    tools: dict[str, Tool] = {}

    # Server-enforced configuration, if set, these will override the client's configuration
    # Typically at least the model name and system message will be set by the server
    model: Optional[str] = None
    system_message: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    disable_audio: Optional[bool] = None
    voice_choice: Optional[str] = None
    transcription_language: Optional[str] = None
    api_version: str = "2025-04-01-preview"  # Default for Realtime API
    _tools_pending = {}
    _token_provider = None
    _current_session_id: Optional[str] = None
    _assistant_response_buffer: str = ""
    _user_transcript_buffer: str = ""
    
    def __init__(self, endpoint: str, deployment: str, credentials: AzureKeyCredential | DefaultAzureCredential, voice_choice: Optional[str] = None, transcription_language: Optional[str] = None):
        self.endpoint = endpoint
        self.deployment = deployment
        self.voice_choice = voice_choice
        self.transcription_language = transcription_language or "auto"  # Default to auto-detection
        # Use environment variable if available, otherwise use default
        self.api_version = os.environ.get("AZURE_OPENAI_REALTIME_API_VERSION", self.api_version)
        if voice_choice is not None:
            logger.info("Realtime voice choice set to %s", voice_choice)
        logger.info("Realtime transcription language set to %s", self.transcription_language)
        if isinstance(credentials, AzureKeyCredential):
            self.key = credentials.key
        else:
            self._token_provider = get_bearer_token_provider(credentials, "https://cognitiveservices.azure.com/.default")
            self._token_provider() # Warm up during startup so we have a token cached when the first request arrives

    async def _process_message_to_client(self, msg: str, client_ws: web.WebSocketResponse, server_ws: web.WebSocketResponse) -> Optional[str]:
        message = json.loads(msg.data)
        updated_message = msg.data
        if message is not None:
            match message["type"]:
                case "session.created":
                    session = message["session"]
                    # Start conversation logging session
                    if conversation_logger:
                        session_id = f"rtmt_{id(client_ws)}_{int(asyncio.get_event_loop().time())}"
                        self._current_session_id = conversation_logger.start_session(session_id)
                        logger.info(f"Started conversation logging for session: {self._current_session_id}")
                    
                    # Hide the instructions, tools and max tokens from clients, if we ever allow client-side 
                    # tools, this will need updating
                    session["instructions"] = ""
                    session["tools"] = []
                    session["voice"] = self.voice_choice
                    session["tool_choice"] = "none"
                    session["max_response_output_tokens"] = None
                    
                    # Configure input audio transcription
                    transcription_config = {"model": "whisper-1"}
                    
                    # Add language specification only if not auto-detection
                    if self.transcription_language and self.transcription_language != "auto":
                        transcription_config["language"] = self.transcription_language
                        logger.info(f"🌐 Transcription configured for language: {self.transcription_language}")
                    else:
                        logger.info("🌍 Transcription configured for automatic language detection")
                    
                    session["input_audio_transcription"] = transcription_config
                    
                    updated_message = json.dumps(message)

                case "response.output_item.added":
                    if "item" in message and message["item"]["type"] == "function_call":
                        updated_message = None

                case "conversation.item.created":
                    if "item" in message and message["item"]["type"] == "function_call":
                        item = message["item"]
                        if item["call_id"] not in self._tools_pending:
                            self._tools_pending[item["call_id"]] = RTToolCall(item["call_id"], message["previous_item_id"])
                        updated_message = None
                    elif "item" in message and message["item"]["type"] == "function_call_output":
                        updated_message = None

                case "response.function_call_arguments.delta":
                    updated_message = None
                
                case "response.function_call_arguments.done":
                    updated_message = None

                case "response.output_item.done":
                    if "item" in message and message["item"]["type"] == "function_call":
                        item = message["item"]
                        tool_call = self._tools_pending[message["item"]["call_id"]]
                        tool = self.tools[item["name"]]
                        args = item["arguments"]
                        result = await tool.target(json.loads(args))
                        
                        # Log tool call
                        if conversation_logger:
                            conversation_logger.log_tool_call(
                                tool_name=item["name"],
                                args=json.loads(args),
                                response=result.to_text(),
                                duration=None  # We could add timing here
                            )
                        
                        await server_ws.send_json({
                            "type": "conversation.item.create",
                            "item": {
                                "type": "function_call_output",
                                "call_id": item["call_id"],
                                "output": result.to_text() if result.destination == ToolResultDirection.TO_SERVER else ""
                            }
                        })
                        if result.destination == ToolResultDirection.TO_CLIENT:
                            # TODO: this will break clients that don't know about this extra message, rewrite 
                            # this to be a regular text message with a special marker of some sort
                            await client_ws.send_json({
                                "type": "extension.middle_tier_tool_response",
                                "previous_item_id": tool_call.previous_id,
                                "tool_name": item["name"],
                                "tool_result": result.to_text()
                            })
                        updated_message = None

                case "response.done":
                    # Log assistant response when complete
                    if conversation_logger and self._assistant_response_buffer.strip():
                        conversation_logger.log_assistant_message(
                            response=self._assistant_response_buffer.strip(),
                            model_used=self.model or self.deployment,
                            metadata={"session_id": self._current_session_id}
                        )
                        self._assistant_response_buffer = ""
                    
                    if len(self._tools_pending) > 0:
                        self._tools_pending.clear() # Any chance tool calls could be interleaved across different outstanding responses?
                        await server_ws.send_json({
                            "type": "response.create"
                        })
                    if "response" in message:
                        replace = False
                        # Process from the end to the beginning to avoid index issues when removing items
                        outputs = message["response"]["output"]
                        for i in range(len(outputs) - 1, -1, -1):
                            if outputs[i]["type"] == "function_call":
                                outputs.pop(i)
                                replace = True
                        if replace:
                            updated_message = json.dumps(message)
                            
                # Add handlers for transcript logging  
                case "conversation.item.input_audio_transcription.completed":
                    # Log user transcript when completed
                    if conversation_logger and "transcript" in message and message["transcript"].strip():
                        conversation_logger.log_user_message(
                            transcript=message["transcript"].strip(),
                            metadata={"session_id": self._current_session_id, "item_id": message.get("item_id")}
                        )
                
                case "response.audio_transcript.delta":
                    # Buffer assistant audio transcript
                    if "delta" in message:
                        self._assistant_response_buffer += message["delta"]
                
                case "response.text.delta":
                    # Buffer assistant text response
                    if "delta" in message:
                        self._assistant_response_buffer += message["delta"]

        return updated_message

    async def _process_message_to_server(self, msg: str, ws: web.WebSocketResponse) -> Optional[str]:
        message = json.loads(msg.data)
        updated_message = msg.data
        if message is not None:
            match message["type"]:
                case "session.update":
                    session = message["session"]
                    if self.system_message is not None:
                        session["instructions"] = self.system_message
                    if self.temperature is not None:
                        session["temperature"] = self.temperature
                    if self.max_tokens is not None:
                        session["max_response_output_tokens"] = self.max_tokens
                    if self.disable_audio is not None:
                        session["disable_audio"] = self.disable_audio
                    if self.voice_choice is not None:
                        session["voice"] = self.voice_choice
                    session["tool_choice"] = "auto" if len(self.tools) > 0 else "none"
                    session["tools"] = [tool.schema for tool in self.tools.values()]
                    logger.info(f"Session update - tool_choice: {session['tool_choice']}, tools count: {len(session.get('tools', []))}")
                    logger.info(f"Available tool names: {[tool['name'] for tool in session.get('tools', [])]}")
                    updated_message = json.dumps(message)

        return updated_message

    async def _forward_messages(self, ws: web.WebSocketResponse):
        async with aiohttp.ClientSession(base_url=self.endpoint) as session:
            params = { "api-version": self.api_version, "deployment": self.deployment}
            headers = {}
            if "x-ms-client-request-id" in ws.headers:
                headers["x-ms-client-request-id"] = ws.headers["x-ms-client-request-id"]
            if self.key is not None:
                headers = { "api-key": self.key }
            else:
                headers = { "Authorization": f"Bearer {self._token_provider()}" } # NOTE: no async version of token provider, maybe refresh token on a timer?
            async with session.ws_connect("/openai/realtime", headers=headers, params=params) as target_ws:
                async def from_client_to_server():
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            new_msg = await self._process_message_to_server(msg, ws)
                            if new_msg is not None:
                                await target_ws.send_str(new_msg)
                        else:
                            print("Error: unexpected message type:", msg.type)
                    
                    # Means it is gracefully closed by the client then time to close the target_ws
                    if target_ws:
                        print("Closing OpenAI's realtime socket connection.")
                        await target_ws.close()
                        
                async def from_server_to_client():
                    async for msg in target_ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            new_msg = await self._process_message_to_client(msg, ws, target_ws)
                            if new_msg is not None:
                                await ws.send_str(new_msg)
                        else:
                            print("Error: unexpected message type:", msg.type)

                try:
                    await asyncio.gather(from_client_to_server(), from_server_to_client())
                except ConnectionResetError:
                    # Ignore the errors resulting from the client disconnecting the socket
                    pass

    async def _websocket_handler(self, request: web.Request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        await self._forward_messages(ws)
        return ws
    
    def attach_to_app(self, app, path):
        app.router.add_get(path, self._websocket_handler)
