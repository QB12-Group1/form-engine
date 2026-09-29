import uuid

from django.db.models import Q, QuerySet
from drf_spectacular.utils import (
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
    inline_serializer,
)
from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer
from rest_framework.viewsets import ModelViewSet

from workspaces.permissions import IsWorkspaceOwner, IsWorkspaceOwnerOrMember

from .models import Workspace
from .serializers import (
    JoinWorkspaceSerializer,
    UserSummarySerializer,
    WorkspaceSerializer,
)

AUTH_ERROR = "Authentication credentials were not provided or are invalid."


@extend_schema_view(
    list=extend_schema(
        summary="List Workspaces",
        description="Lists workspaces owned by or shared with the authenticated user.",
        tags=["Workspaces"],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=WorkspaceSerializer(many=True),
                description="Workspaces retrieved successfully.",
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(description=AUTH_ERROR),
        },
    ),
    create=extend_schema(
        summary="Create Workspace",
        description="Creates a workspace owned by the authenticated user.",
        tags=["Workspaces"],
        request=WorkspaceSerializer,
        responses={
            status.HTTP_201_CREATED: OpenApiResponse(
                response=WorkspaceSerializer,
                description="Workspace created successfully.",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Invalid workspace data."
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(description=AUTH_ERROR),
        },
    ),
    retrieve=extend_schema(
        summary="Get Workspace",
        description="Retrieves a workspace the authenticated user can access.",
        tags=["Workspaces"],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=WorkspaceSerializer,
                description="Workspace retrieved successfully.",
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(description=AUTH_ERROR),
            status.HTTP_403_FORBIDDEN: OpenApiResponse(
                description="The authenticated user cannot access this workspace."
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="Workspace not found."
            ),
        },
    ),
    update=extend_schema(
        summary="Update Workspace",
        description="Replaces workspace information. Only the owner can update it.",
        tags=["Workspaces"],
        request=WorkspaceSerializer,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=WorkspaceSerializer,
                description="Workspace updated successfully.",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Invalid workspace data."
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(description=AUTH_ERROR),
            status.HTTP_403_FORBIDDEN: OpenApiResponse(
                description="Only the workspace owner can update it."
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="Workspace not found."
            ),
        },
    ),
    partial_update=extend_schema(
        summary="Partially Update Workspace",
        description=(
            "Updates one or more workspace fields. Only the owner can update it."
        ),
        tags=["Workspaces"],
        request=WorkspaceSerializer,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=WorkspaceSerializer,
                description="Workspace updated successfully.",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Invalid workspace data."
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(description=AUTH_ERROR),
            status.HTTP_403_FORBIDDEN: OpenApiResponse(
                description="Only the workspace owner can update it."
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="Workspace not found."
            ),
        },
    ),
    destroy=extend_schema(
        summary="Delete Workspace",
        description="Deletes a workspace. Only the owner can delete it.",
        tags=["Workspaces"],
        responses={
            status.HTTP_204_NO_CONTENT: OpenApiResponse(
                description="Workspace deleted successfully."
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(description=AUTH_ERROR),
            status.HTTP_403_FORBIDDEN: OpenApiResponse(
                description="Only the workspace owner can delete it."
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="Workspace not found."
            ),
        },
    ),
)
class WorkspaceViewSet(ModelViewSet):
    queryset = Workspace.objects.all()
    serializer_class = WorkspaceSerializer

    def get_queryset(self) -> QuerySet[Workspace]:
        user = self.request.user
        return (
            Workspace.objects.select_related("owner")
            .prefetch_related("members")
            .filter(Q(owner=user) | Q(members=user))
            .distinct()
        )

    def get_permissions(self) -> list:
        if self.action in [
            "destroy",
            "update",
            "partial_update",
            "refresh_invite_token",
        ]:
            return [IsAuthenticated(), IsWorkspaceOwner()]
        if self.action in ["retrieve", "members"]:
            return [IsAuthenticated(), IsWorkspaceOwnerOrMember()]
        return [IsAuthenticated()]

    def perform_create(self, serializer: BaseSerializer) -> None:
        serializer.save(owner=self.request.user)

    @extend_schema(
        summary="Join Workspace",
        description=(
            "Joins the authenticated user to a workspace using its invite token "
            "and password when required."
        ),
        tags=["Workspaces"],
        request=JoinWorkspaceSerializer,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=inline_serializer(
                    name="JoinWorkspaceResponse",
                    fields={"detail": serializers.CharField()},
                ),
                description="The user joined the workspace or was already a member.",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Invalid invite token or password data."
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(description=AUTH_ERROR),
            status.HTTP_403_FORBIDDEN: OpenApiResponse(
                description="The workspace password is invalid."
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="The invite token is invalid."
            ),
        },
    )
    @action(detail=False, methods=["POST"], serializer_class=JoinWorkspaceSerializer)
    def join(self, request: Request) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data["invite_token"]
        password = serializer.validated_data["password"]

        try:
            workspace = Workspace.objects.get(invite_token=token)
        except Workspace.DoesNotExist:
            return Response(
                {"detail": "Invalid invite link."}, status=status.HTTP_404_NOT_FOUND
            )

        user = request.user
        if workspace.owner == user or workspace.members.contains(user):
            return Response(
                {"detail": "Already in this workspace."}, status=status.HTTP_200_OK
            )

        if workspace.password and not workspace.check_password(password):
            return Response(
                {"detail": "Invalid workspace password."},
                status=status.HTTP_403_FORBIDDEN,
            )

        workspace.members.add(user)
        return Response(
            {"detail": f"Successfully joined {workspace.name}."},
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        summary="Refresh Workspace Invite Token",
        description=(
            "Generates a new invite token for a workspace. Only the owner can "
            "refresh it."
        ),
        tags=["Workspaces"],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=inline_serializer(
                    name="RefreshInviteTokenResponse",
                    fields={"invite_token": serializers.UUIDField()},
                ),
                description="Workspace invite token refreshed successfully.",
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(description=AUTH_ERROR),
            status.HTTP_403_FORBIDDEN: OpenApiResponse(
                description="Only the workspace owner can refresh the invite token."
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="Workspace not found."
            ),
        },
    )
    @action(detail=True, methods=["POST"], url_path="refresh-invite-token")
    def refresh_invite_token(self, request: Request, pk=None) -> Response:
        workspace: Workspace = self.get_object()
        workspace.invite_token = uuid.uuid4()
        workspace.save(update_fields=["invite_token"])
        return Response(
            {"invite_token": workspace.invite_token}, status=status.HTTP_200_OK
        )

    @extend_schema(
        operation_id="workspaces_members_list",
        summary="List Workspace Members",
        description="Lists all members of a workspace.",
        tags=["Workspace Members"],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=UserSummarySerializer(many=True),
                description="Workspace members retrieved successfully.",
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(description=AUTH_ERROR),
            status.HTTP_403_FORBIDDEN: OpenApiResponse(
                description="The authenticated user cannot access this workspace."
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="Workspace not found."
            ),
        },
    )
    @action(detail=True, methods=["GET"], url_path="members")
    def members(self, request: Request, pk: str | None = None) -> Response:
        workspace: Workspace = self.get_object()
        members_serializer = UserSummarySerializer(workspace.members.all(), many=True)
        return Response(members_serializer.data)

    @extend_schema(
        methods=["GET"],
        operation_id="workspaces_member_retrieve",
        summary="Get Workspace Member",
        description="Retrieves a member of a workspace.",
        tags=["Workspace Members"],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=UserSummarySerializer,
                description="Workspace member retrieved successfully.",
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(description=AUTH_ERROR),
            status.HTTP_403_FORBIDDEN: OpenApiResponse(
                description="The authenticated user cannot access this workspace."
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="Workspace or member not found."
            ),
        },
    )
    @extend_schema(
        methods=["DELETE"],
        operation_id="workspaces_member_destroy",
        summary="Remove Workspace Member",
        description=(
            "Removes a member from a workspace. The owner or the member themselves "
            "can remove the membership."
        ),
        tags=["Workspace Members"],
        responses={
            status.HTTP_204_NO_CONTENT: OpenApiResponse(
                description="Workspace member removed successfully."
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="The workspace owner cannot be removed from members."
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(description=AUTH_ERROR),
            status.HTTP_403_FORBIDDEN: OpenApiResponse(
                description="The user does not have permission to remove this member."
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="Workspace or member not found."
            ),
        },
    )
    @action(
        detail=True,
        methods=["GET", "DELETE"],
        url_path=r"members/(?P<user_id>\d+)",
    )
    def members_detail(
        self, request: Request, pk: str | None = None, user_id: str | None = None
    ) -> Response:
        workspace: Workspace = self.get_object()
        target_member = get_object_or_404(workspace.members.all(), pk=user_id)

        if request.method == "GET":
            member_serializer = UserSummarySerializer(target_member)
            return Response(member_serializer.data)

        user = request.user
        if workspace.owner != user and user.id != target_member.id:  # pyright: ignore[reportAttributeAccessIssue]
            return Response(
                {"detail": "You do not have permission to remove this member."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if workspace.owner == target_member:
            return Response(
                {"detail": "Workspace owner cannot be removed from members."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        workspace.members.remove(target_member)
        return Response(status=status.HTTP_204_NO_CONTENT)
