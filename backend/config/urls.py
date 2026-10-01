from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

from workspaces.views import WorkspaceViewSet


def health_check(_: object) -> JsonResponse:
    return JsonResponse({"status": "ok"})


router = DefaultRouter()
router.register(r"workspaces", WorkspaceViewSet, basename="workspace")

urlpatterns = [
    # System & Operations
    path("admin/", admin.site.urls),
    path("healthz/", health_check, name="health-check"),
    # API Documentation (Swagger)
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    # API Endpoints
    path("api/auth/", include("accounts.urls")),
    path("api/", include(router.urls)),
]
