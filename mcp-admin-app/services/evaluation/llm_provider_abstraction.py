"""
LLM Provider Abstraction Layer
=============================

Unified interface for multiple LLM providers supporting parallel execution.
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from concurrent.futures import ThreadPoolExecutor, as_completed

from models.llm import LLMProviderConfig, ModelConfig, TokenEstimate, CostEstimate, TestExecution


@dataclass
class LLMRequest:
    """Standardized request format for all LLM providers."""
    prompt: str
    model_id: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    stop_sequences: Optional[List[str]] = None
    stream: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMResponse:
    """Standardized response format from all LLM providers."""
    content: str
    model_id: str
    provider_id: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    response_time: float
    cost: float
    success: bool
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "content": self.content,
            "model_id": self.model_id,
            "provider_id": self.provider_id,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "response_time": self.response_time,
            "cost": self.cost,
            "success": self.success,
            "error": self.error,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }


class BaseLLMProvider(ABC):
    """Abstract base class for all LLM providers."""
    
    def __init__(self, config: LLMProviderConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{config.name}")
        self._initialized = False
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the provider (authenticate, validate config, etc.)."""
        pass
    
    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response from the LLM."""
        pass
    
    @abstractmethod
    def estimate_tokens(self, text: str, model_id: str) -> TokenEstimate:
        """Estimate token count for given text."""
        pass
    
    @abstractmethod
    def estimate_cost(self, input_tokens: int, output_tokens: int, model_id: str) -> CostEstimate:
        """Estimate cost for given token counts."""
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[ModelConfig]:
        """Get list of available models for this provider."""
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """Test connection to the provider."""
        pass
    
    def is_initialized(self) -> bool:
        """Check if provider is initialized."""
        return self._initialized


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API provider implementation."""
    
    def __init__(self, config: LLMProviderConfig):
        super().__init__(config)
        self.api_key = None
        self.base_url = config.endpoint_url or "https://api.openai.com/v1"
    
    async def initialize(self) -> bool:
        """Initialize OpenAI provider."""
        try:
            # In a real implementation, this would load encrypted credentials
            self.api_key = self.config.settings.get("api_key")
            if not self.api_key:
                self.logger.error("OpenAI API key not found in configuration")
                return False
            
            # Test connection
            if await self.test_connection():
                self._initialized = True
                self.logger.info("OpenAI provider initialized successfully")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to initialize OpenAI provider: {e}")
            return False
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response using OpenAI API."""
        start_time = time.time()
        
        try:
            # Simulate API call (in real implementation, use openai library)
            await asyncio.sleep(0.1)  # Simulate network delay
            
            # Mock response for demonstration
            response_content = f"OpenAI response to: {request.prompt[:50]}..."
            input_tokens = len(request.prompt.split()) * 1.3  # Rough estimate
            output_tokens = len(response_content.split()) * 1.3
            
            response_time = time.time() - start_time
            cost = self.estimate_cost(int(input_tokens), int(output_tokens), request.model_id).total_estimated_cost
            
            return LLMResponse(
                content=response_content,
                model_id=request.model_id,
                provider_id=self.config.id,
                input_tokens=int(input_tokens),
                output_tokens=int(output_tokens),
                total_tokens=int(input_tokens + output_tokens),
                response_time=response_time,
                cost=cost,
                success=True
            )
        
        except Exception as e:
            response_time = time.time() - start_time
            self.logger.error(f"OpenAI API call failed: {e}")
            
            return LLMResponse(
                content="",
                model_id=request.model_id,
                provider_id=self.config.id,
                input_tokens=0,
                output_tokens=0,
                total_tokens=0,
                response_time=response_time,
                cost=0.0,
                success=False,
                error=str(e)
            )
    
    def estimate_tokens(self, text: str, model_id: str) -> TokenEstimate:
        """Estimate tokens for OpenAI models."""
        # Rough estimation (in real implementation, use tiktoken)
        word_count = len(text.split())
        estimated_tokens = int(word_count * 1.3)  # Rough conversion
        
        return TokenEstimate(
            input_tokens=estimated_tokens,
            estimated_output_tokens=estimated_tokens // 2,  # Assume half for output
            confidence_level=0.8,
            tokenizer_used="openai_estimate"
        )
    
    def estimate_cost(self, input_tokens: int, output_tokens: int, model_id: str) -> CostEstimate:
        """Estimate cost for OpenAI models."""
        # Default pricing (should be loaded from config)
        pricing = {
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-3.5-turbo": {"input": 0.001, "output": 0.002},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03}
        }
        
        model_pricing = pricing.get(model_id, pricing["gpt-3.5-turbo"])
        input_cost = (input_tokens / 1000) * model_pricing["input"]
        output_cost = (output_tokens / 1000) * model_pricing["output"]
        
        return CostEstimate(
            input_cost=input_cost,
            estimated_output_cost=output_cost,
            total_estimated_cost=input_cost + output_cost,
            confidence_level=0.95
        )
    
    def get_available_models(self) -> List[ModelConfig]:
        """Get available OpenAI models."""
        return [
            ModelConfig(
                model_id="gpt-4",
                display_name="GPT-4",
                max_tokens=8192,
                input_cost_per_token=0.00003,
                output_cost_per_token=0.00006,
                context_window=8192
            ),
            ModelConfig(
                model_id="gpt-3.5-turbo",
                display_name="GPT-3.5 Turbo",
                max_tokens=4096,
                input_cost_per_token=0.000001,
                output_cost_per_token=0.000002,
                context_window=4096
            )
        ]
    
    async def test_connection(self) -> bool:
        """Test OpenAI API connection."""
        try:
            # Simulate connection test
            await asyncio.sleep(0.05)
            return True
        except Exception as e:
            self.logger.error(f"OpenAI connection test failed: {e}")
            return False


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude API provider implementation."""
    
    def __init__(self, config: LLMProviderConfig):
        super().__init__(config)
        self.api_key = None
        self.base_url = config.endpoint_url or "https://api.anthropic.com"
    
    async def initialize(self) -> bool:
        """Initialize Anthropic provider."""
        try:
            self.api_key = self.config.settings.get("api_key")
            if not self.api_key:
                self.logger.error("Anthropic API key not found in configuration")
                return False
            
            if await self.test_connection():
                self._initialized = True
                self.logger.info("Anthropic provider initialized successfully")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to initialize Anthropic provider: {e}")
            return False
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response using Anthropic API."""
        start_time = time.time()
        
        try:
            # Simulate API call
            await asyncio.sleep(0.15)  # Simulate network delay
            
            response_content = f"Claude response to: {request.prompt[:50]}..."
            input_tokens = len(request.prompt.split()) * 1.2
            output_tokens = len(response_content.split()) * 1.2
            
            response_time = time.time() - start_time
            cost = self.estimate_cost(int(input_tokens), int(output_tokens), request.model_id).total_estimated_cost
            
            return LLMResponse(
                content=response_content,
                model_id=request.model_id,
                provider_id=self.config.id,
                input_tokens=int(input_tokens),
                output_tokens=int(output_tokens),
                total_tokens=int(input_tokens + output_tokens),
                response_time=response_time,
                cost=cost,
                success=True
            )
        
        except Exception as e:
            response_time = time.time() - start_time
            self.logger.error(f"Anthropic API call failed: {e}")
            
            return LLMResponse(
                content="",
                model_id=request.model_id,
                provider_id=self.config.id,
                input_tokens=0,
                output_tokens=0,
                total_tokens=0,
                response_time=response_time,
                cost=0.0,
                success=False,
                error=str(e)
            )
    
    def estimate_tokens(self, text: str, model_id: str) -> TokenEstimate:
        """Estimate tokens for Anthropic models."""
        word_count = len(text.split())
        estimated_tokens = int(word_count * 1.2)
        
        return TokenEstimate(
            input_tokens=estimated_tokens,
            estimated_output_tokens=estimated_tokens // 2,
            confidence_level=0.75,
            tokenizer_used="anthropic_estimate"
        )
    
    def estimate_cost(self, input_tokens: int, output_tokens: int, model_id: str) -> CostEstimate:
        """Estimate cost for Anthropic models."""
        pricing = {
            "claude-3-opus": {"input": 0.015, "output": 0.075},
            "claude-3-sonnet": {"input": 0.003, "output": 0.015},
            "claude-3-haiku": {"input": 0.00025, "output": 0.00125}
        }
        
        model_pricing = pricing.get(model_id, pricing["claude-3-sonnet"])
        input_cost = (input_tokens / 1000) * model_pricing["input"]
        output_cost = (output_tokens / 1000) * model_pricing["output"]
        
        return CostEstimate(
            input_cost=input_cost,
            estimated_output_cost=output_cost,
            total_estimated_cost=input_cost + output_cost,
            confidence_level=0.95
        )
    
    def get_available_models(self) -> List[ModelConfig]:
        """Get available Anthropic models."""
        return [
            ModelConfig(
                model_id="claude-3-opus",
                display_name="Claude 3 Opus",
                max_tokens=4096,
                input_cost_per_token=0.000015,
                output_cost_per_token=0.000075,
                context_window=200000
            ),
            ModelConfig(
                model_id="claude-3-sonnet",
                display_name="Claude 3 Sonnet",
                max_tokens=4096,
                input_cost_per_token=0.000003,
                output_cost_per_token=0.000015,
                context_window=200000
            )
        ]
    
    async def test_connection(self) -> bool:
        """Test Anthropic API connection."""
        try:
            await asyncio.sleep(0.05)
            return True
        except Exception as e:
            self.logger.error(f"Anthropic connection test failed: {e}")
            return False


class GeminiProvider(BaseLLMProvider):
    """Google Gemini API provider implementation."""
    
    def __init__(self, config: LLMProviderConfig):
        super().__init__(config)
        self.api_key = None
        self.base_url = config.endpoint_url or "https://generativelanguage.googleapis.com"
    
    async def initialize(self) -> bool:
        """Initialize Gemini provider."""
        try:
            self.api_key = self.config.settings.get("api_key")
            if not self.api_key:
                self.logger.error("Gemini API key not found in configuration")
                return False
            
            if await self.test_connection():
                self._initialized = True
                self.logger.info("Gemini provider initialized successfully")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to initialize Gemini provider: {e}")
            return False
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response using Gemini API."""
        start_time = time.time()
        
        try:
            # Simulate API call
            await asyncio.sleep(0.12)
            
            response_content = f"Gemini response to: {request.prompt[:50]}..."
            input_tokens = len(request.prompt.split()) * 1.1
            output_tokens = len(response_content.split()) * 1.1
            
            response_time = time.time() - start_time
            cost = self.estimate_cost(int(input_tokens), int(output_tokens), request.model_id).total_estimated_cost
            
            return LLMResponse(
                content=response_content,
                model_id=request.model_id,
                provider_id=self.config.id,
                input_tokens=int(input_tokens),
                output_tokens=int(output_tokens),
                total_tokens=int(input_tokens + output_tokens),
                response_time=response_time,
                cost=cost,
                success=True
            )
        
        except Exception as e:
            response_time = time.time() - start_time
            self.logger.error(f"Gemini API call failed: {e}")
            
            return LLMResponse(
                content="",
                model_id=request.model_id,
                provider_id=self.config.id,
                input_tokens=0,
                output_tokens=0,
                total_tokens=0,
                response_time=response_time,
                cost=0.0,
                success=False,
                error=str(e)
            )
    
    def estimate_tokens(self, text: str, model_id: str) -> TokenEstimate:
        """Estimate tokens for Gemini models."""
        word_count = len(text.split())
        estimated_tokens = int(word_count * 1.1)
        
        return TokenEstimate(
            input_tokens=estimated_tokens,
            estimated_output_tokens=estimated_tokens // 2,
            confidence_level=0.7,
            tokenizer_used="gemini_estimate"
        )
    
    def estimate_cost(self, input_tokens: int, output_tokens: int, model_id: str) -> CostEstimate:
        """Estimate cost for Gemini models."""
        pricing = {
            "gemini-pro": {"input": 0.0005, "output": 0.0015},
            "gemini-pro-vision": {"input": 0.00025, "output": 0.00075}
        }
        
        model_pricing = pricing.get(model_id, pricing["gemini-pro"])
        input_cost = (input_tokens / 1000) * model_pricing["input"]
        output_cost = (output_tokens / 1000) * model_pricing["output"]
        
        return CostEstimate(
            input_cost=input_cost,
            estimated_output_cost=output_cost,
            total_estimated_cost=input_cost + output_cost,
            confidence_level=0.9
        )
    
    def get_available_models(self) -> List[ModelConfig]:
        """Get available Gemini models."""
        return [
            ModelConfig(
                model_id="gemini-pro",
                display_name="Gemini Pro",
                max_tokens=8192,
                input_cost_per_token=0.0000005,
                output_cost_per_token=0.0000015,
                context_window=32768
            )
        ]
    
    async def test_connection(self) -> bool:
        """Test Gemini API connection."""
        try:
            await asyncio.sleep(0.05)
            return True
        except Exception as e:
            self.logger.error(f"Gemini connection test failed: {e}")
            return False


