from semantic_kernel.functions.kernel_plugin import KernelPlugin
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from datetime import datetime
from typing import List, Dict
from shared.cosmos import CosmosService

class JournalingPlugin(KernelPlugin):
    """Plugin for managing and analyzing journaling entries"""

    def __init__(self, kernel, cosmos_service: CosmosService):
        super().__init__()
        self._kernel = kernel
        self._text_plugin = kernel.plugins.get_plugin("text")
        self._memory = kernel.memory
        self.cosmos_service = cosmos_service

    @kernel_function(description="Adds a new journal entry")
    async def add_entry(self, entry_text: str) -> str:
        """Add a new journal entry and return confirmation."""
        timestamp = datetime.now().isoformat()
        
        # Store the entry in semantic memory with metadata
        await self._memory.save_information(
            collection="journal_entries",
            text=entry_text,
            id=timestamp,
            metadata={"timestamp": timestamp}
        )
        
        # Use text plugin to get entry summary
        summary = await self._text_plugin.summarize(entry_text)
        return f"Journal entry added at {timestamp}. Summary: {summary}"

    @kernel_function(description="Analyzes journal entries for emotional trends")
    async def analyze_entries(self, time_period: str = "last_week") -> str:
        """Analyze journal entries to detect emotional trends."""
        # Retrieve entries from memory
        entries = await self._memory.search("journal_entries", f"timestamp > {time_period}")
        
        if not entries:
            return "No journal entries found for the specified time period."

        # Combine all entries for analysis
        combined_text = "\n".join([entry.text for entry in entries])
        
        # Use text plugin for sentiment analysis
        sentiment = await self._text_plugin.analyze_sentiment(combined_text)
        
        # Extract key themes
        themes = await self._text_plugin.extract_key_phrases(combined_text)
        
        # Save insights to CosmosService
        insights = f"Overall sentiment: {sentiment}. Key themes: {themes}"
        await self.cosmos_service.save_journal_insights(time_period, insights)
        
        return f"Analysis complete. {insights}"

    @kernel_function(description="Retrieves past journal entries")
    async def get_entries(self, query: str = "") -> List[Dict]:
        """Retrieve journal entries matching the query."""
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