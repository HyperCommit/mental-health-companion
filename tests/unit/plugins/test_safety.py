import os
import sys

# Add the root directory of the project to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

import pytest
from unittest.mock import AsyncMock, MagicMock
from backend.plugins.safety import SafetyPlugin
from backend.shared.cosmos import CosmosService

class MockKernel:
    """Mock class for the Kernel object."""
    def __init__(self):
        self.invoke_semantic_function = self.mock_invoke_semantic_function
        
    async def mock_invoke_semantic_function(self, prompt: str, service_id: str):
        # Mock different responses based on the input
        if "suicidal thoughts" in prompt.lower():
            return "HIGH: Contains explicit mentions of suicidal ideation"
        elif "feeling sad" in prompt.lower():
            return "LOW: Shows signs of sadness but no immediate risk"
        elif "very anxious" in prompt.lower():
            return "MODERATE: Shows significant anxiety and distress"
        return "NONE: No concerning content detected"

@pytest.fixture
def kernel():
    """Create a mock kernel instance."""
    return MockKernel()

@pytest.fixture
def cosmos_service():
    """Create a mock CosmosService instance."""
    service = AsyncMock(spec=CosmosService)
    service.log_safety_assessment = AsyncMock()
    return service

@pytest.fixture
def safety_plugin(kernel, cosmos_service):
    """Create a safety plugin instance."""
    plugin = SafetyPlugin(cosmos_service=cosmos_service)
    plugin.set_kernel(kernel)
    return plugin

@pytest.mark.asyncio
async def test_assess_risk_high(safety_plugin):
    """Test risk assessment with high-risk content."""
    result = await safety_plugin.assess_risk("I'm having suicidal thoughts")
    
    assert result["risk_level"] == "high"
    assert "suicidal ideation" in result["reasoning"].lower()
    assert result["requires_immediate_action"] is True

@pytest.mark.asyncio
async def test_assess_risk_low(safety_plugin):
    """Test risk assessment with low-risk content."""
    result = await safety_plugin.assess_risk("I'm feeling sad today")
    
    assert result["risk_level"] == "low"
    assert "sadness" in result["reasoning"].lower()
    assert result["requires_immediate_action"] is False

@pytest.mark.asyncio
async def test_assess_risk_moderate(safety_plugin):
    """Test risk assessment with moderate-risk content."""
    result = await safety_plugin.assess_risk("I'm feeling very anxious and can't handle it")
    
    assert result["risk_level"] == "moderate"
    assert "anxiety" in result["reasoning"].lower()
    assert result["requires_immediate_action"] is True

@pytest.mark.asyncio
async def test_assess_risk_none(safety_plugin):
    """Test risk assessment with no risk content."""
    result = await safety_plugin.assess_risk("I had a good day today")
    
    assert result["risk_level"] == "none"
    assert result["requires_immediate_action"] is False

@pytest.mark.asyncio
async def test_log_safety_assessment(safety_plugin, cosmos_service):
    """Test logging safety assessment."""
    user_id = "test_user"
    risk_level = "moderate"
    reasoning = "Shows signs of distress"
    
    await safety_plugin.log_safety_assessment(user_id, risk_level, reasoning)
    
    cosmos_service.log_safety_assessment.assert_called_once_with(user_id, risk_level, reasoning)

@pytest.mark.asyncio
async def test_provide_resources_high_risk(safety_plugin):
    """Test resource provision for high-risk assessment."""
    risk_assessment = {"risk_level": "high", "reasoning": "Suicidal ideation"}
    resources = await safety_plugin.provide_resources(risk_assessment)
    
    assert "988" in resources
    assert "911" in resources
    assert "Crisis Text Line" in resources

@pytest.mark.asyncio
async def test_provide_resources_moderate_risk(safety_plugin):
    """Test resource provision for moderate-risk assessment."""
    risk_assessment = {"risk_level": "moderate", "reasoning": "Shows anxiety"}
    resources = await safety_plugin.provide_resources(risk_assessment)
    
    assert "Crisis Text Line" in resources
    assert "988" in resources
    assert "mental health professional" in resources

@pytest.mark.asyncio
async def test_provide_resources_low_risk(safety_plugin):
    """Test resource provision for low-risk assessment."""
    risk_assessment = {"risk_level": "low", "reasoning": "Mild sadness"}
    resources = await safety_plugin.provide_resources(risk_assessment)
    
    assert "NAMI" in resources
    assert "counselor or therapist" in resources

@pytest.mark.asyncio
async def test_provide_resources_no_risk(safety_plugin):
    """Test resource provision for no-risk assessment."""
    risk_assessment = {"risk_level": "none", "reasoning": "No concerns"}
    resources = await safety_plugin.provide_resources(risk_assessment)
    
    assert resources == ""

@pytest.mark.asyncio
async def test_provide_grounding_prompts_high_risk(safety_plugin):
    """Test grounding prompts for high-risk situations."""
    prompt = await safety_plugin.provide_grounding_prompts("high")
    assert "five things you can see" in prompt.lower()
    assert "four things you can touch" in prompt.lower()
    assert "three things you can hear" in prompt.lower()

@pytest.mark.asyncio
async def test_provide_grounding_prompts_moderate_risk(safety_plugin):
    """Test grounding prompts for moderate-risk situations."""
    prompt = await safety_plugin.provide_grounding_prompts("moderate")
    assert "deep breath" in prompt.lower()
    assert "surroundings" in prompt.lower()

@pytest.mark.asyncio
async def test_provide_grounding_prompts_low_risk(safety_plugin):
    """Test grounding prompts for low-risk situations."""
    prompt = await safety_plugin.provide_grounding_prompts("low")
    assert "small step" in prompt.lower()
    assert "improve your mood" in prompt.lower()