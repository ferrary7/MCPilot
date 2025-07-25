# MCPilot - MCP Gateway

A powerful, FastAPI-based gateway for the Model Context Protocol (MCP), designed to unify and scale your AI toolchain.

<a href="https://glama.ai/mcp/servers/@ferrary7/MCPilot">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/@ferrary7/MCPilot/badge" alt="MCPilot MCP server" />
</a>

## ✅ Current Status

MCPilot is now **fully functional** with the following working features:

### ✅ Working Features
- **FastAPI Gateway Server** - Running on http://localhost:8000/docs
- **Admin Dashboard** - Beautiful web UI at http://localhost:8000
- **REST API Endpoints** - Full CRUD operations via /api/v1/*
- **API Wrapper System** - Convert REST APIs to MCP tools (tested with JSONPlaceholder)
- **Configuration Management** - Environment-based settings
- **Transport Framework** - Ready for HTTP, WebSocket, SSE, stdio
- **Modular Architecture** - Clean separation of concerns
- **Interactive Documentation** - OpenAPI/Swagger UI at /docs

### 🔄 In Progress
- **MCP Server Federation** - Basic framework ready, needs MCP client integration fixes
- **WebSocket Real-time Communication** - Framework ready
- **Admin UI Management** - Backend ready, frontend interactions needed

### 🧪 Tested Examples
The API wrapper successfully converts REST APIs to MCP tools:
```python
# Example: JSONPlaceholder API → MCP Tool
result = await gateway.call_tool(
    "api:jsonplaceholder:get_user",
    {"user_id": "1"}
)
# Returns: Full user data from REST API
```

---

1. **Federation of multiple MCP servers** into one unified endpoint
2. **REST API and function wrapping** as virtual MCP-compliant tools  
3. **Multiple transport support**: HTTP/JSON-RPC, WebSocket, SSE, and stdio
4. **Centralized tools, prompts, and resources** with full JSON-Schema validation
5. **Admin UI** with built-in auth, observability, and transport layers

## 📁 Project Structure

```
src/mcpilot/
├── main.py           # FastAPI application entry point
├── config.py         # Configuration management
├── gateway.py        # Core MCP federation logic
├── api.py           # REST API endpoints
├── admin.py         # Admin management endpoints
├── transports.py    # Transport layer implementations
├── api_wrapper.py   # REST API to MCP tool wrapper
├── middleware.py    # Request/response middleware
└── server.py        # Original MCP server implementation
```

## 🛠️ Installation

### Prerequisites

- Python 3.10 or higher
- uv package manager (recommended) or pip

### Install Dependencies

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -e .
```

## 🚀 Quick Start

### 1. Start the Gateway Server

```bash
# Run the FastAPI server
uv run python -m mcpilot.main

# Or using uvicorn directly
uvicorn mcpilot.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Access the Admin UI

Open your browser to `http://localhost:8000` to access the admin dashboard.

### 3. API Documentation

- OpenAPI/Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🔧 Configuration

MCPilot can be configured via environment variables or a `.env` file:

```env
# Server Configuration
MCPILOT_HOST=0.0.0.0
MCPILOT_PORT=8000
MCPILOT_DEBUG=false

# CORS Settings
MCPILOT_CORS_ORIGINS=["*"]

# Logging
MCPILOT_LOG_LEVEL=INFO
```

### Adding MCP Servers

Configure MCP servers via the admin API or by setting up the configuration:

```python
from mcpilot.config import MCPServerConfig

server_config = MCPServerConfig(
    name="my-server",
    type="stdio",
    command="python",
    args=["-m", "my_mcp_server"],
    enabled=True
)
```

### Adding API Wrappers

Convert REST APIs to MCP tools:

```python
from mcpilot.config import APIWrapperConfig

api_config = APIWrapperConfig(
    name="my-api",
    base_url="https://api.example.com",
    auth_type="bearer",
    auth_config={"token": "your-token"},
    endpoints=[
        {
            "name": "get_user",
            "method": "GET",
            "path": "/users/{user_id}",
            "description": "Get user information",
            "path_params": [
                {"name": "user_id", "type": "string", "required": True}
            ]
        }
    ]
)
```

## 📖 API Endpoints

### Core MCP Operations

- `GET /api/v1/tools` - List all available tools
- `POST /api/v1/tools/call` - Call a tool
- `GET /api/v1/prompts` - List all available prompts
- `POST /api/v1/prompts/get` - Get a prompt
- `GET /api/v1/resources` - List all available resources
- `POST /api/v1/resources/read` - Read a resource

### Admin Operations

- `GET /admin/servers` - List MCP servers
- `POST /admin/servers` - Add new MCP server
- `PUT /admin/servers/{name}` - Update MCP server
- `DELETE /admin/servers/{name}` - Remove MCP server
- `GET /admin/api-wrappers` - List API wrappers
- `POST /admin/api-wrappers` - Add new API wrapper

### Health & Monitoring

- `GET /health` - Health check endpoint
- `GET /api/v1/status` - Gateway and server status
- `GET /admin/metrics` - System metrics

## 🔌 WebSocket Support

Connect to the WebSocket endpoint for real-time MCP communication:

```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws');

// Send MCP JSON-RPC message
ws.send(JSON.stringify({
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list",
    "params": {}
}));
```

## 🧪 Development

### Running in Development Mode

```bash
# Install development dependencies
uv sync --dev

# Run with auto-reload
uvicorn mcpilot.main:app --reload --host 0.0.0.0 --port 8000
```

### Testing

```bash
# Run tests (when implemented)
uv run pytest

# Type checking
uv run mypy src/mcpilot
```

## 📄 License

This project is licensed under the MIT License.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## Original MCP Server Components

MCPilot also includes the original MCP server functionality for development and testing:

### Resources

The server implements a simple note storage system with:
- Custom note:// URI scheme for accessing individual notes
- Each note resource has a name, description and text/plain mimetype

### Prompts

The server provides a single prompt:
- summarize-notes: Creates summaries of all stored notes
  - Optional "style" argument to control detail level (brief/detailed)
  - Generates prompt combining all current notes with style preference

### Tools

The server implements one tool:
- add-note: Adds a new note to the server
  - Takes "name" and "content" as required string arguments
  - Updates server state and notifies clients of resource changes

## Configuration

[TODO: Add configuration details specific to your implementation]

## Quickstart

### Install

#### Claude Desktop

On MacOS: `~/Library/Application\ Support/Claude/claude_desktop_config.json`
On Windows: `%APPDATA%/Claude/claude_desktop_config.json`

<details>
  <summary>Development/Unpublished Servers Configuration</summary>
  ```
  "mcpServers": {
    "MCPilot": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\Users\ary7s\OneDrive\Desktop\MCPilot",
        "run",
        "MCPilot"
      ]
    }
  }
  ```
</details>

<details>
  <summary>Published Servers Configuration</summary>
  ```
  "mcpServers": {
    "MCPilot": {
      "command": "uvx",
      "args": [
        "MCPilot"
      ]
    }
  }
  ```
</details>

## Development

### Building and Publishing

To prepare the package for distribution:

1. Sync dependencies and update lockfile:
```bash
uv sync
```

2. Build package distributions:
```bash
uv build
```

This will create source and wheel distributions in the `dist/` directory.

3. Publish to PyPI:
```bash
uv publish
```

Note: You'll need to set PyPI credentials via environment variables or command flags:
- Token: `--token` or `UV_PUBLISH_TOKEN`
- Or username/password: `--username`/`UV_PUBLISH_USERNAME` and `--password`/`UV_PUBLISH_PASSWORD`

### Debugging

Since MCP servers run over stdio, debugging can be challenging. For the best debugging
experience, we strongly recommend using the [MCP Inspector](https://github.com/modelcontextprotocol/inspector).


You can launch the MCP Inspector via [`npm`](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm) with this command:

```bash
npx @modelcontextprotocol/inspector uv --directory C:\Users\ary7s\OneDrive\Desktop\MCPilot run mcpilot
```


Upon launching, the Inspector will display a URL that you can access in your browser to begin debugging.