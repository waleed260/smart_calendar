"""SmartCalendar - Intelligent Calendar Management Agent.

Main entry point for the SmartCalendar application.
"""

import argparse
import os
import sys
import uuid
from typing import Optional

from .agent import SmartCalendarAgent
from .database import CalendarDatabase


def print_welcome():
    """Print welcome message."""
    print("""
╔══════════════════════════════════════════════════════════╗
║                    SmartCalendar                         ║
║         Your Intelligent Calendar Assistant              ║
╚══════════════════════════════════════════════════════════╝

I can help you:
  • Schedule new events and meetings
  • Check your calendar availability
  • Reschedule or cancel events
  • Get daily/weekly schedule summaries
  • Suggest optimal meeting times

Try commands like:
  "Schedule a team meeting tomorrow at 2 PM for 1 hour"
  "What's my schedule for today?"
  "Show me my upcoming events"
  "Find a time for a 30-minute call next week"
  "Cancel my 3 PM meeting"

Type 'quit' or 'exit' to end the session.
Type 'help' for more information.
""")


def print_help():
    """Print help information."""
    print("""
SmartCalendar Commands:
─────────────────────────────────────────────────────────────

Scheduling:
  • "Schedule [event] on [date] at [time]"
  • "Create a meeting tomorrow morning"
  • "Add [event] to my calendar for next Monday at 10 AM"

Viewing Schedule:
  • "What's my schedule for today?"
  • "Show me tomorrow's events"
  • "What events do I have this week?"
  • "Show upcoming events"

Managing Events:
  • "Reschedule [event] to [new time]"
  • "Move my 2 PM meeting to 4 PM"
  • "Cancel [event]"
  • "Delete the meeting on Friday"

Availability:
  • "When am I free tomorrow?"
  • "Check availability for next Monday"
  • "Suggest times for a 1-hour meeting"

Natural Language Support:
  • "tomorrow morning/afternoon/evening"
  • "next Monday/Tuesday/Wednesday..."
  • "this Friday", "this weekend"
  • "in 2 hours", "in 30 minutes"
  • "end of the week"

─────────────────────────────────────────────────────────────
""")


def get_session_id(session_file: str) -> str:
    """Get or create session ID from file.
    
    Args:
        session_file: Path to session ID file
        
    Returns:
        Session ID string
    """
    try:
        if os.path.exists(session_file):
            with open(session_file, "r") as f:
                return f.read().strip()
    except Exception:
        pass
    
    # Create new session ID
    session_id = str(uuid.uuid4())
    try:
        with open(session_file, "w") as f:
            f.write(session_id)
    except Exception:
        pass
    
    return session_id


def main():
    """Main entry point for SmartCalendar CLI."""
    parser = argparse.ArgumentParser(
        description="SmartCalendar - Intelligent Calendar Management"
    )
    parser.add_argument(
        "--session",
        type=str,
        default=None,
        help="Session ID (auto-generated if not provided)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gpt-4o-mini",
        help="OpenAI model to use (default: gpt-4o-mini)",
    )
    parser.add_argument(
        "--db",
        type=str,
        default=None,
        help="Path to SQLite database (default: ~/.smart_calendar.db)",
    )
    parser.add_argument(
        "--command",
        "-c",
        type=str,
        default=None,
        help="Run a single command and exit",
    )

    args = parser.parse_args()

    # Check for API key
    if not os.environ.get("OPENAI_API_KEY"):
        print(
            "Error: OPENAI_API_KEY environment variable is not set.\n"
            "Please set it with: export OPENAI_API_KEY='your-api-key'"
        )
        sys.exit(1)

    # Initialize database
    db = CalendarDatabase(args.db)

    # Get or create session ID
    session_file = os.path.join(
        os.path.expanduser("~"), ".smart_calendar_session"
    )
    session_id = args.session or get_session_id(session_file)

    # Create agent
    agent = SmartCalendarAgent(
        database=db,
        session_id=session_id,
        model=args.model,
    )

    # Run single command if provided
    if args.command:
        try:
            response = agent.run_sync(args.command)
            print(response)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
        return

    # Interactive mode
    print_welcome()

    while True:
        try:
            user_input = input("\n📅  You: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ["quit", "exit", "q"]:
                print("\nGoodbye! Have a productive day! 👋\n")
                break

            if user_input.lower() in ["help", "h", "?"]:
                print_help()
                continue

            # Run agent
            try:
                response = agent.run_sync(user_input)
                print(f"\n🤖  SmartCalendar: {response}")
            except Exception as e:
                print(f"\nError: {e}")

        except KeyboardInterrupt:
            print("\n\nGoodbye! Have a productive day! 👋\n")
            break
        except EOFError:
            print("\n\nGoodbye! Have a productive day! 👋\n")
            break


if __name__ == "__main__":
    main()
