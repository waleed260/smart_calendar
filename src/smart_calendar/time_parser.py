"""Natural language time parser for SmartCalendar."""

import re
from datetime import datetime, timedelta
from typing import NamedTuple


class ParsedTime(NamedTuple):
    """Result of parsing natural language time."""
    date: str | None  # YYYY-MM-DD
    time: str | None  # HH:MM
    duration_minutes: int | None
    raw_input: str


class NaturalLanguageTimeParser:
    """Parses natural language time expressions into structured datetime values."""

    # Time period mappings
    MORNING_START = "09:00"
    MORNING_END = "12:00"
    AFTERNOON_START = "13:00"
    AFTERNOON_END = "17:00"
    EVENING_START = "18:00"
    EVENING_END = "21:00"
    NIGHT_START = "20:00"
    NIGHT_END = "23:00"

    # Default duration in minutes
    DEFAULT_DURATION = 60

    def __init__(self, reference_date: datetime | None = None):
        """Initialize the parser.
        
        Args:
            reference_date: The reference date for relative expressions.
                           Defaults to current date/time.
        """
        self.reference_date = reference_date or datetime.now()

    def parse(self, text: str) -> ParsedTime:
        """Parse natural language time expression.
        
        Args:
            text: Natural language time expression
            
        Returns:
            ParsedTime with extracted date, time, and duration
        """
        text = text.lower().strip()
        
        date = None
        time = None
        duration = None

        # Try to extract date
        date = self._extract_date(text)
        
        # Try to extract time
        time = self._extract_time(text)
        
        # Try to extract duration
        duration = self._extract_duration(text)

        return ParsedTime(
            date=date,
            time=time,
            duration_minutes=duration,
            raw_input=text
        )

    def _extract_date(self, text: str) -> str | None:
        """Extract date from text.
        
        Args:
            text: Input text
            
        Returns:
            Date in YYYY-MM-DD format or None
        """
        # Check for explicit date patterns first
        # Pattern: YYYY-MM-DD
        match = re.search(r"\d{4}-\d{2}-\d{2}", text)
        if match:
            return match.group()

        # Pattern: MM/DD/YYYY or MM-DD-YYYY
        match = re.search(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})", text)
        if match:
            month, day, year = match.groups()
            return f"{year}-{int(month):02d}-{int(day):02d}"

        # Pattern: Month DD, YYYY or DD Month YYYY
        month_names = {
            "january": 1, "february": 2, "march": 3, "april": 4,
            "may": 5, "june": 6, "july": 7, "august": 8,
            "september": 9, "october": 10, "november": 11, "december": 12,
            "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6,
            "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12
        }
        
        for month_name, month_num in month_names.items():
            # Month DD, YYYY
            match = re.search(
                rf"{month_name}\s+(\d{{1,2}}),?\s+(\d{{4}})",
                text,
                re.IGNORECASE
            )
            if match:
                day, year = match.groups()
                return f"{year}-{month_num:02d}-{int(day):02d}"

        # Relative date expressions
        today = self.reference_date.date()

        if "today" in text:
            return today.isoformat()

        if "tomorrow" in text:
            return (today + timedelta(days=1)).isoformat()

        if "yesterday" in text:
            return (today - timedelta(days=1)).isoformat()

        # Day of week
        day_names = {
            "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
            "friday": 4, "saturday": 5, "sunday": 6,
            "mon": 0, "tue": 1, "wed": 2, "thu": 3, "thur": 3,
            "fri": 4, "sat": 5, "sun": 6
        }

        for day_name, weekday_num in day_names.items():
            if day_name in text:
                # Find next occurrence of this day
                days_ahead = weekday_num - today.weekday()
                
                # Check for "next" modifier
                if "next" in text and day_name in text:
                    # "Next Monday" means the upcoming occurrence of that weekday
                    # If today is that day, go to next week
                    if days_ahead == 0:
                        days_ahead = 7
                    elif days_ahead < 0:
                        days_ahead += 7
                # Check for "this" modifier
                elif "this" in text and day_name in text:
                    if days_ahead < 0:
                        days_ahead += 7
                else:
                    # Default behavior: find the next occurrence
                    if days_ahead < 0:
                        days_ahead += 7
                    # If today is that day, assume they mean today (days_ahead = 0)
                
                return (today + timedelta(days=days_ahead)).isoformat()

        # "in X days" pattern
        match = re.search(r"in\s+(\d+)\s+days?", text)
        if match:
            days = int(match.group(1))
            return (today + timedelta(days=days)).isoformat()

        # "end of the week" - typically Friday
        if "end of the week" in text or "end of week" in text:
            days_ahead = 4 - today.weekday()  # Friday
            if days_ahead < 0:
                days_ahead += 7
            return (today + timedelta(days=days_ahead)).isoformat()

        # "this weekend" - Saturday
        if "this weekend" in text or "weekend" in text:
            days_ahead = 5 - today.weekday()  # Saturday
            if days_ahead < 0:
                days_ahead += 7
            return (today + timedelta(days=days_ahead)).isoformat()

        # "next week" - same weekday next week
        if "next week" in text:
            return (today + timedelta(days=7)).isoformat()

        # "in X weeks" pattern
        match = re.search(r"in\s+(\d+)\s+weeks?", text)
        if match:
            weeks = int(match.group(1))
            return (today + timedelta(weeks=weeks)).isoformat()

        return None

    def _extract_time(self, text: str) -> str | None:
        """Extract time from text.
        
        Args:
            text: Input text
            
        Returns:
            Time in HH:MM format or None
        """
        # Explicit time patterns
        # Pattern: HH:MM AM/PM
        match = re.search(
            r"(\d{1,2}):(\d{2})\s*(am|pm|a\.m\.|p\.m\.)",
            text,
            re.IGNORECASE
        )
        if match:
            hour, minute, period = match.groups()
            hour = int(hour)
            minute = int(minute)
            
            if period.lower() in ["pm", "p.m."] and hour != 12:
                hour += 12
            elif period.lower() in ["am", "a.m."] and hour == 12:
                hour = 0
            
            return f"{hour:02d}:{minute:02d}"

        # Pattern: HH AM/PM (without minutes)
        match = re.search(
            r"(\d{1,2})\s*(am|pm|a\.m\.|p\.m\.)",
            text,
            re.IGNORECASE
        )
        if match:
            hour, period = match.groups()
            hour = int(hour)
            
            if period.lower() in ["pm", "p.m."] and hour != 12:
                hour += 12
            elif period.lower() in ["am", "a.m."] and hour == 12:
                hour = 0
            
            return f"{hour:02d}:00"

        # Pattern: HH:MM (24-hour format)
        match = re.search(r"(\d{1,2}):(\d{2})", text)
        if match:
            hour, minute = match.groups()
            return f"{int(hour):02d}:{int(minute):02d}"

        # Period-based time expressions
        if "morning" in text:
            return self.MORNING_START

        if "afternoon" in text:
            return self.AFTERNOON_START

        if "evening" in text:
            return self.EVENING_START

        if "night" in text:
            return self.NIGHT_START

        if "noon" in text or "lunch" in text:
            return "12:00"

        if "midnight" in text:
            return "00:00"

        # Relative time expressions
        match = re.search(r"in\s+(\d+)\s+hours?", text)
        if match:
            hours = int(match.group(1))
            new_time = self.reference_date + timedelta(hours=hours)
            return new_time.strftime("%H:%M")

        match = re.search(r"in\s+(\d+)\s+minutes?", text)
        if match:
            minutes = int(match.group(1))
            new_time = self.reference_date + timedelta(minutes=minutes)
            return new_time.strftime("%H:%M")

        return None

    def _extract_duration(self, text: str) -> int | None:
        """Extract duration from text.
        
        Args:
            text: Input text
            
        Returns:
            Duration in minutes or None
        """
        # Pattern: X hours
        match = re.search(r"(\d+(?:\.\d+)?)\s*hours?", text)
        if match:
            hours = float(match.group(1))
            return int(hours * 60)

        # Pattern: X minutes
        match = re.search(r"(\d+)\s*minutes?", text)
        if match:
            return int(match.group(1))

        # Pattern: X mins
        match = re.search(r"(\d+)\s*mins?", text)
        if match:
            return int(match.group(1))

        # Pattern: Xh Ym
        match = re.search(r"(\d+)h\s*(\d+)m?", text)
        if match:
            hours = int(match.group(1))
            minutes = int(match.group(2)) if match.group(2) else 0
            return hours * 60 + minutes

        # Common duration keywords
        if "hour" in text and "half" in text:
            return 90

        if "30 min" in text or "half hour" in text:
            return 30

        if "15 min" in text or "quarter hour" in text:
            return 15

        if "quick" in text:
            return 15

        if "lunch" in text:
            return 60

        if "meeting" in text:
            return 60

        if "standup" in text or "stand-up" in text:
            return 15

        if "call" in text:
            return 30

        return None

    def parse_date(self, text: str) -> str | None:
        """Parse just the date from text.
        
        Args:
            text: Natural language date expression
            
        Returns:
            Date in YYYY-MM-DD format or None
        """
        return self._extract_date(text.lower())

    def parse_time(self, text: str) -> str | None:
        """Parse just the time from text.
        
        Args:
            text: Natural language time expression
            
        Returns:
            Time in HH:MM format or None
        """
        return self._extract_time(text.lower())

    def parse_duration(self, text: str) -> int | None:
        """Parse just the duration from text.
        
        Args:
            text: Natural language duration expression
            
        Returns:
            Duration in minutes or None
        """
        return self._extract_duration(text.lower())

    def suggest_time_for_period(self, period: str) -> str:
        """Suggest a time for a given period.
        
        Args:
            period: Time period (morning, afternoon, evening)
            
        Returns:
            Suggested time in HH:MM format
        """
        period = period.lower()
        
        if "morning" in period:
            return self.MORNING_START
        elif "afternoon" in period:
            return self.AFTERNOON_START
        elif "evening" in period:
            return self.EVENING_START
        elif "night" in period:
            return self.NIGHT_START
        
        return self.MORNING_START


def parse_natural_time(
    text: str, reference_date: datetime | None = None
) -> ParsedTime:
    """Convenience function to parse natural language time.
    
    Args:
        text: Natural language time expression
        reference_date: Reference date for relative expressions
        
    Returns:
        ParsedTime with extracted information
    """
    parser = NaturalLanguageTimeParser(reference_date)
    return parser.parse(text)
