from app.sources.models import NormalizedCapture


class SourceProvider:
    async def fetch(self) -> list[NormalizedCapture]:
        raise NotImplementedError
