# groupapp.py
"""
Streamlit app for the academic services ticket system.

Modes:
- Student: take a ticket and check ticket status.
- Staff: call next ticket and see queue overview.
- Display: read-only screen showing queues for all services.

Run locally with:
    streamlit run groupapp.py
"""

import streamlit as st
from queue_system import create_default_system, get_current_time_info

# ----------- initial setup -----------

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


def minutes_to_time_str(total_minutes):
    return f"{total_minutes // 60:02d}:{total_minutes % 60:02d}"


def open_state_message(service, current_time_min, weekday):
    """
    Return (is_open, message) with explanation.
    """
    time_text = minutes_to_time_str(current_time_min)

    if service.is_open(current_time_min, weekday):
        msg = f"Services are currently **OPEN** for tickets. (Time now: {time_text})"
        return True, msg

    # reason for being closed
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


# Fixed list of service codes in the order you requested
SERVICE_CODES = ["AA", "AB", "B", "EA", "EB", "G"]


def get_service_display_label(code, service):
    """Example: 'AA - Academic Services Bachelor Students'."""
    return f"{code} - {service.description}"


def get_all_services_in_order():
    services = []
    labels = []
    for code in SERVICE_CODES:
        svc = queue_system.get_service(code)
        if svc is not None:
            services.append(svc)
            labels.append(get_service_display_label(code, svc))
    return services, labels


# ------------- STUDENT MODE -------------

if mode == "Student":
    st.header("Student – Take a Ticket")
    st.write("Select what you need from the list of services:")

    services_list, labels_list = get_all_services_in_order()

    service_label = st.selectbox(
        "Service",
        labels_list,
        key="student_service_select",
    )
    index = labels_list.index(service_label)
    service = services_list[index]

    current_time_min, weekday = get_current_time_info()
    is_open_now, status_message = open_state_message(
        service, current_time_min, weekday
    )

    if is_open_now:
        st.success(status_message)
    else:
        st.error(status_message)

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
                "Note: waiting time is an estimate based on the average "
                "service time and three staff members working in parallel."
            )

    # ---- Check my ticket ----

    st.markdown("---")
    st.header("Student – Check my ticket")
    st.write(
        "Select the service of your ticket and enter your ticket number "
        "(just the number, for example **1** for ticket **AA-001**)."
    )

    services_check, labels_check = get_all_services_in_order()

    service_label_check = st.selectbox(
        "Service of your ticket",
        labels_check,
        key="check_service_select",
    )
    idx_check = labels_check.index(service_label_check)
    service_check = services_check[idx_check]

    ticket_input = st.text_input(
        "Ticket number (only the digits, e.g. 1, 2, 3…)",
        key="ticket_check_input",
    )

    if st.button("Check ticket status"):
        if not ticket_input.strip():
            st.warning("Please enter a ticket number.")
        else:
            try:
                ticket_number = int(ticket_input)
            except ValueError:
                st.error("Ticket number must be a whole number, e.g. 1 or 2.")
            else:
                status, info = service_check.find_ticket_status(ticket_number)

                code = service_check.code
                label_example = f"{code}-{ticket_number:03d}"

                if status == "serving":
                    st.success(
                        f"✅ Ticket **{label_example}** is "
                        f"**being served now**."
                    )
                elif status == "waiting":
                    people_ahead, est_wait = info
                    st.info(
                        f"Ticket **{label_example}** is **waiting** in the queue.\n\n"
                        f"People ahead of you: **{people_ahead}**\n\n"
                        f"Estimated waiting time: **{est_wait} minutes**"
                    )
                elif status == "done":
                    st.info(
                        f"Ticket **{label_example}** has **already been served**."
                    )
                else:
                    st.error(
                        "Ticket not found in this service. "
                        "Please check that you selected the correct service "
                        "and entered the right number."
                    )

# ------------- STAFF MODE -------------

elif mode == "Staff":
    st.header("Staff – Call Next Ticket")

    services_list, labels_list = get_all_services_in_order()

    service_label = st.selectbox(
        "Service",
        labels_list,
        key="staff_service_select",
    )
    index = labels_list.index(service_label)
    service = services_list[index]

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

    # Queue overview
    st.markdown("---")
    st.subheader("Queue overview")

    total_tickets = sum(
        svc.people_waiting() for svc in queue_system.services.values()
    )
    st.write(f"Tickets in queue (all services): **{total_tickets or 'none'}**")

    services_with_queue = [
        f"{code} ({svc.people_waiting()} waiting)"
        for code, svc in queue_system.services.items()
        if svc.people_waiting() > 0
    ]
    if services_with_queue:
        st.write("Queues with waiting tickets: " + ", ".join(services_with_queue))
    else:
        st.write("All queues are empty at the moment.")

# ------------- DISPLAY MODE -------------

elif mode == "Display":
    st.header("Queue Display")

    current_time_min, weekday = get_current_time_info()
    time_text = minutes_to_time_str(current_time_min)
    st.caption(f"Current time: {time_text}")

    st.markdown("---")

    # Show all queues in fixed order
    for code in SERVICE_CODES:
        svc = queue_system.get_service(code)
        if svc is None:
            continue

        is_open_now, status_message = open_state_message(
            svc, current_time_min, weekday
        )

        st.subheader(get_service_display_label(code, svc))

        if is_open_now:
            st.success(status_message)
        else:
            st.error(status_message)

        if svc.current_ticket is not None:
            st.write(f"Now serving: **{svc.current_ticket.label()}**")
        else:
            st.write("No ticket is currently being served.")

        waiting = svc.people_waiting()
        st.write(f"People waiting in this queue: **{waiting}**")

        if waiting > 0:
            labels = [ticket.label() for ticket in svc.queue]
            st.write("Next tickets: " + ", ".join(labels))
        else:
            st.write("Next tickets: none")

        st.markdown("---")
