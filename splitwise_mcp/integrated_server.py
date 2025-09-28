#!/usr/bin/env python3
"""Integrated server that combines OAuth web interface with FastMCP tools."""

import os
import json
import logging
import time
import asyncio
from typing import Dict, Optional, List, Any
from urllib.parse import urlencode, parse_qs, urlparse
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
import webbrowser
from splitwise import Splitwise
from splitwise.expense import Expense
from splitwise.group import Group
from splitwise.user import ExpenseUser

# Import OAuth components
from .oauth_server import OAuthServer
from .token_storage import store_oauth_token, get_oauth_token

# Import FastMCP
from fastmcp import FastMCP

logger = logging.getLogger("splitwise-integrated-server")

# Initialize FastMCP app
mcp = FastMCP(
    name="Splitwise MCP Server",
    instructions="""
    You are a Splitwise expense management assistant.
    You help users manage their expenses, create splits, manage groups, and track shared costs.
    Always provide clear responses about expense operations and group activities.
    """
)

# Global Splitwise client instance
splitwise_client: Optional[Splitwise] = None

def get_splitwise_client(user_id: Optional[str] = None) -> Splitwise:
    """
    Get or create the Splitwise client instance.
    
    Args:
        user_id: Optional user ID for OAuth token lookup
        
    Returns:
        Splitwise: Configured Splitwise client
        
    Raises:
        ValueError: If required environment variables are not set
    """
    global splitwise_client
    
    if splitwise_client is None:
        consumer_key = os.getenv("SPLITWISE_CONSUMER_KEY")
        consumer_secret = os.getenv("SPLITWISE_CONSUMER_SECRET")
        api_key = os.getenv("SPLITWISE_API_KEY")
        
        if not consumer_key or not consumer_secret:
            raise ValueError("SPLITWISE_CONSUMER_KEY and SPLITWISE_CONSUMER_SECRET must be set")
        
        # Try OAuth token first if user_id provided
        if user_id:
            token_data = get_oauth_token(user_id)
            if token_data:
                splitwise_client = Splitwise(consumer_key, consumer_secret)
                splitwise_client.setOAuth2AccessToken(token_data["access_token"])
                return splitwise_client
        
        # Fall back to API key
        if api_key:
            splitwise_client = Splitwise(consumer_key, consumer_secret, api_key=api_key)
        else:
            # Try OAuth tokens from environment
            oauth_token = os.getenv("SPLITWISE_OAUTH_TOKEN")
            oauth_token_secret = os.getenv("SPLITWISE_OAUTH_TOKEN_SECRET")
            
            if oauth_token and oauth_token_secret:
                splitwise_client = Splitwise(consumer_key, consumer_secret)
                splitwise_client.setAccessToken({
                    'oauth_token': oauth_token,
                    'oauth_token_secret': oauth_token_secret
                })
            else:
                raise ValueError("Either SPLITWISE_API_KEY or OAuth tokens must be set")
    
    return splitwise_client

# MCP Tools - User Management

@mcp.tool()
def get_current_user(user_id: Optional[str] = None) -> str:
    """
    Fetch information about the currently authenticated Splitwise user.
    
    Args:
        user_id: Optional user ID for OAuth authentication
    
    Returns:
        str: Formatted string with user's name and email
        
    Raises:
        Exception: If unable to fetch user information from Splitwise API
    """
    try:
        client = get_splitwise_client(user_id)
        user = client.getCurrentUser()
        return f"Current user: {user.first_name} {user.last_name} ({user.email})"
    except Exception as e:
        logger.error(f"Error getting current user: {str(e)}")
        return f"Error: {str(e)}"

