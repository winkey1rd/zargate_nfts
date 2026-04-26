import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse

from api.app.v1 import core_router
from api.app.core.rate_limit import check_ip_rate_limit, check_token_rate_limit
from api.app.settings import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("API starting up")
    yield
    logger.info("API shutting down")


app = FastAPI(
    lifespan=lifespan,
    title="NFT Synergy API",
    version="1.0.0",
    docs_url="/swagger",
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Rate-Warning", "Retry-After"],
)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """
    Порядок проверок:
    1. IP rate limit (независимо от токена)
    2. Token rate limit (два порога: warn и block)
    """
    await check_ip_rate_limit(request)
    await check_token_rate_limit(request)

    response = await call_next(request)

    # Прокидываем предупреждение в заголовок ответа
    if getattr(request.state, "rate_warn", False):
        response.headers["X-Rate-Warning"] = "You are approaching the rate limit"

    return response


@app.middleware("http")
async def activity_log_middleware(request: Request, call_next):
    """Логируем запрос в таблицу activities после получения ответа."""
    response = await call_next(request)

    token = request.headers.get("X-Token")
    if token and hasattr(request.state, "wallet"):
        from api.app.db import _session_factory
        from nft_shared.models.user import Activity
        try:
            async with _session_factory() as session:
                activity = Activity(
                    token=token,
                    method=f"{request.method} {request.url.path}",
                    query=dict(request.query_params),
                    status=response.status_code,
                )
                session.add(activity)
                await session.commit()
        except Exception as exc:
            logger.warning(f"Failed to log activity: {exc}")

    return response


app.include_router(core_router, prefix="/api/v1")


@app.get("/", include_in_schema=False)
async def docs_redirect():
    return RedirectResponse(url="/swagger")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail},
        headers=getattr(exc, "headers", {}),
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled error: {exc}")
    return JSONResponse(status_code=500, content={"message": "Internal server error"})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=settings.ports.api_port, reload=True)