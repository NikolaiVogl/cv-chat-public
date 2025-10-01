"""
Simple session management for conversation context.
"""
import uuid
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import threading

@dataclass
class ConversationMessage:
    """A single message in the conversation."""
    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: float
    metadata: Optional[Dict[str, Any]] = None

@dataclass 
class ConversationSession:
    """A conversation session with context."""
    session_id: str
    messages: List[ConversationMessage]
    created_at: float
    last_accessed: float
    awaiting_clarification: bool = False
    original_question: Optional[str] = None
    clarification_context: Optional[Dict[str, Any]] = None

class SessionManager:
    """Simple in-memory session manager for conversation context."""
    
    def __init__(self, session_timeout: int = 3600):  # 1 hour timeout
        self.sessions: Dict[str, ConversationSession] = {}
        self.session_timeout = session_timeout
        self._lock = threading.Lock()
    
    def create_session(self) -> str:
        """Create a new conversation session and return session ID."""
        with self._lock:
            session_id = str(uuid.uuid4())
            now = time.time()
            
            self.sessions[session_id] = ConversationSession(
                session_id=session_id,
                messages=[],
                created_at=now,
                last_accessed=now
            )
            
            return session_id
    
    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """Get a session by ID, if it exists and is not expired."""
        with self._lock:
            session = self.sessions.get(session_id)
            if not session:
                return None
            
            now = time.time()
            if now - session.last_accessed > self.session_timeout:
                # Session expired, remove it
                del self.sessions[session_id]
                return None
            
            session.last_accessed = now
            return session
    
    def add_message(self, session_id: str, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Add a message to the session. Returns True if successful."""
        session = self.get_session(session_id)
        if not session:
            return False
        
        with self._lock:
            message = ConversationMessage(
                role=role,
                content=content,
                timestamp=time.time(),
                metadata=metadata or {}
            )
            session.messages.append(message)
            return True
    
    def set_awaiting_clarification(self, session_id: str, original_question: str, context: Dict[str, Any]) -> bool:
        """Mark session as awaiting clarification response."""
        session = self.get_session(session_id)
        if not session:
            return False
        
        with self._lock:
            session.awaiting_clarification = True
            session.original_question = original_question
            session.clarification_context = context
            return True
    
    def clear_clarification_state(self, session_id: str) -> bool:
        """Clear the clarification waiting state."""
        session = self.get_session(session_id)
        if not session:
            return False
        
        with self._lock:
            session.awaiting_clarification = False
            session.original_question = None
            session.clarification_context = None
            return True
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions."""
        now = time.time()
        with self._lock:
            expired_sessions = [
                session_id for session_id, session in self.sessions.items()
                if now - session.last_accessed > self.session_timeout
            ]
            for session_id in expired_sessions:
                del self.sessions[session_id]

# Global session manager instance
session_manager = SessionManager()