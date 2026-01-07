import pytest
from sqlalchemy import select
from datetime import datetime, UTC, timedelta
from src.auth_user.repositories import AuthRepository
from src.auth_user.models import AuthModel, VerificationCodeModel, RefreshTokenModel
from src.auth_user.security import hash_refresh_token


@pytest.mark.asyncio
async def test_repository_create_and_get_user(async_session):
    repo = AuthRepository(async_session)
    email = "repo_test@example.com"

    user = await repo.create_user(email)
    await async_session.commit()

    assert user.id is not None
    assert user.email == email
    assert user.is_verified is False

    found_user = await repo.get_user_by_email(email)
    assert found_user is not None
    assert found_user.id == user.id


@pytest.mark.asyncio
async def test_repository_verification_codes(async_session):
    repo = AuthRepository(async_session)
    email = "code_test@example.com"

    code = await repo.create_verification_code(email)
    await async_session.commit()

    assert code.id is not None
    assert code.email == email
    assert len(code.code) == 6

    found_code = await repo.find_verification_code(email, code.code)
    assert found_code is not None
    assert found_code.id == code.id

    await repo.delete_verification_codes(email)
    await async_session.commit()

    result = await async_session.execute(
        select(VerificationCodeModel).where(VerificationCodeModel.email == email)
    )
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_repository_refresh_token_operations(async_session):
    repo = AuthRepository(async_session)
    email = "token_test@example.com"

    user = await repo.create_user(email)
    await async_session.commit()

    token_hash = hash_refresh_token("test_token")
    expires_at = datetime.now(UTC) + timedelta(days=7)

    token = await repo.save_refresh_token(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at
    )
    await async_session.commit()

    assert token.id is not None
    assert token.user_id == user.id

    await repo.revoke_all_user_tokens(user.id)
    await async_session.commit()

    result = await async_session.execute(
        select(RefreshTokenModel).where(RefreshTokenModel.user_id == user.id)
    )
    tokens = result.scalars().all()
    for token in tokens:
        assert token.revoked is True
