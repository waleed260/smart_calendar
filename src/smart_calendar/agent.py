"""SmartCalendar Agent using OpenAI Agents SDK."""

import json
from datetime import datetime

from agents import Agent, Runner, function_tool

from .database import CalendarDatabase
from .models import ConflictInfo
from .service import CalendarService
from .session import SessionManager


# System instruction for the SmartCalendar agent
SYSTEM_INSTRUCTION = """You are SmartCalendar, an intelligent AI assistant that helps users manage their calendar efficiently.

Your responsibilities include scheduling events, rescheduling events, cancelling events, checking availability, summarizing schedules, and helping users organize their time in a productive way.

CORE CAPABILITIES:
1. Create new events or meetings
2. Check calendar availability
3. Detect scheduling conflicts
4. Suggest alternative meeting times
5. Reschedule existing events
6. Cancel or delete events
7. Provide daily or weekly schedule summaries
8. Interpret natural language time expressions
9. Suggest better scheduling practices
10. Maintain conversational context within the session

IMPORTANT BEHAVIORS:
- Always check for conflicts before scheduling
- If there's a conflict, suggest at least 3 alternative time slots
- Be proactive in suggesting better scheduling practices
- Avoid scheduling overlapping meetings
- Suggest breaks between meetings
- Warn when a day becomes overloaded
- Recommend focus time blocks for deep work
- Encourage balanced schedules

NATURAL LANGUAGE TIME:
You understand expressions like:
- "tomorrow morning", "tomorrow afternoon", "tonight"
- "next Monday", "this Friday", "next week"
- "this weekend", "end of the week"
- "in two hours", "in 30 minutes"

When time expressions are ambiguous, ask for clarification.

OUTPUT FORMATS:

When confirming an event, use this format:
```
Event Scheduled Successfully

Title: [event title]
Date: [formatted date]
Start Time: [formatted time]
Duration: [duration]
Participants: [participants or "None"]
Location: [location or "Not specified"]
```

When there's a conflict:
```
Time Conflict Detected!

The following events conflict with your requested time:
• [Event name] ([time])

Here are available alternatives:

Option 1: [date and time range]
Option 2: [date and time range]
Option 3: [date and time range]
```

For schedule summaries:
```
Today's Schedule:

1. [Event name] — [time]
2. [Event name] — [time]

Free Time:
[time range]
[time range]
```

Be helpful, proactive, and concise. Your goal is to make calendar management effortless and intelligent for the user.
"""


