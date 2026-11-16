"""
Notification model.

Types (must stay in sync with notificationService.js):
  booking_confirmed
  booking_cancelled
  booking_cancelled_by_staff
  vip_assigned
  vip_removed

The `data` field stores a JSON object whose shape varies by type:
  booking_* → { court, date, hour, reason? }
  vip_*     → {}
"""
from django.conf import settings
from django.db import models


class Notification(models.Model):
    TYPE_BOOKING_CONFIRMED = "booking_confirmed"
    TYPE_BOOKING_CANCELLED = "booking_cancelled"
    TYPE_CANCELLED_BY_STAFF = "booking_cancelled_by_staff"
    TYPE_VIP_ASSIGNED = "vip_assigned"
    TYPE_VIP_REMOVED = "vip_removed"

    TYPE_CHOICES = [
        (TYPE_BOOKING_CONFIRMED, "Booking confirmed"),
        (TYPE_BOOKING_CANCELLED, "Booking cancelled"),
        (TYPE_CANCELLED_BY_STAFF, "Booking cancelled by staff"),
        (TYPE_VIP_ASSIGNED, "VIP assigned"),
        (TYPE_VIP_REMOVED, "VIP removed"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    is_read = models.BooleanField(default=False)
    data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.full_name} | {self.type} | read={self.is_read}"
