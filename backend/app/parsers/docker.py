from backend.app.parsers.base import NormalizedLog
from backend.app.schemas.log_ingestion import DockerLogIngest


class DockerParser:
    def parse(self, payload: DockerLogIngest) -> NormalizedLog:
        return NormalizedLog(
            payload.source, payload.timestamp, "ERROR" if payload.stream == "stderr" else "INFO",
            payload.container_name, "container_log", payload.raw_message,
            {"container_id": payload.container_id, "container_name": payload.container_name,
             "stream": payload.stream}, payload.raw_message,
        )
