"""
Example of how to use MCPilot Gateway programmatically
"""
import asyncio
import httpx
from mcpilot.config import Settings, MCPServerConfig, APIWrapperConfig
from mcpilot.gateway import MCPGateway


async def example_usage():
    """Example of using MCPilot Gateway"""
    
    # Create settings with example configurations
    settings = Settings(
        mcp_servers=[
            # Example stdio MCP server
            MCPServerConfig(
                name="notes-server",
                type="stdio",
                command="python",
                args=["-m", "mcpilot.server"],  # Use our built-in server as example
                enabled=True
            ),
            # Example HTTP MCP server (uncomment if you have one)
            # MCPServerConfig(
            #     name="http-server",
            #     type="http",
            #     url="http://localhost:3000/mcp",
            #     enabled=True
            # )
        ],
        api_wrappers=[
            # Example API wrapper - JSONPlaceholder
            APIWrapperConfig(
                name="jsonplaceholder",
                base_url="https://jsonplaceholder.typicode.com",
                auth_type="none",
                endpoints=[
                    {
                        "name": "get_user",
                        "method": "GET",
                        "path": "/users/{user_id}",
                        "description": "Get user information by ID",
                        "path_params": [
                            {
                                "name": "user_id",
                                "type": "string",
                                "description": "The ID of the user to retrieve",
                                "required": True
                            }
                        ]
                    },
                    {
                        "name": "get_posts",
                        "method": "GET", 
                        "path": "/posts",
                        "description": "Get all posts",
                        "query_params": [
                            {
                                "name": "userId",
                                "type": "string",
                                "description": "Filter posts by user ID",
                                "required": False
                            }
                        ]
                    },
                    {
                        "name": "create_post",
                        "method": "POST",
                        "path": "/posts",
                        "description": "Create a new post",
                        "body_schema": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "body": {"type": "string"},
                                "userId": {"type": "integer"}
                            },
                            "required": ["title", "body", "userId"]
                        }
                    }
                ],
                enabled=True
            )
        ]
    )
    
    # Create and initialize gateway
    gateway = MCPGateway(settings)
    await gateway.initialize()
    
    try:
        # List all available tools
        print("Available tools:")
        tools = await gateway.list_tools()
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")
        
        # Call an API wrapper tool
        print("\nCalling JSONPlaceholder API to get user 1:")
        try:
            result = await gateway.call_tool(
                "api:jsonplaceholder:get_user",
                {"user_id": "1"}
            )
            for content in result:
                print(f"  Result: {content.text}")
        except Exception as e:
            print(f"  Error: {e}")
        
        # List all available prompts
        print("\nAvailable prompts:")
        prompts = await gateway.list_prompts()
        for prompt in prompts:
            print(f"  - {prompt.name}: {prompt.description}")
        
        # List all available resources
        print("\nAvailable resources:")
        resources = await gateway.list_resources()
        for resource in resources:
            print(f"  - {resource.name}: {resource.description}")
        
        # Get server status
        print("\nServer status:")
        status = gateway.get_server_status()
        for server_name, server_status in status.items():
            print(f"  - {server_name}: {server_status['status']}")
    
    finally:
        # Shutdown gateway
        await gateway.shutdown()


async def example_http_client():
    """Example of using MCPilot via HTTP API"""
    
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        # Check health
        response = await client.get(f"{base_url}/health")
        print(f"Health check: {response.json()}")
        
        # Get status
        response = await client.get(f"{base_url}/api/v1/status")
        print(f"Status: {response.json()}")
        
        # List tools
        response = await client.get(f"{base_url}/api/v1/tools")
        tools = response.json()
        print(f"Available tools: {len(tools)}")
        for tool in tools:
            print(f"  - {tool['name']}")
        
        # Call a tool (if any available)
        if tools:
            tool_name = tools[0]["name"]
            print(f"\nCalling tool: {tool_name}")
            try:
                response = await client.post(
                    f"{base_url}/api/v1/tools/call",
                    json={
                        "name": tool_name,
                        "arguments": {}
                    }
                )
                result = response.json()
                print(f"Tool result: {result}")
            except Exception as e:
                print(f"Error calling tool: {e}")


if __name__ == "__main__":
    print("MCPilot Gateway Example Usage")
    print("=" * 40)
    
    print("\n1. Direct Gateway Usage:")
    asyncio.run(example_usage())
    
    print("\n2. HTTP API Usage (requires running server):")
    print("   Start the server with: python -m mcpilot.main")
    print("   Then uncomment the line below to test HTTP API")
    # asyncio.run(example_http_client())
