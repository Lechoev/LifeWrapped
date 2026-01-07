from functools import wraps

from fastapi import HTTPException, status

from src.common import exceptions


def file_exceptions(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except exceptions.InvalidImageError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return wrapper
