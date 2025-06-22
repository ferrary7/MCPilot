"""
Main FastAPI application for MCPilot Gateway
"""
import os
from pathlib import Path
from typing import Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import Settings
from .api import api_router
from .admin import admin_router
from .gateway import MCPGateway
from .middleware import setup_middleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    settings = Settings()
    app.state.settings = settings
    app.state.gateway = MCPGateway(settings)
    
    # Initialize the gateway
    await app.state.gateway.initialize()
    
    yield
    
    # Shutdown
    await app.state.gateway.shutdown()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    
    app = FastAPI(
        title="MCPilot",
        description="A powerful, FastAPI-based gateway for the Model Context Protocol",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )
    
    # Setup middleware
    setup_middleware(app)
    
    # Include routers
    app.include_router(api_router, prefix="/api/v1", tags=["API"])
    app.include_router(admin_router, prefix="/admin", tags=["Admin"])
    
    # Static files and templates
    static_dir = Path(__file__).parent / "static"
    templates_dir = Path(__file__).parent / "templates"
    
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=static_dir), name="static")
    
    if templates_dir.exists():
        templates = Jinja2Templates(directory=templates_dir)
        
        @app.get("/")
        async def root(request: Request):
            """Serve the admin UI"""
            return templates.TemplateResponse("admin.html", {"request": request})
    else:
        @app.get("/")
        async def root():
            """API root endpoint"""
            return {
                "message": "Welcome to MCPilot - MCP Gateway",
                "version": "0.1.0",
                "docs": "/docs",
                "admin": "/admin"
            }
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {"status": "healthy", "service": "MCPilot"}
    
    # Error handlers
    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=404,
            content={"detail": "Resource not found"}
        )
    
    @app.exception_handler(500)
    async def internal_error_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )
    
    return app


# Create the app instance
app = create_app()


def main():
    """Main entry point for running the gateway"""
    import uvicorn
    uvicorn.run(
        "mcpilot.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )


if __name__ == "__main__":
    main()
