import os
import logging
import uuid
import time
from typing import Dict, Any, Optional

from semantic_kernel.agents import ChatCompletionAgent,ChatHistoryAgentThread
from semantic_kernel.contents import ChatMessageContent, AuthorRole
from semantic_kernel.connectors.ai.open_ai import OpenAIChatPromptExecutionSettings
#from semantic_kernel.prompt_template import PromptExecutionSettings
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from opencensus.ext.azure.log_exporter import AzureLogHandler

class AzureAgentService:
    """Service for creating and managing Azure OpenAI agents with best practices"""
    
    def __init__(self, kernel):
        """Initialize the Azure Agent Service"""
        self.kernel = kernel
        self.correlation_prefix = f"azure-agent-{uuid.uuid4().hex[:6]}"
        
        # Set up Azure Application Insights logging
        if os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING"):
            handler = AzureLogHandler()
            logging.getLogger().addHandler(handler)
            logging.info("Azure Application Insights configured for agent telemetry")
    
    def create_conversation_agent(self, instructions: str) -> ChatCompletionAgent:
        """Create a conversation agent using Azure OpenAI"""
        settings = OpenAIChatPromptExecutionSettings(
            service_id="conversation",
            temperature=0.7,
            max_tokens=1000,
            top_p=0.95,
            enable_azure_content_filtering=True  # Azure-specific safety feature
        )
        
        agent = ChatCompletionAgent(
            kernel=self.kernel,
            name="ConversationAgent",
            instructions=instructions,
            arguments=settings
        )
        
        return agent
    
    def create_classification_agent(self, instructions: str) -> ChatCompletionAgent:
        """Create a classification agent using Azure OpenAI"""
        settings = OpenAIChatPromptExecutionSettings(
            service_id="classification",
            temperature=0.1,  # Lower temperature for more deterministic responses
            max_tokens=300,
            top_p=0.5,
            enable_azure_content_filtering=True
        )
        
        agent = ChatCompletionAgent(
            kernel=self.kernel,
            name="ClassificationAgent",
            instructions=instructions,
            arguments=settings
        )
        
        return agent
        
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError))
    )
    async def get_agent_response(self, agent: ChatCompletionAgent, 
                              message: str, thread: Optional[ChatHistoryAgentThread] = None) -> Dict:
        """Get a response from an agent with Azure-optimized monitoring and error handling"""
        correlation_id = f"{self.correlation_prefix}-{uuid.uuid4().hex[:8]}"
        start_time = time.time()
        
        if thread is None:
            thread = ChatHistoryAgentThread()
        
        try:
            # Log the request with Azure-compatible dimensions
            logging.info("Azure OpenAI request initiated", extra={
                "custom_dimensions": {
                    "correlation_id": correlation_id,
                    "agent_name": agent.name,
                    "message_length": len(message),
                    "service_id": agent.arguments.get("service_id", "unknown") if hasattr(agent, "arguments") else "unknown"
                }
            })
            
            # Create user message
            user_message = ChatMessageContent(
                role=AuthorRole.USER,
                content=message
            )
            
            # Get the agent's response with timeout handling
            response = await agent.get_response(
                messages=user_message, 
                thread=thread
            )
            
            # Calculate and log metrics
            elapsed_ms = (time.time() - start_time) * 1000
            response_length = len(response.value.content) if response and response.value else 0
            
            logging.info("Azure OpenAI request completed", extra={
                "custom_dimensions": {
                    "correlation_id": correlation_id,
                    "elapsed_ms": elapsed_ms,
                    "response_length": response_length,
                    "agent_name": agent.name,
                    "success": True
                }
            })
            
            return {
                "response": response.value.content if response and response.value else "",
                "thread": response.thread
            }
        except Exception as e:
            # Log failure with Azure-compatible format
            elapsed_ms = (time.time() - start_time) * 1000
            logging.error(f"Azure OpenAI request failed: {str(e)}", extra={
                "custom_dimensions": {
                    "correlation_id": correlation_id,
                    "elapsed_ms": elapsed_ms,
                    "error_type": type(e).__name__,
                    "error": str(e),
                    "agent_name": agent.name if agent else "unknown",
                    "success": False
                }
            })
            raise