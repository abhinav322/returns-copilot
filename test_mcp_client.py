
import asyncio
import sys

from mcp import Client, StdioServerParameters


async def main():
    server = StdioServerParameters(
        command=sys.executable,
        args=["-u", "mcp_server.py"]
    )

    async with Client(server) as client:

        # Discover available tools
        tools = await client.list_tools()
        print("Available tools:", [t.name for t in tools.tools])

        # Call our first MCP tool
        result = await client.call_tool(
            "search_policy",
            {
                "query": "What is the return window for unused items?",
                "region": "UK",
                "top_k": 3
            }
        )

        print("MCP error:", result.is_error)
        print("Tool response:", result.content)


if __name__ == "__main__":
    asyncio.run(main())
