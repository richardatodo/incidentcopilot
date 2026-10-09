from fastapi import FastAPI
from fastapi.responses import JSONResponse

from backend.app.api.v1 import router as api_router
from backend.app.core.database import check_database_connection


app = FastAPI(
    title="IncidentCopilot",
    version="0.1.0",
    description="AI DevOps Incident Copilot",
)

app.include_router(api_router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/ready")
async def readiness_check():
    try:
        check_database_connection()
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready"},
        )

    return {"status": "ready"}