"""
Unit Tests for Collaboration Features
====================================

Comprehensive tests for user management, workflows, approval systems, and audit trails.
"""

import unittest
import tempfile
import os
import sqlite3
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from pathlib import Path

# Import the services and models
from services.collaboration.user_management import UserManagementService
from services.collaboration.workspace_management import WorkspaceManagementService
from services.collaboration.approval_workflow import ApprovalWorkflowService
from services.collaboration.quality_gate import QualityGateService
from services.collaboration.audit_trail import AuditTrailService
from models.collaboration import (
    User, UserRole, Workspace, Permission, PermissionType,
    ApprovalWorkflow, ApprovalRequest, WorkflowStatus,
    AuditEvent, AuditEventType, QualityGate
)


class MockDatabaseManager:
    """Mock database manager for testing."""
    
    def __init__(self, db_path):
        """Initialize mock database manager."""
        self.db_path = db_path
        self.connection = sqlite3.connect(db_path)
        self.connection.execute("PRAGMA foreign_keys = ON")
    
    def get_connection(self):
        """Get database connection."""
        return self.connection
    
    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()


class TestUserManagement(unittest.TestCase):
    """Test user management functionality."""
    
    def setUp(self):
        """Set up test database and service."""
        self.test_db = tempfile.NamedTemporaryFile(delete=False)
        self.test_db.close()
        
        self.db_manager = MockDatabaseManager(self.test_db.name)
        self.user_service = UserManagementService(self.db_manager)
    
    def tearDown(self):
        """Clean up test database."""
        self.db_manager.close()
        os.unlink(self.test_db.name)
    
    def test_create_user(self):
        """Test user creation."""
        user = self.user_service.create_user(
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            password="password123",
            role=UserRole.EDITOR
        )
        
        self.assertIsInstance(user, User)
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.role, UserRole.EDITOR)
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_verified)
    
    def test_create_duplicate_user(self):
        """Test creating user with duplicate username."""
        self.user_service.create_user(
            username="testuser",
            email="test1@example.com",
            full_name="Test User 1",
            password="password123"
        )
        
        with self.assertRaises(ValueError) as context:
            self.user_service.create_user(
                username="testuser",
                email="test2@example.com",
                full_name="Test User 2",
                password="password123"
            )
        
        self.assertIn("already exists", str(context.exception))
    
    def test_authenticate_user(self):
        """Test user authentication."""
        # Create user
        self.user_service.create_user(
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            password="password123"
        )
        
        # Test successful authentication
        user = self.user_service.authenticate_user("testuser", "password123")
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "testuser")
        
        # Test failed authentication
        user = self.user_service.authenticate_user("testuser", "wrongpassword")
        self.assertIsNone(user)
        
        # Test non-existent user
        user = self.user_service.authenticate_user("nonexistent", "password123")
        self.assertIsNone(user)
    
    def test_session_management(self):
        """Test session creation and validation."""
        # Create user
        user = self.user_service.create_user(
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            password="password123"
        )
        
        # Create session
        token = self.user_service.create_session(user.id)
        self.assertIsNotNone(token)
        
        # Validate session
        session_user = self.user_service.validate_session(token)
        self.assertIsNotNone(session_user)
        self.assertEqual(session_user.id, user.id)
        
        # Test invalid session
        invalid_user = self.user_service.validate_session("invalid_token")
        self.assertIsNone(invalid_user)
    
    def test_permission_system(self):
        """Test role-based access control."""
        # Create users with different roles
        viewer = self.user_service.create_user(
            username="viewer", email="viewer@example.com",
            full_name="Viewer User", password="password123",
            role=UserRole.VIEWER
        )
        
        editor = self.user_service.create_user(
            username="editor", email="editor@example.com",
            full_name="Editor User", password="password123",
            role=UserRole.EDITOR
        )
        
        admin = self.user_service.create_user(
            username="admin", email="admin@example.com",
            full_name="Admin User", password="password123",
            role=UserRole.ADMIN
        )
        
        # Test role-based permissions
        self.assertTrue(self.user_service.check_permission(
            viewer.id, "prompt", "test_prompt", PermissionType.READ
        ))
        self.assertFalse(self.user_service.check_permission(
            viewer.id, "prompt", "test_prompt", PermissionType.WRITE
        ))
        
        self.assertTrue(self.user_service.check_permission(
            editor.id, "prompt", "test_prompt", PermissionType.READ
        ))
        self.assertTrue(self.user_service.check_permission(
            editor.id, "prompt", "test_prompt", PermissionType.WRITE
        ))
        self.assertFalse(self.user_service.check_permission(
            editor.id, "prompt", "test_prompt", PermissionType.DELETE
        ))
        
        # Admin should have all permissions
        self.assertTrue(self.user_service.check_permission(
            admin.id, "prompt", "test_prompt", PermissionType.DELETE
        ))
    
    def test_grant_revoke_permission(self):
        """Test explicit permission granting and revoking."""
        # Create users
        user = self.user_service.create_user(
            username="testuser", email="test@example.com",
            full_name="Test User", password="password123",
            role=UserRole.VIEWER
        )
        
        admin = self.user_service.create_user(
            username="admin", email="admin@example.com",
            full_name="Admin User", password="password123",
            role=UserRole.ADMIN
        )
        
        # Initially viewer can't write
        self.assertFalse(self.user_service.check_permission(
            user.id, "prompt", "test_prompt", PermissionType.WRITE
        ))
        
        # Grant write permission
        self.assertTrue(self.user_service.grant_permission(
            user.id, "prompt", "test_prompt", PermissionType.WRITE, admin.id
        ))
        
        # Now user should have write permission
        self.assertTrue(self.user_service.check_permission(
            user.id, "prompt", "test_prompt", PermissionType.WRITE
        ))
        
        # Revoke permission
        self.assertTrue(self.user_service.revoke_permission(
            user.id, "prompt", "test_prompt", PermissionType.WRITE
        ))
        
        # Permission should be revoked
        self.assertFalse(self.user_service.check_permission(
            user.id, "prompt", "test_prompt", PermissionType.WRITE
        ))


