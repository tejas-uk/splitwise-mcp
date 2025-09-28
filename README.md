# Splitwise MCP Server

A Model Context Protocol (MCP) server that provides tools for managing Splitwise expenses, groups, and friends. Built with FastMCP for a clean, Pythonic implementation.

## Features

- **User Management**: Get current user info and friends list
- **Expense Management**: Create and retrieve expenses with custom splits
- **Group Management**: Create and manage expense groups
- **Utilities**: Access currencies, categories, and notifications
- **OAuth Authentication**: Secure user authentication with their own Splitwise credentials
- **Multi-User Support**: Multiple users can authenticate independently
- **Multiple Deployment Options**: Local, stdio, or cloud deployment via HTTP/SSE

## Quick Start

### Prerequisites

- Python 3.10+
- Splitwise OAuth credentials ([Get them here](https://secure.splitwise.com/apps))
- For deployment: Render account (free tier works)

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

2. Add your Splitwise OAuth credentials to `.env`:
```
SPLITWISE_CONSUMER_KEY=your_consumer_key_here
SPLITWISE_CONSUMER_SECRET=your_consumer_secret_here
SPLITWISE_API_KEY=your_api_key_here
```

## Usage

### Local Development

```bash
# Run the integrated server locally
python -m splitwise_mcp.integrated_server

# Server will start on http://localhost:8080
# Homepage: http://localhost:8080/
# OAuth: http://localhost:8080/oauth/authorize
# MCP: http://localhost:8080/sse
```

### Deploy to Render

See [RENDER_OAUTH_DEPLOYMENT.md](RENDER_OAUTH_DEPLOYMENT.md) for detailed cloud deployment instructions.

## Available MCP Tools

### User Management
- **`get_current_user`** - Get current user information
- **`get_friends`** - List all friends with their IDs

### Expense Management
- **`get_expenses`** - Retrieve expenses with optional filters

### Group Management
- **`get_groups`** - List all groups with member counts

### Utilities
- **`get_currencies`** - List all supported currencies
- **`get_categories`** - List expense categories and subcategories

## Example: Using with ChatGPT

### OAuth Authentication Flow
1. **Visit your server homepage**: `https://your-app-name.onrender.com/`
2. **Click "Start Authentication"** and log into Splitwise
3. **Authorize the app** to access your Splitwise data
4. **Configure ChatGPT** with MCP endpoint: `https://your-app-name.onrender.com/sse`
5. **Start using!** Ask ChatGPT to help manage your Splitwise expenses

### Example ChatGPT Commands
- "Show me my recent Splitwise expenses"
- "List all my Splitwise groups"
- "What currencies does Splitwise support?"
- "Show me my Splitwise friends"

## ChatGPT Configuration

Add to your ChatGPT MCP connector settings:

```json
{
  "mcpServers": {
    "splitwise": {
      "url": "https://your-app-name.onrender.com/sse",
      "transport": "sse",
      "name": "Splitwise MCP"
    }
  }
}
```

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
│   ├── integrated_server.py   # Main integrated server (OAuth + MCP)
│   ├── fastmcp_server.py      # FastMCP tools
│   ├── oauth_server.py        # OAuth flow handling
│   └── token_storage.py       # Secure token storage
├── tests/
│   └── test_fastmcp_server.py
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