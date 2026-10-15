# Milestone 4 — Normalization and Correlation Engine

**Status:** Implementation and automated tests completed locally; awaiting final review and commit approval.

## Objective

Implement a deterministic correlation engine over normalized log events, following the PRD's requirements for temporal proximity, service relationships, error signatures, severity weighting, and chronological ordering. Correlation output is an analytical signal, not proof of causation.

## Implemented

- Added a common correlation event model containing the event ID, source, timestamp, severity, service, event type, message, metadata, and original raw message.
- Added a correlation signal model with the later log's ID, related log ID, relevance score, relationship type, and an explainable reason.
- Added a deterministic `correlate_events` function with a configurable time window.
- Added matching for common error signatures, including connection-refused errors, timeouts, CrashLoopBackOff, OOMKilled, HTTP 5xx responses, and deployment failures.
- Added severity weighting so higher-severity events can increase a signal's relevance score.
- Added service identity matching using service names and selected metadata fields, including common container/pod identifiers.
- Sorted events chronologically and described earlier/later ordering in the signal reason without asserting causality.
- Added validation for positive correlation windows and timezone-aware timestamps.
- Exported the correlation models and engine from `backend.app.correlation`.

## Correlation approach

The engine combines deterministic signals for temporal proximity, service identity, error signatures, severity, and event ordering. The implemented component weights are:

| Signal | Weight |
|---|---:|
| Temporal proximity | 0.25 |
| Service relationship | 0.25 |
| Error signature | 0.25 |
| Severity | 0.15 |
| Chronological ordering | 0.10 |

The engine avoids correlating every pair merely because both events fall inside the configured time window. A pair must share a service identity or error signature, or meet the implementation's narrow high-severity/very-close-time fallback. This is a heuristic intended to reduce unrelated associations; it does not establish root cause.

Relationship labels distinguish combined signals, error-signature matches, service relationships, and temporal dependencies. Reasons include timing and matched signal details where applicable.

## Files changed

- `backend/app/correlation/__init__.py` — public exports.
- `backend/app/correlation/models.py` — immutable event and signal data models.
- `backend/app/correlation/engine.py` — deterministic correlation logic.
- `backend/tests/test_correlation.py` — correlation unit tests.

## Tests

Command executed:

```bash
pytest -vv -x
```

Result: **40 passed, 1 warning**.

The test suite includes tests for:

- Temporal correlation and explainable reasons.
- Error-signature matching.
- Severity weighting.
- Service identity matching across Kubernetes pod/container identifiers.
- Unrelated low-severity events.
- Chronological ordering.
- Events outside the correlation window.
- Invalid window values.
- Rejection of timezone-naive timestamps.
- Database metadata does not create a false service identity match.
- Kubernetes ReplicaSet-style suffix matching.
- Generic timeout signature correlation and causation disclaimer.
- Relevance scores remain between 0.0 and 1.0.

The single warning is a Starlette deprecation warning concerning use of `httpx` with `starlette.testclient`; it did not fail the test suite.

Additional command executed:

```bash
alembic check
```

Result: `No new upgrade operations detected.` No schema migration was required for this milestone.

`git diff --check` reported no whitespace errors after the package initializer was cleaned up.

## Verification and limitations

- Automated tests passed in the local development environment.
- Existing API, ingestion, health, and database tests remained passing alongside the new correlation tests.
- No database schema changes were introduced.
- This milestone adds the correlation domain logic only. It does not persist correlation signals, create incidents, construct incident timelines, expose a correlation API, or integrate Qdrant/Ollama. Those concerns remain outside this milestone's scope.
- The current rules and weights are deterministic heuristics and may produce false positives or miss relationships that are not represented by the supported signatures and service metadata.
- Correlation is not proof of causation; an earlier event is only a potential contributor to a later symptom.

## Architecture notes

The engine is implemented as a pure deterministic component, separate from API routes and persistence. It accepts normalized events and returns explainable signals, preserving the project's evidence-first principle and avoiding LLM dependence for deterministic correlation.

## Next milestone

**Milestone 5 — Incident timeline and incident lifecycle.** Do not begin it until Milestone 4 has been reviewed and explicitly approved for completion.
