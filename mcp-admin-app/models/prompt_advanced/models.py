"""
Advanced Prompt Management Models
=================================

Data models for advanced prompt management features including validation,
serialization, and comprehensive metadata support.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
import json
import uuid
from ..base import generate_id


class PromptStatus(Enum):
    """Prompt status enumeration."""
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"


class PromptCategory(Enum):
    """Prompt category enumeration."""
    SUMMARIZATION = "summarization"
    TRANSLATION = "translation"
    EXTRACTION = "extraction"
    REASONING = "reasoning"
    CREATIVE = "creative"
    ANALYSIS = "analysis"
    CLASSIFICATION = "classification"
    GENERATION = "generation"
    CONVERSATION = "conversation"
    CUSTOM = "custom"


class VersionStatus(Enum):
    """Version status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    MERGED = "merged"
    ABANDONED = "abandoned"


class BranchType(Enum):
    """Branch type enumeration."""
    MAIN = "main"
    FEATURE = "feature"
    EXPERIMENT = "experiment"
    HOTFIX = "hotfix"


class ValidationError(Exception):
    """Custom validation error for prompt models."""
    pass


@dataclass
class PromptMetadata:
    """Prompt metadata information with validation and serialization."""
    model: str
    temperature: float = 0.7
    max_tokens: int = 1000
    tags: List[str] = field(default_factory=list)
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    author: str = ""
    description: str = ""
    intent_category: PromptCategory = PromptCategory.CUSTOM
    status: PromptStatus = PromptStatus.DRAFT
    domain: str = ""
    tone: str = ""
    persona: str = ""
    objective: str = ""
    
    def validate(self) -> bool:
        """Validate metadata fields."""
        if not self.model or not isinstance(self.model, str):
            raise ValidationError("Model must be a non-empty string")
        
        if not 0.0 <= self.temperature <= 2.0:
            raise ValidationError("Temperature must be between 0.0 and 2.0")
        
        if not 1 <= self.max_tokens <= 100000:
            raise ValidationError("Max tokens must be between 1 and 100000")
        
        if not isinstance(self.tags, list):
            raise ValidationError("Tags must be a list")
        
        if not isinstance(self.custom_fields, dict):
            raise ValidationError("Custom fields must be a dictionary")
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "tags": self.tags,
            "custom_fields": self.custom_fields,
            "author": self.author,
            "description": self.description,
            "intent_category": self.intent_category.value,
            "status": self.status.value,
            "domain": self.domain,
            "tone": self.tone,
            "persona": self.persona,
            "objective": self.objective
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PromptMetadata':
        """Create instance from dictionary."""
        metadata = cls(
            model=data.get("model", ""),
            temperature=data.get("temperature", 0.7),
            max_tokens=data.get("max_tokens", 1000),
            tags=data.get("tags", []),
            custom_fields=data.get("custom_fields", {}),
            author=data.get("author", ""),
            description=data.get("description", ""),
            intent_category=PromptCategory(data.get("intent_category", "custom")),
            status=PromptStatus(data.get("status", "draft")),
            domain=data.get("domain", ""),
            tone=data.get("tone", ""),
            persona=data.get("persona", ""),
            objective=data.get("objective", "")
        )
        metadata.validate()
        return metadata


@dataclass
class VersionInfo:
    """Version information for prompts."""
    current_version: str
    total_versions: int = 1
    last_modified_by: str = ""
    last_modified_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "current_version": self.current_version,
            "total_versions": self.total_versions,
            "last_modified_by": self.last_modified_by,
            "last_modified_at": self.last_modified_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VersionInfo':
        """Create instance from dictionary."""
        return cls(
            current_version=data.get("current_version", "1.0.0"),
            total_versions=data.get("total_versions", 1),
            last_modified_by=data.get("last_modified_by", ""),
            last_modified_at=datetime.fromisoformat(data["last_modified_at"]) if "last_modified_at" in data else datetime.now()
        )


