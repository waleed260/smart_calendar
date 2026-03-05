"""Event models and data structures for SmartCalendar."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any


@dataclass
class CalendarEvent:
    """Represents a calendar event."""
    id: int | None = None
    title: str = ""
    date: str = ""  # YYYY-MM-DD
    start_time: str = ""  # HH:MM
    end_time: str = ""  # HH:MM
    duration_minutes: int = 0
    description: str | None = None
    participants: list[str] = field(default_factory=list)
    location: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CalendarEvent":
        """Create a CalendarEvent from a dictionary.
        
        Args:
            data: Dictionary with event data
            
        Returns:
            CalendarEvent instance
        """
        participants = []
        if data.get("participants"):
            participants = [
                p.strip() for p in data["participants"].split(",")
            ]

        created_at = None
        if data.get("created_at"):
            created_at = datetime.fromisoformat(data["created_at"])

        updated_at = None
        if data.get("updated_at"):
            updated_at = datetime.fromisoformat(data["updated_at"])

        return cls(
            id=data.get("id"),
            title=data.get("title", ""),
            date=data.get("date", ""),
            start_time=data.get("start_time", ""),
            end_time=data.get("end_time", ""),
            duration_minutes=data.get("duration_minutes", 0),
            description=data.get("description"),
            participants=participants,
            location=data.get("location"),
            created_at=created_at,
            updated_at=updated_at,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary.
        
        Returns:
            Dictionary representation of the event
        """
        return {
            "id": self.id,
            "title": self.title,
            "date": self.date,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_minutes": self.duration_minutes,
            "description": self.description,
            "participants": ", ".join(self.participants) if self.participants else None,
            "location": self.location,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def to_display_dict(self) -> dict[str, Any]:
        """Convert event to a display-friendly dictionary.
        
        Returns:
            Dictionary with formatted event data for display
        """
        return {
            "Title": self.title,
            "Date": self._format_date(),
            "Start Time": self._format_time(self.start_time),
            "End Time": self._format_time(self.end_time),
            "Duration": self._format_duration(),
            "Participants": ", ".join(self.participants) if self.participants else "None",
            "Location": self.location or "Not specified",
        }

    def _format_date(self) -> str:
        """Format date for display."""
        if not self.date:
            return "Not specified"
        try:
            dt = datetime.strptime(self.date, "%Y-%m-%d")
            return dt.strftime("%A, %B %d, %Y")
        except ValueError:
            return self.date

    def _format_time(self, time_str: str) -> str:
        """Format time for display."""
        if not time_str:
            return "Not specified"
        try:
            dt = datetime.strptime(time_str, "%H:%M")
            return dt.strftime("%I:%M %p")
        except ValueError:
            return time_str

    def _format_duration(self) -> str:
        """Format duration for display."""
        hours = self.duration_minutes // 60
        minutes = self.duration_minutes % 60
        
        parts = []
        if hours:
            parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
        if minutes:
            parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
        
        return " ".join(parts) if parts else "Not specified"

    def get_datetime(self) -> datetime:
        """Get event start as datetime."""
        return datetime.strptime(
            f"{self.date} {self.start_time}", "%Y-%m-%d %H:%M"
        )

    def get_end_datetime(self) -> datetime:
        """Get event end as datetime."""
        return datetime.strptime(
            f"{self.date} {self.end_time}", "%Y-%m-%d %H:%M"
        )

    def overlaps_with(self, other: "CalendarEvent") -> bool:
        """Check if this event overlaps with another.
        
        Args:
            other: Another CalendarEvent
            
        Returns:
            True if events overlap
        """
        if self.date != other.date:
            return False

        self_start = datetime.strptime(self.start_time, "%H:%M")
        self_end = datetime.strptime(self.end_time, "%H:%M")
        other_start = datetime.strptime(other.start_time, "%H:%M")
        other_end = datetime.strptime(other.end_time, "%H:%M")

        # Events overlap if one starts before the other ends
        return not (self_end <= other_start or self_start >= other_end)


@dataclass
class TimeSlot:
    """Represents an available time slot."""
    date: str  # YYYY-MM-DD
    start_time: str  # HH:MM
    end_time: str  # HH:MM
    duration_minutes: int

    def to_display_string(self) -> str:
        """Get a display-friendly string representation."""
        try:
            dt = datetime.strptime(self.date, "%Y-%m-%d")
            date_str = dt.strftime("%A, %B %d")
            start_dt = datetime.strptime(self.start_time, "%H:%M")
            end_dt = datetime.strptime(self.end_time, "%H:%M")
            start_str = start_dt.strftime("%I:%M %p")
            end_str = end_dt.strftime("%I:%M %p")
            return f"{date_str}: {start_str} - {end_str}"
        except ValueError:
            return f"{self.date}: {self.start_time} - {self.end_time}"

    def to_event(
        self,
        title: str,
        description: str | None = None,
        participants: list[str] | None = None,
        location: str | None = None,
    ) -> CalendarEvent:
        """Convert time slot to a CalendarEvent.
        
        Args:
            title: Event title
            description: Optional event description
            participants: Optional list of participants
            location: Optional location
            
        Returns:
            CalendarEvent instance
        """
        return CalendarEvent(
            title=title,
            date=self.date,
            start_time=self.start_time,
            end_time=self.end_time,
            duration_minutes=self.duration_minutes,
            description=description,
            participants=participants or [],
            location=location,
        )


@dataclass
class DaySchedule:
    """Represents a day's schedule."""
    date: str
    events: list[CalendarEvent] = field(default_factory=list)
    free_slots: list[TimeSlot] = field(default_factory=list)

    def to_display_string(self, working_hours: tuple[int, int] = (9, 17)) -> str:
        """Get a display-friendly string representation.
        
        Args:
            working_hours: Tuple of (start_hour, end_hour) for working hours
            
        Returns:
            Formatted schedule string
        """
        if not self.events:
            return f"No events scheduled for {self.date}"

        lines = []
        try:
            dt = datetime.strptime(self.date, "%Y-%m-%d")
            date_str = dt.strftime("%A, %B %d, %Y")
        except ValueError:
            date_str = self.date

        lines.append(f"Schedule for {date_str}:")
        lines.append("")

        for i, event in enumerate(self.events, 1):
            start_formatted = datetime.strptime(
                event.start_time, "%H:%M"
            ).strftime("%I:%M %p")
            lines.append(
                f"{i}. {event.title} — {start_formatted} "
                f"({event.duration_minutes} min)"
            )

        if self.free_slots:
            lines.append("")
            lines.append("Free Time:")
            for slot in self.free_slots:
                start_str = datetime.strptime(
                    slot.start_time, "%H:%M"
                ).strftime("%I:%M %p")
                end_str = datetime.strptime(
                    slot.end_time, "%H:%M"
                ).strftime("%I:%M %p")
                lines.append(f"  {start_str} – {end_str}")

        return "\n".join(lines)


@dataclass
class WeekSchedule:
    """Represents a week's schedule."""
    start_date: str
    end_date: str
    days: list[DaySchedule] = field(default_factory=list)

    def to_display_string(self) -> str:
        """Get a display-friendly string representation."""
        lines = []
        try:
            start_dt = datetime.strptime(self.start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(self.end_date, "%Y-%m-%d")
            start_str = start_dt.strftime("%B %d")
            end_str = end_dt.strftime("%d, %Y")
            lines.append(f"Week of {start_str} - {end_str}")
            lines.append("=" * 40)
            lines.append("")
        except ValueError:
            lines.append(f"Week: {self.start_date} to {self.end_date}")
            lines.append("")

        for day in self.days:
            lines.append(day.to_display_string())
            lines.append("")

        return "\n".join(lines)


@dataclass
class ConflictInfo:
    """Information about a scheduling conflict."""
    conflicting_events: list[CalendarEvent]
    requested_date: str
    requested_start: str
    requested_end: str
    suggested_slots: list[TimeSlot] = field(default_factory=list)

    def to_display_string(self) -> str:
        """Get a display-friendly string representation."""
        lines = ["Time Conflict Detected!"]
        lines.append("")
        lines.append("The following events conflict with your requested time:")
        lines.append("")

        for event in self.conflicting_events:
            start_str = datetime.strptime(
                event.start_time, "%H:%M"
            ).strftime("%I:%M %p")
            lines.append(f"• {event.title} ({start_str})")

        if self.suggested_slots:
            lines.append("")
            lines.append("Here are available alternatives:")
            lines.append("")
            for i, slot in enumerate(self.suggested_slots, 1):
                lines.append(f"Option {i}: {slot.to_display_string()}")

        return "\n".join(lines)
