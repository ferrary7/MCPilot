"""
API Wrapper Manager - Convert REST APIs to MCP-compliant tools
"""
import logging
from typing import Dict, List, Any, Optional
import httpx
import mcp.types as types
from .config import APIWrapperConfig

logger = logging.getLogger(__name__)


class APIWrapper:
    """Wrapper for a single REST API to expose as MCP tools"""
    
    def __init__(self, config: APIWrapperConfig):
        self.config = config
        self.client: Optional[httpx.AsyncClient] = None
        self._tools: List[types.Tool] = []
    
    async def initialize(self) -> None:
        """Initialize the API wrapper"""
        # Create HTTP client with auth
        headers = {}
        auth = None
        
        if self.config.auth_type == "bearer":
            token = self.config.auth_config.get("token", "")
            headers["Authorization"] = f"Bearer {token}"
        elif self.config.auth_type == "api_key":
            key_name = self.config.auth_config.get("key_name", "X-API-Key")
            api_key = self.config.auth_config.get("api_key", "")
            headers[key_name] = api_key
        elif self.config.auth_type == "basic":
            username = self.config.auth_config.get("username", "")
            password = self.config.auth_config.get("password", "")
            auth = httpx.BasicAuth(username, password)
        
        self.client = httpx.AsyncClient(
            base_url=self.config.base_url,
            headers=headers,
            auth=auth,
            timeout=30.0
        )
        
        # Generate tools from endpoint configurations
        self._generate_tools()
        
        logger.info(f"API wrapper initialized: {self.config.name}")
    
    async def shutdown(self) -> None:
        """Shutdown the API wrapper"""
        if self.client:
            await self.client.aclose()
            self.client = None
    
    def _generate_tools(self) -> None:
        """Generate MCP tools from API endpoint configurations"""
        self._tools = []
        
        for endpoint_config in self.config.endpoints:
            tool_name = f"api:{self.config.name}:{endpoint_config.get('name', 'unknown')}"
            
            # Create tool schema
            tool = types.Tool(
                name=tool_name,
                description=endpoint_config.get("description", f"Call {endpoint_config.get('path', '')}"),
                inputSchema=self._generate_input_schema(endpoint_config)
            )
            
            self._tools.append(tool)
    
    def _generate_input_schema(self, endpoint_config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate JSON schema for tool input based on endpoint config"""
        schema = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        # Add path parameters
        path_params = endpoint_config.get("path_params", [])
        for param in path_params:
            schema["properties"][param["name"]] = {
                "type": param.get("type", "string"),
                "description": param.get("description", f"Path parameter: {param['name']}")
            }
            if param.get("required", True):
                schema["required"].append(param["name"])
        
        # Add query parameters
        query_params = endpoint_config.get("query_params", [])
        for param in query_params:
            schema["properties"][param["name"]] = {
                "type": param.get("type", "string"),
                "description": param.get("description", f"Query parameter: {param['name']}")
            }
            if param.get("required", False):
                schema["required"].append(param["name"])
        
        # Add body parameters for POST/PUT requests
        body_schema = endpoint_config.get("body_schema")
        if body_schema:
            schema["properties"]["body"] = body_schema
            schema["required"].append("body")
        
        return schema
    
    def get_tools(self) -> List[types.Tool]:
        """Get all tools for this API wrapper"""
        return self._tools
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Call an API endpoint as a tool"""
        if not self.client:
            raise RuntimeError("API wrapper not initialized")
        
        # Parse tool name to get endpoint
        parts = tool_name.split(":")
        if len(parts) != 3 or parts[0] != "api" or parts[1] != self.config.name:
            raise ValueError(f"Invalid tool name: {tool_name}")
        
        endpoint_name = parts[2]
        
        # Find endpoint configuration
        endpoint_config = None
        for config in self.config.endpoints:
            if config.get("name") == endpoint_name:
                endpoint_config = config
                break
        
        if not endpoint_config:
            raise ValueError(f"Endpoint not found: {endpoint_name}")
        
        try:
            # Build request
            method = endpoint_config.get("method", "GET").upper()
            path = endpoint_config.get("path", "/")
            
            # Replace path parameters
            for param_name, param_value in arguments.items():
                path = path.replace(f"{{{param_name}}}", str(param_value))
            
            # Build query parameters
            params = {}
            query_param_names = [p["name"] for p in endpoint_config.get("query_params", [])]
            for param_name, param_value in arguments.items():
                if param_name in query_param_names:
                    params[param_name] = param_value
            
            # Build request body
            json_data = None
            if "body" in arguments:
                json_data = arguments["body"]
            
            # Make request
            response = await self.client.request(
                method=method,
                url=path,
                params=params,
                json=json_data
            )
            
            response.raise_for_status()
            
            # Format response
            result_text = f"API call successful (HTTP {response.status_code})\n"
            
            try:
                result_data = response.json()
                result_text += f"Response: {result_data}"
            except:
                result_text += f"Response: {response.text}"
            
            return [types.TextContent(type="text", text=result_text)]
            
        except httpx.HTTPStatusError as e:
            error_text = f"API call failed (HTTP {e.response.status_code}): {e.response.text}"
            return [types.TextContent(type="text", text=error_text)]
        except Exception as e:
            error_text = f"API call error: {str(e)}"
            return [types.TextContent(type="text", text=error_text)]


class APIWrapperManager:
    """Manages multiple API wrappers"""
    
    def __init__(self, wrapper_configs: List[APIWrapperConfig]):
        self.configs = wrapper_configs
        self.wrappers: Dict[str, APIWrapper] = {}
    
    async def initialize(self) -> None:
        """Initialize all API wrappers"""
        for config in self.configs:
            if config.enabled:
                wrapper = APIWrapper(config)
                await wrapper.initialize()
                self.wrappers[config.name] = wrapper
        
        logger.info(f"API wrapper manager initialized with {len(self.wrappers)} wrappers")
    
    async def shutdown(self) -> None:
        """Shutdown all API wrappers"""
        for wrapper in self.wrappers.values():
            await wrapper.shutdown()
        self.wrappers.clear()
        logger.info("API wrapper manager shutdown")
    
    async def list_tools(self) -> List[types.Tool]:
        """List all tools from all API wrappers"""
        all_tools = []
        for wrapper in self.wrappers.values():
            all_tools.extend(wrapper.get_tools())
        return all_tools
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Call a tool from an API wrapper"""
        # Parse wrapper name from tool name
        parts = tool_name.split(":")
        if len(parts) < 2 or parts[0] != "api":
            raise ValueError(f"Invalid API tool name: {tool_name}")
        
        wrapper_name = parts[1]
        
        if wrapper_name not in self.wrappers:
            raise ValueError(f"API wrapper not found: {wrapper_name}")
        
        return await self.wrappers[wrapper_name].call_tool(tool_name, arguments)
    
    def get_wrapper_status(self) -> Dict[str, Any]:
        """Get status of all API wrappers"""
        status = {}
        for name, wrapper in self.wrappers.items():
            status[name] = {
                "enabled": wrapper.config.enabled,
                "base_url": wrapper.config.base_url,
                "tools_count": len(wrapper.get_tools()),
                "auth_type": wrapper.config.auth_type
            }
        return status
