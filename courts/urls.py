from django.urls import path
from .views import CourtListView

urlpatterns = [
    path("courts/", CourtListView.as_view(), name="court-list"),
]
