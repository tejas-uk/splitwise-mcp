#!/usr/bin/env python3
"""Splitwise MCP Server implementation using FastMCP framework."""

import os
import logging
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv
from fastmcp import FastMCP
from splitwise import Splitwise
from splitwise.expense import Expense
from splitwise.group import Group
from splitwise.user import ExpenseUser

# Import OAuth components
from .oauth_server import start_oauth_flow, complete_oauth_flow, wait_for_oauth_callback
from .token_storage import get_token_storage, store_oauth_token, get_oauth_token, revoke_oauth_token
from .web_oauth_server import start_web_oauth_server, get_authorization_url, get_status_url

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("splitwise-fastmcp")

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


# User Management Tools

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


# Expense Management Tools

@mcp.tool()
def get_expenses(
    group_id: Optional[int] = None,
    friend_id: Optional[int] = None,
    limit: int = 10
) -> str:
    """
    Retrieve a list of expenses with optional filtering by group or friend.
    
    Args:
        group_id: Optional group ID to filter expenses by specific group
        friend_id: Optional friend ID to filter expenses involving specific friend
        limit: Maximum number of expenses to return (default: 10)
        
    Returns:
        str: Formatted list of expenses with description, cost, and currency
        
    Raises:
        Exception: If unable to fetch expenses from Splitwise API
    """
    try:
        client = get_splitwise_client()
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
    group_id: Optional[int] = None
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
                     
    Returns:
        str: Confirmation message with created expense details
        
    Raises:
        ValueError: If user_splits is empty or invalid
        Exception: If expense creation fails or validation errors occur
        
    Example:
        # You (ID: 79774) paid $100 for dinner, split equally with friend (ID: 12345)
        create_expense("Dinner", "100.00", 
                      user_splits=[
                          {"user_id": 79774, "paid_share": "100.00", "owed_share": "50.00"},
                          {"user_id": 12345, "paid_share": "0.00", "owed_share": "50.00"}
                      ])
                      
        # Split $90 three ways, you paid nothing (IDs: 79774=you, 12345=friend1, 67890=friend2)
        create_expense("Uber ride", "90.00",
                      user_splits=[
                          {"user_id": 79774, "paid_share": "0.00", "owed_share": "30.00"},
                          {"user_id": 12345, "paid_share": "90.00", "owed_share": "30.00"},
                          {"user_id": 67890, "paid_share": "0.00", "owed_share": "30.00"}
                      ])
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
        
        client = get_splitwise_client()
        
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


# Group Management Tools

