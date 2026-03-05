"""Session manager for SmartCalendar conversation history."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .database import CalendarDatabase


@dataclass
class Message:
    """Represents a conversation message."""
    role: str  # 'user', 'assistant', or 'system'
    content: str
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Convert message to dictionary."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Message":
        """Create message from dictionary."""
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"])
            if "timestamp" in data
            else datetime.now(),
        )


@dataclass
class Session:
    """Represents a conversation session."""
    session_id: str
    messages: list[Message] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)
    context: dict[str, Any] = field(default_factory=dict)

    def add_message(self, role: str, content: str) -> Message:
        """Add a message to the session."""
        message = Message(role=role, content=content)
        self.messages.append(message)
        self.last_active = datetime.now()
        return message

    def get_messages_for_llm(self, limit: int = 50) -> list[dict[str, str]]:
        """Get messages formatted for LLM API.
        
        Args:
            limit: Maximum number of messages to return
            
        Returns:
            List of message dictionaries with role and content
        """
        recent_messages = self.messages[-limit:] if limit else self.messages
        return [{"role": m.role, "content": m.content} for m in recent_messages]

    def clear_context(self) -> None:
        """Clear session context."""
        self.context = {}

    def set_context(self, key: str, value: Any) -> None:
        """Set a context value."""
        self.context[key] = value

    def get_context(self, key: str, default: Any = None) -> Any:
        """Get a context value."""
        return self.context.get(key, default)


class SessionManager:
    """Manages conversation sessions with SQLite persistence."""

    def __init__(self, database: CalendarDatabase):
        """Initialize the session manager.
        
        Args:
            database: CalendarDatabase instance for persistence
        """
        self.db = database
        self._sessions: dict[str, Session] = {}

    def get_or_create_session(self, session_id: str | None = None) -> Session:
        """Get existing session or create a new one.
        
        Args:
            session_id: Optional session ID. If None, creates a new one.
            
        Returns:
            Session object
        """
        if session_id is None:
            session_id = str(uuid.uuid4())

        # Check in-memory cache first
        if session_id in self._sessions:
            session = self._sessions[session_id]
            # Update last active in database
            self.db.get_or_create_session(session_id)
            return session

        # Load from database or create new
        self.db.get_or_create_session(session_id)
        session = Session(session_id=session_id)

        # Load existing messages from database
        db_messages = self.db.get_session_messages(session_id)
        for msg_data in db_messages:
            session.messages.append(Message.from_dict(msg_data))

        self._sessions[session_id] = session
        return session

    def add_message(
        self, session_id: str, role: str, content: str
    ) -> Message:
        """Add a message to a session.
        
        Args:
            session_id: Session identifier
            role: Message role (user, assistant, system)
            content: Message content
            
        Returns:
            The created Message object
        """
        session = self.get_or_create_session(session_id)
        message = session.add_message(role, content)
        
        # Persist to database
        self.db.add_message(session_id, role, content)
        
        return message

    def get_session(self, session_id: str) -> Session | None:
        """Get a session by ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session object or None if not found
        """
        return self._sessions.get(session_id)

    def get_session_messages(
        self, session_id: str, limit: int = 50
    ) -> list[dict[str, str]]:
        """Get messages for a session formatted for LLM.
        
        Args:
            session_id: Session identifier
            limit: Maximum number of messages to return
            
        Returns:
            List of message dictionaries
        """
        session = self.get_or_create_session(session_id)
        return session.get_messages_for_llm(limit)

    def set_session_context(
        self, session_id: str, key: str, value: Any
    ) -> None:
        """Set a context value for a session.
        
        Args:
            session_id: Session identifier
            key: Context key
            value: Context value
        """
        session = self.get_or_create_session(session_id)
        session.set_context(key, value)

    def get_session_context(
        self, session_id: str, key: str, default: Any = None
    ) -> Any:
        """Get a context value from a session.
        
        Args:
            session_id: Session identifier
            key: Context key
            default: Default value if key not found
            
        Returns:
            Context value or default
        """
        session = self.get_or_create_session(session_id)
        return session.get_context(key, default)

    def clear_session(self, session_id: str) -> bool:
        """Clear a session's messages and context.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if session was cleared, False if not found
        """
        if session_id not in self._sessions:
            return False

        session = self._sessions[session_id]
        session.messages.clear()
        session.context.clear()
        session.last_active = datetime.now()

        return True

    def delete_session(self, session_id: str) -> bool:
        """Delete a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if session was deleted, False if not found
        """
        if session_id not in self._sessions:
            return False

        del self._sessions[session_id]
        # Note: We don't delete from DB to preserve history
        # If you want to delete from DB, add that logic here

        return True
