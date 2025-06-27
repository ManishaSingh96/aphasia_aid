import os
from enum import StrEnum

from pydantic_settings import BaseSettings

app_prefix = "sia_".upper()


class Environment(StrEnum):
    """Enumeration for application environments."""

    PRODUCTION = "production"
    DEVELOPMENT = "development"


class Settings(BaseSettings):
    """Application settings."""

    app_env: str = os.getenv(f"{app_prefix}APP_ENV", Environment.DEVELOPMENT)
    debug: bool = app_env == Environment.DEVELOPMENT
    reload: bool = app_env == Environment.DEVELOPMENT
    proxy_header: bool = app_env == Environment.PRODUCTION
    enable_security_headers: bool = app_env == Environment.PRODUCTION
    log_level: str = "DEBUG" if app_env == Environment.DEVELOPMENT else "INFO"

    # TODO: The reverse proxy IP setting needs be scoped down from "*", but
    # there's some issue with my caddy reverse proxy so there needs to be some
    # more testing before I can ensure this is working as expected.
    trusted_ip: str = os.getenv(f"{app_prefix}REVERSE_PROXY_IP", "*")

    # API settings
    cors_allow_origins: list[str] = os.getenv(
        f"{app_prefix}CORS_ALLOW_ORIGINS",
        "*",
    ).split(",")
    api_v1_prefix: str = os.getenv(f"{app_prefix}API_V1_PREFIX", "/api/v1")
    host: str = os.getenv(
        f"{app_prefix}HOST",
        # binding to all interfaces is intentional for deployment behind a
        # reverse proxy.
        "0.0.0.0",  # noqa: S104 # nosec B104
    )
    port: int = int(os.getenv(f"{app_prefix}PORT", "8000"))


settings = Settings()
