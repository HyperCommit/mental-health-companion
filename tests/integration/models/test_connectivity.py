import asyncio
import os
from dotenv import load_dotenv
from backend.shared.kernel import KernelService

async def test_remote_models():
    """Test remote model functionality"""
    load_dotenv()
    service = KernelService()
    
    # Test conversation model (gpt2)
    prompt_result = await service.generate_journal_prompt(mood="anxious")
    print(f"Journal Prompt: {prompt_result}")
    
    # Test sentiment model
    mood_result = await service.analyze_mood("I'm feeling quite happy today")
    print(f"Mood Analysis: {mood_result}")

if __name__ == "__main__":
    asyncio.run(test_remote_models())