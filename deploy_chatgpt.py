#!/usr/bin/env python3
"""Deployment script for ChatGPT integration."""

import os
import sys
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from splitwise_mcp.web_oauth_server import start_web_oauth_server, get_authorization_url, get_status_url
from splitwise_mcp.token_storage import get_token_storage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("chatgpt-deploy")


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


def start_servers(host="0.0.0.0", port=8080):
    """Start both MCP and OAuth servers."""
    try:
        # Start web OAuth server
        base_url = start_web_oauth_server(host, port)
        
        print(f"🚀 ChatGPT OAuth server started!")
        print(f"   Server URL: {base_url}")
        print(f"   Authorization URL: {get_authorization_url()}")
        print(f"   Status URL: {get_status_url()}")
        print()
        
        # Show configuration for ChatGPT
        print("📋 ChatGPT Configuration:")
        print(f"   OAuth Authorization URL: {get_authorization_url()}")
        print(f"   OAuth Token URL: {base_url}/oauth/callback")
        print(f"   OAuth Status URL: {get_status_url()}")
        print(f"   Client ID: {os.getenv('SPLITWISE_CONSUMER_KEY')}")
        print(f"   Client Secret: {'*' * len(os.getenv('SPLITWISE_CONSUMER_SECRET', ''))}")
        print()
        
        # Show token storage info
        storage = get_token_storage()
        info = storage.get_storage_info()
        print("💾 Token Storage:")
        print(f"   Directory: {info.get('storage_dir', 'Unknown')}")
        print(f"   Users: {info.get('user_count', 0)}")
        print()
        
        print("✅ Ready for ChatGPT integration!")
        print("   Users can authenticate by visiting the authorization URL")
        print("   Press Ctrl+C to stop the server")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to start servers: {e}")
        return False


def main():
    """Main deployment function."""
    print("🔐 Splitwise MCP - ChatGPT Integration Deployer")
    print("=" * 50)
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Get host and port from command line or use defaults
    host = "0.0.0.0"
    port = 8080
    
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Invalid port: {sys.argv[1]}")
            sys.exit(1)
    
    if len(sys.argv) > 2:
        host = sys.argv[2]
    
    # Start servers
    if not start_servers(host, port):
        sys.exit(1)
    
    # Keep server running
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down servers...")
        from splitwise_mcp.web_oauth_server import WebOAuthServer
        WebOAuthServer.stop_server()
        print("✅ Servers stopped")


if __name__ == "__main__":
    main()
