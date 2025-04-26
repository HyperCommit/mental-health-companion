import pytest
from pydantic import ValidationError
from shared.models.user import User, UserCreate, UserUpdate
from datetime import datetime


def test_user_model_creation():
    """Test creating a User instance with all required fields including hashed password."""
    user = User(
        id="123",
        email="test@example.com",
        created_at=datetime.utcnow(),
        hashed_password="$2b$12$CwYGQQtVXSara5eb7DEjUOfdgK0gri67BSOvVvnY22YXmQw0vnHq2",  # Added hashed_password
        subscription_tier="free",
        preferences={"theme": "dark"},
        profile={"name": "Test User"}
    )
    assert user.id == "123"
    assert user.email == "test@example.com"
    assert user.subscription_tier == "free"
    assert user.preferences["theme"] == "dark"
    assert user.profile["name"] == "Test User"
    assert user.hashed_password == "$2b$12$CwYGQQtVXSara5eb7DEjUOfdgK0gri67BSOvVvnY22YXmQw0vnHq2"


def test_user_create_model():
    """Test creating a UserCreate instance with required password fields."""
    user_create = UserCreate(
        email="test@example.com",
        password="Password123",
        password_confirm="Password123"
    )
    assert user_create.email == "test@example.com"
    assert user_create.password == "Password123"
    assert user_create.password_confirm == "Password123"


def test_user_update_model():
    """Test creating a UserUpdate instance with optional fields."""
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
    """Test validation for invalid email format."""
    with pytest.raises(ValidationError):
        User(
            id="123",
            email="invalid-email",
            created_at=datetime.utcnow(),
            hashed_password="$2b$12$CwYGQQtVXSara5eb7DEjUOfdgK0gri67BSOvVvnY22YXmQw0vnHq2"
        )


def test_password_strength_validation():
    """Test password strength validation rules."""
    # Test minimum length validation
    with pytest.raises(ValidationError) as excinfo:
        UserCreate(email="test@example.com", password="Short1", password_confirm="Short1")
    assert "Password must be at least 8 characters" in str(excinfo.value)

    # Test digit requirement validation
    with pytest.raises(ValidationError) as excinfo:
        UserCreate(email="test@example.com", password="PasswordOnly", password_confirm="PasswordOnly")
    assert "Password must contain at least one digit" in str(excinfo.value)

    # Test uppercase letter requirement validation
    with pytest.raises(ValidationError) as excinfo:
        UserCreate(email="test@example.com", password="password123", password_confirm="password123")
    assert "Password must contain at least one uppercase letter" in str(excinfo.value)


def test_password_confirmation_validation():
    """Test password confirmation matching validation."""
    # Test passwords don't match
    with pytest.raises(ValidationError) as excinfo:
        UserCreate(email="test@example.com", password="Password123", password_confirm="DifferentPassword123")
    assert "Passwords do not match" in str(excinfo.value)

    # Test when password_confirm is None (should be valid as it's optional)
    user_create = UserCreate(email="test@example.com", password="Password123")
    assert user_create.email == "test@example.com"
    assert user_create.password == "Password123"
    assert user_create.password_confirm is None