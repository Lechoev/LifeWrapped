from datetime import datetime, UTC

from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth_user.models import AuthModel, VerificationCodeModel, RefreshTokenModel


class AuthRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_by_email(self, email: str) -> AuthModel | None:
        result = await self.session.execute(
            select(AuthModel).where(AuthModel.email == email)
        )
        return result.scalar_one_or_none()

    async def create_user(self, email: str) -> AuthModel:
        user = AuthModel(email=email, is_verified=False)
        self.session.add(user)
        await self.session.flush()
        return user

    async def delete_verification_codes(self, email: str):
        await self.session.execute(
            delete(VerificationCodeModel).where(
                VerificationCodeModel.email == email
            )
        )

    async def create_verification_code(self, email: str) -> VerificationCodeModel:
        code_obj = VerificationCodeModel.generate_code(email=email)
        self.session.add(code_obj)
        await self.session.flush()
        return code_obj

    async def find_verification_code(self, email: str, code: str) -> VerificationCodeModel | None:
        result = await self.session.execute(
            select(VerificationCodeModel)
            .where(
                VerificationCodeModel.email == email,
                VerificationCodeModel.code == code
            )
            .order_by(VerificationCodeModel.created_at.desc())
        )
        return result.scalar_one_or_none()

    async def save_refresh_token(self, user_id: int, token_hash: str, expires_at: datetime) -> RefreshTokenModel:
        token = RefreshTokenModel(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at
        )
        self.session.add(token)
        await self.session.flush()
        return token

    async def find_valid_refresh_token(self, user_id: int, plain_token: str) -> RefreshTokenModel | None:
        result = await self.session.execute(
            select(RefreshTokenModel).where(
                RefreshTokenModel.user_id == user_id,
                RefreshTokenModel.expires_at > datetime.now(UTC),
                RefreshTokenModel.revoked == False
            )
        )
        tokens = result.scalars().all()

        from src.auth_user.security import verify_refresh_token
        for token in tokens:
            if verify_refresh_token(token.token_hash, plain_token):
                return token
        return None

    async def revoke_all_user_tokens(self, user_id: int):
        await self.session.execute(
            update(RefreshTokenModel)
            .where(RefreshTokenModel.user_id == user_id)
            .values(revoked=True)
        )

    async def cleanup_expired_tokens(self) -> int:
        result = await self.session.execute(
            delete(RefreshTokenModel)
            .where(RefreshTokenModel.expires_at < datetime.now(UTC))
            .returning(RefreshTokenModel.id)
        )
        return len(result.scalars().all())

    async def find_valid_refresh_token_by_token(self, plain_token: str) -> RefreshTokenModel | None:
        result = await self.session.execute(
            select(RefreshTokenModel).where(
                RefreshTokenModel.expires_at > datetime.now(UTC),
                RefreshTokenModel.revoked == False
            )
        )
        all_tokens = result.scalars().all()

        from src.auth_user.security import verify_refresh_token
        for token in all_tokens:
            if verify_refresh_token(token.token_hash, plain_token):
                return token

        return None
