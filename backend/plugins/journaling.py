from semantic_kernel.functions.kernel_plugin import KernelPlugin
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from datetime import datetime
from typing import List, Dict, Optional
from backend.shared.cosmos import CosmosService
from pydantic import PrivateAttr
import logging
import uuid
from tenacity import retry, stop_after_attempt, wait_exponential
from backend.shared.azure_agent_service import AzureAgentService

class JournalingPlugin(KernelPlugin):
    """Plugin for managing and analyzing journaling entries"""

    _cosmos_service: CosmosService = PrivateAttr()
    _agent_service: AzureAgentService = PrivateAttr()
    _conversation_agent = PrivateAttr(default=None)
    _classification_agent = PrivateAttr(default=None)
    _correlation_prefix: str = PrivateAttr(default="journal")

    def __init__(self, kernel, cosmos_service: CosmosService, name: str = "JournalingPlugin"):
        super().__init__(name=name)
        self._kernel = kernel
        self._memory = kernel.memory if hasattr(kernel, 'memory') else None
        self._cosmos_service = cosmos_service
        self._agent_service = AzureAgentService(kernel)
        self._correlation_prefix = f"journal-{uuid.uuid4().hex[:6]}"

    def _get_conversation_agent(self):
        """Get or create the conversation agent"""
        if not self._conversation_agent:
            self._conversation_agent = self._agent_service.create_conversation_agent(
                instructions="""You are a supportive journaling assistant.
                Help users reflect on their thoughts and feelings through journaling.
                Be empathetic, thoughtful, and encouraging. Never provide medical advice.
                When summarizing journal entries, focus on key emotions and themes."""
            )
        return self._conversation_agent

    def _get_classification_agent(self):
        """Get or create the classification agent"""
        if not self._classification_agent:
            self._classification_agent = self._agent_service.create_classification_agent(
                instructions="""You analyze journal entries for emotional content.
                Identify primary emotions, intensity levels, and key themes.
                Always return your analysis in JSON format with 'primary_emotion',
                'intensity' (1-10), and 'themes' fields."""
            )
        return self._classification_agent

    @kernel_function(description="Adds a new journal entry")
    async def add_entry(self, entry_text: str) -> str:
        """Add a new journal entry and return confirmation using Azure OpenAI."""
        correlation_id = f"{self._correlation_prefix}-add-{uuid.uuid4().hex[:8]}"
        
        if not entry_text:
            logging.warning("Empty journal entry", extra={"custom_dimensions": {"correlation_id": correlation_id}})
            return "Journal entry cannot be empty."
        
        timestamp = datetime.now().isoformat()
        
        try:
            # Store in memory if available
            if self._memory:
                await self._memory.save_information(
                    collection="journal_entries",
                    text=entry_text,
                    id=timestamp,
                    metadata={"timestamp": timestamp}
                )
                logging.info("Journal entry saved to memory", extra={
                    "custom_dimensions": {"correlation_id": correlation_id}
                })
            
            # Use Azure OpenAI agent for summarization
            agent = self._get_conversation_agent()
            summary_result = await self._agent_service.get_agent_response(
                agent=agent,
                message=f"Summarize this journal entry in one sentence: {entry_text[:500]}..."
            )
            
            summary = summary_result.get("response", f"{entry_text[:50]}...")
            
            # Save to Azure Cosmos DB
            await self._cosmos_service.save_journal_entry(
                user_id="current-user",  # Replace with actual user ID in production
                entry_text=entry_text,
                summary=summary,
                timestamp=timestamp
            )
            
            return f"Journal entry added at {timestamp}. Summary: {summary}"
            
        except Exception as e:
            logging.error(f"Error adding journal entry: {str(e)}", extra={
                "custom_dimensions": {
                    "correlation_id": correlation_id,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            })
            return f"An error occurred while saving your journal entry. Please try again."

    @kernel_function(description="Analyzes journal entries for emotional trends")
    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=5))
    async def analyze_entries(self, time_period: str = "last_week") -> str:
        """Analyze journal entries to detect emotional trends using Azure OpenAI."""
        correlation_id = f"{self._correlation_prefix}-analyze-{uuid.uuid4().hex[:8]}"
        
        try:
            # Retrieve entries from memory if available
            entries = []
            if self._memory:
                entries = await self._memory.search("journal_entries", f"timestamp > {time_period}")
            
            if not entries:
                return "No journal entries found for the specified time period."
    
            # Combine entries for analysis
            combined_text = "\n".join([entry.text for entry in entries])
            
            # Use Azure OpenAI for analysis
            agent = self._get_classification_agent()
            analysis_result = await self._agent_service.get_agent_response(
                agent=agent,
                message=f"""Analyze these journal entries for emotional trends:
                {combined_text[:2000]}...
                
                Return a JSON object with:
                1. overall_sentiment: (positive, negative, neutral)
                2. primary_emotions: [list of main emotions detected]
                3. key_themes: [list of recurring topics]
                4. summary: brief paragraph summarizing the findings
                """
            )
            
            insights = analysis_result.get("response", "Unable to analyze entries.")
            
            # Save insights to Azure Cosmos DB
            await self._cosmos_service.save_journal_insights(time_period, insights)
            
            # Log successful analysis with Azure-compatible format
            logging.info("Journal analysis completed", extra={
                "custom_dimensions": {
                    "correlation_id": correlation_id,
                    "time_period": time_period,
                    "entry_count": len(entries)
                }
            })
            
            return f"Analysis complete. {insights}"
            
        except Exception as e:
            logging.error(f"Error analyzing journal entries: {str(e)}", extra={
                "custom_dimensions": {
                    "correlation_id": correlation_id,
                    "error": str(e),
                    "time_period": time_period
                }
            })
            return "Unable to analyze entries. Please try again later."

    @kernel_function(description="Generates a thoughtful journal prompt based on the user's mood")
    async def generate_prompt(self, mood: str) -> str:
        """Generates a journal prompt customized for the user's current mood using Azure OpenAI"""
        correlation_id = f"{self._correlation_prefix}-prompt-{uuid.uuid4().hex[:8]}"
        
        try:
            # Use Azure OpenAI agent for prompt generation
            agent = self._get_conversation_agent()
            prompt_result = await self._agent_service.get_agent_response(
                agent=agent,
                message=f"""Create a thoughtful journal prompt for someone feeling {mood}.
                The prompt should encourage self-reflection and emotional processing.
                Keep it to a single thoughtful question or short paragraph."""
            )
            
            generated_prompt = prompt_result.get("response", "")
            
            if generated_prompt:
                # Log success with Azure telemetry
                logging.info("Generated journal prompt", extra={
                    "custom_dimensions": {
                        "correlation_id": correlation_id,
                        "mood": mood,
                        "prompt_length": len(generated_prompt)
                    }
                })
                return generated_prompt
            
            # Fallback to static prompts if generation failed
            if mood == "anxious":
                return "What is causing your anxiety today? What would help you feel calmer?"
            elif mood == "happy":
                return "What made you happy today? How can you carry this happiness forward?"
            elif mood == "stressed":
                return "What is in your control right now? What is out of your control?"
            else:
                return "Describe your current feelings and what led to them."
                
        except Exception as e:
            logging.error(f"Error generating journal prompt: {str(e)}", extra={
                "custom_dimensions": {
                    "correlation_id": correlation_id,
                    "error": str(e),
                    "mood": mood
                }
            })
            
            # Fallback to a generic prompt
            return "Describe your current feelings and what led to them."