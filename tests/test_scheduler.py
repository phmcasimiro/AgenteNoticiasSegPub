import pytest
import os
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient
from datetime import datetime

# Setup Environment
os.environ["APP_API_KEY"] = "test_key"
os.environ["REDIS_URL"] = "redis://localhost:6379/0" 

# Import AFTER env setup
from backend.main import app, scheduler

client = TestClient(app)

@pytest.fixture
def mock_fetcher():
    with patch("backend.main.fetcher") as mock:
        yield mock

@pytest.fixture
def mock_save_db():
    with patch("backend.main.save_to_db") as mock:
        yield mock

def test_force_fetch_endpoint(mock_fetcher, mock_save_db):
    """Test /force-fetch triggers the job immediately"""
    
    # Mock return of fetch_all
    mock_fetcher.fetch_all.return_value = [
        {"id": "1", "title": "Test News", "url": "http://test.com", "publishedAt": datetime.now(), "source": "Test", "snippet": "Test", "language": "pt"}
    ]
    
    headers = {"X-API-Key": "test_key"}
    response = client.post("/force-fetch", headers=headers)
    
    assert response.status_code == 200
    assert response.json()["status"] == "Fetch triggered"
    
    # Verify fetcher was called
    mock_fetcher.fetch_all.assert_called_once()
    # Verify save_to_db was called
    mock_save_db.assert_called_once()

def test_scheduler_jobs_configured():
    """Verify that jobs are scheduled for 11:00 and 23:00"""
    with TestClient(app):
        # Startup event runs here, so jobs should be added
        jobs = scheduler.get_jobs()
        # We expect at least 2 jobs
        assert len(jobs) >= 2
        
        # Simpler check: string representation of trigger usually shows cron params
        job_descriptions = [str(job.trigger) for job in jobs]
        
        # Check if we have our specific cron times
        # "cron[hour='11', minute='0']"
        # The string representation might vary, so let's check trigger fields directly if possible or loose string match
        has_11 = any("hour='11'" in d and "minute='0'" in d for d in job_descriptions)
        has_23 = any("hour='23'" in d and "minute='0'" in d for d in job_descriptions)
        
        assert has_11, f"Job for 11:00 not found in {job_descriptions}"
        assert has_23, f"Job for 23:00 not found in {job_descriptions}"
