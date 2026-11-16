from django.urls import path
from .views import MarkAllReadView, MarkReadView, NotificationListView

urlpatterns = [
    path("", NotificationListView.as_view(), name="notification-list"),
    path("<int:pk>/read/", MarkReadView.as_view(), name="notification-read"),
    path("mark-all-read/", MarkAllReadView.as_view(), name="notification-mark-all"),
]
