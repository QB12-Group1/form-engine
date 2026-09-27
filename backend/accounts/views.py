from typing import Any

from django.contrib.auth import get_user_model
from drf_spectacular.utils import (
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
    inline_serializer,
)
from rest_framework import generics, serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import (
    GoogleAuthSerializer,
    RequestOTPSerializer,
    UserProfileSerializer,
    VerifyOTPSerializer,
)
from .services import OTPRateLimitError, OTPService

UserModel = get_user_model()


@extend_schema_view(
    get=extend_schema(
        summary="Get User Profile",
        description="Retrieves the authenticated user's profile.",
        tags=["User Profile"],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=UserProfileSerializer,
                description="Authenticated user's profile retrieved successfully.",
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description=(
                    "Authentication credentials were not provided or are invalid."
                )
            ),
        },
    ),
    put=extend_schema(
        summary="Update User Profile",
        description="Replaces the authenticated user's profile information.",
        tags=["User Profile"],
        request=UserProfileSerializer,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=UserProfileSerializer,
                description="User profile updated successfully.",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Invalid profile data."
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description=(
                    "Authentication credentials were not provided or are invalid."
                )
            ),
        },
    ),
    patch=extend_schema(
        summary="Partially Update User Profile",
        description="Updates one or more fields of the authenticated user's profile.",
        tags=["User Profile"],
        request=UserProfileSerializer,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=UserProfileSerializer,
                description="User profile updated successfully.",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Invalid profile data."
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description=(
                    "Authentication credentials were not provided or are invalid."
                )
            ),
        },
    ),
)
class UserProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get_object(self) -> UserModel:  # pyright: ignore[reportInvalidTypeForm]
        user = self.request.user
        self.check_object_permissions(self.request, user)
        return user


class RequestOTPView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Request OTP",
        description=(
            "Generates and sends a one-time password (OTP)"
            "to the specified email address."
        ),
        tags=["Authentication"],
        request=RequestOTPSerializer,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=inline_serializer(
                    name="RequestOTPSuccessResponse",
                    fields={
                        "detail": serializers.CharField(
                            default="OTP sent successfully."
                        )
                    },
                ),
                description="OTP successfully generated and sent.",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Invalid input data (e.g. malformed email)."
            ),
            status.HTTP_429_TOO_MANY_REQUESTS: OpenApiResponse(
                response=inline_serializer(
                    name="RequestOTPRateLimitResponse",
                    fields={
                        "detail": serializers.CharField(
                            default="Rate limit exceeded. Please try again later."
                        ),
                        "retry_after": serializers.IntegerField(
                            help_text="Cooldown time remaining in seconds",
                            default=60,
                        ),
                    },
                ),
                description=(
                    "Rate limit exceeded. Client must wait before requesting again."
                ),
            ),
        },
    )
    def post(self, request: Request) -> Response:
        serializer = RequestOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]

        try:
            OTPService.send(email)
        except OTPRateLimitError as e:
            return Response(
                data={
                    "detail": "Rate limit exceeded. Please try again later.",
                    "retry_after": e.retry_after,
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        return Response({"detail": "OTP sent successfully."}, status=status.HTTP_200_OK)


class VerifyOTPView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Verify OTP",
        description=(
            "Verifies a one-time password (OTP) for the specified email address. "
            "Creates the user when needed and returns JWT access and refresh tokens."
        ),
        tags=["Authentication"],
        request=VerifyOTPSerializer,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=inline_serializer(
                    name="VerifyOTPSuccessResponse",
                    fields={
                        "access": serializers.CharField(help_text="JWT access token"),
                        "refresh": serializers.CharField(help_text="JWT refresh token"),
                        "email": serializers.EmailField(
                            help_text="Verified user's email address"
                        ),
                        "is_new": serializers.BooleanField(
                            help_text="Whether a new user account was created"
                        ),
                    },
                ),
                description="OTP successfully verified and JWT tokens returned.",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description=(
                    "Invalid input data or OTP verification failure "
                    "(invalid, expired, or exhausted code)."
                )
            ),
        },
    )
    def post(self, request: Request) -> Response:
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        raw_code = serializer.validated_data["code"]

        is_verified, message = OTPService.verify(email, raw_code)

        if not is_verified:
            return Response({"detail": message}, status=status.HTTP_400_BAD_REQUEST)

        user, created = UserModel.objects.get_or_create(email=email)

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "email": user.email,
                "is_new": created,
            },
            status=status.HTTP_200_OK,
        )


class GoogleAuthView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Google OAuth Login",
        description=(
            "Authenticates or registers a user via a Google ID token. "
            "Returns JWT access and refresh tokens along with the user's email."
        ),
        tags=["Authentication"],
        request=GoogleAuthSerializer,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=inline_serializer(
                    name="GoogleAuthSuccessResponse",
                    fields={
                        "access": serializers.CharField(help_text="JWT access token"),
                        "refresh": serializers.CharField(help_text="JWT refresh token"),
                        "email": serializers.EmailField(
                            help_text="User's verified email address"
                        ),
                    },
                ),
                description=(
                    "Successfully authenticated with Google.Returns JWT tokens."
                ),
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Invalid Google ID token or missing required fields."
            ),
        },
    )
    def post(self, request: Request) -> Response:
        serializer = GoogleAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        google_data: dict[str, Any] = serializer.validated_data["user_info"]

        user, _ = UserModel.objects.get_or_create(
            email=google_data["email"],
            defaults={
                "email": google_data["email"],
                "first_name": google_data["first_name"],
                "last_name": google_data["last_name"],
            },
        )

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "email": user.email,
            },
            status=status.HTTP_200_OK,
        )
