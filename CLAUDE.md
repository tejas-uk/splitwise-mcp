# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Splitwise MCP (Model Context Protocol) server that provides tools for managing expenses through the Splitwise API. It converts the main features of the namaggarwal/splitwise Python SDK into MCP tools for use with AI assistants.

## Development Commands

```bash
# Install dependencies
pip install -e .

# Install with development dependencies
pip install -e ".[dev]"

# Run the FastMCP server (recommended - cleaner implementation)
python -m splitwise_mcp.fastmcp_server
# Or use the command:
splitwise-mcp-fast

# Run the original MCP server (stdio)
python -m splitwise_mcp.server

# Run the SSE server (HTTP)
python -m splitwise_mcp.sse_server

# Run tests
pytest

# Format code
black splitwise_mcp/
ruff check splitwise_mcp/

# Type checking
mypy splitwise_mcp/
```

## Configuration

1. Copy `.env.example` to `.env`
2. Add Splitwise API credentials:
   - Get API key from https://secure.splitwise.com/apps
   - Set SPLITWISE_CONSUMER_KEY, SPLITWISE_CONSUMER_SECRET, and SPLITWISE_API_KEY

## Architecture

**Main Components:**
- `splitwise_mcp/fastmcp_server.py` - FastMCP server implementation (recommended - cleaner, more Pythonic)
- `splitwise_mcp/server.py` - Original MCP server implementation with all tools
- `splitwise_mcp/__init__.py` - Package initialization
- Configuration via environment variables and .env file

**MCP Tools Implemented:**
- User management: `get_current_user`, `get_friends`
- Expense management: `get_expenses`, `create_expense`
- Group management: `get_groups`, `create_group`
- Utilities: `get_currencies`, `get_categories`, `get_notifications`

**Dependencies:**
- `fastmcp` - FastMCP framework for building MCP servers (v2.12.3+)
- `splitwise` - Official Splitwise Python SDK
- `python-dotenv` - Environment variable management
- `pydantic` - Data validation

## Important Notes

- FastMCP server provides cleaner implementation with decorated tool functions and comprehensive docstrings
- Uses the namaggarwal/splitwise SDK for Splitwise API integration
- Supports both API key and OAuth authentication methods
- All expense amounts should be passed as strings (Splitwise requirement)
- Group creation supports types: apartment, house, trip, other
- Error handling implemented for all API calls with descriptive messages
- Python 3.10+ required for FastMCP compatibility