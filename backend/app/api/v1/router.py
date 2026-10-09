from fastapi import APIRouter

from backend.app.api.v1.incidents import router as incidents_router
from backend.app.api.v1.logs import router as logs_router


router = APIRouter(prefix="/api/v1")

router.include_router(incidents_router)
router.include_router(logs_router)