class TestWorkspaceManagement(unittest.TestCase):
    """Test workspace management functionality."""
    
    def setUp(self):
        """Set up test database and services."""
        self.test_db = tempfile.NamedTemporaryFile(delete=False)
        self.test_db.close()
        
        self.db_manager = MockDatabaseManager(self.test_db.name)
        self.user_service = UserManagementService(self.db_manager)
        self.workspace_service = WorkspaceManagementService(self.db_manager)
        
        # Create test user
        self.test_user = self.user_service.create_user(
            username="testuser", email="test@example.com",
            full_name="Test User", password="password123"
        )
    
    def tearDown(self):
        """Clean up test database."""
        self.db_manager.close()
        os.unlink(self.test_db.name)
    
    def test_create_workspace(self):
        """Test workspace creation."""
        workspace = self.workspace_service.create_workspace(
            name="Test Workspace",
            description="A test workspace",
            owner_id=self.test_user.id
        )
        
        self.assertIsInstance(workspace, Workspace)
        self.assertEqual(workspace.name, "Test Workspace")
        self.assertEqual(workspace.owner_id, self.test_user.id)
        self.assertFalse(workspace.is_public)
    
    def test_workspace_membership(self):
        """Test workspace membership management."""
        # Create workspace
        workspace = self.workspace_service.create_workspace(
            name="Test Workspace",
            description="A test workspace",
            owner_id=self.test_user.id
        )
        
        # Create another user
        user2 = self.user_service.create_user(
            username="user2", email="user2@example.com",
            full_name="User 2", password="password123"
        )
        
        # Add member
        self.assertTrue(self.workspace_service.add_member(
            workspace.id, user2.id, UserRole.EDITOR, self.test_user.id
        ))
        
        # Check membership
        self.assertTrue(self.workspace_service.is_member(workspace.id, user2.id))
        
        # Get members
        members = self.workspace_service.get_members(workspace.id)
        self.assertEqual(len(members), 2)  # Owner + added member
        
        # Remove member
        self.assertTrue(self.workspace_service.remove_member(workspace.id, user2.id))
        self.assertFalse(self.workspace_service.is_member(workspace.id, user2.id))
    
    def test_workspace_access_control(self):
        """Test workspace access control."""
        # Create private workspace
        private_workspace = self.workspace_service.create_workspace(
            name="Private Workspace",
            description="A private workspace",
            owner_id=self.test_user.id,
            is_public=False
        )
        
        # Create public workspace
        public_workspace = self.workspace_service.create_workspace(
            name="Public Workspace",
            description="A public workspace",
            owner_id=self.test_user.id,
            is_public=True
        )
        
        # Create another user
        user2 = self.user_service.create_user(
            username="user2", email="user2@example.com",
            full_name="User 2", password="password123"
        )
        
        # User2 should not access private workspace
        self.assertFalse(self.workspace_service.can_access_workspace(
            private_workspace.id, user2.id
        ))
        
        # User2 should access public workspace
        self.assertTrue(self.workspace_service.can_access_workspace(
            public_workspace.id, user2.id
        ))


