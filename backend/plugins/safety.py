from semantic_kernel.functions.kernel_plugin import KernelPlugin
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from backend.shared.cosmos import CosmosService
from typing import Dict
from pydantic import PrivateAttr

class SafetyPlugin(KernelPlugin):
    """Plugin for identifying potential crisis situations and providing appropriate responses"""
    
    _cosmos_service: CosmosService = PrivateAttr()
    _kernel = PrivateAttr()

    def __init__(self, cosmos_service: CosmosService, name: str = "SafetyPlugin"):
        super().__init__(name=name)
        self._cosmos_service = cosmos_service
        self._kernel = None

    def set_kernel(self, kernel):
        self._kernel = kernel

    @kernel_function(description="Assesses risk level in user text")
    async def assess_risk(self, input_text: str) -> Dict:
        """
        Analyze text to detect potential indicators of crisis or self-harm.
        Returns risk assessment information.
        """
        if not self._kernel:
            raise ValueError("Kernel not set")

        prompt = f"""
        Analyze the following text for signs of crisis, self-harm, or suicidal ideation.
        Provide a risk assessment (none, low, moderate, high) and explain your reasoning.

        Text: {input_text}

        Format your response as: [RISK_LEVEL]: [REASONING]
        """

        result = await self._kernel.invoke_semantic_function(
            prompt=prompt,
            service_id="sentiment"
        )
        
        # Parse the result
        response = str(result).strip()
        if ":" in response:
            risk_level, reasoning = response.split(":", 1)
            risk_level = risk_level.strip().lower()
        else:
            risk_level = "none"
            reasoning = response
            
        return {
            "risk_level": risk_level,
            "reasoning": reasoning.strip(),
            "requires_immediate_action": risk_level in ["moderate", "high"]
        }

    async def log_safety_assessment(self, user_id: str, risk_level: str, reasoning: str):
        """Log a safety assessment to the database."""
        await self._cosmos_service.log_safety_assessment(user_id, risk_level, reasoning)

    @kernel_function(description="Provides crisis support resources")
    async def provide_resources(self, risk_assessment: Dict) -> str:
        """
        Provide appropriate resources based on the risk assessment.
        Higher risk levels receive more urgent and specific resources.
        """
        risk_level = risk_assessment.get("risk_level", "none")
        
        if risk_level == "high":
            return """
            I'm concerned about what you've shared. Please consider:
            
            1. Call or text 988 (US Suicide & Crisis Lifeline) - available 24/7
            2. Text HOME to 741741 (Crisis Text Line) - available 24/7
            3. Call emergency services (911 in US) if you're in immediate danger
            
            Would you like me to provide more specific resources?
            """
        elif risk_level == "moderate":
            return """
            Thank you for sharing. It sounds like you're going through a difficult time. 
            Here are some resources that might help:
            
            1. Text HOME to 741741 (Crisis Text Line) - available 24/7
            2. Call 988 (US Suicide & Crisis Lifeline) - available 24/7
            3. Consider speaking with a mental health professional
            
            Would it help to talk more about what you're experiencing?
            """
        elif risk_level == "low":
            return """
            I appreciate you sharing how you're feeling. While this sounds challenging, 
            here are some supportive resources:
            
            1. National Alliance on Mental Illness (NAMI): 1-800-950-NAMI
            2. Consider scheduling time with a counselor or therapist
            3. The 988 Lifeline is always available if things get more difficult
            
            Would you like to explore some coping strategies together?
            """
        else:
            return ""  # No resources needed for no risk

    @kernel_function(description="Provides grounding prompts for users in crisis")
    async def provide_grounding_prompts(self, risk_level: str) -> str:
        """Provide grounding prompts based on the risk level."""
        if risk_level == "high":
            return "Let's try a grounding exercise together. Name five things you can see, four things you can touch, three things you can hear, two things you can smell, and one thing you can taste."
        elif risk_level == "moderate":
            return "Take a deep breath with me. Look around your surroundings. What is one thing you can do right now to feel safer?"
        elif risk_level == "low":
            return "What is one small step you can take right now to improve your mood?"
        else:
            return "Focus on your breathing and describe how you feel in this moment."