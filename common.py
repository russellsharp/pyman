import logging
import sys
from typing import Any


def patch_logger_with_trace():
    TRACE_LEVEL_NUM = 5

    logging.addLevelName(TRACE_LEVEL_NUM, "TRACE")

    def trace(self: logging.Logger, message: str, *args: Any, **kws: dict[str, Any]):
        if self.isEnabledFor(TRACE_LEVEL_NUM):
            self._log(TRACE_LEVEL_NUM, message, args, **kws)  # type: ignore

    logging.Logger.trace = trace  # type: ignore


_root_logger: logging.Logger | None = None


def setup_logger(module_name: str = __name__, level: int = logging.INFO) -> logging.Logger:
    global _root_logger

    if _root_logger is None:
        _root_logger = logging.getLogger()
        console_handler = logging.StreamHandler(sys.stdout)
        _root_logger.addHandler(console_handler)
        patch_logger_with_trace()
    logger = logging.getLogger(module_name)
    logger.setLevel(level)

    return logger


class InPlaceStreamHandler(logging.StreamHandler):  # type: ignore
    """A logging handler that overwrites the current terminal line."""

    def emit(self, record: logging.LogRecord):
        try:
            msg = self.format(record)
            stream = self.stream
            # \r moves the cursor back to the start of the line
            stream.write(f"\r{msg}")
            self.flush()
        except Exception:
            self.handleError(record)
