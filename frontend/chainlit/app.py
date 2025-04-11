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