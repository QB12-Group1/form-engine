from django.db import transaction
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

from .models import Question, Survey
from .permissions import HasSurveyAccess, HasWorkspaceAccess
from .serializers import QuestionReorderSerializer, QuestionSerializer, SurveySerializer

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


@extend_schema_view(
    list=extend_schema(
        summary="List Survey Questions",
        description="Lists questions in a survey the authenticated user can access.",
        tags=["Survey Questions"],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=QuestionSerializer(many=True),
                description="Survey questions retrieved successfully.",
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(description=AUTH_ERROR),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="Survey not found or is not accessible."
            ),
        },
    ),
    create=extend_schema(
        summary="Create Survey Question",
        description=(
            "Creates a question in a survey the authenticated user can access."
        ),
        tags=["Survey Questions"],
        request=QuestionSerializer,
        responses={
            status.HTTP_201_CREATED: OpenApiResponse(
                response=QuestionSerializer,
                description="Question created successfully.",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Invalid question data."
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(description=AUTH_ERROR),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="Survey not found or is not accessible."
            ),
        },
    ),
)
class SurveyQuestionViewset(
    mixins.ListModelMixin, mixins.CreateModelMixin, GenericViewSet
):
    serializer_class = QuestionSerializer

    def get_survey(self) -> Survey:
        user = self.request.user
        survey_id = self.kwargs.get("survey_pk")
        queryset = (
            Survey.objects.select_related("workspace")
            .filter(Q(workspace__owner=user) | Q(workspace__members=user))
            .distinct()
        )
        return get_object_or_404(queryset, id=survey_id)

    def get_queryset(self) -> QuerySet[Question]:
        if getattr(self, "swagger_fake_view", False):
            return Question.objects.none()

        survey = self.get_survey()
        return Question.objects.select_related("survey").filter(survey=survey)

    def perform_create(self, serializer: BaseSerializer) -> None:
        survey = self.get_survey()
        serializer.save(survey=survey)

    @extend_schema(
        summary="Reorder Survey Questions",
        description=(
            "Reorders every question in a survey. Supply each question ID exactly "
            "once in its desired order."
        ),
        tags=["Survey Questions"],
        request=QuestionReorderSerializer,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=inline_serializer(
                    name="ReorderSurveyQuestionsResponse",
                    fields={"status": serializers.CharField(default="ok")},
                ),
                description="Survey questions reordered successfully.",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description=(
                    "Question IDs must be unique and include every question in the "
                    "survey."
                )
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(description=AUTH_ERROR),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="Survey not found or is not accessible."
            ),
        },
    )
    @action(
        detail=False,
        methods=["POST"],
        url_path="reorder",
        serializer_class=QuestionReorderSerializer,
    )
    def reorder(self, request: Request, survey_pk: str | None = None) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ordered_ids: list[int] = serializer.validated_data["question_ids"]

        survey = self.get_survey()
        questions = list(survey.questions.all())  # pyright: ignore[reportAttributeAccessIssue]

        questions_len = len(questions)
        given_ids_len = len(ordered_ids)

        invalid_response = Response(
            {
                "detail": "Invalid question IDs provided. "
                "Ensure all IDs belong to this survey and are unique."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
        if questions_len != given_ids_len or given_ids_len != len(set(ordered_ids)):
            return invalid_response

        order_map = {
            question_id: index for index, question_id in enumerate(ordered_ids)
        }
        for question in questions:
            try:
                question.order = order_map[question.id]
            except KeyError:
                return invalid_response

        with transaction.atomic():
            Question.objects.bulk_update(questions, ["order"])

        return Response({"status": "ok"}, status=status.HTTP_200_OK)


@extend_schema_view(
    retrieve=extend_schema(
        summary="Get Question",
        description="Retrieves a question the authenticated user can access.",
        tags=["Questions"],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=QuestionSerializer,
                description="Question retrieved successfully.",
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(description=AUTH_ERROR),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="Question not found or is not accessible."
            ),
        },
    ),
    update=extend_schema(
        summary="Update Question",
        description="Replaces the information for a question the user can access.",
        tags=["Questions"],
        request=QuestionSerializer,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=QuestionSerializer,
                description="Question updated successfully.",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Invalid question data."
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(description=AUTH_ERROR),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="Question not found or is not accessible."
            ),
        },
    ),
    partial_update=extend_schema(
        summary="Partially Update Question",
        description="Updates one or more fields of a question the user can access.",
        tags=["Questions"],
        request=QuestionSerializer,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=QuestionSerializer,
                description="Question updated successfully.",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Invalid question data."
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(description=AUTH_ERROR),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="Question not found or is not accessible."
            ),
        },
    ),
    destroy=extend_schema(
        summary="Delete Question",
        description="Deletes a question the authenticated user can access.",
        tags=["Questions"],
        responses={
            status.HTTP_204_NO_CONTENT: OpenApiResponse(
                description="Question deleted successfully."
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(description=AUTH_ERROR),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="Question not found or is not accessible."
            ),
        },
    ),
)
class QuestionViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet,
):
    serializer_class = QuestionSerializer
    permission_classes = [IsAuthenticated, HasSurveyAccess]

    def get_queryset(self) -> QuerySet[Question]:
        if getattr(self, "swagger_fake_view", False):
            return Question.objects.none()

        user = self.request.user
        membership_filter = Q(survey__workspace__owner=user) | Q(
            survey__workspace__members=user
        )
        return (
            Question.objects.select_related("survey__workspace")
            .filter(membership_filter)
            .distinct()
        )
