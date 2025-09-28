# ChatGPT Integration Guide for Splitwise MCP

This guide explains how to integrate your Splitwise MCP server with ChatGPT using OAuth authentication.

## Overview

For OAuth to work properly with ChatGPT's MCP connector, you need:

1. **Web-based OAuth flow** - ChatGPT can redirect users to a web page
2. **Automatic callback handling** - No manual code exchange required
3. **Status checking** - ChatGPT can verify authentication status
4. **User session management** - Multiple users can authenticate independently

## Prerequisites

1. **Splitwise Developer Account** with OAuth credentials
2. **Publicly accessible server** (for production) or localhost (for testing)
3. **HTTPS in production** (required by ChatGPT for security)

## Step 1: Configure Splitwise OAuth

1. Go to [Splitwise Developer Portal](https://secure.splitwise.com/apps)
2. Create or edit your application
3. Set the **Callback URL** to: `https://your-domain.com/oauth/callback`
   - For local testing: `http://localhost:8080/oauth/callback`
4. Note your **Consumer Key** and **Consumer Secret**

## Step 2: Deploy Your MCP Server

### Option A: Local Development
```bash
# Start the MCP server
python -m splitwise_mcp.fastmcp_server

# In another terminal, start the web OAuth server
python -m splitwise_mcp.web_oauth_server 8080
```

### Option B: Production Deployment
Deploy your MCP server to a cloud platform (Render, Heroku, etc.) with:
- Public HTTPS endpoint
- Environment variables set
- Web OAuth server running

## Step 3: Configure ChatGPT MCP Connector

### In ChatGPT:

1. **Go to Settings** → **Connectors** → **Add Connector**
2. **Select MCP** as connector type
3. **Configure OAuth**:
   - **Authorization URL**: `https://your-domain.com/oauth/authorize`
   - **Token URL**: `https://your-domain.com/oauth/callback`
   - **Client ID**: Your Splitwise Consumer Key
   - **Client Secret**: Your Splitwise Consumer Secret
   - **Scope**: `read write` (or appropriate Splitwise scopes)

### Alternative: Manual OAuth Flow

If ChatGPT doesn't support direct OAuth configuration:

1. **Start OAuth Server**: Use `start_chatgpt_oauth_server()`
2. **Get Authorization URL**: Use `get_chatgpt_oauth_urls(user_id)`
3. **Redirect User**: Send user to the authorization URL
4. **Check Status**: Use `check_chatgpt_oauth_status(user_id)`

## Step 4: OAuth Flow for ChatGPT

### User Authentication Process:

1. **ChatGPT initiates OAuth**:
   ```python
   # Get OAuth URLs
   urls = get_chatgpt_oauth_urls(user_id="user_123")
   ```

2. **User visits authorization URL**:
   - Opens in browser
   - User logs into Splitwise
   - User authorizes your application

3. **Automatic callback handling**:
   - OAuth server receives callback
   - Exchanges code for access token
   - Stores token securely

4. **ChatGPT checks status**:
   ```python
   # Check if user is authenticated
   status = check_chatgpt_oauth_status(user_id="user_123")
   ```

5. **Use authenticated API calls**:
   ```python
   # All MCP tools now work with OAuth
   get_current_user(user_id="user_123")
   get_friends(user_id="user_123")
   create_expense(..., user_id="user_123")
   ```

## Step 5: ChatGPT-Specific MCP Tools

Your MCP server now includes these ChatGPT-specific tools:

### OAuth Management
- `start_chatgpt_oauth_server(host, port)` - Start web OAuth server
- `get_chatgpt_oauth_urls(user_id)` - Get OAuth URLs for ChatGPT
- `check_chatgpt_oauth_status(user_id)` - Check authentication status

### Regular Tools (with OAuth support)
- `get_current_user(user_id)` - Get user info with OAuth
- `get_friends(user_id)` - Get friends with OAuth
- `create_expense(..., user_id)` - Create expenses with OAuth
- All other tools support `user_id` parameter

## Step 6: Production Considerations

### Security Requirements

1. **HTTPS Only**: ChatGPT requires HTTPS for OAuth callbacks
2. **Secure Token Storage**: Tokens are encrypted and stored securely
3. **User Isolation**: Each user has separate token storage
4. **Token Expiration**: Automatic token expiration checking

### Environment Variables

```bash
# Required for OAuth
SPLITWISE_CONSUMER_KEY=your_consumer_key
SPLITWISE_CONSUMER_SECRET=your_consumer_secret

# Optional: API key fallback
SPLITWISE_API_KEY=your_api_key
```

### Server Configuration

```python
# Start OAuth server for ChatGPT
start_chatgpt_oauth_server(host="0.0.0.0", port=8080)
```

## Step 7: Testing the Integration

### Test OAuth Flow

1. **Start the servers**:
   ```bash
   # Terminal 1: MCP Server
   python -m splitwise_mcp.fastmcp_server
   
   # Terminal 2: Web OAuth Server
   python -m splitwise_mcp.web_oauth_server
   ```

2. **Test OAuth URLs**:
   ```python
   # Get OAuth URLs
   urls = get_chatgpt_oauth_urls("test_user")
   print(urls)
   ```

3. **Test authentication**:
   - Visit the authorization URL
   - Complete Splitwise authentication
   - Check status: `check_chatgpt_oauth_status("test_user")`

4. **Test API calls**:
   ```python
   # Test authenticated API calls
   user_info = get_current_user(user_id="test_user")
   friends = get_friends(user_id="test_user")
   ```

## Troubleshooting

### Common Issues

1. **"OAuth server not started"**
   - Ensure web OAuth server is running
   - Check port availability

2. **"Callback URL mismatch"**
   - Verify Splitwise app callback URL matches your server
   - Check HTTPS vs HTTP configuration

3. **"Token not found"**
   - Verify user_id matches during authentication
   - Check token storage permissions

4. **"ChatGPT can't access server"**
   - Ensure server is publicly accessible
   - Check firewall and network configuration

### Debug Mode

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Example: Complete ChatGPT Integration

```python
# 1. Start OAuth server
server_info = start_chatgpt_oauth_server(host="0.0.0.0", port=8080)
print(server_info)

# 2. Get OAuth URLs for ChatGPT
urls = get_chatgpt_oauth_urls(user_id="chatgpt_user")
print(urls)

# 3. ChatGPT redirects user to authorization URL
# User completes authentication in browser

# 4. Check authentication status
status = check_chatgpt_oauth_status(user_id="chatgpt_user")
print(status)

# 5. Use authenticated API calls
if "Authenticated" in status:
    user_info = get_current_user(user_id="chatgpt_user")
    friends = get_friends(user_id="chatgpt_user")
    print(f"User: {user_info}")
    print(f"Friends: {friends}")
```

## Security Best Practices

1. **Use HTTPS in production**
2. **Rotate OAuth credentials regularly**
3. **Monitor token usage and expiration**
4. **Implement rate limiting**
5. **Log authentication events**
6. **Use secure token storage**

## Support

For ChatGPT integration issues:
- Check the [Splitwise API Documentation](https://dev.splitwise.com/)
- Review OAuth server logs
- Verify ChatGPT connector configuration
- Test OAuth flow manually first
