from fastapi import FastAPI

from app.api.capture import router as capture_router
from app.api.briefing import router as briefing_router
from app.api.attention import router as attention_router
from app.api.dashboard import router as dashboard_router
from app.api.integrations import router as integrations_router
from app.api.sync import router as sync_router
from app.mcp.server import mcp as compass_mcp

app = FastAPI(title="Compass", version="0.1.0", description="Capture → ClickUp pipeline")


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
