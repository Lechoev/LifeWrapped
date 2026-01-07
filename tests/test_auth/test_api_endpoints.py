import pytest
from datetime import datetime, UTC, timedelta
from sqlalchemy import select

from src.auth_user.models import AuthModel, VerificationCodeModel, RefreshTokenModel
from src.auth_user.security import hash_refresh_token, verify_refresh_token
from src.auth_user.repositories import AuthRepository


def get_unique_email(base_name: str) -> str:
    timestamp = datetime.now().timestamp()
    return f"{base_name}_{timestamp}@example.com"


@pytest.mark.asyncio
async def test_request_code_integration(async_client, async_session):
    email = get_unique_email("request_code_test")

    response = await async_client.post(
        "/auth_router/v1/auth/request-code",
        json={"email": email}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == email
    assert "Код отправлен" in data["message"]

    result = await async_session.execute(
        select(AuthModel).where(AuthModel.email == email)
    )
    user = result.scalar_one_or_none()
    assert user is not None
    assert user.email == email
    assert user.is_verified is False

    result = await async_session.execute(
        select(VerificationCodeModel).where(VerificationCodeModel.email == email)
    )
    code_obj = result.scalar_one_or_none()
    assert code_obj is not None
    assert len(code_obj.code) == 6


@pytest.mark.asyncio
async def test_authenticate_integration(async_client, async_session):
    email = get_unique_email("auth_integration")
    test_code = "888888"

    repo = AuthRepository(async_session)
    user = await repo.create_user(email)
    code_obj = await repo.create_verification_code(email)
    code_obj.code = test_code
    await async_session.commit()

    response = await async_client.post(
        "/auth_router/v1/auth/authenticate",
        json={"email": email, "code": test_code}
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "user" in data
    assert data["user"]["email"] == email
    assert data["user"]["is_verified"] is True

    refresh_token_cookie = response.cookies.get("refresh_token")
    assert refresh_token_cookie is not None

    result = await async_session.execute(
        select(AuthModel).where(AuthModel.email == email)
    )
    user = result.scalar_one_or_none()
    assert user.is_verified is True

    result = await async_session.execute(
        select(RefreshTokenModel).where(RefreshTokenModel.user_id == user.id)
    )
    tokens = result.scalars().all()
    assert len(tokens) >= 1

    saved_token = tokens[-1]
    assert verify_refresh_token(saved_token.token_hash, refresh_token_cookie)

    return {
        "access_token": data["access_token"],
        "refresh_token": refresh_token_cookie,
        "user_id": user.id
    }


@pytest.mark.asyncio
async def test_refresh_token_integration(async_client, async_session):
    email = get_unique_email("refresh_integration")
    test_code = "777777"

    repo = AuthRepository(async_session)
    user = await repo.create_user(email)
    code_obj = await repo.create_verification_code(email)
    code_obj.code = test_code
    await async_session.commit()

    auth_response = await async_client.post(
        "/auth_router/v1/auth/authenticate",
        json={"email": email, "code": test_code}
    )

    assert auth_response.status_code == 200
    refresh_token_cookie = auth_response.cookies.get("refresh_token")
    assert refresh_token_cookie is not None

    response = await async_client.post(
        "/auth_router/v1/auth/refresh",
        cookies={"refresh_token": refresh_token_cookie}
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["access_token"] is not None

    new_refresh_cookie = response.cookies.get("refresh_token")
    assert new_refresh_cookie is not None
    assert new_refresh_cookie != refresh_token_cookie


@pytest.mark.asyncio
async def test_me_endpoint_integration(async_client, async_session):
    email = get_unique_email("me_test")
    test_code = "666666"

    repo = AuthRepository(async_session)
    user = await repo.create_user(email)
    code_obj = await repo.create_verification_code(email)
    code_obj.code = test_code
    await async_session.commit()

    auth_response = await async_client.post(
        "/auth_router/v1/auth/authenticate",
        json={"email": email, "code": test_code}
    )

    assert auth_response.status_code == 200
    auth_data = auth_response.json()
    access_token = auth_data["access_token"]

    response = await async_client.get(
        "/auth_router/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user.id
    assert "message" in data


@pytest.mark.asyncio
async def test_logout_integration(async_client, async_session):
    email = get_unique_email("logout_test")
    test_code = "555555"

    repo = AuthRepository(async_session)
    user = await repo.create_user(email)
    code_obj = await repo.create_verification_code(email)
    code_obj.code = test_code
    await async_session.commit()

    auth_response = await async_client.post(
        "/auth_router/v1/auth/authenticate",
        json={"email": email, "code": test_code}
    )

    assert auth_response.status_code == 200
    access_token = auth_response.json()["access_token"]
    refresh_token_cookie = auth_response.cookies.get("refresh_token")

    response = await async_client.post(
        "/auth_router/v1/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"},
        cookies={"refresh_token": refresh_token_cookie}
    )

    assert response.status_code == 200
    data = response.json()
    assert "msg" in data
    assert data["msg"] == "Успешный выход"

    assert response.cookies.get("refresh_token") is None or response.cookies.get("refresh_token") == ""


@pytest.mark.asyncio
async def test_cleanup_tokens_integration(async_client, async_session):
    email = get_unique_email("cleanup_test")

    repo = AuthRepository(async_session)
    user = await repo.create_user(email)
    user.is_verified = True
    await async_session.commit()

    for i in range(2):
        token_hash = hash_refresh_token(f"expired_{i}")
        expires_at = datetime.now(UTC) - timedelta(days=1)

        token = RefreshTokenModel(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at
        )
        async_session.add(token)

    for i in range(2):
        token_hash = hash_refresh_token(f"valid_{i}")
        expires_at = datetime.now(UTC) + timedelta(days=7)

        token = RefreshTokenModel(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at
        )
        async_session.add(token)

    await async_session.commit()

    response = await async_client.post("/auth_router/v1/auth/cleanup-tokens")

    assert response.status_code == 200
    data = response.json()
    assert "msg" in data
    assert "Очищено" in data["msg"]


@pytest.mark.asyncio
async def test_invalid_code_integration(async_client, async_session):
    email = get_unique_email("invalid_code_test")

    repo = AuthRepository(async_session)
    await repo.create_user(email)
    await async_session.commit()

    response = await async_client.post(
        "/auth_router/v1/auth/authenticate",
        json={"email": email, "code": "wrong_code"}
    )

    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "Неверный код подтверждения" in data["detail"]


@pytest.mark.asyncio
async def test_expired_code_integration(async_client, async_session):
    email = get_unique_email("expired_code_test")
    test_code = "222222"

    repo = AuthRepository(async_session)
    await repo.create_user(email)
    code_obj = await repo.create_verification_code(email)
    code_obj.code = test_code
    code_obj.created_at = datetime.now(UTC) - timedelta(minutes=2)
    await async_session.commit()

    response = await async_client.post(
        "/auth_router/v1/auth/authenticate",
        json={"email": email, "code": test_code}
    )

    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "Код просрочен" in data["detail"]
