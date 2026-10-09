from backend.app.parsers.application import ApplicationParser
from backend.app.parsers.base import NormalizedLog
from backend.app.parsers.docker import DockerParser
from backend.app.parsers.github_actions import GitHubActionsParser
from backend.app.parsers.kubernetes import KubernetesParser
from backend.app.parsers.nginx import NginxParser
from backend.app.schemas.log_ingestion import (
    ApplicationLogIngest, DockerLogIngest, GitHubActionsLogIngest,
    KubernetesLogIngest, LogIngestRequest, NginxLogIngest,
)


def parse_log(payload: LogIngestRequest) -> NormalizedLog:
    if isinstance(payload, NginxLogIngest):
        return NginxParser().parse(payload)
    if isinstance(payload, KubernetesLogIngest):
        return KubernetesParser().parse(payload)
    if isinstance(payload, DockerLogIngest):
        return DockerParser().parse(payload)
    if isinstance(payload, ApplicationLogIngest):
        return ApplicationParser().parse(payload)
    if isinstance(payload, GitHubActionsLogIngest):
        return GitHubActionsParser().parse(payload)
    raise ValueError(f"Unsupported log source: {payload.source}")


__all__ = ["NormalizedLog", "parse_log"]
