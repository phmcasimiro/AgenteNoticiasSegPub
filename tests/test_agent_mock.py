import pytest
from unittest.mock import MagicMock, patch
from groq import Groq, RateLimitError
from backend.agent import get_agent_response

@patch("backend.agent.Groq")
@patch("backend.agent.get_gemini_response")
def test_groq_fallback(mock_gemini, mock_groq_class):
    """Test that RateLimitError in Groq triggers Gemini fallback"""
    # Setup Groq Mock to raise RateLimitError
    mock_client = MagicMock()
    mock_groq_class.return_value = mock_client
    
    # Simulate RateLimitError on chat.completions.create
    # Need to verify exception init args if strictly checking, but generic exception works for flow
    error_response = MagicMock()
    error_response.status_code = 429
    mock_client.chat.completions.create.side_effect = RateLimitError(
        message="Rate limit exceeded", 
        response=error_response,
        body=None
    )
    
    # Setup Gemini Mock response
    mock_gemini.return_value = "[Mojo Fallback - Gemini] Resposta do Fallback"
    
    response = get_agent_response("Qual a situação?", api_key="test_key")
    
    # Verify fallback was called
    mock_gemini.assert_called_once()
    assert "[Mojo Fallback - Gemini]" in response

@patch("backend.agent.Groq")
def test_groq_success(mock_groq_class):
    """Test successful Groq response"""
    mock_client = MagicMock()
    mock_groq_class.return_value = mock_client
    
    mock_completion = MagicMock()
    mock_completion.choices[0].message.content = "Resposta Original Groq"
    mock_completion.choices[0].message.tool_calls = None
    
    mock_client.chat.completions.create.return_value = mock_completion
    
    response = get_agent_response("Teste", api_key="test_key")
    
    assert response == "Resposta Original Groq"
