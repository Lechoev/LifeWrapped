from src.auth_user.emails.cache import SyncCacheInterface
from src.auth_user.emails.sender import EmailSenderInterface


class VerificationEmailService:
    LOCK_TTL = 60
    CACHE_PREFIX = "verification"

    def __init__(self, cache: SyncCacheInterface, sender: EmailSenderInterface):
        self.cache = cache
        self.sender = sender

    def _get_cache_key(self, email: str) -> str:
        """Централизованное создание ключа"""
        return f"{self.CACHE_PREFIX}:{email}"

    def send(self, email: str, code: str) -> bool:
        """
        Пытается отправить код.
        Возвращает True, если отправлено, и False, если сработал лимит.
        """
        key = self._get_cache_key(email)

        # Атомарная блокировка "одно письмо в минуту"
        is_allowed = self.cache.set_if_not_exists(
            key=key,
            value="locked",  # Значение не важно, важен сам факт наличия ключа
            ttl=self.LOCK_TTL
        )

        if not is_allowed:
            # logger.info(f"Rate limit triggered for {email}")
            return False

        self.sender.send_verification_code(email, code)
        return True
