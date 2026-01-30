import logging
import logging.config
import os
import json

class JsonFormatter(logging.Formatter):
    """Format logs as JSON for Cloud Observability"""
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)

class SQLiteHandler(logging.Handler):
    """Custom handler to write logs to SQLite DB"""
    def emit(self, record):
        try:
            msg = self.format(record)
            # Avoid circular import by importing inside method
            from .database import insert_log 
            insert_log(record.levelname, msg)
        except Exception:
            self.handleError(record)

def setup_logging():
    # Detect environment (Production/Docker usually sets ENV=production)
    is_production = os.getenv("ENV", "development").lower() == "production"

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
            "json": {
                "()": JsonFormatter,
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "json" if is_production else "standard",
                "level": "INFO",
            },
            "file": {
                "class": "logging.FileHandler",
                "filename": "app.log",
                "formatter": "json" if is_production else "standard",
                "level": "INFO",
                "encoding": "utf-8",
            },
            "db": {
                "()": SQLiteHandler,
                "formatter": "standard", # DB can keep standard string or JSON, standard is better for simple reading
                "level": "INFO",
            },
        },
        "root": {
            "handlers": ["console", "file", "db"],
            "level": "INFO",
        },
        "loggers": {
            "uvicorn": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
        }
    }
    logging.config.dictConfig(logging_config)
    return logging.getLogger("AgenteSegPub")
