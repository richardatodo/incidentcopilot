from backend.app.parsers.base import NormalizedLog
from backend.app.schemas.log_ingestion import ApplicationLogIngest

_LEVEL_TO_SEVERITY = {
    "TRACE": "DEBUG", "DEBUG": "DEBUG", "INFO": "INFO", "WARN": "WARNING",
    "WARNING": "WARNING", "ERROR": "ERROR", "CRITICAL": "CRITICAL", "FATAL": "CRITICAL",
}


class ApplicationParser:
    def parse(self, payload: ApplicationLogIngest) -> NormalizedLog:
        metadata: dict[str, object] = {"service_name": payload.service_name, "level": payload.level}
        if payload.exception_type is not None:
            metadata["exception_type"] = payload.exception_type
        return NormalizedLog(
            payload.source, payload.timestamp, _LEVEL_TO_SEVERITY[payload.level],
            payload.service_name, "exception" if payload.exception_type else "application_log",
            payload.raw_message, metadata, payload.raw_message,
        )