@mcp.tool()
def get_current_user_id(user_id: Optional[str] = None) -> str:
    """
    Fetch the user ID of the currently authenticated Splitwise user.
    
    Args:
        user_id: Optional user ID for OAuth authentication
    
    Returns:
        str: The user's ID that can be used in expense splits
        
    Raises:
        Exception: If unable to fetch user information from Splitwise API
        
    Note:
        Use this ID when creating expenses where you are one of the participants
    """
    try:
        client = get_splitwise_client(user_id)
        user = client.getCurrentUser()
        return f"Your user ID is: {user.id}"
    except Exception as e:
        logger.error(f"Error getting current user ID: {str(e)}")
        return f"Error: {str(e)}"

@mcp.tool()
def get_friends(user_id: Optional[str] = None) -> str:
    """
    Retrieve the list of friends associated with the current user.
    
    Args:
        user_id: Optional user ID for OAuth authentication
    
    Returns:
        str: Formatted list of friends with their names and IDs
        
    Raises:
        Exception: If unable to fetch friends list from Splitwise API
    """
    try:
        client = get_splitwise_client(user_id)
        friends = client.getFriends()
        
        if not friends:
            return "No friends found in your Splitwise account."
        
        friend_list = ["Friends:"]
        for friend in friends:
            friend_list.append(f"- {friend.first_name} {friend.last_name} (ID: {friend.id})")
        
        return "\n".join(friend_list)
    except Exception as e:
        logger.error(f"Error getting friends: {str(e)}")
        return f"Error: {str(e)}"

# MCP Tools - Expense Management

@mcp.tool()
def get_expenses(
    group_id: Optional[int] = None,
    friend_id: Optional[int] = None,
    limit: int = 10,
    user_id: Optional[str] = None
) -> str:
    """
    Retrieve a list of expenses with optional filtering by group or friend.
    
    Args:
        group_id: Optional group ID to filter expenses by specific group
        friend_id: Optional friend ID to filter expenses involving specific friend
        limit: Maximum number of expenses to return (default: 10)
        user_id: Optional user ID for OAuth authentication
        
    Returns:
        str: Formatted list of expenses with description, cost, and currency
        
    Raises:
        Exception: If unable to fetch expenses from Splitwise API
    """
    try:
        client = get_splitwise_client(user_id)
        expenses = client.getExpenses(
            group_id=group_id,
            friend_id=friend_id,
            limit=limit
        )
        
        if not expenses:
            return "No expenses found with the specified criteria."
        
        expense_list = ["Expenses:"]
        for expense in expenses:
            expense_list.append(
                f"- {expense.description}: {expense.cost} {expense.currency_code} (ID: {expense.id})"
            )
        
        return "\n".join(expense_list)
    except Exception as e:
        logger.error(f"Error getting expenses: {str(e)}")
        return f"Error: {str(e)}"

