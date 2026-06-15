import httpx
from fastapi import APIRouter, HTTPException

from app.schemas.sync import RoadmapSyncResponse
from app.services.roadmap_sync import RoadmapSyncService

router = APIRouter(prefix="/sync", tags=["sync"])


@router.post("/roadmap", response_model=RoadmapSyncResponse)
async def sync_roadmap():
    service = RoadmapSyncService()
    try:
        result = await service.sync()
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=502,
            detail=f"ClickUp API error: {e.response.status_code}",
        )
    return RoadmapSyncResponse(
        created=result.created,
        updated=result.updated,
        unchanged=result.unchanged,
    )