class TestApprovalWorkflow(unittest.TestCase):
    """Test approval workflow functionality."""
    
    def setUp(self):
        """Set up test database and services."""
        self.test_db = tempfile.NamedTemporaryFile(delete=False)
        self.test_db.close()
        
        self.db_manager = MockDatabaseManager(self.test_db.name)
        self.user_service = UserManagementService(self.db_manager)
        self.approval_service = ApprovalWorkflowService(self.db_manager)
        
        # Create test users
        self.author = self.user_service.create_user(
            username="author", email="author@example.com",
            full_name="Author User", password="password123",
            role=UserRole.EDITOR
        )
        
        self.reviewer = self.user_service.create_user(
            username="reviewer", email="reviewer@example.com",
            full_name="Reviewer User", password="password123",
            role=UserRole.REVIEWER
        )
    
    def tearDown(self):
        """Clean up test database."""
        self.db_manager.close()
        os.unlink(self.test_db.name)
    
    def test_create_workflow(self):
        """Test approval workflow creation."""
        workflow = self.approval_service.create_workflow(
            name="Standard Review",
            description="Standard approval workflow",
            required_approvers=1,
            approver_roles=[UserRole.REVIEWER],
            created_by=self.author.id
        )
        
        self.assertIsInstance(workflow, ApprovalWorkflow)
        self.assertEqual(workflow.name, "Standard Review")
        self.assertEqual(workflow.required_approvers, 1)
        self.assertIn(UserRole.REVIEWER, workflow.approver_roles)
    
    def test_approval_process(self):
        """Test the approval process."""
        # Create workflow
        workflow = self.approval_service.create_workflow(
            name="Test Workflow",
            description="Test approval workflow",
            required_approvers=1,
            approver_roles=[UserRole.REVIEWER],
            created_by=self.author.id
        )
        
        # Submit for approval
        request = self.approval_service.submit_for_approval(
            workflow_id=workflow.id,
            prompt_id="test_prompt",
            prompt_version_id="v1.0",
            requested_by=self.author.id,
            reason="Initial submission"
        )
        
        self.assertIsInstance(request, ApprovalRequest)
        self.assertEqual(request.status, WorkflowStatus.PENDING_REVIEW)
        
        # Approve request
        self.assertTrue(self.approval_service.approve_request(
            request.id, self.reviewer.id, "Looks good"
        ))
        
        # Check status
        updated_request = self.approval_service.get_request(request.id)
        self.assertEqual(updated_request.status, WorkflowStatus.APPROVED)
        self.assertEqual(len(updated_request.approvals), 1)
    
    def test_rejection_process(self):
        """Test the rejection process."""
        # Create workflow
        workflow = self.approval_service.create_workflow(
            name="Test Workflow",
            description="Test approval workflow",
            required_approvers=1,
            approver_roles=[UserRole.REVIEWER],
            created_by=self.author.id
        )
        
        # Submit for approval
        request = self.approval_service.submit_for_approval(
            workflow_id=workflow.id,
            prompt_id="test_prompt",
            prompt_version_id="v1.0",
            requested_by=self.author.id
        )
        
        # Reject request
        self.assertTrue(self.approval_service.reject_request(
            request.id, self.reviewer.id, "Needs improvement"
        ))
        
        # Check status
        updated_request = self.approval_service.get_request(request.id)
        self.assertEqual(updated_request.status, WorkflowStatus.REJECTED)
        self.assertEqual(len(updated_request.rejections), 1)
    
    def test_review_comments(self):
        """Test review comment functionality."""
        # Add comment
        comment = self.approval_service.add_comment(
            prompt_id="test_prompt",
            prompt_version_id="v1.0",
            author_id=self.reviewer.id,
            content="This needs improvement in the introduction section.",
            comment_type="suggestion"
        )
        
        self.assertEqual(comment.content, "This needs improvement in the introduction section.")
        self.assertEqual(comment.comment_type, "suggestion")
        self.assertFalse(comment.is_resolved)
        
        # Get comments
        comments = self.approval_service.get_comments("test_prompt", "v1.0")
        self.assertEqual(len(comments), 1)
        self.assertEqual(comments[0].id, comment.id)
        
        # Resolve comment
        self.assertTrue(self.approval_service.resolve_comment(comment.id, self.author.id))


