"""SmartCalendar - Intelligent Calendar Management Agent.

An AI-powered calendar assistant built with OpenAI Agents SDK.
"""

from .agent import SmartCalendarAgent, create_smart_calendar_agent
from .database import CalendarDatabase
from .main import main
from .models import CalendarEvent, ConflictInfo, DaySchedule, TimeSlot, WeekSchedule
from .service import CalendarService
from .session import Message, Session, SessionManager
from .time_parser import NaturalLanguageTimeParser, parse_natural_time

__version__ = "0.1.0"
__all__ = [
    # Main entry point
    "main",
    # Agent
    "SmartCalendarAgent",
    "create_smart_calendar_agent",
    # Database
    "CalendarDatabase",
    # Service
    "CalendarService",
    # Session
    "SessionManager",
    "Session",
    "Message",
    # Models
    "CalendarEvent",
    "ConflictInfo",
    "DaySchedule",
    "TimeSlot",
    "WeekSchedule",
    # Time Parser
    "NaturalLanguageTimeParser",
    "parse_natural_time",
]
