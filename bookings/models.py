"""
Booking model.

A booking occupies one hour on one court (e.g. Court 2, 2026-11-16, 08:00–09:00).
Cancellation is a soft-delete: status changes to CANCELLED, record is kept for audit.
"""
from django.conf import settings
from django.db import models
from courts.models import Court


class Booking(models.Model):
    CONFIRMED = "Confirmed"
    CANCELLED = "Cancelled"
    STATUS_CHOICES = [(CONFIRMED, "Confirmed"), (CANCELLED, "Cancelled")]

    # Cancellation reasons (kept in sync with BookingsPage.jsx REASONS)
    REASON_MAINTENANCE = "maintenance"
    REASON_SCHEDULE = "schedule_change"
    REASON_CUSTOMER = "customer_request"
    REASON_OTHER = "other"
    REASON_CHOICES = [
        (REASON_MAINTENANCE, "Maintenance"),
        (REASON_SCHEDULE, "Schedule change"),
        (REASON_CUSTOMER, "Customer request"),
        (REASON_OTHER, "Other"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bookings",
    )
    court = models.ForeignKey(Court, on_delete=models.PROTECT, related_name="bookings")
    date = models.DateField()
    start_time = models.TimeField()     # always XX:00:00
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=CONFIRMED)
    # Manager-initiated cancellation fields
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="cancellations_made",
    )
    cancel_reason = models.CharField(max_length=30, choices=REASON_CHOICES, blank=True)
    cancel_note = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["date", "start_time"]
        # Prevent double-booking: at most one CONFIRMED booking per court/date/hour
        constraints = [
            models.UniqueConstraint(
                fields=["court", "date", "start_time"],
                condition=models.Q(status="Confirmed"),
                name="unique_confirmed_booking",
            )
        ]

    def __str__(self):
        return f"{self.user.full_name} | {self.court} | {self.date} {self.start_time}"

    @property
    def hour(self):
        return self.start_time.hour
