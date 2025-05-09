import os
import logging
import time
import uuid
import json
from typing import Dict, Any, Optional
from pathlib import Path
import semantic_kernel as sk
# Replace HuggingFace imports with Azure OpenAI
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, AzureTextCompletion
from semantic_kernel.connectors.ai.open_ai import OpenAIChatPromptExecutionSettings
#from semantic_kernel.prompt_template import PromptExecutionSettings
from semantic_kernel.agents import ChatCompletionAgent,ChatHistoryAgentThread
from semantic_kernel.contents import ChatMessageContent, AuthorRole
from semantic_kernel.contents import ChatHistory
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from opencensus.ext.azure.log_exporter import AzureLogHandler
from dotenv import load_dotenv
from backend.shared.azure_agent_service import AzureAgentService

class KernelService:
    """Service for managing Semantic Kernel instances and operations"""
    
    def __init__(self):
        """Initialize the kernel service with proper configuration"""
        load_dotenv()
        self.kernel = self._initialize_kernel()
        self.correlation_prefix = f"mhc-{uuid.uuid4().hex[:6]}"
    
    def _initialize_kernel(self):
        """Initialize and configure Semantic Kernel with Azure OpenAI models"""
        kernel = sk.Kernel()
        
        try:
            # Get API key securely
            azure_api_key = self._get_secret("AZURE_OPENAI_API_KEY")
            azure_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
            
            # Get model configurations
            text_deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT_TEXT")
            classification_deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT_CLASSIFICATION")
            
            # Optional: Get model IDs if different from deployment names
            text_model = os.environ.get("AZURE_OPENAI_MODEL_TEXT", text_deployment)
            classification_model = os.environ.get("AZURE_OPENAI_MODEL_CLASSIFICATION", classification_deployment)
            
            # Configure text completion service for conversation
            conversation_service = self._create_azure_chat_completion(
                deployment_name=text_deployment,
                endpoint=azure_endpoint,
                api_key=azure_api_key,
                model_id=text_model
            )
            
            # Add the service to the kernel
            kernel.add_chat_service(
                service_id="conversation",
                service=conversation_service
            )
            logging.info(f"Configured Azure OpenAI text completion model: {text_deployment}")
            
            # Configure classification service for sentiment analysis
            classification_service = self._create_azure_chat_completion(
                deployment_name=classification_deployment,
                endpoint=azure_endpoint,
                api_key=azure_api_key,
                model_id=classification_model
            )
            kernel.add_chat_service(
                service_id="classification",
                service=classification_service
            )
            logging.info(f"Configured Azure OpenAI classification model: {classification_deployment}")
            
            # Register plugins
            self._register_plugins(kernel)
            
            return kernel
            
        except Exception as e:
            logging.error(f"Failed to initialize kernel: {str(e)}")
            raise RuntimeError(f"Kernel initialization failed: {str(e)}")
    
    def _create_azure_chat_completion(self, deployment_name: str, endpoint: str, 
                                      api_key: str, model_id: str = None) -> AzureChatCompletion:
        """Create an Azure OpenAI chat completion service with proper error handling"""
        try:
            # For Azure environments, prefer managed identity authentication
            if "IDENTITY_ENDPOINT" in os.environ:
                logging.info("Using managed identity for Azure OpenAI authentication")
                # Use DefaultAzureCredential for managed identity authentication
                service = AzureChatCompletion(
                    deployment_name=deployment_name,
                    endpoint=endpoint,
                    model_id=model_id
                    # No api_key - will use DefaultAzureCredential
                )
            else:
                # For development environments, use API key authentication
                service = AzureChatCompletion(
                    deployment_name=deployment_name,
                    endpoint=endpoint,
                    api_key=api_key,
                    model_id=model_id
                )
                
            return service
        except Exception as e:
            logging.error(f"Failed to initialize Azure OpenAI service for {deployment_name}: {str(e)}")
            raise RuntimeError(f"Azure OpenAI service initialization failed: {str(e)}")
    
    def _get_secret(self, secret_name):
        """Get a secret from Azure Key Vault or environment variables"""
        # In production, use Key Vault with Managed Identity
        if os.environ.get("AZURE_KEYVAULT_URL"):
            try:
                # Use DefaultAzureCredential for managed identity in production
                credential = DefaultAzureCredential()
                vault_url = os.environ.get("AZURE_KEYVAULT_URL")
                client = SecretClient(vault_url=vault_url, credential=credential)
                return client.get_secret(secret_name).value
            except Exception as e:
                logging.warning(f"Failed to get secret from Key Vault: {str(e)}")
                logging.warning("Falling back to environment variable")
        
        # Fallback to environment variable
        return os.environ.get(secret_name)
    
    def _register_plugins(self, kernel):
        """Register semantic kernel plugins"""
        try:
            # Import and register your plugins here
            from backend.plugins.mood_analyzer import MoodAnalyzerPlugin
            from backend.plugins.journaling import JournalingPlugin
            from backend.plugins.mindfulness import MindfulnessPlugin
            
            # Register plugins with the kernel
            kernel.add_plugin(MoodAnalyzerPlugin(kernel), "mood")
            kernel.add_plugin(JournalingPlugin(kernel), "journal")
            kernel.add_plugin(MindfulnessPlugin(kernel), "mindfulness")
            
            logging.info("Successfully registered all plugins")
        except Exception as e:
            logging.error(f"Error registering plugins: {str(e)}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError))
    )
    async def _call_remote_model(self, plugin_name, function_name, **kwargs):
        """Call a remote model with retry logic, telemetry, and Azure best practices"""
        correlation_id = f"{self.correlation_prefix}-{uuid.uuid4().hex[:8]}"
        start_time = time.time()
        
        # Add correlation ID to Application Insights
        logging.info(f"Calling remote model", extra={
            "correlation_id": correlation_id,
            "plugin": plugin_name,
            "function": function_name,
            "params": {k: v for k, v in kwargs.items() if k != "input" or len(str(v)) < 50}
        })
        
        try:
            # Invoke the plugin with the kernel
            result = await self.kernel.invoke_plugin(plugin_name, function_name, **kwargs)
            
            # Log successful completion with metrics
            elapsed_ms = (time.time() - start_time) * 1000
            logging.info(f"Remote model call completed", extra={
                "correlation_id": correlation_id,
                "elapsed_ms": elapsed_ms,
                "status": "success"
            })
            
            return result
        except Exception as e:
            # Log failures with detailed diagnostics
            elapsed_ms = (time.time() - start_time) * 1000
            logging.error(f"Remote model call failed", extra={
                "correlation_id": correlation_id,
                "elapsed_ms": elapsed_ms,
                "error": str(e),
                "error_type": type(e).__name__
            })
            raise
    
    async def analyze_mood(self, text):
        """Analyze text to determine mood using remote model"""
        result = await self._call_remote_model("mood", "analyze_mood", input=text)
        return {"mood": str(result).strip()}
    
    async def generate_journal_prompt(self, mood=None):
        """Generate a journal prompt based on mood"""
        result = await self._call_remote_model("journal", "create_prompt", mood=mood or "")
        return str(result).strip()
    
    async def analyze_journal_entry(self, entry):
        """Analyze a journal entry for insights"""
        result = await self._call_remote_model("journal", "analyze_entry", entry=entry)
        return {"insights": str(result).strip()}