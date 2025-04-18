from semantic_kernel.functions.kernel_plugin import KernelPlugin
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from typing import Dict, List
import json
from datetime import datetime
from backend.shared.cosmos import CosmosService
from pydantic import PrivateAttr

class MindfulnessPlugin(KernelPlugin):
    """Plugin for mindfulness exercises and tracking"""

    _cosmos_service: CosmosService = PrivateAttr()
    _sentiment_analyzer = None  # Lazy-loaded

    def __init__(self, kernel, cosmos_service: CosmosService, name: str = "MindfulnessPlugin"):
        super().__init__(name=name)
        self._kernel = kernel
        self._memory = kernel.memory if hasattr(kernel, 'memory') else None
        self._cosmos_service = cosmos_service

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

    @kernel_function(description="Guides a mindfulness exercise")
    async def guide_exercise(self, exercise_type: str) -> str:
        """Provide guidance for a specific mindfulness exercise."""
        if exercise_type not in self._exercises:
            return f"Exercise type '{exercise_type}' not found. Available exercises: {', '.join(self._exercises.keys())}"

        exercise = self._exercises[exercise_type]
        
        # Get current time from kernel's time plugin if available, otherwise use local time
        try:
            if hasattr(self._kernel, 'get_plugin') and self._kernel.get_plugin('time'):
                time_plugin = self._kernel.get_plugin('time')
                current_time = await time_plugin.get_current_time()
            else:
                current_time = datetime.now().isoformat()
        except Exception:
            # Fallback to local time with ISO format if time plugin fails
            current_time = datetime.now().isoformat()
        
        response = [
            f"Starting {exercise_type} exercise at {current_time}",
            f"Duration: {exercise['duration'] // 60} minutes\n",
            "Follow these steps:"
        ]
        
        for i, step in enumerate(exercise['steps'], 1):
            response.append(f"{i}. {step}")
            
        return "\n".join(response)

    @kernel_function(description="Tracks mindfulness progress")
    async def track_progress(self, session_data: Dict) -> str:
        """Track progress based on mindfulness session data."""
        timestamp = datetime.now().isoformat()
        
        # Add timestamp and store in memory if available
        session_data["timestamp"] = timestamp
        if self._memory:
            await self._memory.save_information(
                collection="mindfulness_sessions",
                text=json.dumps(session_data),
                id=timestamp,
                metadata={"exercise_type": session_data.get("exercise_type", "unknown")}
            )
        
        # Save session data to CosmosService
        user_id = session_data.get("user_id", "unknown")
        exercise_type = session_data.get("exercise_type", "unknown")
        duration = session_data.get("duration", 0)
        await self._cosmos_service.save_mindfulness_session(user_id, exercise_type, duration)
        
        # Calculate statistics - if memory is available
        sessions = []
        if self._memory:
            sessions = await self._memory.search(
                "mindfulness_sessions", 
                f"exercise_type:{session_data['exercise_type']}"
            )
        
        total_duration = sum(
            json.loads(s.text).get("duration", 0) 
            for s in sessions
        )
        
        return (f"Session tracked successfully.\n"
                f"Total sessions: {len(sessions)}\n"
                f"Total practice time: {total_duration // 60} minutes")

    @kernel_function(description="Gets mindfulness statistics")
    async def get_statistics(self) -> Dict:
        """Retrieve mindfulness practice statistics."""
        sessions = []
        if self._memory:
            sessions = await self._memory.search("mindfulness_sessions", "")
        
        stats = {
            "total_sessions": len(sessions),
            "exercises": {}
        }
        
        for session in sessions:
            data = json.loads(session.text)
            exercise_type = data.get("exercise_type")
            if exercise_type:
                if exercise_type not in stats["exercises"]:
                    stats["exercises"][exercise_type] = {"count": 0, "total_duration": 0}
                stats["exercises"][exercise_type]["count"] += 1
                stats["exercises"][exercise_type]["total_duration"] += data.get("duration", 0)
        
        return stats

    @kernel_function(description="Analyzes user feedback about mindfulness sessions")
    async def analyze_feedback(self, feedback: str) -> Dict:
        """Analyze user feedback using sentiment analysis."""
        # Lazy-load the sentiment analyzer only when needed
        if self._sentiment_analyzer is None:
            try:
                from transformers import pipeline
                self._sentiment_analyzer = pipeline("sentiment-analysis", 
                                                 model="distilbert-base-uncased-finetuned-sst-2-english")
            except ImportError:
                return {"error": "Transformers library not installed. Install with: pip install transformers torch"}
            except Exception as e:
                return {"error": f"Failed to load sentiment analysis model: {str(e)}"}
        
        try:
            result = self._sentiment_analyzer(feedback)
            
            # Save the feedback and analysis result
            timestamp = datetime.now().isoformat()
            feedback_data = {
                "feedback": feedback,
                "sentiment": result[0],
                "timestamp": timestamp
            }
            
            # Store in memory if available
            if self._memory:
                await self._memory.save_information(
                    collection="mindfulness_feedback",
                    text=json.dumps(feedback_data),
                    id=timestamp
                )
            
            return result[0]  # Return just the sentiment analysis result
        except Exception as e:
            return {"error": f"Error analyzing feedback: {str(e)}"}