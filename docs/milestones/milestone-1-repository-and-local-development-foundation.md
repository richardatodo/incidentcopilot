# Milestone 1: Repository & Local Development Foundation

> **Project:** AI DevOps Incident Copilot (IncidentCopilot)
> **Milestone:** 1 — Repository & Local Development Foundation
> **Status:** Implementation complete pending final verification
> **Audience:** Project documentation + portfolio/blog adaptation

## 1. Introduction

IncidentCopilot is a local-first AI DevOps incident investigation system designed to help developers and DevOps/SRE engineers move from raw operational evidence to a structured, evidence-backed incident diagnosis.

The broader project will eventually ingest logs from Nginx, Kubernetes, Docker, application services, and GitHub Actions; normalize and correlate those events; construct incident timelines; retrieve relevant runbooks and historical incidents; and use a locally hosted LLM to produce a structured diagnosis.

Milestone 1 deliberately does **not** implement those capabilities. Its purpose is to establish a clean, reproducible development foundation on which later milestones can safely build.

The project's engineering principle is to build the deterministic foundation first and introduce AI only where it adds value. That means the first milestone focuses on repository structure, local configuration, backend/frontend foundations, testing, containerization, and developer workflow.

---

## 2. Milestone 1 Objectives

The approved milestone scope establishes a clean monorepo containing the future backend, frontend, runbooks, test data, evaluation assets, Docker Compose configuration, environment examples, documentation, and development tooling.

For this milestone, the implementation targets:

- Python/FastAPI backend foundation
- `/health` and `/ready` endpoints
- Environment-based configuration
- Basic pytest setup and health test
- React + TypeScript + Vite frontend
- Tailwind CSS and Lucide icons
- Minimal frontend application shell
- Backend and frontend Dockerfiles
- Initial Docker Compose architecture
- Root Makefile for common development commands
- Repository hygiene and ignore rules
- Reproducible development documentation

The milestone explicitly excludes:

- Log ingestion
- PostgreSQL models and persistence logic
- Log normalization
- Correlation logic
- Incident analysis
- RAG
- Qdrant integration
- Ollama integration
- AI diagnosis
- SSE incident updates
- Automated remediation
- AWS/cloud infrastructure
- Authentication and RBAC
- Kubernetes deployment

This scope discipline is intentional. Later functionality should be added milestone-by-milestone rather than building the entire PRD at once.

---

## 3. Repository Hygiene First

The project began with a Git repository containing an initial README and minimal repository structure. Before application development, the local repository was cleaned up and prepared for a real development workflow.

### Environment files

The project distinguishes between local secrets/configuration and shareable configuration examples:

```text
.env
.env.example
```

`.env` contains local development values and is ignored by Git.

`.env.example` contains the configuration keys required by the application without exposing the user's local values.

The repository ignore rules include:

```gitignore
.env
.env.local
.env.*.local
!.env.example
```

This provides a useful pattern for local development: developers can copy the example configuration into their own environment without committing private configuration.

### Ignore-rule correction

The original repository also contained a generic `models/` ignore rule. Because the backend architecture intentionally contains a Python package at `backend/app/models/`, that generic rule could accidentally hide source code.

It was changed to:

```gitignore
/models/
```

The leading slash makes the rule apply to the repository-root `models/` directory rather than every directory named `models`.

This is a small but important repository-hygiene lesson: ignore rules should be scoped carefully enough that they do not accidentally hide source code.

### Markdown handling

A `.gitattributes` file was added:

```gitattributes
*.md text
```

The original repository README was stored in a malformed/binary-looking form. The README was replaced with a valid UTF-8 Markdown document, and Markdown files are now explicitly treated as text by Git.

---

## 4. Python Development Environment

A Python virtual environment was created for local backend development:

```bash
python -m venv .venv
```

The environment was activated before installing the project's backend dependencies.

The initial development environment used Python 3.13. The installed backend stack includes FastAPI, Uvicorn, Pydantic Settings, pytest, and HTTPX.

The dependency set was pinned in `requirements.txt` to make local installation reproducible.

The backend package structure was created before adding application behavior:

```text
backend/
├── __init__.py
├── app/
│   ├── __init__.py
│   ├── api/
│   ├── core/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   ├── parsers/
│   ├── correlation/
│   ├── rag/
│   └── llm/
└── tests/
```

The empty packages are intentional. They establish the architectural boundaries required by the PRD without prematurely implementing later milestone functionality.

---

## 5. FastAPI Foundation

The first backend application is intentionally small.

The FastAPI application exposes:

```text
GET /health
GET /ready
```

The health endpoint returns:

```json
{"status": "ok"}
```

The readiness endpoint returns:

```json
{"status": "ready"}
```

The application metadata identifies the project as IncidentCopilot and version `0.1.0`.

