import json
import logging
import os
import sys

from datetime import (
    datetime,
    timezone,
)


STRUCTURED_FIELDS = (
    "request_id",
    "method",
    "path",
    "status_code",
    "duration_ms",
    "order_number",
    "thread_id",
    "intent",
    "workflow_status",
    "source_count",
    "region",
)


class JsonFormatter(
    logging.Formatter,
):

    def format(
        self,
        record: logging.LogRecord,
    ) -> str:

        log_data = {
            "timestamp":
                datetime.now(
                    timezone.utc
                ).isoformat(),

            "level":
                record.levelname,

            "logger":
                record.name,

            "event":
                record.getMessage(),
        }

        for field in STRUCTURED_FIELDS:

            value = getattr(
                record,
                field,
                None,
            )

            if value is not None:

                log_data[field] = value


        if record.exc_info:

            log_data[
                "exception"
            ] = self.formatException(
                record.exc_info
            )


        return json.dumps(
            log_data,
            default=str,
        )


def create_app_logger() -> logging.Logger:

    logger = logging.getLogger(
        "returns_copilot"
    )

    level_name = os.getenv(
        "LOG_LEVEL",
        "INFO",
    ).upper()

    level = getattr(
        logging,
        level_name,
        logging.INFO,
    )

    logger.setLevel(
        level
    )

    logger.propagate = False


    if not logger.handlers:

        handler = logging.StreamHandler(
            sys.stdout
        )

        handler.setFormatter(
            JsonFormatter()
        )

        logger.addHandler(
            handler
        )


    return logger


logger = create_app_logger()