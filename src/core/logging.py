import logging.config
from json import dumps

import structlog
from msgspec.json import Encoder
from settings import settings

encoder = Encoder()
logging.basicConfig(format="%(message)s", level=settings.LOGLEVEL)


def setup_logging(cache_logger_on_first_use: bool = True):
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.CallsiteParameterAdder(
            [
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.FUNC_NAME,
                structlog.processors.CallsiteParameter.LINENO,
            ],
        ),
    ]

    structlog_conf = {
        "processors": [
            structlog.stdlib.filter_by_level,
            *processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        "wrapper_class": structlog.stdlib.BoundLogger,
        "logger_factory": structlog.stdlib.LoggerFactory(),
        "cache_logger_on_first_use": cache_logger_on_first_use,
    }
    structlog.configure(**structlog_conf)

    logging_handler = "json_console" if settings.JSON_LOGS else "plain_console"
    logging_file_handler = "json_file" if settings.JSON_LOGS else "plain_file"
    logging_handlers = [logging_handler] if not settings.SAVE_LOG_FILE else [logging_handler, logging_file_handler]

    logging_handlers_list = {
        "plain_console": {"class": "logging.StreamHandler", "formatter": "plaintext_formatter"},
        "json_console": {"class": "logging.StreamHandler", "formatter": "json_formatter"},
        "null": {"class": "logging.NullHandler"},
    }

    if settings.SAVE_LOG_FILE:
        logging_handlers_list["plain_file"] = {
            "class": "logging.FileHandler",
            "formatter": "plaintext_formatter",
            "filename": settings.LOG_FILE_PATH,
            "mode": "a",
        }
        logging_handlers_list["json_file"] = {
            "class": "logging.FileHandler",
            "formatter": "json_formatter",
            "filename": settings.LOG_FILE_PATH,
            "mode": "a",
        }

    std_logging_conf = {  # noqa: ECE001
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "plaintext_formatter": {
                "()": structlog.stdlib.ProcessorFormatter,
                "foreign_pre_chain": processors,
                "processors": [
                    structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                    structlog.processors.EventRenamer("message", "_event"),
                    structlog.dev.ConsoleRenderer(colors=settings.COLORED_LOGS, event_key="message"),
                ],
            },
            "json_formatter": {
                "()": structlog.stdlib.ProcessorFormatter,
                "foreign_pre_chain": processors,
                "processors": [
                    structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                    structlog.processors.EventRenamer("message", "_event"),
                    structlog.processors.JSONRenderer(serializer=dumps),
                ],
            },
        },
        "handlers": logging_handlers_list,
        "loggers": {
            "": {"handlers": logging_handlers, "level": settings.LOGLEVEL, "propagate": True},
            "aiohttp": {"handlers": logging_handlers, "level": settings.LOGLEVEL, "propagate": True},
            "aiohttp.client": {"handlers": logging_handlers, "level": settings.LOGLEVEL, "propagate": True},
            "aiohttp.websocket": {"handlers": logging_handlers, "level": settings.LOGLEVEL, "propagate": True},
            # **(loggers_config if loggers_config else {}),
        },
    }
    logging.config.dictConfig(std_logging_conf)
