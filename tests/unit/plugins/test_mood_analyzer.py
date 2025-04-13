# filepath: tests/unit/plugins/test_mood_analyzer.py
import os
import sys

# Add the root directory of the project to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

import pytest
from unittest.mock import AsyncMock
from backend.plugins.mood_analyzer import MoodAnalyzerPlugin
from backend.shared.cosmos import CosmosService
import semantic_kernel as sk

class MockKernel:
    """Mock class for the Kernel object."""
    async def invoke_semantic_function(self, prompt: str, service_id: str) -> str:
        return "happy, relaxed"

@pytest.fixture
def kernel():
    """Create a mock kernel instance."""
    return MockKernel()

@pytest.fixture
def cosmos_service():
    """Create a mock CosmosService instance"""
    service = AsyncMock(spec=CosmosService)
    service.save_mood_analysis = AsyncMock()
    return service

@pytest.fixture
def mood_analyzer(kernel, cosmos_service):
    """Create a mood analyzer plugin instance"""
    plugin = MoodAnalyzerPlugin(cosmos_service=cosmos_service, kernel=kernel)
    return plugin

@pytest.mark.asyncio
async def test_analyze_mood(mood_analyzer):
    """Test the mood analysis function"""
    result = await mood_analyzer.analyze_mood("I had a wonderful day today!")
    assert result == "happy, relaxed"

@pytest.mark.asyncio
async def test_detect_patterns(mood_analyzer):
    """Test the pattern detection function"""
    entries = [
        "I felt anxious about my presentation today.",
        "The presentation went well, I'm relieved.",
        "I'm feeling more confident about public speaking."
    ]
    
    result = await mood_analyzer.detect_patterns(entries)
    assert result == "happy, relaxed"  # Using our mock response

@pytest.mark.asyncio
async def test_analyze_mood_empty_input(mood_analyzer):
    """Test analyze_mood with empty input"""
    result = await mood_analyzer.analyze_mood("")
    assert result == "happy, relaxed"  # Using our mock response

@pytest.mark.asyncio
async def test_analyze_mood_invalid_input(mood_analyzer):
    """Test analyze_mood with invalid input"""
    result = await mood_analyzer.analyze_mood("12345!@#$%")
    assert result == "happy, relaxed"  # Using our mock response

@pytest.mark.asyncio
async def test_detect_patterns_empty_entries(mood_analyzer):
    """Test detect_patterns with empty journal entries"""
    result = await mood_analyzer.detect_patterns([])
    assert result == "happy, relaxed"  # Using our mock response

@pytest.mark.asyncio
async def test_detect_patterns_single_entry(mood_analyzer):
    """Test detect_patterns with a single journal entry"""
    result = await mood_analyzer.detect_patterns(["I am feeling great today!"])
    assert result == "happy, relaxed"  # Using our mock response

@pytest.mark.asyncio
async def test_analyze_and_save_mood(mood_analyzer, cosmos_service):
    """Test analyze_and_save_mood to ensure it calls save_mood_analysis"""
    user_id = "user123"
    mood = "happy"
    context = "Had a great day!"

    await mood_analyzer.analyze_and_save_mood(user_id, mood, context)

    cosmos_service.save_mood_analysis.assert_called_once_with(user_id, mood, context)