from semantic_kernel.functions.kernel_plugin import KernelPlugin
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from datetime import datetime
from typing import List, Dict
from backend.shared.cosmos import CosmosService
from pydantic import PrivateAttr

class JournalingPlugin(KernelPlugin):
    """Plugin for managing and analyzing journaling entries"""

    _cosmos_service: CosmosService = PrivateAttr()

    def __init__(self, kernel, cosmos_service: CosmosService, name: str = "JournalingPlugin"):
        super().__init__(name=name)
        self._kernel = kernel
        # Remove dependency on non-existent text plugin
        self._memory = kernel.memory if hasattr(kernel, 'memory') else None
        self._cosmos_service = cosmos_service

    @kernel_function(description="Adds a new journal entry")
    async def add_entry(self, entry_text: str) -> str:
        """Add a new journal entry and return confirmation."""
        timestamp = datetime.now().isoformat()
        
        # Store the entry in semantic memory with metadata if memory is available
        if self._memory:
            await self._memory.save_information(
                collection="journal_entries",
                text=entry_text,
                id=timestamp,
                metadata={"timestamp": timestamp}
            )
        
        # Generate a simple summary since text plugin isn't available
        summary = f"{entry_text[:50]}..." if len(entry_text) > 50 else entry_text
        return f"Journal entry added at {timestamp}. Summary: {summary}"

    @kernel_function(description="Analyzes journal entries for emotional trends")
    async def analyze_entries(self, time_period: str = "last_week") -> str:
        """Analyze journal entries to detect emotional trends."""
        # Retrieve entries from memory if available
        entries = []
        if self._memory:
            entries = await self._memory.search("journal_entries", f"timestamp > {time_period}")
        
        if not entries:
            return "No journal entries found for the specified time period."

        # Combine all entries for analysis
        combined_text = "\n".join([entry.text for entry in entries])
        
        # Perform analysis directly using the conversation service
        prompt = f"""
        Analyze the following journal entries for emotional trends:
        {combined_text[:1000]}...
        
        Provide: 
        1. Overall sentiment (positive, negative, or neutral)
        2. Key themes or recurring topics
        """
        
        try:
            result = await self._kernel.invoke_semantic_function(
                prompt=prompt,
                service_id="conversation"
            )
            insights = str(result).strip()
        except Exception:
            insights = "Unable to analyze entries. Please try again later."
        
        # Save insights to CosmosService
        await self._cosmos_service.save_journal_insights(time_period, insights)
        
        return f"Analysis complete. {insights}"

    @kernel_function(description="Retrieves past journal entries")
    async def get_entries(self, query: str = "") -> List[Dict]:
        """Retrieve journal entries matching the query."""
        if not self._memory:
            return []
            
        entries = await self._memory.search("journal_entries", query)
        return [{"text": e.text, "timestamp": e.metadata["timestamp"]} for e in entries]

    @kernel_function(description="Generates a thoughtful journal prompt based on the user's mood")
    async def generate_prompt(self, mood: str) -> str:
        """Generates a journal prompt customized for the user's current mood"""
        if mood == "anxious":
            return "What is causing your anxiety today? What would help you feel calmer?"
        elif mood == "happy":
            return "What made you happy today? How can you carry this happiness forward?"
        elif mood == "stressed":
            return "What is in your control right now? What is out of your control?"
        else:
            return "Describe your current feelings and what led to them."