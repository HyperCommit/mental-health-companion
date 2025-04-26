# filepath: tests/integration/api/test_cosmos_db.py
import sys
import os
import logging
import asyncio
import uuid
from datetime import datetime
from typing import Optional, Tuple, Dict, List
import pytest
from opencensus.ext.azure.log_exporter import AzureLogHandler

# Add the project root directory to the Python module search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.shared.cosmos import CosmosService
from backend.shared.auth import get_password_hash
from shared.models.user import User
from shared.models.journal import JournalEntry
from shared.models.mood import MoodLog
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from azure.cosmos.exceptions import CosmosHttpResponseError

# Configure logging with Azure Application Insights integration
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Console handler for local debugging
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(console_handler)

# Add Azure Application Insights handler if connection string is available
if os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING"):
    logger.addHandler(AzureLogHandler())

# Initialize CosmosService as a singleton
cosmos_service = CosmosService()

class TestDataFactory:
    """Factory class to create test data objects for integration tests."""
    
    @staticmethod
    async def cleanup_test_data(email: str = "mockuser@example.com") -> None:
        """
        Remove any existing test data to avoid conflicts.
        
        Args:
            email: Email address of test user to remove
        """
        correlation_id = f"cleanup_{uuid.uuid4().hex[:8]}"
        logger.info(f"Starting test data cleanup [correlation_id: {correlation_id}]")
        
        try:
            # Find and delete test user
            query = "SELECT * FROM c WHERE c.email = @email"
            parameters = [{"name": "@email", "value": email}]
            
            user_ids = []
            async for item in cosmos_service.users_container.query_items(
                query=query,
                parameters=parameters,
                partition_key=None
            ):
                user_ids.append(item['id'])
                await cosmos_service.users_container.delete_item(
                    item=item['id'],
                    partition_key=item['id']
                )
                logger.info(f"Deleted test user with ID: {item['id']} [correlation_id: {correlation_id}]")
            
            # Delete associated journal entries and mood logs if user was found
            for user_id in user_ids:
                await TestDataFactory._cleanup_user_data(user_id, correlation_id)
                
        except Exception as e:
            logger.warning(f"Error during test cleanup: {str(e)} [correlation_id: {correlation_id}]", 
                          exc_info=True)
    
    @staticmethod
    async def _cleanup_user_data(user_id: str, correlation_id: str) -> None:
        """
        Clean up data associated with a specific user.
        
        Args:
            user_id: User ID to clean up data for
            correlation_id: Correlation ID for tracing
        """
        try:
            # Clean up journal entries
            query = "SELECT * FROM c WHERE c.user_id = @user_id"
            parameters = [{"name": "@user_id", "value": user_id}]
            
            async for item in cosmos_service.journals_container.query_items(
                query=query,
                parameters=parameters,
                partition_key=user_id
            ):
                await cosmos_service.journals_container.delete_item(
                    item=item['id'],
                    partition_key=user_id
                )
                logger.info(f"Deleted journal entry ID: {item['id']} [correlation_id: {correlation_id}]")
            
            # Clean up mood logs
            async for item in cosmos_service.moods_container.query_items(
                query=query,
                parameters=parameters,
                partition_key=user_id
            ):
                await cosmos_service.moods_container.delete_item(
                    item=item['id'],
                    partition_key=user_id
                )
                logger.info(f"Deleted mood log ID: {item['id']} [correlation_id: {correlation_id}]")
                
        except Exception as e:
            logger.warning(f"Error cleaning up user data: {str(e)} [correlation_id: {correlation_id}]")
    
    @staticmethod
    async def create_mock_data() -> Tuple[User, List[JournalEntry], List[MoodLog]]:
        """
        Create mock data in Cosmos DB for testing all models.
        
        Returns:
            Tuple containing the created user, journal entries, and mood logs
        """
        correlation_id = f"create_mock_{uuid.uuid4().hex[:8]}"
        logger.info(f"Creating mock test data [correlation_id: {correlation_id}]")
        
        # Clean up any existing test data
        await TestDataFactory.cleanup_test_data()
        
        # Create mock user
        user_id = str(uuid.uuid4())
        hashed_password = get_password_hash("MockPassword123")
        user = await cosmos_service.create_user(
            id=user_id,
            email="mockuser@example.com",
            hashed_password=hashed_password
        )
        logger.info(f"Created User: {user} [correlation_id: {correlation_id}]")
        
        # Create mock journal entries
        journal_entries = []
        for i in range(3):
            entry = await cosmos_service.create_journal_entry(
                user_id=user_id,
                content=f"Test journal entry {i+1} - This is a mock entry for testing.",
                mood_indicators=["calm", "productive"] if i % 2 == 0 else ["anxious", "tired"],
                mood_score=7 if i % 2 == 0 else 4
            )
            journal_entries.append(entry)
            logger.info(f"Created Journal Entry {i+1}: {entry.id} [correlation_id: {correlation_id}]")
        
        # Create mock mood logs
        mood_logs = []
        mood_contexts = ["morning", "afternoon", "evening"]
        mood_factors = [["sleep", "exercise"], ["work", "social"], ["nutrition", "leisure"]]
        
        for i in range(3):
            mood_log = await cosmos_service.create_mood_log(
                user_id=user_id,
                mood_score=8 if i % 2 == 0 else 5,
                mood_labels=["happy", "energetic"] if i % 2 == 0 else ["neutral", "relaxed"],
                context=mood_contexts[i],
                factors=mood_factors[i],
                location="home" if i % 2 == 0 else "work"
            )
            mood_logs.append(mood_log)
            logger.info(f"Created Mood Log {i+1}: {mood_log.id} [correlation_id: {correlation_id}]")
        
        return user, journal_entries, mood_logs


