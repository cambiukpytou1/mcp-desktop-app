"""
Security and Audit Data Models
==============================

Data models for security events, audit trails, and monitoring.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from .base import SecurityEventType, RiskLevel, generate_id
import hashlib


@dataclass
class SecurityEvent:
    """Security event record."""
    id: str = field(default_factory=generate_id)
    timestamp: datetime = field(default_factory=datetime.now)
    event_type: SecurityEventType = SecurityEventType.TOOL_EXECUTION
    user: str = "unknown"
    resource: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    risk_level: RiskLevel = RiskLevel.LOW
    source_ip: Optional[str] = None
    user_agent: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type.value,
            "user": self.user,
            "resource": self.resource,
            "details": self.details,
            "risk_level": self.risk_level.value,
            "source_ip": self.source_ip,
            "user_agent": self.user_agent
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SecurityEvent':
        """Create instance from dictionary."""
        event = cls()
        event.id = data.get("id", generate_id())
        event.timestamp = datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.now()
        event.event_type = SecurityEventType(data.get("event_type", "tool_execution"))
        event.user = data.get("user", "unknown")
        event.resource = data.get("resource", "")
        event.details = data.get("details", {})
        event.risk_level = RiskLevel(data.get("risk_level", "low"))
        event.source_ip = data.get("source_ip")
        event.user_agent = data.get("user_agent")
        return event


@dataclass
class AuditEvent:
    """Audit trail event record."""
    id: str = field(default_factory=generate_id)
    timestamp: datetime = field(default_factory=datetime.now)
    user: str = "system"
    action: str = ""
    resource_type: str = ""
    resource_id: str = ""
    old_value: Optional[Dict[str, Any]] = None
    new_value: Optional[Dict[str, Any]] = None
    checksum: str = field(default="")
    session_id: Optional[str] = None
    
    def __post_init__(self):
        """Generate checksum after initialization."""
        if not self.checksum:
            self.checksum = self._generate_checksum()
    
    def _generate_checksum(self) -> str:
        """Generate cryptographic checksum for integrity verification."""
        data = f"{self.timestamp.isoformat()}{self.user}{self.action}{self.resource_type}{self.resource_id}"
        if self.old_value:
            data += str(sorted(self.old_value.items()))
        if self.new_value:
            data += str(sorted(self.new_value.items()))
        return hashlib.sha256(data.encode()).hexdigest()
    
    def verify_integrity(self) -> bool:
        """Verify the integrity of this audit event."""
        expected_checksum = self._generate_checksum()
        return self.checksum == expected_checksum
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "user": self.user,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "checksum": self.checksum,
            "session_id": self.session_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AuditEvent':
        """Create instance from dictionary."""
        event = cls()
        event.id = data.get("id", generate_id())
        event.timestamp = datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.now()
        event.user = data.get("user", "system")
        event.action = data.get("action", "")
        event.resource_type = data.get("resource_type", "")
        event.resource_id = data.get("resource_id", "")
        event.old_value = data.get("old_value")
        event.new_value = data.get("new_value")
        event.checksum = data.get("checksum", "")
        event.session_id = data.get("session_id")
        return event


@dataclass
class Alert:
    """System alert definition."""
    id: str = field(default_factory=generate_id)
    timestamp: datetime = field(default_factory=datetime.now)
    title: str = ""
    message: str = ""
    severity: RiskLevel = RiskLevel.LOW
    source: str = ""
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "title": self.title,
            "message": self.message,
            "severity": self.severity.value,
            "source": self.source,
            "acknowledged": self.acknowledged,
            "acknowledged_by": self.acknowledged_by,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None
        }


@dataclass
class SecurityReport:
    """Security report summary."""
    period_start: datetime
    period_end: datetime
    total_events: int = 0
    events_by_type: Dict[str, int] = field(default_factory=dict)
    events_by_risk: Dict[str, int] = field(default_factory=dict)
    top_users: List[Dict[str, Any]] = field(default_factory=list)
    top_resources: List[Dict[str, Any]] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "total_events": self.total_events,
            "events_by_type": self.events_by_type,
            "events_by_risk": self.events_by_risk,
            "top_users": self.top_users,
            "top_resources": self.top_resources,
            "generated_at": self.generated_at.isoformat()
        }