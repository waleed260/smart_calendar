#!/usr/bin/env python3
"""Test script for SmartCalendar core functionality."""

import os
import tempfile
from datetime import datetime

from smart_calendar.database import CalendarDatabase
from smart_calendar.service import CalendarService
from smart_calendar.time_parser import NaturalLanguageTimeParser
from smart_calendar.models import CalendarEvent


def test_database():
    """Test database operations."""
    print("Testing Database Operations...")
    
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    try:
        db = CalendarDatabase(db_path)
        
        # Create event
        event_id = db.create_event(
            title="Team Meeting",
            date="2026-03-07",
            start_time="10:00",
            end_time="11:00",
            duration_minutes=60,
            description="Weekly team sync",
            participants="Alice, Bob, Charlie",
            location="Conference Room A",
        )
        print(f"  ✓ Created event with ID: {event_id}")
        
        # Get event
        event = db.get_event(event_id)
        assert event is not None
        assert event["title"] == "Team Meeting"
        print(f"  ✓ Retrieved event: {event['title']}")
        
        # Check for conflicts (should be none)
        conflicts = db.check_conflict("2026-03-07", "14:00", "15:00")
        assert len(conflicts) == 0
        print("  ✓ No conflicts for non-overlapping time")
        
        # Check for conflicts (should find one)
        conflicts = db.check_conflict("2026-03-07", "10:30", "11:30")
        assert len(conflicts) == 1
        print(f"  ✓ Found conflict: {conflicts[0]['title']}")
        
        # Update event
        updated = db.update_event(event_id, title="Updated Team Meeting")
        assert updated
        event = db.get_event(event_id)
        assert event["title"] == "Updated Team Meeting"
        print("  ✓ Updated event title")
        
        # Get events by date
        events = db.get_events_by_date("2026-03-07")
        assert len(events) == 1
        print(f"  ✓ Retrieved {len(events)} event(s) for date")
        
        # Delete event
        deleted = db.delete_event(event_id)
        assert deleted
        event = db.get_event(event_id)
        assert event is None
        print("  ✓ Deleted event")
        
        # Test session management
        session_id = "test-session-123"
        db.get_or_create_session(session_id)
        db.add_message(session_id, "user", "Hello")
        db.add_message(session_id, "assistant", "Hi there!")
        
        messages = db.get_session_messages(session_id)
        assert len(messages) == 2
        print("  ✓ Session messages stored and retrieved")
        
        print("Database Tests: PASSED ✓\n")
        
    finally:
        os.unlink(db_path)


def test_time_parser():
    """Test natural language time parsing."""
    print("Testing Time Parser...")
    
    parser = NaturalLanguageTimeParser(
        reference_date=datetime(2026, 3, 6, 12, 0)  # Friday
    )
    
    # Test date parsing
    # Reference date is Friday March 6, 2026
    tests = [
        ("today", "2026-03-06"),
        ("tomorrow", "2026-03-07"),
        ("next Monday", "2026-03-09"),  # From Friday, next Monday is 3 days away
        ("this Friday", "2026-03-06"),
        ("next week", "2026-03-13"),
    ]
    
    for text, expected in tests:
        result = parser.parse_date(text)
        assert result == expected, f"Failed for '{text}': got {result}, expected {expected}"
        print(f"  ✓ '{text}' -> {result}")
    
    # Test time parsing
    time_tests = [
        ("9 AM", "09:00"),
        ("2 PM", "14:00"),
        ("2:30 PM", "14:30"),
        ("morning", "09:00"),
        ("afternoon", "13:00"),
        ("evening", "18:00"),
    ]
    
    for text, expected in time_tests:
        result = parser.parse_time(text)
        assert result == expected, f"Failed for '{text}': got {result}, expected {expected}"
        print(f"  ✓ '{text}' -> {result}")
    
    # Test duration parsing
    duration_tests = [
        ("1 hour", 60),
        ("30 minutes", 30),
        ("2 hours", 120),
        ("1h 30m", 90),
    ]
    
    for text, expected in duration_tests:
        result = parser.parse_duration(text)
        assert result == expected, f"Failed for '{text}': got {result}, expected {expected}"
        print(f"  ✓ '{text}' -> {result} minutes")
    
    print("Time Parser Tests: PASSED ✓\n")


def test_calendar_service():
    """Test calendar service operations."""
    print("Testing Calendar Service...")
    
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    try:
        db = CalendarDatabase(db_path)
        service = CalendarService(db)
        
        # Create event
        success, event, message = service.create_event(
            title="Project Review",
            date="2026-03-07",
            start_time="14:00",
            duration_minutes=60,
            description="Review project progress",
            participants=["Alice", "Bob"],
            location="Room 101",
        )
        assert success
        assert isinstance(event, CalendarEvent)
        print(f"  ✓ Created event: {event.title}")
        
        # Try to create conflicting event
        success, result, message = service.create_event(
            title="Conflicting Meeting",
            date="2026-03-07",
            start_time="14:30",
            duration_minutes=30,
        )
        assert not success
        print(f"  ✓ Detected conflict: {message}")
        
        # Get schedule for date
        schedule = service.get_events_for_date("2026-03-07")
        assert len(schedule.events) == 1
        print(f"  ✓ Retrieved schedule with {len(schedule.events)} event(s)")
        
        # Find available slots
        slots = service.find_available_slots("2026-03-07", duration_minutes=30, max_days=3)
        assert len(slots) > 0
        print(f"  ✓ Found {len(slots)} available slot(s)")
        
        # Reschedule event
        success, event, message = service.reschedule_event(
            event_id=1,
            new_date="2026-03-08",
            new_start_time="10:00",
        )
        assert success
        print(f"  ✓ Rescheduled event to {event.date}")
        
        # Cancel event
        success, event, message = service.cancel_event(1)
        assert success
        print(f"  ✓ Cancelled event: {message}")
        
        print("Calendar Service Tests: PASSED ✓\n")
        
    finally:
        os.unlink(db_path)


def main():
    """Run all tests."""
    print("=" * 50)
    print("SmartCalendar Test Suite")
    print("=" * 50)
    print()
    
    test_database()
    test_time_parser()
    test_calendar_service()
    
    print("=" * 50)
    print("All Tests Passed! ✓")
    print("=" * 50)


if __name__ == "__main__":
    main()
