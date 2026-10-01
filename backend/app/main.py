from fastapi import FastAPI


app = FastAPI(
    title="IncidentCopilot",
    version="0.1.0",
    description="AI DevOps Incident Copilot"
)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/ready")
async def ready_check():
    return {"status": "ready"}
