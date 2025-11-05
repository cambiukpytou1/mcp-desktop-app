"""
Base Data Models and Enums for MCP Admin Application
===================================================

Core data structures and enumerations used throughout the application.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
import uuid


class ServerStatus(Enum):
    """MCP Server status enumeration."""
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    UNKNOWN = "unknown"


class RiskLevel(Enum):
    """Risk level enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class LLMProviderType(Enum):
    """LLM Provider type enumeration."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE_OPENAI = "azure_openai"
    GOOGLE = "google"
    OLLAMA = "ollama"
    LM_STUDIO = "lm_studio"
    CUSTOM = "custom"


class ProviderStatus(Enum):
    """Provider status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    TESTING = "testing"
    CONNECTING = "connecting"


class ErrorType(Enum):
    """LLM error type enumeration."""
    AUTHENTICATION_FAILED = "auth_failed"
    RATE_LIMIT_EXCEEDED = "rate_limit"
    MODEL_UNAVAILABLE = "model_unavailable"
    COST_LIMIT_EXCEEDED = "cost_limit"
    NETWORK_ERROR = "network_error"
    INVALID_REQUEST = "invalid_request"
    PROVIDER_ERROR = "provider_error"
    TIMEOUT = "timeout"


class SecurityEventType(Enum):
    """Security event type enumeration."""
    AUTHENTICATION_SUCCESS = "auth_success"
    AUTHENTICATION_FAILURE = "auth_failure"
    TOOL_EXECUTION = "tool_execution"
    CONFIGURATION_CHANGE = "config_change"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    API_KEY_ACCESS = "api_key_access"
    CREDENTIAL_CREATED = "credential_created"
    CREDENTIAL_UPDATED = "credential_updated"
    CREDENTIAL_DELETED = "credential_deleted"


class TestStatus(Enum):
    """Test execution status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TestType(Enum):
    """Test type enumeration."""
    SINGLE = "single"
    BATCH = "batch"
    AB_TEST = "ab_test"
    MULTI_MODEL = "multi_model"


@dataclass
class ToolParameter:
    """Tool parameter definition."""
    name: str
    type: str
    description: str
    required: bool = False
    default: Optional[Any] = None


@dataclass
class PromptParameter:
    """Prompt template parameter definition."""
    name: str
    type: str
    description: str
    required: bool = True
    default: Optional[str] = None


@dataclass
class UsageStats:
    """Usage statistics for LLM providers."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tokens: int = 0
    average_response_time: float = 0.0
    last_used: Optional[datetime] = None


def generate_id() -> str:
    """Generate a unique identifier."""
    return str(uuid.uuid4())