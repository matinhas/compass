from app.services.system_status import check_system_health


async def get_system_status() -> dict:
    """Get Compass system health: database, roadmap sync, Gmail, and respond.io
    connectivity. Returns environment name, per-service status, and app version."""
    return await check_system_health()
