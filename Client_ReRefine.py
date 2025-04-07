# import asyncio
# import sys
# import json
# from typing import Optional
# from contextlib import AsyncExitStack

# from mcp import ClientSession, StdioServerParameters
# from mcp.client.stdio import stdio_client
# from dotenv import load_dotenv

# load_dotenv()

# class MCPClient:
#     def __init__(self):
#         self.session: Optional[ClientSession] = None
#         self.exit_stack = AsyncExitStack()

#     async def connect_to_server(self, server_script_path: str):
#         if not server_script_path.endswith('.py'):
#             raise ValueError("Server script must be a .py file")

#         server_params = StdioServerParameters(
#             command="python3",
#             args=[server_script_path],
#             env=None
#         )

#         print("Connecting to server...")
#         stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
#         self.stdio, self.write = stdio_transport
#         self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

#         await self.session.initialize()

#         response = await self.session.list_tools()
#         tools = response.tools
#         print("\nConnected to server with tools:", [tool.name for tool in tools])

#     async def process_query(self, tool_name: str, tool_args: dict) -> str:
#         print(f"Calling tool '{tool_name}' with args: {tool_args}")
#         result = await self.session.call_tool(tool_name, tool_args)
#         return result.content

#     async def chat_loop(self):
#         print("\nMCP Client Started!")
#         print("Type 'quit' to exit. Example input: invest_analyze {\"user_story\": {\"UserStory\": {\"Title\": \"Test\", ...}}}")

#         while True:
#             try:
#                 query = input("\nCommand: ").strip()
#                 if query.lower() == 'quit':
#                     break

#                 parts = query.split(maxsplit=1)
#                 if len(parts) < 2:
#                     print("Please provide a tool name and arguments (e.g., 'invest_analyze {...}')")
#                     continue
                
#                 tool_name, args_str = parts
#                 try:
#                     tool_args = json.loads(args_str)  # Use json.loads instead of eval
#                     if not isinstance(tool_args, dict):
#                         raise ValueError("Arguments must be a dictionary")
#                 except json.JSONDecodeError as e:
#                     print(f"Error parsing JSON arguments: {str(e)}")
#                     continue

#                 response = await self.process_query(tool_name, tool_args)
#                 print("\nResponse:")
#                 print(response)

#             except Exception as e:
#                 print(f"\nError: {str(e)}")

#     async def cleanup(self):
#         await self.exit_stack.aclose()

# async def main():
#     if len(sys.argv) < 2:
#         print("Usage: python3 client.py <path_to_server_script>")
#         sys.exit(1)

#     client = MCPClient()
#     try:
#         await client.connect_to_server(sys.argv[1])
#         await client.chat_loop()
#     finally:
#         await client.cleanup()

# if __name__ == "__main__":
#     asyncio.run(main())









# import asyncio
# import sys
# import json
# from typing import Optional
# from contextlib import AsyncExitStack

# from mcp import ClientSession, StdioServerParameters
# from mcp.client.stdio import stdio_client
# from dotenv import load_dotenv

# load_dotenv()

# class MCPClient:
#     def __init__(self):
#         self.session: Optional[ClientSession] = None
#         self.exit_stack = AsyncExitStack()

#     async def connect_to_server(self, server_script_path: str):
#         if not server_script_path.endswith('.py'):
#             raise ValueError("Server script must be a .py file")

#         server_params = StdioServerParameters(
#             command="python3",
#             args=[server_script_path],
#             env=None
#         )

#         print("Connecting to server...")
#         stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
#         self.stdio, self.write = stdio_transport
#         self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

#         await self.session.initialize()

#         response = await self.session.list_tools()
#         tools = response.tools
#         print("\nConnected to server with tools:", [tool.name for tool in tools])

#     async def process_query(self, tool_name: str, tool_args: dict) -> str:
#         print(f"Calling tool '{tool_name}' with args: {tool_args}")
#         result = await self.session.call_tool(tool_name, tool_args)
#         # Extract the core JSON from the content list
#         for item in result.content:
#             if item.get("type") == "json" and "json" in item:
#                 return json.dumps(item["json"], indent=2)  # Return only the core INVEST data as a formatted string
#         return json.dumps(result.content, indent=2)  # Fallback to full content if no json type found

