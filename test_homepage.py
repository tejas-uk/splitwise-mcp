#!/usr/bin/env python3
"""Test the homepage locally."""

import requests
import time
import subprocess
import sys
from pathlib import Path

def test_homepage():
    """Test the homepage locally."""
    print("🧪 Testing Splitwise MCP Homepage")
    print("=" * 40)
    
    # Start server in background
    print("🚀 Starting web OAuth server...")
    process = subprocess.Popen([
        sys.executable, "-m", "splitwise_mcp.web_oauth_server", "8080"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Wait for server to start
    print("⏳ Waiting for server to start...")
    time.sleep(3)
    
    try:
        # Test homepage
        print("🏠 Testing homepage...")
        response = requests.get("http://localhost:8080/", timeout=10)
        
        if response.status_code == 200:
            print("✅ Homepage loaded successfully!")
            print(f"   Status Code: {response.status_code}")
            print(f"   Content Length: {len(response.content)} bytes")
            
            # Check for key elements
            content = response.text
            if "Splitwise MCP Server" in content:
                print("✅ Title found")
            if "Start Authentication" in content:
                print("✅ Authentication button found")
            if "API Endpoints" in content:
                print("✅ API documentation found")
            if "ChatGPT Ready" in content:
                print("✅ ChatGPT integration info found")
                
        else:
            print(f"❌ Homepage failed: {response.status_code}")
            
        # Test health endpoint
        print("\n🏥 Testing health endpoint...")
        health_response = requests.get("http://localhost:8080/health", timeout=10)
        
        if health_response.status_code == 200:
            health_data = health_response.json()
            print("✅ Health check successful!")
            print(f"   Status: {health_data['status']}")
            print(f"   OAuth Configured: {health_data['oauth_configured']}")
            print(f"   Version: {health_data['version']}")
        else:
            print(f"❌ Health check failed: {health_response.status_code}")
            
        # Test OAuth endpoints
        print("\n🔐 Testing OAuth endpoints...")
        oauth_endpoints = [
            "/oauth/authorize",
            "/oauth/status", 
            "/oauth/callback"
        ]
        
        for endpoint in oauth_endpoints:
            try:
                resp = requests.get(f"http://localhost:8080{endpoint}", timeout=5)
                if resp.status_code in [200, 302, 400]:  # Expected responses
                    print(f"✅ {endpoint}: {resp.status_code}")
                else:
                    print(f"⚠️  {endpoint}: {resp.status_code}")
            except Exception as e:
                print(f"❌ {endpoint}: Error - {e}")
        
        print(f"\n🌐 Homepage URL: http://localhost:8080/")
        print(f"🏥 Health URL: http://localhost:8080/health")
        print(f"🔐 OAuth URL: http://localhost:8080/oauth/authorize")
        
        print("\n✅ All tests completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        
    finally:
        # Clean up
        print("\n🧹 Stopping server...")
        process.terminate()
        process.wait()
        print("✅ Server stopped")

if __name__ == "__main__":
    test_homepage()
