from django.contrib import admin
from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("user", "court", "date", "start_time", "status", "cancel_reason", "created_at")
    list_filter = ("status", "court", "date")
    search_fields = ("user__full_name", "user__email")
    raw_id_fields = ("user", "cancelled_by")
    date_hierarchy = "date"
