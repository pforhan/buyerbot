import pytest
from unittest.mock import MagicMock, patch
from processor import sync_channel

def test_sync_channel_ignores_bot_posts():
    # Setup
    mock_client = MagicMock()
    mock_llm = MagicMock()
    
    # Mock auth.test to return bot user ID
    mock_client.auth_test.return_value = {"user_id": "B_BOT_123"}
    
    # Mock history
    mock_client.conversations_history.return_value = {
        "messages": [
            {"ts": "1", "user": "U_USER_1", "text": "FS: Macbook $1000"},
            {"ts": "2", "user": "B_BOT_123", "text": "I am a bot post"},
            {"ts": "3", "bot_id": "B_OTHER_BOT", "text": "Other bot post"}
        ]
    }
    
    # Mock LLM analysis
    mock_llm.analyze_post.return_value = [{"product_name": "Macbook", "price": "1000", "status": "Available"}]
    
    # Patch save_items_for_post to avoid DB calls
    with patch("processor.save_items_for_post") as mock_save:
        sync_channel(mock_client, "C1", "T1", mock_llm)
        
        # Verify
        # If the bot ignore logic is working, analyze_post should only be called once (for U_USER_1)
        assert mock_llm.analyze_post.call_count == 1
        mock_llm.analyze_post.assert_called_once()
        
        # Check first call args
        args, kwargs = mock_llm.analyze_post.call_args
        assert args[0] == "FS: Macbook $1000"

def test_sync_channel_ignores_bot_replies():
    # Setup
    mock_client = MagicMock()
    mock_llm = MagicMock()
    
    mock_client.auth_test.return_value = {"user_id": "B_BOT_123"}
    
    # Mock history with one user post that has replies
    mock_client.conversations_history.return_value = {
        "messages": [
            {"ts": "1", "user": "U_USER_1", "text": "FS: Macbook $1000", "thread_ts": "1", "reply_count": 2}
        ]
    }
    
    # Mock replies
    mock_client.conversations_replies.return_value = {
        "messages": [
            {"ts": "1", "user": "U_USER_1", "text": "FS: Macbook $1000"}, # Main post
            {"ts": "1.1", "user": "U_USER_2", "text": "Is it still available?"},
            {"ts": "1.2", "user": "B_BOT_123", "text": "New Sale listing: Macbook"} # Bot reply
        ]
    }
    
    mock_llm.analyze_post.return_value = []
    
    with patch("processor.save_items_for_post") as mock_save:
        sync_channel(mock_client, "C1", "T1", mock_llm)
        
        # Verify replies passed to LLM
        # Bot reply (ts 1.2) should be excluded
        mock_llm.analyze_post.assert_called_once_with("FS: Macbook $1000", ["Is it still available?"])

def test_sync_channel_filters_by_bot_id_when_auth_fails():
    # Setup
    mock_client = MagicMock()
    mock_llm = MagicMock()
    
    # Mock auth.test to RAISE an exception
    mock_client.auth_test.side_effect = Exception("Slack API Error")
    
    # Mock history with a bot post (has bot_id) and a user post
    mock_client.conversations_history.return_value = {
        "messages": [
            {"ts": "1", "user": "U_USER_1", "text": "FS: Macbook $1000"},
            {"ts": "2", "bot_id": "B_ANY_BOT", "text": "I am a bot"}
        ]
    }
    
    mock_llm.analyze_post.return_value = []
    
    with patch("processor.save_items_for_post") as mock_save:
        sync_channel(mock_client, "C1", "T1", mock_llm)
        
        # Verify
        # Even if auth_test failed, bot_id check should still filter out the second message
        assert mock_llm.analyze_post.call_count == 1
        mock_llm.analyze_post.assert_called_once()

def test_sync_channel_skips_non_root_messages():
    # Setup
    mock_client = MagicMock()
    mock_llm = MagicMock()
    
    mock_client.auth_test.return_value = {"user_id": "B_BOT_123"}
    
    # History includes a root message (ts 1) and its reply (ts 1.1)
    mock_client.conversations_history.return_value = {
        "messages": [
            {"ts": "1", "user": "U_1", "text": "Root message", "thread_ts": "1", "reply_count": 1},
            {"ts": "1.1", "user": "U_2", "text": "Reply message", "thread_ts": "1"}
        ]
    }
    
    # Replies for ts 1
    mock_client.conversations_replies.return_value = {
        "messages": [
            {"ts": "1", "user": "U_1", "text": "Root message"},
            {"ts": "1.1", "user": "U_2", "text": "Reply message"}
        ]
    }
    
    mock_llm.analyze_post.return_value = []
    
    with patch("processor.save_items_for_post") as mock_save:
        sync_channel(mock_client, "C1", "T1", mock_llm)
        
        # Should only be called for the root (ts 1)
        # If it were called for ts 1.1, the text would be "Reply message"
        mock_llm.analyze_post.assert_called_once_with("Root message", ["Reply message"])
        assert mock_llm.analyze_post.call_count == 1

def test_sync_channel_processes_root_from_reply():
    # Setup: The history only sees the reply (root is old/not in recent 50)
    mock_client = MagicMock()
    mock_llm = MagicMock()
    mock_client.auth_test.return_value = {"user_id": "B_BOT"}
    
    # History only has the reply
    mock_client.conversations_history.return_value = {
        "messages": [
            {"ts": "1.1", "user": "U_2", "text": "Reply message", "thread_ts": "1"}
        ]
    }
    
    # replies API returns the whole thread starting from root
    mock_client.conversations_replies.return_value = {
        "messages": [
            {"ts": "1", "user": "U_1", "text": "Old Root message"},
            {"ts": "1.1", "user": "U_2", "text": "Reply message"}
        ]
    }
    
    mock_llm.analyze_post.return_value = []
    
    with patch("processor.save_items_for_post") as mock_save:
        sync_channel(mock_client, "C1", "T1", mock_llm)
        
        # Should be called with the root text and the reply list
        mock_llm.analyze_post.assert_called_once_with("Old Root message", ["Reply message"])

def test_sync_channel_handles_items_in_replies():
    # Setup: Items are in replies, root is just "For sale (thread)"
    mock_client = MagicMock()
    mock_llm = MagicMock()
    mock_client.auth_test.return_value = {"user_id": "B_BOT"}
    
    mock_client.conversations_history.return_value = {
        "messages": [
            {"ts": "1", "user": "U_1", "text": "For sale (thread)", "thread_ts": "1", "reply_count": 1}
        ]
    }
    
    mock_client.conversations_replies.return_value = {
        "messages": [
            {"ts": "1", "user": "U_1", "text": "For sale (thread)"},
            {"ts": "1.1", "user": "U_1", "text": "Macbook Pro $1000"}
        ]
    }
    
    # LLM should see both texts and be able to extract
    mock_llm.analyze_post.return_value = [{"product_name": "Macbook Pro", "price": "1000"}]
    
    with patch("processor.save_items_for_post") as mock_save:
        sync_channel(mock_client, "C1", "T1", mock_llm)
        
        mock_llm.analyze_post.assert_called_once_with("For sale (thread)", ["Macbook Pro $1000"])
        mock_save.assert_called_once()
        args, kwargs = mock_save.call_args
        assert kwargs["slack_ts"] == "1"
        assert kwargs["user_id"] == "U_1"
