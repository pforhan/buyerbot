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
    mock_llm.analyze_post.return_value = [{"product_name": "Macbook", "price": "1000", "status": "Available", "post_type": "Sale"}]
    
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
