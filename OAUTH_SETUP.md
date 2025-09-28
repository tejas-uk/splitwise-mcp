# OAuth Setup for Splitwise MCP

This guide explains how to set up OAuth authentication for the Splitwise MCP server, allowing users to authenticate with their own Splitwise credentials instead of using API keys.

## Overview

OAuth authentication provides several benefits:
- **User-specific access**: Each user authenticates with their own Splitwise account
- **Enhanced security**: No need to share API keys
- **Better user experience**: Users can manage their own authentication
- **Multi-user support**: Multiple users can use the same MCP server

## Prerequisites

1. **Splitwise Developer Account**: You need a Splitwise account and developer credentials
2. **Consumer Key & Secret**: Register your application with Splitwise to get these
3. **Python Dependencies**: Ensure `cryptography` is installed (added to requirements.txt)

## Step 1: Register Your Application with Splitwise

1. Go to [Splitwise Developer Portal](https://secure.splitwise.com/apps)
2. Sign in with your Splitwise account
3. Click "Create New App"
4. Fill in the application details:
   - **App Name**: Your MCP server name (e.g., "Splitwise MCP Server")
   - **Description**: Brief description of your application
   - **Website**: Your website or GitHub repository
   - **Callback URL**: `http://localhost:8080/oauth/callback` (for local development)
5. Note down your **Consumer Key** and **Consumer Secret**

## Step 2: Configure Environment Variables

Create or update your `.env` file with the OAuth credentials:

```bash
# OAuth Configuration (Required for OAuth)
SPLITWISE_CONSUMER_KEY=your_consumer_key_here
SPLITWISE_CONSUMER_SECRET=your_consumer_secret_here

# Optional: API Key fallback (for backward compatibility)
SPLITWISE_API_KEY=your_api_key_here
```

## Step 3: Install Dependencies

Install the required dependencies including the new cryptography package:

```bash
pip install -r requirements.txt
```

## Step 4: OAuth Authentication Flow

### For Users (OAuth Flow)

1. **Start OAuth Authentication**:
   ```python
   # This will open a browser window for authentication
   start_oauth_authentication(port=8080)
   ```

2. **Complete Authentication**:
   - The browser will open to Splitwise's authorization page
   - User logs in and authorizes your application
   - User is redirected back with an authorization code
   - Use the returned code and state to complete authentication:
   ```python
   complete_oauth_authentication(
       code="authorization_code_from_callback",
       state="state_parameter_from_callback", 
       user_id="unique_user_identifier"
   )
   ```

### For Developers (Testing OAuth)

You can test the OAuth flow using the standalone OAuth server:

```bash
python -m splitwise_mcp.oauth_server your_consumer_key your_consumer_secret
```

This will:
1. Start a local OAuth callback server
2. Open your browser to the authorization URL
3. Wait for the callback
4. Exchange the code for an access token
5. Display the access token

## Step 5: Using OAuth with MCP Tools

Once OAuth is set up, you can use all MCP tools with OAuth authentication by providing a `user_id` parameter:

```python
# Get current user info with OAuth
get_current_user(user_id="my_user_id")

# Get friends with OAuth
get_friends(user_id="my_user_id")

# Create expenses with OAuth
create_expense(
    description="Dinner",
    cost="100.00",
    user_splits=[...],
    user_id="my_user_id"
)
```

## OAuth Management Tools

The MCP server includes several tools for managing OAuth authentication:

### Authentication Tools
- `start_oauth_authentication(port=8080)` - Start OAuth flow
- `complete_oauth_authentication(code, state, user_id)` - Complete OAuth flow
- `check_oauth_status(user_id)` - Check authentication status
- `revoke_oauth_authentication(user_id)` - Revoke OAuth token

### Management Tools
- `list_oauth_users()` - List all authenticated users
- `get_oauth_storage_info()` - Get storage information

## Security Features

### Token Storage
- OAuth tokens are encrypted using Fernet (AES 128 in CBC mode)
- Tokens are stored in `~/.splitwise-mcp/oauth_tokens.json`
- Encryption key is stored in `~/.splitwise-mcp/encryption.key`
- Both files have restrictive permissions (600)

### Token Management
- Automatic token expiration checking
- Secure token revocation
- Multi-user token isolation
- No plaintext token storage

## Troubleshooting

### Common Issues

1. **"Consumer key/secret not set"**
   - Ensure `SPLITWISE_CONSUMER_KEY` and `SPLITWISE_CONSUMER_SECRET` are in your `.env` file

2. **"OAuth callback timeout"**
   - Check that port 8080 is available
   - Ensure the callback URL matches your Splitwise app configuration

3. **"Token not found"**
   - Verify the user_id matches what was used during authentication
   - Check if the token has expired

4. **"Authorization failed"**
   - Verify the consumer key and secret are correct
   - Check that the callback URL in Splitwise matches your configuration

### Debug Mode

Enable debug logging to troubleshoot OAuth issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Migration from API Key to OAuth

If you're currently using API keys, you can migrate to OAuth:

1. **Keep API Key as Fallback**: Your existing API key will still work
2. **Add OAuth Credentials**: Add consumer key and secret to `.env`
3. **Gradual Migration**: Users can authenticate with OAuth while maintaining API key support
4. **Remove API Key**: Once all users are on OAuth, you can remove the API key

## Production Deployment

For production deployment:

1. **Update Callback URL**: Change the callback URL in your Splitwise app to your production domain
2. **Secure Storage**: Ensure the token storage directory has proper permissions
3. **HTTPS**: Use HTTPS for the OAuth callback URL
4. **Environment Variables**: Set OAuth credentials in your production environment

## Example: Complete OAuth Setup

```python
# 1. Start OAuth flow
result = start_oauth_authentication()
print(f"Go to: {result['authorization_url']}")

# 2. After user completes authentication in browser
# (In a real application, you'd capture this from the callback)
code = "authorization_code_from_callback"
state = "state_from_callback"
user_id = "user_123"

# 3. Complete authentication
success = complete_oauth_authentication(code, state, user_id)
print(success)

# 4. Use OAuth for API calls
user_info = get_current_user(user_id="user_123")
print(user_info)
```

## Support

For issues with OAuth setup:
- Check the [Splitwise API Documentation](https://dev.splitwise.com/)
- Review the OAuth server logs for error messages
- Ensure all environment variables are set correctly
- Verify your Splitwise app configuration matches your setup
