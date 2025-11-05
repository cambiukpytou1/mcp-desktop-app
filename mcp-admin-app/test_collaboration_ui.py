#!/usr/bin/env python3
"""
Test script for Collaboration UI components
==========================================

Tests the collaboration page and workflow management interface.
"""

import tkinter as tk
from tkinter import ttk
import sys
import os
import logging

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data.database import DatabaseManager
from services.collaboration.workspace_management import WorkspaceManagementService
from services.collaboration.user_management import UserManagementService
from services.collaboration.approval_workflow import ApprovalWorkflowService
from ui.collaboration_page import CollaborationPage
from models.collaboration import UserRole


def setup_test_data(workspace_service, user_service, approval_service):
    """Set up test data for demonstration."""
    try:
        # Create test users
        admin_user = user_service.create_user(
            username="admin",
            email="admin@example.com",
            full_name="System Administrator",
            password="admin123",
            role=UserRole.ADMIN
        )
        
        editor_user = user_service.create_user(
            username="editor1",
            email="editor@example.com",
            full_name="Content Editor",
            password="editor123",
            role=UserRole.EDITOR
        )
        
        reviewer_user = user_service.create_user(
            username="reviewer1",
            email="reviewer@example.com",
            full_name="Content Reviewer",
            password="reviewer123",
            role=UserRole.REVIEWER
        )
        
        # Create test workspace
        workspace = workspace_service.create_workspace(
            name="Test Workspace",
            description="A test workspace for collaboration features",
            owner_id=admin_user.id,
            is_public=False
        )
        
        # Add members to workspace
        workspace_service.add_member(workspace.id, editor_user.id, UserRole.EDITOR, admin_user.id)
        workspace_service.add_member(workspace.id, reviewer_user.id, UserRole.REVIEWER, admin_user.id)
        
        # Create test approval workflow
        workflow = approval_service.create_workflow(
            name="Standard Review",
            description="Standard prompt review workflow",
            required_approvers=1,
            approver_roles=[UserRole.REVIEWER, UserRole.ADMIN],
            created_by=admin_user.id,
            steps=["Security scan", "Quality review", "Final approval"]
        )
        
        # Create test approval request
        approval_service.submit_for_approval(
            workflow_id=workflow.id,
            prompt_id="test_prompt_001",
            prompt_version_id="v1.0",
            requested_by=editor_user.id,
            reason="New prompt for customer service",
            priority="normal"
        )
        
        print("Test data created successfully!")
        return admin_user.id
        
    except Exception as e:
        print(f"Error setting up test data: {e}")
        return "admin"


def main():
    """Main test function."""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create main window
    root = tk.Tk()
    root.title("Collaboration UI Test")
    root.geometry("1200x800")
    
    try:
        # Initialize database and services
        from pathlib import Path
        db_path = Path("test_collaboration.db")
        db_manager = DatabaseManager(db_path)
        db_manager.initialize()
        
        workspace_service = WorkspaceManagementService(db_manager)
        user_service = UserManagementService(db_manager)
        approval_service = ApprovalWorkflowService(db_manager)
        
        # Set up test data
        current_user_id = setup_test_data(workspace_service, user_service, approval_service)
        
        # Create collaboration page
        collaboration_page = CollaborationPage(
            parent=root,
            workspace_service=workspace_service,
            user_service=user_service,
            approval_service=approval_service,
            current_user_id=current_user_id
        )
        
        # Add menu bar for testing
        menubar = tk.Menu(root)
        root.config(menu=menubar)
        
        test_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Test", menu=test_menu)
        test_menu.add_command(label="Refresh All", command=lambda: [
            collaboration_page.refresh_workspaces(),
            collaboration_page.refresh_members(),
            collaboration_page.refresh_approval_queue()
        ])
        test_menu.add_separator()
        test_menu.add_command(label="Exit", command=root.quit)
        
        print("Collaboration UI test started successfully!")
        print("Features to test:")
        print("- Workspace selection and management")
        print("- Team member management")
        print("- Approval queue and workflow actions")
        print("- Workflow configuration")
        print("- Workflow status and statistics")
        
        # Start the GUI
        root.mainloop()
        
    except Exception as e:
        print(f"Error running collaboration UI test: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()