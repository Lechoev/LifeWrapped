from functools import wraps

from fastapi import HTTPException, status

from src.auth_user import exceptions


def auth_exceptions(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except (
            exceptions.InvalidVerificationCodeError,
            exceptions.ExpiredVerificationCodeError,
        ) as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except exceptions.UserNotFoundError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except exceptions.RefreshTokenNotFoundError as e:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    return wrapper
