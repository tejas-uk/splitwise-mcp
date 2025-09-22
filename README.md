# Splitwise MCP Server

A Model Context Protocol (MCP) server that provides tools for managing Splitwise expenses, groups, and friends. Built with FastMCP for a clean, Pythonic implementation.

## Features

- **User Management**: Get current user info and friends list
- **Expense Management**: Create and retrieve expenses with custom splits
- **Group Management**: Create and manage expense groups
- **Utilities**: Access currencies, categories, and notifications
- **Multiple Deployment Options**: Local, stdio, or cloud deployment via HTTP/SSE

## Quick Start

### Prerequisites

- Python 3.10+
- Splitwise API credentials ([Get them here](https://secure.splitwise.com/apps))

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/splitwise-mcp.git
cd splitwise-mcp

# Install dependencies
pip install -r requirements.txt
# or for development
pip install -e ".[dev]"
```

### Configuration

1. Copy the environment template:
```bash
cp .env.example .env
```

2. Add your Splitwise credentials to `.env`:
```
SPLITWISE_CONSUMER_KEY=your_consumer_key_here
SPLITWISE_CONSUMER_SECRET=your_consumer_secret_here
SPLITWISE_API_KEY=your_api_key_here
```

## Usage

### Local Development (stdio)

```bash
# Run the FastMCP server locally
python -m splitwise_mcp.fastmcp_server

# Or use the command
splitwise-mcp-fast
```

### HTTP/SSE Server (for Cursor/Cloud)

```bash
# Run the SSE server
python -m splitwise_mcp.fastmcp_sse_server

# Or use the command
splitwise-mcp-fast-sse

# Server will start on http://localhost:8000/sse
```

### Deploy to Render

See [RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md) for detailed cloud deployment instructions.

## Available Tools

### User Management
- **`get_current_user`** - Get current user information
- **`get_current_user_id`** - Get your user ID for expense splits
- **`get_friends`** - List all friends with their IDs

### Expense Management
- **`get_expenses`** - Retrieve expenses with optional filters
  - Filter by group_id, friend_id, or limit
- **`create_expense`** - Create new expenses with custom splits
  - Requires explicit user_splits for all participants
  - Validates that paid amounts = owed amounts = total cost

### Group Management
- **`get_groups`** - List all groups with member counts
- **`create_group`** - Create new groups (apartment, house, trip, other)

### Utilities
- **`get_currencies`** - List all supported currencies
- **`get_categories`** - List expense categories and subcategories
- **`get_notifications`** - Get recent notifications

## Example: Creating an Expense

```python
# First, get your user ID
get_current_user_id()
# Returns: "Your user ID is: 79774"

# Get friend IDs
get_friends()
# Returns list with friend names and IDs

# Create expense: You paid $100 for dinner, split with friend
create_expense(
    description="Dinner at restaurant",
    cost="100.00",
    user_splits=[
        {"user_id": 79774, "paid_share": "100.00", "owed_share": "50.00"},  # You
        {"user_id": 12345, "paid_share": "0.00", "owed_share": "50.00"}    # Friend
    ]
)
```

## Cursor Configuration

Add to your Cursor MCP settings (`.cursor/mcp.json`):

### For Local Development:
```json
{
  "mcpServers": {
    "splitwise": {
      "command": "python",
      "args": ["-m", "splitwise_mcp.fastmcp_server"],
      "cwd": "/path/to/splitwise-mcp"
    }
  }
}
```

### For Cloud Deployment:
```json
{
  "mcpServers": {
    "splitwise": {
      "url": "https://your-app.onrender.com/sse",
      "transport": "sse",
      "name": "Splitwise MCP"
    }
  }
}
```

See [cursor-config.json](cursor-config.json) for a complete example.

## Development

### Running Tests
```bash
pytest tests/
```

### Code Quality
```bash
# Format code
black splitwise_mcp/

# Lint
ruff check splitwise_mcp/

# Type checking
mypy splitwise_mcp/
```

## Project Structure

```
splitwise-mcp/
├── splitwise_mcp/
│   ├── __init__.py
│   ├── fastmcp_server.py      # Main FastMCP server (stdio)
│   └── fastmcp_sse_server.py  # HTTP/SSE server for cloud
├── tests/
│   └── test_fastmcp_server.py
├── .env.example               # Environment template
├── .gitignore                 # Git ignore file
├── cursor-config.json         # Cursor configuration example
├── render.yaml                # Render deployment config
├── requirements.txt           # Python dependencies
├── pyproject.toml            # Project configuration
└── README.md                  # This file
```

## Important Notes

- **All amounts must be strings** (Splitwise API requirement)
- **User splits are mandatory** - You must explicitly define how expenses are split
- **Include yourself in splits** - Your user ID must be in the user_splits array
- **Totals must match** - Sum of paid_share = Sum of owed_share = Total cost
- **Python 3.10+ required** for FastMCP compatibility

## Troubleshooting

### Common Issues

1. **"Error creating expense"**
   - Ensure all user IDs are valid
   - Check that amounts are strings (e.g., "50.00" not 50.00)
   - Verify totals match exactly

2. **"User not found"**
   - Use `get_current_user_id()` to get your ID
   - Use `get_friends()` to get valid friend IDs

3. **Authentication errors**
   - Verify your API credentials in `.env`
   - Ensure all three values are set (consumer key, secret, and API key)

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

- [Splitwise API Documentation](https://dev.splitwise.com/)
- [MCP Protocol Documentation](https://modelcontextprotocol.io)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)