class LocalModelProvider(BaseLLMProvider):
    """Local model provider (Ollama, etc.) implementation."""
    
    def __init__(self, config: LLMProviderConfig):
        super().__init__(config)
        self.base_url = config.endpoint_url or "http://localhost:11434"
    
    async def initialize(self) -> bool:
        """Initialize local model provider."""
        try:
            if await self.test_connection():
                self._initialized = True
                self.logger.info("Local model provider initialized successfully")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to initialize local model provider: {e}")
            return False
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response using local model."""
        start_time = time.time()
        
        try:
            # Simulate local model call
            await asyncio.sleep(0.5)  # Local models are typically slower
            
            response_content = f"Local model response to: {request.prompt[:50]}..."
            input_tokens = len(request.prompt.split())
            output_tokens = len(response_content.split())
            
            response_time = time.time() - start_time
            
            return LLMResponse(
                content=response_content,
                model_id=request.model_id,
                provider_id=self.config.id,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                response_time=response_time,
                cost=0.0,  # Local models have no API cost
                success=True
            )
        
        except Exception as e:
            response_time = time.time() - start_time
            self.logger.error(f"Local model call failed: {e}")
            
            return LLMResponse(
                content="",
                model_id=request.model_id,
                provider_id=self.config.id,
                input_tokens=0,
                output_tokens=0,
                total_tokens=0,
                response_time=response_time,
                cost=0.0,
                success=False,
                error=str(e)
            )
    
    def estimate_tokens(self, text: str, model_id: str) -> TokenEstimate:
        """Estimate tokens for local models."""
        word_count = len(text.split())
        estimated_tokens = word_count  # Simple word-based estimation
        
        return TokenEstimate(
            input_tokens=estimated_tokens,
            estimated_output_tokens=estimated_tokens // 2,
            confidence_level=0.6,
            tokenizer_used="word_count"
        )
    
    def estimate_cost(self, input_tokens: int, output_tokens: int, model_id: str) -> CostEstimate:
        """Estimate cost for local models (always 0)."""
        return CostEstimate(
            input_cost=0.0,
            estimated_output_cost=0.0,
            total_estimated_cost=0.0,
            confidence_level=1.0
        )
    
    def get_available_models(self) -> List[ModelConfig]:
        """Get available local models."""
        return [
            ModelConfig(
                model_id="llama2",
                display_name="Llama 2",
                max_tokens=4096,
                input_cost_per_token=0.0,
                output_cost_per_token=0.0,
                context_window=4096
            ),
            ModelConfig(
                model_id="mistral",
                display_name="Mistral 7B",
                max_tokens=8192,
                input_cost_per_token=0.0,
                output_cost_per_token=0.0,
                context_window=8192
            )
        ]
    
    async def test_connection(self) -> bool:
        """Test local model connection."""
        try:
            await asyncio.sleep(0.1)
            return True
        except Exception as e:
            self.logger.error(f"Local model connection test failed: {e}")
            return False


class MultiModelExecutor:
    """Executes prompts across multiple models in parallel."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.providers: Dict[str, BaseLLMProvider] = {}
        self.max_concurrent = 5
    
    def add_provider(self, provider: BaseLLMProvider) -> None:
        """Add a provider to the executor."""
        self.providers[provider.config.id] = provider
        self.logger.info(f"Added provider: {provider.config.name}")
    
    def remove_provider(self, provider_id: str) -> None:
        """Remove a provider from the executor."""
        if provider_id in self.providers:
            del self.providers[provider_id]
            self.logger.info(f"Removed provider: {provider_id}")
    
    async def execute_parallel(self, request: LLMRequest, provider_ids: List[str]) -> List[LLMResponse]:
        """Execute request across multiple providers in parallel."""
        if not provider_ids:
            provider_ids = list(self.providers.keys())
        
        # Filter to available providers
        available_providers = [
            self.providers[pid] for pid in provider_ids 
            if pid in self.providers and self.providers[pid].is_initialized()
        ]
        
        if not available_providers:
            self.logger.warning("No initialized providers available for execution")
            return []
        
        self.logger.info(f"Executing request across {len(available_providers)} providers")
        
        # Execute in parallel with semaphore to limit concurrency
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def execute_with_semaphore(provider: BaseLLMProvider) -> LLMResponse:
            async with semaphore:
                return await provider.generate(request)
        
        tasks = [execute_with_semaphore(provider) for provider in available_providers]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and convert to LLMResponse objects
        valid_responses = []
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                self.logger.error(f"Provider {available_providers[i].config.name} failed: {response}")
                # Create error response
                error_response = LLMResponse(
                    content="",
                    model_id=request.model_id,
                    provider_id=available_providers[i].config.id,
                    input_tokens=0,
                    output_tokens=0,
                    total_tokens=0,
                    response_time=0.0,
                    cost=0.0,
                    success=False,
                    error=str(response)
                )
                valid_responses.append(error_response)
            else:
                valid_responses.append(response)
        
        return valid_responses
    
    def get_provider_factory(self, provider_type: str) -> type:
        """Get provider class for given type."""
        provider_map = {
            "openai": OpenAIProvider,
            "anthropic": AnthropicProvider,
            "gemini": GeminiProvider,
            "local": LocalModelProvider,
            "ollama": LocalModelProvider
        }
        return provider_map.get(provider_type.lower(), LocalModelProvider)