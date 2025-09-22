#!/usr/bin/env python3
"""Tests for the FastMCP Splitwise server implementation."""

import os
import sys
import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from splitwise_mcp import fastmcp_server
from splitwise.user import User
from splitwise.expense import Expense
from splitwise.group import Group
from splitwise.currency import Currency
from splitwise.category import Category


class TestSplitwiseFastMCPServer:
    """Test suite for FastMCP Splitwise server."""
    
    @pytest.fixture
    def mock_splitwise_client(self):
        """Create a mock Splitwise client."""
        with patch('splitwise_mcp.fastmcp_server.get_splitwise_client') as mock_get_client:
            mock_client = Mock()
            mock_get_client.return_value = mock_client
            yield mock_client
    
    def test_get_current_user(self, mock_splitwise_client):
        """Test getting current user information."""
        # Setup mock user
        mock_user = Mock(spec=User)
        mock_user.first_name = "John"
        mock_user.last_name = "Doe"
        mock_user.email = "john.doe@example.com"
        mock_splitwise_client.getCurrentUser.return_value = mock_user
        
        # Call the tool
        result = fastmcp_server.get_current_user()
        
        # Verify
        assert result == "Current user: John Doe (john.doe@example.com)"
        mock_splitwise_client.getCurrentUser.assert_called_once()
    
    def test_get_friends(self, mock_splitwise_client):
        """Test retrieving friends list."""
        # Setup mock friends
        friend1 = Mock()
        friend1.first_name = "Alice"
        friend1.last_name = "Smith"
        friend1.id = 123
        
        friend2 = Mock()
        friend2.first_name = "Bob"
        friend2.last_name = "Johnson"
        friend2.id = 456
        
        mock_splitwise_client.getFriends.return_value = [friend1, friend2]
        
        # Call the tool
        result = fastmcp_server.get_friends()
        
        # Verify
        assert "Friends:" in result
        assert "Alice Smith (ID: 123)" in result
        assert "Bob Johnson (ID: 456)" in result
        mock_splitwise_client.getFriends.assert_called_once()
    
    def test_get_friends_empty(self, mock_splitwise_client):
        """Test getting friends when list is empty."""
        mock_splitwise_client.getFriends.return_value = []
        
        result = fastmcp_server.get_friends()
        
        assert result == "No friends found in your Splitwise account."
    
    def test_get_expenses(self, mock_splitwise_client):
        """Test retrieving expenses."""
        # Setup mock expenses
        expense1 = Mock(spec=Expense)
        expense1.description = "Dinner"
        expense1.cost = "50.00"
        expense1.currency_code = "USD"
        expense1.id = 1001
        
        expense2 = Mock(spec=Expense)
        expense2.description = "Movie tickets"
        expense2.cost = "30.00"
        expense2.currency_code = "USD"
        expense2.id = 1002
        
        mock_splitwise_client.getExpenses.return_value = [expense1, expense2]
        
        # Call the tool
        result = fastmcp_server.get_expenses(limit=5)
        
        # Verify
        assert "Expenses:" in result
        assert "Dinner: 50.00 USD (ID: 1001)" in result
        assert "Movie tickets: 30.00 USD (ID: 1002)" in result
        mock_splitwise_client.getExpenses.assert_called_once_with(
            group_id=None,
            friend_id=None,
            limit=5
        )
    
    def test_create_expense_success(self, mock_splitwise_client):
        """Test creating an expense successfully."""
        # Setup mock current user
        mock_user = Mock()
        mock_user.id = 999
        mock_splitwise_client.getCurrentUser.return_value = mock_user
        
        # Setup mock created expense
        created_expense = Mock(spec=Expense)
        created_expense.description = "Lunch"
        created_expense.cost = "25.00"
        created_expense.currency_code = "USD"
        created_expense.id = 2001
        
        mock_splitwise_client.createExpense.return_value = (created_expense, None)
        
        # Call the tool
        result = fastmcp_server.create_expense(
            description="Lunch",
            cost="25.00",
            currency_code="USD"
        )
        
        # Verify
        assert "Created expense: Lunch - 25.00 USD (ID: 2001)" in result
        mock_splitwise_client.createExpense.assert_called_once()
    
    def test_create_expense_with_error(self, mock_splitwise_client):
        """Test expense creation with error."""
        mock_splitwise_client.createExpense.return_value = (None, "Invalid expense data")
        
        result = fastmcp_server.create_expense(
            description="Test",
            cost="10.00"
        )
        
        assert "Error creating expense: Invalid expense data" in result
    
    def test_get_groups(self, mock_splitwise_client):
        """Test retrieving groups."""
        # Setup mock groups
        group1 = Mock(spec=Group)
        group1.name = "Apartment"
        group1.id = 5001
        group1.members = [Mock(), Mock(), Mock()]
        
        group2 = Mock(spec=Group)
        group2.name = "Road Trip"
        group2.id = 5002
        group2.members = [Mock(), Mock()]
        
        mock_splitwise_client.getGroups.return_value = [group1, group2]
        
        # Call the tool
        result = fastmcp_server.get_groups()
        
        # Verify
        assert "Groups:" in result
        assert "Apartment (ID: 5001, Members: 3)" in result
        assert "Road Trip (ID: 5002, Members: 2)" in result
        mock_splitwise_client.getGroups.assert_called_once()
    
    def test_create_group_success(self, mock_splitwise_client):
        """Test creating a group successfully."""
        # Setup mock created group
        created_group = Mock(spec=Group)
        created_group.name = "Summer House"
        created_group.id = 6001
        
        mock_splitwise_client.createGroup.return_value = (created_group, None)
        
        # Call the tool
        result = fastmcp_server.create_group(
            name="Summer House",
            description="Beach vacation",
            group_type="trip"
        )
        
        # Verify
        assert "Created group: Summer House (ID: 6001)" in result
        mock_splitwise_client.createGroup.assert_called_once()
    
    def test_create_group_invalid_type(self, mock_splitwise_client):
        """Test creating group with invalid type."""
        result = fastmcp_server.create_group(
            name="Test Group",
            group_type="invalid"
        )
        
        assert "Invalid group type" in result
        assert "apartment, house, trip, other" in result
        mock_splitwise_client.createGroup.assert_not_called()
    
    def test_get_currencies(self, mock_splitwise_client):
        """Test retrieving currencies."""
        # Setup mock currencies
        currency1 = Mock(spec=Currency)
        currency1.currency_code = "USD"
        currency1.unit = "$"
        
        currency2 = Mock(spec=Currency)
        currency2.currency_code = "EUR"
        currency2.unit = "€"
        
        mock_splitwise_client.getCurrencies.return_value = [currency1, currency2]
        
        # Call the tool
        result = fastmcp_server.get_currencies()
        
        # Verify
        assert "Supported Currencies:" in result
        assert "USD: $" in result
        assert "EUR: €" in result
        mock_splitwise_client.getCurrencies.assert_called_once()
    
    def test_get_categories(self, mock_splitwise_client):
        """Test retrieving categories."""
        # Setup mock categories
        category1 = Mock(spec=Category)
        category1.name = "Food and drink"
        category1.id = 1
        category1.subcategories = []
        
        category2 = Mock(spec=Category)
        category2.name = "Transportation"
        category2.id = 2
        
        # Setup subcategories
        subcat1 = Mock()
        subcat1.name = "Taxi"
        subcat1.id = 21
        
        subcat2 = Mock()
        subcat2.name = "Bus/train"
        subcat2.id = 22
        
        category2.subcategories = [subcat1, subcat2]
        
        mock_splitwise_client.getCategories.return_value = [category1, category2]
        
        # Call the tool
        result = fastmcp_server.get_categories()
        
        # Verify
        assert "Expense Categories:" in result
        assert "Food and drink (ID: 1)" in result
        assert "Transportation (ID: 2)" in result
        assert "  - Taxi (ID: 21)" in result
        assert "  - Bus/train (ID: 22)" in result
        mock_splitwise_client.getCategories.assert_called_once()
    
    def test_get_notifications(self, mock_splitwise_client):
        """Test retrieving notifications."""
        # Setup mock notifications
        notification1 = Mock()
        notification1.content = "John paid you $25.00"
        notification1.id = 8001
        
        notification2 = Mock()
        notification2.content = "You added 'Dinner' expense"
        notification2.id = 8002
        
        mock_splitwise_client.getNotifications.return_value = [notification1, notification2]
        
        # Call the tool
        result = fastmcp_server.get_notifications(limit=20)
        
        # Verify
        assert "Notifications:" in result
        assert "John paid you $25.00 (ID: 8001)" in result
        assert "You added 'Dinner' expense (ID: 8002)" in result
        mock_splitwise_client.getNotifications.assert_called_once_with(limit=20)
    
    def test_error_handling(self, mock_splitwise_client):
        """Test error handling in tools."""
        # Simulate an API error
        mock_splitwise_client.getCurrentUser.side_effect = Exception("API Error")
        
        result = fastmcp_server.get_current_user()
        
        assert "Error: API Error" in result
    
    def test_environment_validation(self):
        """Test that client initialization validates environment variables."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="SPLITWISE_CONSUMER_KEY"):
                fastmcp_server.get_splitwise_client()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])