from semantic_kernel.functions.kernel_plugin import KernelPlugin
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from backend.shared.cosmos import CosmosService
from typing import Dict, Optional
from pydantic import PrivateAttr
import logging
import uuid
import time
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from backend.shared.azure_agent_service import AzureAgentService
import json

class SafetyPlugin(KernelPlugin):
    """Plugin for identifying potential crisis situations using Azure OpenAI"""
    
    _cosmos_service: CosmosService = PrivateAttr()
    _kernel = PrivateAttr()
    _agent_service: AzureAgentService = PrivateAttr(default=None)
    _classification_agent = PrivateAttr(default=None)
    _conversation_agent = PrivateAttr(default=None)
    _correlation_prefix: str = PrivateAttr(default="safety")

    def __init__(self, cosmos_service: CosmosService, name: str = "SafetyPlugin"):
        super().__init__(name=name)
        self._cosmos_service = cosmos_service
        self._kernel = None
        self._correlation_prefix = f"safety-{uuid.uuid4().hex[:6]}"

    def set_kernel(self, kernel):
        """Set the kernel and initialize agent service"""
        self._kernel = kernel
        self._agent_service = AzureAgentService(kernel)

    def _get_classification_agent(self):
        """Get or create the classification agent for risk assessment"""
        if not self._classification_agent and self._agent_service:
            self._classification_agent = self._agent_service.create_classification_agent(
                instructions="""You are a mental health risk assessor.
                Analyze text for signs of crisis, self-harm, or suicidal ideation.
                Always return a JSON object with:
                - risk_level: (none, low, moderate, high)
                - reasoning: explanation for your assessment
                Be careful not to minimize real concerns or overreact to mild statements.
                This is critical for user safety."""
            )
        return self._classification_agent

    def _get_conversation_agent(self):
        """Get or create the conversation agent for providing resources"""
        if not self._conversation_agent and self._agent_service:
            self._conversation_agent = self._agent_service.create_conversation_agent(
                instructions="""You are a supportive mental health companion.
                Provide empathetic and helpful responses to users in crisis.
                Always prioritize user safety. For high-risk situations, 
                include crisis resources like suicide hotlines (988) and crisis text line (741741).
                Be warm, supportive, and non-judgmental."""
            )
        return self._conversation_agent

    @kernel_function(description="Assesses risk level in user text")
    @retry(
        wait_exponential(multiplier=1, min=1, max=10),  # positional arguments first
        stop=stop_after_attempt(3),  # then keyword arguments
        retry=retry_if_exception_type((ConnectionError, TimeoutError))
    )
    async def assess_risk(self, input_text: str) -> Dict:
        """
        Analyze text to detect potential crisis indicators using Azure OpenAI.
        Returns risk assessment information with Azure monitoring.
        """
        correlation_id = f"{self._correlation_prefix}-assess-{uuid.uuid4().hex[:8]}"
        start_time = time.time()
        
        if not self._kernel:
            raise ValueError("Kernel not set")
            
        if not input_text or not isinstance(input_text, str):
            logging.warning("Invalid input for risk assessment", extra={"custom_dimensions": {
                "correlation_id": correlation_id
            }})
            return {"risk_level": "none", "reasoning": "No valid input provided", "requires_immediate_action": False}

        try:
            # Use Azure OpenAI for risk assessment
            agent = self._get_classification_agent()
            assessment_result = await self._agent_service.get_agent_response(
                agent=agent,
                message=f"""Analyze the following text for signs of crisis, self-harm, or suicidal ideation.
                
                Text: {input_text}
                
                Return a JSON response with risk_level (none, low, moderate, high) and reasoning.
                Example: {{"risk_level": "low", "reasoning": "User mentions feeling down but no indications of self-harm"}}
                """
            )
            
            response = assessment_result.get("response", "{}")
            
            # Parse the response - handle potential JSON parsing issues
            try:
                # Try to parse as JSON
                result = json.loads(response)
                risk_level = result.get("risk_level", "none").lower()
                reasoning = result.get("reasoning", "No reasoning provided")
            except json.JSONDecodeError:
                # Fallback parsing if not valid JSON
                if ":" in response:
                    risk_level, reasoning = response.split(":", 1)
                    risk_level = risk_level.strip().lower()
                else:
                    risk_level = "none"
                    reasoning = response
            
            # Validate risk level
            if risk_level not in ["none", "low", "moderate", "high"]:
                risk_level = "none"
            
            # Create the result
            result = {
                "risk_level": risk_level,
                "reasoning": reasoning.strip(),
                "requires_immediate_action": risk_level in ["moderate", "high"]
            }
            
            # Log with Azure Application Insights compatible format
            elapsed_ms = (time.time() - start_time) * 1000
            logging.info("Risk assessment completed", extra={
                "custom_dimensions": {
                    "correlation_id": correlation_id,
                    "elapsed_ms": elapsed_ms,
                    "risk_level": risk_level,
                    "requires_action": result["requires_immediate_action"],
                    "input_length": len(input_text)
                }
            })
            
            # Save risk assessment to Azure Cosmos DB
            await self._cosmos_service.log_safety_assessment(
                user_id="current-user",  # Replace with actual user ID in production
                risk_level=risk_level,
                reasoning=reasoning
            )
            
            return result
            
        except Exception as e:
            # Log error with Azure Application Insights compatible format
            elapsed_ms = (time.time() - start_time) * 1000
            logging.error(f"Risk assessment failed: {str(e)}", extra={
                "custom_dimensions": {
                    "correlation_id": correlation_id,
                    "elapsed_ms": elapsed_ms,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            })
            
            # Return a safe default
            return {
                "risk_level": "none",
                "reasoning": "Assessment failed. Please try again.",
                "requires_immediate_action": False
            }

    @kernel_function(description="Provides grounding prompts for users in crisis")
    async def provide_grounding_prompts(self, risk_level: str) -> str:
        """Provide grounding prompts based on the risk level using Azure OpenAI."""
        correlation_id = f"{self._correlation_prefix}-grounding-{uuid.uuid4().hex[:8]}"
        
        try:
            if risk_level not in ["none", "low", "moderate", "high"]:
                risk_level = "none"
                
            # Use Azure OpenAI for personalized grounding prompts
            agent = self._get_conversation_agent()
            prompt_result = await self._agent_service.get_agent_response(
                agent=agent,
                message=f"""Create a grounding exercise for someone with {risk_level} risk level of crisis.
                Make it appropriate for their level of distress. For high risk, focus on immediate
                sensory experiences (5-4-3-2-1 technique). For moderate risk, focus on breathing and 
                present moment awareness. For low risk, focus on gentle reflection."""
            )
            
            response = prompt_result.get("response", "")
            
            if response:
                # Log successful generation with Azure telemetry
                logging.info("Generated grounding prompt", extra={
                    "custom_dimensions": {
                        "correlation_id": correlation_id,
                        "risk_level": risk_level,
                        "response_length": len(response)
                    }
                })
                return response
                
            # Fallback to hardcoded responses if generation failed
            if risk_level == "high":
                return "Let's try a grounding exercise together. Name five things you can see, four things you can touch, three things you can hear, two things you can smell, and one thing you can taste."
            elif risk_level == "moderate":
                return "Take a deep breath with me. Look around your surroundings. What is one thing you can do right now to feel safer?"
            elif risk_level == "low":
                return "What is one small step you can take right now to improve your mood?"
            else:
                return "Focus on your breathing and describe how you feel in this moment."
                
        except Exception as e:
            # Log error with Azure telemetry
            logging.error(f"Error providing grounding prompts: {str(e)}", extra={
                "custom_dimensions": {
                    "correlation_id": correlation_id,
                    "risk_level": risk_level,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            })
            
            # Fallback to basic grounding prompt
            return "Take a moment to breathe deeply. Focus on your breath going in and out."