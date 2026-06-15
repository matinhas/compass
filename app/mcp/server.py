from mcp.server.fastmcp import FastMCP

from app.mcp.tools.attention import get_attention
from app.mcp.tools.briefing import get_briefing
from app.mcp.tools.commitments import get_commitments, sync_roadmap
from app.mcp.tools.dashboard import get_dashboard
from app.mcp.tools.roadmap import get_roadmap
from app.mcp.tools.system_status import get_system_status

mcp = FastMCP(
    "Compass",
    instructions=(
        "Compass is the intelligence and project management system for Mirra. "
        "Use these tools to access live data from the Compass database and roadmap. "
        "Never query ClickUp, Gmail, or respond.io directly — always go through Compass."
    ),
)

mcp.add_tool(get_dashboard)
mcp.add_tool(get_briefing)
mcp.add_tool(get_attention)
mcp.add_tool(get_roadmap)
mcp.add_tool(get_commitments)
mcp.add_tool(sync_roadmap)
mcp.add_tool(get_system_status)

if __name__ == "__main__":
    mcp.run(transport="stdio")
