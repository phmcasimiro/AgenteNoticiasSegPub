import pytest
import os

# Setup Environment for Test BEFORE importing app
os.environ["APP_API_KEY"] = "test_key"

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health_check_public():
    """Health Check should be public"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_news_unauthorized():
    """Accessing /news without key should fail"""
    response = client.get("/news?q=teste")
    assert response.status_code == 401
    assert "Invalid or missing API Key" in response.json()["detail"]

def test_news_authorized_empty():
    """Accessing /news with key should work (mocking data or empty)"""
    # Note: This might hit external APIs if not mocked. 
    # Ideally we mock search_db/external search, but for integration test:
    headers = {"X-API-Key": "test_key"}
    response = client.get("/news?q=policia_teste_mock", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_chat_authorized():
    """Accessing /chat with key should work"""
    headers = {"X-API-Key": "test_key"}
    # Mocking Agent would be better, but we check if auth passes
    # We expect 200 or 500 (if Groq fails), but NOT 401
    response = client.get("/chat?q=ola", headers=headers)
    assert response.status_code != 401
