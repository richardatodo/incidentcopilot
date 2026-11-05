# Milestone 5 — Incident Lifecycle & Timeline

## Implemented

Milestone 5 introduces incident creation, retrieval, lifecycle transitions, log association, and a chronological incident timeline.

### 1. Incident creation and retrieval
- Added incident creation with title and severity validation.
- New incidents start with the `OPEN` status.
- Incident titles are trimmed, and blank titles are rejected.
- Added endpoints to list incidents and retrieve an incident by ID.
- Unknown incident IDs return HTTP 404.

### 2. Incident lifecycle
Implemented explicit lifecycle transitions:

- `OPEN` → `INVESTIGATING`
- `OPEN` → `RESOLVED`
- `INVESTIGATING` → `RESOLVED`

Lifecycle behavior:
- Investigation is an explicit action; attaching logs does not change incident status.
- Repeating the investigation action is idempotent.
- Resolution records `ended_at`.
- Repeated resolution is idempotent and preserves the original `ended_at`.
- A resolved incident cannot transition back to `INVESTIGATING`; the API returns HTTP 409.

### 3. Log association
- Added an endpoint to associate existing logs with an incident.
- Supports attaching multiple logs in one request.
- Rejects duplicate log IDs and requests containing unknown logs.
- Re-evaluates deterministic correlations across the incident's complete associated log set.
- Refreshes existing association metadata when additional logs are attached.
- Stores directional correlation metadata against the later log event.
- Log association does not alter incident lifecycle status.

### 4. Incident timeline
The timeline distinguishes two event types:

- `observed_log`: an actual persisted log event, including its timestamp, source, severity, service, and message.
- `correlation`: a deterministic relationship produced by the correlation engine, including the later log ID, related earlier log ID, relationship type, relevance score, and reason.

Timeline behavior:
- Events are ordered chronologically.
- At identical timestamps, observed log events appear before derived correlation events.
- Correlation direction is preserved: `log_id` identifies the later event and `related_log_id` identifies the earlier event.
- Correlation events are recomputed from associated logs; they are not presented as AI-generated observations.

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/v1/incidents` | Create an incident |
| GET | `/api/v1/incidents` | List incidents |
| GET | `/api/v1/incidents/{incident_id}` | Retrieve an incident |
| GET | `/api/v1/incidents/{incident_id}/events` | Retrieve the incident timeline |
| POST | `/api/v1/incidents/{incident_id}/logs` | Associate logs with an incident |
| POST | `/api/v1/incidents/{incident_id}/investigate` | Move an incident into investigation |
| POST | `/api/v1/incidents/{incident_id}/resolve` | Resolve an incident |

## Files Changed

- `backend/app/api/v1/incidents.py`
- `backend/app/schemas/incident.py`
- `backend/app/services/incident_lifecycle.py` — new
- `backend/tests/test_incidents.py` — new

## Tests

Full backend test suite:

`60 passed, 1 warning in 2.53s`

The warning is a Starlette deprecation warning concerning the use of `httpx` with `starlette.testclient`. It did not cause test failures.

Verification:
- `pytest backend/tests -q` — passed.
- `git diff --check` — passed.
- `alembic check` — no new upgrade operations detected.

## Verification

The implementation was verified against the local PostgreSQL test database through the backend test suite.

The tests cover:
- Incident creation and validation.
- Incident listing and retrieval.
- Investigation and resolution transitions.
- Idempotent lifecycle operations.
- Prevention of reopening resolved incidents.
- Log association and missing-log handling.
- Timeline event generation and chronological ordering.
- Directional deterministic correlation events.

No new database migration was required because the existing database models already contained the fields and relationships needed for this milestone.

## Known Issues

- The existing Starlette/httpx test-client deprecation warning remains.
- Correlation scores are deterministic relevance heuristics, not probabilities or proof of causation.
- Timeline correlation events are derived from associated logs and the existing deterministic correlation engine. AI-generated diagnosis and interpretation remain outside this milestone.

## Architecture Notes

The milestone preserves the project's layered architecture:

- **API layer:** Defines HTTP endpoints and translates service exceptions into HTTP responses.
- **Schema layer:** Validates incoming requests and shapes API responses.
- **Service layer:** Implements incident lifecycle, log association, and timeline orchestration.
- **Domain/correlation layer:** Supplies deterministic correlation signals.
- **Persistence layer:** Uses the existing SQLAlchemy models and PostgreSQL database.

The incident lifecycle service does not introduce an LLM dependency, vector database dependency, or frontend functionality.

## Next Milestone

**Milestone 6 — Qdrant Integration & Evidence Retrieval (RAG foundation).**

The next milestone should focus on the approved Qdrant and evidence-retrieval scope. It should not introduce AI diagnosis or frontend functionality ahead of their designated milestones.

---

**Milestone status:** Functionally complete; local verification passed. Changes are not yet committed or pushed.
