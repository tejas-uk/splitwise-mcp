#!/usr/bin/env python3
"""OAuth web server for handling Splitwise authentication flow."""

import os
import json
import secrets
import logging
from typing import Dict, Optional, Tuple
from urllib.parse import urlencode, parse_qs, urlparse
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
import webbrowser
from splitwise import Splitwise

logger = logging.getLogger("splitwise-oauth")


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler for OAuth callback."""
    
    def do_GET(self):
        """Handle GET requests for OAuth callback."""
        if self.path.startswith('/oauth/callback'):
            self.handle_oauth_callback()
        else:
            self.send_error(404, "Not Found")
    
    def handle_oauth_callback(self):
        """Handle OAuth callback with authorization code."""
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
            
            # Store the authorization code and state for the main process
            OAuthServer.set_callback_data(code, state)
            
            # Send success response
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html_response = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Splitwise OAuth Success</title>
                <style>
                    body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                    .success { color: #4CAF50; }
                    .message { margin: 20px 0; }
                </style>
            </head>
            <body>
                <h1 class="success">✅ Authentication Successful!</h1>
                <p class="message">You can now close this window and return to your MCP client.</p>
                <p>Your Splitwise account has been successfully connected.</p>
            </body>
            </html>
            """
            
            self.wfile.write(html_response.encode())
            
        except Exception as e:
            logger.error(f"Error handling OAuth callback: {e}")
            self.send_error(500, f"Internal server error: {e}")
    
    def log_message(self, format, *args):
        """Override to reduce log noise."""
        pass


class OAuthServer:
    """OAuth server for handling Splitwise authentication."""
    
    _callback_data: Optional[Tuple[str, str]] = None
    _server: Optional[HTTPServer] = None
    _server_thread: Optional[Thread] = None
    
    @classmethod
    def set_callback_data(cls, code: str, state: str):
        """Set the callback data from OAuth flow."""
        cls._callback_data = (code, state)
    
    @classmethod
    def get_callback_data(cls) -> Optional[Tuple[str, str]]:
        """Get the callback data from OAuth flow."""
        return cls._callback_data
    
    @classmethod
    def clear_callback_data(cls):
        """Clear the callback data."""
        cls._callback_data = None
    
    @classmethod
    def start_server(cls, port: int = 8080) -> str:
        """Start the OAuth callback server."""
        if cls._server is not None:
            return f"http://localhost:{port}/oauth/callback"
        
        try:
            cls._server = HTTPServer(('localhost', port), OAuthCallbackHandler)
            cls._server_thread = Thread(target=cls._server.serve_forever, daemon=True)
            cls._server_thread.start()
            
            callback_url = f"http://localhost:{port}/oauth/callback"
            logger.info(f"OAuth callback server started on {callback_url}")
            return callback_url
            
        except Exception as e:
            logger.error(f"Failed to start OAuth server: {e}")
            raise
    
    @classmethod
    def stop_server(cls):
        """Stop the OAuth callback server."""
        if cls._server:
            cls._server.shutdown()
            cls._server.server_close()
            cls._server = None
            cls._server_thread = None
            logger.info("OAuth callback server stopped")
    
    @classmethod
    def get_authorization_url(cls, consumer_key: str, consumer_secret: str, 
                            redirect_uri: str) -> Tuple[str, str]:
        """Get OAuth authorization URL and state."""
        try:
            # Initialize Splitwise client
            splitwise = Splitwise(consumer_key, consumer_secret)
            
            # Generate authorization URL
            url, state = splitwise.getOAuth2AuthorizeURL(redirect_uri)
            
            logger.info(f"Generated OAuth authorization URL with state: {state}")
            return url, state
            
        except Exception as e:
            logger.error(f"Error generating authorization URL: {e}")
            raise
    
    @classmethod
    def exchange_code_for_token(cls, consumer_key: str, consumer_secret: str,
                              code: str, redirect_uri: str) -> str:
        """Exchange authorization code for access token."""
        try:
            # Initialize Splitwise client
            splitwise = Splitwise(consumer_key, consumer_secret)
            
            # Exchange code for access token
            access_token = splitwise.getOAuth2AccessToken(code, redirect_uri)
            
            logger.info("Successfully obtained OAuth access token")
            return access_token
            
        except Exception as e:
            logger.error(f"Error exchanging code for token: {e}")
            raise


