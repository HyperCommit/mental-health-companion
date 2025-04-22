import pytest
import asyncio
import logging
from dotenv import load_dotenv
from backend.shared.kernel import KernelService
from backend.plugins.journaling import JournalingPlugin
from backend.plugins.safety import SafetyPlugin
from backend.plugins.mood_analyzer import MoodAnalyzerPlugin
from backend.shared.cosmos import CosmosService

# Configure logging
logging.basicConfig(level=logging.INFO)

@pytest.mark.asyncio
async def test_azure_openai_integration():
    """Test all plugins with Azure OpenAI integration"""
    load_dotenv()
    
    # Initialize services
    kernel_service = KernelService()
    cosmos_service = CosmosService()
    
    # Initialize plugins
    journaling_plugin = JournalingPlugin(kernel_service.kernel, cosmos_service)
    
    safety_plugin = SafetyPlugin(cosmos_service)
    safety_plugin.set_kernel(kernel_service.kernel)
    
    mood_analyzer = MoodAnalyzerPlugin(cosmos_service, kernel_service.kernel)
    
    # Test journaling plugin
    journal_prompt = await journaling_plugin.generate_prompt("anxious")
    print(f"Journal Prompt: {journal_prompt}")
    
    # Test safety plugin
    risk_assessment = await safety_plugin.assess_risk(
        "I'm feeling a bit down today but I'm managing okay."
    )
    print(f"Risk Assessment: {risk_assessment}")
    
    # Test mood analyzer
    mood = await mood_analyzer.analyze_mood(
        "I feel overwhelmed with all the work I have to do, but I'm trying to stay positive."
    )
    print(f"Mood Analysis: {mood}")

if __name__ == "__main__":
    asyncio.run(test_azure_openai_integration())