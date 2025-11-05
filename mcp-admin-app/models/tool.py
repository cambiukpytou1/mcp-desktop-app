"""
Enhanced MCP Tool Data Models
============================

Comprehensive data models for MCP tool management, discovery, and analytics.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from models.base import generate_id


class ToolCategory(Enum):
    """Tool category enumeration."""
    FILE_OPERATIONS = "file_operations"
    WEB_SEARCH = "web_search"
    CODE_ANALYSIS = "code_analysis"
    DATA_PROCESSING = "data_processing"
    API_INTEGRATION = "api_integration"
    SYSTEM_TOOLS = "system_tools"
    COMMUNICATION = "communication"
    PRODUCTIVITY = "productivity"
    SECURITY = "security"
    MONITORING = "monitoring"
    GENERAL = "general"


class ToolStatus(Enum):
    """Tool status enumeration."""
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    DISABLED = "disabled"
    ERROR = "error"
    TESTING = "testing"
    QUARANTINED = "quarantined"


class ExecutionStatus(Enum):
    """Tool execution status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class SecurityLevel(Enum):
    """Security level enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    RESTRICTED = "restricted"


class PermissionType(Enum):
    """Permission type enumeration."""
    READ = "read"
    EXECUTE = "execute"
    CONFIGURE = "configure"
    ADMIN = "admin"


@dataclass
class ValidationRule:
    """Parameter validation rule."""
    rule_type: str  # "regex", "range", "enum", "custom"
    value: Any
    error_message: str = ""


@dataclass
class ToolParameter:
    """Enhanced tool parameter definition."""
    name: str
    type: str
    description: str
    required: bool = False
    default_value: Optional[Any] = None
    validation_rules: List[ValidationRule] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    sensitive: bool = False  # For passwords, API keys, etc.


@dataclass
class ToolMetadata:
    """Tool metadata and classification information."""
    version: str = "1.0.0"
    author: str = ""
    documentation_url: str = ""
    source_url: str = ""
    license: str = ""
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    compatibility: Dict[str, Any] = field(default_factory=dict)
    performance_hints: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResourceUsage:
    """Resource usage metrics."""
    cpu_time: float = 0.0
    memory_mb: float = 0.0
    network_bytes: int = 0
    disk_io_bytes: int = 0
    execution_time: float = 0.0


@dataclass
class ToolPermission:
    """Tool permission configuration."""
    user_id: Optional[str] = None
    role: Optional[str] = None
    permissions: List[PermissionType] = field(default_factory=list)
    rate_limit: int = 0  # requests per minute
    daily_quota: int = 0  # daily execution limit
    allowed_contexts: List[str] = field(default_factory=list)
    restrictions: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolRegistryEntry:
    """Comprehensive tool registry entry."""
    id: str = field(default_factory=generate_id)
    name: str = ""
    description: str = ""
    server_id: str = ""
    category: ToolCategory = ToolCategory.GENERAL
    schema: Dict[str, Any] = field(default_factory=dict)
    parameters: List[ToolParameter] = field(default_factory=list)
    permissions: List[ToolPermission] = field(default_factory=list)
    status: ToolStatus = ToolStatus.AVAILABLE
    metadata: ToolMetadata = field(default_factory=ToolMetadata)
    
    # Analytics fields
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_used: Optional[datetime] = None
    usage_count: int = 0
    average_execution_time: float = 0.0
    success_rate: float = 1.0
    
    # Configuration
    enabled: bool = True
    aliases: List[str] = field(default_factory=list)
    default_parameters: Dict[str, Any] = field(default_factory=dict)
    security_level: SecurityLevel = SecurityLevel.MEDIUM
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "server_id": self.server_id,
            "category": self.category.value,
            "schema": self.schema,
            "parameters": [
                {
                    "name": p.name,
                    "type": p.type,
                    "description": p.description,
                    "required": p.required,
                    "default_value": p.default_value,
                    "validation_rules": [
                        {
                            "rule_type": r.rule_type,
                            "value": r.value,
                            "error_message": r.error_message
                        } for r in p.validation_rules
                    ],
                    "examples": p.examples,
                    "sensitive": p.sensitive
                } for p in self.parameters
            ],
            "permissions": [
                {
                    "user_id": perm.user_id,
                    "role": perm.role,
                    "permissions": [p.value for p in perm.permissions],
                    "rate_limit": perm.rate_limit,
                    "daily_quota": perm.daily_quota,
                    "allowed_contexts": perm.allowed_contexts,
                    "restrictions": perm.restrictions
                } for perm in self.permissions
            ],
            "status": self.status.value,
            "metadata": {
                "version": self.metadata.version,
                "author": self.metadata.author,
                "documentation_url": self.metadata.documentation_url,
                "source_url": self.metadata.source_url,
                "license": self.metadata.license,
                "tags": self.metadata.tags,
                "dependencies": self.metadata.dependencies,
                "compatibility": self.metadata.compatibility,
                "performance_hints": self.metadata.performance_hints
            },
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "usage_count": self.usage_count,
            "average_execution_time": self.average_execution_time,
            "success_rate": self.success_rate,
            "enabled": self.enabled,
            "aliases": self.aliases,
            "default_parameters": self.default_parameters,
            "security_level": self.security_level.value
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ToolRegistryEntry':
        """Create instance from dictionary."""
        entry = cls()
        entry.id = data.get("id", generate_id())
        entry.name = data.get("name", "")
        entry.description = data.get("description", "")
        entry.server_id = data.get("server_id", "")
        entry.category = ToolCategory(data.get("category", "general"))
        entry.schema = data.get("schema", {})
        
        # Parse parameters
        entry.parameters = []
        for p_data in data.get("parameters", []):
            param = ToolParameter(
                name=p_data.get("name", ""),
                type=p_data.get("type", "string"),
                description=p_data.get("description", ""),
                required=p_data.get("required", False),
                default_value=p_data.get("default_value"),
                examples=p_data.get("examples", []),
                sensitive=p_data.get("sensitive", False)
            )
            # Parse validation rules
            for r_data in p_data.get("validation_rules", []):
                rule = ValidationRule(
                    rule_type=r_data.get("rule_type", ""),
                    value=r_data.get("value"),
                    error_message=r_data.get("error_message", "")
                )
                param.validation_rules.append(rule)
            entry.parameters.append(param)
        
        # Parse permissions
        entry.permissions = []
        for perm_data in data.get("permissions", []):
            permission = ToolPermission(
                user_id=perm_data.get("user_id"),
                role=perm_data.get("role"),
                permissions=[PermissionType(p) for p in perm_data.get("permissions", [])],
                rate_limit=perm_data.get("rate_limit", 0),
                daily_quota=perm_data.get("daily_quota", 0),
                allowed_contexts=perm_data.get("allowed_contexts", []),
                restrictions=perm_data.get("restrictions", {})
            )
            entry.permissions.append(permission)
        
        entry.status = ToolStatus(data.get("status", "available"))
        
        # Parse metadata
        metadata_data = data.get("metadata", {})
        entry.metadata = ToolMetadata(
            version=metadata_data.get("version", "1.0.0"),
            author=metadata_data.get("author", ""),
            documentation_url=metadata_data.get("documentation_url", ""),
            source_url=metadata_data.get("source_url", ""),
            license=metadata_data.get("license", ""),
            tags=metadata_data.get("tags", []),
            dependencies=metadata_data.get("dependencies", []),
            compatibility=metadata_data.get("compatibility", {}),
            performance_hints=metadata_data.get("performance_hints", {})
        )
        
        entry.created_at = datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now()
        entry.updated_at = datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.now()
        entry.last_used = datetime.fromisoformat(data["last_used"]) if data.get("last_used") else None
        entry.usage_count = data.get("usage_count", 0)
        entry.average_execution_time = data.get("average_execution_time", 0.0)
        entry.success_rate = data.get("success_rate", 1.0)
        entry.enabled = data.get("enabled", True)
        entry.aliases = data.get("aliases", [])
        entry.default_parameters = data.get("default_parameters", {})
        entry.security_level = SecurityLevel(data.get("security_level", "medium"))
        
        return entry


@dataclass
class ToolExecution:
    """Tool execution record."""
    id: str = field(default_factory=generate_id)
    tool_id: str = ""
    user_id: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None
    status: ExecutionStatus = ExecutionStatus.PENDING
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    execution_time: Optional[float] = None
    error_message: Optional[str] = None
    resource_usage: ResourceUsage = field(default_factory=ResourceUsage)
    sandbox_id: Optional[str] = None
    workflow_id: Optional[str] = None
    parent_execution_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "tool_id": self.tool_id,
            "user_id": self.user_id,
            "parameters": self.parameters,
            "result": self.result,
            "status": self.status.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "execution_time": self.execution_time,
            "error_message": self.error_message,
            "resource_usage": {
                "cpu_time": self.resource_usage.cpu_time,
                "memory_mb": self.resource_usage.memory_mb,
                "network_bytes": self.resource_usage.network_bytes,
                "disk_io_bytes": self.resource_usage.disk_io_bytes,
                "execution_time": self.resource_usage.execution_time
            },
            "sandbox_id": self.sandbox_id,
            "workflow_id": self.workflow_id,
            "parent_execution_id": self.parent_execution_id
        }


@dataclass
class ToolFilters:
    """Tool registry search and filter criteria."""
    name: Optional[str] = None
    category: Optional[ToolCategory] = None
    server_id: Optional[str] = None
    status: Optional[ToolStatus] = None
    enabled: Optional[bool] = None
    tags: List[str] = field(default_factory=list)
    security_level: Optional[SecurityLevel] = None
    has_permissions: Optional[bool] = None
    min_success_rate: Optional[float] = None
    max_execution_time: Optional[float] = None
    last_used_after: Optional[datetime] = None
    last_used_before: Optional[datetime] = None


@dataclass
class DiscoveredTool:
    """Tool discovered from MCP server."""
    name: str
    description: str
    schema: Dict[str, Any]
    server_id: str
    discovered_at: datetime = field(default_factory=datetime.now)
    classification_confidence: float = 0.0
    suggested_category: Optional[ToolCategory] = None
    metadata_extracted: Dict[str, Any] = field(default_factory=dict)