@dataclass
class PerformanceMetrics:
    """Performance metrics for prompt versions."""
    average_score: float = 0.0
    total_executions: int = 0
    success_rate: float = 0.0
    average_tokens: int = 0
    average_cost: float = 0.0
    average_response_time: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "average_score": self.average_score,
            "total_executions": self.total_executions,
            "success_rate": self.success_rate,
            "average_tokens": self.average_tokens,
            "average_cost": self.average_cost,
            "average_response_time": self.average_response_time
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PerformanceMetrics':
        """Create instance from dictionary."""
        return cls(
            average_score=data.get("average_score", 0.0),
            total_executions=data.get("total_executions", 0),
            success_rate=data.get("success_rate", 0.0),
            average_tokens=data.get("average_tokens", 0),
            average_cost=data.get("average_cost", 0.0),
            average_response_time=data.get("average_response_time", 0.0)
        )


@dataclass
class PromptVersion:
    """Prompt version information with comprehensive tracking."""
    version_id: str = field(default_factory=generate_id)
    prompt_id: str = ""
    content: str = ""
    metadata_snapshot: Optional[PromptMetadata] = None
    parent_version: Optional[str] = None
    branch_name: str = "main"
    branch_type: BranchType = BranchType.MAIN
    commit_message: str = ""
    status: VersionStatus = VersionStatus.ACTIVE
    performance_metrics: Optional[PerformanceMetrics] = None
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    
    def validate(self) -> bool:
        """Validate version data."""
        if not self.version_id:
            raise ValidationError("Version ID is required")
        
        if not self.prompt_id:
            raise ValidationError("Prompt ID is required")
        
        if not self.content:
            raise ValidationError("Content is required")
        
        if self.metadata_snapshot:
            self.metadata_snapshot.validate()
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "version_id": self.version_id,
            "prompt_id": self.prompt_id,
            "content": self.content,
            "metadata_snapshot": self.metadata_snapshot.to_dict() if self.metadata_snapshot else None,
            "parent_version": self.parent_version,
            "branch_name": self.branch_name,
            "branch_type": self.branch_type.value,
            "commit_message": self.commit_message,
            "status": self.status.value,
            "performance_metrics": self.performance_metrics.to_dict() if self.performance_metrics else None,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PromptVersion':
        """Create instance from dictionary."""
        version = cls(
            version_id=data.get("version_id", generate_id()),
            prompt_id=data.get("prompt_id", ""),
            content=data.get("content", ""),
            parent_version=data.get("parent_version"),
            branch_name=data.get("branch_name", "main"),
            branch_type=BranchType(data.get("branch_type", "main")),
            commit_message=data.get("commit_message", ""),
            status=VersionStatus(data.get("status", "active")),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            created_by=data.get("created_by", "")
        )
        
        if data.get("metadata_snapshot"):
            version.metadata_snapshot = PromptMetadata.from_dict(data["metadata_snapshot"])
        
        if data.get("performance_metrics"):
            version.performance_metrics = PerformanceMetrics.from_dict(data["performance_metrics"])
        
        version.validate()
        return version


@dataclass
class Prompt:
    """Advanced prompt model with comprehensive features."""
    id: str = field(default_factory=generate_id)
    name: str = ""
    content: str = ""
    metadata: Optional[PromptMetadata] = None
    version_info: Optional[VersionInfo] = None
    folder_path: str = ""
    project_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Initialize default values after creation."""
        if self.metadata is None:
            self.metadata = PromptMetadata(model="gpt-3.5-turbo")
        if self.version_info is None:
            self.version_info = VersionInfo(current_version="1.0.0")
    
    def validate(self) -> bool:
        """Validate prompt data."""
        if not self.id:
            raise ValidationError("Prompt ID is required")
        
        if not self.name or not isinstance(self.name, str):
            raise ValidationError("Prompt name must be a non-empty string")
        
        if not self.content or not isinstance(self.content, str):
            raise ValidationError("Prompt content must be a non-empty string")
        
        if self.metadata:
            self.metadata.validate()
        
        if len(self.name) > 255:
            raise ValidationError("Prompt name must be 255 characters or less")
        
        if len(self.content) > 100000:
            raise ValidationError("Prompt content must be 100,000 characters or less")
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "content": self.content,
            "metadata": self.metadata.to_dict() if self.metadata else None,
            "version_info": self.version_info.to_dict() if self.version_info else None,
            "folder_path": self.folder_path,
            "project_id": self.project_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Prompt':
        """Create instance from dictionary."""
        prompt = cls(
            id=data.get("id", generate_id()),
            name=data.get("name", ""),
            content=data.get("content", ""),
            folder_path=data.get("folder_path", ""),
            project_id=data.get("project_id"),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.now()
        )
        
        if data.get("metadata"):
            prompt.metadata = PromptMetadata.from_dict(data["metadata"])
        
        if data.get("version_info"):
            prompt.version_info = VersionInfo.from_dict(data["version_info"])
        
        prompt.validate()
        return prompt
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Prompt':
        """Create instance from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)


