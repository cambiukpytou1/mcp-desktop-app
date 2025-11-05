"""
Collaboration Data Models for MCP Admin Application
==================================================

Data models for user management, permissions, workflows, and audit trails.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from models.base import generate_id


class UserRole(Enum):
    """User role enumeration for role-based access control."""
    VIEWER = "viewer"
    EDITOR = "editor"
    REVIEWER = "reviewer"
    ADMIN = "admin"


class PermissionType(Enum):
    """Permission type enumeration."""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    APPROVE = "approve"
    ADMIN = "admin"


class WorkflowStatus(Enum):
    """Workflow status enumeration."""
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PRODUCTION = "production"
    ARCHIVED = "archived"


class AuditEventType(Enum):
    """Audit event type enumeration."""
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    PROMPT_CREATED = "prompt_created"
    PROMPT_UPDATED = "prompt_updated"
    PROMPT_DELETED = "prompt_deleted"
    PROMPT_APPROVED = "prompt_approved"
    PROMPT_REJECTED = "prompt_rejected"
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_REVOKED = "permission_revoked"
    WORKSPACE_CREATED = "workspace_created"
    WORKSPACE_UPDATED = "workspace_updated"
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_COMPLETED = "workflow_completed"


@dataclass
class User:
    """User account information."""
    id: str = field(default_factory=generate_id)
    username: str = ""
    email: str = ""
    full_name: str = ""
    password_hash: str = ""
    salt: str = ""
    
    # Role and permissions
    role: UserRole = UserRole.VIEWER
    is_active: bool = True
    is_verified: bool = False
    
    # Session management
    last_login: Optional[datetime] = None
    session_token: Optional[str] = None
    session_expires: Optional[datetime] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: Optional[str] = None
    
    # Preferences
    preferences: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "role": self.role.value,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "created_by": self.created_by,
            "preferences": self.preferences
        }
        
        if include_sensitive:
            data.update({
                "password_hash": self.password_hash,
                "salt": self.salt,
                "session_token": self.session_token,
                "session_expires": self.session_expires.isoformat() if self.session_expires else None
            })
        
        return data


@dataclass
class Workspace:
    """Workspace for organizing prompts and users."""
    id: str = field(default_factory=generate_id)
    name: str = ""
    description: str = ""
    
    # Access control
    owner_id: str = ""
    is_public: bool = False
    
    # Settings
    settings: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "owner_id": self.owner_id,
            "is_public": self.is_public,
            "settings": self.settings,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


@dataclass
class Permission:
    """Permission assignment for users and resources."""
    id: str = field(default_factory=generate_id)
    user_id: str = ""
    resource_type: str = ""  # "prompt", "workspace", "system"
    resource_id: str = ""
    permission_type: PermissionType = PermissionType.READ
    
    # Metadata
    granted_by: str = ""
    granted_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "permission_type": self.permission_type.value,
            "granted_by": self.granted_by,
            "granted_at": self.granted_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None
        }


@dataclass
class ApprovalWorkflow:
    """Approval workflow for prompt certification."""
    id: str = field(default_factory=generate_id)
    name: str = ""
    description: str = ""
    
    # Workflow configuration
    required_approvers: int = 1
    approver_roles: List[UserRole] = field(default_factory=lambda: [UserRole.REVIEWER])
    auto_approve_conditions: Dict[str, Any] = field(default_factory=dict)
    
    # Steps
    steps: List[str] = field(default_factory=list)
    
    # Metadata
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "required_approvers": self.required_approvers,
            "approver_roles": [role.value for role in self.approver_roles],
            "auto_approve_conditions": self.auto_approve_conditions,
            "steps": self.steps,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "is_active": self.is_active
        }


@dataclass
class ApprovalRequest:
    """Individual approval request for a prompt."""
    id: str = field(default_factory=generate_id)
    workflow_id: str = ""
    prompt_id: str = ""
    prompt_version_id: str = ""
    
    # Request details
    requested_by: str = ""
    requested_at: datetime = field(default_factory=datetime.now)
    reason: str = ""
    priority: str = "normal"  # "low", "normal", "high", "urgent"
    
    # Status
    status: WorkflowStatus = WorkflowStatus.PENDING_REVIEW
    current_step: int = 0
    
    # Approvals
    approvals: List[Dict[str, Any]] = field(default_factory=list)
    rejections: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metadata
    completed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "prompt_id": self.prompt_id,
            "prompt_version_id": self.prompt_version_id,
            "requested_by": self.requested_by,
            "requested_at": self.requested_at.isoformat(),
            "reason": self.reason,
            "priority": self.priority,
            "status": self.status.value,
            "current_step": self.current_step,
            "approvals": self.approvals,
            "rejections": self.rejections,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None
        }


@dataclass
class ReviewComment:
    """Review comment for prompts."""
    id: str = field(default_factory=generate_id)
    prompt_id: str = ""
    prompt_version_id: str = ""
    approval_request_id: Optional[str] = None
    
    # Comment details
    author_id: str = ""
    content: str = ""
    comment_type: str = "general"  # "general", "suggestion", "issue", "approval", "rejection"
    
    # Threading
    parent_comment_id: Optional[str] = None
    thread_id: str = field(default_factory=generate_id)
    
    # Status
    is_resolved: bool = False
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "prompt_id": self.prompt_id,
            "prompt_version_id": self.prompt_version_id,
            "approval_request_id": self.approval_request_id,
            "author_id": self.author_id,
            "content": self.content,
            "comment_type": self.comment_type,
            "parent_comment_id": self.parent_comment_id,
            "thread_id": self.thread_id,
            "is_resolved": self.is_resolved,
            "resolved_by": self.resolved_by,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


@dataclass
class AuditEvent:
    """Audit trail event for compliance and security."""
    id: str = field(default_factory=generate_id)
    event_type: AuditEventType = AuditEventType.PROMPT_UPDATED
    
    # Event details
    user_id: str = ""
    resource_type: str = ""
    resource_id: str = ""
    action: str = ""
    
    # Context
    details: Dict[str, Any] = field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    
    # Changes (for update events)
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    checksum: Optional[str] = None  # For tamper detection
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "event_type": self.event_type.value,
            "user_id": self.user_id,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "action": self.action,
            "details": self.details,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "session_id": self.session_id,
            "old_values": self.old_values,
            "new_values": self.new_values,
            "timestamp": self.timestamp.isoformat(),
            "checksum": self.checksum
        }


@dataclass
class QualityGate:
    """Quality gate configuration for prompt certification."""
    id: str = field(default_factory=generate_id)
    name: str = ""
    description: str = ""
    
    # Gate configuration
    criteria: List[Dict[str, Any]] = field(default_factory=list)
    required_score: float = 0.8
    auto_pass_conditions: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "criteria": self.criteria,
            "required_score": self.required_score,
            "auto_pass_conditions": self.auto_pass_conditions,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "is_active": self.is_active
        }