#     # async def process_query(self, tool_name: str, tool_args: dict) -> str:
#     #     print(f"Calling tool '{tool_name}' with args: {tool_args}")
#     #     result = await self.session.call_tool(tool_name, tool_args)
#     #     print(f"Result content: {result.content}")
#     #     for item in result.content:
#     #         if hasattr(item, 'type') and item.type == "json" and hasattr(item, 'text'):
#     #             core_json = json.loads(item.text)
#     #             return json.dumps(core_json, indent=2)
#     #     return json.dumps(result.content, indent=2)

#     async def chat_loop(self):
#         print("\nMCP Client Started!")
#         print("Type 'quit' to exit. Example input: invest_analyze {\"user_story\": {\"UserStory\": {\"Title\": \"Test\", ...}}}")

#         while True:
#             try:
#                 query = input("\nCommand: ").strip()
#                 if query.lower() == 'quit':
#                     break

#                 parts = query.split(maxsplit=1)
#                 if len(parts) < 2:
#                     print("Please provide a tool name and arguments (e.g., 'invest_analyze {...}')")
#                     continue
                
#                 tool_name, args_str = parts
#                 try:
#                     tool_args = json.loads(args_str)
#                     if not isinstance(tool_args, dict):
#                         raise ValueError("Arguments must be a dictionary")
#                 except json.JSONDecodeError as e:
#                     print(f"Error parsing JSON arguments: {str(e)}")
#                     continue

#                 response = await self.process_query(tool_name, tool_args)
#                 print("\nResponse:")
#                 print(response)

#             except Exception as e:
#                 print(f"\nError: {str(e)}")

#     async def cleanup(self):
#         await self.exit_stack.aclose()

# async def main():
#     if len(sys.argv) < 2:
#         print("Usage: python3 client.py <path_to_server_script>")
#         sys.exit(1)

#     client = MCPClient()
#     try:
#         await client.connect_to_server(sys.argv[1])
#         await client.chat_loop()
#     finally:
#         await client.cleanup()

# if __name__ == "__main__":
#     asyncio.run(main())















# import asyncio
# import sys
# import json
# from typing import Optional
# from contextlib import AsyncExitStack

# from mcp import ClientSession, StdioServerParameters
# from mcp.client.stdio import stdio_client
# from dotenv import load_dotenv

# load_dotenv()

# class MCPClient:
#     def __init__(self):
#         self.session: Optional[ClientSession] = None
#         self.exit_stack = AsyncExitStack()

#     async def connect_to_server(self, server_script_path: str):
#         if not server_script_path.endswith('.py'):
#             raise ValueError("Server script must be a .py file")

#         server_params = StdioServerParameters(
#             command="python3",
#             args=[server_script_path],
#             env=None
#         )

#         print("Connecting to server...")
#         stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
#         self.stdio, self.write = stdio_transport
#         self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

#         await self.session.initialize()

#         response = await self.session.list_tools()
#         tools = response.tools
#         print("\nConnected to server with tools:", [tool.name for tool in tools])

#     async def process_query(self, tool_name: str, tool_args: dict) -> str:
#         print(f"Calling tool '{tool_name}' with args: {tool_args}")
#         result = await self.session.call_tool(tool_name, tool_args)
#         for item in result.content:
#             if hasattr(item, 'type') and item.type == "json" and hasattr(item, 'text'):
#                 core_json = json.loads(item.text)
#                 return json.dumps(core_json, indent=2)
#         # Fallback: Convert TextContent objects to serializable dicts
#         serializable_content = [
#             {"type": item.type, "text": item.text} if hasattr(item, 'type') and hasattr(item, 'text') else str(item)
#             for item in result.content
#         ]
#         return json.dumps(serializable_content, indent=2)

