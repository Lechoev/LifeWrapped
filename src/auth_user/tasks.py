from celery import Task

from src.conf.celery import celery_app
from src.conf.logger import get_logger
from src.auth_user.emails.dependencies import get_email_sender, get_redis_cache
from src.auth_user.emails.services import VerificationEmailService

logger = get_logger(__name__)


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=5,
    retry_kwargs={"max_retries": 3},
)
def send_email(self: Task, email: str, code: str):
    logger.info("Send verification email task started",extra={"email": email, "retry": self.request.retries})

    cache = get_redis_cache()
    sender = get_email_sender()

    service: VerificationEmailService = VerificationEmailService(cache=cache, sender=sender)
    service.send(email, code)

    logger.info("Verification email sent successfully",extra={"email": email})
