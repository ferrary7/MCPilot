"""
MCPilot: A powerful, FastAPI-based gateway for the Model Context Protocol
"""
from . import server
from .main import create_app
import asyncio

def main():
    """Main entry point for the package."""
    asyncio.run(server.main())

__version__ = "0.1.0"

# Optionally expose other important items at package level
__all__ = ['main', 'server', 'create_app']