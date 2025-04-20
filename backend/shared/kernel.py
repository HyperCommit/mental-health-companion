import os
import logging
import time
import uuid
from pathlib import Path
import semantic_kernel as sk
from semantic_kernel.connectors.ai.hugging_face import HuggingFaceTextCompletion
from semantic_kernel.connectors.ai.open_ai import AzureTextCompletion, OpenAITextCompletion
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from azure.identity import DefaultAzureCredential
#from azure.keyvault.secrets import SecretClient
from dotenv import load_dotenv

class KernelService:
    """Service for managing Semantic Kernel instances and operations"""
    
    def __init__(self):
        """Initialize the kernel service with proper configuration"""
        load_dotenv()
        self.kernel = self._initialize_kernel()
        self.correlation_prefix = f"mhc-{uuid.uuid4().hex[:6]}"
    
    def _initialize_kernel(self):
        """Initialize and configure Semantic Kernel with remote models"""
        kernel = sk.Kernel()
        
        try:
            # Get API key securely
            hf_api_token = self._get_secret("HUGGINGFACE_API_TOKEN")
            
            # Get model configurations
            primary_model = os.environ.get("PRIMARY_MODEL", "gpt2")
            sentiment_model = os.environ.get("SENTIMENT_MODEL", 
                                           "distilbert-base-uncased-finetuned-sst-2-english")
            
            # Configure primary conversation model
            conversation_service = self._create_huggingface_service(
                model_id=primary_model,
                task="text-generation"
            )
            
            # Use the correct method for the current API version
            # This is the current method in newer versions
            kernel.add_text_completion(
                service_id="conversation",
                service=conversation_service
            )
            logging.info(f"Configured remote conversation model: {primary_model}")
            
            # Configure sentiment analysis model
            sentiment_service = self._create_huggingface_service(
                model_id=sentiment_model,
                task="text-classification"
            )
            kernel.add_text_completion(
                service_id="sentiment",
                service=sentiment_service
            )
            logging.info(f"Configured remote sentiment analysis model: {sentiment_model}")
            
            # Set up HuggingFace token in environment
            os.environ["HUGGING_FACE_API_KEY"] = hf_api_token
            
            # Register plugins
            self._register_plugins(kernel)
            
            return kernel
            
        except Exception as e:
            logging.error(f"Failed to initialize kernel: {str(e)}")
            raise RuntimeError(f"Kernel initialization failed: {str(e)}")
    
    def _create_huggingface_service(self, model_id: str, task: str) -> HuggingFaceTextCompletion:
        """Create a HuggingFace service with proper error handling"""
        try:
            # Create service with the correct parameters
            service = HuggingFaceTextCompletion(
                ai_model_id=model_id,  # Updated parameter name
                task=task
            )
            return service
        except Exception as e:
            logging.error(f"Failed to initialize HuggingFace service for {model_id}: {str(e)}")
            raise RuntimeError(f"HuggingFace service initialization failed: {str(e)}")
    
    def _get_secret(self, secret_name):
        """Get a secret from Azure Key Vault or environment variables"""
        # In production, use Key Vault with Managed Identity
        if os.environ.get("AZURE_KEYVAULT_URL"):
            try:
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
        """Call a remote model with retry logic and telemetry"""
        correlation_id = f"{self.correlation_prefix}-{uuid.uuid4().hex[:8]}"
        start_time = time.time()
        
        logging.info(f"Calling remote model", extra={
            "correlation_id": correlation_id,
            "plugin": plugin_name,
            "function": function_name,
            "params": {k: v for k, v in kwargs.items() if k != "input" or len(str(v)) < 50}
        })
        
        try:
            result = await self.kernel.invoke_plugin(plugin_name, function_name, **kwargs)
            
            elapsed_ms = (time.time() - start_time) * 1000
            logging.info(f"Remote model call completed in {elapsed_ms:.2f}ms", extra={
                "correlation_id": correlation_id,
                "elapsed_ms": elapsed_ms
            })
            
            return result
        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            logging.error(f"Remote model call failed: {str(e)}", extra={
                "correlation_id": correlation_id,
                "elapsed_ms": elapsed_ms,
                "error": str(e)
            })
            raise
    
    # Replace direct kernel calls with the enhanced method
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