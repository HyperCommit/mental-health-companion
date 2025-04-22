import semantic_kernel as sk
from semantic_kernel.functions.kernel_plugin import KernelPlugin
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from backend.shared.cosmos import CosmosService
from pydantic import PrivateAttr
import logging
import uuid
from tenacity import retry, stop_after_attempt, wait_exponential
from backend.shared.azure_agent_service import AzureAgentService

class MoodAnalyzerPlugin(KernelPlugin):
    """Plugin for analyzing mood from text using Azure OpenAI"""

    _cosmos_service: CosmosService = PrivateAttr()
    _kernel: sk.Kernel = PrivateAttr()
    _agent_service: AzureAgentService = PrivateAttr(default=None)
    _classification_agent = PrivateAttr(default=None)
    _correlation_prefix: str = PrivateAttr(default="mood")

    def __init__(self, cosmos_service: CosmosService, kernel: sk.Kernel, name: str = "MoodAnalyzerPlugin"):
        super().__init__(name=name)
        self._cosmos_service = cosmos_service
        self._kernel = kernel
        self._agent_service = AzureAgentService(kernel)
        self._correlation_prefix = f"mood-{uuid.uuid4().hex[:6]}"

    def _get_classification_agent(self):
        """Get or create the classification agent for mood analysis"""
        if not self._classification_agent:
            self._classification_agent = self._agent_service.create_classification_agent(
                instructions="""You are a mood and emotion analyzer.
                Analyze text to identify emotional states and patterns.
                Return specific emotion labels (like anxious, joyful, frustrated)
                rather than general categories. Include intensity when relevant.
                Always consider context and nuance in emotional expression."""
            )
        return self._classification_agent

    @kernel_function(description="Analyzes text to determine user's emotional state")
    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=5))
    async def analyze_mood(self, input_text: str) -> str:
        """Analyze text content to determine mood state using Azure OpenAI."""
        correlation_id = f"{self._correlation_prefix}-analyze-{uuid.uuid4().hex[:8]}"
        
        if not input_text:
            logging.warning("Empty text for mood analysis", extra={"custom_dimensions": {
                "correlation_id": correlation_id
            }})
            return "Unable to analyze mood from empty text."
        
        try:
            # Use Azure OpenAI for mood analysis
            agent = self._get_classification_agent()
            analysis_result = await self._agent_service.get_agent_response(
                agent=agent,
                message=f"""Analyze the following text and identify the emotional state of the writer.
                Return the primary emotions detected (e.g., "anxious", "content", "sad", "hopeful").
                
                Text: {input_text}
                
                Primary emotions:"""
            )
            
            result = analysis_result.get("response", "").strip()
            
            # Log successful analysis with Azure telemetry
            logging.info("Mood analysis completed", extra={
                "custom_dimensions": {
                    "correlation_id": correlation_id,
                    "input_length": len(input_text),
                    "result_length": len(result)
                }
            })
            
            return result
            
        except Exception as e:
            # Log error with Azure telemetry
            logging.error(f"Error analyzing mood: {str(e)}", extra={
                "custom_dimensions": {
                    "correlation_id": correlation_id,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            })
            return "Unable to analyze mood. Please try again later."

    async def analyze_and_save_mood(self, user_id: str, mood: str, context: str):
        """Save mood analysis to Azure Cosmos DB"""
        correlation_id = f"{self._correlation_prefix}-save-{uuid.uuid4().hex[:8]}"
        
        try:
            # Save to Azure Cosmos DB
            await self._cosmos_service.save_mood_analysis(user_id, mood, context)
            
            # Log successful save with Azure telemetry
            logging.info("Mood analysis saved", extra={
                "custom_dimensions": {
                    "correlation_id": correlation_id,
                    "user_id": user_id,
                    "mood": mood
                }
            })
            
        except Exception as e:
            # Log error with Azure telemetry
            logging.error(f"Error saving mood analysis: {str(e)}", extra={
                "custom_dimensions": {
                    "correlation_id": correlation_id,
                    "error": str(e),
                    "user_id": user_id
                }
            })

    @kernel_function(description="Identifies emotional patterns over time")
    async def detect_patterns(self, journal_entries: list) -> str:
        """Analyze multiple entries to find emotional patterns using Azure OpenAI."""
        correlation_id = f"{self._correlation_prefix}-patterns-{uuid.uuid4().hex[:8]}"
        
        if not journal_entries or len(journal_entries) == 0:
            return "No entries provided for pattern detection."
        
        try:
            # Format entries for analysis
            entries_text = "\n\n".join([f"Entry {i+1}: {entry}" for i, entry in enumerate(journal_entries)])
            
            # Use Azure OpenAI for pattern analysis
            agent = self._get_classification_agent()
            pattern_result = await self._agent_service.get_agent_response(
                agent=agent,
                message=f"""Review these journal entries chronologically and identify emotional patterns or trends.
                Focus on recurring themes, triggers, and changes in emotional state.
                
                Entries:
                {entries_text}
                
                Provide:
                1. Primary emotional patterns
                2. Potential triggers or causes
                3. Changes over time
                """
            )
            
            result = pattern_result.get("response", "").strip()
            
            # Log successful pattern detection with Azure telemetry
            logging.info("Pattern detection completed", extra={
                "custom_dimensions": {
                    "correlation_id": correlation_id,
                    "entry_count": len(journal_entries),
                    "result_length": len(result)
                }
            })
            
            return result
            
        except Exception as e:
            # Log error with Azure telemetry
            logging.error(f"Error detecting patterns: {str(e)}", extra={
                "custom_dimensions": {
                    "correlation_id": correlation_id,
                    "error": str(e),
                    "entry_count": len(journal_entries)
                }
            })
            return "Unable to detect patterns. Please try again later."