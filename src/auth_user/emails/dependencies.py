from src.auth_user.emails.cache import (
    AsyncCacheInterface,
    AsyncRedisCache,
    SyncCacheInterface,
    SyncRedisCache,
)
from src.auth_user.emails.sender import EmailSenderInterface, SmtpEmailSender
from src.conf.settings import settings


def get_email_sender() -> EmailSenderInterface:
    return SmtpEmailSender(
        host=settings.EMAIL_HOST,
        port=settings.EMAIL_PORT,
        user=settings.EMAIL_HOST_USER,
        password=settings.EMAIL_HOST_PASSWORD,
        from_email=settings.DEFAULT_FROM_EMAIL,
        use_tls=settings.EMAIL_USE_TLS,
    )


def get_redis_cache() -> SyncCacheInterface:
    return SyncRedisCache(settings.REDIS_URL)


async def get_async_redis_cache() -> AsyncCacheInterface:
    return await AsyncRedisCache.get_instance(settings.REDIS_URL)
