from datetime import date, time, datetime
from django.conf import settings
from django.utils import timezone
from rest_framework import serializers
from courts.models import Court
from .models import Booking


OPEN_HOUR = getattr(settings, "BOOKING_OPEN_HOUR", 6)
CLOSE_HOUR = getattr(settings, "BOOKING_CLOSE_HOUR", 21)  # last slot starts at 20:00


class AvailabilitySerializer(serializers.ModelSerializer):
    """
    Shape returned by GET /api/bookings/availability/?date=YYYY-MM-DD

      { "id": 12, "court": 2, "start_time": "08:00", "is_mine": true }
    """
    is_mine = serializers.SerializerMethodField()
    court = serializers.IntegerField(source="court_id")
    start_time = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = ["id", "court", "start_time", "is_mine"]

    def get_is_mine(self, obj):
        request = self.context.get("request")
        return request is not None and obj.user_id == request.user.id

    def get_start_time(self, obj):
        return obj.start_time.strftime("%H:%M")


class CreateBookingSerializer(serializers.Serializer):
    """
    Shape sent by POST /api/bookings/

      { "court": 2, "date": "2026-11-16", "start_time": "08:00" }
    """
    court = serializers.IntegerField()
    date = serializers.DateField()
    start_time = serializers.RegexField(r"^\d{2}:00$", max_length=5)

    def validate_court(self, value):
        try:
            return Court.objects.get(pk=value)
        except Court.DoesNotExist:
            raise serializers.ValidationError("Court not found.")

    def validate(self, data):
        user = self.context["request"].user
        court: Court = data["court"]
        booking_date: date = data["date"]
        hour = int(data["start_time"][:2])

        # --- VIP court check ---
        if court.is_vip:
            is_manager = user.role == "OPERATIONS_MANAGER"
            if not is_manager and not user.is_vip:
                raise serializers.ValidationError(
                    "Court 1 is reserved for VIP members and operations staff."
                )

        # --- Opening hours check ---
        if not (OPEN_HOUR <= hour < CLOSE_HOUR):
            raise serializers.ValidationError(
                f"Bookings are only available between {OPEN_HOUR:02d}:00 and {CLOSE_HOUR:02d}:00."
            )

        # --- Past slot check ---
        slot_start = datetime.combine(booking_date, time(hour, 0))
        # Make timezone-aware if USE_TZ is on
        if settings.USE_TZ:
            slot_start = timezone.make_aware(slot_start)
        if slot_start <= timezone.now():
            raise serializers.ValidationError("You cannot book a slot that is in the past.")

        # --- Double booking check ---
        if Booking.objects.filter(
            court=court,
            date=booking_date,
            start_time=time(hour, 0),
            status=Booking.CONFIRMED,
        ).exists():
            raise serializers.ValidationError(
                "That slot is already taken. Please choose another time."
            )

        return data


class ManagerBookingSerializer(serializers.ModelSerializer):
    """
    Full booking record for the manager dashboard.

    Shape the frontend expects:
      { id, customer, court, date, hour, status, reason?, note? }
    """
    customer = serializers.CharField(source="user.full_name")
    court = serializers.IntegerField(source="court_id")
    hour = serializers.IntegerField(source="start_time.hour")
    reason = serializers.CharField(source="cancel_reason", allow_blank=True)
    note = serializers.CharField(source="cancel_note", allow_blank=True)
    date = serializers.DateField(format="%Y-%m-%d")

    class Meta:
        model = Booking
        fields = ["id", "customer", "court", "date", "hour", "status", "reason", "note"]


class ManagerCancelSerializer(serializers.Serializer):
    """Body sent by manager when cancelling: { reason, note? }"""
    reason = serializers.ChoiceField(choices=Booking.REASON_CHOICES)
    note = serializers.CharField(max_length=200, allow_blank=True, required=False, default="")

    def validate(self, data):
        booking = self.context["booking"]
        if booking.status == Booking.CANCELLED:
            raise serializers.ValidationError("This booking is already cancelled.")
        return data


class ManagerCreateBookingSerializer(serializers.Serializer):
    """
    Body for manager creating a booking on behalf of a customer:
      { customer_id, court, date, start_time }
    """
    customer_id = serializers.IntegerField()
    court = serializers.IntegerField()
    date = serializers.DateField()
    start_time = serializers.RegexField(r"^\d{2}:00$", max_length=5)

    def validate_court(self, value):
        try:
            return Court.objects.get(pk=value)
        except Court.DoesNotExist:
            raise serializers.ValidationError("Court not found.")

    def validate_customer_id(self, value):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            return User.objects.get(pk=value, role__in=["CUSTOMER", "COACH"])
        except User.DoesNotExist:
            raise serializers.ValidationError("Customer not found.")

    def validate(self, data):
        court: Court = data["court"]
        booking_date: date = data["date"]
        hour = int(data["start_time"][:2])

        if not (OPEN_HOUR <= hour < CLOSE_HOUR):
            raise serializers.ValidationError(
                f"Bookings are only available between {OPEN_HOUR:02d}:00 and {CLOSE_HOUR:02d}:00."
            )

        if Booking.objects.filter(
            court=court,
            date=booking_date,
            start_time=time(hour, 0),
            status=Booking.CONFIRMED,
        ).exists():
            raise serializers.ValidationError("That slot is already taken.")

        return data
