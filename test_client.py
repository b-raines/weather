import asyncio
import subprocess
import time
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    print("Starting server process...")
    # Start the server using mcp CLI
    server_process = subprocess.Popen(
        ["mcp", "run", "weather.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Give the server a moment to start
    print("Waiting for server to start...")
    time.sleep(2)
    
    # Check if server started successfully
    if server_process.poll() is not None:
        print("Server failed to start!")
        print("Server stdout:", server_process.stdout.read())
        print("Server stderr:", server_process.stderr.read())
        return
    
    # Initialize session and client objects
    session = None
    exit_stack = AsyncExitStack()
    
    try:
        # Set up server parameters
        server_params = StdioServerParameters(
            command="python",
            args=["weather.py"],
            env=None
        )

        # Create client transport
        stdio_transport = await exit_stack.enter_async_context(stdio_client(server_params))
        stdio, write = stdio_transport
        
        # Initialize session
        session = await exit_stack.enter_async_context(ClientSession(stdio, write))
        await session.initialize()

        # List available tools
        response = await session.list_tools()
        tools = response.tools
        print("\nConnected to server with tools:", [tool.name for tool in tools])
        
        # Test getting alerts for California
        print("\nTesting get_alerts for California...")
        result = await session.call_tool("get_alerts", {"state": "CA"})
        print("Result:", result)
        
        # Test getting forecast for San Francisco
        print("\nTesting get_forecast for San Francisco...")
        result = await session.call_tool("get_forecast", {
            "latitude": 37.7749,
            "longitude": -122.4194
        })
        print("Result:", result)
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")
    finally:
        # Clean up resources
        if session:
            await exit_stack.aclose()
        
        # Clean up the server process
        print("\nCleaning up server process...")
        server_process.terminate()
        stdout, stderr = server_process.communicate()
        print("Server stdout:", stdout)
        print("Server stderr:", stderr)

if __name__ == "__main__":
    asyncio.run(main()) 