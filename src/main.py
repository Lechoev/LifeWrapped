import contextlib
from typing import AsyncIterator

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from prometheus_fastapi_instrumentator import Instrumentator

from src import conf
from src.auth_user.exceptions import AuthError
from src.auth_user.routers import router as auth_router
from src.conf.logger import get_logger
from src.goals.routers import router as goals_router
from src.profiles.routers import router as profiles_router

logger = get_logger(__name__)


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("Starting application...")
    logger.info("Initializing database connection...")
    conf.db_manager.init(conf.settings.database_url)
    logger.info("Database initialized")
    yield
    await conf.db_manager.close()


app = FastAPI(title="FastAPI", lifespan=lifespan)


@app.exception_handler(Exception)
async def internal_server_error_handler(request: Request, exc: Exception):
    logger.error(
        f"Unhandled exception: {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "client": request.client.host if request.client else None,
            "exc_type": type(exc).__name__,
        },
        exc_info=True,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Внутренняя ошибка сервера"},
    )


@app.exception_handler(AuthError)
async def auth_error_handler(request: Request, exc: AuthError):
    """
    Обработчик ошибок аутентификации.
    """
    logger.warning(
        f"Auth error: {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "client": request.client.host if request.client else None,
        },
    )

    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": str(exc)},
    )


@app.get("/")
async def start_handler():
    return {"message": "ok!"}


app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(auth_router, prefix="/auth_router")
app.include_router(profiles_router, prefix="/profiles_router")
app.include_router(goals_router, prefix="/goals_router")

instrumentator = Instrumentator()
instrumentator.instrument(app).expose(app, endpoint="/metrics")
