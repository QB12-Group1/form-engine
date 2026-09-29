from typing import Any

from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView


class IsWorkspaceOwner(BasePermission):
    def has_object_permission(self, request: Request, view: APIView, obj: Any) -> bool:
        return obj.owner == request.user.id  # pyright: ignore[reportAttributeAccessIssue]


class IsWorkspaceOwnerOrMember(IsWorkspaceOwner):
    def has_object_permission(self, request: Request, view: APIView, obj: Any) -> bool:
        return super().has_object_permission(
            request, view, obj
        ) or obj.members.contains(request.user)
