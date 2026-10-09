from datetime import datetime
from ipaddress import IPv4Address, IPv6Address
from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.app.schemas.log import LogResponse

NonEmptyString = Annotated[str, Field(min_length=1, max_length=255)]
RawLogMessage = Annotated[str, Field(min_length=1, max_length=100_000)]


class LogIngestBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    timestamp: datetime
    raw_message: RawLogMessage

    @field_validator("timestamp")
    @classmethod
    def timestamp_must_include_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamp must include a timezone")
        return value

    @field_validator("raw_message")
    @classmethod
    def raw_message_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("raw_message must not be blank")
        return value  # Preserve the original message exactly.


class NginxLogIngest(LogIngestBase):
    source: Literal["nginx"]
    client_ip: IPv4Address | IPv6Address
    status_code: int = Field(ge=100, le=599)
    request_method: Literal["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]
    request_path: NonEmptyString
    upstream_addr: NonEmptyString | None = None


class KubernetesLogIngest(LogIngestBase):
    source: Literal["kubernetes"]
    pod_name: NonEmptyString
    namespace: NonEmptyString
    event_type: Literal["Normal", "Warning"]
    reason: NonEmptyString


class DockerLogIngest(LogIngestBase):
    source: Literal["docker"]
    container_id: NonEmptyString
    container_name: NonEmptyString
    stream: Literal["stdout", "stderr"]


class ApplicationLogIngest(LogIngestBase):
    source: Literal["application"]
    service_name: NonEmptyString
    level: Literal["TRACE", "DEBUG", "INFO", "WARN", "WARNING", "ERROR", "CRITICAL", "FATAL"]
    exception_type: NonEmptyString | None = None


class GitHubActionsLogIngest(LogIngestBase):
    source: Literal["github_actions"]
    workflow_name: NonEmptyString
    job_status: Literal[
        "queued", "in_progress", "completed", "success", "failure", "cancelled",
        "skipped", "timed_out", "action_required", "neutral", "stale",
    ]
    step_failed: NonEmptyString | None = None


LogIngestRequest = Annotated[
    Union[NginxLogIngest, KubernetesLogIngest, DockerLogIngest,
          ApplicationLogIngest, GitHubActionsLogIngest],
    Field(discriminator="source"),
]


class LogBatchIngestResponse(BaseModel):
    count: int
    logs: list[LogResponse]
