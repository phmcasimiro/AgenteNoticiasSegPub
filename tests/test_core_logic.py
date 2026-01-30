import pytest
import sqlite3
import os
from datetime import datetime
from unittest.mock import MagicMock, patch
from backend.models import NewsItem
from backend.database import get_connection, save_to_db, search_db, init_db

# --- Tests de Banco de Dados ---
# Usamos um banco em memória para isolamento total
# Usamos um banco em memória para isolamento total
# IMPORTANT: In-memory SQLite (:memory:) is fresh per connection unless shared via URI?cache=shared or same object.
# Since app logic calls get_connection() every time, we must patch get_connection to return the SAME connection object.

@pytest.fixture
def mock_db_path(monkeypatch):
    """Override get_connection using a custom proxy class"""
    
    real_conn = sqlite3.connect(":memory:")
    real_conn.row_factory = sqlite3.Row
    
    class ConnectionProxy:
        def __init__(self, conn):
            self.conn = conn
            self.row_factory = sqlite3.Row # support attribute access
        
        def cursor(self):
            return self.conn.cursor()
            
        def commit(self):
            return self.conn.commit()
            
        def execute(self, sql, params=()):
            return self.conn.execute(sql, params)
            
        def close(self):
            # No-op
            pass
            
        def __getattr__(self, name):
            # Delegate other attributes
            return getattr(self.conn, name)

    proxy = ConnectionProxy(real_conn)
    
    monkeypatch.setattr("backend.database.get_connection", lambda: proxy)
    
    # Initialize DB
    init_db()
    
    yield
    
    real_conn.close()

def test_save_and_retrieve_news(mock_db_path):
    """Test saving items and searching for them"""
    item = NewsItem(
        id="test_id_123",
        title="Police Operation in DF",
        url="http://test.com",
        publishedAt=datetime.now(),
        source="Test Source",
        snippet="A major operation happened in Brasilia",
        language="pt"
    )
    
    save_to_db([item])
    
    # Search by title keyword
    results = search_db("Operation")
    assert len(results) == 1
    assert results[0].id == "test_id_123"
    assert results[0].title == "Police Operation in DF"

def test_db_deduplication(mock_db_path):
    """Test INSERT OR IGNORE behavior"""
    item = NewsItem(
        id="dup_id",
        title="Original Title",
        url="http://test.com",
        publishedAt=datetime.now(),
        source="Test",
        snippet="Test",
        language="pt"
    )
    
    # First save
    save_to_db([item])
    
    # Verify it exists via public API
    results = search_db("Original")
    assert len(results) == 1, "Initial save failed"
    assert results[0].id == "dup_id"

    # Second save (should be ignored due to ID collision)
    save_to_db([item]) 
    
    # Verify we still have only 1
    results = search_db("Original")
    assert len(results) == 1, "Deduplication failed (found multiple or error)"

# --- Tests de Fetcher (Parsing) ---
from backend.fetchers import NewsFetcher

@patch("backend.fetchers.feedparser.parse")
def test_google_rss_parsing(mock_parse):
    """Test parsing of Google RSS feed"""
    # Mock feedparser response structure
    mock_entry = MagicMock()
    mock_entry.title = "Crimes drop in DF"
    mock_entry.link = "http://g1.com/news"
    mock_entry.summary = "Statistics show drop..."
    # published_parsed is a struct_time, let's mock validation passes or exception handling
    # The code checks hasattr(entry, 'published_parsed')
    del mock_entry.published_parsed 
    
    mock_feed = MagicMock()
    mock_feed.entries = [mock_entry]
    mock_parse.return_value = mock_feed
    
    fetcher = NewsFetcher()
    items = fetcher.fetch_google_rss("segurança")
    
    assert len(items) == 1
    assert items[0].title == "Crimes drop in DF"
    assert items[0].source == "Google News RSS"
