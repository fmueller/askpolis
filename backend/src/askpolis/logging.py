import logging
import os
from logging import Logger
from typing import Any, cast

_configured = False


class AttributesAwareLogger(Logger):
    def debug_with_attrs(self: Logger, message: str, attrs: dict[str, Any]) -> None:
        return self.debug(_expand_message(message, attrs))

    def info_with_attrs(self: Logger, message: str, attrs: dict[str, Any]) -> None:
        return self.info(_expand_message(message, attrs))

    def warning_with_attrs(self: Logger, message: str, attrs: dict[str, Any]) -> None:
        return self.warning(_expand_message(message, attrs))

    def error_with_attrs(self: Logger, message: str, attrs: dict[str, Any]) -> None:
        return self.error(_expand_message(message, attrs))


def _configure_logging() -> None:
    global _configured
    if not _configured:
        logging.setLoggerClass(AttributesAwareLogger)
        _configured = True


def get_logger(name: str) -> AttributesAwareLogger:
    _configure_logging()
    logger = cast(AttributesAwareLogger, logging.getLogger(name))
    logger.setLevel(_get_log_level_from_otel_default_env_var())
    return logger


def _get_log_level_from_otel_default_env_var() -> int:
    log_level = os.getenv("OTEL_PYTHON_LOG_LEVEL", "INFO").upper().strip()
    if log_level == "INFO":
        return logging.INFO
    if log_level == "DEBUG":
        return logging.DEBUG
    if log_level == "WARNING" or log_level == "WARN":
        return logging.WARNING
    return logging.ERROR


def _expand_message(message: str, attrs: dict[str, Any]) -> str:
    attrs_str = " ".join(f"{k}={v}" for k, v in attrs.items())
    return f"{message} {attrs_str}".strip()
