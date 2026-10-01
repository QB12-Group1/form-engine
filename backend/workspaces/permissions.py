from typing import Any

from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView


class IsWorkspaceOwner(BasePermission):
    def has_object_permission(self, request: Request, view: APIView, obj: Any) -> bool:
        return obj.owner == request.user


class IsWorkspaceOwnerOrMember(IsWorkspaceOwner):
    def has_object_permission(self, request: Request, view: APIView, obj: Any) -> bool:
        return obj.owner == request.user or obj.members.contains(request.user)
