from pydantic import BaseModel


class RoadmapSyncResponse(BaseModel):
    created: int
    updated: int
    unchanged: int
