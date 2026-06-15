import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.capture import router as capture_router
from app.api.briefing import router as briefing_router
from app.api.attention import router as attention_router
from app.api.dashboard import router as dashboard_router
from app.api.integrations import router as integrations_router
from app.api.sync import router as sync_router
from app.mcp.server import mcp as compass_mcp

logger = logging.getLogger(__name__)

_SYNC_INTERVAL_SECONDS = 1800  # 30 minutes


async def _sync_loop() -> None:
    from app.services.roadmap_sync import RoadmapSyncService
    while True:
        await asyncio.sleep(_SYNC_INTERVAL_SECONDS)
        try:
            result = await RoadmapSyncService().sync()
            logger.info("Auto-sync: created=%d updated=%d unchanged=%d", result.created, result.updated, result.unchanged)
        except Exception as e:
            logger.warning("Auto-sync failed: %s", e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(_sync_loop())
    async with compass_mcp.session_manager.run():
        yield
    task.cancel()


app = FastAPI(title="Compass", version="0.1.0", description="Capture → ClickUp pipeline", lifespan=lifespan)


@app.get("/health", tags=["system"])
def health():
    return {"status": "ok"}


app.include_router(capture_router)
app.include_router(briefing_router)
app.include_router(attention_router)
app.include_router(dashboard_router)
app.include_router(integrations_router)
app.include_router(sync_router)
app.mount("/mcp", compass_mcp.streamable_http_app())
