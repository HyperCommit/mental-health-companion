# filepath: backend/shared/cosmos.py
import os
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime

import azure.cosmos.cosmos_client as cosmos_client
import azure.cosmos.exceptions as exceptions
from azure.cosmos.partition_key import PartitionKey

from shared.models.user import User
from shared.models.journal import JournalEntry
from shared.models.mood import MoodLog
from infrastructure.config.settings import get_settings

settings = get_settings()

class CosmosService:
    """Service for interacting with Azure Cosmos DB"""
    
    def __init__(self):
        # Parse connection string to get endpoint and key
        conn_str = settings["cosmos_connection_string"]
        parts = dict(part.split('=', 1) for part in conn_str.split(';') if part)
        endpoint = parts.get('AccountEndpoint')
        key = parts.get('AccountKey')
        
        # Initialize the Cosmos client with separate URL and credential
        self.client = cosmos_client.CosmosClient(
            url=endpoint,
            credential=key
        )
        
        # Create database if it doesn't exist
        db_name = settings["cosmos_database_name"]
        self.database = self.client.create_database_if_not_exists(db_name)
        
        # Create containers if they don't exist
        self.users_container = self.database.create_container_if_not_exists(
            id="users",
            partition_key=PartitionKey(path="/id")
        )
        
        self.journal_container = self.database.create_container_if_not_exists(
            id="journal_entries",
            partition_key=PartitionKey(path="/user_id")
        )
        
        self.mood_container = self.database.create_container_if_not_exists(
            id="mood_logs",
            partition_key=PartitionKey(path="/user_id")
        )
    
    # User methods
    async def get_user(self, user_id: str) -> Optional[User]:
        """Get a user by ID"""
        try:
            query = f"SELECT * FROM c WHERE c.id = '{user_id}'"
            results = self.users_container.query_items(
                query=query,
                enable_cross_partition_query=True
            )
            
            items = list(results)
            if not items:
                return None
                
            return User(**items[0])
        except exceptions.CosmosResourceNotFoundError:
            return None
    
    async def create_user(self, id: str, email: str, subscription_tier: str = "free") -> User:
        """Create a new user"""
        user_data = {
            "id": id,
            "email": email,
            "created_at": datetime.utcnow().isoformat(),
            "subscription_tier": subscription_tier,
            "preferences": {},
            "profile": {},
            "type": "user"
        }
        
        created_item = self.users_container.create_item(body=user_data)
        return User(**created_item)
    
    # Journal methods
    async def get_journal_entries(self, user_id: str, skip: int = 0, limit: int = 10) -> List[JournalEntry]:
        """Get journal entries for a user"""
        query = f"""
        SELECT * FROM c 
        WHERE c.user_id = '{user_id}' AND c.type = 'journal_entry'
        ORDER BY c.created_at DESC
        OFFSET {skip} LIMIT {limit}
        """
        
        items = list(self.journal_container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        
        return [JournalEntry(**item) for item in items]
    
    async def get_journal_entry(self, entry_id: str) -> Optional[JournalEntry]:
        """Get a specific journal entry"""
        try:
            query = f"SELECT * FROM c WHERE c.id = '{entry_id}'"
            items = list(self.journal_container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
            if not items:
                return None
                
            return JournalEntry(**items[0])
        except exceptions.CosmosResourceNotFoundError:
            return None
    
    async def create_journal_entry(
        self, 
        user_id: str, 
        content: str, 
        mood_indicators: List[str] = None,
        mood_score: Optional[int] = None,
        ai_insights: Optional[Dict] = None
    ) -> JournalEntry:
        """Create a new journal entry"""
        if mood_indicators is None:
            mood_indicators = []
            
        entry_data = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "content": content,
            "mood_indicators": mood_indicators,
            "mood_score": mood_score,
            "created_at": datetime.utcnow().isoformat(),
            "ai_insights": ai_insights,
            "type": "journal_entry"
        }
        
        created_item = self.journal_container.create_item(body=entry_data)
        return JournalEntry(**created_item)
    
    async def update_journal_entry(
        self,
        entry_id: str,
        user_id: str,
        update_data: Dict[str, Any]
    ) -> JournalEntry:
        """Update a journal entry"""
        entry = await self.get_journal_entry(entry_id)
        if not entry or entry.user_id != user_id:
            return None
        
        # Prepare update document
        update_dict = {**entry.dict(), **update_data}
        update_dict["updated_at"] = datetime.utcnow().isoformat()
        
        # Update in database
        updated_item = self.journal_container.replace_item(
            item=entry_id,
            body=update_dict
        )
        
        return JournalEntry(**updated_item)
    
    async def delete_journal_entry(self, entry_id: str, user_id: str) -> bool:
        """Delete a journal entry"""
        entry = await self.get_journal_entry(entry_id)
        if not entry or entry.user_id != user_id:
            return False
        
        self.journal_container.delete_item(item=entry_id, partition_key=user_id)
        return True