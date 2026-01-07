from celery import Task

from src.conf.celery import celery_app
from src.auth_user.emails.dependencies import get_email_sender, get_redis_cache
from src.auth_user.emails.services import VerificationEmailService


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=5,
    retry_kwargs={"max_retries": 3},
)
def send_email(self: Task, email: str, code: str):
    cache = get_redis_cache()
    sender = get_email_sender()

    service: VerificationEmailService = VerificationEmailService(cache=cache, sender=sender)
    service.send(email, code)
