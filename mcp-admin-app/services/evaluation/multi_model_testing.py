"""
Multi-Model Testing Infrastructure
=================================

Infrastructure for testing prompts across multiple LLM providers simultaneously.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from concurrent.futures import ThreadPoolExecutor

from .llm_provider_abstraction import (
    BaseLLMProvider, MultiModelExecutor, LLMRequest, LLMResponse,
    OpenAIProvider, AnthropicProvider, GeminiProvider, LocalModelProvider
)
from models.llm import LLMProviderConfig, TestExecution, TestStatus, TestType
from models.base import generate_id


@dataclass
class TestConfiguration:
    """Configuration for multi-model testing."""
    test_id: str = field(default_factory=generate_id)
    name: str = ""
    description: str = ""
    prompt_template_id: str = ""
    provider_configs: List[str] = field(default_factory=list)  # Provider IDs
    model_configs: Dict[str, str] = field(default_factory=dict)  # provider_id -> model_id
    test_parameters: Dict[str, Any] = field(default_factory=dict)
    iterations: int = 1
    parallel_execution: bool = True
    timeout_seconds: int = 30
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = "system"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "test_id": self.test_id,
            "name": self.name,
            "description": self.description,
            "prompt_template_id": self.prompt_template_id,
            "provider_configs": self.provider_configs,
            "model_configs": self.model_configs,
            "test_parameters": self.test_parameters,
            "iterations": self.iterations,
            "parallel_execution": self.parallel_execution,
            "timeout_seconds": self.timeout_seconds,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by
        }


@dataclass
class TestSession:
    """A testing session containing multiple test runs."""
    session_id: str = field(default_factory=generate_id)
    name: str = ""
    configurations: List[TestConfiguration] = field(default_factory=list)
    status: TestStatus = TestStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    total_cost: float = 0.0
    results: List[TestExecution] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "session_id": self.session_id,
            "name": self.name,
            "configurations": [config.to_dict() for config in self.configurations],
            "status": self.status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "total_executions": self.total_executions,
            "successful_executions": self.successful_executions,
            "failed_executions": self.failed_executions,
            "total_cost": self.total_cost,
            "results": [result.to_dict() for result in self.results],
            "metadata": self.metadata
        }


class MultiModelTestingInfrastructure:
    """Infrastructure for managing multi-model testing operations."""
    
    def __init__(self, config_manager, db_manager):
        self.logger = logging.getLogger(__name__)
        self.config_manager = config_manager
        self.db_manager = db_manager
        self.executor = MultiModelExecutor()
        self.providers: Dict[str, BaseLLMProvider] = {}
        self.active_sessions: Dict[str, TestSession] = {}
        
        # Initialize default providers
        self._initialize_default_providers()
    
    def _initialize_default_providers(self):
        """Initialize default provider configurations."""
        try:
            # Load provider configurations from config
            provider_configs = self.config_manager.get("llm_providers", {})
            
            for provider_id, config_data in provider_configs.items():
                try:
                    config = LLMProviderConfig.from_dict(config_data)
                    provider = self._create_provider(config)
                    if provider:
                        self.providers[provider_id] = provider
                        self.executor.add_provider(provider)
                        self.logger.info(f"Initialized provider: {config.name}")
                except Exception as e:
                    self.logger.error(f"Failed to initialize provider {provider_id}: {e}")
        
        except Exception as e:
            self.logger.error(f"Failed to initialize providers: {e}")
    
    def _create_provider(self, config: LLMProviderConfig) -> Optional[BaseLLMProvider]:
        """Create provider instance based on configuration."""
        try:
            provider_class = self.executor.get_provider_factory(config.provider_type.value)
            return provider_class(config)
        except Exception as e:
            self.logger.error(f"Failed to create provider {config.name}: {e}")
            return None
    
    async def add_provider(self, config: LLMProviderConfig) -> bool:
        """Add a new provider to the testing infrastructure."""
        try:
            provider = self._create_provider(config)
            if not provider:
                return False
            
            # Initialize the provider
            if await provider.initialize():
                self.providers[config.id] = provider
                self.executor.add_provider(provider)
                
                # Save to configuration
                provider_configs = self.config_manager.get("llm_providers", {})
                provider_configs[config.id] = config.to_dict()
                self.config_manager.set("llm_providers", provider_configs)
                
                self.logger.info(f"Added provider: {config.name}")
                return True
            else:
                self.logger.error(f"Failed to initialize provider: {config.name}")
                return False
        
        except Exception as e:
            self.logger.error(f"Failed to add provider: {e}")
            return False
    
    def remove_provider(self, provider_id: str) -> bool:
        """Remove a provider from the testing infrastructure."""
        try:
            if provider_id in self.providers:
                del self.providers[provider_id]
                self.executor.remove_provider(provider_id)
                
                # Remove from configuration
                provider_configs = self.config_manager.get("llm_providers", {})
                if provider_id in provider_configs:
                    del provider_configs[provider_id]
                    self.config_manager.set("llm_providers", provider_configs)
                
                self.logger.info(f"Removed provider: {provider_id}")
                return True
            return False
        
        except Exception as e:
            self.logger.error(f"Failed to remove provider: {e}")
            return False
    
    def get_available_providers(self) -> List[Dict[str, Any]]:
        """Get list of available providers with their status."""
        providers = []
        for provider_id, provider in self.providers.items():
            providers.append({
                "id": provider_id,
                "name": provider.config.name,
                "type": provider.config.provider_type.value,
                "initialized": provider.is_initialized(),
                "models": [model.to_dict() for model in provider.get_available_models()]
            })
        return providers
    
    async def test_provider_connections(self) -> Dict[str, bool]:
        """Test connections to all providers."""
        results = {}
        for provider_id, provider in self.providers.items():
            try:
                results[provider_id] = await provider.test_connection()
            except Exception as e:
                self.logger.error(f"Connection test failed for {provider_id}: {e}")
                results[provider_id] = False
        return results
    
    def create_test_configuration(self, 
                                prompt_template_id: str,
                                provider_ids: List[str],
                                model_configs: Dict[str, str],
                                test_parameters: Dict[str, Any] = None,
                                name: str = "",
                                description: str = "",
                                iterations: int = 1) -> TestConfiguration:
        """Create a new test configuration."""
        config = TestConfiguration(
            name=name or f"Test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            description=description,
            prompt_template_id=prompt_template_id,
            provider_configs=provider_ids,
            model_configs=model_configs,
            test_parameters=test_parameters or {},
            iterations=iterations
        )
        
        self.logger.info(f"Created test configuration: {config.name}")
        return config
    
    async def execute_test_configuration(self, config: TestConfiguration) -> TestSession:
        """Execute a test configuration and return results."""
        session = TestSession(
            name=f"Session_{config.name}",
            configurations=[config],
            status=TestStatus.RUNNING,
            started_at=datetime.now()
        )
        
        self.active_sessions[session.session_id] = session
        
        try:
            self.logger.info(f"Starting test session: {session.name}")
            
            # Get the prompt content (this would normally come from prompt repository)
            prompt_content = self._get_prompt_content(config.prompt_template_id)
            if not prompt_content:
                raise ValueError(f"Prompt template not found: {config.prompt_template_id}")
            
            # Execute tests for each iteration
            for iteration in range(config.iterations):
                self.logger.info(f"Executing iteration {iteration + 1}/{config.iterations}")
                
                # Create LLM request
                request = LLMRequest(
                    prompt=prompt_content,
                    model_id="default",  # Will be overridden per provider
                    parameters=config.test_parameters
                )
                
                # Execute across all configured providers
                if config.parallel_execution:
                    responses = await self._execute_parallel(request, config)
                else:
                    responses = await self._execute_sequential(request, config)
                
                # Convert responses to test executions
                for response in responses:
                    execution = self._create_test_execution(response, config, iteration)
                    session.results.append(execution)
                    session.total_executions += 1
                    
                    if execution.success:
                        session.successful_executions += 1
                    else:
                        session.failed_executions += 1
                    
                    session.total_cost += execution.actual_cost
            
            session.status = TestStatus.COMPLETED
            session.completed_at = datetime.now()
            
            self.logger.info(f"Completed test session: {session.name}")
            
        except Exception as e:
            self.logger.error(f"Test session failed: {e}")
            session.status = TestStatus.FAILED
            session.completed_at = datetime.now()
            session.metadata["error"] = str(e)
        
        return session
    
    async def _execute_parallel(self, request: LLMRequest, config: TestConfiguration) -> List[LLMResponse]:
        """Execute request in parallel across providers."""
        # Update request with model configurations
        responses = []
        
        for provider_id in config.provider_configs:
            if provider_id not in self.providers:
                continue
            
            # Create request with provider-specific model
            provider_request = LLMRequest(
                prompt=request.prompt,
                model_id=config.model_configs.get(provider_id, "default"),
                parameters=request.parameters
            )
            
            try:
                response = await self.providers[provider_id].generate(provider_request)
                responses.append(response)
            except Exception as e:
                self.logger.error(f"Provider {provider_id} execution failed: {e}")
                # Create error response
                error_response = LLMResponse(
                    content="",
                    model_id=provider_request.model_id,
                    provider_id=provider_id,
                    input_tokens=0,
                    output_tokens=0,
                    total_tokens=0,
                    response_time=0.0,
                    cost=0.0,
                    success=False,
                    error=str(e)
                )
                responses.append(error_response)
        
        return responses
    
    async def _execute_sequential(self, request: LLMRequest, config: TestConfiguration) -> List[LLMResponse]:
        """Execute request sequentially across providers."""
        responses = []
        
        for provider_id in config.provider_configs:
            if provider_id not in self.providers:
                continue
            
            provider_request = LLMRequest(
                prompt=request.prompt,
                model_id=config.model_configs.get(provider_id, "default"),
                parameters=request.parameters
            )
            
            try:
                response = await self.providers[provider_id].generate(provider_request)
                responses.append(response)
            except Exception as e:
                self.logger.error(f"Provider {provider_id} execution failed: {e}")
                error_response = LLMResponse(
                    content="",
                    model_id=provider_request.model_id,
                    provider_id=provider_id,
                    input_tokens=0,
                    output_tokens=0,
                    total_tokens=0,
                    response_time=0.0,
                    cost=0.0,
                    success=False,
                    error=str(e)
                )
                responses.append(error_response)
        
        return responses
    
    def _create_test_execution(self, response: LLMResponse, config: TestConfiguration, iteration: int) -> TestExecution:
        """Create a TestExecution from an LLMResponse."""
        return TestExecution(
            prompt_template_id=config.prompt_template_id,
            provider_id=response.provider_id,
            model_id=response.model_id,
            test_type=TestType.MULTI_MODEL,
            status=TestStatus.COMPLETED if response.success else TestStatus.FAILED,
            parameters=config.test_parameters,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            actual_cost=response.cost,
            response_time=response.response_time,
            success=response.success,
            response_content=response.content,
            error_message=response.error,
            executed_at=response.timestamp,
            metadata={
                "iteration": iteration,
                "test_config_id": config.test_id,
                "response_metadata": response.metadata
            }
        )
    
    def _get_prompt_content(self, prompt_template_id: str) -> Optional[str]:
        """Get prompt content from template ID (placeholder implementation)."""
        # This would normally query the prompt repository
        # For now, return a sample prompt
        return f"Sample prompt for template {prompt_template_id}. Please respond with a helpful answer."
    
    def get_test_session(self, session_id: str) -> Optional[TestSession]:
        """Get a test session by ID."""
        return self.active_sessions.get(session_id)
    
    def get_active_sessions(self) -> List[TestSession]:
        """Get all active test sessions."""
        return list(self.active_sessions.values())
    
    def cancel_session(self, session_id: str) -> bool:
        """Cancel an active test session."""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            if session.status == TestStatus.RUNNING:
                session.status = TestStatus.CANCELLED
                session.completed_at = datetime.now()
                self.logger.info(f"Cancelled test session: {session.name}")
                return True
        return False
    
    async def run_quick_test(self, prompt: str, provider_ids: List[str] = None) -> List[LLMResponse]:
        """Run a quick test across specified providers."""
        if not provider_ids:
            provider_ids = list(self.providers.keys())
        
        request = LLMRequest(prompt=prompt, model_id="default")
        
        responses = []
        for provider_id in provider_ids:
            if provider_id in self.providers and self.providers[provider_id].is_initialized():
                try:
                    response = await self.providers[provider_id].generate(request)
                    responses.append(response)
                except Exception as e:
                    self.logger.error(f"Quick test failed for {provider_id}: {e}")
        
        return responses
    
    def get_provider_statistics(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all providers."""
        stats = {}
        for provider_id, provider in self.providers.items():
            # This would normally query the database for historical data
            stats[provider_id] = {
                "name": provider.config.name,
                "type": provider.config.provider_type.value,
                "initialized": provider.is_initialized(),
                "total_requests": 0,  # Would come from database
                "successful_requests": 0,
                "failed_requests": 0,
                "average_response_time": 0.0,
                "total_cost": 0.0
            }
        return stats