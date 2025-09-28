# Deploying Splitwise MCP with OAuth to Render

This guide walks you through deploying your Splitwise MCP server with OAuth support to Render for ChatGPT integration.

## 🚀 **Quick Start**

1. **Fork this repository** to your GitHub account
2. **Set up Splitwise OAuth** credentials
3. **Deploy to Render** using the provided configuration
4. **Configure ChatGPT** with your OAuth URLs

## 📋 **Prerequisites**

- [Render account](https://render.com) (free tier works)
- [GitHub account](https://github.com) 
- [Splitwise account](https://splitwise.com) with developer access
- [Splitwise Developer Portal](https://secure.splitwise.com/apps) access

## 🔧 **Step 1: Set Up Splitwise OAuth**

### 1.1 Create Splitwise Application

1. Go to [Splitwise Developer Portal](https://secure.splitwise.com/apps)
2. Click **"Create New App"**
3. Fill in the application details:
   - **App Name**: `Splitwise MCP Server` (or your preferred name)
   - **Description**: `MCP server for Splitwise expense management with OAuth`
   - **Website**: `https://your-app-name.onrender.com` (your Render service URL)
   - **Callback URL**: `https://your-app-name.onrender.com/oauth/callback`
     - ⚠️ **Important**: Replace `your-app-name` with what you'll name your Render service
4. Click **"Create App"**
5. **Save your credentials**:
   - Consumer Key
   - Consumer Secret

### 1.2 Note Your URLs

After deployment, your service will provide:
- **Homepage URL**: `https://your-app-name.onrender.com/` (beautiful landing page)
- **Authorization URL**: `https://your-app-name.onrender.com/oauth/authorize`
- **Token URL**: `https://your-app-name.onrender.com/oauth/callback`
- **Status URL**: `https://your-app-name.onrender.com/oauth/status`
- **Health URL**: `https://your-app-name.onrender.com/health`

## 🚀 **Step 2: Deploy to Render**

### 2.1 Fork and Prepare Repository

1. **Fork this repository** to your GitHub account
2. **Clone your fork** locally (optional, for customizations)
3. **Push to GitHub** (if you made changes)

### 2.2 Deploy via Render Dashboard

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **"New +"** → **"Web Service"**
3. **Connect your GitHub** account if not already connected
4. **Select your forked repository**
5. **Configure the service**:

   **Basic Settings:**
   - **Name**: `splitwise-mcp-oauth` (or your preferred name)
   - **Region**: Choose closest to you (Oregon, Frankfurt, etc.)
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Instance Type**: `Free` (upgrade later if needed)

   **Build & Deploy:**
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python -m splitwise_mcp.web_oauth_server`

### 2.3 Set Environment Variables

In your Render service dashboard, go to **"Environment"** and add:

```bash
# Required for OAuth
SPLITWISE_CONSUMER_KEY=your_consumer_key_here
SPLITWISE_CONSUMER_SECRET=your_consumer_secret_here

# Optional: API key fallback
SPLITWISE_API_KEY=your_api_key_here

# Render automatically sets PORT=10000
```

### 2.4 Deploy

1. Click **"Create Web Service"**
2. **Wait for deployment** (usually 2-3 minutes)
3. **Note your service URL**: `https://your-app-name.onrender.com`

## 🔗 **Step 3: Update Splitwise Callback URL**

1. Go back to [Splitwise Developer Portal](https://secure.splitwise.com/apps)
2. **Edit your application**
3. **Update the Callback URL** to: `https://your-app-name.onrender.com/oauth/callback`
4. **Save changes**

## 🤖 **Step 4: Configure ChatGPT**

### 4.1 Get Your OAuth URLs

Your deployed service provides these URLs:
- **Base URL**: `https://your-app-name.onrender.com`
- **Authorization URL**: `https://your-app-name.onrender.com/oauth/authorize`
- **Token URL**: `https://your-app-name.onrender.com/oauth/callback`
- **Status URL**: `https://your-app-name.onrender.com/oauth/status`

### 4.2 Configure ChatGPT MCP Connector

In ChatGPT, configure the MCP connector with:

**OAuth Settings:**
- **Authorization URL**: `https://your-app-name.onrender.com/oauth/authorize`
- **Token URL**: `https://your-app-name.onrender.com/oauth/callback`
- **Client ID**: Your Splitwise Consumer Key
- **Client Secret**: Your Splitwise Consumer Secret
- **Scope**: `read write` (or appropriate Splitwise scopes)

**Alternative: Manual OAuth Flow**
If ChatGPT doesn't support direct OAuth configuration, users can:
1. Visit: `https://your-app-name.onrender.com/oauth/authorize`
2. Complete Splitwise authentication
3. Return to ChatGPT to use the MCP tools

## 🧪 **Step 5: Test Your Deployment**

### 5.1 Test Homepage

1. **Visit your service**: `https://your-app-name.onrender.com`
2. **Verify the beautiful homepage loads** with:
   - Professional design with gradient background
   - Clear authentication instructions
   - API endpoint documentation
   - Feature highlights
   - Responsive design for mobile/desktop

### 5.2 Test OAuth Flow

1. **Click "Start Authentication"** on the homepage
2. **Complete Splitwise login** and authorization
3. **Verify success message** appears
4. **Test health endpoint**: `https://your-app-name.onrender.com/health`

### 5.3 Test MCP Tools

Once authenticated, test the MCP tools:

```python
# Test user info
get_current_user(user_id="default_user")

# Test friends list
get_friends(user_id="default_user")

# Test expense creation
create_expense(
    description="Test expense",
    cost="10.00",
    user_splits=[...],
    user_id="default_user"
)
```

## 📊 **Step 6: Monitor Your Deployment**

### 6.1 Render Dashboard

- **Logs**: Real-time server logs
- **Events**: Deployment history
- **Metrics**: Performance monitoring

### 6.2 Health Checks

Test your service health:
```bash
# Check if server is running
curl https://your-app-name.onrender.com/

# Check OAuth status
curl https://your-app-name.onrender.com/oauth/status?user_id=test
```

## 🔧 **Configuration Options**

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SPLITWISE_CONSUMER_KEY` | ✅ | Your Splitwise app's consumer key |
| `SPLITWISE_CONSUMER_SECRET` | ✅ | Your Splitwise app's consumer secret |
| `SPLITWISE_API_KEY` | ❌ | Fallback API key (optional) |
| `PORT` | ❌ | Port (auto-set by Render) |

### Custom Configuration

You can customize the deployment by modifying `render.yaml`:

```yaml
services:
  - type: web
    name: splitwise-mcp-server
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: python -m splitwise_mcp.web_oauth_server
    envVars:
      - key: SPLITWISE_CONSUMER_KEY
        sync: false
      - key: SPLITWISE_CONSUMER_SECRET
        sync: false
      - key: SPLITWISE_API_KEY
        sync: false
    region: oregon
    plan: free
```

## 🚨 **Troubleshooting**

### Common Issues

1. **"OAuth not configured"**
   - Check environment variables are set
   - Verify Consumer Key and Secret are correct

2. **"Callback URL mismatch"**
   - Ensure Splitwise callback URL matches your Render URL
   - Check for HTTPS vs HTTP differences

3. **"Service not responding"**
   - Check Render dashboard for deployment status
   - Free tier services sleep after inactivity (cold start delay)

4. **"Token not found"**
   - Verify user completed OAuth flow
   - Check token storage permissions

### Debug Steps

1. **Check Render logs** for error messages
2. **Verify environment variables** are set correctly
3. **Test OAuth flow** manually in browser
4. **Check Splitwise app configuration**

## 🔒 **Security Considerations**

### Production Security

1. **HTTPS Only**: Render provides HTTPS automatically
2. **Environment Variables**: Never commit secrets to code
3. **Token Storage**: OAuth tokens are encrypted and stored securely
4. **User Isolation**: Each user has separate token storage

### Free Tier Limitations

- **Sleep Mode**: Services sleep after 15 minutes of inactivity
- **Cold Start**: 10-30 second delay when waking up
- **Monthly Hours**: Limited to 750 hours/month
- **Performance**: May be slower than paid tiers

## 📈 **Scaling and Upgrades**

### Upgrade to Paid Plan

For production use, consider upgrading:
1. **Paid Plans**: Better performance and reliability
2. **Custom Domains**: Use your own domain
3. **Auto-scaling**: Handle traffic spikes
4. **Persistent Storage**: Better token storage

### Performance Optimization

1. **Database**: Consider external database for token storage
2. **Caching**: Implement token caching
3. **CDN**: Use CDN for static assets
4. **Monitoring**: Set up proper monitoring

## 🎯 **Next Steps**

After successful deployment:

1. **Test with ChatGPT** integration
2. **Monitor usage** and performance
3. **Consider upgrades** for production use
4. **Set up monitoring** and alerts
5. **Document** your specific configuration

## 📞 **Support**

- [Render Documentation](https://render.com/docs)
- [Splitwise API Documentation](https://dev.splitwise.com/)
- [MCP Protocol Documentation](https://modelcontextprotocol.io)
- [GitHub Issues](https://github.com/your-repo/issues)

## 🎉 **Success!**

Your Splitwise MCP server with OAuth is now deployed and ready for ChatGPT integration!

**Your OAuth URLs:**
- Authorization: `https://your-app-name.onrender.com/oauth/authorize`
- Token: `https://your-app-name.onrender.com/oauth/callback`
- Status: `https://your-app-name.onrender.com/oauth/status`

Users can now authenticate with their own Splitwise accounts and use all MCP tools securely!
