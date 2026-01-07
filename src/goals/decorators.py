from functools import wraps

from fastapi import HTTPException, status

from src.goals import exceptions


def goal_exceptions(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except exceptions.IdNotFoundError as e:
            raise HTTPException(detail=str(e), status_code=status.HTTP_400_BAD_REQUEST)
        except (exceptions.ParentNotFoundError, exceptions.GoalNotFound) as e:
            raise HTTPException(detail=str(e), status_code=status.HTTP_400_BAD_REQUEST)

    return wrapper
