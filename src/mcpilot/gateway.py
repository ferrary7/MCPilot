"""
MCPilot Gateway - Core federation and routing logic
"""
import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from datetime import datetime

import mcp.types as types
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client

from .config import Settings, MCPServerConfig
from .transports import TransportManager
from .api_wrapper import APIWrapperManager


logger = logging.getLogger(__name__)


@dataclass
class ServerInfo:
    """Information about a connected MCP server"""
    name: str
    config: MCPServerConfig
    session: Optional[ClientSession] = None
    capabilities: Optional[types.ServerCapabilities] = None
    status: str = "disconnected"
    last_error: Optional[str] = None
    connected_at: Optional[datetime] = None


class MCPGateway:
    """
    Main gateway class that federates multiple MCP servers and provides
    unified access to tools, prompts, and resources.
    """
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.servers: Dict[str, ServerInfo] = {}
        self.transport_manager = TransportManager()
        self.api_wrapper_manager = APIWrapperManager(settings.api_wrappers)
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the gateway and connect to all configured servers"""
        if self._initialized:
            return
        
        logger.info("Initializing MCPilot Gateway...")
        
        # Initialize transport manager
        await self.transport_manager.initialize()
        
        # Initialize API wrapper manager
        await self.api_wrapper_manager.initialize()
        
        # Connect to all configured MCP servers
        for server_config in self.settings.mcp_servers:
            if server_config.enabled:
                await self._connect_server(server_config)
        
        self._initialized = True
        logger.info("MCPilot Gateway initialized successfully")
    
    async def shutdown(self) -> None:
        """Shutdown the gateway and disconnect from all servers"""
        logger.info("Shutting down MCPilot Gateway...")
        
        # Disconnect from all servers
        for server_info in self.servers.values():
            await self._disconnect_server(server_info.name)
        
        # Shutdown managers
        await self.transport_manager.shutdown()
        await self.api_wrapper_manager.shutdown()
        
        self._initialized = False
        logger.info("MCPilot Gateway shutdown complete")
    
    async def _connect_server(self, config: MCPServerConfig) -> bool:
        """Connect to a single MCP server"""
        logger.info(f"Connecting to MCP server: {config.name}")
        
        server_info = ServerInfo(name=config.name, config=config)
        self.servers[config.name] = server_info
        
        try:
            if config.type == "stdio":
                session = await self._connect_stdio_server(config)
            elif config.type == "sse":
                session = await self._connect_sse_server(config)
            else:
                raise ValueError(f"Unsupported transport type: {config.type}")
            
            server_info.session = session
            server_info.status = "connected"
            server_info.connected_at = datetime.now()
            
            # Get server capabilities
            result = await session.initialize()
            server_info.capabilities = result.capabilities
            
            logger.info(f"Successfully connected to {config.name}")
            return True
            
        except Exception as e:
            error_msg = f"Failed to connect to {config.name}: {str(e)}"
            logger.error(error_msg)
            server_info.status = "error"
            server_info.last_error = error_msg
            return False
    
    async def _connect_stdio_server(self, config: MCPServerConfig) -> ClientSession:
        """Connect to a stdio-based MCP server"""
        if not config.command:
            raise ValueError("Command is required for stdio servers")
        
        # Start the process and create stdio client
        read_stream, write_stream = await stdio_client(
            command=config.command,
            args=config.args,
            env=config.env
        )
        
        # Create session
        session = ClientSession(read_stream, write_stream)
        return session
    
    async def _connect_sse_server(self, config: MCPServerConfig) -> ClientSession:
        """Connect to an SSE-based MCP server"""
        if not config.url:
            raise ValueError("URL is required for SSE servers")
        
        # Create SSE client
        session = await sse_client(config.url)
        return session
    
    async def _disconnect_server(self, server_name: str) -> None:
        """Disconnect from a server"""
        if server_name not in self.servers:
            return
        
        server_info = self.servers[server_name]
        if server_info.session:
            try:
                await server_info.session.close()
            except Exception as e:
                logger.error(f"Error disconnecting from {server_name}: {e}")
        
        server_info.status = "disconnected"
        server_info.session = None
    
    async def list_tools(self, server_filter: Optional[List[str]] = None) -> List[types.Tool]:
        """List all available tools from all connected servers"""
        all_tools = []
        
        # Get tools from MCP servers
        for server_name, server_info in self.servers.items():
            if server_filter and server_name not in server_filter:
                continue
                
            if server_info.session and server_info.status == "connected":
                try:
                    result = await server_info.session.list_tools()
                    for tool in result.tools:
                        # Add server prefix to tool name for namespacing
                        tool.name = f"{server_name}:{tool.name}"
                        all_tools.append(tool)
                except Exception as e:
                    logger.error(f"Error listing tools from {server_name}: {e}")
        
        # Get tools from API wrappers
        api_tools = await self.api_wrapper_manager.list_tools()
        all_tools.extend(api_tools)
        
        return all_tools
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Call a tool by name"""
        # Check if it's an API wrapper tool
        if name.startswith("api:"):
            return await self.api_wrapper_manager.call_tool(name, arguments)
        
        # Parse server and tool name
        if ":" not in name:
            raise ValueError(f"Tool name must include server prefix: {name}")
        
        server_name, tool_name = name.split(":", 1)
        
        if server_name not in self.servers:
            raise ValueError(f"Server not found: {server_name}")
        
        server_info = self.servers[server_name]
        if not server_info.session or server_info.status != "connected":
            raise ValueError(f"Server not connected: {server_name}")
        
        try:
            result = await server_info.session.call_tool(tool_name, arguments)
            return result.content
        except Exception as e:
            logger.error(f"Error calling tool {name}: {e}")
            raise
    
    async def list_prompts(self, server_filter: Optional[List[str]] = None) -> List[types.Prompt]:
        """List all available prompts from all connected servers"""
        all_prompts = []
        
        for server_name, server_info in self.servers.items():
            if server_filter and server_name not in server_filter:
                continue
                
            if server_info.session and server_info.status == "connected":
                try:
                    result = await server_info.session.list_prompts()
                    for prompt in result.prompts:
                        # Add server prefix to prompt name for namespacing
                        prompt.name = f"{server_name}:{prompt.name}"
                        all_prompts.append(prompt)
                except Exception as e:
                    logger.error(f"Error listing prompts from {server_name}: {e}")
        
        return all_prompts
    
    async def get_prompt(self, name: str, arguments: Optional[Dict[str, str]] = None) -> types.GetPromptResult:
        """Get a prompt by name"""
        # Parse server and prompt name
        if ":" not in name:
            raise ValueError(f"Prompt name must include server prefix: {name}")
        
        server_name, prompt_name = name.split(":", 1)
        
        if server_name not in self.servers:
            raise ValueError(f"Server not found: {server_name}")
        
        server_info = self.servers[server_name]
        if not server_info.session or server_info.status != "connected":
            raise ValueError(f"Server not connected: {server_name}")
        
        try:
            result = await server_info.session.get_prompt(prompt_name, arguments)
            return result
        except Exception as e:
            logger.error(f"Error getting prompt {name}: {e}")
            raise
    
    async def list_resources(self, server_filter: Optional[List[str]] = None) -> List[types.Resource]:
        """List all available resources from all connected servers"""
        all_resources = []
        
        for server_name, server_info in self.servers.items():
            if server_filter and server_name not in server_filter:
                continue
                
            if server_info.session and server_info.status == "connected":
                try:
                    result = await server_info.session.list_resources()
                    # Add server prefix to resource URIs for namespacing
                    for resource in result.resources:
                        # Modify URI to include server prefix
                        original_uri = str(resource.uri)
                        resource.uri = f"mcp://{server_name}/{original_uri}"
                        all_resources.append(resource)
                except Exception as e:
                    logger.error(f"Error listing resources from {server_name}: {e}")
        
        return all_resources
    
    async def read_resource(self, uri: str) -> str:
        """Read a resource by URI"""
        # Parse server from URI
        if not uri.startswith("mcp://"):
            raise ValueError(f"Invalid resource URI: {uri}")
        
        # Extract server name from URI
        uri_parts = uri[6:].split("/", 1)  # Remove "mcp://" prefix
        if len(uri_parts) != 2:
            raise ValueError(f"Invalid resource URI format: {uri}")
        
        server_name, original_uri = uri_parts
        
        if server_name not in self.servers:
            raise ValueError(f"Server not found: {server_name}")
        
        server_info = self.servers[server_name]
        if not server_info.session or server_info.status != "connected":
            raise ValueError(f"Server not connected: {server_name}")
        
        try:
            result = await server_info.session.read_resource(original_uri)
            return result.contents[0].text if result.contents else ""
        except Exception as e:
            logger.error(f"Error reading resource {uri}: {e}")
            raise
    
    def get_server_status(self) -> Dict[str, Any]:
        """Get status of all servers"""
        status = {}
        for server_name, server_info in self.servers.items():
            status[server_name] = {
                "status": server_info.status,
                "connected_at": server_info.connected_at.isoformat() if server_info.connected_at else None,
                "last_error": server_info.last_error,
                "capabilities": server_info.capabilities.model_dump() if server_info.capabilities else None
            }
        return status
