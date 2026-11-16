from django.urls import path
from .views import (
    AvailabilityView,
    CancelBookingView,
    CreateBookingView,
    ManagerBookingListCreateView,
    ManagerCancelBookingView,
    ManagerCoachListCreateView,
    ManagerCoachToggleView,
    ManagerCustomerListView,
    ManagerToggleVipView,
)

urlpatterns = [
    # --- Customer-facing ---
    path("availability/", AvailabilityView.as_view(), name="booking-availability"),
    path("", CreateBookingView.as_view(), name="booking-create"),
    path("<int:pk>/cancel/", CancelBookingView.as_view(), name="booking-cancel"),

    # --- Manager-facing ---
    path("manager/", ManagerBookingListCreateView.as_view(), name="manager-booking-list"),
    path("manager/<int:pk>/cancel/", ManagerCancelBookingView.as_view(), name="manager-booking-cancel"),
    path("manager/customers/", ManagerCustomerListView.as_view(), name="manager-customers"),
    path("manager/customers/<int:pk>/vip/", ManagerToggleVipView.as_view(), name="manager-toggle-vip"),
    path("manager/coaches/", ManagerCoachListCreateView.as_view(), name="manager-coaches"),
    path("manager/coaches/<int:pk>/toggle/", ManagerCoachToggleView.as_view(), name="manager-coach-toggle"),
]
