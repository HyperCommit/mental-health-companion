import pytest
from pydantic import ValidationError
from shared.models.user import User, UserCreate, UserUpdate
from datetime import datetime

def test_user_model_creation():
    user = User(
        id="123",
        email="test@example.com",
        created_at=datetime.utcnow(),
        subscription_tier="free",
        preferences={"theme": "dark"},
        profile={"name": "Test User"}
    )
    assert user.id == "123"
    assert user.email == "test@example.com"
    assert user.subscription_tier == "free"
    assert user.preferences["theme"] == "dark"
    assert user.profile["name"] == "Test User"

def test_user_create_model():
    user_create = UserCreate(email="test@example.com")
    assert user_create.email == "test@example.com"

def test_user_update_model():
    user_update = UserUpdate(
        email="updated@example.com",
        preferences={"notifications": "enabled"},
        profile={"age": 30},
        subscription_tier="gold"
    )
    assert user_update.email == "updated@example.com"
    assert user_update.preferences["notifications"] == "enabled"
    assert user_update.profile["age"] == 30
    assert user_update.subscription_tier == "gold"

def test_user_model_invalid_email():
    with pytest.raises(ValidationError):
        User(
            id="123",
            email="invalid-email",
            created_at=datetime.utcnow()
        )