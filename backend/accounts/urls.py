from django.urls import path

from .views import GoogleAuthView

app_name = "accounts"

urlpatterns = [
    path("google/", GoogleAuthView.as_view(), name="google-auth"),
]
