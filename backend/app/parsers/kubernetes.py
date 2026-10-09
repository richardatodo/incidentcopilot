from backend.app.parsers.base import NormalizedLog
from backend.app.schemas.log_ingestion import KubernetesLogIngest


class KubernetesParser:
    def parse(self, payload: KubernetesLogIngest) -> NormalizedLog:
        return NormalizedLog(
            payload.source, payload.timestamp,
            "WARNING" if payload.event_type == "Warning" else "INFO",
            payload.pod_name, "kubernetes_event", payload.raw_message,
            {"pod_name": payload.pod_name, "namespace": payload.namespace,
             "source_event_type": payload.event_type, "reason": payload.reason},
            payload.raw_message,
        )
