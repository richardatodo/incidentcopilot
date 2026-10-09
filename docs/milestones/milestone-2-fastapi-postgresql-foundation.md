# Milestone 2: FastAPI Foundation and PostgreSQL

## Overview

Milestone 2 establishes the persistence and API foundation for IncidentCopilot, a local-first AI DevOps incident investigation platform.

The implementation introduces PostgreSQL as the relational database, SQLAlchemy for ORM-based database access, Alembic for versioned schema migrations, and versioned API endpoints for listing incidents and logs.

The milestone deliberately does not implement log ingestion, incident correlation, vector search, or AI-powered diagnosis.

## 1. Architecture

The application follows this request flow:

```text
HTTP Request
     |
     v
FastAPI Application
     |
     v
Versioned API Router
     |
     v
SQLAlchemy Session
     |
     v
PostgreSQL
```

Database access is managed through a shared SQLAlchemy engine and session factory. API endpoints obtain database sessions through FastAPI dependency injection.

Schema changes are managed through Alembic migrations rather than application startup code.

## 2. Database Foundation

PostgreSQL 16 runs as a Docker Compose service with a persistent named volume.

SQLAlchemy models were introduced for six database tables:

| Model | Purpose |
|---|---|
| `Incident` | Stores incident details, severity, status, and timestamps |
| `Log` | Stores log records and their normalized fields |
| `IncidentLog` | Associates incidents with logs |
| `Diagnosis` | Stores structured incident diagnosis results |
| `Evidence` | Associates diagnosis records with supporting logs |
| `InvestigationStep` | Stores ordered investigation steps and their statuses |

UUID identifiers are used for the primary entities. Relationships are represented using foreign keys, and PostgreSQL-specific JSONB columns support structured log metadata and diagnosis responses.

The schema was generated and applied through an initial Alembic migration.

**Initial migration:** `49464b6f3ff9`

The migration was confirmed as the current database revision, and Alembic reported no new upgrade operations.

## 3. API Endpoints

### Health check

`GET /health`

Returns a basic application health response:

```json
{
  "status": "ok"
}
```

This endpoint checks application availability without requiring a database query.

### Readiness check

`GET /ready`

Checks whether the application can connect to PostgreSQL.

When the database connection succeeds, the endpoint returns:

```json
{
  "status": "ready"
}
```

When the database connection fails, the endpoint returns HTTP 503 with a `not_ready` status.

### List incidents

`GET /api/v1/incidents`

Returns incidents ordered by creation time, newest first.

The endpoint currently returns an empty JSON array when no incidents exist.

### List logs

`GET /api/v1/logs`

Returns logs ordered by timestamp, newest first.

The endpoint currently returns an empty JSON array when no logs exist.

Pydantic response schemas define the API response contracts for incidents and logs.

## 4. Local and Docker Configuration

During verification, a database connection failure revealed that `localhost` inside the backend container referred to the backend container itself rather than PostgreSQL.

The configuration was separated into two environment files:

- `.env` supports running the FastAPI application directly on the host, using `localhost` for PostgreSQL.
- `.env.docker` supplies the Docker backend with a database URL using `postgres`, the Compose service hostname.

The Compose definition references `.env.docker` through `env_file`. PostgreSQL settings are supplied through Compose variable interpolation rather than embedding the database password directly in the Compose YAML.

Both environment files are excluded by `.gitignore` and were confirmed to be untracked.

`.env.example` provides a configuration template for developers setting up their own local environment.

Local development credentials must remain development-only. The database password in the backend connection URL must match the password configured for the PostgreSQL service.

## 5. Testing and Verification

### Automated tests

The backend test suite was executed using:

```bash
pytest -q
```

**Result: 6 passed, 1 warning.**

The tests cover:

- Application health and readiness endpoints.
- Empty incident and log collection responses.
- Database connectivity.
- Registration of the expected database tables.

### Migration verification

The following commands were executed:

```bash
alembic current
alembic check
```

Results:

- Current migration: `49464b6f3ff9 (head)`
- Schema comparison: `No new upgrade operations detected.`

### Docker verification

The following checks were performed:

```bash
docker compose config --quiet
docker compose up -d --force-recreate
docker compose ps
```

The backend, frontend, and PostgreSQL containers started successfully. PostgreSQL reported a healthy status.

The backend container's database hostname was verified as `postgres`.

The following endpoints were also tested against the running Docker application:

- `/health`
- `/ready`
- `/api/v1/incidents`
- `/api/v1/logs`

The readiness endpoint returned `{"status":"ready"}`, and the incident and log endpoints returned empty arrays.

### Repository hygiene

`git diff --check` reported no whitespace errors. Git displayed a warning about potential LF-to-CRLF conversion for `docker-compose.yml`; this should be reviewed before committing.

## 6. Known Issues and Limitations

1. **Dependency deprecation warning:** The test suite reports a Starlette deprecation warning involving `httpx` and `starlette.testclient`. The tests pass, but dependency compatibility should be reviewed before upgrading packages.
2. **Line endings:** Git reports a potential line-ending conversion for `docker-compose.yml` on Windows.
3. **Empty collections:** No log ingestion or incident creation workflow has been implemented yet. Empty API collections are expected.
4. **Database configuration:** Developers must configure the local and Docker database URLs correctly and keep credentials consistent.
5. **No ingestion or diagnosis:** Log parsing, normalization, incident correlation, Qdrant retrieval, and Ollama diagnosis remain outside this milestone's scope.

## 7. Architecture Decisions

- PostgreSQL remains the relational persistence layer.
- SQLAlchemy provides database access and ORM mapping.
- Alembic provides explicit, version-controlled schema changes.
- UUIDs identify primary entities.
- Pydantic schemas define API response contracts.
- Database sessions are injected into endpoints through FastAPI dependencies.
- Docker and host development use distinct database hostnames.
- Health and readiness are separate checks so application availability is distinguishable from database readiness.
- The application remains local-first and does not require AWS or a cloud-hosted database.

## 8. Conclusion

Milestone 2 establishes the database-backed API foundation required for subsequent incident investigation capabilities.

The database schema is migrated, the API endpoints respond as expected, Docker connectivity is verified, and the backend test suite passes.

The implementation remains intentionally limited to persistence and API foundations.

## Next Milestone

**Milestone 3: Multi-source Log Ingestion**

The next milestone will introduce log ingestion from the supported sources defined in the PRD. Work should begin only after Milestone 2 changes and documentation have been reviewed and approved.
