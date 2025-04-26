# filepath: backend/shared/cosmos.py
import os
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from azure.cosmos.aio import CosmosClient
from azure.cosmos import PartitionKey, exceptions
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from opencensus.ext.azure.log_exporter import AzureLogHandler

from shared.models.user import User
from shared.models.journal import JournalEntry
from shared.models.mood import MoodLog

# Configure logging with Azure Application Insights
logger = logging.getLogger(__name__)
if os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING"):
    logger.addHandler(AzureLogHandler())

class CosmosService:
    """
    Service for Azure Cosmos DB operations including user management.
    
    This class handles database operations following Azure best practices 
    for security, resilience, and performance.
    """
    
    def __init__(self):
        """Initialize the CosmosService with proper connection handling."""
        try:
            connection_string = os.environ.get("COSMOS_CONNECTION_STRING")
            db_name = os.environ.get("COSMOS_DATABASE_NAME", "aifrontiers")
            
            if not connection_string:
                raise ValueError("COSMOS_CONNECTION_STRING environment variable not set")
                
            # Create the client with proper connection mode
            self.client = CosmosClient.from_connection_string(connection_string)
            self.database = self.client.get_database_client(db_name)
            
            # Get container clients
            self.users_container = self.database.get_container_client("users")
            self.journal_container = self.database.get_container_client("journal_entries")
            self.mood_container = self.database.get_container_client("mood_logs")
            
            logger.info("CosmosService initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize CosmosService: {str(e)}", exc_info=True)
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(exceptions.CosmosHttpResponseError)
    )
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Retrieves a user by their email address.
        
        Args:
            email: Email address of the user to retrieve
            
        Returns:
            User object if found, None otherwise
        """
        try:
            correlation_id = f"get_user_email_{uuid.uuid4().hex[:8]}"
            logger.info(f"Retrieving user by email: {email} [correlation_id: {correlation_id}]")
            
            # Modify query to sort by creation date (newest first)
            query = "SELECT * FROM c WHERE c.email = @email ORDER BY c.created_at DESC"
            parameters = [{"name": "@email", "value": email}]
            
            items = []
            
            # Execute query - remove enable_cross_partition_query parameter since it's not supported
            async for item in self.users_container.query_items(
                query=query,
                parameters=parameters
            ):
                items.append(item)
            
            if not items:
                logger.info(f"No user found with email {email} [correlation_id: {correlation_id}]")
                return None
            
            if len(items) > 1:
                logger.warning(f"Found {len(items)} users with email {email}, returning most recent [correlation_id: {correlation_id}]")
            
            return User(**items[0])
            
        except Exception as e:
            logger.error(f"Error retrieving user by email: {str(e)} [correlation_id: {correlation_id}]", exc_info=True)
            return None
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(exceptions.CosmosHttpResponseError)
    )
    async def get_user(self, user_id: str) -> Optional[User]:
        """
        Retrieves a user by their ID with retry mechanism.
        
        Args:
            user_id: ID of the user to retrieve
            
        Returns:
            User object if found, None otherwise
            
        Raises:
            Exception: If a database error occurs that can't be handled by retries
        """
        try:
            # Generate correlation ID for request tracing
            correlation_id = f"get_user_{uuid.uuid4().hex[:8]}"
            logger.info(f"Retrieving user by ID: {user_id} [correlation_id: {correlation_id}]")
            
            # Using read_item for direct ID lookup (more efficient than query)
            try:
                item = await self.users_container.read_item(
                    item=user_id, 
                    partition_key=user_id  # Assuming ID is the partition key
                )
                logger.info(f"User with ID {user_id} retrieved successfully [correlation_id: {correlation_id}]")
                return User(**item)
            except exceptions.CosmosResourceNotFoundError:
                logger.info(f"User with ID {user_id} not found [correlation_id: {correlation_id}]")
                return None
                
        except exceptions.CosmosHttpResponseError as e:
            # Log specific Cosmos DB error for better diagnostics
            logger.error(f"Cosmos DB error retrieving user by ID {user_id}: {str(e)} [correlation_id: {correlation_id}]", 
                        exc_info=True)
            raise  # Let the retry decorator handle the retry
        except Exception as e:
            # Log unexpected errors
            logger.error(f"Unexpected error retrieving user by ID {user_id}: {str(e)} [correlation_id: {correlation_id}]", 
                        exc_info=True)
            return None
    
    async def create_user(self, id: str, email: str, hashed_password: str) -> User:
        """
        Creates a new user in Cosmos DB with secure password storage.
        
        Args:
            id: Unique identifier for the user
            email: User's email address
            hashed_password: Pre-hashed password for secure storage
            
        Returns:
            Created User object
            
        Raises:
            Exception: If user creation fails
        """
        try:
            # Generate correlation ID for request tracing
            correlation_id = f"create_user_{uuid.uuid4().hex[:8]}"
            logger.info(f"Creating new user with email: {email} [correlation_id: {correlation_id}]")
            
            # Prepare user data with default values
            current_time = datetime.utcnow()
            user_data = {
                "id": id,
                "email": email,
                "hashed_password": hashed_password,
                "created_at": current_time.isoformat(),
                "subscription_tier": "free",
                "preferences": {},
                "profile": {}
            }
            
            # Create the user in Cosmos DB
            created_item = await self.users_container.create_item(body=user_data)
            logger.info(f"User with email {email} created successfully [correlation_id: {correlation_id}]")
            
            return User(**created_item)
            
        except exceptions.CosmosResourceExistsError:
            logger.error(f"User with ID {id} already exists [correlation_id: {correlation_id}]")
            raise ValueError(f"User with ID {id} already exists")
        except Exception as e:
            logger.error(f"Failed to create user: {str(e)} [correlation_id: {correlation_id}]", exc_info=True)
            raise
    
    async def get_journal_entries(self, user_id: str, skip: int = 0, limit: int = 10) -> List[JournalEntry]:
        """Get journal entries for a user"""
        query = f"""
        SELECT * FROM c 
        WHERE c.user_id = '{user_id}' AND c.type = 'journal_entry'
        ORDER BY c.created_at DESC
        OFFSET {skip} LIMIT {limit}
        """
        
        items = []
        async for item in self.journal_container.query_items(query=query):
            items.append(item)
        
        return [JournalEntry(**item) for item in items]
    
    async def get_journal_entry(self, entry_id: str, user_id: str = None) -> Optional[JournalEntry]:
        """Get a specific journal entry
        
        Args:
            entry_id: ID of the journal entry to retrieve
            user_id: Optional user ID for partition key (if container is partitioned)
            
        Returns:
            JournalEntry object if found, None otherwise
        """
        try:
            # Generate correlation ID for tracing
            correlation_id = f"get_journal_{uuid.uuid4().hex[:8]}"
            logger.info(f"Retrieving journal entry by ID: {entry_id} [correlation_id: {correlation_id}]")
            
            query = f"SELECT * FROM c WHERE c.id = '{entry_id}'"
            
            # Add user_id condition if provided
            if user_id:
                query += f" AND c.user_id = '{user_id}'"
                
            items = []
            async for item in self.journal_container.query_items(query=query):
                items.append(item)
            
            if not items:
                logger.info(f"Journal entry with ID {entry_id} not found [correlation_id: {correlation_id}]")
                return None
                
            logger.info(f"Retrieved journal entry: {entry_id} [correlation_id: {correlation_id}]")
            return JournalEntry(**items[0])
        except exceptions.CosmosResourceNotFoundError:
            logger.warning(f"Journal entry with ID {entry_id} not found [correlation_id: {correlation_id}]")
            return None
        except Exception as e:
            logger.error(f"Error retrieving journal entry: {str(e)} [correlation_id: {correlation_id}]", exc_info=True)
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
        
        created_item = await self.journal_container.create_item(body=entry_data)
        return JournalEntry(**created_item)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(exceptions.CosmosHttpResponseError)
    )
    async def update_journal_entry(
        self,
        entry_id: str,
        user_id: str,
        **update_fields
    ) -> Optional[JournalEntry]:
        """
        Update a journal entry with new values.
        
        Args:
            entry_id: ID of the journal entry to update
            user_id: ID of the user who owns the entry
            **update_fields: Keyword arguments for fields to update
            
        Returns:
            Updated JournalEntry object if successful, None otherwise
            
        Raises:
            CosmosHttpResponseError: If a database operation fails
        """
        try:
            correlation_id = f"update_journal_{uuid.uuid4().hex[:8]}"
            logger.info(f"Updating journal entry: {entry_id} [correlation_id: {correlation_id}]")
            
            # Get the existing entry
            entry = await self.get_journal_entry(entry_id)
            if not entry or entry.user_id != user_id:
                logger.warning(f"Journal entry {entry_id} not found or not owned by user {user_id} [correlation_id: {correlation_id}]")
                return None
            
            # Convert entry to dictionary with proper JSON serialization for datetime objects
            update_dict = {}
            for key, value in entry.dict().items():
                if isinstance(value, datetime):
                    update_dict[key] = value.isoformat()
                else:
                    update_dict[key] = value
            
            # Update with new fields
            update_dict.update(update_fields)
            
            # Add updated timestamp
            update_dict["updated_at"] = datetime.utcnow().isoformat()
            
            # Update in database
            updated_item = await self.journal_container.replace_item(
                item=entry_id,
                body=update_dict
            )
            
            logger.info(f"Journal entry {entry_id} updated successfully [correlation_id: {correlation_id}]")
            return JournalEntry(**updated_item)
            
        except exceptions.CosmosResourceNotFoundError:
            logger.warning(f"Journal entry {entry_id} not found during update [correlation_id: {correlation_id}]")
            return None
        except Exception as e:
            logger.error(f"Error updating journal entry: {str(e)} [correlation_id: {correlation_id}]", exc_info=True)
            raise
    
    async def delete_journal_entry(self, entry_id: str, user_id: str) -> bool:
        """Delete a journal entry"""
        entry = await self.get_journal_entry(entry_id)
        if not entry or entry.user_id != user_id:
            return False
        
        await self.journal_container.delete_item(item=entry_id, partition_key=user_id)
        return True

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(exceptions.CosmosHttpResponseError)
    )
    async def create_mood_log(
        self,
        user_id: str,
        mood_score: int,
        mood_labels: List[str],
        context: str = None,
        factors: List[str] = None,
        location: str = None
    ) -> MoodLog:
        """
        Create a new mood log entry for a user.
        
        Args:
            user_id: ID of the user this mood log belongs to
            mood_score: Numeric score representing user's mood (typically 1-10)
            mood_labels: List of descriptive mood labels
            context: Optional context when mood was logged (e.g., "morning", "after work")
            factors: Optional list of factors affecting mood
            location: Optional location where mood was recorded
            
        Returns:
            Created MoodLog object
            
        Raises:
            CosmosHttpResponseError: If a database operation fails
        """
        try:
            correlation_id = f"create_mood_{uuid.uuid4().hex[:8]}"
            logger.info(f"Creating mood log for user: {user_id} [correlation_id: {correlation_id}]")
            
            # Generate unique ID for the mood log
            mood_log_id = str(uuid.uuid4())
            current_time = datetime.utcnow()
            
            # Prepare mood log data
            mood_data = {
                "id": mood_log_id,
                "user_id": user_id,
                "mood_score": mood_score,
                "mood_labels": mood_labels,
                "timestamp": current_time.isoformat(),
                "context": context,
                "factors": factors or [],
                "location": location,
                "created_at": current_time.isoformat(),
                "updated_at": current_time.isoformat()
            }
            
            # Create item in Cosmos DB - remove the partition_key parameter since 
            # the SDK extracts it from the mood_data object
            created_item = await self.mood_container.create_item(body=mood_data)
            
            logger.info(f"Created mood log with ID: {mood_log_id} [correlation_id: {correlation_id}]")
            
            # Return as MoodLog model instance
            return MoodLog(**created_item)
            
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Cosmos DB error creating mood log: {str(e)} [correlation_id: {correlation_id}]", 
                        exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating mood log: {str(e)} [correlation_id: {correlation_id}]", 
                        exc_info=True)
            raise ValueError(f"Failed to create mood log: {str(e)}")

    async def get_mood_logs(self, user_id: str, limit: int = 10, skip: int = 0) -> List[MoodLog]:
        """
        Retrieve mood logs for a specific user.
        
        Args:
            user_id: ID of the user to fetch mood logs for
            limit: Maximum number of logs to return (default: 10)
            skip: Number of logs to skip (for pagination, default: 0)
            
        Returns:
            List of MoodLog objects for the user
        """
        try:
            # Generate correlation ID for tracing
            correlation_id = f"get_moods_{uuid.uuid4().hex[:8]}"
            logger.info(f"Retrieving mood logs for user: {user_id} [correlation_id: {correlation_id}]")
            
            # Query to fetch mood logs ordered by timestamp (newest first)
            query = f"""
            SELECT * FROM c 
            WHERE c.user_id = '{user_id}' 
            ORDER BY c.timestamp DESC 
            OFFSET {skip} LIMIT {limit}
            """
            
            items = []
            async for item in self.mood_container.query_items(query=query):
                items.append(item)
            
            logger.info(f"Retrieved {len(items)} mood logs for user {user_id} [correlation_id: {correlation_id}]")
            return [MoodLog(**item) for item in items]
            
        except Exception as e:
            logger.error(f"Error retrieving mood logs for user {user_id}: {str(e)} [correlation_id: {correlation_id}]", 
                       exc_info=True)
            return []

def check_database_connection() -> bool:
    """Check if the Cosmos DB connection is active"""
    try:
        # Attempt to read database properties to verify connection
        _ = CosmosService().database.read()
        return True
    except exceptions.CosmosHttpResponseError:
        return False