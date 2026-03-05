"""SQLite database module for SmartCalendar."""

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any


class CalendarDatabase:
    """SQLite database manager for calendar events and sessions."""

    def __init__(self, db_path: str | None = None):
        """Initialize the database connection.
        
        Args:
            db_path: Path to the SQLite database file. Defaults to ~/.smart_calendar.db
        """
        if db_path is None:
            db_path = str(Path.home() / ".smart_calendar.db")
        self.db_path = db_path
        self._init_tables()

    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_tables(self) -> None:
        """Initialize database tables."""
        with self.get_connection() as conn:
            # Events table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    date TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    duration_minutes INTEGER NOT NULL,
                    description TEXT,
                    participants TEXT,
                    location TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # Sessions table for conversation history
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    created_at TEXT NOT NULL,
                    last_active TEXT NOT NULL
                )
            """)

            # Messages table for conversation history
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                )
            """)

            # Create indexes for better query performance
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_date 
                ON events(date)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_session 
                ON messages(session_id)
            """)

    # Event operations
    def create_event(
        self,
        title: str,
        date: str,
        start_time: str,
        end_time: str,
        duration_minutes: int,
        description: str | None = None,
        participants: str | None = None,
        location: str | None = None,
    ) -> int:
        """Create a new calendar event.
        
        Args:
            title: Event title
            date: Event date (YYYY-MM-DD)
            start_time: Start time (HH:MM)
            end_time: End time (HH:MM)
            duration_minutes: Duration in minutes
            description: Optional event description
            participants: Comma-separated list of participants
            location: Event location or meeting link
            
        Returns:
            The ID of the created event
        """
        now = datetime.now().isoformat()
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO events 
                (title, date, start_time, end_time, duration_minutes, 
                 description, participants, location, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                title, date, start_time, end_time, duration_minutes,
                description, participants, location, now, now
            ))
            return cursor.lastrowid

    def get_event(self, event_id: int) -> dict[str, Any] | None:
        """Get an event by ID.
        
        Args:
            event_id: The event ID
            
        Returns:
            Event data as a dictionary or None if not found
        """
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM events WHERE id = ?", (event_id,)
            ).fetchone()
            if row:
                return dict(row)
            return None

    def get_events_by_date(self, date: str) -> list[dict[str, Any]]:
        """Get all events for a specific date.
        
        Args:
            date: Date in YYYY-MM-DD format
            
        Returns:
            List of events sorted by start time
        """
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM events WHERE date = ? ORDER BY start_time",
                (date,)
            ).fetchall()
            return [dict(row) for row in rows]

    def get_events_by_date_range(
        self, start_date: str, end_date: str
    ) -> list[dict[str, Any]]:
        """Get all events within a date range.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            List of events sorted by date and start time
        """
        with self.get_connection() as conn:
            rows = conn.execute(
                """SELECT * FROM events 
                   WHERE date BETWEEN ? AND ? 
                   ORDER BY date, start_time""",
                (start_date, end_date)
            ).fetchall()
            return [dict(row) for row in rows]

    def get_events_by_title(self, title: str) -> list[dict[str, Any]]:
        """Get events by title (partial match).
        
        Args:
            title: Title to search for
            
        Returns:
            List of matching events
        """
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM events WHERE title LIKE ? ORDER BY date DESC",
                (f"%{title}%",)
            ).fetchall()
            return [dict(row) for row in rows]

    def update_event(
        self,
        event_id: int,
        date: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        duration_minutes: int | None = None,
        title: str | None = None,
        description: str | None = None,
        participants: str | None = None,
        location: str | None = None,
    ) -> bool:
        """Update an existing event.
        
        Args:
            event_id: The event ID to update
            date: New date (optional)
            start_time: New start time (optional)
            end_time: New end time (optional)
            duration_minutes: New duration (optional)
            title: New title (optional)
            description: New description (optional)
            participants: New participants (optional)
            location: New location (optional)
            
        Returns:
            True if event was updated, False if not found
        """
        now = datetime.now().isoformat()
        updates = []
        values = []

        if date is not None:
            updates.append("date = ?")
            values.append(date)
        if start_time is not None:
            updates.append("start_time = ?")
            values.append(start_time)
        if end_time is not None:
            updates.append("end_time = ?")
            values.append(end_time)
        if duration_minutes is not None:
            updates.append("duration_minutes = ?")
            values.append(duration_minutes)
        if title is not None:
            updates.append("title = ?")
            values.append(title)
        if description is not None:
            updates.append("description = ?")
            values.append(description)
        if participants is not None:
            updates.append("participants = ?")
            values.append(participants)
        if location is not None:
            updates.append("location = ?")
            values.append(location)

        if not updates:
            return False

        updates.append("updated_at = ?")
        values.append(now)
        values.append(event_id)

        with self.get_connection() as conn:
            cursor = conn.execute(
                f"UPDATE events SET {', '.join(updates)} WHERE id = ?",
                values
            )
            return cursor.rowcount > 0

    def delete_event(self, event_id: int) -> bool:
        """Delete an event.
        
        Args:
            event_id: The event ID to delete
            
        Returns:
            True if event was deleted, False if not found
        """
        with self.get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM events WHERE id = ?", (event_id,)
            )
            return cursor.rowcount > 0

    def check_conflict(
        self, date: str, start_time: str, end_time: str, exclude_event_id: int | None = None
    ) -> list[dict[str, Any]]:
        """Check for scheduling conflicts.
        
        Args:
            date: Date to check (YYYY-MM-DD)
            start_time: Start time (HH:MM)
            end_time: End time (HH:MM)
            exclude_event_id: Optional event ID to exclude (for rescheduling)
            
        Returns:
            List of conflicting events
        """
        with self.get_connection() as conn:
            if exclude_event_id:
                rows = conn.execute(
                    """SELECT * FROM events 
                       WHERE date = ? 
                       AND NOT (end_time <= ? OR start_time >= ?)
                       AND id != ?
                       ORDER BY start_time""",
                    (date, start_time, end_time, exclude_event_id)
                ).fetchall()
            else:
                rows = conn.execute(
                    """SELECT * FROM events 
                       WHERE date = ? 
                       AND NOT (end_time <= ? OR start_time >= ?)
                       ORDER BY start_time""",
                    (date, start_time, end_time)
                ).fetchall()
            return [dict(row) for row in rows]

    # Session operations
    def create_session(self, session_id: str) -> None:
        """Create a new session.
        
        Args:
            session_id: Unique session identifier
        """
        now = datetime.now().isoformat()
        with self.get_connection() as conn:
            conn.execute(
                "INSERT INTO sessions (session_id, created_at, last_active) VALUES (?, ?, ?)",
                (session_id, now, now)
            )

    def get_or_create_session(self, session_id: str) -> str:
        """Get existing session or create new one.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            The session ID
        """
        now = datetime.now().isoformat()
        with self.get_connection() as conn:
            # Check if session exists
            row = conn.execute(
                "SELECT session_id FROM sessions WHERE session_id = ?",
                (session_id,)
            ).fetchone()
            
            if row:
                # Update last active
                conn.execute(
                    "UPDATE sessions SET last_active = ? WHERE session_id = ?",
                    (now, session_id)
                )
            else:
                # Create new session
                conn.execute(
                    "INSERT INTO sessions (session_id, created_at, last_active) VALUES (?, ?, ?)",
                    (session_id, now, now)
                )
            
            return session_id

    def add_message(
        self, session_id: str, role: str, content: str
    ) -> None:
        """Add a message to the session history.
        
        Args:
            session_id: Session identifier
            role: Message role (user, assistant, system)
            content: Message content
        """
        now = datetime.now().isoformat()
        with self.get_connection() as conn:
            conn.execute(
                "INSERT INTO messages (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                (session_id, role, content, now)
            )
            # Update session last active
            conn.execute(
                "UPDATE sessions SET last_active = ? WHERE session_id = ?",
                (now, session_id)
            )

    def get_session_messages(
        self, session_id: str, limit: int = 50
    ) -> list[dict[str, Any]]:
        """Get messages for a session.
        
        Args:
            session_id: Session identifier
            limit: Maximum number of messages to return
            
        Returns:
            List of messages ordered by timestamp
        """
        with self.get_connection() as conn:
            rows = conn.execute(
                """SELECT role, content, timestamp FROM messages 
                   WHERE session_id = ? 
                   ORDER BY timestamp DESC 
                   LIMIT ?""",
                (session_id, limit)
            ).fetchall()
            # Reverse to get chronological order
            return [dict(row) for row in reversed(rows)]

    def get_all_events(self) -> list[dict[str, Any]]:
        """Get all events.
        
        Returns:
            List of all events
        """
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM events ORDER BY date, start_time"
            ).fetchall()
            return [dict(row) for row in rows]
