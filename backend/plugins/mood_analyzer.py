import semantic_kernel as sk
from semantic_kernel.functions.kernel_plugin import KernelPlugin
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from backend.shared.cosmos import CosmosService
from pydantic import Field, PrivateAttr

class MoodAnalyzerPlugin(KernelPlugin):
    """Plugin for analyzing mood from text and detecting patterns"""

    _cosmos_service: CosmosService = PrivateAttr()
    _kernel: sk.Kernel = PrivateAttr()

    def __init__(self, cosmos_service: CosmosService, kernel: sk.Kernel, name: str = "MoodAnalyzerPlugin"):
        super().__init__(name=name)
        self._cosmos_service = cosmos_service
        self._kernel = kernel

    @kernel_function(description="Analyzes text to determine user's emotional state")
    async def analyze_mood(self, input_text: str) -> str:
        """Analyze text content to determine mood state and return key emotions detected."""
        prompt = f"""
        Analyze the following text and identify the emotional state of the writer.
        Return the primary emotions detected (e.g., "anxious", "content", "sad", "hopeful").
        
        Text: {input_text}
        
        Primary emotions:
        """
        
        result = await self._kernel.invoke_semantic_function(
            prompt=prompt,
            service_id="sentiment"
        )
        
        return str(result).strip()

    async def analyze_and_save_mood(self, user_id: str, mood: str, context: str):
        await self._cosmos_service.save_mood_analysis(user_id, mood, context)

    @kernel_function(description="Identifies emotional patterns over time")
    async def detect_patterns(self, journal_entries: list) -> str:
        """Analyze multiple entries to find emotional patterns over time."""
        entries_text = "\n\n".join([f"Entry {i+1}: {entry}" for i, entry in enumerate(journal_entries)])
        
        prompt = f"""
        Review these journal entries chronologically and identify any emotional patterns or trends.
        Focus on recurring themes, triggers, and changes in emotional state.
        
        Entries:
        {entries_text}
        
        Emotional patterns detected:
        """
        
        result = await self._kernel.invoke_semantic_function(
            prompt=prompt,
            service_id="conversation"
        )
        
        return str(result).strip()