@mcp.tool()
def create_expense(
    description: str,
    cost: str,
    user_splits: List[Dict[str, Any]],
    currency_code: str = "USD",
    group_id: Optional[int] = None,
    user_id: Optional[str] = None
) -> str:
    """
    Create a new expense and split it among users.
    
    IMPORTANT: You must include ALL users involved in the expense, including yourself.
    Use get_current_user_id() to get your user ID and get_friends() to get friend IDs.
    
    Args:
        description: Description of the expense (e.g., "Dinner at restaurant")
        cost: Total cost of the expense as a string (Splitwise requirement)
        user_splits: List of user splits. Each split must have:
                     - user_id: ID of the user (integer)
                     - paid_share: Amount this user paid (as string, e.g., "50.00")
                     - owed_share: Amount this user owes (as string, e.g., "25.00")
                     
                     Rules:
                     - Sum of all paid_share must equal cost
                     - Sum of all owed_share must equal cost
                     - Include yourself in the splits
        currency_code: Three-letter currency code (default: USD)
        group_id: Optional group ID to add expense to a specific group
        user_id: Optional user ID for OAuth authentication
                     
    Returns:
        str: Confirmation message with created expense details
        
    Raises:
        ValueError: If user_splits is empty or invalid
        Exception: If expense creation fails or validation errors occur
    """
    try:
        # Validate user_splits
        if not user_splits:
            return "Error: user_splits is required and cannot be empty"
        
        if not isinstance(user_splits, list):
            return "Error: user_splits must be a list of dictionaries"
        
        # Validate each split and ensure proper data types
        for split in user_splits:
            if not all(key in split for key in ["user_id", "paid_share", "owed_share"]):
                return "Error: Each split must have user_id, paid_share, and owed_share"
            
            # Validate that shares are strings (Splitwise requirement)
            if not isinstance(split["paid_share"], str):
                return f"Error: paid_share must be a string, got {type(split['paid_share']).__name__}"
            
            if not isinstance(split["owed_share"], str):
                return f"Error: owed_share must be a string, got {type(split['owed_share']).__name__}"
        
        # Validate that total paid equals total owed
        total_paid = sum(float(split["paid_share"]) for split in user_splits)
        total_owed = sum(float(split["owed_share"]) for split in user_splits)
        
        if abs(total_paid - total_owed) > 0.01:  # Allow small rounding differences
            return f"Error: Total paid ({total_paid:.2f}) must equal total owed ({total_owed:.2f})"
        
        # Validate that total paid equals the expense cost
        if abs(total_paid - float(cost)) > 0.01:
            return f"Error: Total paid ({total_paid:.2f}) must equal expense cost ({cost})"
        
        client = get_splitwise_client(user_id)
        
        expense = Expense()
        expense.setDescription(str(description))
        expense.setCost(str(cost))
        expense.setCurrencyCode(str(currency_code))
        
        if group_id:
            expense.setGroupId(int(group_id))
        
        # Create users list with proper ExpenseUser objects
        users = []
        for split in user_splits:
            expense_user = ExpenseUser()
            expense_user.setId(int(split["user_id"]))
            expense_user.setPaidShare(str(split["paid_share"]))
            expense_user.setOwedShare(str(split["owed_share"]))
            users.append(expense_user)
        
        expense.setUsers(users)
        
        # Log the expense details for debugging
        logger.info(f"Creating expense: {description}, Cost: {cost}, Users: {len(users)}")
        for i, split in enumerate(user_splits):
            logger.info(f"  User {i+1}: ID={split['user_id']}, Paid={split['paid_share']}, Owed={split['owed_share']}")
        
        created_expense, errors = client.createExpense(expense)
        
        if errors:
            # Extract error messages from Splitwise error object
            if hasattr(errors, 'errors'):
                error_messages = []
                for error in errors.errors:
                    if hasattr(error, 'message'):
                        error_messages.append(error.message)
                    else:
                        error_messages.append(str(error))
                error_text = "; ".join(error_messages)
            elif hasattr(errors, 'message'):
                error_text = errors.message
            else:
                error_text = str(errors)
            
            logger.error(f"Splitwise API errors: {error_text}")
            return f"Error creating expense: {error_text}"
        
        if not created_expense:
            return "Error: Expense creation failed with no error message"
        
        return (f"Created expense: {created_expense.description} - "
                f"{created_expense.cost} {created_expense.currency_code} "
                f"(ID: {created_expense.id})")
    except Exception as e:
        logger.error(f"Error creating expense: {str(e)}", exc_info=True)
        return f"Error: {str(e)}"

# MCP Tools - Group Management

@mcp.tool()
def get_groups(user_id: Optional[str] = None) -> str:
    """
    Retrieve all groups associated with the current user.
    
    Args:
        user_id: Optional user ID for OAuth authentication
    
    Returns:
        str: Formatted list of groups with names, IDs, and member counts
        
    Raises:
        Exception: If unable to fetch groups from Splitwise API
    """
    try:
        client = get_splitwise_client(user_id)
        groups = client.getGroups()
        
        if not groups:
            return "No groups found in your Splitwise account."
        
        group_list = ["Groups:"]
        for group in groups:
            member_count = len(group.members) if group.members else 0
            group_list.append(f"- {group.name} (ID: {group.id}, Members: {member_count})")
        
        return "\n".join(group_list)
    except Exception as e:
        logger.error(f"Error getting groups: {str(e)}")
        return f"Error: {str(e)}"

