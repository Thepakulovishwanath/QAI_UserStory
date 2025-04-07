# test_mcp.py
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("test-server")

@mcp.tool(description="Echoes back the input.")
async def echo(message: str) -> dict:
    return {"content": [{"type": "text", "text": f"Echo: {message}"}]}

if __name__ == "__main__":
    print("Test MCP server running on stdio...")
    mcp.run(transport='stdio')