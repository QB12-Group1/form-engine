from typing import Any

from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import GoogleAuthSerializer, TokenResponseSerializer

UserModel = get_user_model()


class GoogleAuthView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=GoogleAuthSerializer,
        responses={200: TokenResponseSerializer},
        summary="Google OAuth Login",
        description="Submit a Google ID token to obtain JWT access and refresh tokens.",
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
