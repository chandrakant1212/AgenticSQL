"""
Structured logging configuration.

Sets up application-wide logging with structured output.
Sensitive information (API keys, passwords) is redacted.
"""

import logging
import re
import sys
from typing import Any

from app.config import get_settings


class SensitiveDataFilter(logging.Filter):
    """Filter that redacts sensitive information from log messages."""

    SENSITIVE_PATTERNS = [
        (re.compile(r'(api[_-]?key\s*[=:]\s*)["\']?[\w\-]+["\']?', re.IGNORECASE), r'\1***REDACTED***'),
        (re.compile(r'(password\s*[=:]\s*)["\']?[\w\-]+["\']?', re.IGNORECASE), r'\1***REDACTED***'),
        (re.compile(r'(secret\s*[=:]\s*)["\']?[\w\-]+["\']?', re.IGNORECASE), r'\1***REDACTED***'),
        (re.compile(r'(token\s*[=:]\s*)["\']?[\w\-]+["\']?', re.IGNORECASE), r'\1***REDACTED***'),
        (re.compile(r'(sk-[a-zA-Z0-9]{20,})'), '***REDACTED_KEY***'),
        (re.compile(r'(AIza[a-zA-Z0-9_-]{35})'), '***REDACTED_KEY***'),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        """Redact sensitive data from log record."""
        if isinstance(record.msg, str):
            for pattern, replacement in self.SENSITIVE_PATTERNS:
                record.msg = pattern.sub(replacement, record.msg)
        if record.args:
            sanitized_args = []
            for arg in record.args if isinstance(record.args, tuple) else [record.args]:
                if isinstance(arg, str):
                    for pattern, replacement in self.SENSITIVE_PATTERNS:
                        arg = pattern.sub(replacement, arg)
                sanitized_args.append(arg)
            record.args = tuple(sanitized_args) if isinstance(record.args, tuple) else sanitized_args[0]
        return True


def setup_logging() -> None:
    """Configure application logging."""
    settings = get_settings()

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler with structured format
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    # Add sensitive data filter
    handler.addFilter(SensitiveDataFilter())

    root_logger.addHandler(handler)

    # Reduce noise from third-party libraries
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a named logger."""
    return logging.getLogger(name)
