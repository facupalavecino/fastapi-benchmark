from benchmark.core.constants import LOGS_DIR


LOGGING_CONFIG = {
    "version": 1,
    "formatters": {
        "basic": {
            "format": (
                '{asctime} | level={levelname} ({filename}, line {lineno}) message="{message}"'  # noqa:E501
            ),
            "style": "{",
        },
        "console_basic": {
            "format": (
                '{asctime} | level={levelname} ({filename}, line {lineno}) message="{message}"'  # noqa:E501
            ),
            "style": "{",
        },
    },
    "handlers": {
        "file_handler": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "maxBytes": 1024 * 1024 * 10,  # 10MB
            "encoding": "utf8",
            "backupCount": 10,
            "filename": LOGS_DIR / "benchmark-api-log.log",
            "formatter": "basic",
        },
        "console_handler": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "console_basic",
        },
    },
    "loggers": {
        "benchmark": {
            "handlers": ["file_handler", "console_handler"],
            "level": "INFO",
            "propagate": True,
        }
    },
}
