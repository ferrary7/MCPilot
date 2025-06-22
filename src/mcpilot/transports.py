"""
Transport manager for different MCP communication protocols
"""
import asyncio
import logging
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class Transport(ABC):
    """Abstract base class for MCP transports"""
    
    @abstractmethod
    async def connect(self, config: Dict[str, Any]) -> bool:
        """Connect using this transport"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect this transport"""
        pass
    
    @abstractmethod
    async def send_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Send a message and return response"""
        pass


class StdioTransport(Transport):
    """STDIO transport for MCP communication"""
    
    def __init__(self):
        self.process: Optional[asyncio.subprocess.Process] = None
        self.connected = False
    
    async def connect(self, config: Dict[str, Any]) -> bool:
        """Connect via STDIO"""
        try:
            command = config.get("command")
            args = config.get("args", [])
            env = config.get("env", {})
            
            if not command:
                raise ValueError("Command is required for STDIO transport")
            
            # Start the subprocess
            self.process = await asyncio.create_subprocess_exec(
                command,
                *args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )
            
            self.connected = True
            logger.info(f"STDIO transport connected: {command}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect STDIO transport: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Disconnect STDIO transport"""
        if self.process:
            self.process.terminate()
            await self.process.wait()
            self.process = None
        self.connected = False
    
    async def send_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Send message via STDIO"""
        if not self.process or not self.connected:
            raise RuntimeError("Transport not connected")
        
        # Implementation would handle JSON-RPC over STDIO
        # This is a simplified placeholder
        return {"result": "stdio_response"}


class HTTPTransport(Transport):
    """HTTP transport for MCP communication"""
    
    def __init__(self):
        self.base_url: Optional[str] = None
        self.session: Optional[Any] = None  # Would use httpx.AsyncClient
        self.connected = False
    
    async def connect(self, config: Dict[str, Any]) -> bool:
        """Connect via HTTP"""
        try:
            import httpx
            
            self.base_url = config.get("url")
            if not self.base_url:
                raise ValueError("URL is required for HTTP transport")
            
            self.session = httpx.AsyncClient(base_url=self.base_url)
            self.connected = True
            logger.info(f"HTTP transport connected: {self.base_url}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect HTTP transport: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Disconnect HTTP transport"""
        if self.session:
            await self.session.aclose()
            self.session = None
        self.connected = False
    
    async def send_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Send message via HTTP"""
        if not self.session or not self.connected:
            raise RuntimeError("Transport not connected")
        
        try:
            response = await self.session.post("/mcp", json=message)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"HTTP transport error: {e}")
            raise


class WebSocketTransport(Transport):
    """WebSocket transport for MCP communication"""
    
    def __init__(self):
        self.websocket: Optional[Any] = None  # Would use websockets.WebSocketClientProtocol
        self.connected = False
    
    async def connect(self, config: Dict[str, Any]) -> bool:
        """Connect via WebSocket"""
        try:
            import websockets
            
            url = config.get("url")
            if not url:
                raise ValueError("URL is required for WebSocket transport")
            
            self.websocket = await websockets.connect(url)
            self.connected = True
            logger.info(f"WebSocket transport connected: {url}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect WebSocket transport: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Disconnect WebSocket transport"""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
        self.connected = False
    
    async def send_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Send message via WebSocket"""
        if not self.websocket or not self.connected:
            raise RuntimeError("Transport not connected")
        
        try:
            import json
            await self.websocket.send(json.dumps(message))
            response = await self.websocket.recv()
            return json.loads(response)
        except Exception as e:
            logger.error(f"WebSocket transport error: {e}")
            raise


class SSETransport(Transport):
    """Server-Sent Events transport for MCP communication"""
    
    def __init__(self):
        self.session: Optional[Any] = None  # Would use httpx.AsyncClient
        self.connected = False
    
    async def connect(self, config: Dict[str, Any]) -> bool:
        """Connect via SSE"""
        try:
            import httpx
            
            url = config.get("url")
            if not url:
                raise ValueError("URL is required for SSE transport")
            
            self.session = httpx.AsyncClient()
            self.connected = True
            logger.info(f"SSE transport connected: {url}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect SSE transport: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Disconnect SSE transport"""
        if self.session:
            await self.session.aclose()
            self.session = None
        self.connected = False
    
    async def send_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Send message via SSE"""
        if not self.session or not self.connected:
            raise RuntimeError("Transport not connected")
        
        # SSE is typically unidirectional, so this might post to an endpoint
        # and listen for responses via SSE stream
        return {"result": "sse_response"}


class TransportManager:
    """Manages different transport types"""
    
    def __init__(self):
        self.transports: Dict[str, Transport] = {}
        self._transport_classes = {
            "stdio": StdioTransport,
            "http": HTTPTransport,
            "websocket": WebSocketTransport,
            "sse": SSETransport
        }
    
    async def initialize(self) -> None:
        """Initialize the transport manager"""
        logger.info("Transport manager initialized")
    
    async def shutdown(self) -> None:
        """Shutdown all transports"""
        for transport in self.transports.values():
            await transport.disconnect()
        self.transports.clear()
        logger.info("Transport manager shutdown")
    
    async def create_transport(self, transport_type: str, config: Dict[str, Any]) -> Optional[Transport]:
        """Create and connect a transport"""
        if transport_type not in self._transport_classes:
            logger.error(f"Unsupported transport type: {transport_type}")
            return None
        
        transport_class = self._transport_classes[transport_type]
        transport = transport_class()
        
        if await transport.connect(config):
            transport_id = f"{transport_type}_{len(self.transports)}"
            self.transports[transport_id] = transport
            return transport
        
        return None
    
    async def remove_transport(self, transport_id: str) -> bool:
        """Remove and disconnect a transport"""
        if transport_id in self.transports:
            await self.transports[transport_id].disconnect()
            del self.transports[transport_id]
            return True
        return False
    
    def get_transport(self, transport_id: str) -> Optional[Transport]:
        """Get a transport by ID"""
        return self.transports.get(transport_id)
    
    def list_transports(self) -> Dict[str, str]:
        """List all active transports"""
        return {
            transport_id: type(transport).__name__
            for transport_id, transport in self.transports.items()
        }
