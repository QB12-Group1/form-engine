import uuid

from django.db.models import Q, QuerySet
from rest_framework import status
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


class WorkspaceViewSet(ModelViewSet):
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

    @action(detail=False, methods=["POST"], serializer_class=JoinWorkspaceSerializer)
    def join(self, request: Request) -> Response:
        serializer = self.get_serializer()
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

    @action(detail=True, methods=["POST"], url_path="refresh-invite-token")
    def refresh_invite_token(self, request: Request, pk=None) -> Response:
        workspace: Workspace = self.get_object()
        workspace.invite_token = uuid.uuid4()
        workspace.save(update_fields=["invite_token"])
        return Response(
            {"invite_token": workspace.invite_token}, status=status.HTTP_200_OK
        )

    @action(detail=True, methods=["GET"], url_path="members")
    def members(self, request: Request, pk: str | None = None) -> Response:
        workspace: Workspace = self.get_object()
        members_serializer = UserSummarySerializer(workspace.members.all(), many=True)
        return Response(members_serializer.data)

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
