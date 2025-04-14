import pytest
from shared.models.mood import MoodLogBase, MoodLogCreate, MoodLogInDB, MoodLog
from datetime import datetime
from pydantic import ValidationError

def test_mood_log_base_valid():
    mood_log = MoodLogBase(
        mood_score=5,
        mood_labels=["happy", "calm"],
        context="Had a good day",
        factors=["exercise", "good sleep"]
    )
    assert mood_log.mood_score == 5
    assert mood_log.mood_labels == ["happy", "calm"]
    assert mood_log.context == "Had a good day"
    assert mood_log.factors == ["exercise", "good sleep"]

def test_mood_log_base_invalid_score():
    with pytest.raises(ValidationError):
        MoodLogBase(mood_score=11)

def test_mood_log_create():
    mood_log_create = MoodLogCreate(
        mood_score=7,
        mood_labels=["relaxed"],
        context="Meditation session",
        factors=["meditation"]
    )
    assert mood_log_create.mood_score == 7
    assert mood_log_create.mood_labels == ["relaxed"]
    assert mood_log_create.context == "Meditation session"
    assert mood_log_create.factors == ["meditation"]

def test_mood_log_in_db():
    mood_log_in_db = MoodLogInDB(
        mood_score=8,
        mood_labels=["content"],
        user_id="user123",
        location="Home",
        sentiment_score=0.85
    )
    assert mood_log_in_db.mood_score == 8
    assert mood_log_in_db.mood_labels == ["content"]
    assert mood_log_in_db.user_id == "user123"
    assert mood_log_in_db.location == "Home"
    assert mood_log_in_db.sentiment_score == 0.85
    assert isinstance(mood_log_in_db.timestamp, datetime)

def test_mood_log():
    mood_log = MoodLog(
        mood_score=6,
        mood_labels=["neutral"],
        user_id="user456",
        location="Office",
        sentiment_score=0.5
    )
    assert mood_log.mood_score == 6
    assert mood_log.mood_labels == ["neutral"]
    assert mood_log.user_id == "user456"
    assert mood_log.location == "Office"
    assert mood_log.sentiment_score == 0.5
    assert isinstance(mood_log.timestamp, datetime)