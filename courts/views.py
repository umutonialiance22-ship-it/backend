from rest_framework.permissions import AllowAny
from rest_framework.generics import ListAPIView
from .models import Court
from .serializers import CourtSerializer


class CourtListView(ListAPIView):
    """GET /api/courts/  — public endpoint, used if the frontend ever fetches courts dynamically."""
    queryset = Court.objects.all().order_by("id")
    serializer_class = CourtSerializer
    permission_classes = [AllowAny]
