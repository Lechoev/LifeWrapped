from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.auth_user.security import get_user_id_from_access_token
from src.auth_user.services import AuthService
from src.common.dependencies import get_uow_factory
from src.auth_user.emails.dependencies import get_async_redis_cache

security = HTTPBearer()


async def get_auth_service() -> AuthService:
    cache = await get_async_redis_cache()
    return AuthService(
        uow_factory=get_uow_factory(),
        cache=cache
    )


async def get_current_verified_user(
        credentials: HTTPAuthorizationCredentials = Depends(security)
) -> int:
    token = credentials.credentials
    return get_user_id_from_access_token(token)
