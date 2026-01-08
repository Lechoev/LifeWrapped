from src.auth_user.emails.cache import SyncCacheInterface
from src.auth_user.emails.sender import EmailSenderInterface
from src.conf.logger import get_logger

logger = get_logger(__name__)


class VerificationEmailService:
    LOCK_TTL = 60
    CACHE_PREFIX = "verification"

    def __init__(self, cache: SyncCacheInterface, sender: EmailSenderInterface):
        self.cache = cache
        self.sender = sender

    def _get_cache_key(self, email: str) -> str:
        return f"{self.CACHE_PREFIX}:{email}"

    def send(self, email: str, code: str) -> bool:
        key = self._get_cache_key(email)

        is_allowed = self.cache.set_if_not_exists(
            key=key, value="locked", ttl=self.LOCK_TTL
        )

        if not is_allowed:
            logger.info("Email rate limit triggered", extra={"email": email})
            return False

        self.sender.send_verification_code(email, code)
        logger.info("Verification email sent", extra={"email": email})
        return True
