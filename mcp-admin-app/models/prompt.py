"""
Prompt Template Data Models
===========================

Data models for prompt template management and versioning.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from .base import PromptParameter, generate_id


@dataclass
class PromptTemplate:
    """Prompt template definition with versioning support."""
    id: str = field(default_factory=generate_id)
    name: str = ""
    description: str = ""
    content: str = ""
    version: int = 1
    status: str = "draft"  # draft, active, archived
    target_tools: List[str] = field(default_factory=list)
    parameters: List[PromptParameter] = field(default_factory=list)
    created_by: str = "system"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
    usage_count: int = 0
    last_used: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "content": self.content,
            "version": self.version,
            "status": self.status,
            "target_tools": self.target_tools,
            "parameters": [
                {
                    "name": p.name,
                    "type": p.type,
                    "description": p.description,
                    "required": p.required,
                    "default": p.default
                } for p in self.parameters
            ],
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "tags": self.tags,
            "usage_count": self.usage_count,
            "last_used": self.last_used.isoformat() if self.last_used else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PromptTemplate':
        """Create instance from dictionary."""
        template = cls()
        template.id = data.get("id", generate_id())
        template.name = data.get("name", "")
        template.description = data.get("description", "")
        template.content = data.get("content", "")
        template.version = data.get("version", 1)
        template.status = data.get("status", "draft")
        template.target_tools = data.get("target_tools", [])
        
        # Convert parameter dictionaries to PromptParameter objects
        param_data = data.get("parameters", [])
        template.parameters = [
            PromptParameter(
                name=p["name"],
                type=p["type"],
                description=p["description"],
                required=p.get("required", True),
                default=p.get("default")
            ) for p in param_data
        ]
        
        template.created_by = data.get("created_by", "system")
        template.created_at = datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now()
        template.updated_at = datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.now()
        template.tags = data.get("tags", [])
        template.usage_count = data.get("usage_count", 0)
        template.last_used = datetime.fromisoformat(data["last_used"]) if data.get("last_used") else None
        
        return template


@dataclass
class TemplateVersion:
    """Template version history entry."""
    version: int
    content: str
    created_at: datetime
    created_by: str
    change_notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "version": self.version,
            "content": self.content,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
            "change_notes": self.change_notes
        }


@dataclass
class TestResult:
    """Result of prompt template testing."""
    success: bool
    output: str
    error: Optional[str] = None
    execution_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "execution_time": self.execution_time,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class ExecutionResult:
    """Result of prompt template execution."""
    template_id: str
    parameters: Dict[str, Any]
    result: TestResult
    user: str = "system"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "template_id": self.template_id,
            "parameters": self.parameters,
            "result": self.result.to_dict(),
            "user": self.user
        }