The application is started locally with:

```bash
uvicorn backend.app.main:app --reload
```

The endpoints were verified during development, including the automatically generated FastAPI documentation and OpenAPI endpoint.

The backend does **not** contain log ingestion, persistence, correlation, RAG, or AI logic at this stage. Keeping `main.py` small establishes a clean entry point for later API routers and service layers.

---

## 6. Configuration Management

Configuration is handled through `pydantic-settings` in:

```text
backend/app/core/config.py
```

The current configuration surface includes:

```text
DATABASE_URL
QDRANT_URL
OLLAMA_URL
OLLAMA_MODEL
LOG_CORRELATION_WINDOW_SECONDS
RAG_TOP_K
```

The settings class loads `.env` for local development while providing sensible defaults for values that can safely have them.

This establishes the configuration mechanism before the services that will eventually consume those settings are implemented.

The important architectural decision is that application code should not hard-code environment-specific infrastructure addresses or model names.

---

## 7. Testing Foundation

A basic health test was added using FastAPI's `TestClient`:

```text
backend/tests/test_health.py
```

The test verifies both:

1. The endpoint returns HTTP 200.
2. The response body contains the expected health status.

Pytest initially could not import the `backend` package. The issue was resolved by adding the repository root to the pytest Python path through:

```ini
[pytest]
pythonpath = .
testpaths = backend/tests
```

After the fix, the health test passed successfully.

During testing, a Starlette/HTTPX deprecation warning was observed. It did not cause the test to fail and was not expanded into unnecessary dependency changes during this foundation milestone.

This is an example of maintaining milestone discipline: a non-blocking warning is recorded rather than allowing it to trigger unrelated dependency churn.

---

## 8. Frontend Foundation

The frontend was initialized as a React + TypeScript + Vite application.

The selected stack for the foundation is:

- React
- TypeScript
- Vite
- Tailwind CSS
- Lucide React
- Oxlint

The frontend source was reduced to the application pieces actually needed for the milestone:

```text
frontend/src/
├── App.tsx
├── index.css
└── main.tsx
```

The initial Vite starter documentation and unused assets were reviewed. The generated `frontend/README.md` was removed because the repository-level README is the project's authoritative development documentation.

An unused `frontend/public/icons.svg` file was also checked for references. No references were found, so it was removed.

The favicon remains because it is referenced by `frontend/index.html`.

---

## 9. Node/Vite Compatibility Issue

One of the practical issues encountered during frontend setup was a Node.js version compatibility problem.

The machine initially had Node.js `20.16.0`. The generated/current Vite toolchain required a newer Node version, so the frontend could not be used reliably with the original runtime.

Node.js was upgraded to:

```text
Node v24.21.0
npm 10.9.2
```

The frontend dependencies were then reinstalled after removing the existing `node_modules` directory and lockfile generated under the incompatible setup.

The production build subsequently completed successfully.

This is a useful development lesson: when a modern frontend toolchain reports a runtime requirement, resolve the runtime/toolchain compatibility issue before modifying application code to work around it.

---

## 10. Tailwind CSS and Lucide

Tailwind CSS was integrated through the Vite plugin, with the stylesheet importing Tailwind directly:

```css
@import "tailwindcss";
```

Lucide React provides the initial interface icons.

The first application shell intentionally uses only a small number of visual elements: an application identity area, a local-environment indicator, a milestone message, and a development-ready status element.

It is not intended to be the final IncidentCopilot dashboard.

---

## 11. Dockerizing the Backend

The backend received a dedicated Dockerfile:

```text
backend/Dockerfile
```

The image uses Python 3.13 slim, installs the pinned requirements, copies the backend package, exposes port `8000`, and starts Uvicorn on `0.0.0.0`.

The backend image also has a `.dockerignore` that excludes:

- Python caches
- pytest cache
- the local virtual environment
- local environment files
- Git metadata

This prevents local development artifacts and private configuration from unnecessarily entering the image build context.

The backend image was successfully built and the container endpoints were verified.

---

## 12. Dockerizing the Frontend

The frontend received its own Dockerfile:

```text
frontend/Dockerfile
```

The container:

1. Uses Node 24 Alpine.
2. Copies package manifests.
3. Runs `npm ci` for reproducible dependency installation.
4. Copies the source.
5. Builds the frontend.
6. Runs Vite preview on port `4173`.

The frontend also has a `.dockerignore` to exclude `node_modules`, build output, local environment files, and Git metadata.

The image was successfully built and the resulting application was verified through the exposed port.

---

## 13. Docker Compose Foundation

The root `docker-compose.yml` establishes the first local multi-service architecture:

```text
frontend → backend
```

At this milestone the Compose file intentionally contains only:

- `backend`
- `frontend`

