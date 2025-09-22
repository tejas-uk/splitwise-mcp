# Deploying Splitwise MCP Server to Render

This guide explains how to deploy the Splitwise MCP server to Render and configure it for use with Cursor or other MCP-compatible clients.

## Prerequisites

1. A [Render account](https://render.com) (free tier works)
2. A [Splitwise account](https://secure.splitwise.com/apps) with API credentials
3. This repository pushed to GitHub or GitLab

## Step 1: Get Splitwise API Credentials

1. Go to https://secure.splitwise.com/apps
2. Register a new application
3. Note down your:
   - Consumer Key
   - Consumer Secret
   - API Key

## Step 2: Deploy to Render

### Option A: Deploy with Render Button (Recommended)

1. Fork this repository to your GitHub account
2. Click the button below or go to Render Dashboard and create a new Web Service

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

### Option B: Manual Deployment

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click "New +" → "Web Service"
3. Connect your GitHub/GitLab account if not already connected
4. Select your forked repository
5. Configure the service:
   - **Name**: `splitwise-mcp` (or your preferred name)
   - **Region**: Choose closest to you
   - **Branch**: `main`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python -m splitwise_mcp.fastmcp_sse_server`
   - **Instance Type**: Free

## Step 3: Set Environment Variables

In your Render service dashboard, go to "Environment" and add:

```bash
SPLITWISE_CONSUMER_KEY=your_consumer_key_here
SPLITWISE_CONSUMER_SECRET=your_consumer_secret_here
SPLITWISE_API_KEY=your_api_key_here
PORT=10000
```

## Step 4: Deploy

1. Click "Create Web Service" or "Save Changes"
2. Wait for the deployment to complete (usually 2-3 minutes)
3. Once deployed, you'll get a URL like: `https://splitwise-mcp.onrender.com`

## Step 5: Configure Cursor

### Cursor Configuration

Add this to your Cursor MCP settings (`.cursor/mcp_settings.json` or through Cursor settings):

```json
{
  "mcpServers": {
    "splitwise": {
      "url": "https://your-service-name.onrender.com/sse",
      "transport": "sse",
      "name": "Splitwise MCP",
      "description": "Manage Splitwise expenses and groups"
    }
  }
}
```

Replace `your-service-name` with your actual Render service URL.

### Alternative: Using Environment Variables in Cursor

If you want to keep your Render URL private:

1. Create a `.env.local` file in your Cursor workspace:
```bash
SPLITWISE_MCP_URL=https://your-service-name.onrender.com/sse
```

2. Reference it in your MCP settings:
```json
{
  "mcpServers": {
    "splitwise": {
      "url": "${SPLITWISE_MCP_URL}",
      "transport": "sse",
      "name": "Splitwise MCP"
    }
  }
}
```

## Step 6: Test the Connection

### Via Direct HTTP Request

Test if your server is running:

```bash
curl https://your-service-name.onrender.com/health
```

### Via Cursor

1. Open Cursor
2. Open the MCP panel
3. You should see "Splitwise MCP" in your available tools
4. Try a simple command like "Get my current Splitwise user info"

## Available Tools

Once connected, you'll have access to these tools:

- **User Management**
  - `get_current_user` - Get your Splitwise account info
  - `get_friends` - List all your Splitwise friends

- **Expense Management**
  - `get_expenses` - Retrieve expenses with filters
  - `create_expense` - Create new expenses with splits

- **Group Management**
  - `get_groups` - List all your groups
  - `create_group` - Create new groups

- **Utilities**
  - `get_currencies` - List supported currencies
  - `get_categories` - List expense categories
  - `get_notifications` - Get recent notifications

## Monitoring & Logs

1. Go to your Render service dashboard
2. Click on "Logs" to see real-time logs
3. Check "Events" for deployment history

## Troubleshooting

### Server Not Responding

1. Check Render dashboard for deployment status
2. Verify environment variables are set correctly
3. Check logs for error messages

### Authentication Errors

1. Verify your Splitwise API credentials
2. Ensure all three environment variables are set:
   - `SPLITWISE_CONSUMER_KEY`
   - `SPLITWISE_CONSUMER_SECRET`
   - `SPLITWISE_API_KEY`

### Connection Issues from Cursor

1. Ensure the URL includes `/sse` at the end
2. Check if the service is awake (free tier services sleep after inactivity)
3. Try refreshing Cursor's MCP connection

### Free Tier Limitations

Render's free tier services:
- Spin down after 15 minutes of inactivity
- May have a cold start delay (10-30 seconds)
- Limited to 750 hours/month

For production use, consider upgrading to a paid plan.

## Security Notes

1. **Never commit API keys** to your repository
2. Use Render's environment variables for sensitive data
3. Consider adding request authentication if exposing publicly
4. Regularly rotate your Splitwise API keys

## Advanced Configuration

### Custom Port

To use a different port, update the `PORT` environment variable in Render.

### Adding Authentication

For production use, consider adding authentication:

1. Add an `API_KEY` environment variable in Render
2. Modify the server to check for this key in requests
3. Update your Cursor configuration to include the key

### Scaling

If you need better performance:
1. Upgrade to a paid Render plan
2. Increase instance type
3. Enable auto-scaling if available

## Support

- [Render Documentation](https://render.com/docs)
- [Splitwise API Documentation](https://dev.splitwise.com/)
- [MCP Protocol Documentation](https://modelcontextprotocol.io)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)

## Example Usage in Cursor

Once configured, you can use natural language commands like:

- "Show me my recent Splitwise expenses"
- "Create a new expense for lunch that cost $45, split equally with my group"
- "List all my Splitwise groups"
- "What currencies does Splitwise support?"

The MCP server will handle these requests and interact with your Splitwise account automatically.