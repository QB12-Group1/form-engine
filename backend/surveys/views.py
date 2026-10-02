from django.db.models import Q, QuerySet
from drf_spectacular.utils import (
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
    inline_serializer,
)
from rest_framework import mixins, serializers, status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer
from rest_framework.viewsets import GenericViewSet

from workspaces.models import Workspace

from .models import Survey
from .permissions import HasWorkspaceAccess
from .serializers import SurveySerializer

AUTH_ERROR = "Authentication credentials were not provided or are invalid."


@extend_schema_view(
    list=extend_schema(
        summary="List Workspace Surveys",
        description="Lists surveys in a workspace the authenticated user can access.",
        tags=["Workspace Surveys"],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=SurveySerializer(many=True),
                description="Workspace surveys retrieved successfully.",
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(description=AUTH_ERROR),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="Workspace not found or is not accessible."
            ),
        },
    ),
    create=extend_schema(
        summary="Create Workspace Survey",
        description=(
            "Creates a survey in a workspace the authenticated user can access. "
            "The survey is created as a draft."
        ),
        tags=["Workspace Surveys"],
        request=SurveySerializer,
        responses={
            status.HTTP_201_CREATED: OpenApiResponse(
                response=SurveySerializer,
                description="Survey created successfully.",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Invalid survey data."
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(description=AUTH_ERROR),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="Workspace not found or is not accessible."
            ),
        },
    ),
)
class WorkspaceSurveyViewset(
    mixins.ListModelMixin, mixins.CreateModelMixin, GenericViewSet
):
    serializer_class = SurveySerializer

    def get_workspace(self) -> Workspace:
        user = self.request.user
        workspace_id = self.kwargs.get("workspace_pk")
        queryset = Workspace.objects.filter(Q(owner=user) | Q(members=user)).distinct()
        return get_object_or_404(queryset, id=workspace_id)

    def get_queryset(self) -> QuerySet[Survey]:
        if getattr(self, "swagger_fake_view", False):
            return Survey.objects.none()

        workspace = self.get_workspace()
        return Survey.objects.select_related("workspace").filter(workspace=workspace)

    def perform_create(self, serializer: BaseSerializer) -> None:
        workspace = self.get_workspace()
        serializer.save(workspace=workspace)


@extend_schema_view(
    retrieve=extend_schema(
        summary="Get Survey",
        description="Retrieves a survey the authenticated user can access.",
        tags=["Surveys"],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=SurveySerializer,
                description="Survey retrieved successfully.",
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(description=AUTH_ERROR),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="Survey not found or is not accessible."
            ),
        },
    ),
    update=extend_schema(
        summary="Update Survey",
        description="Replaces the information for a survey the user can access.",
        tags=["Surveys"],
        request=SurveySerializer,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=SurveySerializer,
                description="Survey updated successfully.",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Invalid survey data."
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(description=AUTH_ERROR),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="Survey not found or is not accessible."
            ),
        },
    ),
    partial_update=extend_schema(
        summary="Partially Update Survey",
        description="Updates one or more fields of a survey the user can access.",
        tags=["Surveys"],
        request=SurveySerializer,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=SurveySerializer,
                description="Survey updated successfully.",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Invalid survey data."
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(description=AUTH_ERROR),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="Survey not found or is not accessible."
            ),
        },
    ),
    destroy=extend_schema(
        summary="Delete Survey",
        description="Deletes a survey the authenticated user can access.",
        tags=["Surveys"],
        responses={
            status.HTTP_204_NO_CONTENT: OpenApiResponse(
                description="Survey deleted successfully."
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(description=AUTH_ERROR),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="Survey not found or is not accessible."
            ),
        },
    ),
)
class SurveyViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet,
):
    serializer_class = SurveySerializer
    permission_classes = [IsAuthenticated, HasWorkspaceAccess]

    def get_queryset(self) -> QuerySet[Survey]:
        if getattr(self, "swagger_fake_view", False):
            return Survey.objects.none()

        user = self.request.user
        membership_filter = Q(workspace__owner=user) | Q(workspace__members=user)
        surveys = Survey.objects.select_related("workspace").filter(membership_filter)
        return surveys.distinct()

    @extend_schema(
        summary="Publish Survey",
        description="Changes a survey's status to published.",
        tags=["Surveys"],
        request=None,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=inline_serializer(
                    name="PublishSurveyResponse",
                    fields={"status": serializers.CharField()},
                ),
                description="Survey published successfully.",
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(description=AUTH_ERROR),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="Survey not found or is not accessible."
            ),
        },
    )
    @action(detail=True, methods=["POST"])
    def publish(self, request: Request, pk: str | None = None) -> Response:
        survey: Survey = self.get_object()
        survey.status = Survey.SurveyStatus.PUBLISHED
        survey.save(update_fields=["status", "updated_at"])
        return Response({"status": survey.status}, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Close Survey",
        description="Changes a survey's status to closed.",
        tags=["Surveys"],
        request=None,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=inline_serializer(
                    name="CloseSurveyResponse",
                    fields={"status": serializers.CharField()},
                ),
                description="Survey closed successfully.",
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(description=AUTH_ERROR),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="Survey not found or is not accessible."
            ),
        },
    )
    @action(detail=True, methods=["POST"])
    def close(self, request: Request, pk: str | None = None) -> Response:
        survey: Survey = self.get_object()
        survey.status = Survey.SurveyStatus.CLOSED
        survey.save(update_fields=["status", "updated_at"])
        return Response({"status": survey.status}, status=status.HTTP_200_OK)