@dataclass
class PromptBranch:
    """Prompt branch for version control."""
    branch_id: str = field(default_factory=generate_id)
    prompt_id: str = ""
    name: str = ""
    base_version: str = ""
    head_version: str = ""
    branch_type: BranchType = BranchType.FEATURE
    is_active: bool = True
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    merged_at: Optional[datetime] = None
    
    def validate(self) -> bool:
        """Validate branch data."""
        if not self.branch_id:
            raise ValidationError("Branch ID is required")
        
        if not self.prompt_id:
            raise ValidationError("Prompt ID is required")
        
        if not self.name:
            raise ValidationError("Branch name is required")
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "branch_id": self.branch_id,
            "prompt_id": self.prompt_id,
            "name": self.name,
            "base_version": self.base_version,
            "head_version": self.head_version,
            "branch_type": self.branch_type.value,
            "is_active": self.is_active,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "merged_at": self.merged_at.isoformat() if self.merged_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PromptBranch':
        """Create instance from dictionary."""
        branch = cls(
            branch_id=data.get("branch_id", generate_id()),
            prompt_id=data.get("prompt_id", ""),
            name=data.get("name", ""),
            base_version=data.get("base_version", ""),
            head_version=data.get("head_version", ""),
            branch_type=BranchType(data.get("branch_type", "feature")),
            is_active=data.get("is_active", True),
            created_by=data.get("created_by", ""),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            merged_at=datetime.fromisoformat(data["merged_at"]) if data.get("merged_at") else None
        )
        branch.validate()
        return branch


@dataclass
class PromptProject:
    """Prompt project for organization with enhanced features."""
    id: str = field(default_factory=generate_id)
    name: str = ""
    description: str = ""
    prompts: List[str] = field(default_factory=list)
    settings: Dict[str, Any] = field(default_factory=dict)
    permissions: Dict[str, List[str]] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    
    def validate(self) -> bool:
        """Validate project data."""
        if not self.id:
            raise ValidationError("Project ID is required")
        
        if not self.name or not isinstance(self.name, str):
            raise ValidationError("Project name must be a non-empty string")
        
        if not isinstance(self.prompts, list):
            raise ValidationError("Prompts must be a list")
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "prompts": self.prompts,
            "settings": self.settings,
            "permissions": self.permissions,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "created_by": self.created_by
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PromptProject':
        """Create instance from dictionary."""
        project = cls(
            id=data.get("id", generate_id()),
            name=data.get("name", ""),
            description=data.get("description", ""),
            prompts=data.get("prompts", []),
            settings=data.get("settings", {}),
            permissions=data.get("permissions", {}),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.now(),
            created_by=data.get("created_by", "")
        )
        project.validate()
        return project


