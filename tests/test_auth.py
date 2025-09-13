import pytest
from fastapi import HTTPException
import os

from src.main import verify_webhook_token


class TestVerifyWebhookToken:
    """Test the verify_webhook_token dependency function."""
    
    def test_valid_token_passes(self, set_webhook_token):
        """Test that a valid token is accepted."""
        # Token was set by fixture
        token = "test-webhook-token"
        
        result = verify_webhook_token(token)
        
        assert result == token

    def test_invalid_token_raises_401(self, set_webhook_token):
        """Test that an invalid token raises HTTPException with 401."""
        # Token was set to "test-webhook-token" by fixture
        invalid_token = "wrong-token"
        
        with pytest.raises(HTTPException) as exc_info:
            verify_webhook_token(invalid_token)
        
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Unauthorized"

    def test_none_token_raises_401(self, set_webhook_token):
        """Test that None token raises HTTPException with 401."""
        with pytest.raises(HTTPException) as exc_info:
            verify_webhook_token(None)
        
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Unauthorized"

    def test_empty_token_raises_401(self, set_webhook_token):
        """Test that empty string token raises HTTPException with 401.""" 
        with pytest.raises(HTTPException) as exc_info:
            verify_webhook_token("")
        
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Unauthorized"

    def test_no_env_variable_set(self, monkeypatch):
        """Test behavior when DIUN_WEBHOOK_TOKEN environment variable is not set."""
        # Remove the environment variable
        monkeypatch.delenv("DIUN_WEBHOOK_TOKEN", raising=False)
        
        # Any token should fail when env var is not set (None)
        with pytest.raises(HTTPException) as exc_info:
            verify_webhook_token("any-token")
        
        assert exc_info.value.status_code == 401

    def test_different_valid_token(self, monkeypatch):
        """Test with a different valid token."""
        custom_token = "my-custom-secret-token"
        monkeypatch.setenv("DIUN_WEBHOOK_TOKEN", custom_token)
        
        result = verify_webhook_token(custom_token)
        
        assert result == custom_token

    def test_case_sensitive_token(self, monkeypatch):
        """Test that token comparison is case-sensitive."""
        token = "CaseSensitiveToken"
        monkeypatch.setenv("DIUN_WEBHOOK_TOKEN", token)
        
        # Correct case should work
        result = verify_webhook_token(token)
        assert result == token
        
        # Wrong case should fail
        with pytest.raises(HTTPException):
            verify_webhook_token("casesensitivetoken")
        
        with pytest.raises(HTTPException):
            verify_webhook_token("CASESENSITIVETOKEN")

    def test_token_with_special_characters(self, monkeypatch):
        """Test tokens with special characters."""
        special_token = "token-with_special.chars@123!"
        monkeypatch.setenv("DIUN_WEBHOOK_TOKEN", special_token)
        
        result = verify_webhook_token(special_token)
        
        assert result == special_token

    def test_whitespace_in_token(self, monkeypatch):
        """Test that whitespace in tokens is preserved."""
        token_with_space = "token with space"
        monkeypatch.setenv("DIUN_WEBHOOK_TOKEN", token_with_space)
        
        result = verify_webhook_token(token_with_space)
        assert result == token_with_space
        
        # Token without space should fail
        with pytest.raises(HTTPException):
            verify_webhook_token("tokenwithspace")