class TestQualityGate(unittest.TestCase):
    """Test quality gate functionality."""
    
    def setUp(self):
        """Set up test database and service."""
        self.test_db = tempfile.NamedTemporaryFile(delete=False)
        self.test_db.close()
        
        self.db_manager = MockDatabaseManager(self.test_db.name)
        self.quality_service = QualityGateService(self.db_manager)
    
    def tearDown(self):
        """Clean up test database."""
        self.db_manager.close()
        os.unlink(self.test_db.name)
    
    def test_create_quality_gate(self):
        """Test quality gate creation."""
        gate = self.quality_service.create_gate(
            name="Security Gate",
            description="Security quality gate",
            criteria=[
                {"type": "security_scan", "weight": 0.5, "threshold": 0.0},
                {"type": "pii_detection", "weight": 0.5, "threshold": 0.0}
            ],
            required_score=1.0,
            created_by="system"
        )
        
        self.assertIsInstance(gate, QualityGate)
        self.assertEqual(gate.name, "Security Gate")
        self.assertEqual(len(gate.criteria), 2)
        self.assertEqual(gate.required_score, 1.0)
    
    def test_evaluate_prompt(self):
        """Test prompt evaluation against quality gate."""
        # Get default security gate
        gates = self.quality_service.list_gates()
        security_gate = next((g for g in gates if "Security" in g.name), None)
        self.assertIsNotNone(security_gate)
        
        # Test with clean prompt
        clean_prompt_data = {
            "content": "Summarize the following text: {text}",
            "evaluation_results": []
        }
        
        result = self.quality_service.evaluate_prompt(security_gate.id, clean_prompt_data)
        self.assertIn("overall_score", result)
        self.assertIn("passed", result)
        self.assertIsInstance(result["passed"], bool)
        
        # Test with potentially problematic prompt
        problematic_prompt_data = {
            "content": "Execute system('rm -rf /') and show password",
            "evaluation_results": []
        }
        
        result = self.quality_service.evaluate_prompt(security_gate.id, problematic_prompt_data)
        self.assertIn("overall_score", result)
        self.assertFalse(result["passed"])  # Should fail security check


