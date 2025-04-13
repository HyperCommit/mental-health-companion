import sys
import os

# Add the project root directory to the Python module search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import asyncio
import uuid
from datetime import datetime
from backend.shared.cosmos import CosmosService
from shared.models.user import User
from shared.models.journal import JournalEntry
from shared.models.mood import MoodLog

# Initialize CosmosService
cosmos_service = CosmosService()

async def create_mock_data():
    """Create mock data in Cosmos DB for testing."""
    # Create mock user
    user_id = str(uuid.uuid4())
    user = await cosmos_service.create_user(
        id=user_id,
        email="mockuser@example.com",
        subscription_tier="free"
    )
    print(f"Created User: {user}")

    # Create mock journal entries
    for i in range(3):
        journal_entry = await cosmos_service.create_journal_entry(
            user_id=user_id,
            content=f"Mock journal entry {i+1}",
            mood_indicators=["happy", "productive"],
            mood_score=8 + i
        )
        print(f"Created Journal Entry: {journal_entry}")

    # Create mock mood logs
    for i in range(2):
        mood_log = MoodLog(
            id=str(uuid.uuid4()),
            user_id=user_id,
            mood_score=5 + i,
            mood_labels=["calm", "focused"],
            timestamp=datetime.utcnow()
        )
        # Use model_dump() with datetime serialization
        mood_data = mood_log.model_dump()
        # Convert datetime to ISO string
        mood_data['timestamp'] = mood_data['timestamp'].isoformat()
        cosmos_service.mood_container.create_item(body=mood_data)
        print(f"Created Mood Log: {mood_log}")
    
    return user

async def test_cosmos_service():
    """Test CosmosService methods."""
    # Create mock data and get the user ID
    created_user_id = None
    
    try:
        # Create mock data and capture the user ID
        created_user_id = (await create_mock_data()).id
        print(f"\nTesting with user ID: {created_user_id}")

        # Fetch user
        user = await cosmos_service.get_user(created_user_id)
        print(f"Fetched User: {user}")

        # Fetch journal entries
        journal_entries = await cosmos_service.get_journal_entries(user_id=created_user_id)
        print(f"Fetched Journal Entries: {journal_entries}")

        # Fetch specific journal entry
        if journal_entries:
            entry_id = journal_entries[0].id
            journal_entry = await cosmos_service.get_journal_entry(entry_id)
            print(f"Fetched Journal Entry: {journal_entry}")
    except Exception as e:
        print(f"Error during test: {str(e)}")
        raise

# Run the test logic
if __name__ == "__main__":
    asyncio.run(test_cosmos_service())