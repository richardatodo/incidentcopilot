from backend.app.parsers.base import NormalizedLog
from backend.app.schemas.log_ingestion import NginxLogIngest


class NginxParser:
    def parse(self, payload: NginxLogIngest) -> NormalizedLog:
        severity = "ERROR" if payload.status_code >= 500 else "WARNING" if payload.status_code >= 400 else "INFO"
        metadata: dict[str, object] = {
            "client_ip": str(payload.client_ip),
            "status_code": payload.status_code,
            "request_method": payload.request_method,
            "request_path": payload.request_path,
        }
        if payload.upstream_addr is not None:
            metadata["upstream_addr"] = payload.upstream_addr
        return NormalizedLog(payload.source, payload.timestamp, severity, "nginx", "http_request",
                             payload.raw_message, metadata, payload.raw_message)
