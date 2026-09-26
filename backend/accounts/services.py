import re
import string
from gettext import ngettext

from django.core.cache import cache
from django.db import transaction
from django.utils import timezone
from django.utils.crypto import get_random_string

from config.tasks import send_email_task

from .models import OTP


class OTPServiceError(Exception):
    pass


class OTPRateLimitError(OTPServiceError):
    def __init__(self, retry_after: int, message: str | None = None) -> None:
        self.retry_after = retry_after
        if not message:
            message = (
                "Too many requests."
                f"Please wait {retry_after} seconds before trying again."
            )
        super().__init__(message)


class OTPService:
    CODE_LENGTH = 6
    EXPIRY_MINUTES = 2
    MAX_ATTEMPTS = 5
    COOLDOWN_SECONDS = 60
    ALLOWED_CHARS = string.digits
    OTP_REGEX = rf"^[{re.escape(ALLOWED_CHARS)}]+$"

    @classmethod
    def generate_code(cls) -> str:
        return get_random_string(cls.CODE_LENGTH, cls.ALLOWED_CHARS)

    @classmethod
    def can_request(cls, email: str) -> tuple[bool, int]:
        cache_key = f"otp_cooldown:{email}"
        remaining_ttl = cache.ttl(cache_key) if hasattr(cache, "ttl") else 0  # pyright: ignore[reportAttributeAccessIssue]
        if cache.get(cache_key):
            return False, remaining_ttl or cls.COOLDOWN_SECONDS
        return True, 0

    @classmethod
    def revoke_pending(cls, email: str) -> int:
        now = timezone.now()
        return OTP.objects.filter(email=email, status=OTP.Status.PENDING).update(
            status=OTP.Status.REVOKED, consumed_at=now
        )

    @classmethod
    def send(cls, email: str) -> OTP:
        raw_code = cls.generate_code()
        expires_at = timezone.now() + timezone.timedelta(minutes=cls.EXPIRY_MINUTES)

        is_allowed, remaining_seconds = cls.can_request(email)
        if not is_allowed:
            raise OTPRateLimitError(retry_after=remaining_seconds)

        with transaction.atomic():
            cls.revoke_pending(email)

            otp = OTP(email=email, max_attempts=cls.MAX_ATTEMPTS, expires_at=expires_at)
            otp.set_code(raw_code)
            otp.save()

            cache_key = f"otp_cooldown:{email}"
            cache.set(cache_key, True, timeout=cls.COOLDOWN_SECONDS)

        transaction.on_commit(
            lambda: send_email_task.delay(
                subject="Your Security Code",
                message=(
                    f"Your verification code: {raw_code}\n"
                    f"This code is valid for {cls.EXPIRY_MINUTES} minutes.\n"
                    "If you did not request this, please ignore this email."
                ),
                to_email=email,
            )
        )

        return otp

    @classmethod
    def verify(cls, email: str, raw_code: str) -> tuple[bool, str | None]:
        with transaction.atomic():
            otp = (
                OTP.objects.select_for_update()
                .filter(email=email, status=OTP.Status.PENDING)
                .order_by("-created_at")
                .first()
            )

            if not otp:
                return False, "No active OTP request found. Please request a new code."

            if otp.is_expired:
                return False, "Code has expired. Please request a new code."

            if otp.is_exhausted:
                return False, "Maximum attempts reached. Please request a new code."

            if not otp.check_code(raw_code):
                otp.attempts_count += 1
                otp.save(update_fields=["attempts_count"])
                remaining_attempts = otp.max_attempts - otp.attempts_count
                return False, ngettext(
                    "Invalid code. %(count)d attempt remaining.",
                    "Invalid code. %(count)d attempts remaining.",
                    remaining_attempts,
                ) % {"count": remaining_attempts}

            otp.status = OTP.Status.VERIFIED
            otp.consumed_at = timezone.now()
            otp.save(update_fields=["status", "consumed_at"])
            return True, None
