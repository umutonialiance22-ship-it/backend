"""
Booking views.

Customer-facing:
  GET  /api/bookings/availability/?date=YYYY-MM-DD
  POST /api/bookings/
  POST /api/bookings/{id}/cancel/

Manager-facing (OPERATIONS_MANAGER only):
  GET  /api/bookings/manager/
  POST /api/bookings/manager/
  POST /api/bookings/manager/{id}/cancel/
  GET  /api/bookings/manager/customers/
  POST /api/bookings/manager/customers/{id}/vip/
  GET  /api/bookings/manager/coaches/
  POST /api/bookings/manager/coaches/
  POST /api/bookings/manager/coaches/{id}/toggle/
"""
from datetime import date as date_type, time
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from notifications.utils import send_notification
from .models import Booking
from .permissions import IsManager
from .serializers import (
    AvailabilitySerializer,
    CreateBookingSerializer,
    ManagerBookingSerializer,
    ManagerCancelSerializer,
    ManagerCreateBookingSerializer,
)
from users.serializers import UserSummarySerializer

User = get_user_model()


# ---------------------------------------------------------------------------
# Customer endpoints
# ---------------------------------------------------------------------------

class AvailabilityView(APIView):
    """GET /api/bookings/availability/?date=YYYY-MM-DD"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        raw_date = request.query_params.get("date")
        if not raw_date:
            return Response({"detail": "date parameter is required."}, status=400)
        try:
            booking_date = date_type.fromisoformat(raw_date)
        except ValueError:
            return Response({"detail": "Invalid date format. Use YYYY-MM-DD."}, status=400)

        bookings = Booking.objects.filter(
            date=booking_date,
            status=Booking.CONFIRMED,
        ).select_related("user")

        serializer = AvailabilitySerializer(bookings, many=True, context={"request": request})
        return Response(serializer.data)


class CreateBookingView(APIView):
    """POST /api/bookings/"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreateBookingSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            # Flatten to a simple detail string the frontend can display
            errors = serializer.errors
            detail = next(iter(errors.values()))
            if isinstance(detail, list):
                detail = detail[0]
            return Response({"detail": str(detail)}, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        hour = int(data["start_time"][:2])
        booking = Booking.objects.create(
            user=request.user,
            court=data["court"],
            date=data["date"],
            start_time=time(hour, 0),
        )
        # Notify the customer
        send_notification(
            user=request.user,
            notif_type="booking_confirmed",
            data={"court": booking.court_id, "date": str(booking.date), "hour": hour},
        )
        return Response({"id": booking.id}, status=status.HTTP_201_CREATED)


class CancelBookingView(APIView):
    """POST /api/bookings/{id}/cancel/"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            booking = Booking.objects.get(pk=pk, user=request.user)
        except Booking.DoesNotExist:
            return Response({"detail": "Booking not found."}, status=status.HTTP_404_NOT_FOUND)

        if booking.status == Booking.CANCELLED:
            return Response({"detail": "Booking is already cancelled."}, status=status.HTTP_400_BAD_REQUEST)

        # Prevent cancelling past slots
        slot_dt = timezone.make_aware(
            timezone.datetime.combine(booking.date, booking.start_time)
        )
        if slot_dt <= timezone.now():
            return Response(
                {"detail": "You cannot cancel a slot that has already started."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        booking.status = Booking.CANCELLED
        booking.cancelled_by = request.user
        booking.cancel_reason = Booking.REASON_CUSTOMER
        booking.save()

        send_notification(
            user=request.user,
            notif_type="booking_cancelled",
            data={"court": booking.court_id, "date": str(booking.date), "hour": booking.hour},
        )
        return Response({"detail": "Booking cancelled."})


# ---------------------------------------------------------------------------
# Manager endpoints
# ---------------------------------------------------------------------------

class ManagerBookingListCreateView(APIView):
    """
    GET  /api/bookings/manager/           — full booking list (all users, all dates by default)
    POST /api/bookings/manager/           — create booking on behalf of a customer
    """
    permission_classes = [IsManager]

    def get(self, request):
        qs = Booking.objects.select_related("user", "court").order_by("-date", "start_time")
        # Optional filters
        d = request.query_params.get("date")
        if d:
            qs = qs.filter(date=d)
        court = request.query_params.get("court")
        if court:
            qs = qs.filter(court_id=court)
        s = request.query_params.get("status")
        if s:
            qs = qs.filter(status=s)
        return Response(ManagerBookingSerializer(qs, many=True).data)

    def post(self, request):
        serializer = ManagerCreateBookingSerializer(data=request.data)
        if not serializer.is_valid():
            detail = next(iter(serializer.errors.values()))
            if isinstance(detail, list):
                detail = detail[0]
            return Response({"detail": str(detail)}, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        hour = int(data["start_time"][:2])
        booking = Booking.objects.create(
            user=data["customer_id"],      # resolved User instance
            court=data["court"],
            date=data["date"],
            start_time=time(hour, 0),
            cancelled_by=None,
        )
        send_notification(
            user=data["customer_id"],
            notif_type="booking_confirmed",
            data={"court": booking.court_id, "date": str(booking.date), "hour": hour},
        )
        return Response(ManagerBookingSerializer(booking).data, status=status.HTTP_201_CREATED)


class ManagerCancelBookingView(APIView):
    """POST /api/bookings/manager/{id}/cancel/"""
    permission_classes = [IsManager]

    def post(self, request, pk):
        try:
            booking = Booking.objects.select_related("user").get(pk=pk)
        except Booking.DoesNotExist:
            return Response({"detail": "Booking not found."}, status=404)

        serializer = ManagerCancelSerializer(
            data=request.data, context={"booking": booking}
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        booking.status = Booking.CANCELLED
        booking.cancelled_by = request.user
        booking.cancel_reason = serializer.validated_data["reason"]
        booking.cancel_note = serializer.validated_data.get("note", "")
        booking.save()

        send_notification(
            user=booking.user,
            notif_type="booking_cancelled_by_staff",
            data={
                "court": booking.court_id,
                "date": str(booking.date),
                "hour": booking.hour,
                "reason": booking.cancel_reason,
            },
        )
        return Response(ManagerBookingSerializer(booking).data)


# ---------------------------------------------------------------------------
# Manager — customer management
# ---------------------------------------------------------------------------

class ManagerCustomerListView(APIView):
    """GET /api/bookings/manager/customers/"""
    permission_classes = [IsManager]

    def get(self, request):
        customers = User.objects.filter(role__in=[User.CUSTOMER, User.COACH]).order_by("full_name")
        return Response(UserSummarySerializer(customers, many=True).data)


class ManagerToggleVipView(APIView):
    """POST /api/bookings/manager/customers/{id}/vip/"""
    permission_classes = [IsManager]

    def post(self, request, pk):
        try:
            customer = User.objects.get(pk=pk, role=User.CUSTOMER)
        except User.DoesNotExist:
            return Response({"detail": "Customer not found."}, status=404)

        customer.is_vip = not customer.is_vip
        customer.save(update_fields=["is_vip"])

        notif_type = "vip_assigned" if customer.is_vip else "vip_removed"
        send_notification(user=customer, notif_type=notif_type, data={})

        return Response(UserSummarySerializer(customer).data)


# ---------------------------------------------------------------------------
# Manager — coach management
# ---------------------------------------------------------------------------

class ManagerCoachListCreateView(APIView):
    """
    GET  /api/bookings/manager/coaches/
    POST /api/bookings/manager/coaches/   — create a coach account (sends invitation email)
    """
    permission_classes = [IsManager]

    def get(self, request):
        coaches = User.objects.filter(role=User.COACH).order_by("full_name")
        return Response(_coach_data(coaches))

    def post(self, request):
        name = request.data.get("name", "").strip()
        email = request.data.get("email", "").strip().lower()
        phone = request.data.get("phone", "").strip()

        errors = {}
        if not name:
            errors["name"] = "Full name is required."
        if not email:
            errors["email"] = "Email is required."
        elif User.objects.filter(email=email).exists():
            errors["email"] = "A user with this email already exists."
        if errors:
            return Response(errors, status=400)

        # Create account with an unusable password; they set it via invitation
        coach = User.objects.create_user(
            email=email,
            full_name=name,
            phone=phone,
            password=None,
            role=User.COACH,
        )
        _send_coach_invitation(coach)
        return Response(_coach_row(coach), status=201)


class ManagerCoachToggleView(APIView):
    """POST /api/bookings/manager/coaches/{id}/toggle/"""
    permission_classes = [IsManager]

    def post(self, request, pk):
        try:
            coach = User.objects.get(pk=pk, role=User.COACH)
        except User.DoesNotExist:
            return Response({"detail": "Coach not found."}, status=404)

        coach.is_active = not coach.is_active
        coach.save(update_fields=["is_active"])
        return Response(_coach_row(coach))


def _coach_row(coach):
    if not coach.has_usable_password():
        coach_status = "Invited"
    elif coach.is_active:
        coach_status = "Active"
    else:
        coach_status = "Inactive"
    return {
        "id": coach.id,
        "name": coach.full_name,
        "email": coach.email,
        "phone": coach.phone,
        "status": coach_status,
    }


def _coach_data(coaches):
    return [_coach_row(c) for c in coaches]


def _send_coach_invitation(coach):
    """Send a password-setup invitation email to the new coach."""
    from django.core.mail import send_mail
    from django.conf import settings

    subject = "You've been invited to join Nyarutarama Tennis Club"
    body = (
        f"Hi {coach.full_name},\n\n"
        "The Operations Manager has created a coach account for you at Nyarutarama Tennis Club.\n"
        "Please contact the club to set up your password.\n\n"
        "Nyarutarama Tennis Club"
    )
    try:
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [coach.email], fail_silently=True)
    except Exception:
        pass  # don't block the response if email fails
