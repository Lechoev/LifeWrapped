from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from src.auth_user.models import AuthModel, RefreshTokenModel


@pytest.mark.asyncio
async def test_full_auth_flow_async(async_client, async_session):
    email = "test@example.com"

    response = await async_client.post(
        "/auth_router/v1/auth/request-code",
        json={"email": email},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["email"] == email
    assert "Код отправлен" in response_data["message"]

    result = await async_session.execute(
        select(AuthModel).where(AuthModel.email == email)
    )
    user = result.scalar_one_or_none()

    assert user is not None
    assert user.email == email
    assert user.is_verified is False


@pytest.mark.asyncio
async def test_request_verification_code(async_session, mock_cache, uow_factory):
    from src.auth_user.services import AuthService

    service = AuthService(uow_factory=uow_factory, cache=mock_cache)
    email = "test@example.com"

    result = await service.request_verification_code(email)

    assert result["email"] == email
    assert "Код отправлен" in result["message"]

    result_db = await async_session.execute(
        select(AuthModel).where(AuthModel.email == email)
    )
    user = result_db.scalar_one_or_none()
    assert user is not None
    assert user.email == email


@pytest.mark.asyncio
async def test_authenticate_with_code(async_session, mock_cache, uow_factory):
    from src.auth_user.services import AuthService

    service = AuthService(uow_factory=uow_factory, cache=mock_cache)
    email = "auth_test@example.com"
    test_code = "123456"

    async with uow_factory() as uow:
        user = await uow.auth.create_user(email)

        from src.auth_user.models import VerificationCodeModel

        code_obj = VerificationCodeModel(email=email, code=test_code)
        uow.session.add(code_obj)

    access_token, refresh_token, user_data = await service.authenticate_with_code(
        email=email, code=test_code
    )

    assert access_token is not None
    assert refresh_token is not None
    assert user_data["email"] == email
    assert user_data["is_verified"] is True

    result = await async_session.execute(
        select(AuthModel).where(AuthModel.email == email)
    )
    user = result.scalar_one_or_none()
    assert user is not None
    assert user.is_verified is True


@pytest.mark.asyncio
async def test_refresh_tokens(async_session, mock_cache, uow_factory):
    from src.auth_user.security import hash_refresh_token
    from src.auth_user.services import AuthService

    service = AuthService(uow_factory=uow_factory, cache=mock_cache)
    email = "refresh_test@example.com"

    async with uow_factory() as uow:
        user = await uow.auth.create_user(email)
        user.is_verified = True

        test_refresh_token = "test_refresh_token_123"
        token_hash = hash_refresh_token(test_refresh_token)
        expires_at = datetime.now(UTC) + timedelta(days=7)

        refresh_token_obj = RefreshTokenModel(
            user_id=user.id, token_hash=token_hash, expires_at=expires_at
        )
        uow.session.add(refresh_token_obj)

    new_access_token, new_refresh_token = await service.refresh_tokens(
        test_refresh_token
    )

    assert new_access_token is not None
    assert new_refresh_token is not None
    assert new_refresh_token != test_refresh_token

    result = await async_session.execute(
        select(RefreshTokenModel).where(RefreshTokenModel.token_hash == token_hash)
    )
    old_token = result.scalar_one_or_none()
    assert old_token is not None
    assert old_token.revoked is True


@pytest.mark.asyncio
async def test_rate_limiting(async_session, mock_cache, uow_factory):
    from src.auth_user.services import AuthService

    service = AuthService(uow_factory=uow_factory, cache=mock_cache)
    email = "rate_test@example.com"

    mock_cache.set_if_not_exists.side_effect = [True, False]

    result1 = await service.request_verification_code(email)
    assert result1["email"] == email
    assert "Код отправлен" in result1["message"]

    result2 = await service.request_verification_code(email)
    assert "Код уже отправлен, подождите 60 сек" in result2["message"]


@pytest.mark.asyncio
async def test_invalid_verification_code(async_session, mock_cache, uow_factory):
    from src.auth_user import exceptions
    from src.auth_user.services import AuthService

    service = AuthService(uow_factory=uow_factory, cache=mock_cache)
    email = "invalid_code_test@example.com"

    async with uow_factory() as uow:
        await uow.auth.create_user(email)

    with pytest.raises(exceptions.InvalidVerificationCodeError) as exc_info:
        await service.authenticate_with_code(email=email, code="wrong_code")

    assert "Неверный код подтверждения" in str(exc_info.value)


@pytest.mark.asyncio
async def test_logout(async_session, mock_cache, uow_factory):
    from src.auth_user.security import hash_refresh_token
    from src.auth_user.services import AuthService

    service = AuthService(uow_factory=uow_factory, cache=mock_cache)
    email = "logout_test@example.com"
    test_refresh_token = "logout_test_token"

    async with uow_factory() as uow:
        user = await uow.auth.create_user(email)
        user.is_verified = True

        token_hash = hash_refresh_token(test_refresh_token)
        expires_at = datetime.now(UTC) + timedelta(days=7)

        refresh_token = RefreshTokenModel(
            user_id=user.id, token_hash=token_hash, expires_at=expires_at
        )
        uow.session.add(refresh_token)

    result = await service.logout(user_id=user.id, refresh_token=test_refresh_token)

    assert result is True

    result = await async_session.execute(
        select(RefreshTokenModel).where(RefreshTokenModel.token_hash == token_hash)
    )
    token = result.scalar_one_or_none()
    assert token is not None
    assert token.revoked is True


@pytest.mark.asyncio
async def test_logout_all(async_session, mock_cache, uow_factory):
    from src.auth_user.security import hash_refresh_token
    from src.auth_user.services import AuthService

    service = AuthService(uow_factory=uow_factory, cache=mock_cache)
    email = "logout_all_test@example.com"

    async with uow_factory() as uow:
        user = await uow.auth.create_user(email)
        user.is_verified = True

        for i in range(3):
            token_hash = hash_refresh_token(f"token_{i}")
            expires_at = datetime.now(UTC) + timedelta(days=7)

            refresh_token = RefreshTokenModel(
                user_id=user.id, token_hash=token_hash, expires_at=expires_at
            )
            uow.session.add(refresh_token)

    await service.logout_all(user.id)

    result = await async_session.execute(
        select(RefreshTokenModel).where(RefreshTokenModel.user_id == user.id)
    )
    tokens = result.scalars().all()

    assert len(tokens) == 3
    for token in tokens:
        assert token.revoked is True


@pytest.mark.asyncio
async def test_cleanup_expired_tokens(async_session, mock_cache, uow_factory):
    from src.auth_user.security import hash_refresh_token
    from src.auth_user.services import AuthService

    service = AuthService(uow_factory=uow_factory, cache=mock_cache)
    email = "cleanup_test@example.com"

    async with uow_factory() as uow:
        user = await uow.auth.create_user(email)
        user.is_verified = True

        expired_token_hash = hash_refresh_token("expired_token")
        expired_at = datetime.now(UTC) - timedelta(days=1)

        expired_token = RefreshTokenModel(
            user_id=user.id, token_hash=expired_token_hash, expires_at=expired_at
        )
        uow.session.add(expired_token)

        valid_token_hash = hash_refresh_token("valid_token")
        valid_at = datetime.now(UTC) + timedelta(days=7)

        valid_token = RefreshTokenModel(
            user_id=user.id, token_hash=valid_token_hash, expires_at=valid_at
        )
        uow.session.add(valid_token)

    cleaned_count = await service.cleanup_expired_tokens()

    assert cleaned_count == 1

    result = await async_session.execute(
        select(RefreshTokenModel).where(
            RefreshTokenModel.token_hash == expired_token_hash
        )
    )
    assert result.scalar_one_or_none() is None

    result = await async_session.execute(
        select(RefreshTokenModel).where(
            RefreshTokenModel.token_hash == valid_token_hash
        )
    )
    assert result.scalar_one_or_none() is not None