PostgreSQL, Qdrant, and Ollama are not yet added as running services because their actual application integrations belong to later milestones.

This follows the project's no-overbuild principle: the Compose foundation should prove that the repository's application boundaries work without prematurely introducing infrastructure that the current milestone does not consume.

The Compose configuration was validated with:

```bash
docker compose config
```

The full Compose stack was also built and started successfully.

The following checks were performed against the running containers:

```text
GET http://localhost:8000/health
→ {"status":"ok"}

GET http://localhost:8000/ready
→ {"status":"ready"}

GET http://localhost:4173/
→ IncidentCopilot frontend HTML
```

The stack was subsequently stopped with:

```bash
docker compose down
```

---

## 14. Docker Desktop / Engine Issue

During the Docker portion of the milestone, Docker CLI commands initially could not be used because the Docker engine was not running.

Docker Desktop was started and the Docker context/server became available through the Linux/WSL2 backend.

The environment was then verified with Docker version and server information, after which image builds and Compose execution succeeded.

This illustrates an important distinction when debugging containers: a Dockerfile problem and a Docker engine availability problem produce very different failure modes. Before changing application/container configuration, verify that the container runtime itself is healthy.

---

## 15. Makefile Developer Workflow

A root `Makefile` was added with common commands:

```text
make backend
make frontend
make test
make build
make up
make down
```

The Windows environment did not provide the `make` command directly. `mingw32-make` was available and was used to verify the Makefile targets.

The verified targets included:

- backend startup
- frontend startup
- backend tests
- frontend production build
- Docker Compose startup
- Docker Compose shutdown

The Makefile provides a consistent developer interface while remaining simple enough for the project's local-first development model.

---

## 16. Problems Encountered and How They Were Resolved

### Problem 1: Python package import during pytest

**Symptom:** pytest could not import the `backend` package.

**Resolution:** add the repository root to the pytest Python path and explicitly define the backend test directory.

**Lesson:** test discovery and Python import paths should be established deliberately in a monorepo.

### Problem 2: Node/Vite runtime incompatibility

**Symptom:** the installed Node 20.16 runtime was below the requirement of the current Vite toolchain.

**Resolution:** upgrade Node to 24.21.0, reinstall frontend dependencies, and rebuild.

**Lesson:** keep the local runtime aligned with the selected build toolchain.

### Problem 3: Docker engine unavailable

**Symptom:** Docker commands could not reach a running engine.

**Resolution:** start Docker Desktop and verify the Docker server/context before continuing.

**Lesson:** validate the runtime before debugging container definitions.

### Problem 4: Accidental ignore of backend source directory

**Symptom:** the generic `models/` ignore rule could hide `backend/app/models/`.

**Resolution:** change the rule to `/models/`.

**Lesson:** repository ignore patterns should be scoped to their intended location.

### Problem 5: Invalid historical README representation

**Symptom:** Git initially treated the repository's original README as binary because the stored file contained NUL bytes and was not valid UTF-8 Markdown.

**Resolution:** replace it with a clean UTF-8 Markdown README and add `.gitattributes` to mark Markdown files as text.

**Lesson:** repository documentation is part of engineering quality, not an afterthought.

### Problem 6: Generated Vite files that did not belong in project documentation

**Symptom:** the generated frontend contained a generic Vite README and an unused SVG asset.

**Resolution:** inspect references, retain useful generated configuration, and remove unused/generated project-specific clutter.

**Lesson:** generated scaffolding should be reviewed rather than blindly committed.

---

## 17. Verification Performed During Milestone 1

The following checks were successfully performed during implementation:

### Backend

```bash
pytest
```

The health test passed.

The FastAPI development server was started and verified through:

```text
/health     → HTTP 200
/ready      → HTTP 200
/docs       → HTTP 200
/openapi.json → HTTP 200
```

### Frontend

The Vite development server was started and the application was visually verified in the browser.

The production build completed successfully with:

```bash
npm run build
```

### Docker

Both backend and frontend images were built successfully.

The Compose configuration was validated and the complete two-service stack was started successfully.

### Repository hygiene

The staged repository was checked with:

```bash
git diff --cached --check
```

The final check produced no output, indicating that Git's staged whitespace/error check was clean.

Generated Python cache directories were also removed after verification to keep the working tree clean.

---

## 18. Architecture Decisions Established by Milestone 1

### Local-first development

The MVP is designed to run locally and does not require AWS, Azure, GCP, paid APIs, or cloud-hosted LLM infrastructure.

### Backend separation

The backend package structure separates API, core configuration, models, schemas, services, parsers, correlation, RAG, and LLM concerns.

These boundaries are established before their full implementations are introduced.

### Deterministic-first architecture

The project's future workflow is designed around:

