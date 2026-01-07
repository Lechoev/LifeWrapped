from functools import wraps

from fastapi import HTTPException, status

from src.profiles import exceptions


def profile_exceptions(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except exceptions.ProfileNotFoundError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except exceptions.ProfileAlreadyExistsError as e:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    return wrapper
