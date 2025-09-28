#!/usr/bin/env python3
"""Web-based OAuth server for ChatGPT MCP integration."""

import os
import json
import logging
import time
from typing import Dict, Optional
from urllib.parse import urlencode, parse_qs, urlparse
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
import webbrowser
from splitwise import Splitwise

# Import OAuth components
from .oauth_server import OAuthServer
from .token_storage import store_oauth_token, get_oauth_token

logger = logging.getLogger("splitwise-web-oauth")


class WebOAuthHandler(BaseHTTPRequestHandler):
    """HTTP handler for web-based OAuth flow."""
    
    def do_GET(self):
        """Handle GET requests for OAuth flow."""
        try:
            if self.path.startswith('/oauth/authorize'):
                self.handle_authorize()
            elif self.path.startswith('/oauth/callback'):
                self.handle_callback()
            elif self.path.startswith('/oauth/status'):
                self.handle_status()
            elif self.path == '/':
                self.handle_home()
            elif self.path == '/health':
                self.handle_health()
            else:
                self.send_error(404, "Not Found")
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            self.send_error(500, f"Internal server error: {e}")
    
    def handle_home(self):
        """Handle home page with OAuth initiation."""
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        # Get server info
        host, port = self.server.server_address
        # Check if we're in production (Render sets PORT env var)
        is_production = os.getenv('PORT') is not None
        if is_production:
            # In production, use HTTPS and the actual domain
            base_url = f"https://{os.getenv('RENDER_EXTERNAL_URL', f'{host}:{port}')}"
        else:
            # In development, use HTTP
            base_url = f"http://{host}:{port}" if port != 80 else f"http://{host}"
        
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Splitwise MCP Server - OAuth Authentication</title>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                }}
                
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                
                .header {{
                    text-align: center;
                    color: white;
                    margin-bottom: 40px;
                }}
                
                .header h1 {{
                    font-size: 3rem;
                    margin-bottom: 10px;
                    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                }}
                
                .header p {{
                    font-size: 1.2rem;
                    opacity: 0.9;
                }}
                
                .main-content {{
                    background: white;
                    border-radius: 15px;
                    padding: 40px;
                    box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                    margin-bottom: 30px;
                }}
                
                .auth-section {{
                    text-align: center;
                    margin-bottom: 40px;
                }}
                
                .button {{
                    background: linear-gradient(45deg, #4CAF50, #45a049);
                    color: white;
                    padding: 15px 40px;
                    text-decoration: none;
                    border-radius: 50px;
                    display: inline-block;
                    margin: 10px;
                    font-size: 18px;
                    font-weight: 600;
                    transition: all 0.3s ease;
                    box-shadow: 0 4px 15px rgba(76, 175, 80, 0.3);
                }}
                
                .button:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 6px 20px rgba(76, 175, 80, 0.4);
                }}
                
                .status {{
                    margin: 20px 0;
                    padding: 20px;
                    border-radius: 10px;
                    font-weight: 500;
                }}
                
                .success {{
                    background: #d4edda;
                    color: #155724;
                    border: 1px solid #c3e6cb;
                }}
                
                .error {{
                    background: #f8d7da;
                    color: #721c24;
                    border: 1px solid #f5c6cb;
                }}
                
                .info {{
                    background: #d1ecf1;
                    color: #0c5460;
                    border: 1px solid #bee5eb;
                }}
                
                .features {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 30px;
                    margin: 40px 0;
                }}
                
                .feature {{
                    padding: 30px;
                    background: #f8f9fa;
                    border-radius: 10px;
                    text-align: center;
                    border-left: 4px solid #4CAF50;
                }}
                
                .feature h3 {{
                    color: #2c3e50;
                    margin-bottom: 15px;
                    font-size: 1.3rem;
                }}
                
                .feature p {{
                    color: #666;
                    line-height: 1.5;
                }}
                
                .api-info {{
                    background: #f8f9fa;
                    padding: 30px;
                    border-radius: 10px;
                    margin: 30px 0;
                }}
                
                .api-info h3 {{
                    color: #2c3e50;
                    margin-bottom: 20px;
                }}
                
                .url-list {{
                    background: #2c3e50;
                    color: #ecf0f1;
                    padding: 20px;
                    border-radius: 8px;
                    font-family: 'Courier New', monospace;
                    margin: 15px 0;
                }}
                
                .url-list code {{
                    color: #e74c3c;
                    font-weight: bold;
                }}
                
                .footer {{
                    text-align: center;
                    color: white;
                    margin-top: 40px;
                    opacity: 0.8;
                }}
                
                .footer a {{
                    color: white;
                    text-decoration: none;
                }}
                
                .footer a:hover {{
                    text-decoration: underline;
                }}
                
                @media (max-width: 768px) {{
                    .header h1 {{
                        font-size: 2rem;
                    }}
                    
                    .main-content {{
                        padding: 20px;
                    }}
                    
                    .features {{
                        grid-template-columns: 1fr;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 Splitwise MCP Server</h1>
                    <p>Secure OAuth Authentication for ChatGPT Integration</p>
                </div>
                
                <div class="main-content">
                    <div class="auth-section">
                        <h2>🚀 Get Started</h2>
                        <p>Authenticate with your Splitwise account to use the MCP server with ChatGPT.</p>
                        
                        <a href="/oauth/authorize" class="button">🔑 Start Authentication</a>
                        
                        <div id="status" class="status info">
                            Click "Start Authentication" to begin the OAuth flow.
                        </div>
                    </div>
                    
                    <div class="features">
                        <div class="feature">
                            <h3>🔒 Secure OAuth</h3>
                            <p>Authenticate with your own Splitwise credentials. No shared API keys required.</p>
                        </div>
                        
                        <div class="feature">
                            <h3>🤖 ChatGPT Ready</h3>
                            <p>Seamlessly integrate with ChatGPT's MCP connector for natural language expense management.</p>
                        </div>
                        
                        <div class="feature">
                            <h3>👥 Multi-User Support</h3>
                            <p>Each user authenticates independently with their own Splitwise account.</p>
                        </div>
                        
                        <div class="feature">
                            <h3>📊 Full API Access</h3>
                            <p>Create expenses, manage groups, track friends, and access all Splitwise features.</p>
                        </div>
                    </div>
                    
                    <div class="api-info">
                        <h3>🔗 API Endpoints</h3>
                        <p>This server provides the following OAuth endpoints:</p>
                        
                        <div class="url-list">
                            <div><strong>Authorization URL:</strong> <code>{base_url}/oauth/authorize</code></div>
                            <div><strong>Token URL:</strong> <code>{base_url}/oauth/callback</code></div>
                            <div><strong>Status URL:</strong> <code>{base_url}/oauth/status</code></div>
                            <div><strong>MCP Endpoint:</strong> <code>{base_url}/sse</code></div>
                        </div>
                        
                        <p><strong>For ChatGPT Integration:</strong> Use the Authorization URL as your OAuth endpoint in ChatGPT's MCP connector settings.</p>
                    </div>
                    
                    <div class="api-info">
                        <h3>📖 How to Use</h3>
                        <ol style="margin-left: 20px; line-height: 1.8;">
                            <li><strong>Authenticate:</strong> Click "Start Authentication" and log into your Splitwise account</li>
                            <li><strong>Authorize:</strong> Grant permission for the MCP server to access your Splitwise data</li>
                            <li><strong>Configure ChatGPT:</strong> Add this server to your ChatGPT MCP connector settings</li>
                            <li><strong>Start Using:</strong> Ask ChatGPT to help manage your Splitwise expenses!</li>
                        </ol>
                    </div>
                </div>
                
                <div class="footer">
                    <p>
                        <a href="https://github.com/your-repo/splitwise-mcp" target="_blank">GitHub Repository</a> | 
                        <a href="https://dev.splitwise.com/" target="_blank">Splitwise API</a> | 
                        <a href="https://modelcontextprotocol.io" target="_blank">MCP Protocol</a>
                    </p>
                    <p>Built with ❤️ for the Splitwise and ChatGPT communities</p>
                </div>
            </div>
            
            <script>
                // Check for status updates
                function checkStatus() {{
                    fetch('/oauth/status')
                        .then(response => response.json())
                        .then(data => {{
                            const statusDiv = document.getElementById('status');
                            if (data.authenticated) {{
                                statusDiv.className = 'status success';
                                statusDiv.innerHTML = '✅ Authentication successful! You can now close this window and return to ChatGPT.';
                            }} else if (data.error) {{
                                statusDiv.className = 'status error';
                                statusDiv.innerHTML = '❌ Error: ' + data.error;
                            }}
                        }})
                        .catch(err => console.log('Status check failed:', err));
                }}
                
                // Check status every 2 seconds
                setInterval(checkStatus, 2000);
            </script>
        </body>
        </html>
        """
        
        self.wfile.write(html.encode())
    
    def handle_authorize(self):
        """Handle OAuth authorization initiation."""
        try:
            consumer_key = os.getenv("SPLITWISE_CONSUMER_KEY")
            consumer_secret = os.getenv("SPLITWISE_CONSUMER_SECRET")
            
            if not consumer_key or not consumer_secret:
                self.send_error(500, "OAuth not configured")
                return
            
            # Get user_id from query parameters
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            user_id = query_params.get('user_id', ['default_user'])[0]
            
            # Start OAuth flow
            redirect_uri = f"http://{self.server.server_address[0]}:{self.server.server_address[1]}/oauth/callback"
            result = OAuthServer.get_authorization_url(consumer_key, consumer_secret, redirect_uri)
            
            auth_url, state = result
            
            # Store state for verification
            WebOAuthServer.set_pending_auth(user_id, state)
            
            # Redirect to Splitwise authorization
            self.send_response(302)
            self.send_header('Location', auth_url)
            self.end_headers()
            
        except Exception as e:
            logger.error(f"Error in authorize: {e}")
            self.send_error(500, f"Authorization error: {e}")
    
    def handle_callback(self):
        """Handle OAuth callback."""
        try:
            # Parse query parameters
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            
            code = query_params.get('code', [None])[0]
            state = query_params.get('state', [None])[0]
            error = query_params.get('error', [None])[0]
            
            if error:
                self.send_error(400, f"OAuth error: {error}")
                return
            
            if not code or not state:
                self.send_error(400, "Missing authorization code or state")
                return
            
            # Verify state and get user_id
            user_id = WebOAuthServer.get_user_for_state(state)
            if not user_id:
                self.send_error(400, "Invalid or expired state")
                return
            
            # Exchange code for token
            consumer_key = os.getenv("SPLITWISE_CONSUMER_KEY")
            consumer_secret = os.getenv("SPLITWISE_CONSUMER_SECRET")
            redirect_uri = f"http://{self.server.server_address[0]}:{self.server.server_address[1]}/oauth/callback"
            
            access_token = OAuthServer.exchange_code_for_token(
                consumer_key, consumer_secret, code, redirect_uri
            )
            
            # Store the token
            success = store_oauth_token(user_id, access_token)
            
            if success:
                # Mark as authenticated
                WebOAuthServer.set_authenticated(user_id, True)
                
                # Send success response
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                
                html = """
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Authentication Successful</title>
                    <style>
                        body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                        .success { color: #4CAF50; }
                        .message { margin: 20px 0; }
                    </style>
                </head>
                <body>
                    <h1 class="success">✅ Authentication Successful!</h1>
                    <p class="message">Your Splitwise account has been successfully connected.</p>
                    <p>You can now close this window and return to ChatGPT.</p>
                    <script>
                        // Auto-refresh parent page if in iframe
                        if (window.parent !== window) {
                            window.parent.location.reload();
                        }
                    </script>
                </body>
                </html>
                """
                
                self.wfile.write(html.encode())
            else:
                self.send_error(500, "Failed to store token")
                
        except Exception as e:
            logger.error(f"Error in callback: {e}")
            self.send_error(500, f"Callback error: {e}")
    
    def handle_status(self):
        """Handle status check requests."""
        try:
            # Get user_id from query parameters
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            user_id = query_params.get('user_id', ['default_user'])[0]
            
            # Check authentication status
            token_data = get_oauth_token(user_id)
            is_authenticated = token_data is not None
            
            status_data = {
                "authenticated": is_authenticated,
                "user_id": user_id,
                "error": None
            }
            
            if not is_authenticated:
                # Check if there's a pending authentication
                pending = WebOAuthServer.get_pending_auth(user_id)
                if pending:
                    status_data["pending"] = True
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            self.wfile.write(json.dumps(status_data).encode())
            
        except Exception as e:
            logger.error(f"Error in status: {e}")
            self.send_error(500, f"Status error: {e}")
    
    def handle_health(self):
        """Handle health check requests."""
        try:
            # Check if OAuth is configured
            consumer_key = os.getenv("SPLITWISE_CONSUMER_KEY")
            consumer_secret = os.getenv("SPLITWISE_CONSUMER_SECRET")
            
            health_data = {
                "status": "healthy",
                "timestamp": int(time.time()),
                "oauth_configured": bool(consumer_key and consumer_secret),
                "version": "1.0.0",
                "service": "splitwise-mcp-oauth"
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            self.wfile.write(json.dumps(health_data).encode())
            
        except Exception as e:
            logger.error(f"Error in health check: {e}")
            self.send_error(500, f"Health check error: {e}")
    
    def log_message(self, format, *args):
        """Override to reduce log noise."""
        pass


class WebOAuthServer:
    """Web-based OAuth server for ChatGPT integration."""
    
    _server: Optional[HTTPServer] = None
    _server_thread: Optional[Thread] = None
    _pending_auth: Dict[str, str] = {}  # user_id -> state
    _authenticated: Dict[str, bool] = {}  # user_id -> authenticated
    
    @classmethod
    def set_pending_auth(cls, user_id: str, state: str):
        """Set pending authentication for user."""
        cls._pending_auth[user_id] = state
    
    @classmethod
    def get_user_for_state(cls, state: str) -> Optional[str]:
        """Get user_id for state."""
        for user_id, stored_state in cls._pending_auth.items():
            if stored_state == state:
                return user_id
        return None
    
    @classmethod
    def set_authenticated(cls, user_id: str, authenticated: bool):
        """Set authentication status for user."""
        cls._authenticated[user_id] = authenticated
        if authenticated and user_id in cls._pending_auth:
            del cls._pending_auth[user_id]
    
    @classmethod
    def get_pending_auth(cls, user_id: str) -> Optional[str]:
        """Get pending authentication state for user."""
        return cls._pending_auth.get(user_id)
    
    @classmethod
    def start_server(cls, host: str = "0.0.0.0", port: int = 8080) -> str:
        """Start the web OAuth server."""
        if cls._server is not None:
            return f"http://{host}:{port}"
        
        try:
            cls._server = HTTPServer((host, port), WebOAuthHandler)
            cls._server_thread = Thread(target=cls._server.serve_forever, daemon=True)
            cls._server_thread.start()
            
            base_url = f"http://{host}:{port}"
            logger.info(f"Web OAuth server started on {base_url}")
            return base_url
            
        except Exception as e:
            logger.error(f"Failed to start web OAuth server: {e}")
            raise
    
    @classmethod
    def stop_server(cls):
        """Stop the web OAuth server."""
        if cls._server:
            cls._server.shutdown()
            cls._server.server_close()
            cls._server = None
            cls._server_thread = None
            logger.info("Web OAuth server stopped")
    
    @classmethod
    def get_authorization_url(cls, user_id: str = "default_user") -> str:
        """Get authorization URL for user."""
        if not cls._server:
            raise RuntimeError("Server not started")
        
        host, port = cls._server.server_address
        return f"http://{host}:{port}/oauth/authorize?user_id={user_id}"
    
    @classmethod
    def get_status_url(cls, user_id: str = "default_user") -> str:
        """Get status check URL for user."""
        if not cls._server:
            raise RuntimeError("Server not started")
        
        host, port = cls._server.server_address
        return f"http://{host}:{port}/oauth/status?user_id={user_id}"


def start_web_oauth_server(host: str = "0.0.0.0", port: int = 8080) -> str:
    """
    Start web OAuth server for ChatGPT integration.
    
    Args:
        host: Host to bind to (default: 0.0.0.0 for external access)
        port: Port to bind to (default: 8080)
        
    Returns:
        Base URL of the server
    """
    return WebOAuthServer.start_server(host, port)


def get_authorization_url(user_id: str = "default_user") -> str:
    """
    Get authorization URL for OAuth flow.
    
    Args:
        user_id: User identifier
        
    Returns:
        Authorization URL
    """
    return WebOAuthServer.get_authorization_url(user_id)


def get_status_url(user_id: str = "default_user") -> str:
    """
    Get status check URL for OAuth flow.
    
    Args:
        user_id: User identifier
        
    Returns:
        Status check URL
    """
    return WebOAuthServer.get_status_url(user_id)


if __name__ == "__main__":
    # Example usage
    import sys
    
    port = 8080
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    
    try:
        # Start web OAuth server
        base_url = start_web_oauth_server(port=port)
        print(f"Web OAuth server started on {base_url}")
        print(f"Authorization URL: {get_authorization_url()}")
        print(f"Status URL: {get_status_url()}")
        print("\nPress Ctrl+C to stop the server")
        
        # Keep server running
        import time
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nShutting down server...")
        WebOAuthServer.stop_server()
    except Exception as e:
        print(f"Error: {e}")
        WebOAuthServer.stop_server()
