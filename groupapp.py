# groupapp.py
"""
Streamlit app for the academic services ticket system.

Interfaces:
- Student: take a ticket and check ticket status.
- Staff: call next ticket and see a queue overview.
- Display: read-only screen with queue information for every service.

To run:
    streamlit run groupapp.py
"""

import streamlit as st
from queue_system import create_default_system, get_current_time_info


# ----------------- initial setup -----------------

if "queue_system" not in st.session_state:
    st.session_state.queue_system = create_default_system()

queue_system = st.session_state.queue_system

st.title("Academic Services Ticket System")

st.info(
    "Support schedule: **In-person walk-ins – Monday, Wednesday and Friday "
    "– 10:00 am – 1:00 pm.**"
)

st.sidebar.header("Mode")
mode = st.sidebar.radio("Choose interface", ["Student", "Staff", "Display"])

service_names = queue_system.get_service_names()
if not service_names:
    st.error("No services configured.")
    st.stop()


def minutes_to_time_str(total_minutes: int) -> str:
    return f"{total_minutes // 60:02d}:{total_minutes % 60:02d}"


def open_state_message(service, current_time_min, weekday):
    """
    Return (is_open, message) with a human-friendly explanation
    of why the service is open or closed.
    """
    time_text = minutes_to_time_str(current_time_min)

    if service.is_open(current_time_min, weekday):
        msg = f"Services are currently **OPEN** for tickets. (Time now: {time_text})"
        return True, msg

    # Determine reason for being closed
    if weekday not in service.allowed_weekdays:
        reason = "today is not a scheduled support day."
    elif current_time_min < service.opening_time_min:
        reason = "they have not opened yet."
    elif current_time_min >= service.closing_time_min:
        reason = "they are already closed for today."
    else:
        reason = "they are temporarily unavailable."

    msg = (
        f"Services are currently **CLOSED** for tickets, because {reason} "
        f"(Time now: {time_text})."
    )
    return False, msg


# ----------------- STUDENT VIEW -----------------

if mode == "Student":
    st.header("Student – Take a Ticket")
    st.write("Select what you need from the list of services:")

    student_service_name = st.selectbox(
        "Service", service_names, key="student_service_select"
    )
    service = queue_system.get_service(student_service_name)

    current_time_min, weekday = get_current_time_info()
    is_open_now, status_message = open_state_message(
        service, current_time_min, weekday
    )

    # Green (success) if open, red (error) if closed
    if is_open_now:
        st.success(status_message)
    else:
        st.error(status_message)

    st.write(
        f"Opening hours for {service.name}: "
        f"Monday, Wednesday and Friday – "
        f"{minutes_to_time_str(service.opening_time_min)}–"
        f"{minutes_to_time_str(service.closing_time_min)}"
    )

    st.write("")

    if is_open_now:
        people_ahead, estimated_wait = service.estimate_waiting_time_for_new_ticket()
        st.write(f"People currently waiting in this queue: **{people_ahead}**")
        st.write(
            f"Estimated waiting time if you take a ticket now: "
            f"**{estimated_wait} minutes**"
        )

        if st.button("Take ticket"):
            ticket = service.take_ticket(current_time_min)
            st.success("Ticket created successfully!")
            st.write(f"**Your ticket:** {ticket.label()}")
            st.write(f"People ahead of you: **{people_ahead}**")
            st.write(f"Estimated waiting time: **{estimated_wait} minutes**")
            st.info(
                "The waiting time is an estimate based on average service time "
                "and the number of staff members (three counters working in "
                "parallel)."
            )
    else:
        st.warning("You cannot take a ticket because the service is closed.")

    # -------- Student – Check my ticket --------

    st.markdown("---")
    st.header("Student – Check my ticket")
    st.write("Enter your ticket number (e.g. 1, 2, 3…).")

    ticket_input = st.text_input("Ticket number", key="ticket_check_input")

    if st.button("Check ticket status"):
        if not ticket_input.strip():
            st.warning("Please enter a ticket number.")
        else:
            try:
                ticket_number = int(ticket_input)
            except ValueError:
                st.error("Ticket number must be a whole number, e.g. 1 or 2.")
            else:
                status, info = service.find_ticket_status(ticket_number)

                if status == "serving":
                    st.success(
                        f"✅ Ticket {service.name}-{ticket_number} is "
                        f"**being served now**."
                    )
                elif status == "waiting":
                    people_ahead, est_wait = info
                    st.info(
                        f"Ticket {service.name}-{ticket_number} is "
                        f"**waiting** in the queue.\n\n"
                        f"People ahead of you: **{people_ahead}**\n\n"
                        f"Estimated waiting time: **{est_wait} minutes**"
                    )
                elif status == "done":
                    st.info(
                        f"Ticket {service.name}-{ticket_number} has "
                        f"**already been served**."
                    )
                else:
                    st.error(
                        "Ticket not found. It may have been served already, "
                        "or it belongs to another service or day."
                    )

# ----------------- STAFF VIEW -----------------

elif mode == "Staff":
    st.header("Staff – Call Next Ticket")

    staff_service_name = st.selectbox(
        "Service", service_names, key="staff_service_select"
    )
    service = queue_system.get_service(staff_service_name)

    current_time_min, weekday = get_current_time_info()
    is_open_now, status_message = open_state_message(
        service, current_time_min, weekday
    )

    if is_open_now:
        st.success(status_message)
    else:
        st.error(status_message)

    st.write("")

    if service.current_ticket is not None:
        st.write(f"Current ticket: **{service.current_ticket.label()}**")
    else:
        st.write("No ticket is currently being served.")

    if st.button("Call next ticket"):
        next_ticket = service.call_next()
        if next_ticket is None:
            st.warning("No more tickets in the queue for this service.")
        else:
            st.success(f"Now serving: **{next_ticket.label()}**")

    # -------- Queue overview --------

    st.markdown("---")
    st.subheader("Queue overview")

    total_tickets = sum(
        s.people_waiting() for s in queue_system.services.values()
    )
    st.write(f"Tickets in queue: **{total_tickets or 'none'}**")

    services_with_queue = [
        sname for sname, s in queue_system.services.items() if s.people_waiting() > 0
    ]
    if services_with_queue:
        st.write("Their services: " + ", ".join(services_with_queue))
    else:
        st.write("Their services: none")

# ----------------- DISPLAY VIEW -----------------

elif mode == "Display":
    st.header("Queue Display")

    current_time_min, weekday = get_current_time_info()
    time_text = minutes_to_time_str(current_time_min)
    st.caption(f"Current time: {time_text}")

    st.markdown("---")

    # For each service, show open/closed, current ticket and queue length
    for service_name in service_names:
        service = queue_system.get_service(service_name)

        is_open_now, status_message = open_state_message(
            service, current_time_min, weekday
        )

        st.subheader(service.name)

        if is_open_now:
            st.success(status_message)
        else:
            st.error(status_message)

        if service.current_ticket is not None:
            st.write(f"Now serving: **{service.current_ticket.label()}**")
        else:
            st.write("No ticket is currently being served.")

        waiting = service.people_waiting()
        st.write(f"People waiting in this queue: **{waiting}**")

        if waiting > 0:
            labels = [ticket.label() for ticket in service.queue]
            st.write("Next tickets: " + ", ".join(labels))
        else:
            st.write("Next tickets: none")

        st.markdown("---")
