from django.db import models


class Workspace(models.Model):
    owner = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="workspaces"
    )
    name = models.CharField(max_length=100)
    password = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
