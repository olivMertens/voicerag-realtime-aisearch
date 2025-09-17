"""
Système de logging pour les transcripts des conversations utilisateur
Permet de sauvegarder et rejouer les conversations
"""
import json
import logging
import os
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger("conversation_logger")

class ConversationLogger:
    def __init__(self, log_dir: str = "conversation_logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.current_session_id = None
        self.current_log_file = None
        
    def start_session(self, session_id: Optional[str] = None) -> str:
        """Démarre une nouvelle session de conversation"""
        if session_id is None:
            session_id = f"session_{int(time.time())}"
        
        self.current_session_id = session_id
        timestamp = datetime.now().isoformat()
        
        # Créer le fichier de log pour cette session
        log_filename = f"{session_id}_{timestamp.replace(':', '-').split('.')[0]}.json"
        self.current_log_file = self.log_dir / log_filename
        
        # Initialiser le fichier avec les métadonnées de session
        session_data = {
            "session_id": session_id,
            "start_time": timestamp,
            "messages": [],
            "metadata": {
                "user_agent": os.environ.get("HTTP_USER_AGENT", "unknown"),
                "environment": os.environ.get("RUNNING_IN_PRODUCTION", "development")
            }
        }
        
        with open(self.current_log_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Started conversation session: {session_id}")
        return session_id
    
    def log_user_message(self, transcript: str, audio_duration: Optional[float] = None, 
                        metadata: Optional[Dict[str, Any]] = None):
        """Log un message utilisateur avec transcript"""
        if not self.current_session_id or not self.current_log_file:
            self.start_session()
        
        message_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "user",
            "transcript": transcript,
            "audio_duration": audio_duration,
            "metadata": metadata or {},
            "message_id": f"user_{int(time.time() * 1000)}"
        }
        
        self._append_message(message_entry)
        logger.info(f"Logged user message: {transcript[:100]}...")
        
    def log_assistant_message(self, response: str, model_used: str = "gpt-4o-realtime",
                            tokens_used: Optional[int] = None, latency: Optional[float] = None,
                            metadata: Optional[Dict[str, Any]] = None):
        """Log une réponse de l'assistant"""
        if not self.current_session_id or not self.current_log_file:
            return
        
        message_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "assistant", 
            "response": response,
            "model_used": model_used,
            "tokens_used": tokens_used,
            "latency": latency,
            "metadata": metadata or {},
            "message_id": f"assistant_{int(time.time() * 1000)}"
        }
        
        self._append_message(message_entry)
        logger.info(f"Logged assistant message: {response[:100]}...")
        
    def log_tool_call(self, tool_name: str, args: Dict[str, Any], response: Any,
                     duration: Optional[float] = None):
        """Log un appel de tool avec ses paramètres et réponse"""
        if not self.current_session_id or not self.current_log_file:
            return
        
        tool_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "tool_call",
            "tool_name": tool_name,
            "args": args,
            "response": self._serialize_response(response),
            "duration": duration,
            "message_id": f"tool_{int(time.time() * 1000)}"
        }
        
        self._append_message(tool_entry)
        logger.info(f"Logged tool call: {tool_name}")
        
    def _append_message(self, message_entry: Dict[str, Any]):
        """Ajoute un message au fichier de log de session"""
        if not self.current_log_file.exists():
            return
            
        try:
            # Lire le fichier existant
            with open(self.current_log_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            # Ajouter le nouveau message
            session_data["messages"].append(message_entry)
            session_data["last_updated"] = datetime.now().isoformat()
            
            # Sauvegarder
            with open(self.current_log_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Error appending message to log: {e}")
    
    def _serialize_response(self, response: Any) -> Any:
        """Sérialise la réponse pour le JSON"""
        if isinstance(response, (dict, list, str, int, float, bool, type(None))):
            return response
        try:
            return str(response)
        except Exception:
            return "<non-serializable>"
    
    def get_session_history(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Récupère l'historique d'une session"""
        for log_file in self.log_dir.glob(f"{session_id}_*.json"):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error reading session {session_id}: {e}")
        return None
    
    def list_sessions(self) -> List[Dict[str, str]]:
        """Liste toutes les sessions disponibles"""
        sessions = []
        for log_file in self.log_dir.glob("session_*.json"):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    sessions.append({
                        "session_id": data["session_id"],
                        "start_time": data["start_time"],
                        "message_count": len(data.get("messages", [])),
                        "file_path": str(log_file)
                    })
            except Exception as e:
                logger.warning(f"Could not read log file {log_file}: {e}")
        
        return sorted(sessions, key=lambda x: x["start_time"], reverse=True)
    
    def end_session(self):
        """Termine la session courante"""
        if self.current_log_file and self.current_log_file.exists():
            try:
                with open(self.current_log_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                
                session_data["end_time"] = datetime.now().isoformat()
                session_data["duration"] = (
                    datetime.fromisoformat(session_data["end_time"]) - 
                    datetime.fromisoformat(session_data["start_time"])
                ).total_seconds()
                
                with open(self.current_log_file, 'w', encoding='utf-8') as f:
                    json.dump(session_data, f, indent=2, ensure_ascii=False)
                    
                logger.info(f"Ended conversation session: {self.current_session_id}")
            except Exception as e:
                logger.error(f"Error ending session: {e}")
        
        self.current_session_id = None
        self.current_log_file = None

# Instance globale
conversation_logger = ConversationLogger()