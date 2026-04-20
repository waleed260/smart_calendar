# SmartCalendar

<div align="center">

**An Intelligent AI-Powered Calendar Assistant*



</div>

---

## Overview

SmartCalendar is an intelligent conversational AI assistant that revolutionizes how you manage your schedule. Built on the **Python**, it understands natural language, detects scheduling conflicts, and provides smart recommendations to optimize your time.

Instead of wrestling with complex calendar interfaces, simply tell SmartCalendar what you need in plain English—whether it's "schedule a team meeting tomorrow morning" or "find time for a 30-minute call next week."

---

## ✨ Key Features

### 🗣️ Natural Language Understanding
- Understands expressions like "tomorrow morning," "next Monday," "in 2 hours"
- Parses dates, times, and durations from conversational input
- Supports multiple date/time formats (12-hour, 24-hour, relative)

### 🤖 AI-Powered Intelligence
- Built on Python  with function calling
- Context-aware conversations with persistent session history
- Proactive scheduling suggestions and conflict resolution

### 📅 Comprehensive Calendar Management
- **Create Events** — Schedule meetings with titles, participants, locations
- **Check Availability** — Find free slots for specific durations
- **Detect Conflicts** — Automatic conflict detection with alternative suggestions
- **Reschedule Events** — Move meetings with one command
- **Cancel Events** — Quick deletion with confirmation
- **Schedule Summaries** — Daily and weekly overviews

### 🧠 Smart Scheduling
- Suggests optimal meeting times (prefers mid-morning and mid-afternoon)
- Recommends breaks between meetings
- Warns about overloaded days
- Identifies focus time blocks for deep work

### 💾 Persistent Storage
- SQLite database for events and conversation history
- Session persistence across restarts
- Automatic session ID management

---

## 🚀 Quick Start

### Prerequisites

- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) package manager (recommended)
- OpenAI API key

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd smart_calendar

# Install dependencies with uv
uv sync

# Or with pip
pip install -e .
```

### Configuration

Set your OpenAI API key:

```bash
export OPENAI_API_KEY='sk-...'
```

### Usage

**Interactive Mode:**
```bash
uv run smart-calendar
```

**Single Command:**
```bash
uv run smart-calendar -c "Schedule a team meeting tomorrow at 2 PM"
```

**With Custom Options:**
```bash
uv run smart-calendar --model gpt-4o --db ./my_calendar.db
```

---

## 📖 Usage Examples

### Creating Events

```
📅  You: Schedule a team meeting tomorrow at 2 PM for 1 hour

🤖  SmartCalendar: Event Scheduled Successfully

Title: Team Meeting
Date: Saturday, March 07, 2026
Start Time: 02:00 PM
Duration: 1 hour
Participants: None
Location: Not specified
```

```
📅  You: Add a lunch meeting next Monday at noon with Alice and Bob at Cafe Central

🤖  SmartCalendar: Event Scheduled Successfully

Title: Lunch Meeting
Date: Monday, March 09, 2026
Start Time: 12:00 PM
Duration: 1 hour
Participants: Alice, Bob
Location: Cafe Central
```

### Viewing Schedule

```
📅  You: What's my schedule for today?

🤖  SmartCalendar: Schedule for Friday, March 06, 2026:

1. Team Standup — 09:00 AM (15 min)
2. Product Review — 01:30 PM (60 min)

Free Time:
  09:15 AM – 01:30 PM
  02:30 PM – 05:00 PM
```

```
📅  You: Show my upcoming events

🤖  SmartCalendar: Here are your upcoming events:

1. Team Meeting — Saturday, March 07 at 02:00 PM
2. Lunch Meeting — Monday, March 09 at 12:00 PM
3. Project Review — Tuesday, March 10 at 10:00 AM
```

### Managing Events

```
📅  You: Reschedule my 2 PM meeting to 4 PM

🤖  SmartCalendar: Event 'Team Meeting' rescheduled successfully.

Title: Team Meeting
Date: Saturday, March 07, 2026
Start Time: 04:00 PM
Duration: 1 hour
```

```
📅  You: Cancel my 3 PM meeting

🤖  SmartCalendar: Event 'Team Meeting' has been cancelled.
```

### Checking Availability

```
📅  You: When am I free tomorrow?

🤖  SmartCalendar: Available slots for Saturday, March 07:

• 09:00 AM – 12:00 PM (3 hours)
• 01:00 PM – 05:00 PM (4 hours)
```

```
📅  You: Suggest times for a 1-hour meeting

🤖  SmartCalendar: Optimal meeting suggestions:

Option 1: Monday, March 09: 10:00 AM – 11:00 AM
Option 2: Monday, March 09: 02:00 PM – 03:00 PM
Option 3: Tuesday, March 10: 10:00 AM – 11:00 AM
```

### Conflict Resolution

```
📅  You: Schedule a call tomorrow at 2 PM

🤖  SmartCalendar: Time Conflict Detected!

The following events conflict with your requested time:
• Team Meeting (02:00 PM)

Here are available alternatives:

