from semantic_kernel.functions.kernel_plugin import KernelPlugin
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from typing import Dict, List
import json
from datetime import datetime
from backend.shared.cosmos import CosmosService
from pydantic import PrivateAttr
import logging
import uuid
from tenacity import retry, stop_after_attempt, wait_exponential
from backend.shared.azure_agent_service import AzureAgentService

class MindfulnessPlugin(KernelPlugin):
    """Plugin for mindfulness exercises and tracking using Azure OpenAI"""

    _cosmos_service: CosmosService = PrivateAttr()
    _kernel = PrivateAttr()
    _agent_service: AzureAgentService = PrivateAttr(default=None)
    _conversation_agent = PrivateAttr(default=None)
    _classification_agent = PrivateAttr(default=None)
    _correlation_prefix: str = PrivateAttr(default="mindful")

    def __init__(self, kernel, cosmos_service: CosmosService, name: str = "MindfulnessPlugin"):
        super().__init__(name=name)
        self._kernel = kernel
        self._memory = kernel.memory if hasattr(kernel, 'memory') else None
        self._cosmos_service = cosmos_service
        self._agent_service = AzureAgentService(kernel)
        self._correlation_prefix = f"mindful-{uuid.uuid4().hex[:6]}"

        self._exercises = {
            "breathing": {
                "duration": 300,  # 5 minutes
                "steps": [
                    "Find a comfortable position",
                    "Close your eyes and take a deep breath",
                    "Breathe in for 4 counts",
                    "Hold for 4 counts",
                    "Exhale for 4 counts",
                    "Repeat the cycle"
                ]
            },
            "body_scan": {
                "duration": 600,  # 10 minutes
                "steps": [
                    "Lie down comfortably",
                    "Focus attention on your feet",
                    "Slowly move attention up through your body",
                    "Notice any sensations without judgment",
                    "Release any tension you find"
                ]
            },
            "mindful_walking": {
                "duration": 900,  # 15 minutes
                "steps": [
                    "Find a quiet space to walk",
                    "Walk at a natural pace",
                    "Notice the sensation of each step",
                    "Focus on your breathing while walking",
                    "Observe your surroundings mindfully"
                ]
            }
        }

    def _get_conversation_agent(self):
        """Get or create the conversation agent"""
        if not self._conversation_agent:
            self._conversation_agent = self._agent_service.create_conversation_agent(
                instructions="""You are a mindfulness meditation guide.
                Provide calming, supportive guidance for mindfulness practices.
                Use clear, simple language with a gentle, soothing tone.
                Focus on present moment awareness, acceptance, and compassion.
                Never provide medical advice."""
            )
        return self._conversation_agent

    def _get_classification_agent(self):
        """Get or create the classification agent"""
        if not self._classification_agent:
            self._classification_agent = self._agent_service.create_classification_agent(
                instructions="""You analyze feedback about mindfulness experiences.
                Identify sentiment (positive/negative/neutral) and key themes.
                Look for indications of effectiveness and challenges.
                Return analysis in JSON format with 'sentiment', 'effectiveness',
                and 'themes' fields."""
            )
        return self._classification_agent

    @kernel_function(description="Guides a mindfulness exercise")
    async def guide_exercise(self, exercise_type: str) -> str:
        """Provide guidance for a specific mindfulness exercise using Azure OpenAI."""
        correlation_id = f"{self._correlation_prefix}-guide-{uuid.uuid4().hex[:8]}"
        
        if exercise_type not in self._exercises:
            logging.warning(f"Invalid exercise type: {exercise_type}", extra={"custom_dimensions": {
                "correlation_id": correlation_id
            }})
            return f"Exercise type '{exercise_type}' not found. Available exercises: {', '.join(self._exercises.keys())}"

        try:
            exercise = self._exercises[exercise_type]
            current_time = datetime.now().isoformat()
            
            # Use Azure OpenAI for enhanced guidance
            agent = self._get_conversation_agent()
            exercise_result = await self._agent_service.get_agent_response(
                agent=agent,
                message=f"""Create a guided meditation script for {exercise_type} practice.
                Duration: {exercise['duration'] // 60} minutes
                
                Include these steps:
                {', '.join(exercise['steps'])}
                
                Make it calming, step-by-step, and suitable for beginners.
                Start with an introduction and end with a gentle conclusion."""
            )
            
            guidance = exercise_result.get("response", "")
            
            if not guidance:
                # Fallback to basic guidance
                response = [
                    f"Starting {exercise_type} exercise at {current_time}",
                    f"Duration: {exercise['duration'] // 60} minutes\n",
                    "Follow these steps:"
                ]
                
                for i, step in enumerate(exercise['steps'], 1):
                    response.append(f"{i}. {step}")
                    
                guidance = "\n".join(response)
            
            # Log successful guidance with Azure telemetry
            logging.info("Generated mindfulness guidance", extra={
                "custom_dimensions": {
                    "correlation_id": correlation_id,
                    "exercise_type": exercise_type,
                    "guidance_length": len(guidance)
                }
            })
                
            return guidance
            
        except Exception as e:
            # Log error with Azure telemetry
            logging.error(f"Error generating exercise guidance: {str(e)}", extra={
                "custom_dimensions": {
                    "correlation_id": correlation_id,
                    "error": str(e),
                    "exercise_type": exercise_type
                }
            })
            
            # Fallback to basic guidance
            exercise = self._exercises.get(exercise_type, {"duration": 300, "steps": ["Focus on your breath"]})
            response = [
                f"Starting {exercise_type} exercise",
                f"Duration: {exercise['duration'] // 60} minutes\n",
                "Follow these steps:"
            ]
            
            for i, step in enumerate(exercise['steps'], 1):
                response.append(f"{i}. {step}")
                
            return "\n".join(response)

    @kernel_function(description="Analyzes user feedback about mindfulness sessions")
    async def analyze_feedback(self, feedback: str) -> Dict:
        """Analyze user feedback using Azure OpenAI sentiment analysis."""
        correlation_id = f"{self._correlation_prefix}-analyze-{uuid.uuid4().hex[:8]}"
        
        if not feedback or not isinstance(feedback, str):
            return {"error": "Invalid feedback text"}
        
        try:
            # Use Azure OpenAI for sentiment analysis
            agent = self._get_classification_agent()
            analysis_result = await self._agent_service.get_agent_response(
                agent=agent,
                message=f"""Analyze this feedback about a mindfulness session:
                
                "{feedback}"
                
                Return a JSON object with:
                1. sentiment: (positive, negative, or neutral)
                2. effectiveness: rating from 1-10 based on the feedback
                3. themes: list of key themes or issues mentioned
                """
            )
            
            response = analysis_result.get("response", "")
            
            # Try to parse as JSON
            try:
                result = json.loads(response)
            except json.JSONDecodeError:
                # Fallback if not valid JSON
                result = {
                    "sentiment": "neutral",
                    "effectiveness": 5,
                    "themes": ["Unable to parse detailed themes"],
                    "raw_analysis": response
                }
            
            # Save the feedback and analysis
            timestamp = datetime.now().isoformat()
            feedback_data = {
                "feedback": feedback,
                "analysis": result,
                "timestamp": timestamp
            }
            
            # Store in memory if available
            if self._memory:
                await self._memory.save_information(
                    collection="mindfulness_feedback",
                    text=json.dumps(feedback_data),
                    id=timestamp
                )
            
            # Log successful analysis with Azure telemetry
            logging.info("Analyzed mindfulness feedback", extra={
                "custom_dimensions": {
                    "correlation_id": correlation_id,
                    "sentiment": result.get("sentiment", "unknown"),
                    "effectiveness": result.get("effectiveness", 0)
                }
            })
            
            return result
            
        except Exception as e:
            # Log error with Azure telemetry
            logging.error(f"Error analyzing feedback: {str(e)}", extra={
                "custom_dimensions": {
                    "correlation_id": correlation_id,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            })
            return {"error": f"Error analyzing feedback: {str(e)}"}