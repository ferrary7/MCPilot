"""
Configuration settings for MCPilot
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class MCPServerConfig(BaseModel):
    """Configuration for an MCP server"""
    name: str
    type: str = Field(default="stdio", description="Transport type: stdio, http, websocket")
    command: Optional[str] = None
    args: List[str] = Field(default_factory=list)
    env: Dict[str, str] = Field(default_factory=dict)
    url: Optional[str] = None
    enabled: bool = True
    timeout: int = 30


class APIWrapperConfig(BaseModel):
    """Configuration for API wrapper"""
    name: str
    base_url: str
    auth_type: str = Field(default="none", description="Auth type: none, bearer, api_key, basic")
    auth_config: Dict[str, Any] = Field(default_factory=dict)
    endpoints: List[Dict[str, Any]] = Field(default_factory=list)
    enabled: bool = True


class TransportConfig(BaseModel):
    """Transport configuration"""
    http_enabled: bool = True
    websocket_enabled: bool = True
    sse_enabled: bool = True
    stdio_enabled: bool = True


class AdminConfig(BaseModel):
    """Admin UI configuration"""
    enabled: bool = True
    auth_enabled: bool = False
    username: str = "admin"
    password: str = "admin"


class Settings(BaseSettings):
    """Main application settings"""
    
    # Basic app configuration
    app_name: str = "MCPilot"
    app_version: str = "0.1.0"
    debug: bool = False
    
    # Server configuration
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    
    # CORS configuration
    cors_origins: List[str] = Field(default=["*"])
    cors_credentials: bool = True
    cors_methods: List[str] = Field(default=["*"])
    cors_headers: List[str] = Field(default=["*"])
    
    # MCP Servers configuration
    mcp_servers: List[MCPServerConfig] = Field(default_factory=list)
    
    # API Wrappers configuration
    api_wrappers: List[APIWrapperConfig] = Field(default_factory=list)
    
    # Transport configuration
    transport: TransportConfig = Field(default_factory=TransportConfig)
    
    # Admin configuration
    admin: AdminConfig = Field(default_factory=AdminConfig)
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Request timeout
    request_timeout: int = 30
    
    # Rate limiting
    rate_limit_enabled: bool = False
    rate_limit_requests: int = 100
    rate_limit_window: int = 60
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_prefix = "MCPILOT_"