def start_oauth_flow(consumer_key: str, consumer_secret: str, 
                    port: int = 8080, auto_open: bool = True) -> Dict[str, str]:
    """
    Start the OAuth flow for Splitwise authentication.
    
    Args:
        consumer_key: Splitwise consumer key
        consumer_secret: Splitwise consumer secret
        port: Port for OAuth callback server
        auto_open: Whether to automatically open the browser
        
    Returns:
        Dict containing authorization URL and instructions
    """
    try:
        # Start OAuth callback server
        redirect_uri = OAuthServer.start_server(port)
        
        # Get authorization URL
        auth_url, state = OAuthServer.get_authorization_url(
            consumer_key, consumer_secret, redirect_uri
        )
        
        # Open browser if requested
        if auto_open:
            webbrowser.open(auth_url)
        
        return {
            "authorization_url": auth_url,
            "state": state,
            "redirect_uri": redirect_uri,
            "instructions": (
                "1. Complete authentication in your browser\n"
                "2. Use complete_oauth_flow() with the returned code and state"
            )
        }
        
    except Exception as e:
        logger.error(f"Error starting OAuth flow: {e}")
        raise


def complete_oauth_flow(consumer_key: str, consumer_secret: str, 
                       code: str, state: str) -> str:
    """
    Complete the OAuth flow by exchanging code for access token.
    
    Args:
        consumer_key: Splitwise consumer key
        consumer_secret: Splitwise consumer secret
        code: Authorization code from callback
        state: State parameter from callback
        
    Returns:
        Access token for API calls
    """
    try:
        # Get redirect URI (assuming same port as started)
        redirect_uri = f"http://localhost:8080/oauth/callback"
        
        # Exchange code for token
        access_token = OAuthServer.exchange_code_for_token(
            consumer_key, consumer_secret, code, redirect_uri
        )
        
        # Stop the OAuth server
        OAuthServer.stop_server()
        
        return access_token
        
    except Exception as e:
        logger.error(f"Error completing OAuth flow: {e}")
        raise


def wait_for_oauth_callback(timeout: int = 300) -> Optional[Tuple[str, str]]:
    """
    Wait for OAuth callback with authorization code.
    
    Args:
        timeout: Maximum time to wait in seconds
        
    Returns:
        Tuple of (code, state) or None if timeout
    """
    import time
    
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        callback_data = OAuthServer.get_callback_data()
        if callback_data:
            return callback_data
        time.sleep(1)
    
    return None


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python oauth_server.py <consumer_key> <consumer_secret>")
        sys.exit(1)
    
    consumer_key = sys.argv[1]
    consumer_secret = sys.argv[2]
    
    try:
        # Start OAuth flow
        result = start_oauth_flow(consumer_key, consumer_secret)
        print(f"Authorization URL: {result['authorization_url']}")
        print(f"State: {result['state']}")
        
        # Wait for callback
        print("Waiting for OAuth callback...")
        callback_data = wait_for_oauth_callback()
        
        if callback_data:
            code, state = callback_data
            print(f"Received code: {code}")
            print(f"Received state: {state}")
            
            # Complete OAuth flow
            access_token = complete_oauth_flow(consumer_key, consumer_secret, code, state)
            print(f"Access token: {access_token}")
        else:
            print("OAuth callback timeout")
            
    except KeyboardInterrupt:
        print("\nOAuth flow cancelled")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        OAuthServer.stop_server()
