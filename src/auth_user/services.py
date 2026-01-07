import logging
from datetime import datetime, UTC, timedelta

from src.auth_user import exceptions
from src.auth_user import security
from src.conf.settings import settings
from src.auth_user.tasks import send_email
from src.auth_user.emails.cache import AsyncCacheInterface

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, uow_factory, cache):
        self.uow_factory = uow_factory
        self.cache: AsyncCacheInterface = cache

    async def request_verification_code(self, email: str) -> dict:
        logger.info("Starting verification code request")

        verification_key = f"verification:{email.lower()}"
        if not await self.cache.set_if_not_exists(verification_key, "1", ttl=60):
            logger.warning(f"Rate limit hit for verification code request, {email=}")
            return {"message": "Код уже отправлен, подождите 60 сек."}

        async with self.uow_factory() as uow:
            user = await uow.auth.get_user_by_email(email)
            if not user:
                await uow.auth.create_user(email)
            await uow.auth.delete_verification_codes(email)
            code = await uow.auth.create_verification_code(email)
            send_email.delay(email=email, code=code.code)
            logger.info(f"Verification code sent to {email=}")
            return {
                "email": email,
                "message": "Код отправлен на почту"
            }

    async def authenticate_with_code(self, email: str, code: str):
        logger.info("Starting authentication with code")

        async with self.uow_factory() as uow:
            code_obj = await uow.auth.find_verification_code(email, code)
            if not code_obj:
                logger.warning(f"Invalid verification code for {email=}")
                raise exceptions.InvalidVerificationCodeError("Неверный код подтверждения")

            if not code_obj.is_valid():
                logger.warning(f"Expired verification code for {email=}")
                raise exceptions.ExpiredVerificationCodeError("Код просрочен")

            code_obj.mark_used()

            user = await uow.auth.get_user_by_email(email)
            if not user:
                logger.warning(f"User {email=} not found")
                raise exceptions.UserNotFoundError(f"Пользователь {email} не найден")

            if not user.is_verified:
                user.is_verified = True

            logger.info(f"Delete verification code {email=}")
            await uow.auth.delete_verification_codes(email)
            logger.info(f"Verification code removed")

            access_token = security.create_access_token(user.id)
            refresh_token = security.create_refresh_token()

            expires_at = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
            await uow.auth.save_refresh_token(
                user_id=user.id,
                token_hash=security.hash_refresh_token(refresh_token),
                expires_at=expires_at
            )
            logger.info(f"Refresh token saved")

            return access_token, refresh_token, {
                "id": user.id,
                "email": user.email,
                "is_verified": user.is_verified
            }

    async def refresh_tokens(self, refresh_token: str):
        logger.info("Starting refresh tokens")
        async with self.uow_factory() as uow:
            valid_token = await uow.auth.find_valid_refresh_token_by_token(refresh_token)

            if not valid_token:
                logger.warning(f"Invalid refresh token for {refresh_token=}")
                raise exceptions.RefreshTokenNotFoundError("Невалидный или отозванный refresh токен")

            valid_token.revoked = True
            valid_token.revoked_at = datetime.now(UTC)

            new_access_token = security.create_access_token(valid_token.user_id)
            new_refresh_token = security.create_refresh_token()

            logger.info(f"Create new refresh token")
            expires_at = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
            await uow.auth.save_refresh_token(
                user_id=valid_token.user_id,
                token_hash=security.hash_refresh_token(new_refresh_token),
                expires_at=expires_at
            )
            logger.info(f"Refresh token saved")
            return new_access_token, new_refresh_token

    async def logout(self, user_id: int, refresh_token: str = None) -> bool:
        logger.info("Starting logout")
        async with self.uow_factory() as uow:
            if refresh_token:
                logger.info(f"Find refresh token")
                token = await uow.auth.find_valid_refresh_token(user_id, refresh_token)
                if token:
                    token.revoked = True
                    logger.info(f"Refresh token revoked")
                    return True
            return False

    async def logout_all(self, user_id: int):
        async with self.uow_factory() as uow:
            await uow.auth.revoke_all_user_tokens(user_id)

    async def cleanup_expired_tokens(self) -> int:
        async with self.uow_factory() as uow:
            cleaned = await uow.auth.cleanup_expired_tokens()
            return cleaned