Option 1: Saturday, March 07: 09:00 AM – 12:00 PM
Option 2: Saturday, March 07: 03:00 PM – 05:00 PM
Option 3: Sunday, March 08: 09:00 AM – 05:00 PM
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     SmartCalendar Agent                      │
│                   (OpenAI Agents SDK)                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐   │
│  │   Create    │ │   Check     │ │    Reschedule       │   │
│  │   Event     │ │ Availability│ │      Event          │   │
│  └─────────────┘ └─────────────┘ └─────────────────────┘   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐   │
│  │   Cancel    │ │   Get       │ │    Suggest          │   │
│  │   Event     │ │  Schedule   │ │      Times          │   │
│  └─────────────┘ └─────────────┘ └─────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Calendar Service                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  • Event CRUD Operations                             │   │
│  │  • Conflict Detection                                │   │
│  │  • Free Slot Calculation                             │   │
│  │  • Smart Scheduling Suggestions                      │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Natural Language Parser                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  • Date Extraction (today, tomorrow, next Monday)    │   │
│  │  • Time Extraction (9 AM, 14:30, morning)            │   │
│  │  • Duration Extraction (1 hour, 30 mins)             │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   SQLite Database Layer                      │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐   │
│  │   Events    │ │  Sessions   │ │     Messages        │   │
│  │   Table     │ │   Table     │ │     Table           │   │
│  └─────────────┘ └─────────────┘ └─────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
smart_calendar/
├── src/smart_calendar/
│   ├── __init__.py          # Package exports and version
│   ├── main.py              # CLI entry point with argument parsing
│   ├── agent.py             # SmartCalendar Agent (OpenAI Agents SDK)
│   ├── database.py          # SQLite database layer with connection pooling
│   ├── service.py           # Calendar business logic and operations
│   ├── session.py           # Session and conversation history management
│   ├── models.py            # Data models (Event, TimeSlot, Schedule, etc.)
│   └── time_parser.py       # Natural language time expression parser
├── tests/
│   └── test_core.py         # Core functionality tests
├── pyproject.toml           # Project configuration and dependencies
└── README.md                # This file
```

---

## 🔧 API Reference

### SmartCalendarAgent

The main agent class that integrates all components.

```python
from smart_calendar import SmartCalendarAgent

# Initialize agent
agent = SmartCalendarAgent(
    session_id="my-session",  # Optional: persist conversations
    model="gpt-4o-mini",       # OpenAI model to use
)

# Run synchronously
response = agent.run_sync("Schedule a meeting tomorrow at 10 AM")
print(response)

# Run asynchronously
response = await agent.run("Schedule a meeting tomorrow at 10 AM")
```

### CalendarService

Business logic layer for calendar operations.

```python
from smart_calendar import CalendarDatabase, CalendarService

db = CalendarDatabase()
service = CalendarService(db)

# Create event
success, event, message = service.create_event(
    title="Team Meeting",
    date="2026-03-07",
    start_time="14:00",
    duration_minutes=60,
    participants=["Alice", "Bob"],
    location="Conference Room A",
)

# Check availability
slots = service.check_availability("2026-03-07", duration_minutes=30)

# Get schedule
schedule = service.get_events_for_date("2026-03-07")
print(schedule.to_display_string())
```

### NaturalLanguageTimeParser

Parse natural language time expressions.

```python
from smart_calendar import NaturalLanguageTimeParser

parser = NaturalLanguageTimeParser()

# Parse date
date = parser.parse_date("next Monday")  # "2026-03-09"

# Parse time
time = parser.parse_time("2:30 PM")  # "14:30"

# Parse duration
duration = parser.parse_duration("1 hour 30 minutes")  # 90

# Full parse
result = parser.parse("tomorrow morning for 30 minutes")
# ParsedTime(date="2026-03-07", time="09:00", duration_minutes=30, ...)
```

---

## 🧪 Running Tests

```bash
# Run the test suite
uv run python tests/test_core.py
```

The test suite covers:
- Database operations (CRUD, conflicts, sessions)
- Natural language time parsing
- Calendar service operations

---

## 📋 Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--session SESSION` | Session ID for conversation history | Auto-generated |
| `--model MODEL` | OpenAI model to use | `gpt-4o-mini` |
| `--db PATH` | Path to SQLite database | `~/.smart_calendar.db` |
| `-c, --command CMD` | Run single command and exit | Interactive mode |

---

## 🕐 Supported Time Expressions

### Dates
- **Relative**: today, tomorrow, yesterday, next week
- **Days**: Monday, Tuesday, next Friday, this Sunday
- **Explicit**: 2026-03-15, 03/15/2026, March 15 2026
- **Special**: end of the week, this weekend

### Times
- **12-hour**: 9 AM, 2:30 PM, 11:45 am
- **24-hour**: 09:00, 14:30, 23:00
- **Periods**: morning (9 AM), afternoon (1 PM), evening (6 PM), night (8 PM)
- **Relative**: in 2 hours, in 30 minutes

### Durations
- **Explicit**: 1 hour, 30 minutes, 1h 30m
- **Implicit**: meeting (60 min), call (30 min), standup (15 min), lunch (60 min)

---

## 🗄️ Database Schema

### Events Table
```sql
CREATE TABLE events (
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
);
```

### Sessions Table
```sql
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT UNIQUE NOT NULL,
    created_at TEXT NOT NULL,
    last_active TEXT NOT NULL
);
```

### Messages Table
```sql
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);
```

---

## 🔐 Security Considerations

- API keys are read from environment variables only (never stored)
- SQLite database is stored in user's home directory with default permissions
- Session IDs are UUIDs to prevent guessing
- No sensitive data is logged

---
## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [python-dateutil](https://dateutil.readthedocs.io/) — Date manipulation utilities
- [uv](https://github.com/astral-sh/uv) — Fast Python package management

---

<div align="center">

**SmartCalendar** — Making calendar management effortless and intelligent.


</div>
# smart_calendar



