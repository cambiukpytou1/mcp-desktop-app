"""
Enhanced LLM Provider Data Models
=================================

Comprehensive data models for LLM provider management, testing, analytics, and security.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from .base import (
    LLMProviderType, ProviderStatus, UsageStats, ErrorType, 
    TestStatus, TestType, SecurityEventType, RiskLevel, generate_id
)


# Legacy LLMProvider class - kept for backward compatibility
# New implementations should use LLMProviderConfig
@dataclass
class LLMProvider:
    """Legacy LLM Provider configuration - use LLMProviderConfig for new implementations."""
    id: str = field(default_factory=generate_id)
    name: str = ""
    provider_type: LLMProviderType = LLMProviderType.CUSTOM
    api_endpoint: str = ""
    credentials: Dict[str, str] = field(default_factory=dict)  # Deprecated - use EncryptedCredential
    usage_stats: UsageStats = field(default_factory=UsageStats)
    status: ProviderStatus = ProviderStatus.INACTIVE
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    description: str = ""
    max_tokens: Optional[int] = None
    rate_limit: Optional[int] = None
    priority: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "provider_type": self.provider_type.value,
            "api_endpoint": self.api_endpoint,
            "credentials": self.credentials,  # Note: Should be encrypted in production
            "usage_stats": {
                "total_requests": self.usage_stats.total_requests,
                "successful_requests": self.usage_stats.successful_requests,
                "failed_requests": self.usage_stats.failed_requests,
                "total_tokens": self.usage_stats.total_tokens,
                "average_response_time": self.usage_stats.average_response_time,
                "last_used": self.usage_stats.last_used.isoformat() if self.usage_stats.last_used else None
            },
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "description": self.description,
            "max_tokens": self.max_tokens,
            "rate_limit": self.rate_limit,
            "priority": self.priority
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LLMProvider':
        """Create instance from dictionary."""
        provider = cls()
        provider.id = data.get("id", generate_id())
        provider.name = data.get("name", "")
        provider.provider_type = LLMProviderType(data.get("provider_type", "custom"))
        provider.api_endpoint = data.get("api_endpoint", "")
        provider.credentials = data.get("credentials", {})
        
        # Parse usage stats
        stats_data = data.get("usage_stats", {})
        provider.usage_stats = UsageStats(
            total_requests=stats_data.get("total_requests", 0),
            successful_requests=stats_data.get("successful_requests", 0),
            failed_requests=stats_data.get("failed_requests", 0),
            total_tokens=stats_data.get("total_tokens", 0),
            average_response_time=stats_data.get("average_response_time", 0.0),
            last_used=datetime.fromisoformat(stats_data["last_used"]) if stats_data.get("last_used") else None
        )
        
        provider.status = ProviderStatus(data.get("status", "inactive"))
        provider.created_at = datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now()
        provider.updated_at = datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.now()
        provider.description = data.get("description", "")
        provider.max_tokens = data.get("max_tokens")
        provider.rate_limit = data.get("rate_limit")
        provider.priority = data.get("priority", 1)
        
        return provider


@dataclass
class ConnectionResult:
    """Result of LLM provider connection test."""
    success: bool
    response_time: float = 0.0
    error: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "success": self.success,
            "response_time": self.response_time,
            "error": self.error,
            "details": self.details,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class ModelConfig:
    """Configuration for a specific LLM model."""
    model_id: str
    display_name: str
    max_tokens: int
    input_cost_per_token: float
    output_cost_per_token: float
    supports_streaming: bool = False
    context_window: int = 4096
    tokenizer_type: str = "default"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "model_id": self.model_id,
            "display_name": self.display_name,
            "max_tokens": self.max_tokens,
            "input_cost_per_token": self.input_cost_per_token,
            "output_cost_per_token": self.output_cost_per_token,
            "supports_streaming": self.supports_streaming,
            "context_window": self.context_window,
            "tokenizer_type": self.tokenizer_type
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelConfig':
        """Create instance from dictionary."""
        return cls(
            model_id=data["model_id"],
            display_name=data["display_name"],
            max_tokens=data["max_tokens"],
            input_cost_per_token=data["input_cost_per_token"],
            output_cost_per_token=data["output_cost_per_token"],
            supports_streaming=data.get("supports_streaming", False),
            context_window=data.get("context_window", 4096),
            tokenizer_type=data.get("tokenizer_type", "default")
        )


@dataclass
class EncryptedCredential:
    """Encrypted credential storage for LLM providers."""
    provider_id: str
    credential_type: str  # API_KEY, TOKEN, CERTIFICATE
    encrypted_value: bytes
    encryption_method: str
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "provider_id": self.provider_id,
            "credential_type": self.credential_type,
            "encrypted_value": self.encrypted_value.hex(),  # Convert bytes to hex string
            "encryption_method": self.encryption_method,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "last_used": self.last_used.isoformat() if self.last_used else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EncryptedCredential':
        """Create instance from dictionary."""
        return cls(
            provider_id=data["provider_id"],
            credential_type=data["credential_type"],
            encrypted_value=bytes.fromhex(data["encrypted_value"]),
            encryption_method=data["encryption_method"],
            created_at=datetime.fromisoformat(data["created_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
            last_used=datetime.fromisoformat(data["last_used"]) if data.get("last_used") else None
        )


@dataclass
class LLMProviderConfig:
    """Enhanced LLM Provider configuration with security and analytics."""
    id: str = field(default_factory=generate_id)
    name: str = ""
    provider_type: LLMProviderType = LLMProviderType.CUSTOM
    endpoint_url: Optional[str] = None
    models: List[ModelConfig] = field(default_factory=list)
    settings: Dict[str, Any] = field(default_factory=dict)
    is_local: bool = False
    status: ProviderStatus = ProviderStatus.INACTIVE
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    description: str = ""
    priority: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "provider_type": self.provider_type.value,
            "endpoint_url": self.endpoint_url,
            "models": [model.to_dict() for model in self.models],
            "settings": self.settings,
            "is_local": self.is_local,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "description": self.description,
            "priority": self.priority
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LLMProviderConfig':
        """Create instance from dictionary."""
        provider = cls()
        provider.id = data.get("id", generate_id())
        provider.name = data.get("name", "")
        provider.provider_type = LLMProviderType(data.get("provider_type", "custom"))
        provider.endpoint_url = data.get("endpoint_url")
        provider.models = [ModelConfig.from_dict(model_data) for model_data in data.get("models", [])]
        provider.settings = data.get("settings", {})
        provider.is_local = data.get("is_local", False)
        provider.status = ProviderStatus(data.get("status", "inactive"))
        provider.created_at = datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now()
        provider.updated_at = datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.now()
        provider.description = data.get("description", "")
        provider.priority = data.get("priority", 1)
        return provider


@dataclass
class TokenEstimate:
    """Token count estimation with confidence metrics."""
    input_tokens: int
    estimated_output_tokens: int
    confidence_level: float  # 0.0 to 1.0
    tokenizer_used: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "input_tokens": self.input_tokens,
            "estimated_output_tokens": self.estimated_output_tokens,
            "confidence_level": self.confidence_level,
            "tokenizer_used": self.tokenizer_used
        }


@dataclass
class CostEstimate:
    """Cost estimation for LLM usage."""
    input_cost: float
    estimated_output_cost: float
    total_estimated_cost: float
    confidence_level: float
    currency: str = "USD"
    pricing_date: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "input_cost": self.input_cost,
            "estimated_output_cost": self.estimated_output_cost,
            "total_estimated_cost": self.total_estimated_cost,
            "confidence_level": self.confidence_level,
            "currency": self.currency,
            "pricing_date": self.pricing_date.isoformat()
        }


@dataclass
class TestExecution:
    """Comprehensive test execution record."""
    id: str = field(default_factory=generate_id)
    prompt_template_id: str = ""
    provider_id: str = ""
    model_id: str = ""
    test_type: TestType = TestType.SINGLE
    status: TestStatus = TestStatus.PENDING
    parameters: Dict[str, Any] = field(default_factory=dict)
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost: float = 0.0
    actual_cost: float = 0.0
    response_time: float = 0.0
    success: bool = False
    response_content: str = ""
    error_message: Optional[str] = None
    quality_score: Optional[float] = None
    executed_at: datetime = field(default_factory=datetime.now)
    executed_by: str = "system"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "prompt_template_id": self.prompt_template_id,
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "test_type": self.test_type.value,
            "status": self.status.value,
            "parameters": self.parameters,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "estimated_cost": self.estimated_cost,
            "actual_cost": self.actual_cost,
            "response_time": self.response_time,
            "success": self.success,
            "response_content": self.response_content,
            "error_message": self.error_message,
            "quality_score": self.quality_score,
            "executed_at": self.executed_at.isoformat(),
            "executed_by": self.executed_by,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TestExecution':
        """Create instance from dictionary."""
        execution = cls()
        execution.id = data.get("id", generate_id())
        execution.prompt_template_id = data.get("prompt_template_id", "")
        execution.provider_id = data.get("provider_id", "")
        execution.model_id = data.get("model_id", "")
        execution.test_type = TestType(data.get("test_type", "single"))
        execution.status = TestStatus(data.get("status", "pending"))
        execution.parameters = data.get("parameters", {})
        execution.input_tokens = data.get("input_tokens", 0)
        execution.output_tokens = data.get("output_tokens", 0)
        execution.estimated_cost = data.get("estimated_cost", 0.0)
        execution.actual_cost = data.get("actual_cost", 0.0)
        execution.response_time = data.get("response_time", 0.0)
        execution.success = data.get("success", False)
        execution.response_content = data.get("response_content", "")
        execution.error_message = data.get("error_message")
        execution.quality_score = data.get("quality_score")
        execution.executed_at = datetime.fromisoformat(data["executed_at"]) if "executed_at" in data else datetime.now()
        execution.executed_by = data.get("executed_by", "system")
        execution.metadata = data.get("metadata", {})
        return execution


@dataclass
class UsageMetrics:
    """Comprehensive usage metrics for analytics."""
    provider_id: str
    model_id: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost: float = 0.0
    average_response_time: float = 0.0
    average_quality_score: float = 0.0
    time_period_start: datetime = field(default_factory=datetime.now)
    time_period_end: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_cost": self.total_cost,
            "average_response_time": self.average_response_time,
            "average_quality_score": self.average_quality_score,
            "time_period_start": self.time_period_start.isoformat(),
            "time_period_end": self.time_period_end.isoformat(),
            "last_updated": self.last_updated.isoformat()
        }


@dataclass
class LLMError:
    """Comprehensive LLM error information."""
    error_code: str
    error_type: ErrorType
    message: str
    provider_id: str
    model_id: Optional[str] = None
    retry_after: Optional[int] = None
    suggested_action: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "error_code": self.error_code,
            "error_type": self.error_type.value,
            "message": self.message,
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "retry_after": self.retry_after,
            "suggested_action": self.suggested_action,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class SecurityAuditEvent:
    """Security audit event for LLM operations."""
    event_type: SecurityEventType
    user_id: str
    description: str
    id: str = field(default_factory=generate_id)
    provider_id: Optional[str] = None
    risk_level: RiskLevel = RiskLevel.LOW
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "event_type": self.event_type.value,
            "provider_id": self.provider_id,
            "user_id": self.user_id,
            "description": self.description,
            "risk_level": self.risk_level.value,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class LLMUsageRecord:
    """Individual LLM usage record with enhanced tracking."""
    id: str = field(default_factory=generate_id)
    timestamp: datetime = field(default_factory=datetime.now)
    provider_id: str = ""
    model_id: str = ""
    tool_id: Optional[str] = None
    prompt_template_id: Optional[str] = None
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost: float = 0.0
    actual_cost: float = 0.0
    response_time_ms: int = 0
    success: bool = True
    error: Optional[str] = None
    error_type: Optional[ErrorType] = None
    quality_score: Optional[float] = None
    user: str = "system"
    session_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "tool_id": self.tool_id,
            "prompt_template_id": self.prompt_template_id,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "estimated_cost": self.estimated_cost,
            "actual_cost": self.actual_cost,
            "response_time_ms": self.response_time_ms,
            "success": self.success,
            "error": self.error,
            "error_type": self.error_type.value if self.error_type else None,
            "quality_score": self.quality_score,
            "user": self.user,
            "session_id": self.session_id
        }