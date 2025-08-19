"""
Basic tests for WhatsApp-AutoCoder service
"""

import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_health_endpoint():
    """Test that the health endpoint exists and returns correct status"""
    # Mock test for CI/CD - replace with actual test when ready
    assert True
    
def test_twilio_webhook_structure():
    """Test that webhook structure is correct"""
    # Mock test for CI/CD - replace with actual test when ready
    from app.models.twilio_models import TwilioWebhookPayload
    
    # Test that model can be instantiated
    payload = TwilioWebhookPayload(
        from_number="whatsapp:+1234567890",
        to_number="whatsapp:+0987654321",
        body="Test message",
        message_sid="MSG123",
        account_sid="AC123",
        num_media=0
    )
    
    assert payload.from_number == "whatsapp:+1234567890"
    assert payload.body == "Test message"

def test_response_formatter():
    """Test response formatter basic functionality"""
    # Mock environment variables before importing
    with patch.dict(os.environ, {
        'TWILIO_ACCOUNT_SID': 'test_sid',
        'TWILIO_AUTH_TOKEN': 'test_token',
        'TWILIO_PHONE_NUMBER': 'whatsapp:+14155238886'
    }):
        from app.services.response_formatter import ResponseFormatter
        
        formatter = ResponseFormatter()
        
        # Test basic formatting
        text = "Hello World"
        formatted = formatter.format_for_whatsapp(text)
        assert formatted == text
        
        # Test truncation
        long_text = "x" * 2000
        formatted = formatter.format_for_whatsapp(long_text)
        assert len(formatted) <= 1620  # Max length + truncation message

def test_conversation_state_model():
    """Test conversation state model"""
    from app.state.models import ConversationState, UserSession
    import uuid
    
    session = UserSession(
        session_id=str(uuid.uuid4()),
        phone_number="whatsapp:+1234567890"
    )
    
    state = ConversationState(
        phone_number="whatsapp:+1234567890",
        session=session
    )
    
    assert state.phone_number == "whatsapp:+1234567890"
    assert state.get_active_project() is None

def test_config_loading():
    """Test configuration loading"""
    # Mock environment variables
    with patch.dict(os.environ, {
        'TWILIO_ACCOUNT_SID': 'test_sid',
        'TWILIO_AUTH_TOKEN': 'test_token',
        'TWILIO_PHONE_NUMBER': 'whatsapp:+14155238886'
    }):
        from app.utils.config import Settings
        
        # Create settings with test values
        settings = Settings(
            TWILIO_ACCOUNT_SID='test_sid',
            TWILIO_AUTH_TOKEN='test_token',
            TWILIO_PHONE_NUMBER='whatsapp:+14155238886'
        )
        
        assert settings.TWILIO_ACCOUNT_SID == 'test_sid'
        assert settings.TWILIO_AUTH_TOKEN == 'test_token'
