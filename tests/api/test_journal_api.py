# filepath: tests/integration/api/test_journal_api.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from backend.api.main import app
from shared.models.user import User
from shared.models.journal import JournalEntry
from datetime import datetime

# Mock authenticated user for tests
test_user = User(
    id="test-user-id",
    email="test@example.com",
    created_at=datetime.utcnow(),
    subscription_tier="free"
)

# Create test client
client = TestClient(app)

# Mock the get_current_user dependency
@pytest.fixture(autouse=True)
def override_get_current_user():
    with patch("backend.shared.auth.get_current_user", return_value=test_user):
        yield

# Mock CosmosService
@pytest.fixture(autouse=True)
def mock_cosmos_service():
    with patch("backend.shared.cosmos.CosmosService") as mock:
        # Setup mock return values
        instance = mock.return_value
        instance.get_journal_entries.return_value = [
            JournalEntry(
                id="test-entry-1",
                user_id=test_user.id,
                content="Test journal entry",
                created_at=datetime.utcnow(),
                mood_indicators=["calm", "focused"],
                mood_score=7
            )
        ]
        
        instance.create_journal_entry.return_value = JournalEntry(
            id="new-entry-id",
            user_id=test_user.id,
            content="New test entry",
            created_at=datetime.utcnow(),
            mood_indicators=["happy"],
            mood_score=8
        )
        
        yield mock

# Mock KernelService
@pytest.fixture(autouse=True)
def mock_kernel_service():
    with patch("backend.shared.kernel.KernelService") as mock:
        instance = mock.return_value
        instance.analyze_journal_entry.return_value = {
            "insights": "Test insights"
        }
        instance.generate_journal_prompt.return_value = "What made you happy today?"
        yield mock

def test_get_journal_entries():
    """Test retrieving journal entries"""
    response = client.get("/api/journal/")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["content"] == "Test journal entry"

def test_create_journal_entry():
    """Test creating a journal entry"""
    entry_data = {
        "content": "New test entry",
        "mood_indicators": ["happy"],
        "mood_score": 8
    }
    
    response = client.post("/api/journal/", json=entry_data)
    assert response.status_code == 200
    result = response.json()
    assert result["content"] == "New test entry"
    assert result["user_id"] == test_user.id

def test_generate_journal_prompt():
    """Test generating a journal prompt"""
    response = client.post("/api/journal/prompt", params={"mood": "happy"})
    assert response.status_code == 200
    assert response.json()["prompt"] == "What made you happy today?"