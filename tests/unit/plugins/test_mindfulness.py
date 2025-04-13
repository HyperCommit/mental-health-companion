import os
import sys

# Add the root directory of the project to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

import pytest
from unittest.mock import AsyncMock
from backend.plugins.mindfulness import MindfulnessPlugin
from backend.shared.cosmos import CosmosService

class MockKernel:
    """Mock class for the Kernel object."""
    def __init__(self):
        self.plugins = {"time": AsyncMock()}
        self.plugins["time"].get_current_time = AsyncMock(return_value="2025-04-13T10:00:00")
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
    service.save_mindfulness_session = AsyncMock()
    return service

@pytest.fixture
def mindfulness_plugin(kernel, cosmos_service):
    """Create a mindfulness plugin instance."""
    return MindfulnessPlugin(kernel=kernel, cosmos_service=cosmos_service)

@pytest.mark.asyncio
async def test_guide_exercise(mindfulness_plugin, kernel):
    """Test guiding a mindfulness exercise."""
    result = await mindfulness_plugin.guide_exercise("breathing")

    assert "Starting breathing exercise at 2025-04-13T10:00:00" in result
    assert "Duration: 5 minutes" in result
    assert "1. Find a comfortable position" in result

@pytest.mark.asyncio
async def test_guide_exercise_invalid_type(mindfulness_plugin):
    """Test guiding an invalid mindfulness exercise."""
    result = await mindfulness_plugin.guide_exercise("invalid_type")

    assert "Exercise type 'invalid_type' not found" in result

@pytest.mark.asyncio
async def test_track_progress(mindfulness_plugin, kernel, cosmos_service):
    """Test tracking mindfulness progress."""
    session_data = {
        "user_id": "user123",
        "exercise_type": "breathing",
        "duration": 300
    }

    kernel.memory.search = AsyncMock(return_value=[
        AsyncMock(text='{"duration": 300}'),
        AsyncMock(text='{"duration": 600}')
    ])

    result = await mindfulness_plugin.track_progress(session_data)

    kernel.memory.save_information.assert_called_once()
    cosmos_service.save_mindfulness_session.assert_called_once_with("user123", "breathing", 300)
    assert "Total sessions: 2" in result
    assert "Total practice time: 15 minutes" in result

@pytest.mark.asyncio
async def test_get_statistics(mindfulness_plugin, kernel):
    """Test retrieving mindfulness statistics."""
    kernel.memory.search = AsyncMock(return_value=[
        AsyncMock(text='{"exercise_type": "breathing", "duration": 300}'),
        AsyncMock(text='{"exercise_type": "body_scan", "duration": 600}'),
        AsyncMock(text='{"exercise_type": "breathing", "duration": 300}')
    ])

    result = await mindfulness_plugin.get_statistics()

    assert result["total_sessions"] == 3
    assert result["exercises"]["breathing"]["count"] == 2
    assert result["exercises"]["breathing"]["total_duration"] == 600
    assert result["exercises"]["body_scan"]["count"] == 1
    assert result["exercises"]["body_scan"]["total_duration"] == 600