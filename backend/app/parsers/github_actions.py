from backend.app.parsers.base import NormalizedLog
from backend.app.schemas.log_ingestion import GitHubActionsLogIngest

_STATUS_TO_SEVERITY = {
    "failure": "ERROR", "timed_out": "ERROR", "action_required": "ERROR",
    "cancelled": "WARNING", "stale": "WARNING", "success": "INFO", "skipped": "INFO",
    "neutral": "INFO", "queued": "INFO", "in_progress": "INFO", "completed": "INFO",
}


class GitHubActionsParser:
    def parse(self, payload: GitHubActionsLogIngest) -> NormalizedLog:
        metadata: dict[str, object] = {"workflow_name": payload.workflow_name, "job_status": payload.job_status}
        if payload.step_failed is not None:
            metadata["step_failed"] = payload.step_failed
        failed = payload.job_status in {"failure", "timed_out", "action_required"}
        return NormalizedLog(
            payload.source, payload.timestamp, _STATUS_TO_SEVERITY[payload.job_status],
            payload.workflow_name, "workflow_failure" if failed else "workflow_job",
            payload.raw_message, metadata, payload.raw_message,
        )
