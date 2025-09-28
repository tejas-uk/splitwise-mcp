#!/usr/bin/env python3
"""Render deployment helper script."""

import os
import sys
import json
from pathlib import Path

def check_environment():
    """Check if required environment variables are set."""
    required_vars = ["SPLITWISE_CONSUMER_KEY", "SPLITWISE_CONSUMER_SECRET"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these in your .env file or environment")
        return False
    
    print("✅ Environment variables configured")
    return True

def generate_render_config():
    """Generate Render configuration."""
    config = {
        "services": [
            {
                "type": "web",
                "name": "splitwise-mcp-oauth",
                "runtime": "python",
                "buildCommand": "pip install -r requirements.txt",
                "startCommand": "python -m splitwise_mcp.web_oauth_server",
                "envVars": [
                    {
                        "key": "SPLITWISE_CONSUMER_KEY",
                        "sync": False
                    },
                    {
                        "key": "SPLITWISE_CONSUMER_SECRET", 
                        "sync": False
                    },
                    {
                        "key": "SPLITWISE_API_KEY",
                        "sync": False
                    },
                    {
                        "key": "PORT",
                        "value": "10000"
                    }
                ],
                "region": "oregon",
                "plan": "free"
            }
        ]
    }
    
    return config

def generate_chatgpt_config(service_url):
    """Generate ChatGPT MCP configuration."""
    config = {
        "mcpServers": {
            "splitwise": {
                "url": f"{service_url}/sse",
                "transport": "sse",
                "name": "Splitwise MCP",
                "description": "Manage Splitwise expenses and groups with OAuth"
            }
        }
    }
    
    return config

def main():
    """Main deployment helper function."""
    print("🚀 Splitwise MCP - Render Deployment Helper")
    print("=" * 50)
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Get service name from user
    service_name = input("Enter your Render service name (e.g., 'splitwise-mcp-oauth'): ").strip()
    if not service_name:
        service_name = "splitwise-mcp-oauth"
    
    service_url = f"https://{service_name}.onrender.com"
    
    print(f"\n📋 Deployment Configuration:")
    print(f"   Service Name: {service_name}")
    print(f"   Service URL: {service_url}")
    print(f"   OAuth URLs:")
    print(f"     Authorization: {service_url}/oauth/authorize")
    print(f"     Token: {service_url}/oauth/callback")
    print(f"     Status: {service_url}/oauth/status")
    
    # Generate configurations
    render_config = generate_render_config()
    chatgpt_config = generate_chatgpt_config(service_url)
    
    # Save configurations
    with open("render-config.json", "w") as f:
        json.dump(render_config, f, indent=2)
    
    with open("chatgpt-mcp-config.json", "w") as f:
        json.dump(chatgpt_config, f, indent=2)
    
    print(f"\n✅ Configuration files generated:")
    print(f"   - render-config.json (for Render dashboard)")
    print(f"   - chatgpt-mcp-config.json (for ChatGPT)")
    
    print(f"\n📝 Next Steps:")
    print(f"1. Go to https://dashboard.render.com")
    print(f"2. Create new Web Service")
    print(f"3. Connect your GitHub repository")
    print(f"4. Use these settings:")
    print(f"   - Build Command: pip install -r requirements.txt")
    print(f"   - Start Command: python -m splitwise_mcp.web_oauth_server")
    print(f"5. Set environment variables:")
    print(f"   - SPLITWISE_CONSUMER_KEY: {os.getenv('SPLITWISE_CONSUMER_KEY', 'YOUR_KEY')}")
    print(f"   - SPLITWISE_CONSUMER_SECRET: {'*' * len(os.getenv('SPLITWISE_CONSUMER_SECRET', ''))}")
    print(f"6. Update Splitwise app callback URL to: {service_url}/oauth/callback")
    print(f"7. Configure ChatGPT with the generated config")
    
    print(f"\n🔗 OAuth URLs for Splitwise App Configuration:")
    print(f"   Callback URL: {service_url}/oauth/callback")
    
    print(f"\n🤖 ChatGPT MCP Configuration:")
    print(f"   Add this to your ChatGPT MCP settings:")
    print(json.dumps(chatgpt_config, indent=2))

if __name__ == "__main__":
    main()
