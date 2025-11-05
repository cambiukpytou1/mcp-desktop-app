"""
MCP Server Data Models
=====================

Data models for MCP server management and configuration.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from .base import ServerStatus, generate_id


@dataclass
class MCPServer:
    """MCP Server configuration and status."""
    id: str = field(default_factory=generate_id)
    name: str = ""
    command: str = ""
    args: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)
    status: ServerStatus = ServerStatus.UNKNOWN
    created_at: datetime = field(default_factory=datetime.now)
    last_seen: Optional[datetime] = None
    description: str = ""
    auto_start: bool = False
    health_check_url: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "command": self.command,
            "args": self.args,
            "env": self.env,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "description": self.description,
            "auto_start": self.auto_start,
            "health_check_url": self.health_check_url
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MCPServer':
        """Create instance from dictionary."""
        server = cls()
        server.id = data.get("id", generate_id())
        server.name = data.get("name", "")
        server.command = data.get("command", "")
        server.args = data.get("args", [])
        server.env = data.get("env", {})
        server.status = ServerStatus(data.get("status", "unknown"))
        server.created_at = datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now()
        server.last_seen = datetime.fromisoformat(data["last_seen"]) if data.get("last_seen") else None
        server.description = data.get("description", "")
        server.auto_start = data.get("auto_start", False)
        server.health_check_url = data.get("health_check_url")
        return server


@dataclass
class MCPTool:
    """MCP Tool definition and metadata."""
    id: str = field(default_factory=generate_id)
    name: str = ""
    description: str = ""
    schema: Dict[str, Any] = field(default_factory=dict)
    server_id: str = ""
    enabled: bool = True
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    category: str = "general"
    usage_count: int = 0
    last_used: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "schema": self.schema,
            "server_id": self.server_id,
            "enabled": self.enabled,
            "parameters": self.parameters,
            "category": self.category,
            "usage_count": self.usage_count,
            "last_used": self.last_used.isoformat() if self.last_used else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MCPTool':
        """Create instance from dictionary."""
        tool = cls()
        tool.id = data.get("id", generate_id())
        tool.name = data.get("name", "")
        tool.description = data.get("description", "")
        tool.schema = data.get("schema", {})
        tool.server_id = data.get("server_id", "")
        tool.enabled = data.get("enabled", True)
        tool.parameters = data.get("parameters", [])
        tool.category = data.get("category", "general")
        tool.usage_count = data.get("usage_count", 0)
        tool.last_used = datetime.fromisoformat(data["last_used"]) if data.get("last_used") else None
        return tool