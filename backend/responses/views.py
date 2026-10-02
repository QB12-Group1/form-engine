from django.utils import timezone
from drf_spectacular.utils import (
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
    inline_serializer,
)
from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.mixins import CreateModelMixin, RetrieveModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from .models import ResponseSession
from .serializers import AnswerSerializer, ResponseSessionSerializer

NOT_FOUND = "Response session not found."


@extend_schema_view(
    create=extend_schema(
        summary="Start Response Session",
        description="Starts a new response session for a survey.",
        tags=["Response Sessions"],
        request=ResponseSessionSerializer,
        responses={
            status.HTTP_201_CREATED: OpenApiResponse(
                response=ResponseSessionSerializer,
                description="Response session created successfully.",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Invalid response session data."
            ),
        },
    ),
    retrieve=extend_schema(
        summary="Get Response Session",
        description="Retrieves response session details.",
        tags=["Response Sessions"],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=ResponseSessionSerializer,
                description="Response session retrieved successfully.",
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(description=NOT_FOUND),
        },
    ),
)
class ResponseSessionViewSet(CreateModelMixin, RetrieveModelMixin, GenericViewSet):
    queryset = ResponseSession.objects.all()
    serializer_class = ResponseSessionSerializer
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Complete Response Session",
        description="Marks a response session as completed.",
        tags=["Response Sessions"],
        request=None,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=inline_serializer(
                    name="CompleteResponseSessionResponse",
                    fields={
                        "id": serializers.IntegerField(),
                        "is_completed": serializers.BooleanField(),
                        "submitted_at": serializers.DateTimeField(),
                        "updated_at": serializers.DateTimeField(),
                    },
                ),
                description="Response session marked as completed.",
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(description=NOT_FOUND),
        },
    )
    @action(detail=True, methods=["PATCH"])
    def complete(self, request: Request, pk: str | None = None) -> Response:
        session = self.get_object()
        session.is_completed = True
        session.submitted_at = timezone.now()
        session.save(update_fields=["is_completed", "submitted_at", "updated_at"])
        return Response(
            {
                "id": session.id,
                "is_completed": session.is_completed,
                "submitted_at": session.submitted_at,
                "updated_at": session.updated_at,
            }
        )

    @extend_schema(
        methods=["GET"],
        summary="List Session Answers",
        description=("Retrieves all answers submitted within a response session."),
        tags=["Response Sessions"],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=AnswerSerializer(many=True),
                description="Answers retrieved successfully.",
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(description=NOT_FOUND),
        },
    )
    @extend_schema(
        methods=["POST"],
        summary="Submit Session Answer",
        description=("Submits an answer for a question within a response session. "),
        tags=["Response Sessions"],
        request=AnswerSerializer,
        responses={
            status.HTTP_201_CREATED: OpenApiResponse(
                response=AnswerSerializer,
                description="Answer submitted successfully.",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description=(
                    "Invalid answer data, or the response session is already completed."
                )
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(description=NOT_FOUND),
        },
    )
    @action(detail=True, methods=["GET", "POST"])
    def answers(self, request: Request, pk: str | None = None) -> Response:
        session = self.get_object()
        if request.method == "GET":
            return Response(AnswerSerializer(session.answers.all(), many=True).data)

        serializer = AnswerSerializer(data=request.data, context={"session": session})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        serializer.save(
            respondent_ip=self.request.META.get("REMOTE_ADDR", ""),
            user_agent=self.request.META.get("HTTP_USER_AGENT", ""),
        )
