from typing import Any

from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from workspaces.permissions import IsWorkspaceOwnerOrMember


class HasWorkspaceAccess(BasePermission):
    def has_object_permission(self, request: Request, view: APIView, obj: Any) -> bool:
        return IsWorkspaceOwnerOrMember().has_object_permission(
            request, view, obj.workspace
        )


class HasSurveyAccess(BasePermission):
    def has_object_permission(self, request: Request, view: APIView, obj: Any) -> bool:
        return IsWorkspaceOwnerOrMember().has_object_permission(
            request, view, obj.survey.workspace
        )