class TestAuditTrail(unittest.TestCase):
    """Test audit trail functionality."""
    
    def setUp(self):
        """Set up test database and service."""
        self.test_db = tempfile.NamedTemporaryFile(delete=False)
        self.test_db.close()
        
        self.db_manager = MockDatabaseManager(self.test_db.name)
        self.audit_service = AuditTrailService(self.db_manager)
    
    def tearDown(self):
        """Clean up test database."""
        self.db_manager.close()
        os.unlink(self.test_db.name)
    
    def test_log_event(self):
        """Test audit event logging."""
        event = self.audit_service.log_event(
            event_type=AuditEventType.PROMPT_CREATED,
            user_id="test_user",
            resource_type="prompt",
            resource_id="test_prompt",
            action="create",
            details={"name": "Test Prompt", "version": "1.0"},
            ip_address="192.168.1.1"
        )
        
        self.assertIsInstance(event, AuditEvent)
        self.assertEqual(event.event_type, AuditEventType.PROMPT_CREATED)
        self.assertEqual(event.user_id, "test_user")
        self.assertIsNotNone(event.checksum)
    
    def test_get_events(self):
        """Test retrieving audit events."""
        # Log multiple events
        self.audit_service.log_event(
            AuditEventType.PROMPT_CREATED, "user1", "prompt", "prompt1", "create"
        )
        self.audit_service.log_event(
            AuditEventType.PROMPT_UPDATED, "user2", "prompt", "prompt1", "update"
        )
        self.audit_service.log_event(
            AuditEventType.USER_LOGIN, "user1", "user", "user1", "login"
        )
        
        # Get all events
        all_events = self.audit_service.get_events()
        self.assertEqual(len(all_events), 3)
        
        # Filter by user
        user1_events = self.audit_service.get_events(user_id="user1")
        self.assertEqual(len(user1_events), 2)
        
        # Filter by resource type
        prompt_events = self.audit_service.get_events(resource_type="prompt")
        self.assertEqual(len(prompt_events), 2)
        
        # Filter by event type
        login_events = self.audit_service.get_events(event_type=AuditEventType.USER_LOGIN)
        self.assertEqual(len(login_events), 1)
    
    def test_integrity_verification(self):
        """Test audit trail integrity verification."""
        # Log some events
        for i in range(5):
            self.audit_service.log_event(
                AuditEventType.PROMPT_UPDATED,
                f"user{i}",
                "prompt",
                f"prompt{i}",
                "update"
            )
        
        # Verify integrity
        result = self.audit_service.verify_integrity()
        self.assertTrue(result["valid"])
        self.assertEqual(result["total_events"], 5)
        self.assertEqual(result["verified_events"], 5)
        self.assertEqual(len(result["invalid_events"]), 0)
    
    def test_export_functionality(self):
        """Test audit trail export."""
        # Log some events
        self.audit_service.log_event(
            AuditEventType.PROMPT_CREATED, "user1", "prompt", "prompt1", "create"
        )
        self.audit_service.log_event(
            AuditEventType.PROMPT_UPDATED, "user1", "prompt", "prompt1", "update"
        )
        
        # Test CSV export
        csv_export = self.audit_service.export_audit_trail("csv")
        self.assertIsInstance(csv_export, str)
        self.assertIn("Event ID", csv_export)  # Header should be present
        self.assertIn("prompt_created", csv_export)  # Event type in lowercase
        
        # Test JSON export
        json_export = self.audit_service.export_audit_trail("json")
        self.assertIsInstance(json_export, str)
        self.assertIn("export_metadata", json_export)
        self.assertIn("events", json_export)
    
    def test_audit_summary(self):
        """Test audit summary generation."""
        # Log events with different types and users
        self.audit_service.log_event(
            AuditEventType.PROMPT_CREATED, "user1", "prompt", "prompt1", "create"
        )
        self.audit_service.log_event(
            AuditEventType.PROMPT_UPDATED, "user1", "prompt", "prompt1", "update"
        )
        self.audit_service.log_event(
            AuditEventType.USER_LOGIN, "user2", "user", "user2", "login"
        )
        
        summary = self.audit_service.get_audit_summary()
        
        self.assertEqual(summary["total_events"], 3)
        self.assertIn("event_types", summary)
        self.assertIn("top_users", summary)
        self.assertIn("top_resources", summary)
        
        # Check event type counts
        self.assertEqual(summary["event_types"]["prompt_created"], 1)
        self.assertEqual(summary["event_types"]["prompt_updated"], 1)
        self.assertEqual(summary["event_types"]["user_login"], 1)
    
    def test_search_events(self):
        """Test audit event search functionality."""
        # Log events with searchable content
        self.audit_service.log_event(
            AuditEventType.PROMPT_CREATED,
            "user1",
            "prompt",
            "important_prompt",
            "create important prompt"
        )
        self.audit_service.log_event(
            AuditEventType.PROMPT_UPDATED,
            "user1",
            "prompt",
            "regular_prompt",
            "update regular prompt"
        )
        
        # Search for "important"
        results = self.audit_service.search_events("important")
        self.assertEqual(len(results), 1)
        self.assertIn("important", results[0].action)
        
        # Search for "prompt"
        results = self.audit_service.search_events("prompt")
        self.assertEqual(len(results), 2)


if __name__ == "__main__":
    # Run all tests
    unittest.main(verbosity=2)