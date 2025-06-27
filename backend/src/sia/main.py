import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Callable, Dict

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

from .config import settings
from .routers import (
    cash,
)
from .telemetry.log import get_logger, init_logger

init_logger()
logger = get_logger(__name__)

HEALTH_CHECK_ENDPOINT = "/healthz"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Context manager for managing the lifespan of the FastAPI application.

    Initializes and shuts down application resources.
    """
    logger.info("initializing application")
    yield
    logger.info("shutdown complete")


app = FastAPI(
    version="0.1.0",
    lifespan=lifespan,
)

# NOTE: Uncomment if CORS needed
# Add CORS middleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=settings.cors_allow_origins,
#     # allow_credentials=True,
#     allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
#     allow_headers=["*"],
# )


@app.middleware("http")
async def log_requests(request: Request, call_next: Callable) -> Response:
    """
    Middleware to log incoming HTTP requests.

    Skips logging for health check endpoint.
    """
    if request.url.path == HEALTH_CHECK_ENDPOINT:
        return await call_next(request)

    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(
        path=request.url.path,
        method=request.method,
        status_code=response.status_code,
        processing_time_ms=round(process_time * 1000, 2),
    )
    return response


@app.middleware("http")
async def add_security_headers(request: Request, call_next: Callable) -> Response:
    """Middleware to add security headers to HTTP responses."""
    response = await call_next(request)
    if settings.enable_security_headers:
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
    return response


@app.exception_handler(Exception)
async def global_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    """Global exception handler to catch and log unhandled exceptions."""
    # logger.info(f"Unhandled exception: {str(exc)}", exc_info=exc)
    logger.info(f"Unhandled exception: {exc!s}")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get(HEALTH_CHECK_ENDPOINT)
async def health_check() -> Dict:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "environment": settings.app_env,
    }


@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint."""
    return {"message": "who's the #1 under18 don?"}


# routers
app.include_router(cash.router, prefix=settings.api_v1_prefix)


def main() -> None:
    """Run the FastAPI application using Uvicorn."""
    # NOTE: uvicorn handles the signals for us
    uvicorn.run(
        "sia.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        access_log=False,
        log_level=settings.log_level.lower(),
        # tell uvicorn to be aware of the proxy and
        # to trust the headers it sends, needed because fastapi sends that back
        # to the client
        proxy_headers=settings.proxy_header,
        forwarded_allow_ips=settings.trusted_ip,
    )


if __name__ == "__main__":
    main()