@mcp.tool()
def get_groups() -> str:
    """
    Retrieve all groups associated with the current user.
    
    Returns:
        str: Formatted list of groups with names, IDs, and member counts
        
    Raises:
        Exception: If unable to fetch groups from Splitwise API
    """
    try:
        client = get_splitwise_client()
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
    group_type: str = "other"
) -> str:
    """
    Create a new expense sharing group in Splitwise.
    
    Args:
        name: Name of the group (e.g., "Europe Trip 2024")
        description: Optional description providing more details about the group
        group_type: Type of group - one of: apartment, house, trip, other (default: other)
        
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
        
        client = get_splitwise_client()
        
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


# Utility Tools

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
def get_notifications(limit: int = 10) -> str:
    """
    Fetch recent notifications for the current user from Splitwise.
    
    Args:
        limit: Maximum number of notifications to retrieve (default: 10)
        
    Returns:
        str: Formatted list of notifications with their content
        
    Raises:
        Exception: If unable to fetch notifications from Splitwise API
        
    Note:
        Notifications include updates about expenses, payments, and group activities
    """
    try:
        client = get_splitwise_client()
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


# OAuth Authentication Tools

@mcp.tool()
def start_oauth_authentication(port: int = 8080) -> str:
    """
    Start OAuth authentication flow for Splitwise.
    
    This will open a browser window for the user to authenticate with Splitwise.
    After authentication, use complete_oauth_authentication() to finish the process.
    
    Args:
        port: Port for OAuth callback server (default: 8080)
        
    Returns:
        str: Instructions and authorization URL for OAuth flow
        
    Raises:
        Exception: If OAuth flow cannot be started
    """
    try:
        consumer_key = os.getenv("SPLITWISE_CONSUMER_KEY")
        consumer_secret = os.getenv("SPLITWISE_CONSUMER_SECRET")
        
        if not consumer_key or not consumer_secret:
            return "Error: SPLITWISE_CONSUMER_KEY and SPLITWISE_CONSUMER_SECRET must be set"
        
        result = start_oauth_flow(consumer_key, consumer_secret, port)
        
        return (f"OAuth authentication started!\n\n"
                f"Authorization URL: {result['authorization_url']}\n"
                f"State: {result['state']}\n\n"
                f"Instructions:\n{result['instructions']}\n\n"
                f"After completing authentication, use complete_oauth_authentication() "
                f"with the returned code and state.")
        
    except Exception as e:
        logger.error(f"Error starting OAuth authentication: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
def complete_oauth_authentication(code: str, state: str, user_id: str) -> str:
    """
    Complete OAuth authentication flow by exchanging code for access token.
    
    Args:
        code: Authorization code from OAuth callback
        state: State parameter from OAuth callback
        user_id: Unique identifier for the user (for token storage)
        
    Returns:
        str: Success message with authentication status
        
    Raises:
        Exception: If OAuth completion fails
    """
    try:
        consumer_key = os.getenv("SPLITWISE_CONSUMER_KEY")
        consumer_secret = os.getenv("SPLITWISE_CONSUMER_SECRET")
        
        if not consumer_key or not consumer_secret:
            return "Error: SPLITWISE_CONSUMER_KEY and SPLITWISE_CONSUMER_SECRET must be set"
        
        # Exchange code for access token
        access_token = complete_oauth_flow(consumer_key, consumer_secret, code, state)
        
        # Store the token
        success = store_oauth_token(user_id, access_token)
        
        if success:
            return (f"OAuth authentication completed successfully!\n"
                    f"User ID: {user_id}\n"
                    f"Access token stored securely.\n\n"
                    f"You can now use all Splitwise MCP tools with OAuth authentication.")
        else:
            return "Error: Failed to store OAuth token"
        
    except Exception as e:
        logger.error(f"Error completing OAuth authentication: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
def check_oauth_status(user_id: str) -> str:
    """
    Check OAuth authentication status for a user.
    
    Args:
        user_id: Unique identifier for the user
        
    Returns:
        str: Authentication status and token information
    """
    try:
        token_data = get_oauth_token(user_id)
        
        if token_data:
            return (f"OAuth Status: Authenticated\n"
                    f"User ID: {user_id}\n"
                    f"Token Type: {token_data.get('token_type', 'Unknown')}\n"
                    f"Created: {token_data.get('created_at', 'Unknown')}\n"
                    f"Expires In: {token_data.get('expires_in', 'Unknown')} seconds")
        else:
            return f"OAuth Status: Not authenticated\nUser ID: {user_id}\nNo valid token found."
        
    except Exception as e:
        logger.error(f"Error checking OAuth status: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
def revoke_oauth_authentication(user_id: str) -> str:
    """
    Revoke OAuth authentication for a user.
    
    Args:
        user_id: Unique identifier for the user
        
    Returns:
        str: Confirmation message
    """
    try:
        success = revoke_oauth_token(user_id)
        
        if success:
            return f"OAuth authentication revoked for user: {user_id}"
        else:
            return f"No OAuth token found for user: {user_id}"
        
    except Exception as e:
        logger.error(f"Error revoking OAuth authentication: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
def list_oauth_users() -> str:
    """
    List all users with OAuth authentication.
    
    Returns:
        str: List of users with stored OAuth tokens
    """
    try:
        storage = get_token_storage()
        users = storage.list_users()
        
        if users:
            user_list = ["Users with OAuth authentication:"]
            for user_id in users:
                user_list.append(f"- {user_id}")
            return "\n".join(user_list)
        else:
            return "No users with OAuth authentication found."
        
    except Exception as e:
        logger.error(f"Error listing OAuth users: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
def get_oauth_storage_info() -> str:
    """
    Get information about OAuth token storage.
    
    Returns:
        str: Storage information and statistics
    """
    try:
        storage = get_token_storage()
        info = storage.get_storage_info()
        
        return (f"OAuth Token Storage Information:\n"
                f"Storage Directory: {info.get('storage_dir', 'Unknown')}\n"
                f"Tokens File: {info.get('tokens_file', 'Unknown')}\n"
                f"Key File: {info.get('key_file', 'Unknown')}\n"
                f"User Count: {info.get('user_count', 0)}\n"
                f"Users: {', '.join(info.get('users', []))}")
        
    except Exception as e:
        logger.error(f"Error getting OAuth storage info: {e}")
        return f"Error: {str(e)}"


# ChatGPT Integration Tools

@mcp.tool()
def start_chatgpt_oauth_server(host: str = "0.0.0.0", port: int = 8080) -> str:
    """
    Start web OAuth server for ChatGPT integration.
    
    This creates a web server that ChatGPT can redirect users to for OAuth authentication.
    The server provides a web interface for users to authenticate with Splitwise.
    
    Args:
        host: Host to bind to (default: 0.0.0.0 for external access)
        port: Port to bind to (default: 8080)
        
    Returns:
        str: Server information and URLs for ChatGPT integration
        
    Note:
        This is specifically designed for ChatGPT MCP connector integration.
        Users will be redirected to the authorization URL to authenticate.
    """
    try:
        # Start web OAuth server
        base_url = start_web_oauth_server(host, port)
        
        return (f"ChatGPT OAuth server started successfully!\n\n"
                f"Server URL: {base_url}\n"
                f"Authorization URL: {get_authorization_url()}\n"
                f"Status URL: {get_status_url()}\n\n"
                f"Configuration for ChatGPT:\n"
                f"- OAuth Authorization URL: {get_authorization_url()}\n"
                f"- OAuth Token URL: {base_url}/oauth/callback\n"
                f"- OAuth Status URL: {get_status_url()}\n\n"
                f"Users can now authenticate by visiting the authorization URL.")
        
    except Exception as e:
        logger.error(f"Error starting ChatGPT OAuth server: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
def get_chatgpt_oauth_urls(user_id: str = "default_user") -> str:
    """
    Get OAuth URLs for ChatGPT integration.
    
    Args:
        user_id: User identifier for OAuth flow
        
    Returns:
        str: OAuth URLs and instructions for ChatGPT
    """
    try:
        auth_url = get_authorization_url(user_id)
        status_url = get_status_url(user_id)
        
        return (f"ChatGPT OAuth Integration URLs:\n\n"
                f"User ID: {user_id}\n"
                f"Authorization URL: {auth_url}\n"
                f"Status Check URL: {status_url}\n\n"
                f"Instructions for ChatGPT:\n"
                f"1. Redirect user to: {auth_url}\n"
                f"2. User completes authentication in browser\n"
                f"3. Check status at: {status_url}\n"
                f"4. Use user_id '{user_id}' for API calls")
        
    except Exception as e:
        logger.error(f"Error getting ChatGPT OAuth URLs: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
def check_chatgpt_oauth_status(user_id: str = "default_user") -> str:
    """
    Check OAuth authentication status for ChatGPT integration.
    
    Args:
        user_id: User identifier to check
        
    Returns:
        str: Authentication status and token information
    """
    try:
        # Check if user has valid token
        token_data = get_oauth_token(user_id)
        
        if token_data:
            return (f"✅ OAuth Status: Authenticated\n"
                    f"User ID: {user_id}\n"
                    f"Token Type: {token_data.get('token_type', 'Unknown')}\n"
                    f"Created: {token_data.get('created_at', 'Unknown')}\n"
                    f"Expires In: {token_data.get('expires_in', 'Unknown')} seconds\n\n"
                    f"User is ready to use Splitwise MCP tools.")
        else:
            return (f"❌ OAuth Status: Not authenticated\n"
                    f"User ID: {user_id}\n"
                    f"No valid token found.\n\n"
                    f"User needs to complete OAuth authentication first.")
        
    except Exception as e:
        logger.error(f"Error checking ChatGPT OAuth status: {e}")
        return f"Error: {str(e)}"


def main():
    """Run the FastMCP server."""
    mcp.run()


if __name__ == "__main__":
    main()