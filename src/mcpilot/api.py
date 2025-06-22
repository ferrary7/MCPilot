"""
API routes for MCPilot Gateway
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

import mcp.types as types
from .gateway import MCPGateway


# Request/Response models
class ToolCallRequest(BaseModel):
    name: str
    arguments: Dict[str, Any] = {}


class PromptRequest(BaseModel):
    name: str
    arguments: Optional[Dict[str, str]] = None


class ResourceRequest(BaseModel):
    uri: str


class ToolCallResponse(BaseModel):
    content: List[Dict[str, Any]]


class PromptResponse(BaseModel):
    description: str
    messages: List[Dict[str, Any]]


class ResourceResponse(BaseModel):
    content: str


# Create router
api_router = APIRouter()


def get_gateway(request: Request) -> MCPGateway:
    """Dependency to get the gateway instance"""
    return request.app.state.gateway


@api_router.get("/")
async def api_root():
    """API root endpoint"""
    return {
        "message": "MCPilot API v1",
        "endpoints": {
            "tools": "/tools",
            "prompts": "/prompts", 
            "resources": "/resources",
            "status": "/status"
        }
    }


@api_router.get("/status")
async def get_status(gateway: MCPGateway = Depends(get_gateway)):
    """Get gateway and server status"""
    return {
        "gateway": "operational",
        "servers": gateway.get_server_status()
    }


@api_router.get("/tools", response_model=List[types.Tool])
async def list_tools(
    server_filter: Optional[str] = None,
    gateway: MCPGateway = Depends(get_gateway)
):
    """List all available tools"""
    try:
        filters = server_filter.split(",") if server_filter else None
        tools = await gateway.list_tools(server_filter=filters)
        return tools
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/tools/call", response_model=ToolCallResponse)
async def call_tool(
    request: ToolCallRequest,
    gateway: MCPGateway = Depends(get_gateway)
):
    """Call a tool"""
    try:
        result = await gateway.call_tool(request.name, request.arguments)
        # Convert TextContent objects to dicts
        content = []
        for item in result:
            if hasattr(item, 'model_dump'):
                content.append(item.model_dump())
            else:
                content.append({"type": "text", "text": str(item)})
        return ToolCallResponse(content=content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/prompts", response_model=List[types.Prompt])
async def list_prompts(
    server_filter: Optional[str] = None,
    gateway: MCPGateway = Depends(get_gateway)
):
    """List all available prompts"""
    try:
        filters = server_filter.split(",") if server_filter else None
        prompts = await gateway.list_prompts(server_filter=filters)
        return prompts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/prompts/get", response_model=PromptResponse)
async def get_prompt(
    request: PromptRequest,
    gateway: MCPGateway = Depends(get_gateway)
):
    """Get a prompt"""
    try:
        result = await gateway.get_prompt(request.name, request.arguments)
        # Convert to response format
        messages = []
        for msg in result.messages:
            if hasattr(msg, 'model_dump'):
                messages.append(msg.model_dump())
            else:
                messages.append({"role": "user", "content": str(msg)})
        
        return PromptResponse(
            description=result.description,
            messages=messages
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/resources", response_model=List[types.Resource])
async def list_resources(
    server_filter: Optional[str] = None,
    gateway: MCPGateway = Depends(get_gateway)
):
    """List all available resources"""
    try:
        filters = server_filter.split(",") if server_filter else None
        resources = await gateway.list_resources(server_filter=filters)
        return resources
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/resources/read", response_model=ResourceResponse)
async def read_resource(
    request: ResourceRequest,
    gateway: MCPGateway = Depends(get_gateway)
):
    """Read a resource"""
    try:
        content = await gateway.read_resource(request.uri)
        return ResourceResponse(content=content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket endpoint for real-time communication
@api_router.websocket("/ws")
async def websocket_endpoint(websocket, gateway: MCPGateway = Depends(get_gateway)):
    """WebSocket endpoint for real-time MCP communication"""
    await websocket.accept()
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            # Process MCP request
            method = data.get("method")
            params = data.get("params", {})
            
            if method == "tools/list":
                result = await gateway.list_tools()
                await websocket.send_json({
                    "id": data.get("id"),
                    "result": [tool.model_dump() for tool in result]
                })
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                result = await gateway.call_tool(tool_name, arguments)
                await websocket.send_json({
                    "id": data.get("id"),
                    "result": [item.model_dump() for item in result]
                })
            else:
                await websocket.send_json({
                    "id": data.get("id"),
                    "error": {"code": -32601, "message": "Method not found"}
                })
                
    except Exception as e:
        await websocket.send_json({
            "error": {"code": -32603, "message": f"Internal error: {str(e)}"}
        })
    finally:
        await websocket.close()