@pytest.mark.asyncio
@retry(
    stop=stop_after_attempt(3), 
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(CosmosHttpResponseError)
)
async def test_cosmos_service() -> None:
    """
    Test CosmosService methods for all models with retry logic.
    
    This comprehensive test validates the creation and retrieval of
    users, journal entries, and mood logs in the Azure Cosmos DB.
    """
    correlation_id = f"test_{uuid.uuid4().hex[:8]}"
    logger.info(f"Starting Cosmos DB integration test [correlation_id: {correlation_id}]")
    
    # Create all test data
    user, journal_entries, mood_logs = await TestDataFactory.create_mock_data()
    user_id = user.id
    
    # Test 1: User retrieval by email
    user_by_email = await cosmos_service.get_user_by_email("mockuser@example.com")
    assert user_by_email is not None, "Failed to retrieve user by email"
    assert user_by_email.id == user_id, f"User ID mismatch: got {user_by_email.id}, expected {user_id}"
    logger.info(f"Test 1 passed: Retrieved user by email [correlation_id: {correlation_id}]")
    
    # Test 2: Journal entry retrieval
    retrieved_entries = await cosmos_service.get_journal_entries(user_id)
    assert len(retrieved_entries) == 3, f"Expected 3 journal entries, got {len(retrieved_entries)}"
    
    # Verify specific entry
    first_entry_id = journal_entries[0].id
    retrieved_entry = await cosmos_service.get_journal_entry(first_entry_id, user_id)
    assert retrieved_entry is not None, f"Failed to retrieve journal entry {first_entry_id}"
    assert retrieved_entry.content == journal_entries[0].content, "Journal entry content mismatch"
    logger.info(f"Test 2 passed: Retrieved journal entries [correlation_id: {correlation_id}]")
    
    # Test 3: Mood log retrieval
    retrieved_moods = await cosmos_service.get_mood_logs(user_id)
    assert len(retrieved_moods) == 3, f"Expected 3 mood logs, got {len(retrieved_moods)}"
    
    # Verify mood log properties
    assert any(mood.mood_score == 8 for mood in retrieved_moods), "Missing expected mood score"
    assert any("happy" in mood.mood_labels for mood in retrieved_moods), "Missing expected mood label"
    logger.info(f"Test 3 passed: Retrieved mood logs [correlation_id: {correlation_id}]")
    
    # Test 4: Update operations
    # Update journal entry
    update_result = await cosmos_service.update_journal_entry(
        entry_id=first_entry_id,
        user_id=user_id,
        content="Updated journal content for testing",
        sentiment_score=0.75
    )
    assert update_result.content == "Updated journal content for testing", "Journal update failed"
    assert update_result.sentiment_score == 0.75, "Journal sentiment update failed"
    logger.info(f"Test 4 passed: Updated journal entry [correlation_id: {correlation_id}]")
    
    logger.info(f"All Cosmos DB integration tests passed successfully [correlation_id: {correlation_id}]")


# Run the test logic when executed directly
if __name__ == "__main__":
    asyncio.run(test_cosmos_service())