from datetime import datetime


def time_to_minutes(time_str):
    hours, minutes = time_str.split(":")
    return int(hours) * 60 + int(minutes)


def get_current_time_info():
    now = datetime.now()
    current_minutes = now.hour * 60 + now.minute
    weekday = now.weekday()
    return current_minutes, weekday


class Ticket:
    def __init__(self, service_name, number, time_taken_minutes):
        self.service_name = service_name
        self.number = number
        self.time_taken_minutes = time_taken_minutes
        self.status = "waiting"

    def label(self):
        return f"{self.service_name}-{self.number}"


class Service:
    def __init__(
        self,
        name,
        description,
        avg_service_time_min,
        avg_staff_count,
        opening_time="10:00",
        closing_time="13:00",
        allowed_weekdays=None,
    ):
        self.name = name
        self.description = description
        self.avg_service_time_min = avg_service_time_min
        self.avg_staff_count = avg_staff_count

        self.opening_time_min = time_to_minutes(opening_time)
        self.closing_time_min = time_to_minutes(closing_time)

        if allowed_weekdays is None:
            self.allowed_weekdays = [0, 1, 2, 3, 4]
        else:
            self.allowed_weekdays = allowed_weekdays

        self.next_ticket_number = 1
        self.queue = []
        self.current_ticket = None
        self.served_tickets = []

    # ----------------- open / wait time -----------------

    def is_open(self, current_time_min, weekday):
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
        Wait time assuming several counters in parallel.
        If there are fewer people ahead than counters, wait = 0.
        """
        staff = self.avg_staff_count if self.avg_staff_count > 0 else 1
        if people_ahead < staff:
            return 0
        effective_ahead = people_ahead - staff + 1
        estimated = int((effective_ahead / staff) * self.avg_service_time_min)
        return estimated

    def estimate_waiting_time_for_new_ticket(self):
        people_ahead = self.people_waiting()
        estimated = self._estimate_waiting_from_position(people_ahead)
        return people_ahead, estimated

    # ----------------- queue operations -----------------

    def take_ticket(self, current_time_min):
        ticket = Ticket(self.name, self.next_ticket_number, current_time_min)
        self.queue.append(ticket)
        self.next_ticket_number += 1
        return ticket

    def call_next(self):
        # finish current ticket
        if self.current_ticket is not None:
            self.current_ticket.status = "done"
            self.served_tickets.append(self.current_ticket)

        # get next one
        if not self.queue:
            self.current_ticket = None
            return None

        next_ticket = self.queue.pop(0)
        next_ticket.status = "serving"
        self.current_ticket = next_ticket
        return next_ticket

    # ----------------- ticket lookup -----------------

    def find_ticket_status(self, number):
        # being served now
        if self.current_ticket and self.current_ticket.number == number:
            return "serving", None

        # waiting
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
    def __init__(self):
        self.services = {}

    def add_service(self, service):
        self.services[service.name] = service

    def get_service(self, service_name):
        return self.services.get(service_name)

    def get_service_names(self):
        return list(self.services.keys())


def create_default_system():
    """
    Four services, all open Mon/Wed/Fri 10:00–13:00.
    We assume 3 staff members per service.
    """
    system = QueueSystem()
    mwf_only = [0, 2, 4]  # Monday, Wednesday, Friday

    masters = Service(
        name="Masters",
        description="Support for master's students (enrolment, documents, etc.).",
        avg_service_time_min=10,
        avg_staff_count=3,
        opening_time="10:00",
        closing_time="13:00",
        allowed_weekdays=mwf_only,
    )

    undergraduate = Service(
        name="Undergraduate",
        description="Support for undergraduate students.",
        avg_service_time_min=8,
        avg_staff_count=3,
        opening_time="10:00",
        closing_time="13:00",
        allowed_weekdays=mwf_only,
    )

    it_support = Service(
        name="IT Support",
        description="Help with accounts, passwords, Wi-Fi and other IT problems.",
        avg_service_time_min=7,
        avg_staff_count=3,
        opening_time="10:00",
        closing_time="13:00",
        allowed_weekdays=mwf_only,
    )

    others = Service(
        name="Others",
        description="Any other academic or administrative questions.",
        avg_service_time_min=12,
        avg_staff_count=3,
        opening_time="10:00",
        closing_time="13:00",
        allowed_weekdays=mwf_only,
    )

    system.add_service(masters)
    system.add_service(undergraduate)
    system.add_service(it_support)
    system.add_service(others)

    return system