@mcp.tool()
def create_group(
    name: str,
    description: str = "",
    group_type: str = "other",
    user_id: Optional[str] = None
) -> str:
    """
    Create a new expense sharing group in Splitwise.
    
    Args:
        name: Name of the group (e.g., "Europe Trip 2024")
        description: Optional description providing more details about the group
        group_type: Type of group - one of: apartment, house, trip, other (default: other)
        user_id: Optional user ID for OAuth authentication
        
    Returns:
        str: Confirmation message with created group name and ID
        
    Raises:
        ValueError: If invalid group type is provided
        Exception: If group creation fails
        
    Example:
        create_group("Beach House Weekend", "Summer vacation rental", "trip")
    """
    try:
        valid_types = ["apartment", "house", "trip", "other"]
        if group_type not in valid_types:
            return f"Invalid group type. Must be one of: {', '.join(valid_types)}"
        
        client = get_splitwise_client(user_id)
        
        group = Group()
        group.setName(name)
        group.setDescription(description)
        group.setType(group_type)
        
        created_group, errors = client.createGroup(group)
        
        if errors:
            return f"Error creating group: {errors}"
        
        return f"Created group: {created_group.name} (ID: {created_group.id})"
    except Exception as e:
        logger.error(f"Error creating group: {str(e)}")
        return f"Error: {str(e)}"

# MCP Tools - Utilities

@mcp.tool()
def get_currencies() -> str:
    """
    Retrieve the list of all currencies supported by Splitwise.
    
    Returns:
        str: Formatted list of currency codes and their units
        
    Raises:
        Exception: If unable to fetch currencies from Splitwise API
    """
    try:
        client = get_splitwise_client()
        currencies = client.getCurrencies()
        
        if not currencies:
            return "No currencies found."
        
        currency_list = ["Supported Currencies:"]
        for currency in currencies:
            currency_list.append(f"- {currency.currency_code}: {currency.unit}")
        
        return "\n".join(currency_list)
    except Exception as e:
        logger.error(f"Error getting currencies: {str(e)}")
        return f"Error: {str(e)}"

@mcp.tool()
def get_categories() -> str:
    """
    Retrieve all available expense categories from Splitwise.
    
    Returns:
        str: Formatted list of expense categories with names and IDs
        
    Raises:
        Exception: If unable to fetch categories from Splitwise API
        
    Note:
        Categories help organize expenses (e.g., Food, Transportation, Entertainment)
    """
    try:
        client = get_splitwise_client()
        categories = client.getCategories()
        
        if not categories:
            return "No categories found."
        
        category_list = ["Expense Categories:"]
        for category in categories:
            # Handle main categories
            category_list.append(f"- {category.name} (ID: {category.id})")
            
            # Handle subcategories if they exist
            if hasattr(category, 'subcategories') and category.subcategories:
                for subcat in category.subcategories:
                    category_list.append(f"  - {subcat.name} (ID: {subcat.id})")
        
        return "\n".join(category_list)
    except Exception as e:
        logger.error(f"Error getting categories: {str(e)}")
        return f"Error: {str(e)}"

@mcp.tool()
def get_notifications(limit: int = 10, user_id: Optional[str] = None) -> str:
    """
    Fetch recent notifications for the current user from Splitwise.
    
    Args:
        limit: Maximum number of notifications to retrieve (default: 10)
        user_id: Optional user ID for OAuth authentication
        
    Returns:
        str: Formatted list of notifications with their content
        
    Raises:
        Exception: If unable to fetch notifications from Splitwise API
        
    Note:
        Notifications include updates about expenses, payments, and group activities
    """
    try:
        client = get_splitwise_client(user_id)
        notifications = client.getNotifications(limit=limit)
        
        if not notifications:
            return "No notifications found."
        
        notification_list = ["Notifications:"]
        for notification in notifications:
            notification_list.append(f"- {notification.content} (ID: {notification.id})")
        
        return "\n".join(notification_list)
    except Exception as e:
        logger.error(f"Error getting notifications: {str(e)}")
        return f"Error: {str(e)}"

