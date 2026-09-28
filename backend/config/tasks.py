from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=5,
    retry_backoff_max=300,
    retry_jitter=True,
    max_retries=3,
    rate_limit="50/m",
    ignore_result=True,
    soft_time_limit=30,
    time_limit=45,
)
def send_email_task(
    self, subject: str, message: str, to_email: str | list[str]
) -> None:
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[to_email] if isinstance(to_email, str) else to_email,
    )
