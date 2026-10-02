import asyncio

from django.contrib.auth.models import AbstractUser, BaseUserManager


class UserManager(BaseUserManager):
    def _check_permission(self, superuser: bool, extra_fields: dict) -> None:
        extra_fields.setdefault("is_staff", superuser)
        extra_fields.setdefault("is_superuser", superuser)

        is_staff, is_superuser = (
            extra_fields.get("is_staff"),
            extra_fields.get("is_superuser"),
        )

        if superuser:
            if not is_staff:
                raise ValueError("Superuser must have `is_staff=True`")

            if not is_superuser:
                raise ValueError("Superuser must have `is_superuser=True`")
        else:
            if is_staff:
                raise ValueError("Regular user must have `is_staff=False`.")

            if is_superuser:
                raise ValueError("Regular user must have `is_superuser=False`.")

    def _check_fields(self, superuser: bool, **kwargs) -> None:
        username, email, password = (
            kwargs.get("username"),
            kwargs.get("email"),
            kwargs.get("password"),
        )

        if superuser:
            if not username:
                raise ValueError("The given username must be set.")

            if not password:
                raise ValueError("The given password must be set.")

            if email:
                raise ValueError("Superuser must have `email=None`")
        else:
            if not email:
                raise ValueError("The given email must be set.")

            if username:
                raise ValueError("Regular user must have `username=None`.")

            if password:
                raise ValueError("Regular user must have `password=None`.")

    def _create_user_object(
        self,
        username: str | None = None,
        email: str | None = None,
        password: str | None = None,
        **extra_fields,
    ) -> AbstractUser:
        username = self.model.normalize_username(username) if username else None
        email = self.normalize_email(email) if email else None

        if username and email:
            raise ValueError("Provide either a username or an email, not both.")

        if username and not password:
            raise ValueError("A password is required when providing a username.")

        if email and password:
            raise ValueError(
                "Password is not allowed for email-based (passwordless) accounts."
            )

        user = self.model(username=username, email=email, **extra_fields)
        return user

    def create_user(self, email: str, **extra_fields) -> AbstractUser:
        self._check_permission(False, extra_fields)
        self._check_fields(False, email=email, **extra_fields)

        user = self._create_user_object(email=email, **extra_fields)
        user.set_unusable_password()
        user.save(using=self.db)
        return user

    async def acreate_user(self, email: str, **extra_fields) -> AbstractUser:
        self._check_permission(False, extra_fields)
        self._check_fields(False, email=email, **extra_fields)

        user = self._create_user_object(email=email, **extra_fields)
        user.set_unusable_password()
        await user.asave(using=self.db)
        return user

    def create_superuser(
        self, username: str, password: str, **extra_fields
    ) -> AbstractUser:
        self._check_permission(True, extra_fields)
        self._check_fields(True, username=username, password=password, **extra_fields)

        user = self._create_user_object(
            username=username, password=password, **extra_fields
        )
        user.set_password(password)
        user.save()
        return user

    async def acreate_superuser(
        self, username: str, password: str, extra_fields
    ) -> AbstractUser:
        self._check_permission(True, extra_fields)
        self._check_fields(True, username=username, password=password, **extra_fields)

        user = self._create_user_object(
            username=username, password=password, **extra_fields
        )
        await asyncio.to_thread(user.set_password, password)
        await user.asave()
        return user