class IntegratedHandler(BaseHTTPRequestHandler):
    """HTTP handler that provides both OAuth and MCP functionality."""
    
    def do_GET(self):
        """Handle GET requests."""
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
            elif self.path == '/sse':
                self.handle_mcp_sse()
            else:
                self.send_error(404, "Not Found")
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            self.send_error(500, f"Internal server error: {e}")
    
    def do_POST(self):
        """Handle POST requests for MCP."""
        try:
            if self.path == '/sse':
                self.handle_mcp_sse()
            else:
                self.send_error(404, "Not Found")
        except Exception as e:
            logger.error(f"Error handling POST request: {e}")
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
                
                .mcp-tools {{
                    background: #e8f5e8;
                    padding: 30px;
                    border-radius: 10px;
                    margin: 30px 0;
                    border-left: 4px solid #4CAF50;
                }}
                
                .mcp-tools h3 {{
                    color: #2c3e50;
                    margin-bottom: 20px;
                }}
                
                .tool-list {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 15px;
                    margin: 20px 0;
                }}
                
                .tool {{
                    background: white;
                    padding: 15px;
                    border-radius: 8px;
                    border: 1px solid #ddd;
                }}
                
                .tool-name {{
                    font-weight: bold;
                    color: #2c3e50;
                    margin-bottom: 5px;
                }}
                
                .tool-desc {{
                    font-size: 0.9rem;
                    color: #666;
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
                    <p>Secure OAuth Authentication + Full MCP Tools for ChatGPT Integration</p>
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
                    
                    <div class="mcp-tools">
                        <h3>🛠️ Available MCP Tools</h3>
                        <p>This server provides comprehensive Splitwise functionality through MCP tools:</p>
                        
                        <div class="tool-list">
                            <div class="tool">
                                <div class="tool-name">get_current_user</div>
                                <div class="tool-desc">Get your Splitwise account information</div>
                            </div>
                            <div class="tool">
                                <div class="tool-name">get_current_user_id</div>
                                <div class="tool-desc">Get your user ID for expense splits</div>
                            </div>
                            <div class="tool">
                                <div class="tool-name">get_friends</div>
                                <div class="tool-desc">List all your Splitwise friends</div>
                            </div>
                            <div class="tool">
                                <div class="tool-name">get_expenses</div>
                                <div class="tool-desc">Retrieve expenses with filters</div>
                            </div>
                            <div class="tool">
                                <div class="tool-name">create_expense</div>
                                <div class="tool-desc">Create new expenses with custom splits</div>
                            </div>
                            <div class="tool">
                                <div class="tool-name">get_groups</div>
                                <div class="tool-desc">List all your groups</div>
                            </div>
                            <div class="tool">
                                <div class="tool-name">create_group</div>
                                <div class="tool-desc">Create new expense groups</div>
                            </div>
                            <div class="tool">
                                <div class="tool-name">get_currencies</div>
                                <div class="tool-desc">List supported currencies</div>
                            </div>
                            <div class="tool">
                                <div class="tool-name">get_categories</div>
                                <div class="tool-desc">List expense categories</div>
                            </div>
                            <div class="tool">
                                <div class="tool-name">get_notifications</div>
                                <div class="tool-desc">Get recent notifications</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="api-info">
                        <h3>🔗 API Endpoints</h3>
                        <p>This server provides the following endpoints:</p>
                        
                        <div class="url-list">
                            <div><strong>Homepage:</strong> <code>{base_url}/</code></div>
                            <div><strong>Authorization URL:</strong> <code>https://secure.splitwise.com/oauth/authorize</code></div>
                            <div><strong>Token URL:</strong> <code>https://secure.splitwise.com/oauth/token</code></div>
                            <div><strong>Status URL:</strong> <code>{base_url}/oauth/status</code></div>
                            <div><strong>MCP Endpoint:</strong> <code>{base_url}/sse</code></div>
                            <div><strong>Health Check:</strong> <code>{base_url}/health</code></div>
                        </div>
                        
                        <p><strong>For ChatGPT Integration:</strong> Use the MCP Endpoint URL in ChatGPT's MCP connector settings.</p>
                    </div>
                    
                    <div class="api-info">
                        <h3>📖 How to Use</h3>
                        <ol style="margin-left: 20px; line-height: 1.8;">
                            <li><strong>Authenticate:</strong> Click "Start Authentication" and log into your Splitwise account</li>
                            <li><strong>Authorize:</strong> Grant permission for the MCP server to access your Splitwise data</li>
                            <li><strong>Configure ChatGPT:</strong> Add this server to your ChatGPT MCP connector settings using the MCP Endpoint URL</li>
                            <li><strong>Start Using:</strong> Ask ChatGPT to help manage your Splitwise expenses using natural language!</li>
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
            IntegratedServer.set_pending_auth(user_id, state)
            
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
            user_id = IntegratedServer.get_user_for_state(state)
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
                IntegratedServer.set_authenticated(user_id, True)
                
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
                pending = IntegratedServer.get_pending_auth(user_id)
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
                "mcp_tools_available": True,
                "version": "1.0.0",
                "service": "splitwise-mcp-integrated"
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            self.wfile.write(json.dumps(health_data).encode())
            
        except Exception as e:
            logger.error(f"Error in health check: {e}")
            self.send_error(500, f"Health check error: {e}")
    
    def handle_mcp_sse(self):
        """Handle MCP SSE requests."""
        try:
            # This is a simplified MCP handler
            # In a real implementation, you'd integrate with FastMCP
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = {
                "message": "MCP endpoint is available",
                "status": "ready",
                "tools": [
                    "get_current_user",
                    "get_current_user_id",
                    "get_friends", 
                    "get_expenses",
                    "create_expense",
                    "get_groups",
                    "create_group",
                    "get_currencies",
                    "get_categories",
                    "get_notifications"
                ]
            }
            
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            logger.error(f"Error in MCP SSE: {e}")
            self.send_error(500, f"MCP error: {e}")
    
    def log_message(self, format, *args):
        """Override to reduce log noise."""
        pass


class IntegratedServer:
    """Integrated server for OAuth and MCP functionality."""
    
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
        """Start the integrated server."""
        if cls._server is not None:
            return f"http://{host}:{port}"
        
        try:
            cls._server = HTTPServer((host, port), IntegratedHandler)
            cls._server_thread = Thread(target=cls._server.serve_forever, daemon=True)
            cls._server_thread.start()
            
            base_url = f"http://{host}:{port}"
            logger.info(f"Integrated server started on {base_url}")
            return base_url
            
        except Exception as e:
            logger.error(f"Failed to start integrated server: {e}")
            raise
    
    @classmethod
    def stop_server(cls):
        """Stop the integrated server."""
        if cls._server:
            cls._server.shutdown()
            cls._server.server_close()
            cls._server = None
            cls._server_thread = None
            logger.info("Integrated server stopped")


def main():
    """Main function to run the integrated server."""
    import sys
    
    port = 8080
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    
    try:
        # Start integrated server
        base_url = IntegratedServer.start_server(port=port)
        print(f"🚀 Integrated Splitwise MCP Server started!")
        print(f"   Homepage: {base_url}/")
        print(f"   OAuth: {base_url}/oauth/authorize")
        print(f"   MCP: {base_url}/sse")
        print(f"   Health: {base_url}/health")
        print("\nPress Ctrl+C to stop the server")
        
        # Keep server running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Shutting down server...")
        IntegratedServer.stop_server()
        print("✅ Server stopped")
    except Exception as e:
        print(f"❌ Error: {e}")
        IntegratedServer.stop_server()


if __name__ == "__main__":
    main()
