# tools.py
import logging
import sqlite3
import asyncio
from typing import Optional, List
from dataclasses import dataclass
from contextlib import contextmanager
from datetime import datetime
import requests
from livekit.agents import function_tool, RunContext

# ---------------------------
# Existing utility tools (unchanged)
# ---------------------------

@function_tool()
async def get_weather(context: RunContext, city: str) -> str:
    url = f"https://wttr.in/{city}?format=3"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        weather = response.text.strip()
        logging.info(f"Weather for {city}: {weather}")
        return weather
    except requests.RequestException as e:
        logging.error(f"Weather request failed for {city}: {e}")
        return f"Could not retrieve weather for {city}."

@function_tool()
async def get_datetime(context: "RunContext", query: str = "full") -> str:
    try:
        now = datetime.now()
        hour_24 = now.hour
        minute = now.minute
        hour_12 = hour_24 % 12 or 12
        am_pm = "AM" if hour_24 < 12 else "PM"

        if 5 <= hour_24 < 12:
            part_of_day = "morning"
        elif 12 <= hour_24 < 17:
            part_of_day = "afternoon"
        elif 17 <= hour_24 < 21:
            part_of_day = "evening"
        else:
            part_of_day = "night"

        time_str = f"{hour_12}:{minute:02d} {am_pm} ({part_of_day})"
        date_str = now.strftime("%B %d, %Y")
        day_str = now.strftime("%A")
        full_str = f"It’s {day_str}, {date_str} at {time_str}"

        if query == "time":
            response = f"The time is {time_str}"
        elif query == "date":
            response = f"Today is {date_str}"
        elif query == "day":
            response = f"Today is {day_str}"
        else:
            response = full_str

        logging.info(f"Datetime response for query='{query}': {response}")
        return response
    except Exception as e:
        logging.error(f"Failed to get datetime: {e}")
        return "Sorry, I couldn’t figure out the current date and time."

# ---------------------------
# Minimal DB driver for iPhone service centre
# ---------------------------

@dataclass
class ServiceTicket:
    serial: str
    model: str
    customer_name: str
    contact: str
    issue_description: str
    status: str
    received_at: str

class DatabaseDriver:

    def __init__(self, db_path: str = "service_db.sqlite"):
        self.db_path = db_path
        self._init_db()

    # Get connection to db using path
    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    # Initailization of database
    def _init_db(self):
        with self._get_connection() as conn:
            # middle-ware between sqdb and sql commands
            cursor = conn.cursor()
            # creating table if none exists
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                serial TEXT PRIMARY KEY,
                model TEXT NOT NULL,
                customer_name TEXT NOT NULL,
                contact TEXT NOT NULL,
                issue_description TEXT NOT NULL,
                status TEXT NOT NULL,
                received_at TEXT NOT NULL
            )
            """)
            conn.commit()

    def create_ticket(self,
                    serial: str,
                    model: str,
                    customer_name: str,
                    contact: str,
                    issue_description: str,
                    status: str = "received",
                    received_at: Optional[str] = None) -> ServiceTicket:
        received_at = received_at or datetime.utcnow().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO tickets (serial, model, customer_name, contact, issue_description, status, received_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (serial, model, customer_name, contact, issue_description, status, received_at),
            )
            conn.commit()
        return ServiceTicket(serial, model, customer_name, contact, issue_description, status, received_at)

    def get_ticket_by_serial(self, serial: str) -> Optional[ServiceTicket]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tickets WHERE serial = ?", (serial,))
            row = cursor.fetchone()
            if not row:
                return None
            return ServiceTicket(serial=row[0], model=row[1], customer_name=row[2], contact=row[3],
                                issue_description=row[4], status=row[5], received_at=row[6])

    def list_tickets(self) -> List[ServiceTicket]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tickets ORDER BY received_at DESC")
            rows = cursor.fetchall()
            return [ServiceTicket(serial=row[0], model=row[1], customer_name=row[2], contact=row[3],
                                issue_description=row[4], status=row[5], received_at=row[6]) for row in rows]

# single shared DB instance for the agent tools
# getting the instance of the above db
_db = DatabaseDriver()

# ---------------------------
# Exposed function_tools for agent use (async wrappers)
# Function defs for using in agent as tools
# ---------------------------

@function_tool()
async def create_ticket(context: RunContext,
                        serial: str,
                        model: str,
                        customer_name: str,
                        contact: str,
                        issue_description: str) -> str:
    # normalize & validate inputs
    def _norm(val: Optional[str]) -> str:
        return (val or "").strip()

    fields = {
        "serial": _norm(serial),
        "model": _norm(model),
        "customer_name": _norm(customer_name),
        "contact": _norm(contact),
        "issue_description": _norm(issue_description),
    }

    missing = [name for name, val in fields.items() if not val]
    if missing:
        return f"Missing required fields for creating a ticket: {', '.join(missing)}. Please provide them before I create the ticket."

    try:
        ticket = await asyncio.to_thread(
            _db.create_ticket,
            fields["serial"],
            fields["model"],
            fields["customer_name"],
            fields["contact"],
            fields["issue_description"],
        )
        logging.info("Created ticket %s for %s", ticket.serial, ticket.customer_name)
        return f"Ticket created: {ticket.serial} — {ticket.model} — status: {ticket.status}"
    except sqlite3.IntegrityError:
        logging.warning("Attempt to create duplicate serial: %s", fields["serial"])
        return f"A ticket with serial '{fields['serial']}' already exists."
    except Exception:
        logging.exception("Failed to create ticket due to an unexpected error")
        return "Failed to create ticket due to an internal error."
    
@function_tool()
async def get_ticket_by_serial_tool(context: RunContext, serial: str) -> str:
    # validation process
    if not serial or not str(serial).strip():
        return "Missing required field: serial. Please provide the serial number to fetch the ticket."
            
    # asynchronous operation to get the information from the db
    try:
        ticket = await asyncio.to_thread(_db.get_ticket_by_serial, serial.strip())
        date_only = datetime.fromisoformat(ticket.received_at).strftime("%Y-%m-%d")
        if not ticket:
            return f"No ticket found with serial '{serial.strip()}'."
        # Return compact, final result (avoids extra commentary)
        return (
            f"Serial: {ticket.serial}\n"
            f"Model: {ticket.model}\n"
            f"Customer: {ticket.customer_name}\n"
            f"Contact: {ticket.contact}\n"
            f"Issue: {ticket.issue_description}\n"
            f"Status: {ticket.status}\n"
            f"Received at: {date_only}"
        )
    except Exception as e:
        logging.exception("Failed to fetch ticket: %s", e)
        date_only = ticket.received_at  # fallback if parsing fails
        return "Failed to fetch ticket due to an internal error."


@function_tool()
async def list_tickets_tool(context: RunContext) -> str:
    # Function used to list the tickets 
    try:
        tickets = await asyncio.to_thread(_db.list_tickets)
        if not tickets:
            return "No tickets found."
        lines = []
        for t in tickets:
            lines.append(f"{t.serial} | {t.model} | {t.customer_name} | {t.status} | received: {t.received_at}")
        return "\n".join(lines)
    except Exception as e:
        logging.exception("Failed to list tickets: %s", e)
        return "Failed to list tickets due to an internal error."