#     async def chat_loop(self):
#         print("\nMCP Client Started!")
#         print("Type 'quit' to exit. Example input: invest_analyze {\"user_story\": {\"UserStory\": {\"Title\": \"Test\", ...}}}")

#         while True:
#             try:
#                 query = input("\nCommand: ").strip()
#                 if query.lower() == 'quit':
#                     break

#                 parts = query.split(maxsplit=1)
#                 if len(parts) < 2:
#                     print("Please provide a tool name and arguments (e.g., 'invest_analyze {...}')")
#                     continue
                
#                 tool_name, args_str = parts
#                 try:
#                     tool_args = json.loads(args_str)
#                     if not isinstance(tool_args, dict):
#                         raise ValueError("Arguments must be a dictionary")
#                 except json.JSONDecodeError as e:
#                     print(f"Error parsing JSON arguments: {str(e)}")
#                     continue

#                 response = await self.process_query(tool_name, tool_args)
#                 print("\nResponse:")
#                 print(response)

#             except Exception as e:
#                 print(f"\nError: {str(e)}")

#     async def cleanup(self):
#         await self.exit_stack.aclose()

# async def main():
#     if len(sys.argv) < 2:
#         print("Usage: python3 client.py <path_to_server_script>")
#         sys.exit(1)

#     client = MCPClient()
#     try:
#         await client.connect_to_server(sys.argv[1])
#         await client.chat_loop()
#     finally:
#         await client.cleanup()

# if __name__ == "__main__":
#     asyncio.run(main())



















import asyncio
import sys
import json
from typing import Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv

load_dotenv()

class MCPClient:
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()

    async def connect_to_server(self, server_script_path: str):
        if not server_script_path.endswith('.py'):
            raise ValueError("Server script must be a .py file")

        server_params = StdioServerParameters(
            command="python3",
            args=[server_script_path],
            env=None
        )

        print("Connecting to server...")
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

        await self.session.initialize()

        response = await self.session.list_tools()
        tools = response.tools
        print("\nConnected to server with tools:", [tool.name for tool in tools])

    async def process_query(self, tool_name: str, tool_args: dict) -> str:
        print(f"Calling tool '{tool_name}' with args: {tool_args}")
        result = await self.session.call_tool(tool_name, tool_args)
        for item in result.content:
            if hasattr(item, 'type') and item.type == "text" and hasattr(item, 'text'):
                # Parse the text field as JSON and return it formatted without escapes
                core_json = json.loads(item.text)
                return json.dumps(core_json, indent=2, ensure_ascii=False)
        # Fallback: Convert TextContent objects to serializable dicts
        serializable_content = [
            {"type": item.type, "text": item.text} if hasattr(item, 'type') and hasattr(item, 'text') else str(item)
            for item in result.content
        ]
        return json.dumps(serializable_content, indent=2, ensure_ascii=False)

    async def chat_loop(self):
        print("\nMCP Client Started!")
        print("Type 'quit' to exit. Example input: invest_analyze {\"user_story\": {\"UserStory\": {\"Title\": \"Test\", ...}}}")

        while True:
            try:
                query = input("\nCommand: ").strip()
                if query.lower() == 'quit':
                    break

                parts = query.split(maxsplit=1)
                if len(parts) < 2:
                    print("Please provide a tool name and arguments (e.g., 'invest_analyze {...}')")
                    continue
                
                tool_name, args_str = parts
                try:
                    tool_args = json.loads(args_str)
                    if not isinstance(tool_args, dict):
                        raise ValueError("Arguments must be a dictionary")
                except json.JSONDecodeError as e:
                    print(f"Error parsing JSON arguments: {str(e)}")
                    continue

                response = await self.process_query(tool_name, tool_args)
                print("\nResponse:")
                print(response)

            except Exception as e:
                print(f"\nError: {str(e)}")

    async def cleanup(self):
        await self.exit_stack.aclose()

async def main():
    if len(sys.argv) < 2:
        print("Usage: python3 client.py <path_to_server_script>")
        sys.exit(1)

    client = MCPClient()
    try:
        await client.connect_to_server(sys.argv[1])
        await client.chat_loop()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(main())