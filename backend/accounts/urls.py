from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("otp/request/", views.RequestOTPView.as_view(), name="request-otp"),
    path("otp/verify/", views.VerifyOTPView.as_view(), name="verify-otp"),
    path("google/", views.GoogleAuthView.as_view(), name="google"),
]
