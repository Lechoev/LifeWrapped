from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse

from src.auth_user.decorators import auth_exceptions
from src.auth_user.dependencies import get_auth_service, get_current_verified_user
from src.auth_user.schemas import AuthSchema, VerificationCodeSchema
from src.auth_user.services import AuthService
from src.conf import settings
from src.conf.logger import get_logger

logger = get_logger(__name__)


router = APIRouter(tags=["auth_user"])


@router.post("/v1/auth/request-code", summary="Запросить код подтверждения")
@auth_exceptions
async def request_verification_code(
    auth: AuthSchema,
    service: AuthService = Depends(get_auth_service),
) -> dict:
    logger.info("Request verification code", extra={"email": auth.email})
    result = await service.request_verification_code(auth.email)
    return result


@router.post("/v1/auth/authenticate", summary="Аутентификация по коду")
@auth_exceptions
async def authenticate(
    data: VerificationCodeSchema,
    service: AuthService = Depends(get_auth_service),
) -> JSONResponse:
    logger.info("Authenticate attempt", extra={"email": data.email})

    access_token, refresh_token, user = await service.authenticate_with_code(
        email=data.email, code=data.code
    )

    response = JSONResponse(
        content={
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": user,
        },
        status_code=status.HTTP_200_OK,
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
        path="/",
    )

    return response


@router.post("/v1/auth/refresh", summary="Обновление токенов")
@auth_exceptions
async def refresh(
    request: Request,
    service: AuthService = Depends(get_auth_service),
) -> JSONResponse:
    logger.info("Refresh token attempt")

    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token отсутствует"
        )

    new_access_token, new_refresh_token = await service.refresh_tokens(refresh_token)

    response = JSONResponse(
        content={
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }
    )

    # Обновляем refresh токен в cookie
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
        path="/",
    )

    return response


@router.post("/v1/auth/logout", summary="Выход с текущего устройства")
@auth_exceptions
async def logout(
    request: Request,
    service: AuthService = Depends(get_auth_service),
    current_user: int = Depends(get_current_verified_user),
) -> JSONResponse:
    logger.info("Logout", extra={"user_id": current_user})

    refresh_token = request.cookies.get("refresh_token")
    await service.logout(current_user, refresh_token)

    response = JSONResponse(
        content={"msg": "Успешный выход"}, status_code=status.HTTP_200_OK
    )

    response.delete_cookie(key="refresh_token", path="/")
    return response


@router.post("/v1/auth/logout/all", summary="Выход со всех устройств")
@auth_exceptions
async def logout_all(
    service: AuthService = Depends(get_auth_service),
    current_user: int = Depends(get_current_verified_user),
) -> JSONResponse:
    logger.info("Logout all sessions", extra={"user_id": current_user})

    await service.logout_all(current_user)

    response = JSONResponse(
        content={"msg": "Успешный выход со всех устройств"},
        status_code=status.HTTP_200_OK,
    )

    response.delete_cookie(key="refresh_token", path="/")
    return response


@router.get("/v1/auth/me", summary="Информация о текущем пользователе")
async def get_current_user_info(
    current_user: int = Depends(get_current_verified_user),
) -> dict:
    return {
        "id": current_user,
        "message": "Используйте профиль для получения полной информации",
    }


@router.post("/v1/auth/cleanup-tokens", summary="Очистка просроченных токенов")
@auth_exceptions
async def cleanup_tokens(
    service: AuthService = Depends(get_auth_service),
) -> dict:
    logger.info("Cleanup expired tokens started")

    cleaned = await service.cleanup_expired_tokens()
    return {"msg": f"Очищено {cleaned} просроченных токенов"}
