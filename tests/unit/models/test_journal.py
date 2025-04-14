import pytest
from pydantic import ValidationError
from shared.models.journal import JournalEntryBase, JournalEntryCreate, JournalEntryUpdate, JournalEntryInDB
from datetime import datetime
import uuid

def test_journal_entry_base():
    # Test valid JournalEntryBase
    entry = JournalEntryBase(content="Today was a good day", mood_indicators=["happy", "relaxed"], mood_score=8)
    assert entry.content == "Today was a good day"
    assert entry.mood_indicators == ["happy", "relaxed"]
    assert entry.mood_score == 8

    # Test invalid mood_score
    with pytest.raises(ValidationError):
        JournalEntryBase(content="Invalid mood score", mood_score=11)

    # Test empty content
    with pytest.raises(ValidationError):
        JournalEntryBase(content="")

def test_journal_entry_create():
    # Test JournalEntryCreate inherits correctly
    entry = JournalEntryCreate(content="Creating a new entry", mood_indicators=["excited"], mood_score=9)
    assert entry.content == "Creating a new entry"
    assert entry.mood_indicators == ["excited"]
    assert entry.mood_score == 9

def test_journal_entry_update():
    # Test JournalEntryUpdate with partial updates
    entry = JournalEntryUpdate(content="Updated content")
    assert entry.content == "Updated content"
    assert entry.mood_indicators is None
    assert entry.mood_score is None

def test_journal_entry_in_db():
    # Test JournalEntryInDB default values
    entry = JournalEntryInDB(content="Database entry", user_id="user123")
    assert entry.id is not None
    assert uuid.UUID(entry.id)  # Check if id is a valid UUID
    assert entry.user_id == "user123"
    assert entry.created_at <= datetime.utcnow()
    assert entry.updated_at is None
    assert entry.ai_insights is None
    assert entry.sentiment_score is None

    # Test JournalEntryInDB with all fields
    entry = JournalEntryInDB(
        content="Full entry",
        user_id="user456",
        ai_insights={"key": "value"},
        sentiment_score=0.85
    )
    assert entry.ai_insights == {"key": "value"}
    assert entry.sentiment_score == 0.85