"""Calendar service with all core operations for SmartCalendar."""

from datetime import datetime, timedelta
from typing import Any

from .database import CalendarDatabase
from .models import (
    CalendarEvent,
    ConflictInfo,
    DaySchedule,
    TimeSlot,
    WeekSchedule,
)
from .time_parser import NaturalLanguageTimeParser


class CalendarService:
    """Service for managing calendar events and operations."""

    # Working hours configuration
    WORKING_HOUR_START = 9  # 9 AM
    WORKING_HOUR_END = 17  # 5 PM

    # Minimum meeting duration in minutes
    MIN_MEETING_DURATION = 15

    # Default meeting duration in minutes
    DEFAULT_MEETING_DURATION = 60

    # Maximum days to search for available slots
    MAX_DAYS_TO_SEARCH = 14

    def __init__(self, database: CalendarDatabase):
        """Initialize the calendar service.
        
        Args:
            database: CalendarDatabase instance
        """
        self.db = database
        self.time_parser = NaturalLanguageTimeParser()

    # Event Creation
    def create_event(
        self,
        title: str,
        date: str,
        start_time: str,
        duration_minutes: int,
        description: str | None = None,
        participants: list[str] | None = None,
        location: str | None = None,
    ) -> tuple[bool, CalendarEvent | ConflictInfo, str]:
        """Create a new calendar event.
        
        Args:
            title: Event title
            date: Event date (YYYY-MM-DD)
            start_time: Start time (HH:MM)
            duration_minutes: Duration in minutes
            description: Optional event description
            participants: Optional list of participants
            location: Optional location
            
        Returns:
            Tuple of (success, event_or_conflict, message)
        """
        # Calculate end time
        start_dt = datetime.strptime(start_time, "%H:%M")
        end_dt = start_dt + timedelta(minutes=duration_minutes)
        end_time = end_dt.strftime("%H:%M")

        # Check for conflicts
        conflicts = self.db.check_conflict(date, start_time, end_time)

        if conflicts:
            # Find alternative slots
            suggested_slots = self.find_available_slots(
                date, duration_minutes, max_days=3
            )
            
            conflict_info = ConflictInfo(
                conflicting_events=[CalendarEvent.from_dict(c) for c in conflicts],
                requested_date=date,
                requested_start=start_time,
                requested_end=end_time,
                suggested_slots=suggested_slots,
            )
            return (
                False,
                conflict_info,
                f"Cannot schedule '{title}' due to conflicts. Please choose another time."
            )

        # Create the event
        participants_str = (
            ", ".join(participants) if participants else None
        )
        event_id = self.db.create_event(
            title=title,
            date=date,
            start_time=start_time,
            end_time=end_time,
            duration_minutes=duration_minutes,
            description=description,
            participants=participants_str,
            location=location,
        )

        event = CalendarEvent(
            id=event_id,
            title=title,
            date=date,
            start_time=start_time,
            end_time=end_time,
            duration_minutes=duration_minutes,
            description=description,
            participants=participants or [],
            location=location,
        )

        return (True, event, f"Event '{title}' scheduled successfully.")

    # Event Retrieval
    def get_event(self, event_id: int) -> CalendarEvent | None:
        """Get an event by ID.
        
        Args:
            event_id: Event ID
            
        Returns:
            CalendarEvent or None
        """
        event_data = self.db.get_event(event_id)
        if event_data:
            return CalendarEvent.from_dict(event_data)
        return None

    def get_events_by_title(
        self, title: str, limit: int = 5
    ) -> list[CalendarEvent]:
        """Get events by title (partial match).
        
        Args:
            title: Title to search for
            limit: Maximum number of events to return
            
        Returns:
            List of matching CalendarEvents
        """
        events = self.db.get_events_by_title(title)
        return [CalendarEvent.from_dict(e) for e in events[:limit]]

    def get_events_for_date(self, date: str) -> DaySchedule:
        """Get all events for a specific date.
        
        Args:
            date: Date in YYYY-MM-DD format
            
        Returns:
            DaySchedule with events and free slots
        """
        events_data = self.db.get_events_by_date(date)
        events = [CalendarEvent.from_dict(e) for e in events_data]

        # Calculate free slots
        free_slots = self._calculate_free_slots(date, events)

        return DaySchedule(date=date, events=events, free_slots=free_slots)

    def get_events_for_week(
        self, start_date: str
    ) -> WeekSchedule:
        """Get all events for a week.
        
        Args:
            start_date: Start date of the week (YYYY-MM-DD)
            
        Returns:
            WeekSchedule with daily schedules
        """
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = start_dt + timedelta(days=6)
        
        end_date = end_dt.strftime("%Y-%m-%d")
        
        events_data = self.db.get_events_by_date_range(start_date, end_date)
        events = [CalendarEvent.from_dict(e) for e in events_data]

        # Group events by day
        days = []
        current_dt = start_dt
        while current_dt <= end_dt:
            date_str = current_dt.strftime("%Y-%m-%d")
            day_events = [e for e in events if e.date == date_str]
            free_slots = self._calculate_free_slots(date_str, day_events)
            days.append(DaySchedule(date=date_str, events=day_events, free_slots=free_slots))
            current_dt += timedelta(days=1)

        return WeekSchedule(
            start_date=start_date,
            end_date=end_date,
            days=days,
        )

    def _calculate_free_slots(
        self, date: str, events: list[CalendarEvent]
    ) -> list[TimeSlot]:
        """Calculate free time slots for a date.
        
        Args:
            date: Date in YYYY-MM-DD format
            events: List of events for the date
            
        Returns:
            List of available TimeSlots
        """
        if not events:
            # Entire working day is free
            return [
                TimeSlot(
                    date=date,
                    start_time=f"{self.WORKING_HOUR_START:02d}:00",
                    end_time=f"{self.WORKING_HOUR_END:02d}:00",
                    duration_minutes=(
                        self.WORKING_HOUR_END - self.WORKING_HOUR_START
                    )
                    * 60,
                )
            ]

        # Sort events by start time
        sorted_events = sorted(events, key=lambda e: e.start_time)

        free_slots = []
        current_time = self.WORKING_HOUR_START * 60  # Convert to minutes

        for event in sorted_events:
            event_start = self._time_to_minutes(event.start_time)
            event_end = self._time_to_minutes(event.end_time)

            if event_start > current_time:
                # Free slot before this event
                duration = event_start - current_time
                if duration >= self.MIN_MEETING_DURATION:
                    free_slots.append(
                        TimeSlot(
                            date=date,
                            start_time=self._minutes_to_time(current_time),
                            end_time=self._minutes_to_time(event_start),
                            duration_minutes=duration,
                        )
                    )

            current_time = max(current_time, event_end)

        # Check for free slot after last event
        work_end = self.WORKING_HOUR_END * 60
        if current_time < work_end:
            duration = work_end - current_time
            if duration >= self.MIN_MEETING_DURATION:
                free_slots.append(
                    TimeSlot(
                        date=date,
                        start_time=self._minutes_to_time(current_time),
                        end_time=self._minutes_to_time(work_end),
                        duration_minutes=duration,
                    )
                )

        return free_slots

    def _time_to_minutes(self, time_str: str) -> int:
        """Convert HH:MM to minutes since midnight."""
        h, m = map(int, time_str.split(":"))
        return h * 60 + m

    def _minutes_to_time(self, minutes: int) -> str:
        """Convert minutes since midnight to HH:MM."""
        h = minutes // 60
        m = minutes % 60
        return f"{h:02d}:{m:02d}"

    # Event Rescheduling
    def reschedule_event(
        self,
        event_id: int,
        new_date: str,
        new_start_time: str,
    ) -> tuple[bool, CalendarEvent | ConflictInfo, str]:
        """Reschedule an existing event.
        
        Args:
            event_id: Event ID to reschedule
            new_date: New date (YYYY-MM-DD)
            new_start_time: New start time (HH:MM)
            
        Returns:
            Tuple of (success, event_or_conflict, message)
        """
        # Get the existing event
        event = self.get_event(event_id)
        if not event:
            return (False, None, f"Event with ID {event_id} not found.")

        # Calculate new end time
        start_dt = datetime.strptime(new_start_time, "%H:%M")
        end_dt = start_dt + timedelta(minutes=event.duration_minutes)
        new_end_time = end_dt.strftime("%H:%M")

        # Check for conflicts (excluding the current event)
        conflicts = self.db.check_conflict(
            new_date, new_start_time, new_end_time, exclude_event_id=event_id
        )

        if conflicts:
            suggested_slots = self.find_available_slots(
                new_date, event.duration_minutes, max_days=3
            )
            
            conflict_info = ConflictInfo(
                conflicting_events=[CalendarEvent.from_dict(c) for c in conflicts],
                requested_date=new_date,
                requested_start=new_start_time,
                requested_end=new_end_time,
                suggested_slots=suggested_slots,
            )
            return (
                False,
                conflict_info,
                f"Cannot reschedule to the new time due to conflicts."
            )

        # Update the event
        self.db.update_event(
            event_id=event_id,
            date=new_date,
            start_time=new_start_time,
            end_time=new_end_time,
        )

        # Return updated event
        updated_event = CalendarEvent(
            id=event.id,
            title=event.title,
            date=new_date,
            start_time=new_start_time,
            end_time=new_end_time,
            duration_minutes=event.duration_minutes,
            description=event.description,
            participants=event.participants,
            location=event.location,
        )

        return (True, updated_event, f"Event '{event.title}' rescheduled successfully.")

    # Event Cancellation
    def cancel_event(self, event_id: int) -> tuple[bool, CalendarEvent | None, str]:
        """Cancel/delete an event.
        
        Args:
            event_id: Event ID to cancel
            
        Returns:
            Tuple of (success, deleted_event, message)
        """
        event = self.get_event(event_id)
        if not event:
            return (False, None, f"Event with ID {event_id} not found.")

        self.db.delete_event(event_id)
        return (True, event, f"Event '{event.title}' has been cancelled.")

    # Availability Checking
    def check_availability(
        self,
        date: str,
        duration_minutes: int,
        preferred_start: str | None = None,
        preferred_end: str | None = None,
    ) -> list[TimeSlot]:
        """Check available time slots for a given duration.
        
        Args:
            date: Date to check (YYYY-MM-DD)
            duration_minutes: Required duration in minutes
            preferred_start: Optional preferred start time (HH:MM)
            preferred_end: Optional preferred end time (HH:MM)
            
        Returns:
            List of available TimeSlots
        """
        day_schedule = self.get_events_for_date(date)
        
        # Filter slots by duration
        available_slots = [
            slot for slot in day_schedule.free_slots
            if slot.duration_minutes >= duration_minutes
        ]

        # Filter by preferred time range if specified
        if preferred_start or preferred_end:
            filtered_slots = []
            for slot in available_slots:
                slot_start = self._time_to_minutes(slot.start_time)
                slot_end = self._time_to_minutes(slot.end_time)
                
                if preferred_start:
                    pref_start = self._time_to_minutes(preferred_start)
                    if slot_end <= pref_start:
                        continue
                
                if preferred_end:
                    pref_end = self._time_to_minutes(preferred_end)
                    if slot_start >= pref_end:
                        continue
                
                filtered_slots.append(slot)
            
            available_slots = filtered_slots

        return available_slots

    def find_available_slots(
        self,
        start_date: str,
        duration_minutes: int,
        max_days: int = 7,
    ) -> list[TimeSlot]:
        """Find available time slots across multiple days.
        
        Args:
            start_date: Start searching from this date (YYYY-MM-DD)
            duration_minutes: Required duration in minutes
            max_days: Maximum number of days to search
            
        Returns:
            List of available TimeSlots (up to 10)
        """
        slots = []
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")

        for i in range(max_days):
            if len(slots) >= 10:
                break

            current_date = (start_dt + timedelta(days=i)).strftime("%Y-%m-%d")
            day_slots = self.check_availability(current_date, duration_minutes)
            slots.extend(day_slots[:3])  # Get up to 3 slots per day

        return slots[:10]

    # Smart Scheduling Suggestions
    def suggest_optimal_times(
        self,
        duration_minutes: int,
        preferred_days: list[str] | None = None,
        avoid_days: list[str] | None = None,
    ) -> list[TimeSlot]:
        """Suggest optimal meeting times based on smart scheduling.
        
        Args:
            duration_minutes: Required duration in minutes
            preferred_days: Optional list of preferred weekdays (0=Monday, 6=Sunday)
            avoid_days: Optional list of days to avoid
            
        Returns:
            List of suggested TimeSlots
        """
        suggestions = []
        start_dt = datetime.now()

        for i in range(self.MAX_DAYS_TO_SEARCH):
            if len(suggestions) >= 5:
                break

            current_date = (start_dt + timedelta(days=i)).date()
            weekday = current_date.weekday()

            # Skip avoided days
            if avoid_days and weekday in avoid_days:
                continue

            # Prefer preferred days
            if preferred_days and weekday not in preferred_days:
                continue

            date_str = current_date.isoformat()
            day_slots = self.check_availability(date_str, duration_minutes)

            # Prioritize mid-morning and mid-afternoon slots
            for slot in day_slots:
                slot_start = self._time_to_minutes(slot.start_time)
                
                # Prefer 10-11 AM or 2-4 PM
                if (10 * 60 <= slot_start <= 11 * 60) or (
                    14 * 60 <= slot_start <= 16 * 60
                ):
                    suggestions.append(slot)
                    if len(suggestions) >= 5:
                        break

        return suggestions

    def get_schedule_summary(
        self, date: str | None = None
    ) -> str:
        """Get a summary of the schedule for a date or today.
        
        Args:
            date: Optional date (YYYY-MM-DD). Defaults to today.
            
        Returns:
            Formatted schedule summary string
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        # Check if date is a day name
        day_names = {
            "today": datetime.now().strftime("%Y-%m-%d"),
            "tomorrow": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
            "yesterday": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
        }
        
        if date.lower() in day_names:
            date = day_names[date.lower()]

        day_schedule = self.get_events_for_date(date)
        return day_schedule.to_display_string(
            (self.WORKING_HOUR_START, self.WORKING_HOUR_END)
        )

    def get_upcoming_events(self, limit: int = 5) -> list[CalendarEvent]:
        """Get upcoming events.
        
        Args:
            limit: Maximum number of events to return
            
        Returns:
            List of upcoming CalendarEvents
        """
        today = datetime.now().strftime("%Y-%m-%d")
        all_events = self.db.get_all_events()
        
        # Filter to future events and sort
        upcoming = []
        for event_data in all_events:
            event = CalendarEvent.from_dict(event_data)
            event_datetime = event.get_datetime()
            if event_datetime >= datetime.now():
                upcoming.append(event)

        # Sort by date and time
        upcoming.sort(key=lambda e: e.get_datetime())
        
        return upcoming[:limit]

    # Helper methods for the agent
    def format_event_for_display(self, event: CalendarEvent) -> dict[str, Any]:
        """Format an event for display.
        
        Args:
            event: CalendarEvent to format
            
        Returns:
            Dictionary with formatted event data
        """
        return event.to_display_dict()

    def parse_and_create_event(
        self,
        title: str,
        natural_date: str,
        natural_time: str,
        duration_minutes: int | None = None,
        description: str | None = None,
        participants: list[str] | None = None,
        location: str | None = None,
    ) -> tuple[bool, CalendarEvent | ConflictInfo, str]:
        """Create an event using natural language date/time.
        
        Args:
            title: Event title
            natural_date: Natural language date expression
            natural_time: Natural language time expression
            duration_minutes: Optional duration (will be inferred if not provided)
            description: Optional description
            participants: Optional participants
            location: Optional location
            
        Returns:
            Tuple of (success, event_or_conflict, message)
        """
        # Parse natural language
        date = self.time_parser.parse_date(natural_date)
        time = self.time_parser.parse_time(natural_time)
        
        if not date:
            return (
                False,
                None,
                f"Could not understand the date '{natural_date}'. Please use a format like 'tomorrow', 'next Monday', or '2024-01-15'."
            )
        
        if not time:
            return (
                False,
                None,
                f"Could not understand the time '{natural_time}'. Please use a format like '9 AM', '2:30 PM', or '14:00'."
            )

        # Use default duration if not specified
        if duration_minutes is None:
            duration_minutes = self.time_parser.parse_duration(
                natural_time
            ) or self.DEFAULT_MEETING_DURATION

        return self.create_event(
            title=title,
            date=date,
            start_time=time,
            duration_minutes=duration_minutes,
            description=description,
            participants=participants,
            location=location,
        )
