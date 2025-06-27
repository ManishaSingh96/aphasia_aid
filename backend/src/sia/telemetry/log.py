import logging
import os
import sys
from typing import Iterable, Optional

import structlog
from structlog.typing import Processor

# NOTE: Usage
# In the main init file:
# from src.<package_name>.log import get_logger, init_logger
# init_logger()
# logger = get_logger(__name__)
#
# In different files:
# from src.<package_name>.log import get_logger
# logger = get_logger(__name__)


def setup_stdlogger() -> None:
    """Set up standard logging configuration."""
    datefmt = "%d-%m-%Y %I:%M:%S %p"
    format_str = "[%(name)s] [%(levelname)s] %(message)s"
    logging.basicConfig(
        format=format_str,
        stream=sys.stdout,  # https://12factor.net/logs
        level=os.getenv("LOGLEVEL", logging.INFO),
        datefmt=datefmt,
    )
    # NOTE: We can supress unwanted library logs here
    # logging.getLogger("httpx").setLevel(logging.WARNING)
    # logging.getLogger("hamilton.async_driver").setLevel(logging.FATAL)
    # logging.getLogger("hamilton.telemetry").setLevel(logging.WARNING)
    # logging.getLogger("hpack").setLevel(logging.FATAL)
    # logging.getLogger("httpcore").setLevel(logging.FATAL)
    # logging.getLogger("openai").setLevel(logging.FATAL)
    # logging.getLogger("botocore").setLevel(logging.FATAL)
    # logging.getLogger("aiobotocore").setLevel(logging.FATAL)


def get_structlog_processors() -> Iterable[Processor]:
    """Get structlog processors based on environment."""
    processors: Iterable[Processor] = [
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M.%S"),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.CallsiteParameterAdder(
            {
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.FUNC_NAME,
                structlog.processors.CallsiteParameter.LINENO,
            },
        ),
    ]
    if sys.stderr.isatty():
        return [*processors, structlog.dev.ConsoleRenderer()]  # type: ignore
    else:
        return [  # type: ignore
            *processors,
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]


def setup_structlog() -> None:
    """Configure structlog."""
    structlog.configure(
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
        wrapper_class=structlog.BoundLogger,
        processors=get_structlog_processors(),
    )


def init_logger() -> None:
    """Initialize both standard logging and structlog."""
    setup_stdlogger()
    setup_structlog()


def get_logger(name: Optional[str] = None) -> structlog.BoundLogger:
    """
    Get a structlog logger instance.

    If no name is provided, it attempts to infer the caller's module name.
    """
    if name is None:
        import inspect

        frame = inspect.currentframe()
        if frame:
            try:
                frame = frame.f_back
                if frame:
                    name = frame.f_globals["__name__"]
            finally:
                del frame

    return structlog.get_logger(name)
