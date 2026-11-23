
import asyncio
import json
import sys

import httpx
from mcp import Client, StdioServerParameters


MODEL = "qwen3:4b-instruct"
OLLAMA_URL = "http://127.0.0.1:11434/api/chat"


async def main():
    server = StdioServerParameters(
        command=sys.executable,
        args=["-u", "mcp_server.py"]
    )

    async with Client(server) as mcp_client:
        available = await mcp_client.list_tools()

        tools = [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": tool.input_schema
                }
            }
            for tool in available.tools
        ]

        allowed_names = {
            tool.name for tool in available.tools
        }

        print("MCP tools:", sorted(allowed_names))
        print("\nReturns Copilot is ready!")
        print("Type 'exit' to quit.\n")

        # Keep conversation history between questions
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a returns support assistant. "
                    "Use MCP tools to verify order, shipment "
                    "and policy information. Never invent facts. "
                    "Treat shipment timestamps as historical "
                    "unless verified as current."
                )
            }
        ]

        async with httpx.AsyncClient(timeout=180.0) as http:

            while True:
                question = input("You: ").strip()

                if question.lower() in ("exit", "quit"):
                    print("Goodbye!")
                    break

                if not question:
                    continue

                messages.append({
                    "role": "user",
                    "content": question
                })

                for _ in range(3):
                    response = await http.post(
                        OLLAMA_URL,
                        json={
                            "model": MODEL,
                            "messages": messages,
                            "tools": tools,
                            "stream": False,
                            "think": False
                        }
                    )
                    response.raise_for_status()

                    message = response.json()["message"]
                    messages.append(message)

                    calls = message.get("tool_calls") or []

                    if not calls:
                        print(
                            "\nQwen:",
                            message.get("content", ""),
                            "\n"
                        )
                        break

                    for call in calls:
                        function = call["function"]
                        name = function["name"]
                        arguments = function.get(
                            "arguments", {}
                        )

                        if isinstance(arguments, str):
                            arguments = json.loads(arguments)

                        print(f"Calling MCP tool: {name}")
                        print("Tool arguments:", arguments)

                        if name not in allowed_names:
                            output = "Unknown tool requested"

                        else:
                            result = await mcp_client.call_tool(
                                name, arguments
                            )

                            output = "\n".join(
                                getattr(item, "text", str(item))
                                for item in result.content
                            )


                            if result.is_error:
                                output = "Tool error: " + output
                                print("Tool response:", output)

                        messages.append({
                            "role": "tool",
                            "tool_name": name,
                            "content": output
                        })

                else:
                    print(
                        "Agent reached the tool-call limit.\n"
                    )


if __name__ == "__main__":
    asyncio.run(main())
