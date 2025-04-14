# Mental Health Companion: DRAFT Technical Design Document
AI-powered mental health companion app using Semantic Kernel, FastAPI, and Chainlit.

## Table of Contents
- [1. Overview](#1-overview)
- [2. User Flows](#2-user-flows)
- [3. System Architecture](#3-system-architecture)
- [4. Monorepo Structure](#4-monorepo-structure)
- [5. Component Specifications](#5-component-specifications)
- [6. Data Models](#6-data-models)
- [7. API Endpoints](#7-api-endpoints)
- [8. Plugin Implementations](#8-plugin-implementations)
- [9. Chainlit Implementation](#9-chainlit-implementation)
- [10. Authentication and Security](#10-authentication-and-security)
- [11. Database Integration](#11-database-integration)
- [12. Deployment Strategy](#12-deployment-strategy)
- [13. Tiered Features](#13-tiered-features)
- [14. Implementation Timeline](#14-implementation-timeline)
- [15. Testing Strategy](#15-testing-strategy)
- [16. Build and Deployment](#16-build-and-deployment)

## 1. Overview

The Mental Health Companion is an AI-powered application that provides personalized mental wellness support through mood tracking, guided journaling, mindfulness exercises, and AI-driven insights. The system initially deploys as a Chainlit-based conversational web interface with plans for mobile expansion via React Native in future phases.

### Key Features
- Mood tracking and visualization
- AI-guided journaling
- Personalized insights from journal entries
- Mindfulness exercise recommendations
- Crisis detection and support
- Weekly mental wellness reports

### Technology Stack
- **Web Interface**: Chainlit (Free Tier)
- **Backend Framework**: FastAPI (Free Tier)
- **AI Framework**: Semantic Kernel (Free Tier)
- **Database**: Azure Cosmos DB (Paid Tier)
- **Authentication**: Firebase Auth (Free Tier)
- **AI Models**: HuggingFace (Free Tier for self-hosted)

## 2. User Flows

### 2.1 Onboarding Flow
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Landing Page│────▶│  Sign Up    │────▶│ Initial Mood│────▶│  Dashboard  │
│             │     │(Firebase Auth)    │ Assessment  │     │             │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

### 2.2 Daily Check-in Flow
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Dashboard  │────▶│ Mood Logger │────▶│ Journaling  │
│             │     │             │     │ Prompt      │
└─────────────┘     └─────────────┘     └─────┬───────┘
                                              │
                                        ┌─────▼───────┐
                                        │ Mindfulness │
                                        │ Suggestion  │
                                        └─────────────┘
```

### 2.3 Crisis Support Flow
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  User Input │────▶│Risk Detection────▶│ Resources & │
│             │     │              │    │ Support     │
└─────────────┘     └──────┬──────┘    └─────────────┘
                           │No Risk
                           ▼
                    ┌─────────────┐
                    │ Continue    │
                    │ Normal Flow │
                    └─────────────┘
```

### 2.4 Insights Flow
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Weekly     │────▶│ Mood & Entry│────▶│ Personalized│
│  Trigger    │     │ Analysis    │     │ Insights    │
└─────────────┘     └─────────────┘     └─────────────┘
```

## 3. System Architecture

```
┌─────────────────────┐     ┌─────────────────────────┐     ┌─────────────────┐
│  Chainlit Web UI    │────▶│  Backend Services       │────▶│  AI Services    │
│  (Python)           │     │  (FastAPI)              │     │ (Semantic Kernel)│
└─────────────────────┘     └─────────────────────────┘     └─────────────────┘
          │                             │                             │
          ▼                             ▼                             ▼
┌─────────────────────┐     ┌─────────────────────────┐     ┌─────────────────┐
│  Authentication     │────▶│  Azure Cosmos DB        │◀────│  Remote Models   │
│  (Firebase Auth)    │     │  (Document & Vector DB) │     │  (HuggingFace)  │
└─────────────────────┘     └─────────────────────────┘     └─────────────────┘
```

**Service Tier Labels:**
- Chainlit Web UI: **Free Tier**
- FastAPI Backend: **Free Tier**
- Firebase Authentication: **Free Tier** (up to 50,000 MAU)
- Semantic Kernel: **Free Tier** (open source)
- Azure Cosmos DB: **Paid Tier** (no free tier available)
- HuggingFace Models: **Free Tier** (self-hosted)

## 4. Monorepo Structure

```
mental-health-companion/
├── .github/                  # GitHub Actions workflows
│   └── workflows/            # CI/CD pipeline definitions
├── backend/                  # Backend application
│   ├── api/                  # FastAPI endpoints
│   │   ├── main.py           # Application entrypoint
│   │   ├── routers/          # API route definitions
│   │   │   ├── auth.py
│   │   │   ├── journal.py
│   │   │   ├── mood.py
│   │   │   ├── mindfulness.py
│   │   │   └── insights.py
│   │   └── dependencies.py   # FastAPI dependencies
│   ├── plugins/              # Semantic Kernel plugins
│   │   ├── mood_analyzer.py
│   │   ├── journaling.py
│   │   ├── mindfulness.py
│   │   └── safety.py
│   └── shared/               # Common services
│       ├── auth.py           # Authentication service
│       ├── cosmos.py         # Cosmos DB service
│       └── kernel.py         # Semantic Kernel service
├── frontend/                 # Web application
│   ├── src/                  # Source code
│   │   ├── components/       # Reusable UI components
│   │   ├── screens/          # Page definitions
│   │   ├── services/         # API services
│   │   └── utils/            # Utility functions
│   ├── public/               # Public assets
│   └── chainlit/             # Chainlit application
│       ├── app.py            # Chainlit application
│       ├── components/       # Reusable UI components
│       └── pages/            # Page definitions
├── shared/                   # Shared libraries
│   ├── models/               # Pydantic data models
│   │   ├── user.py
│   │   ├── journal.py
│   │   ├── mood.py
│   │   └── mindfulness.py
│   └── utils/                # Shared utility functions
│       ├── validation.py
│       ├── security.py
│       └── formatting.py
├── docs/                     # Documentation
│   ├── api/                  # API documentation
│   ├── architecture/         # Architecture diagrams
│   └── user-guides/          # User guides
├── infrastructure/           # Deployment and infrastructure
│   ├── bicep/                # Bicep templates
│   ├── config/               # Configuration files
│   │   ├── settings.py       # Application settings
│   │   └── logging.py        # Logging configuration
│   └── scripts/              # Deployment scripts
│       ├── Dockerfile        # Main application Dockerfile
│       └── supervisord.conf  # Process management config
├── tests/                    # Test suite
│   ├── unit/                 # Unit tests
│   ├── integration/          # Integration tests
│   └── e2e/                  # End-to-end tests
├── .env.example              # Example environment variables
├── pyproject.toml            # Python project metadata
├── requirements.txt          # Python dependencies
└── README.md                 # Project overview
```

## 5. Component Specifications

### 5.1 FastAPI Backend (Free Tier)

```python
# filepath: backend/api/main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from backend.shared.auth import get_current_user

# Create FastAPI application
app = FastAPI(
    title="Mental Health Companion API",
    description="Backend API for the Mental Health Companion application",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers from the routers directory
from backend.api.routers import auth, journal, mood, mindfulness, insights

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(
    journal.router, 
    prefix="/api/journal", 
    tags=["Journal"], 
    dependencies=[Depends(get_current_user)]
)
app.include_router(
    mood.router, 
    prefix="/api/mood", 
    tags=["Mood"], 
    dependencies=[Depends(get_current_user)]
)
app.include_router(
    mindfulness.router, 
    prefix="/api/mindfulness", 
    tags=["Mindfulness"], 
    dependencies=[Depends(get_current_user)]
)
app.include_router(
    insights.router, 
    prefix="/api/insights", 
    tags=["Insights"], 
    dependencies=[Depends(get_current_user)]
)

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}
```

### 5.2 Semantic Kernel Setup (Free Tier)

```python
# filepath: backend/shared/kernel.py
import os
import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_source import HuggingFaceTextCompletion
from dotenv import load_dotenv
from infrastructure.config.settings import get_settings

settings = get_settings()

class KernelService:
    """Service for managing Semantic Kernel instances and operations"""
    
    def __init__(self):
        self.kernel = self._initialize_kernel()
    
    def _initialize_kernel(self):
        """Initialize and configure Semantic Kernel with local models"""
        load_dotenv()
        
        # Create kernel instance
        kernel = sk.Kernel()
        
        # Configure AI services
        conversation_model = settings.primary_model
        sentiment_model = settings.sentiment_model
        
        # Add text completion services
        kernel.add_text_completion_service(
            "conversation", 
            HuggingFaceTextCompletion(conversation_model)
        )
        
        kernel.add_text_completion_service(
            "sentiment",
            HuggingFaceTextCompletion(sentiment_model)
        )
        
        # Register plugins
        from backend.plugins.mood_analyzer import MoodAnalyzerPlugin
        from backend.plugins.journaling import JournalingPlugin
        from backend.plugins.mindfulness import MindfulnessPlugin
        from backend.plugins.safety import SafetyPlugin
        
        kernel.add_plugin(MoodAnalyzerPlugin(), "mood")
        kernel.add_plugin(JournalingPlugin(), "journal")
        kernel.add_plugin(MindfulnessPlugin(), "mindfulness")
        kernel.add_plugin(SafetyPlugin(), "safety")
        
        return kernel
    
    async def analyze_mood(self, text):
        """Analyze text to determine mood"""
        result = await self.kernel.invoke_plugin("mood", "analyze_mood", input=text)
        return {"mood": str(result).strip()}
    
    async def generate_journal_prompt(self, mood=None):
        """Generate a journal prompt based on mood"""
        result = await self.kernel.invoke_plugin("journal", "create_prompt", mood=mood or "")
        return str(result).strip()
    
    async def analyze_journal_entry(self, entry):
        """Analyze a journal entry for insights"""
        result = await self.kernel.invoke_plugin("journal", "analyze_entry", entry=entry)
        return {"insights": str(result).strip()}
```

## 6. Data Models

### 6.1 User Model

```python
# filepath: shared/models/user.py
from pydantic import BaseModel, Field, EmailStr
from typing import Dict, Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    
class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    preferences: Optional[Dict] = None
    profile: Optional[Dict] = None
    subscription_tier: Optional[str] = None

class User(UserBase):
    id: str
    created_at: datetime
    subscription_tier: str = "free"
    preferences: Dict = Field(default_factory=dict)
    profile: Dict = Field(default_factory=dict)
    
    class Config:
        orm_mode = True
```

### 6.2 Journal Model

```python
# filepath: shared/models/journal.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
import uuid

class JournalEntryBase(BaseModel):
    content: str = Field(..., min_length=1)
    mood_indicators: List[str] = Field(default_factory=list)
    mood_score: Optional[int] = Field(None, ge=1, le=10)

class JournalEntryCreate(JournalEntryBase):
    pass

class JournalEntryUpdate(JournalEntryBase):
    content: Optional[str] = None
    mood_indicators: Optional[List[str]] = None
    mood_score: Optional[int] = None

class JournalEntryInDB(JournalEntryBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    ai_insights: Optional[Dict] = None
    
    class Config:
        orm_mode = True

class JournalEntry(JournalEntryInDB):
    pass
```

### 6.3 Mood Model

```python
# filepath: shared/models/mood.py
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid

class MoodLogBase(BaseModel):
    mood_score: int = Field(..., ge=1, le=10)
    mood_labels: List[str] = Field(default_factory=list)
    context: Optional[str] = None
    factors: Optional[List[str]] = None

class MoodLogCreate(MoodLogBase):
    pass

class MoodLogInDB(MoodLogBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    location: Optional[str] = None
    
    class Config:
        orm_mode = True

class MoodLog(MoodLogInDB):
    pass
```

## 7. API Endpoints

### 7.1 Journal API

```python
# filepath: backend/api/routers/journal.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from shared.models.journal import JournalEntry, JournalEntryCreate, JournalEntryUpdate
from shared.models.user import User
from backend.shared.auth import get_current_user
from backend.shared.cosmos import CosmosService
from backend.shared.kernel import KernelService

router = APIRouter()
cosmos_service = CosmosService()
kernel_service = KernelService()

@router.get("/", response_model=List[JournalEntry])
async def get_journal_entries(
    skip: int = 0, 
    limit: int = 10,
    current_user: User = Depends(get_current_user)
):
    """Get all journal entries for the current user"""
    return await cosmos_service.get_journal_entries(current_user.id, skip, limit)

@router.post("/", response_model=JournalEntry)
async def create_journal_entry(
    entry: JournalEntryCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new journal entry"""
    # Generate AI insights on the entry
    insights = await kernel_service.analyze_journal_entry(entry.content)
    
    # Create entry in database
    return await cosmos_service.create_journal_entry(
        user_id=current_user.id,
        content=entry.content,
        mood_indicators=entry.mood_indicators,
        mood_score=entry.mood_score,
        ai_insights=insights
    )

@router.get("/{entry_id}", response_model=JournalEntry)
async def get_journal_entry(
    entry_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific journal entry"""
    entry = await cosmos_service.get_journal_entry(entry_id)
    
    if not entry or entry.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Journal entry not found")
        
    return entry

@router.put("/{entry_id}", response_model=JournalEntry)
async def update_journal_entry(
    entry_id: str,
    entry_update: JournalEntryUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update a journal entry"""
    existing_entry = await cosmos_service.get_journal_entry(entry_id)
    
    if not existing_entry or existing_entry.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    
    updated_entry = await cosmos_service.update_journal_entry(
        entry_id=entry_id,
        user_id=current_user.id,
        update_data=entry_update.dict(exclude_unset=True)
    )
    
    return updated_entry

@router.delete("/{entry_id}")
async def delete_journal_entry(
    entry_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a journal entry"""
    existing_entry = await cosmos_service.get_journal_entry(entry_id)
    
    if not existing_entry or existing_entry.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    
    await cosmos_service.delete_journal_entry(entry_id, current_user.id)
    
    return {"message": "Entry deleted successfully"}

@router.post("/prompt", response_model=dict)
async def generate_journal_prompt(
    mood: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Generate a journaling prompt based on mood"""
    prompt = await kernel_service.generate_journal_prompt(mood)
    return {"prompt": prompt}
```

## 8. Plugin Implementations

### 8.1 Mood Analyzer Plugin

```python
# filepath: backend/plugins/mood_analyzer.py
from semantic_kernel.plugin_definition import kernel_function, KernelPlugin

class MoodAnalyzerPlugin(KernelPlugin):
    """Plugin for analyzing mood from text and detecting patterns"""
    
    @kernel_function(description="Analyzes text to determine user's emotional state")
    async def analyze_mood(self, input_text: str) -> str:
        """Analyze text content to determine mood state and return key emotions detected."""
        prompt = f"""
        Analyze the following text and identify the emotional state of the writer.
        Return the primary emotions detected (e.g., "anxious", "content", "sad", "hopeful").
        
        Text: {input_text}
        
        Primary emotions:
        """
        
        result = await self.kernel.invoke_semantic_function(
            prompt=prompt,
            service_id="sentiment"
        )
        
        return str(result).strip()
    
    @kernel_function(description="Identifies emotional patterns over time")
    async def detect_patterns(self, journal_entries: list) -> str:
        """Analyze multiple entries to find emotional patterns over time."""
        entries_text = "\n\n".join([f"Entry {i+1}: {entry}" for i, entry in enumerate(journal_entries)])
        
        prompt = f"""
        Review these journal entries chronologically and identify any emotional patterns or trends.
        Focus on recurring themes, triggers, and changes in emotional state.
        
        Entries:
        {entries_text}
        
        Emotional patterns detected:
        """
        
        result = await self.kernel.invoke_semantic_function(
            prompt=prompt,
            service_id="conversation"
        )
        
        return str(result).strip()
```

### 8.2 Safety Plugin

```python
# filepath: backend/plugins/safety.py
from semantic_kernel.plugin_definition import kernel_function, KernelPlugin

class SafetyPlugin(KernelPlugin):
    """Plugin for identifying potential crisis situations and providing appropriate responses"""
    
    @kernel_function(description="Assesses risk level in user text")
    async def assess_risk(self, input_text: str) -> dict:
        """
        Analyze text to detect potential indicators of crisis or self-harm.
        Returns risk assessment information.
        """
        prompt = f"""
        Analyze the following text for signs of crisis, self-harm, or suicidal ideation.
        Provide a risk assessment (none, low, moderate, high) and explain your reasoning.

        Text: {input_text}

        Format your response as: [RISK_LEVEL]: [REASONING]
        """

        result = await self.kernel.invoke_semantic_function(
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

    @kernel_function(description="Provides crisis support resources")
    async def provide_resources(self, risk_assessment: dict) -> str:
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
```

## 9. Chainlit Implementation

### 9.1 Main Chainlit App

```python
# filepath: frontend/chainlit/app.py
import chainlit as cl
from backend.shared.kernel import KernelService
from backend.shared.auth import verify_firebase_token
from infrastructure.config.settings import get_settings

settings = get_settings()

# UI Configuration
cl.configure(
    title="Mental Health Companion",
    description="AI-powered support for your mental wellbeing",
    logo="frontend/public/images/logo.png",
    theme=cl.Theme(
        primary="#4F46E5",
        background="#F9FAFB",
        accent="#10B981"
    )
)

@cl.on_chat_start
async def setup():
    """Initialize the chat session"""
    # Initialize Kernel Service
    kernel_service = KernelService()
    
    # Store in user session
    cl.user_session.set("kernel_service", kernel_service)
    
    # Welcome message with UI elements
    elements = [
        cl.Image(name="welcome", path="frontend/public/images/welcome.png"),
        cl.Accordion(
            name="getting-started",
            content="I can help with journaling, mood tracking, and mindfulness exercises."
        )
    ]
    
    await cl.Message(
        content="Welcome to your Mental Health Companion. How are you feeling today?",
        elements=elements
    ).send()

@cl.on_message
async def on_message(message: cl.Message):
    """Handle user messages"""
    kernel_service = cl.user_session.get("kernel_service")
    
    # Check for crisis indicators first
    safety_check_step = cl.Step(name="Safety Assessment")
    safety_result = await safety_check_step.run(
        async_fn=lambda: kernel_service.kernel.invoke_plugin(
            "safety", "assess_risk", input_text=message.content
        )
    )
    
    # If high or moderate risk detected, provide resources
    if safety_result.get("requires_immediate_action"):
        resources = await kernel_service.kernel.invoke_plugin(
            "safety", "provide_resources", risk_assessment=safety_result
        )
        
        await cl.Message(
            content=str(resources),
            elements=[
                cl.Link(name="crisis-line", url="https://988lifeline.org/", title="988 Suicide & Crisis Lifeline"),
                cl.Link(name="crisis-text", url="https://www.crisistextline.org/", title="Crisis Text Line")
            ]
        ).send()
        return
    
    # Regular conversation flow
    
    # Create mood analysis step
    mood_step = cl.Step(name="Understanding your mood")
    mood_result = await mood_step.run(
        async_fn=lambda: kernel_service.kernel.invoke_plugin(
            "mood", "analyze_mood", input=message.content
        )
    )
    
    # Store mood for later use
    detected_mood = str(mood_result).strip()
    cl.user_session.set("last_mood", detected_mood)
    
    # Generate response based on mood
    response_step = cl.Step(name="Creating helpful response")
    journal_prompt = await response_step.run(
        async_fn=lambda: kernel_service.kernel.invoke_plugin(
            "journal", "create_prompt", mood=detected_mood
        )
    )
    
    # Send response with action buttons
    await cl.Message(
        content=f"I sense you're feeling {detected_mood}. {journal_prompt}",
        elements=[
            cl.Button(name="log-mood", value="log_mood", label="Log This Mood"),
            cl.Button(name="mindfulness", value="suggest_mindfulness", label="Try Mindfulness")
        ]
    ).send()

@cl.on_action
async def on_action(action):
    """Handle button actions"""
    kernel_service = cl.user_session.get("kernel_service")
    last_mood = cl.user_session.get("last_mood", "neutral")
    
    if action.name == "log-mood":
        # Create a form for mood logging
        await cl.Message(content="Let's log your current mood. Please provide details:").send()
        
        mood_form = cl.Form(
            header="Mood Logger",
            submit_button_text="Save Mood",
            fields=[
                cl.FormField(
                    name="mood_score",
                    field_type=cl.FormFieldType.SLIDER,
                    label="How would you rate your mood?",
                    initial=5,
                    min=1,
                    max=10
                ),
                cl.FormField(
                    name="mood_context",
                    field_type=cl.FormFieldType.TEXT,
                    label="What's the context of your mood?"
                )
            ]
        )
        
        await mood_form.send()
    
    elif action.name == "mindfulness":
        # Recommend mindfulness exercise
        exercise = await kernel_service.kernel.invoke_plugin(
            "mindfulness", 
            "recommend_exercise", 
            mood=last_mood,
            time_available=5
        )
        
        await cl.Message(
            content=f"Here's a mindfulness exercise that might help when feeling {last_mood}:",
            elements=[
                cl.Accordion(
                    name="exercise-instructions",
                    content=exercise
                )
            ]
        ).send()

@cl.on_form_submit
async def on_form_submit(form):
    """Handle form submissions"""
    from backend.shared.cosmos import CosmosService
    
    if form.fields[0].get("name") == "mood_score":
        # Extract form data
        mood_score = int(form.fields[0].get("value", 5))
        mood_context = form.fields[1].get("value", "")
        
        # If authenticated, save to database
        if hasattr(cl.user_session, "user_id"):
            cosmos_service = CosmosService()
            last_mood = cl.user_session.get("last_mood", "")
            
            await cosmos_service.create_mood_log(
                user_id=cl.user_session.user_id,
                mood_score=mood_score,
                mood_labels=[last_mood] if last_mood else [],
                context=mood_context
            )
            
            await cl.Message(
                content=f"Thanks for logging your mood ({mood_score}/10). I've saved this information."
            ).send()
        else:
            # Just acknowledge for unauthenticated users
            await cl.Message(
                content=f"Thanks for logging your mood ({mood_score}/10). Sign in to save your mood history."
            ).send()

@cl.auth_callback
async def auth_callback(auth_info):
    """Authenticate the user with Firebase"""
    # Verify Firebase token
    user_id = verify_firebase_token(auth_info.get("token"))
    if not user_id:
        return None
        
    # Store user ID in session
    cl.user_session.user_id = user_id
    
    return auth_info
```

## 10. Authentication and Security

### 10.1 Firebase Authentication (Free Tier)

```python
# filepath: backend/shared/auth.py
import os
import firebase_admin
from firebase_admin import auth, credentials
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from shared.models.user import User
from backend.shared.cosmos import CosmosService
from infrastructure.config.settings import get_settings

settings = get_settings()

# Initialize Firebase
cred_path = settings.firebase_credentials_path
cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred)

# Security scheme
security = HTTPBearer()
cosmos_service = CosmosService()

async def verify_firebase_token(token: str) -> Optional[str]:
    """Verify Firebase token and return user ID if valid"""
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token.get("uid")
    except Exception:
        return None

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get the current user from the token"""
    token = credentials.credentials
    
    try:
        # Verify the token
        decoded_token = auth.verify_id_token(token)
        user_id = decoded_token.get("uid")
        
        # Get or create user in database
        user = await cosmos_service.get_user(user_id)
        
        if not user:
            # Create new user in the database
            email = decoded_token.get("email", "")
            user = await cosmos_service.create_user(
                id=user_id,
                email=email,
                subscription_tier="free"  # Default to free tier
            )
        
        return user
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
```

## 11. Database Integration

### 11.1 Cosmos DB Service (Paid Tier)

```python
# filepath: backend/shared/cosmos.py
import os
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime

import azure.cosmos.cosmos_client as cosmos_client
import azure.cosmos.exceptions as exceptions
from azure.cosmos.partition_key import PartitionKey

from shared.models.user import User
from shared.models.journal import JournalEntry
from shared.models.mood import MoodLog
from infrastructure.config.settings import get_settings

settings = get_settings()

class CosmosService:
    """Service for interacting with Azure Cosmos DB"""
    
    def __init__(self):
        # Initialize the Cosmos client
        self.client = cosmos_client.CosmosClient(
            settings.cosmos_connection_string
        )
        
        # Get or create database
        db_name = settings.cosmos_database_name
        self.database = self.client.get_database_client(db_name)
        
        # Get or create containers
        self.users_container = self.database.get_container_client("users")
        self.journal_container = self.database.get_container_client("journal_entries")
        self.mood_container = self.database.get_container_client("mood_logs")
    
    # User methods
    async def get_user(self, user_id: str) -> Optional[User]:
        """Get a user by ID"""
        try:
            query = f"SELECT * FROM c WHERE c.id = '{user_id}'"
            results = self.users_container.query_items(
                query=query,
                enable_cross_partition_query=True
            )
            
            items = list(results)
            if not items:
                return None
                
            return User(**items[0])
        except exceptions.CosmosResourceNotFoundError:
            return None
    
    async def create_user(self, id: str, email: str, subscription_tier: str = "free") -> User:
        """Create a new user"""
        user_data = {
            "id": id,
            "email": email,
            "created_at": datetime.utcnow().isoformat(),
            "subscription_tier": subscription_tier,
            "preferences": {},
            "profile": {},
            "type": "user"
        }
        
        created_item = self.users_container.create_item(body=user_data)
        return User(**created_item)
    
    # Journal methods
    async def get_journal_entries(self, user_id: str, skip: int = 0, limit: int = 10) -> List[JournalEntry]:
        """Get journal entries for a user"""
        query = f"""
        SELECT * FROM c 
        WHERE c.user_id = '{user_id}' AND c.type = 'journal_entry'
        ORDER BY c.created_at DESC
        OFFSET {skip} LIMIT {limit}
        """
        
        items = list(self.journal_container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        
        return [JournalEntry(**item) for item in items]
    
    async def get_journal_entry(self, entry_id: str) -> Optional[JournalEntry]:
        """Get a specific journal entry"""
        try:
            query = f"SELECT * FROM c WHERE c.id = '{entry_id}'"
            items = list(self.journal_container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
            if not items:
                return None
                
            return JournalEntry(**items[0])
        except exceptions.CosmosResourceNotFoundError:
            return None
    
    async def create_journal_entry(
        self, 
        user_id: str, 
        content: str, 
        mood_indicators: List[str] = None,
        mood_score: Optional[int] = None,
        ai_insights: Optional[Dict] = None
    ) -> JournalEntry:
        """Create a new journal entry"""
        if mood_indicators is None:
            mood_indicators = []
            
        entry_data = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "content": content,
            "mood_indicators": mood_indicators,
            "mood_score": mood_score,
            "created_at": datetime.utcnow().isoformat(),
            "ai_insights": ai_insights,
            "type": "journal_entry"
        }
        
        created_item = self.journal_container.create_item(body=entry_data)
        return JournalEntry(**created_item)
    
    async def update_journal_entry(
        self,
        entry_id: str,
        user_id: str,
        update_data: Dict[str, Any]
    ) -> JournalEntry:
        """Update a journal entry"""
        entry = await self.get_journal_entry(entry_id)
        if not entry or entry.user_id != user_id:
            return None
        
        # Prepare update document
        update_dict = {**entry.dict(), **update_data}
        update_dict["updated_at"] = datetime.utcnow().isoformat()
        
        # Update in database
        updated_item = self.journal_container.replace_item(
            item=entry_id,
            body=update_dict
        )
        
        return JournalEntry(**updated_item)
    
    async def delete_journal_entry(self, entry_id: str, user_id: str) -> bool:
        """Delete a journal entry"""
        entry = await self.get_journal_entry(entry_id)
        if not entry or entry.user_id != user_id:
            return False
        
        self.journal_container.delete_item(item=entry_id, partition_key=user_id)
        return True
```

## 12. Deployment Strategy

### 12.1 Dockerfile

```dockerfile
# filepath: infrastructure/scripts/Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y supervisor && apt-get clean

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Environment variables
ENV PORT=8000
ENV CHAINLIT_PORT=8501
ENV DEBUG=false

# Expose ports
EXPOSE $PORT
EXPOSE $CHAINLIT_PORT

# Copy supervisor configuration
COPY infrastructure/scripts/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Start services using supervisor
CMD ["/usr/bin/supervisord"]
```

### 12.2 Supervisor Config

```ini
# filepath: infrastructure/scripts/supervisord.conf
[supervisord]
nodaemon=true
user=root

[program:fastapi]
command=uvicorn backend.api.main:app --host 0.0.0.0 --port %(ENV_PORT)s
directory=/app
autostart=true
autorestart=true
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0

[program:chainlit]
command=chainlit run frontend/chainlit/app.py --host 0.0.0.0 --port %(ENV_CHAINLIT_PORT)s
directory=/app
autostart=true
autorestart=true
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0
```

### 12.3 GitHub Actions Workflow

```yaml
# filepath: .github/workflows/build-deploy.yml
name: Build and Deploy

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
          
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          
      - name: Run tests
        run: pytest

  build:
    needs: test
    if: github.event_name == 'push'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Podman
        uses: containers/podman-action@v1
        with:
          podman-version: '4'
          
      - name: Build Container
        run: |
          podman build -t mental-health-companion:${{ github.sha }} -f infrastructure/scripts/Dockerfile .
          podman tag mental-health-companion:${{ github.sha }} mental-health-companion:latest
      
      - name: Login to Registry
        if: github.ref == 'refs/heads/main'
        uses: azure/docker-login@v1
        with:
          login-server: ${{ secrets.REGISTRY_URL }}
          username: ${{ secrets.REGISTRY_USERNAME }}
          password: ${{ secrets.REGISTRY_PASSWORD }}
      
      - name: Push Image
        if: github.ref == 'refs/heads/main'
        run: |
          podman push mental-health-companion:latest ${{ secrets.REGISTRY_URL }}/mental-health-companion:latest
          podman push mental-health-companion:${{ github.sha }} ${{ secrets.REGISTRY_URL }}/mental-health-companion:${{ github.sha }}
```

## 13. Tiered Features

- Basic mood tracking (3 entries per day)
- Standard journaling (text only)
- 5 basic mindfulness exercises
- Weekly mood insights
- Basic conversational support
- 30-day data retention



## 14. Implementation Timeline

### Phase 1: MVP Development
- Repository Project Setup <span style="color: green;">✔️ Completed</span>
- Testing Strategy Setup 
    - Unit Testing 
        - Plugin Unit Tests <span style="color: green;">✔️ Completed</span>
        - API Unit Tests
    - Integration Testing 
        - Database Integration Tests <span style="color: green;">✔️ Completed</span>
        - Plugin Integration Tests
        - API Integration Tests
- Core API Development 
- Firebase Authentication integration
- Basic Chainlit conversational interface
- Core Semantic Kernel plugins <span style="color: green;">✔️ Completed</span>
- Initial Cosmos DB implementation <span style="color: green;">✔️ Completed</span>
- Basic mood tracking and journaling
- User feedback integration
- Performance optimization
- Security hardening
- Documentation completion
- Launch preparation

### Phase 2: Mobile Extension
- React Native app development
- Mobile UI components
- Cross-platform sync
- Push notifications
- Offline capabilities
- App store preparation

### Phase 3: Advanced Features
- Complete plugin implementation
- Advanced mood analysis
- Mindfulness exercise library
- User engagement metrics
- Enhanced data privacy measures


## 15. Testing Strategy

### 15.1 Unit Testing
- Use `pytest` for unit testing.
- Create test cases for each function in the plugins and API endpoints.
    - Test the functionality of `Journaling`,`Mindfulness`, `MoodAnalyzer` and `SafetyPlugin`.
- Mock external dependencies (e.g., Cosmos DB, Semantic Kernel) to isolate tests.   

```python
# filepath: tests/unit/plugins/test_mood_analyzer.py
import pytest
from backend.plugins.mood_analyzer import MoodAnalyzerPlugin
import semantic_kernel as sk

@pytest.fixture
def kernel():
    """Create a test kernel instance"""
    kernel = sk.Kernel()
    # Mock semantic function to return predictable results
    kernel.invoke_semantic_function = lambda prompt, service_id: "happy, relaxed"
    return kernel

@pytest.fixture
def mood_analyzer(kernel):
    """Create a mood analyzer plugin instance"""
    plugin = MoodAnalyzerPlugin()
    plugin.kernel = kernel
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
```

### 15.2 Integration Testing

```python
# filepath: tests/integration/api/test_journal_api.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from backend.api.main import app
from shared.models.user import User
from shared.models.journal import JournalEntry
from datetime import datetime

# Mock authenticated user for tests
test_user = User(
    id="test-user-id",
    email="test@example.com",
    created_at=datetime.utcnow(),
    subscription_tier="free"
)

# Create test client
client = TestClient(app)

# Mock the get_current_user dependency
@pytest.fixture(autouse=True)
def override_get_current_user():
    with patch("backend.shared.auth.get_current_user", return_value=test_user):
        yield

# Mock CosmosService
@pytest.fixture(autouse=True)
def mock_cosmos_service():
    with patch("backend.shared.cosmos.CosmosService") as mock:
        # Setup mock return values
        instance = mock.return_value
        instance.get_journal_entries.return_value = [
            JournalEntry(
                id="test-entry-1",
                user_id=test_user.id,
                content="Test journal entry",
                created_at=datetime.utcnow(),
                mood_indicators=["calm", "focused"],
                mood_score=7
            )
        ]
        
        instance.create_journal_entry.return_value = JournalEntry(
            id="new-entry-id",
            user_id=test_user.id,
            content="New test entry",
            created_at=datetime.utcnow(),
            mood_indicators=["happy"],
            mood_score=8
        )
        
        yield mock

# Mock KernelService
@pytest.fixture(autouse=True)
def mock_kernel_service():
    with patch("backend.shared.kernel.KernelService") as mock:
        instance = mock.return_value
        instance.analyze_journal_entry.return_value = {
            "insights": "Test insights"
        }
        instance.generate_journal_prompt.return_value = "What made you happy today?"
        yield mock

def test_get_journal_entries():
    """Test retrieving journal entries"""
    response = client.get("/api/journal/")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["content"] == "Test journal entry"

def test_create_journal_entry():
    """Test creating a journal entry"""
    entry_data = {
        "content": "New test entry",
        "mood_indicators": ["happy"],
        "mood_score": 8
    }
    
    response = client.post("/api/journal/", json=entry_data)
    assert response.status_code == 200
    result = response.json()
    assert result["content"] == "New test entry"
    assert result["user_id"] == test_user.id

def test_generate_journal_prompt():
    """Test generating a journal prompt"""
    response = client.post("/api/journal/prompt", params={"mood": "happy"})
    assert response.status_code == 200
    assert response.json()["prompt"] == "What made you happy today?"
```

## 16. Build and Deployment

### 16.1 Build and Deployment Steps

The project uses GitHub Actions for CI/CD to automate testing, building, and deploying the application. Below are the steps included in the pipeline:

#### 16.1.1 Testing
1. Checkout the repository using `actions/checkout@v3`.
2. Set up Python environment using `actions/setup-python@v4` with Python version 3.10.
3. Install dependencies using `pip install -r requirements.txt`.
4. Run tests using `pytest` and generate a coverage report.

#### 16.1.2 Building
1. Build the backend container:
   - Use `podman build` to create a container image for the backend.
   - Tag the image with the latest commit SHA and `latest` tag.
2. Build the frontend container:
   - Navigate to the `frontend/chainlit` directory.
   - Use `chainlit build` to build the frontend application.
   - Use `podman build` to create a container image for the frontend.
   - Tag the image with the latest commit SHA and `latest` tag.

#### 16.1.3 Deployment
1. Login to Azure Container Registry using `azure/docker-login@v1`.
2. Push the backend and frontend container images to the Azure Container Registry.
3. Deploy the backend to Azure Container Instances:
   - Use `az container create` to deploy the backend container.
   - Configure environment variables such as `COSMOS_CONNECTION_STRING`, `FIREBASE_CONFIG`, `PRIMARY_MODEL`, and `SENTIMENT_MODEL`.
4. Deploy the frontend to Azure Container Instances:
   - Use `az container create` to deploy the frontend container.
   - Expose the application on port 8501.
````