@dataclass
class TokenUsage:
    """Token usage information."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TokenUsage':
        """Create instance from dictionary."""
        return cls(
            prompt_tokens=data.get("prompt_tokens", 0),
            completion_tokens=data.get("completion_tokens", 0),
            total_tokens=data.get("total_tokens", 0)
        )


@dataclass
class ScoringRubric:
    """Scoring rubric for evaluations."""
    name: str = ""
    criteria: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    weights: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "criteria": self.criteria,
            "weights": self.weights
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScoringRubric':
        """Create instance from dictionary."""
        return cls(
            name=data.get("name", ""),
            criteria=data.get("criteria", {}),
            weights=data.get("weights", {})
        )


@dataclass
class CostSummary:
    """Cost summary for evaluations."""
    total_cost: float = 0.0
    cost_per_model: Dict[str, float] = field(default_factory=dict)
    token_costs: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "total_cost": self.total_cost,
            "cost_per_model": self.cost_per_model,
            "token_costs": self.token_costs
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CostSummary':
        """Create instance from dictionary."""
        return cls(
            total_cost=data.get("total_cost", 0.0),
            cost_per_model=data.get("cost_per_model", {}),
            token_costs=data.get("token_costs", {})
        )


@dataclass
class EvaluationResult:
    """Comprehensive evaluation result model."""
    result_id: str = field(default_factory=generate_id)
    prompt_version_id: str = ""
    model: str = ""
    input_variables: Dict[str, Any] = field(default_factory=dict)
    output: str = ""
    scores: Dict[str, float] = field(default_factory=dict)
    token_usage: Optional[TokenUsage] = None
    execution_time: float = 0.0
    cost: float = 0.0
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def validate(self) -> bool:
        """Validate evaluation result data."""
        if not self.result_id:
            raise ValidationError("Result ID is required")
        
        if not self.prompt_version_id:
            raise ValidationError("Prompt version ID is required")
        
        if not self.model:
            raise ValidationError("Model is required")
        
        if self.execution_time < 0:
            raise ValidationError("Execution time cannot be negative")
        
        if self.cost < 0:
            raise ValidationError("Cost cannot be negative")
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "result_id": self.result_id,
            "prompt_version_id": self.prompt_version_id,
            "model": self.model,
            "input_variables": self.input_variables,
            "output": self.output,
            "scores": self.scores,
            "token_usage": self.token_usage.to_dict() if self.token_usage else None,
            "execution_time": self.execution_time,
            "cost": self.cost,
            "error": self.error,
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EvaluationResult':
        """Create instance from dictionary."""
        result = cls(
            result_id=data.get("result_id", generate_id()),
            prompt_version_id=data.get("prompt_version_id", ""),
            model=data.get("model", ""),
            input_variables=data.get("input_variables", {}),
            output=data.get("output", ""),
            scores=data.get("scores", {}),
            execution_time=data.get("execution_time", 0.0),
            cost=data.get("cost", 0.0),
            error=data.get("error"),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now()
        )
        
        if data.get("token_usage"):
            result.token_usage = TokenUsage.from_dict(data["token_usage"])
        
        result.validate()
        return result


@dataclass
class EvaluationRun:
    """Evaluation run containing multiple results."""
    run_id: str = field(default_factory=generate_id)
    prompt_version_id: str = ""
    test_dataset: str = ""
    models_tested: List[str] = field(default_factory=list)
    scoring_rubric: Optional[ScoringRubric] = None
    results: List[EvaluationResult] = field(default_factory=list)
    cost_summary: Optional[CostSummary] = None
    status: str = "pending"
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    def validate(self) -> bool:
        """Validate evaluation run data."""
        if not self.run_id:
            raise ValidationError("Run ID is required")
        
        if not self.prompt_version_id:
            raise ValidationError("Prompt version ID is required")
        
        if not isinstance(self.models_tested, list):
            raise ValidationError("Models tested must be a list")
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "run_id": self.run_id,
            "prompt_version_id": self.prompt_version_id,
            "test_dataset": self.test_dataset,
            "models_tested": self.models_tested,
            "scoring_rubric": self.scoring_rubric.to_dict() if self.scoring_rubric else None,
            "results": [result.to_dict() for result in self.results],
            "cost_summary": self.cost_summary.to_dict() if self.cost_summary else None,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EvaluationRun':
        """Create instance from dictionary."""
        run = cls(
            run_id=data.get("run_id", generate_id()),
            prompt_version_id=data.get("prompt_version_id", ""),
            test_dataset=data.get("test_dataset", ""),
            models_tested=data.get("models_tested", []),
            status=data.get("status", "pending"),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None
        )
        
        if data.get("scoring_rubric"):
            run.scoring_rubric = ScoringRubric.from_dict(data["scoring_rubric"])
        
        if data.get("results"):
            run.results = [EvaluationResult.from_dict(result) for result in data["results"]]
        
        if data.get("cost_summary"):
            run.cost_summary = CostSummary.from_dict(data["cost_summary"])
        
        run.validate()
        return run