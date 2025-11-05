"""
Approval Workflow Service for MCP Admin Application
==================================================

Service for managing approval workflows, review processes, and prompt certification.
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
import json

from models.collaboration import (
    ApprovalWorkflow, ApprovalRequest, ReviewComment, QualityGate,
    WorkflowStatus, UserRole
)
from data.database import DatabaseManager


class ApprovalWorkflowService:
    """Service for approval workflows and review processes."""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize the approval workflow service."""
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
        self._init_database()
    
    def _init_database(self):
        """Initialize database tables for approval workflows."""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Approval workflows table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS approval_workflows (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    required_approvers INTEGER DEFAULT 1,
                    approver_roles TEXT NOT NULL,
                    auto_approve_conditions TEXT DEFAULT '{}',
                    steps TEXT DEFAULT '[]',
                    created_by TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            """)
            
            # Approval requests table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS approval_requests (
                    id TEXT PRIMARY KEY,
                    workflow_id TEXT NOT NULL,
                    prompt_id TEXT NOT NULL,
                    prompt_version_id TEXT NOT NULL,
                    requested_by TEXT NOT NULL,
                    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    reason TEXT,
                    priority TEXT DEFAULT 'normal',
                    status TEXT DEFAULT 'pending_review',
                    current_step INTEGER DEFAULT 0,
                    approvals TEXT DEFAULT '[]',
                    rejections TEXT DEFAULT '[]',
                    completed_at TIMESTAMP,
                    expires_at TIMESTAMP,
                    FOREIGN KEY (workflow_id) REFERENCES approval_workflows(id)
                )
            """)
            
            # Review comments table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS review_comments (
                    id TEXT PRIMARY KEY,
                    prompt_id TEXT NOT NULL,
                    prompt_version_id TEXT NOT NULL,
                    approval_request_id TEXT,
                    author_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    comment_type TEXT DEFAULT 'general',
                    parent_comment_id TEXT,
                    thread_id TEXT NOT NULL,
                    is_resolved BOOLEAN DEFAULT 0,
                    resolved_by TEXT,
                    resolved_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (approval_request_id) REFERENCES approval_requests(id)
                )
            """)
            
            # Quality gates table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS quality_gates (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    criteria TEXT DEFAULT '[]',
                    required_score REAL DEFAULT 0.8,
                    auto_pass_conditions TEXT DEFAULT '{}',
                    created_by TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_approval_requests_status ON approval_requests(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_approval_requests_prompt ON approval_requests(prompt_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_review_comments_prompt ON review_comments(prompt_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_review_comments_thread ON review_comments(thread_id)")
            
            conn.commit()
    
    def create_workflow(self, name: str, description: str, required_approvers: int,
                       approver_roles: List[UserRole], created_by: str,
                       auto_approve_conditions: Dict = None, steps: List[str] = None) -> ApprovalWorkflow:
        """Create a new approval workflow."""
        try:
            workflow = ApprovalWorkflow(
                name=name,
                description=description,
                required_approvers=required_approvers,
                approver_roles=approver_roles,
                auto_approve_conditions=auto_approve_conditions or {},
                steps=steps or [],
                created_by=created_by
            )
            
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO approval_workflows (
                        id, name, description, required_approvers, approver_roles,
                        auto_approve_conditions, steps, created_by, created_at,
                        updated_at, is_active
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    workflow.id, workflow.name, workflow.description,
                    workflow.required_approvers,
                    json.dumps([role.value for role in workflow.approver_roles]),
                    json.dumps(workflow.auto_approve_conditions),
                    json.dumps(workflow.steps),
                    workflow.created_by,
                    workflow.created_at.isoformat(),
                    workflow.updated_at.isoformat(),
                    workflow.is_active
                ))
                conn.commit()
            
            self.logger.info(f"Created approval workflow: {name} ({workflow.id})")
            return workflow
            
        except Exception as e:
            self.logger.error(f"Error creating approval workflow {name}: {e}")
            raise
    
    def get_workflow(self, workflow_id: str) -> Optional[ApprovalWorkflow]:
        """Get an approval workflow by ID."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, name, description, required_approvers, approver_roles,
                           auto_approve_conditions, steps, created_by, created_at,
                           updated_at, is_active
                    FROM approval_workflows 
                    WHERE id = ?
                """, (workflow_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                return ApprovalWorkflow(
                    id=row[0],
                    name=row[1],
                    description=row[2],
                    required_approvers=row[3],
                    approver_roles=[UserRole(role) for role in json.loads(row[4])],
                    auto_approve_conditions=json.loads(row[5]),
                    steps=json.loads(row[6]),
                    created_by=row[7],
                    created_at=datetime.fromisoformat(row[8]),
                    updated_at=datetime.fromisoformat(row[9]),
                    is_active=bool(row[10])
                )
                
        except Exception as e:
            self.logger.error(f"Error getting approval workflow {workflow_id}: {e}")
            return None
    
    def list_workflows(self, active_only: bool = True) -> List[ApprovalWorkflow]:
        """List all approval workflows."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT id, name, description, required_approvers, approver_roles,
                           auto_approve_conditions, steps, created_by, created_at,
                           updated_at, is_active
                    FROM approval_workflows
                """
                
                if active_only:
                    query += " WHERE is_active = 1"
                
                query += " ORDER BY name"
                cursor.execute(query)
                
                workflows = []
                for row in cursor.fetchall():
                    workflow = ApprovalWorkflow(
                        id=row[0],
                        name=row[1],
                        description=row[2],
                        required_approvers=row[3],
                        approver_roles=[UserRole(role) for role in json.loads(row[4])],
                        auto_approve_conditions=json.loads(row[5]),
                        steps=json.loads(row[6]),
                        created_by=row[7],
                        created_at=datetime.fromisoformat(row[8]),
                        updated_at=datetime.fromisoformat(row[9]),
                        is_active=bool(row[10])
                    )
                    workflows.append(workflow)
                
                return workflows
                
        except Exception as e:
            self.logger.error(f"Error listing approval workflows: {e}")
            return []
    
    def submit_for_approval(self, workflow_id: str, prompt_id: str, prompt_version_id: str,
                           requested_by: str, reason: str = "", priority: str = "normal",
                           expires_hours: int = 168) -> ApprovalRequest:
        """Submit a prompt for approval."""
        try:
            # Check if workflow exists
            workflow = self.get_workflow(workflow_id)
            if not workflow:
                raise ValueError(f"Workflow {workflow_id} not found")
            
            # Check for existing pending request
            existing = self.get_pending_request(prompt_id, prompt_version_id)
            if existing:
                raise ValueError(f"Approval request already exists for this prompt version")
            
            # Create approval request
            request = ApprovalRequest(
                workflow_id=workflow_id,
                prompt_id=prompt_id,
                prompt_version_id=prompt_version_id,
                requested_by=requested_by,
                reason=reason,
                priority=priority,
                expires_at=datetime.now() + timedelta(hours=expires_hours)
            )
            
            # Check auto-approve conditions
            if self._check_auto_approve(workflow, request):
                request.status = WorkflowStatus.APPROVED
                request.completed_at = datetime.now()
            
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO approval_requests (
                        id, workflow_id, prompt_id, prompt_version_id, requested_by,
                        requested_at, reason, priority, status, current_step,
                        approvals, rejections, completed_at, expires_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    request.id, request.workflow_id, request.prompt_id,
                    request.prompt_version_id, request.requested_by,
                    request.requested_at.isoformat(), request.reason,
                    request.priority, request.status.value, request.current_step,
                    json.dumps(request.approvals), json.dumps(request.rejections),
                    request.completed_at.isoformat() if request.completed_at else None,
                    request.expires_at.isoformat() if request.expires_at else None
                ))
                conn.commit()
            
            self.logger.info(f"Submitted approval request: {request.id} for prompt {prompt_id}")
            return request
            
        except Exception as e:
            self.logger.error(f"Error submitting approval request: {e}")
            raise
    
    def _check_auto_approve(self, workflow: ApprovalWorkflow, request: ApprovalRequest) -> bool:
        """Check if a request meets auto-approve conditions."""
        try:
            conditions = workflow.auto_approve_conditions
            if not conditions:
                return False
            
            # Example auto-approve conditions:
            # - Author has certain role
            # - Prompt meets quality thresholds
            # - Minor changes only
            
            # This is a simplified implementation
            # In practice, you'd implement more sophisticated logic
            
            return False  # Default to manual approval
            
        except Exception as e:
            self.logger.error(f"Error checking auto-approve conditions: {e}")
            return False
    
    def approve_request(self, request_id: str, approver_id: str, comment: str = "") -> bool:
        """Approve an approval request."""
        try:
            request = self.get_request(request_id)
            if not request:
                raise ValueError(f"Approval request {request_id} not found")
            
            if request.status != WorkflowStatus.PENDING_REVIEW:
                raise ValueError(f"Request is not pending approval (status: {request.status.value})")
            
            # Add approval
            approval = {
                "approver_id": approver_id,
                "approved_at": datetime.now().isoformat(),
                "comment": comment
            }
            request.approvals.append(approval)
            
            # Check if enough approvals
            workflow = self.get_workflow(request.workflow_id)
            if len(request.approvals) >= workflow.required_approvers:
                request.status = WorkflowStatus.APPROVED
                request.completed_at = datetime.now()
            
            # Update database
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE approval_requests 
                    SET approvals = ?, status = ?, completed_at = ?
                    WHERE id = ?
                """, (
                    json.dumps(request.approvals),
                    request.status.value,
                    request.completed_at.isoformat() if request.completed_at else None,
                    request_id
                ))
                conn.commit()
            
            self.logger.info(f"Approved request {request_id} by user {approver_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error approving request {request_id}: {e}")
            return False
    
    def reject_request(self, request_id: str, reviewer_id: str, reason: str) -> bool:
        """Reject an approval request."""
        try:
            request = self.get_request(request_id)
            if not request:
                raise ValueError(f"Approval request {request_id} not found")
            
            if request.status != WorkflowStatus.PENDING_REVIEW:
                raise ValueError(f"Request is not pending approval (status: {request.status.value})")
            
            # Add rejection
            rejection = {
                "reviewer_id": reviewer_id,
                "rejected_at": datetime.now().isoformat(),
                "reason": reason
            }
            request.rejections.append(rejection)
            request.status = WorkflowStatus.REJECTED
            request.completed_at = datetime.now()
            
            # Update database
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE approval_requests 
                    SET rejections = ?, status = ?, completed_at = ?
                    WHERE id = ?
                """, (
                    json.dumps(request.rejections),
                    request.status.value,
                    request.completed_at.isoformat(),
                    request_id
                ))
                conn.commit()
            
            self.logger.info(f"Rejected request {request_id} by user {reviewer_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error rejecting request {request_id}: {e}")
            return False
    
    def get_request(self, request_id: str) -> Optional[ApprovalRequest]:
        """Get an approval request by ID."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, workflow_id, prompt_id, prompt_version_id, requested_by,
                           requested_at, reason, priority, status, current_step,
                           approvals, rejections, completed_at, expires_at
                    FROM approval_requests 
                    WHERE id = ?
                """, (request_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                return ApprovalRequest(
                    id=row[0],
                    workflow_id=row[1],
                    prompt_id=row[2],
                    prompt_version_id=row[3],
                    requested_by=row[4],
                    requested_at=datetime.fromisoformat(row[5]),
                    reason=row[6],
                    priority=row[7],
                    status=WorkflowStatus(row[8]),
                    current_step=row[9],
                    approvals=json.loads(row[10]),
                    rejections=json.loads(row[11]),
                    completed_at=datetime.fromisoformat(row[12]) if row[12] else None,
                    expires_at=datetime.fromisoformat(row[13]) if row[13] else None
                )
                
        except Exception as e:
            self.logger.error(f"Error getting approval request {request_id}: {e}")
            return None
    
    def get_pending_request(self, prompt_id: str, prompt_version_id: str) -> Optional[ApprovalRequest]:
        """Get pending approval request for a prompt version."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id FROM approval_requests 
                    WHERE prompt_id = ? AND prompt_version_id = ? 
                    AND status IN ('pending_review', 'in_review')
                    ORDER BY requested_at DESC
                    LIMIT 1
                """, (prompt_id, prompt_version_id))
                
                row = cursor.fetchone()
                if row:
                    return self.get_request(row[0])
                
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting pending request: {e}")
            return None
    
    def list_requests(self, status: WorkflowStatus = None, user_id: str = None,
                     prompt_id: str = None) -> List[ApprovalRequest]:
        """List approval requests with optional filters."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT id, workflow_id, prompt_id, prompt_version_id, requested_by,
                           requested_at, reason, priority, status, current_step,
                           approvals, rejections, completed_at, expires_at
                    FROM approval_requests
                    WHERE 1=1
                """
                params = []
                
                if status:
                    query += " AND status = ?"
                    params.append(status.value)
                
                if user_id:
                    query += " AND requested_by = ?"
                    params.append(user_id)
                
                if prompt_id:
                    query += " AND prompt_id = ?"
                    params.append(prompt_id)
                
                query += " ORDER BY requested_at DESC"
                cursor.execute(query, params)
                
                requests = []
                for row in cursor.fetchall():
                    request = ApprovalRequest(
                        id=row[0],
                        workflow_id=row[1],
                        prompt_id=row[2],
                        prompt_version_id=row[3],
                        requested_by=row[4],
                        requested_at=datetime.fromisoformat(row[5]),
                        reason=row[6],
                        priority=row[7],
                        status=WorkflowStatus(row[8]),
                        current_step=row[9],
                        approvals=json.loads(row[10]),
                        rejections=json.loads(row[11]),
                        completed_at=datetime.fromisoformat(row[12]) if row[12] else None,
                        expires_at=datetime.fromisoformat(row[13]) if row[13] else None
                    )
                    requests.append(request)
                
                return requests
                
        except Exception as e:
            self.logger.error(f"Error listing approval requests: {e}")
            return []
    
    def add_comment(self, prompt_id: str, prompt_version_id: str, author_id: str,
                   content: str, comment_type: str = "general",
                   approval_request_id: str = None, parent_comment_id: str = None) -> ReviewComment:
        """Add a review comment to a prompt."""
        try:
            comment = ReviewComment(
                prompt_id=prompt_id,
                prompt_version_id=prompt_version_id,
                approval_request_id=approval_request_id,
                author_id=author_id,
                content=content,
                comment_type=comment_type,
                parent_comment_id=parent_comment_id
            )
            
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO review_comments (
                        id, prompt_id, prompt_version_id, approval_request_id,
                        author_id, content, comment_type, parent_comment_id,
                        thread_id, is_resolved, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    comment.id, comment.prompt_id, comment.prompt_version_id,
                    comment.approval_request_id, comment.author_id, comment.content,
                    comment.comment_type, comment.parent_comment_id,
                    comment.thread_id, comment.is_resolved,
                    comment.created_at.isoformat(), comment.updated_at.isoformat()
                ))
                conn.commit()
            
            self.logger.info(f"Added review comment: {comment.id}")
            return comment
            
        except Exception as e:
            self.logger.error(f"Error adding review comment: {e}")
            raise
    
    def get_comments(self, prompt_id: str, prompt_version_id: str = None) -> List[ReviewComment]:
        """Get review comments for a prompt."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT id, prompt_id, prompt_version_id, approval_request_id,
                           author_id, content, comment_type, parent_comment_id,
                           thread_id, is_resolved, resolved_by, resolved_at,
                           created_at, updated_at
                    FROM review_comments
                    WHERE prompt_id = ?
                """
                params = [prompt_id]
                
                if prompt_version_id:
                    query += " AND prompt_version_id = ?"
                    params.append(prompt_version_id)
                
                query += " ORDER BY created_at ASC"
                cursor.execute(query, params)
                
                comments = []
                for row in cursor.fetchall():
                    comment = ReviewComment(
                        id=row[0],
                        prompt_id=row[1],
                        prompt_version_id=row[2],
                        approval_request_id=row[3],
                        author_id=row[4],
                        content=row[5],
                        comment_type=row[6],
                        parent_comment_id=row[7],
                        thread_id=row[8],
                        is_resolved=bool(row[9]),
                        resolved_by=row[10],
                        resolved_at=datetime.fromisoformat(row[11]) if row[11] else None,
                        created_at=datetime.fromisoformat(row[12]),
                        updated_at=datetime.fromisoformat(row[13])
                    )
                    comments.append(comment)
                
                return comments
                
        except Exception as e:
            self.logger.error(f"Error getting review comments: {e}")
            return []
    
    def resolve_comment(self, comment_id: str, resolved_by: str) -> bool:
        """Mark a review comment as resolved."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE review_comments 
                    SET is_resolved = 1, resolved_by = ?, resolved_at = ?
                    WHERE id = ?
                """, (resolved_by, datetime.now().isoformat(), comment_id))
                conn.commit()
                
                success = cursor.rowcount > 0
                if success:
                    self.logger.info(f"Resolved comment {comment_id}")
                
                return success
                
        except Exception as e:
            self.logger.error(f"Error resolving comment {comment_id}: {e}")
            return False