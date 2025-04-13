import os
import sys

# Add the root directory of the project to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

import pytest
from unittest.mock import AsyncMock
from backend.plugins.journaling import JournalingPlugin
from backend.shared.cosmos import CosmosService

class MockKernel:
    """Mock class for the Kernel object."""
    def __init__(self):
        self.plugins = {"text": AsyncMock()}
        self.plugins["text"].summarize = AsyncMock(return_value="This is a summary.")
        self.plugins["text"].analyze_sentiment = AsyncMock(return_value="Positive")
        self.plugins["text"].extract_key_phrases = AsyncMock(return_value="happiness, work stress")
        self.memory = AsyncMock()

    def get_plugin(self, plugin_name):
        """Mock method to retrieve a plugin by name."""
        return self.plugins.get(plugin_name)

@pytest.fixture
def kernel():
    """Create a mock kernel instance."""
    return MockKernel()

@pytest.fixture
def cosmos_service():
    """Create a mock CosmosService instance."""
    service = AsyncMock(spec=CosmosService)
    service.save_journal_insights = AsyncMock()
    return service

@pytest.fixture
def journaling_plugin(kernel, cosmos_service):
    """Create a journaling plugin instance."""
    return JournalingPlugin(kernel=kernel, cosmos_service=cosmos_service)

@pytest.mark.asyncio
async def test_add_entry(journaling_plugin, kernel):
    """Test adding a journal entry."""
    kernel.memory.save_information = AsyncMock()
    kernel.plugins["text"].summarize = AsyncMock(return_value="This is a summary.")

    result = await journaling_plugin.add_entry("Today was a productive day.")

    kernel.memory.save_information.assert_called_once()
    kernel.plugins["text"].summarize.assert_called_once_with("Today was a productive day.")
    assert "Journal entry added" in result

@pytest.mark.asyncio
async def test_analyze_entries(journaling_plugin, kernel, cosmos_service):
    """Test analyzing journal entries."""
    kernel.memory.search = AsyncMock(return_value=[
        AsyncMock(text="I felt happy today."),
        AsyncMock(text="I was stressed about work.")
    ])
    kernel.plugins["text"].analyze_sentiment = AsyncMock(return_value="Positive")
    kernel.plugins["text"].extract_key_phrases = AsyncMock(return_value="happiness, work stress")

    result = await journaling_plugin.analyze_entries(time_period="last_week")

    kernel.memory.search.assert_called_once_with("journal_entries", "timestamp > last_week")
    kernel.plugins["text"].analyze_sentiment.assert_called_once()
    kernel.plugins["text"].extract_key_phrases.assert_called_once()
    cosmos_service.save_journal_insights.assert_called_once()
    assert "Analysis complete" in result

@pytest.mark.asyncio
async def test_get_entries(journaling_plugin, kernel):
    """Test retrieving journal entries."""
    kernel.memory.search = AsyncMock(return_value=[
        AsyncMock(text="Entry 1", metadata={"timestamp": "2025-04-12T10:00:00"}),
        AsyncMock(text="Entry 2", metadata={"timestamp": "2025-04-13T12:00:00"})
    ])

    result = await journaling_plugin.get_entries(query="")

    kernel.memory.search.assert_called_once_with("journal_entries", "")
    assert len(result) == 2
    assert result[0]["text"] == "Entry 1"
    assert result[1]["timestamp"] == "2025-04-13T12:00:00"

@pytest.mark.asyncio
async def test_generate_prompt(journaling_plugin):
    """Test generating a journal prompt based on mood."""
    result = await journaling_plugin.generate_prompt("happy")
    assert result == "What made you happy today? How can you carry this happiness forward?"

    result = await journaling_plugin.generate_prompt("anxious")
    assert result == "What is causing your anxiety today? What would help you feel calmer?"

    result = await journaling_plugin.generate_prompt("unknown")
    assert result == "Describe your current feelings and what led to them."