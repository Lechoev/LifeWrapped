from datetime import UTC, datetime, timedelta

from src.auth_user import exceptions, security
from src.auth_user.emails.cache import AsyncCacheInterface
from src.auth_user.tasks import send_email
from src.conf.logger import get_logger
from src.conf.settings import settings

logger = get_logger(__name__)


class AuthService:
    def __init__(self, uow_factory, cache: AsyncCacheInterface):
        self.uow_factory = uow_factory
        self.cache = cache

    async def request_verification_code(self, email: str) -> dict:
        logger.info("Verification code request started", extra={"email": email})

        verification_key = f"verification:{email.lower()}"
        if not await self.cache.set_if_not_exists(verification_key, "1", ttl=60):
            logger.warning("Verification code rate limit hit", extra={"email": email})
            return {"message": "Код уже отправлен, подождите 60 сек."}

        async with self.uow_factory() as uow:
            user = await uow.auth.get_user_by_email(email)
            if not user:
                await uow.auth.create_user(email)
                logger.info(
                    "User created during verification request", extra={"email": email}
                )

            await uow.auth.delete_verification_codes(email)
            code = await uow.auth.create_verification_code(email)
            send_email.delay(email=email, code=code.code)

            logger.info("Verification code sent", extra={"email": email})

            return {"email": email, "message": "Код отправлен на почту"}

    async def authenticate_with_code(self, email: str, code: str):
        logger.info(
            "Authentication with verification code started", extra={"email": email}
        )

        async with self.uow_factory() as uow:
            code_obj = await uow.auth.find_verification_code(email, code)
            if not code_obj:
                logger.warning("Invalid verification code", extra={"email": email})
                raise exceptions.InvalidVerificationCodeError(
                    "Неверный код подтверждения"
                )

            if not code_obj.is_valid():
                logger.warning("Expired verification code", extra={"email": email})
                raise exceptions.ExpiredVerificationCodeError("Код просрочен")

            code_obj.mark_used()

            user = await uow.auth.get_user_by_email(email)
            if not user:
                logger.error(
                    "Verification code exists but user not found",
                    extra={"email": email},
                )
                raise exceptions.UserNotFoundError(f"Пользователь {email} не найден")

            if not user.is_verified:
                user.is_verified = True

            await uow.auth.delete_verification_codes(email)

            access_token = security.create_access_token(user.id)
            refresh_token = security.create_refresh_token()

            expires_at = datetime.now(UTC) + timedelta(
                days=settings.REFRESH_TOKEN_EXPIRE_DAYS
            )
            await uow.auth.save_refresh_token(
                user_id=user.id,
                token_hash=security.hash_refresh_token(refresh_token),
                expires_at=expires_at,
            )

            logger.info(
                "User authenticated successfully",
                extra={"user_id": user.id, "email": user.email},
            )

            return (
                access_token,
                refresh_token,
                {"id": user.id, "email": user.email, "is_verified": user.is_verified},
            )

    async def refresh_tokens(self, refresh_token: str):
        logger.info("Refresh tokens started")

        async with self.uow_factory() as uow:
            valid_token = await uow.auth.find_valid_refresh_token_by_token(
                refresh_token
            )
            if not valid_token:
                logger.warning("Invalid refresh token attempt")
                raise exceptions.RefreshTokenNotFoundError(
                    "Невалидный или отозванный refresh токен"
                )

            valid_token.revoked = True
            valid_token.revoked_at = datetime.now(UTC)

            new_access_token = security.create_access_token(valid_token.user_id)
            new_refresh_token = security.create_refresh_token()

            expires_at = datetime.now(UTC) + timedelta(
                days=settings.REFRESH_TOKEN_EXPIRE_DAYS
            )

            await uow.auth.save_refresh_token(
                user_id=valid_token.user_id,
                token_hash=security.hash_refresh_token(new_refresh_token),
                expires_at=expires_at,
            )

            logger.info("Refresh token rotated", extra={"user_id": valid_token.user_id})

            return new_access_token, new_refresh_token

    async def logout(self, user_id: int, refresh_token: str | None = None) -> bool:
        logger.info("Logout started", extra={"user_id": user_id})

        if not refresh_token:
            return False

        async with self.uow_factory() as uow:
            token = await uow.auth.find_valid_refresh_token(user_id, refresh_token)
            if not token:
                return False

            token.revoked = True

            logger.info("Refresh token revoked", extra={"user_id": user_id})
            return True

    async def logout_all(self, user_id: int) -> None:
        logger.info("Logout from all sessions started", extra={"user_id": user_id})

        async with self.uow_factory() as uow:
            await uow.auth.revoke_all_user_tokens(user_id)

        logger.info("User logged out from all sessions", extra={"user_id": user_id})

    async def cleanup_expired_tokens(self) -> int:
        logger.info("Expired refresh tokens cleanup started")

        async with self.uow_factory() as uow:
            cleaned = await uow.auth.cleanup_expired_tokens()
        logger.info("Expired refresh tokens cleaned", extra={"count": cleaned})

        return cleaned