class SmartCalendarAgent:
    """SmartCalendar agent powered by OpenAI Agents SDK."""

    def __init__(
        self,
        database: CalendarDatabase | None = None,
        session_id: str | None = None,
        model: str = "gpt-4o-mini",
    ):
        """Initialize the SmartCalendar agent.

        Args:
            database: CalendarDatabase instance (creates new one if None)
            session_id: Session ID for conversation history
            model: OpenAI model to use
        """
        self.db = database or CalendarDatabase()
        self.service = CalendarService(self.db)
        self.session_manager = SessionManager(self.db)
        self.session_id = session_id or self._generate_session_id()
        self.model = model

        # Get or create session
        self.session = self.session_manager.get_or_create_session(self.session_id)

        # Create the agent with tools
        self.agent = self._create_agent()

    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        import uuid

        return str(uuid.uuid4())

    def _create_agent(self) -> Agent:
        """Create the OpenAI Agent with tools."""
        return Agent(
            name="SmartCalendar",
            instructions=SYSTEM_INSTRUCTION,
            model=self.model,
            tools=[
                self._create_event_tool(),
                self._get_schedule_tool(),
                self._check_availability_tool(),
                self._reschedule_event_tool(),
                self._cancel_event_tool(),
                self._find_events_tool(),
                self._get_upcoming_events_tool(),
                self._suggest_times_tool(),
            ],
        )

    # Tool definitions
    def _create_event_tool(self):
        """Tool to create a new event."""

        @function_tool
        def create_event(
            title: str,
            date: str,
            start_time: str,
            duration_minutes: int = 60,
            description: str | None = None,
            participants: list[str] | None = None,
            location: str | None = None,
        ) -> str:
            """Create a new calendar event.

            Args:
                title: Event title
                date: Event date in YYYY-MM-DD format
                start_time: Start time in HH:MM format (24-hour)
                duration_minutes: Duration in minutes (default: 60)
                description: Optional event description
                participants: Optional list of participant names
                location: Optional location or meeting link

            Returns:
                Confirmation message or conflict information
            """
            success, result, message = self.service.create_event(
                title=title,
                date=date,
                start_time=start_time,
                duration_minutes=duration_minutes,
                description=description,
                participants=participants,
                location=location,
            )

            if success:
                event = result
                response = {
                    "status": "success",
                    "message": message,
                    "event": {
                        "Title": event.title,
                        "Date": self._format_date_display(event.date),
                        "Start Time": self._format_time_display(event.start_time),
                        "Duration": f"{event.duration_minutes} minutes",
                        "Participants": (
                            ", ".join(event.participants)
                            if event.participants
                            else "None"
                        ),
                        "Location": event.location or "Not specified",
                    },
                }
            else:
                conflict = result
                alternatives = []
                if isinstance(conflict, ConflictInfo):
                    alternatives = [
                        slot.to_display_string()
                        for slot in conflict.suggested_slots[:3]
                    ]

                response = {
                    "status": "conflict",
                    "message": message,
                    "conflicting_events": [
                        e.title for e in conflict.conflicting_events
                    ],
                    "alternatives": alternatives,
                }

            return json.dumps(response, indent=2)

        return create_event

    def _get_schedule_tool(self):
        """Tool to get schedule for a date."""

        @function_tool
        def get_schedule(date: str | None = None) -> str:
            """Get the schedule for a specific date or today.

            Args:
                date: Optional date in YYYY-MM-DD format, or natural language
                      like 'today', 'tomorrow', 'next Monday'. Defaults to today.

            Returns:
                Formatted schedule summary
            """
            summary = self.service.get_schedule_summary(date or "today")
            return summary

        return get_schedule

    def _check_availability_tool(self):
        """Tool to check availability."""

        @function_tool
        def check_availability(
            date: str,
            duration_minutes: int = 60,
        ) -> str:
            """Check available time slots for a given date and duration.

            Args:
                date: Date in YYYY-MM-DD format
                duration_minutes: Required duration in minutes (default: 60)

            Returns:
                List of available time slots
            """
            slots = self.service.check_availability(date, duration_minutes)

            if not slots:
                return json.dumps(
                    {"status": "no_availability", "message": "No available slots found"}
                )

            response = {
                "status": "success",
                "date": self._format_date_display(date),
                "available_slots": [
                    {
                        "start": slot.start_time,
                        "end": slot.end_time,
                        "duration": f"{slot.duration_minutes} minutes",
                    }
                    for slot in slots
                ],
            }
            return json.dumps(response, indent=2)

        return check_availability

    def _reschedule_event_tool(self):
        """Tool to reschedule an event."""

        @function_tool
        def reschedule_event(
            event_id: int,
            new_date: str,
            new_start_time: str,
        ) -> str:
            """Reschedule an existing event to a new time.

            Args:
                event_id: The ID of the event to reschedule
                new_date: New date in YYYY-MM-DD format
                new_start_time: New start time in HH:MM format (24-hour)

            Returns:
                Confirmation message or conflict information
            """
            success, result, message = self.service.reschedule_event(
                event_id=event_id,
                new_date=new_date,
                new_start_time=new_start_time,
            )

            if success:
                event = result
                response = {
                    "status": "success",
                    "message": message,
                    "event": {
                        "Title": event.title,
                        "Date": self._format_date_display(event.date),
                        "Start Time": self._format_time_display(event.start_time),
                        "Duration": f"{event.duration_minutes} minutes",
                    },
                }
            else:
                conflict = result
                alternatives = []
                if isinstance(conflict, ConflictInfo):
                    alternatives = [
                        slot.to_display_string()
                        for slot in conflict.suggested_slots[:3]
                    ]

                response = {
                    "status": "conflict",
                    "message": message,
                    "alternatives": alternatives,
                }

            return json.dumps(response, indent=2)

        return reschedule_event

    def _cancel_event_tool(self):
        """Tool to cancel an event."""

        @function_tool
        def cancel_event(event_id: int) -> str:
            """Cancel/delete an event.

            Args:
                event_id: The ID of the event to cancel

            Returns:
                Confirmation message
            """
            success, event, message = self.service.cancel_event(event_id)

            if success:
                response = {
                    "status": "success",
                    "message": message,
                    "cancelled_event": event.title if event else None,
                }
            else:
                response = {
                    "status": "error",
                    "message": message,
                }

            return json.dumps(response, indent=2)

        return cancel_event

    def _find_events_tool(self):
        """Tool to find events by title."""

        @function_tool
        def find_events(title: str, limit: int = 5) -> str:
            """Find events by title (partial match).

            Args:
                title: Title or partial title to search for
                limit: Maximum number of events to return (default: 5)

            Returns:
                List of matching events
            """
            events = self.service.get_events_by_title(title, limit)

            if not events:
                return json.dumps(
                    {
                        "status": "not_found",
                        "message": f"No events found matching '{title}'",
                    }
                )

            response = {
                "status": "success",
                "events": [
                    {
                        "id": e.id,
                        "title": e.title,
                        "date": self._format_date_display(e.date),
                        "start_time": self._format_time_display(e.start_time),
                        "duration": f"{e.duration_minutes} minutes",
                    }
                    for e in events
                ],
            }
            return json.dumps(response, indent=2)

        return find_events

    def _get_upcoming_events_tool(self):
        """Tool to get upcoming events."""

        @function_tool
        def get_upcoming_events(limit: int = 5) -> str:
            """Get upcoming events.

            Args:
                limit: Maximum number of events to return (default: 5)

            Returns:
                List of upcoming events
            """
            events = self.service.get_upcoming_events(limit)

            if not events:
                return json.dumps(
                    {"status": "success", "message": "No upcoming events", "events": []}
                )

            response = {
                "status": "success",
                "events": [
                    {
                        "id": e.id,
                        "title": e.title,
                        "date": self._format_date_display(e.date),
                        "start_time": self._format_time_display(e.start_time),
                        "duration": f"{e.duration_minutes} minutes",
                    }
                    for e in events
                ],
            }
            return json.dumps(response, indent=2)

        return get_upcoming_events

    def _suggest_times_tool(self):
        """Tool to suggest optimal meeting times."""

        @function_tool
        def suggest_optimal_times(
            duration_minutes: int = 60,
            preferred_days: list[int] | None = None,
        ) -> str:
            """Suggest optimal meeting times based on smart scheduling.

            Args:
                duration_minutes: Required duration in minutes (default: 60)
                preferred_days: Optional list of preferred weekdays
                               (0=Monday, 6=Sunday)

            Returns:
                List of suggested time slots
            """
            slots = self.service.suggest_optimal_times(duration_minutes, preferred_days)

            if not slots:
                return json.dumps(
                    {"status": "no_suggestions", "message": "No optimal times found"}
                )

            response = {
                "status": "success",
                "suggestions": [
                    {
                        "date": self._format_date_display(slot.date),
                        "time": f"{slot.start_time} - {slot.end_time}",
                        "duration": f"{slot.duration_minutes} minutes",
                    }
                    for slot in slots
                ],
            }
            return json.dumps(response, indent=2)

        return suggest_optimal_times

    # Helper methods
    def _format_date_display(self, date_str: str) -> str:
        """Format date for display."""
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            return dt.strftime("%A, %B %d, %Y")
        except ValueError:
            return date_str

    def _format_time_display(self, time_str: str) -> str:
        """Format time for display."""
        try:
            dt = datetime.strptime(time_str, "%H:%M")
            return dt.strftime("%I:%M %p")
        except ValueError:
            return time_str

    async def run(self, user_input: str) -> str:
        """Run the agent with user input.

        Args:
            user_input: User's message

        Returns:
            Agent's response
        """
        # Add user message to session history
        self.session_manager.add_message(self.session_id, "user", user_input)

        # Get conversation history
        history = self.session_manager.get_session_messages(self.session_id, limit=20)

        # Run the agent
        result = await Runner.run(
            self.agent,
            input=user_input,
            conversation_history=history[:-1],  # Exclude current user message
        )

        # Add assistant response to session history
        self.session_manager.add_message(
            self.session_id, "assistant", result.final_output
        )

        return result.final_output

    def run_sync(self, user_input: str) -> str:
        """Run the agent synchronously.

        Args:
            user_input: User's message

        Returns:
            Agent's response
        """
        import asyncio

        return asyncio.run(self.run(user_input))


# Convenience function to create and run the agent
def create_smart_calendar_agent(
    session_id: str | None = None,
    model: str = "gpt-4o-mini",
) -> SmartCalendarAgent:
    """Create a new SmartCalendar agent instance.

    Args:
        session_id: Optional session ID for conversation history
        model: OpenAI model to use

    Returns:
        SmartCalendarAgent instance
    """
    return SmartCalendarAgent(session_id=session_id, model=model)
