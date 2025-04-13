from semantic_kernel.functions.kernel_plugin import KernelPlugin
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from typing import Dict, List
import json
from datetime import datetime
from shared.cosmos import CosmosService

class MindfulnessPlugin(KernelPlugin):
    """Plugin for mindfulness exercises and tracking"""

    def __init__(self, kernel, cosmos_service: CosmosService):
        super().__init__()
        self._kernel = kernel
        self._time_plugin = kernel.plugins.get_plugin("time")
        self._memory = kernel.memory
        self.cosmos_service = cosmos_service

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
        current_time = await self._time_plugin.get_current_time()
        
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
        
        # Add timestamp and store in memory
        session_data["timestamp"] = timestamp
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
        await self.cosmos_service.save_mindfulness_session(user_id, exercise_type, duration)
        
        # Calculate statistics
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