import uuid

from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.db import models


class Workspace(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="workspaces"
    )
    name = models.CharField(max_length=100)
    password = models.CharField(max_length=256, blank=True, null=True)  # noqa: DJ001
    invite_token = models.UUIDField(default=uuid.uuid4, unique=True, null=True)
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="joined_workspaces", blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.owner})"

    def check_password(self, raw_password: str) -> bool:
        return check_password(raw_password, self.password) if self.password else False
