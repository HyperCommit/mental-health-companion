from semantic_kernel.functions.kernel_plugin import KernelPlugin
from semantic_kernel.functions.kernel_function_decorator import kernel_function

class MoodAnalyzerPlugin(KernelPlugin):
    """Plugin for analyzing mood from text and detecting patterns"""
    
    @kernel_function(description="Analyzes text to determine user's emotional state")
    async def analyze_mood(self, input_text: str) -> str:
        """Analyze text content to determine mood state and return key emotions detected."""
        prompt = f"""
        Analyze the following text and identify the emotional state of the writer.
        Return the primary emotions detected (e.g., "anxious", "content", "sad", "hopeful").
        
        Text: {input_text}
        
        Primary emotions:
        """
        
        result = await self.kernel.invoke_semantic_function(
            prompt=prompt,
            service_id="sentiment"
        )
        
        return str(result).strip()
    
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
        
        result = await self.kernel.invoke_semantic_function(
            prompt=prompt,
            service_id="conversation"
        )
        
        return str(result).strip()