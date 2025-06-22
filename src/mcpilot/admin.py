"""
Admin API routes for MCPilot Gateway
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from .config import Settings, MCPServerConfig, APIWrapperConfig
from .gateway import MCPGateway


# Request/Response models
class ServerConfigRequest(BaseModel):
    name: str
    type: str
    command: Optional[str] = None
    args: List[str] = []
    env: Dict[str, str] = {}
    url: Optional[str] = None
    enabled: bool = True
    timeout: int = 30


class APIWrapperConfigRequest(BaseModel):
    name: str
    base_url: str
    auth_type: str = "none"
    auth_config: Dict[str, Any] = {}
    endpoints: List[Dict[str, Any]] = []
    enabled: bool = True


# Create router
admin_router = APIRouter()


def get_gateway(request: Request) -> MCPGateway:
    """Dependency to get the gateway instance"""
    return request.app.state.gateway


def get_settings(request: Request) -> Settings:
    """Dependency to get the settings instance"""
    return request.app.state.settings


@admin_router.get("/")
async def admin_dashboard():
    """Admin dashboard (placeholder for now)"""
    return {
        "message": "MCPilot Admin Dashboard",
        "endpoints": {
            "servers": "/admin/servers",
            "api-wrappers": "/admin/api-wrappers",
            "settings": "/admin/settings",
            "logs": "/admin/logs"
        }
    }


# Server management endpoints
@admin_router.get("/servers")
async def list_servers(gateway: MCPGateway = Depends(get_gateway)):
    """List all configured servers and their status"""
    return {
        "servers": gateway.get_server_status()
    }


@admin_router.post("/servers")
async def add_server(
    config: ServerConfigRequest,
    gateway: MCPGateway = Depends(get_gateway),
    settings: Settings = Depends(get_settings)
):
    """Add a new server configuration"""
    try:
        # Convert to MCPServerConfig
        server_config = MCPServerConfig(**config.model_dump())
        
        # Add to settings
        settings.mcp_servers.append(server_config)
        
        # Connect to the server if enabled
        if server_config.enabled:
            success = await gateway._connect_server(server_config)
            if not success:
                raise HTTPException(status_code=400, detail="Failed to connect to server")
        
        return {"message": f"Server {config.name} added successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@admin_router.put("/servers/{server_name}")
async def update_server(
    server_name: str,
    config: ServerConfigRequest,
    gateway: MCPGateway = Depends(get_gateway),
    settings: Settings = Depends(get_settings)
):
    """Update server configuration"""
    try:
        # Find and update server config
        for i, server_config in enumerate(settings.mcp_servers):
            if server_config.name == server_name:
                # Disconnect existing server
                await gateway._disconnect_server(server_name)
                
                # Update config
                settings.mcp_servers[i] = MCPServerConfig(**config.model_dump())
                
                # Reconnect if enabled
                if config.enabled:
                    await gateway._connect_server(settings.mcp_servers[i])
                
                return {"message": f"Server {server_name} updated successfully"}
        
        raise HTTPException(status_code=404, detail="Server not found")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@admin_router.delete("/servers/{server_name}")
async def remove_server(
    server_name: str,
    gateway: MCPGateway = Depends(get_gateway),
    settings: Settings = Depends(get_settings)
):
    """Remove a server configuration"""
    try:
        # Disconnect server
        await gateway._disconnect_server(server_name)
        
        # Remove from settings
        settings.mcp_servers = [
            s for s in settings.mcp_servers if s.name != server_name
        ]
        
        # Remove from gateway
        if server_name in gateway.servers:
            del gateway.servers[server_name]
        
        return {"message": f"Server {server_name} removed successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@admin_router.post("/servers/{server_name}/connect")
async def connect_server(
    server_name: str,
    gateway: MCPGateway = Depends(get_gateway),
    settings: Settings = Depends(get_settings)
):
    """Connect to a server"""
    try:
        # Find server config
        server_config = None
        for config in settings.mcp_servers:
            if config.name == server_name:
                server_config = config
                break
        
        if not server_config:
            raise HTTPException(status_code=404, detail="Server not found")
        
        success = await gateway._connect_server(server_config)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to connect to server")
        
        return {"message": f"Connected to {server_name}"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@admin_router.post("/servers/{server_name}/disconnect")
async def disconnect_server(
    server_name: str,
    gateway: MCPGateway = Depends(get_gateway)
):
    """Disconnect from a server"""
    try:
        await gateway._disconnect_server(server_name)
        return {"message": f"Disconnected from {server_name}"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# API wrapper management endpoints
@admin_router.get("/api-wrappers")
async def list_api_wrappers(settings: Settings = Depends(get_settings)):
    """List all configured API wrappers"""
    return {
        "api_wrappers": [wrapper.model_dump() for wrapper in settings.api_wrappers]
    }


@admin_router.post("/api-wrappers")
async def add_api_wrapper(
    config: APIWrapperConfigRequest,
    settings: Settings = Depends(get_settings)
):
    """Add a new API wrapper configuration"""
    try:
        # Convert to APIWrapperConfig
        wrapper_config = APIWrapperConfig(**config.model_dump())
        
        # Add to settings
        settings.api_wrappers.append(wrapper_config)
        
        return {"message": f"API wrapper {config.name} added successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Settings management
@admin_router.get("/settings")
async def get_settings_endpoint(settings: Settings = Depends(get_settings)):
    """Get current settings"""
    return settings.model_dump()


@admin_router.put("/settings")
async def update_settings(
    new_settings: Dict[str, Any],
    settings: Settings = Depends(get_settings)
):
    """Update settings"""
    try:
        # Update settings (simplified - in production, you'd want validation)
        for key, value in new_settings.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
        
        return {"message": "Settings updated successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Monitoring endpoints
@admin_router.get("/logs")
async def get_logs():
    """Get application logs (placeholder)"""
    return {
        "logs": [
            {"timestamp": "2024-01-01T12:00:00", "level": "INFO", "message": "Gateway started"},
            {"timestamp": "2024-01-01T12:01:00", "level": "INFO", "message": "Server connected"},
        ]
    }


@admin_router.get("/metrics")
async def get_metrics(gateway: MCPGateway = Depends(get_gateway)):
    """Get system metrics"""
    return {
        "servers_connected": len([s for s in gateway.servers.values() if s.status == "connected"]),
        "servers_total": len(gateway.servers),
        "uptime": "1h 30m",  # Placeholder
        "requests_total": 1234,  # Placeholder
        "requests_per_minute": 45  # Placeholder
    }
