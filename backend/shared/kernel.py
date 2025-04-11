import os
import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_source import HuggingFaceTextCompletion
from dotenv import load_dotenv
from infrastructure.config.settings import get_settings

settings = get_settings()

class KernelService:
    """Service for managing Semantic Kernel instances and operations"""
    
    def __init__(self):
        self.kernel = self._initialize_kernel()
    
    def _initialize_kernel(self):
        """Initialize and configure Semantic Kernel with local models"""
        load_dotenv()
        
        # Create kernel instance
        kernel = sk.Kernel()
        
        # Configure AI services
        conversation_model = settings.primary_model
        sentiment_model = settings.sentiment_model
        
        # Add text completion services
        kernel.add_text_completion_service(
            "conversation", 
            HuggingFaceTextCompletion(conversation_model)
        )
        
        kernel.add_text_completion_service(
            "sentiment",
            HuggingFaceTextCompletion(sentiment_model)
        )
        
        # Register plugins
        from backend.plugins.mood_analyzer import MoodAnalyzerPlugin
        from backend.plugins.journaling import JournalingPlugin
        from backend.plugins.mindfulness import MindfulnessPlugin
        from backend.plugins.safety import SafetyPlugin
        
        kernel.add_plugin(MoodAnalyzerPlugin(), "mood")
        kernel.add_plugin(JournalingPlugin(), "journal")
        kernel.add_plugin(MindfulnessPlugin(), "mindfulness")
        kernel.add_plugin(SafetyPlugin(), "safety")
        
        return kernel
    
    async def analyze_mood(self, text):
        """Analyze text to determine mood"""
        result = await self.kernel.invoke_plugin("mood", "analyze_mood", input=text)
        return {"mood": str(result).strip()}
    
    async def generate_journal_prompt(self, mood=None):
        """Generate a journal prompt based on mood"""
        result = await self.kernel.invoke_plugin("journal", "create_prompt", mood=mood or "")
        return str(result).strip()
    
    async def analyze_journal_entry(self, entry):
        """Analyze a journal entry for insights"""
        result = await self.kernel.invoke_plugin("journal", "analyze_entry", entry=entry)
        return {"insights": str(result).strip()}