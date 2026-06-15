from fastapi import FastAPI

from app.api.capture import router as capture_router
from app.api.briefing import router as briefing_router

app = FastAPI(title="Compass", version="0.1.0", description="Capture → ClickUp pipeline")


@app.get("/health", tags=["system"])
def health():
    return {"status": "ok"}


app.include_router(capture_router)
app.include_router(briefing_router)
