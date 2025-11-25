# queue_system.py
"""
Queue system for academic services.

Queues (sub-services):
AA - Academic Services Bachelor Students
AB - Academic Services Masters Students
B  - Treasury
EA - International Mobility Incoming Students
EB - International Mobility Outgoing Students
G  - Student Recruitment & Scholarships

All queues:
- open Monday, Wednesday and Friday
- from 10:00 to 13:00
- assume 3 staff members working in parallel
"""

from datetime import datetime


def time_to_minutes(time_str):
    """Convert 'HH:MM' string to minutes since midnight."""
    hours, minutes = time_str.split(":")
    return int(hours) * 60 + int(minutes)


def get_current_time_info():
    """
    Returns:
        current_minutes: minutes since midnight
        weekday: 0 = Monday, ..., 6 = Sunday
    """
    now = datetime.now()
    current_minutes = now.hour * 60 + now.minute
    weekday = now.weekday()
    return current_minutes, weekday


class Ticket:
    """Represents a single ticket."""

    def __init__(self, service_code, number, time_taken_minutes):
        self.service_code = service_code  # e.g. "AA"
        self.number = number              # sequential integer
        self.time_taken_minutes = time_taken_minutes
        self.status = "waiting"           # "waiting", "serving", "done"

    def label(self):
        """
        Ticket label shown to the user.
        Example: "AA-001" or "B-003".
        """
        return f"{self.service_code}-{self.number:03d}"


class Service:
    """Represents one queue (e.g. 'AA' or 'EB')."""

    def __init__(
        self,
        code,
        description,
        avg_service_time_min,
        avg_staff_count,
        opening_time="10:00",
        closing_time="13:00",
        allowed_weekdays=None,
    ):
        self.code = code
        self.description = description
        self.avg_service_time_min = avg_service_time_min
        self.avg_staff_count = avg_staff_count

        # schedule
        self.opening_time_min = time_to_minutes(opening_time)
        self.closing_time_min = time_to_minutes(closing_time)

        # default: Monday–Friday
        if allowed_weekdays is None:
            self.allowed_weekdays = [0, 1, 2, 3, 4]
        else:
            self.allowed_weekdays = allowed_weekdays

        # queue state
        self.next_ticket_number = 1
        self.queue = []          # waiting tickets
        self.current_ticket = None
        self.served_tickets = [] # finished tickets

    # ---------- open / waiting-time helpers ----------

    def is_open(self, current_time_min, weekday):
        """Check if service is open for tickets at given time."""
        if weekday not in self.allowed_weekdays:
            return False
        if current_time_min < self.opening_time_min:
            return False
        if current_time_min >= self.closing_time_min:
            return False
        return True

    def people_waiting(self):
        return len(self.queue)

    def _estimate_waiting_from_position(self, people_ahead):
        """
        Estimate waiting time given the number of people ahead in the queue.

        We assume several counters working in parallel (avg_staff_count).
        If there are fewer people ahead than counters, wait = 0.
        """
        staff = self.avg_staff_count if self.avg_staff_count > 0 else 1

        if people_ahead < staff:
            return 0

        # After first round of people go to the available counters
        effective_ahead = people_ahead - staff + 1
        estimated = int((effective_ahead / staff) * self.avg_service_time_min)
        return estimated

    def estimate_waiting_time_for_new_ticket(self):
        people_ahead = self.people_waiting()
        estimated = self._estimate_waiting_from_position(people_ahead)
        return people_ahead, estimated

    # ---------- queue operations ----------

    def take_ticket(self, current_time_min):
        """Create a new ticket in this queue."""
        ticket = Ticket(self.code, self.next_ticket_number, current_time_min)
        self.queue.append(ticket)
        self.next_ticket_number += 1
        return ticket

    def call_next(self):
        """
        Finish current ticket (if any) and call the next one.
        """
        if self.current_ticket is not None:
            self.current_ticket.status = "done"
            self.served_tickets.append(self.current_ticket)

        if not self.queue:
            self.current_ticket = None
            return None

        next_ticket = self.queue.pop(0)
        next_ticket.status = "serving"
        self.current_ticket = next_ticket
        return next_ticket

    # ---------- ticket lookup (within this service) ----------

    def find_ticket_status(self, number):
        """
        Find ticket by number *within this service*.

        Returns (status, info):
          - "serving", None
          - "waiting", (people_ahead, estimated_wait)
          - "done", None
          - "not_found", None
        """
        # being served now
        if self.current_ticket and self.current_ticket.number == number:
            return "serving", None

        # waiting in this queue
        for idx, ticket in enumerate(self.queue):
            if ticket.number == number:
                people_ahead = idx
                est_wait = self._estimate_waiting_from_position(people_ahead)
                return "waiting", (people_ahead, est_wait)

        # already done
        for ticket in self.served_tickets:
            if ticket.number == number:
                return "done", None

        return "not_found", None


class QueueSystem:
    """Holds all sub-services (AA, AB, B, EA, EB, G)."""

    def __init__(self):
        self.services = {}  # code -> Service

    def add_service(self, service):
        self.services[service.code] = service

    def get_service(self, code):
        return self.services.get(code)

    def get_service_codes(self):
        return list(self.services.keys())


def create_default_system():
    """
    Create all queues with correct codes and descriptions.

    All are open on Monday, Wednesday and Friday, 10:00–13:00.
    We assume 3 staff members for each queue.
    """
    system = QueueSystem()
    mwf_only = [0, 2, 4]  # Monday, Wednesday, Friday

    # A - Academic Services
    aa = Service(
        code="AA",
        description="Academic Services Bachelor Students",
        avg_service_time_min=10,
        avg_staff_count=3,
        opening_time="10:00",
        closing_time="13:00",
        allowed_weekdays=mwf_only,
    )

    ab = Service(
        code="AB",
        description="Academic Services Masters Students",
        avg_service_time_min=10,
        avg_staff_count=3,
        opening_time="10:00",
        closing_time="13:00",
        allowed_weekdays=mwf_only,
    )

    # B - Treasury
    b = Service(
        code="B",
        description="Treasury",
        avg_service_time_min=8,
        avg_staff_count=3,
        opening_time="10:00",
        closing_time="13:00",
        allowed_weekdays=mwf_only,
    )

    # E - International Mobility Students
    ea = Service(
        code="EA",
        description="International Mobility Incoming Students",
        avg_service_time_min=12,
        avg_staff_count=3,
        opening_time="10:00",
        closing_time="13:00",
        allowed_weekdays=mwf_only,
    )

    eb = Service(
        code="EB",
        description="International Mobility Outgoing Students",
        avg_service_time_min=12,
        avg_staff_count=3,
        opening_time="10:00",
        closing_time="13:00",
        allowed_weekdays=mwf_only,
    )

    # G - Student Recruitment & Scholarships
    g = Service(
        code="G",
        description="Student Recruitment & Scholarships",
        avg_service_time_min=9,
        avg_staff_count=3,
        opening_time="10:00",
        closing_time="13:00",
        allowed_weekdays=mwf_only,
    )

    for svc in (aa, ab, b, ea, eb, g):
        system.add_service(svc)

    return system

