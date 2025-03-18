import os
import sys

import asyncio
from typing import Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from dotenv import load_dotenv

session: Optional[ClientSession] = None
exit_stack = AsyncExitStack()

async def connect_to_server(server_script_path: str = "./weather.py", venv_path: Optional[str] = "./venv"):
    """Connect to an MCP server
    
    Args:
        server_script_path: Path to the server script (.py or .js)
    """
    is_python = server_script_path.endswith('.py')
    is_js = server_script_path.endswith('.js')
    if not (is_python or is_js):
        raise ValueError("Server script must be a .py or .js file")
        

    command = "python" if is_python else "node"
    # Determine the command based on the script type
    if is_python:
        # If a virtual environment path is provided, use the Python interpreter from the virtual environment
        if venv_path:
            # Construct the path to the Python interpreter in the virtual environment
            if sys.platform == 'win32':
                # Windows
                python_executable = os.path.join(venv_path, 'Scripts', 'python.exe')
            else:
                # macOS and Linux
                python_executable = os.path.join(venv_path, 'bin', 'python')
            # Check if the Python interpreter exists
            if not os.path.exists(python_executable):
                raise ValueError(f"Python interpreter not found in virtual environment: {python_executable}")
            command = python_executable
        else:
            # Use the system Python interpreter
            command = "python"
    else:
        command = "node"
    
    # Set up the environment variables if using a virtual environment
    env = os.environ.copy()
    if venv_path:
        # Add the virtual environment's bin directory to the PATH
        if sys.platform == 'win32':
            # Windows
            env['PATH'] = os.path.join(venv_path, 'Scripts') + os.pathsep + env['PATH']
        else:
            # macOS and Linux
            env['PATH'] = os.path.join(venv_path, 'bin') + os.pathsep + env['PATH']
    
    server_params = StdioServerParameters(
        command=command,
        args=[server_script_path],
        env=env
    )
    
    try:
        stdio_transport = await exit_stack.enter_async_context(stdio_client(server_params))
        stdio, write = stdio_transport
        session = await exit_stack.enter_async_context(ClientSession(stdio, write))
        
        await session.initialize()
        
        # List available tools
        response = await session.list_tools()
        tools = response.tools
        available_tools = [{ 
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.inputSchema
        } for tool in response.tools]

        print("\nConnected to server with tools:", [tool.name for tool in tools])
        print(available_tools)
    except Exception as e:
        print(f"An error occurred while connecting to the server: {e}")
        raise

    tool_name = "test_func"
    tool_args = {
        "test_str" : "this is a test"
    }
    result = await session.call_tool(tool_name, tool_args)
    print("="*20, "\n", [{
                    "role": "user", 
                    "content": result.content
                }])

async def main():
    # if len(sys.argv) < 2:
    #     print("Usage: python client.py ./weather.py")
    #     sys.exit(1)

    try:
        await connect_to_server()

    finally:
        await exit_stack.aclose()

if __name__ == "__main__":
    # import sys
    asyncio.run(main())