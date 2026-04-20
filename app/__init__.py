import logging
import sys
from types import TracebackType

logger = logging.getLogger(__name__)


def handle_uncaught_exception(
    exc_type: type[BaseException],
    exc_value: BaseException,
    exc_traceback: TracebackType | None,
) -> None:
    logger.critical(
        "uncaught exception, application will terminate.",
        exc_info=(exc_type, exc_value, exc_traceback),
    )


sys.excepthook = handle_uncaught_exception