```text
Ingestion
→ Parsing
→ Normalization
→ Persistence
→ Correlation
→ Timeline
→ Evidence
→ RAG
→ LLM
```

Milestone 1 establishes the application foundation without bypassing this architecture by placing future AI behavior directly inside routes.

### Minimal Compose architecture

Only the services required to demonstrate the initial application boundary are included at this stage. Infrastructure for PostgreSQL, Qdrant, and Ollama belongs to the milestones where those services are actually integrated.

---

## 19. What Milestone 1 Establishes

At the end of this milestone, IncidentCopilot has a foundation that supports continued incremental development:

- A structured monorepo
- Local environment configuration
- A working FastAPI application
- Health and readiness endpoints
- Backend configuration management
- Automated backend health testing
- A React/TypeScript frontend
- Tailwind CSS styling
- Lucide icons
- Containerized backend
- Containerized frontend
- Docker Compose orchestration
- A basic developer command interface
- Repository documentation
- Git hygiene suitable for continued development

The important result is not the amount of application functionality. It is that the project now has a stable base from which the actual incident-investigation capabilities can be added without immediately accumulating architectural debt.

---

## 20. What Is Intentionally Not Implemented Yet

The following capabilities remain outside Milestone 1:

- Five-source log ingestion
- Source-specific parsers
- Common normalized event schema implementation
- PostgreSQL persistence
- Correlation engine
- Incident lifecycle
- Incident timeline
- Evidence extraction
- Qdrant vector storage
- Runbook ingestion
- Historical incident retrieval
- Ollama integration
- Structured AI diagnosis
- React incident dashboard
- SSE updates
- End-to-end incident workflow
- AI evaluation dataset
- CI/CD pipeline
- Portfolio polish for the complete system

These are not missing accidentally. They are deliberately deferred to the subsequent milestones defined by the PRD.

---

## 21. Reproducible Local Setup

A developer starting from a fresh clone should have the following prerequisites available:

- Git
- Python 3.11+
- Node.js compatible with the selected Vite toolchain
- npm
- Docker Desktop / Docker Engine
- Docker Compose

### Backend

Create and activate a virtual environment, then install:

```bash
pip install -r requirements.txt
```

Start the backend:

```bash
uvicorn backend.app.main:app --reload
```

### Frontend

Install dependencies:

```bash
cd frontend
npm install
```

Start the development server:

```bash
npm run dev
```

### Tests

From the repository root:

```bash
pytest
```

### Docker Compose

From the repository root:

```bash
docker compose up --build
```

Stop the stack with:

```bash
docker compose down
```

The root README remains the primary quick-start guide; this document provides the deeper milestone history and engineering narrative.

---

## 22. Lessons Learned

### Build the foundation before the intelligence

IncidentCopilot is an AI project, but the first milestone contains almost no AI. This is intentional. Reliable incident investigation requires trustworthy evidence, persistence, correlation, and deterministic analysis before an LLM can provide useful explanations.

### Verify each layer independently

The backend, frontend, containers, and Compose configuration were each tested separately before being considered part of the complete local stack.

### Keep generated scaffolding under control

Vite provides a useful starting point, but generated documentation and assets should be reviewed against the actual project rather than automatically becoming permanent project structure.

### Treat repository hygiene as engineering work

`.gitignore`, `.gitattributes`, environment handling, dependency locks, Docker ignore rules, newline consistency, and generated-file cleanup all affect the reliability and maintainability of the project.

### Fix root causes instead of working around symptoms

The Node/Vite issue was solved by aligning the runtime with the toolchain. The Docker issue was solved by starting and verifying the engine. The pytest import issue was solved through explicit project configuration. These are preferable to fragile workarounds in application code.

---

## 23. Portfolio Perspective

Milestone 1 may appear simple compared with the eventual AI diagnosis workflow, but it demonstrates several engineering practices that matter in a production-oriented AI system:

- disciplined scope management
- reproducible environments
- clean service boundaries
- automated testing
- containerization
- local-first development
- configuration management
- repository hygiene
- incremental architecture development
- explicit verification

The later milestones will add the more visible AI and DevOps capabilities. The foundation established here is what allows those capabilities to be developed and tested without turning the project into an unstructured prototype.

---

## 24. Conclusion

Milestone 1 establishes IncidentCopilot as a working local development project rather than just a product specification.

The repository now has a functioning backend, frontend, testing foundation, Docker foundation, developer commands, configuration strategy, and project documentation. More importantly, the implementation remains within the approved milestone scope.

The next stage can therefore focus on the first real product capability: building the FastAPI and PostgreSQL foundation required to persist and expose incident-related data, while preserving the deterministic-first and local-first principles established here.

**Milestone 1 principle:** build a clean, verifiable foundation first; add incident intelligence incrementally.
