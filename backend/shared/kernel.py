import os
from pathlib import Path
import semantic_kernel as sk
from semantic_kernel.connectors.ai.hugging_face import HuggingFaceTextCompletion
from huggingface_hub import snapshot_download
from dotenv import load_dotenv
from infrastructure.config.settings import get_settings
from backend.shared.cosmos import CosmosService

settings = get_settings()

class KernelService:
    """Service for managing Semantic Kernel instances and operations"""
    
    def __init__(self):
        self.kernel = self._initialize_kernel()
    
    def _download_model(self, model_name: str) -> str:
        """Download model from HuggingFace Hub if not present locally"""
        cache_dir = Path.home() / ".cache" / "huggingface" / "hub"
        model_path = cache_dir / model_name
        
        if not model_path.exists():
            model_path = snapshot_download(
                repo_id=model_name,
                cache_dir=str(cache_dir)
            )
            
        return str(model_path)
    
    def _initialize_kernel(self):
        """Initialize and configure Semantic Kernel with local models"""
        load_dotenv()
        
        # Create kernel instance
        kernel = sk.Kernel()
        
        # Get model names from settings
        conversation_model = settings["primary_model"]
        
        # Download model if not present locally
        conversation_path = self._download_model(conversation_model)
        
        # Create text completion service with a proper text-to-text model
        conversation_service = HuggingFaceTextCompletion(
            service_id="conversation",
            ai_model_id=conversation_path,
            device=-1  # Use -1 for CPU, or 0+ for specific GPU devices
        )
        
        # Add services to the kernel using dictionary assignment
        # Since kernel.services is a dictionary in version 1.28.0
        kernel.services["conversation"] = conversation_service
        
        # Create an instance of CosmosService to pass to plugins
        cosmos_service = CosmosService()
        
        # Register plugins
        from backend.plugins.mood_analyzer import MoodAnalyzerPlugin
        from backend.plugins.journaling import JournalingPlugin
        from backend.plugins.mindfulness import MindfulnessPlugin
        from backend.plugins.safety import SafetyPlugin
        
        # Initialize plugins with the required parameters
        mood_plugin = MoodAnalyzerPlugin(cosmos_service=cosmos_service, kernel=kernel)
        journal_plugin = JournalingPlugin(kernel=kernel, cosmos_service=cosmos_service)
        mindfulness_plugin = MindfulnessPlugin(kernel=kernel, cosmos_service=cosmos_service)
        
        # SafetyPlugin has a different initialization pattern
        safety_plugin = SafetyPlugin(cosmos_service=cosmos_service)
        safety_plugin.set_kernel(kernel)  # Set kernel using the separate method
        
        # Add initialized plugins to the kernel
        kernel.add_plugin(mood_plugin, "mood")
        kernel.add_plugin(journal_plugin, "journal")
        kernel.add_plugin(mindfulness_plugin, "mindfulness")
        kernel.add_plugin(safety_plugin, "safety")
        
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