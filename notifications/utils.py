"""
Helpers called by other apps to create notifications and send emails.
"""
from django.core.mail import send_mail
from django.conf import settings


def send_notification(user, notif_type: str, data: dict):
    """
    Create an in-app notification and send a matching email.
    Import is deferred to avoid circular imports at module load time.
    """
    from .models import Notification

    Notification.objects.create(user=user, type=notif_type, data=data)
    _send_email(user, notif_type, data)


# ---------------------------------------------------------------------------
# Email helpers
# ---------------------------------------------------------------------------

def _send_email(user, notif_type: str, data: dict):
    subject, body = _build_email(user, notif_type, data)
    if not subject:
        return
    try:
        send_mail(
            subject,
            body,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=True,
        )
    except Exception:
        pass


def _build_email(user, notif_type: str, data: dict):
    name = user.full_name
    court = data.get("court", "")
    date = data.get("date", "")
    hour = data.get("hour")
    time_str = f"{hour:02d}:00–{hour + 1:02d}:00" if hour is not None else ""
    reason = data.get("reason", "")

    if notif_type == "booking_confirmed":
        subject = "Your court booking is confirmed – Nyarutarama Tennis Club"
        body = (
            f"Hi {name},\n\n"
            f"Your booking for Court {court} on {date} at {time_str} is confirmed.\n\n"
            "See you on the court!\nNyarutarama Tennis Club"
        )
    elif notif_type == "booking_cancelled":
        subject = "Your booking has been cancelled – Nyarutarama Tennis Club"
        body = (
            f"Hi {name},\n\n"
            f"Your booking for Court {court} on {date} at {time_str} has been cancelled.\n\n"
            "You can make a new booking anytime.\nNyarutarama Tennis Club"
        )
    elif notif_type == "booking_cancelled_by_staff":
        reason_display = {
            "maintenance": "scheduled maintenance",
            "schedule_change": "a schedule change",
            "customer_request": "your request",
            "other": "operational reasons",
        }.get(reason, reason)
        subject = "Your booking was cancelled by the club – Nyarutarama Tennis Club"
        body = (
            f"Hi {name},\n\n"
            f"We had to cancel your booking for Court {court} on {date} at {time_str} "
            f"due to {reason_display}.\n\n"
            "We apologise for the inconvenience. Please contact us to rebook.\n"
            "Nyarutarama Tennis Club"
        )
    elif notif_type == "vip_assigned":
        subject = "VIP access granted – Nyarutarama Tennis Club"
        body = (
            f"Hi {name},\n\n"
            "Great news! You have been granted VIP membership and can now book the VIP court (Court 1) directly.\n\n"
            "Nyarutarama Tennis Club"
        )
    elif notif_type == "vip_removed":
        subject = "VIP access removed – Nyarutarama Tennis Club"
        body = (
            f"Hi {name},\n\n"
            "Your VIP membership has been updated and you no longer have direct access to Court 1.\n\n"
            "Nyarutarama Tennis Club"
        )
    else:
        return None, None

    return subject, body
