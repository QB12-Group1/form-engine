from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.utils import timezone
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


class OTP(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        VERIFIED = "verified", _("Verified")
        REVOKED = "revoked", _("Revoked")

    email = models.EmailField()
    status = models.CharField(
        max_length=16, default=Status.PENDING, choices=Status.choices, db_index=True
    )

    code = models.CharField(max_length=128)
    attempts_count = models.PositiveSmallIntegerField(default=0)
    max_attempts = models.PositiveSmallIntegerField(default=5)

    expires_at = models.DateTimeField(db_index=True)
    consumed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "OTP"
        verbose_name_plural = "OTPs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["email", "-created_at"],
                name="idx_otp_lookup",
                condition=models.Q(status="pending"),
            )
        ]
        constraints = (
            models.CheckConstraint(
                condition=models.Q(attempts_count__lte=models.F("max_attempts")),
                name="otp_attempts_within_limit",
            ),
            models.CheckConstraint(
                condition=models.Q(email__isnull=False),
                name="otp_has_recipient",
            ),
        )

    def __str__(self) -> str:
        recipient = self.email or "No Recipient"
        return f"OTP ({recipient}) [{self.effective_status}]"

    @property
    def is_expired(self) -> bool:
        return self.expires_at <= timezone.now()

    @property
    def is_exhausted(self) -> bool:
        return self.attempts_count >= self.max_attempts

    @property
    def is_usable(self) -> bool:
        return (
            self.status == self.Status.PENDING
            and not self.is_expired
            and not self.is_exhausted
        )

    @property
    def effective_status(self) -> str:
        if self.status == self.Status.VERIFIED:
            val = self.Status.VERIFIED.label
        elif self.status == self.Status.REVOKED:
            val = self.Status.REVOKED.label
        elif self.is_exhausted:
            val = "Exhausted"
        elif self.is_expired:
            val = "Expired"
        else:
            val = self.Status.PENDING.label

        return val

    def set_code(self, raw_code: str) -> None:
        self.code = make_password(raw_code)

    def check_code(self, raw_code: str) -> bool:
        return check_password(raw_code, self.code)
