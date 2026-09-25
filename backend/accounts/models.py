from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from .managers import UserManager


class User(AbstractUser):
    REQUIRED_FIELDS = []

    username = models.CharField(
        _("username"),
        max_length=150,
        unique=True,
        null=True,
        blank=True,
        help_text=_(
            "Required for staff and admin users. 150 characters or fewer."
            "Letters, digits and @/./+/-/_ only."
        ),
        validators=[UnicodeUsernameValidator()],
        error_messages={
            "unique": _("A user with that username already exists."),
        },
    )
    email = models.EmailField(
        _("email address"),
        unique=True,
        null=True,
        blank=True,
        help_text=_("Required for regular users. Format: user@example.com"),
        error_messages={"unique": _("A user with that email already exists.")},
    )

    objects = UserManager()  # pyright: ignore[reportAssignmentType]

    def _normalize_nullable_fields(self, update_fields=None) -> None:
        if update_fields is None or "username" in update_fields:
            self.username = self.username or None

        if update_fields is None or "email" in update_fields:
            self.email = self.email or None

    def clean(self) -> None:
        super().clean()
        return self._normalize_nullable_fields()

    def save(self, *args, **kwargs) -> None:
        update_fields = kwargs.get("update_fields")
        self._normalize_nullable_fields(update_fields)
        return super().save(*args, **kwargs)

    async def asave(self, *args, **kwargs) -> None:
        update_fields = kwargs.get("update_fields")
        self._normalize_nullable_fields(update_fields)
        return await super().asave(*args, **kwargs)

    def __str__(self) -> str:
        identifier = self.username or self.email or f"User #{self.pk or 'new'}"
        full_name = self.get_full_name()
        return f"{identifier} ({full_name})" if full_name else identifier
