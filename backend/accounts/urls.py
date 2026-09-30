from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    # OTP Authentication
    path("otp/request/", views.RequestOTPView.as_view(), name="request-otp"),
    path("otp/verify/", views.VerifyOTPView.as_view(), name="verify-otp"),
    # OAuth / Social Login
    path("google/", views.GoogleAuthView.as_view(), name="google"),
    # JWT Token Lifecycle
    path("token/refresh/", views.RefreshTokenView.as_view(), name="token-refresh"),
    path(
        "token/blacklist/",
        views.BlacklistTokenView.as_view(),
        name="token-blacklist",
    ),
    # Current User Profile
    path("me/", views.UserProfileView.as_view(), name="me"),
]
