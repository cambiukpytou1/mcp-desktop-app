"""
Collaboration Page for MCP Admin Application
===========================================

UI component for workspace management and team collaboration features.
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import Dict, List, Optional, Callable
import logging

from models.collaboration import Workspace, User, UserRole, WorkflowStatus
from services.collaboration.workspace_management import WorkspaceManagementService
from services.collaboration.user_management import UserManagementService
from services.collaboration.approval_workflow import ApprovalWorkflowService


class CollaborationPage:
    """Main collaboration interface for workspace and team management."""
    
    def __init__(self, parent, workspace_service: WorkspaceManagementService,
                 user_service: UserManagementService, 
                 approval_service: ApprovalWorkflowService,
                 current_user_id: str = "admin"):
        """Initialize the collaboration page."""
        self.parent = parent
        self.workspace_service = workspace_service
        self.user_service = user_service
        self.approval_service = approval_service
        self.current_user_id = current_user_id
        self.logger = logging.getLogger(__name__)
        
        # State
        self.current_workspace: Optional[Workspace] = None
        self.workspaces: List[Workspace] = []
        self.workspace_members: List[Dict] = []
        
        # UI components
        self.main_frame = None
        self.workspace_selector = None
        self.workspace_info_frame = None
        self.members_tree = None
        self.approval_queue_tree = None
        
        self.setup_ui()
        self.refresh_workspaces()
    
    def setup_ui(self):
        """Set up the collaboration interface."""
        # Main container
        self.main_frame = ttk.Frame(self.parent)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create notebook for different sections
        notebook = ttk.Notebook(self.main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Workspace Management tab
        workspace_frame = ttk.Frame(notebook)
        notebook.add(workspace_frame, text="Workspace Management")
        self.setup_workspace_management(workspace_frame)
        
        # Approval Workflow tab
        approval_frame = ttk.Frame(notebook)
        notebook.add(approval_frame, text="Approval Workflows")
        self.setup_approval_workflows(approval_frame)
    
    def setup_workspace_management(self, parent):
        """Set up workspace management interface."""
        # Workspace selector section
        selector_frame = ttk.LabelFrame(parent, text="Workspace Selection", padding=10)
        selector_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Workspace selector
        selector_row = ttk.Frame(selector_frame)
        selector_row.pack(fill=tk.X)
        
        ttk.Label(selector_row, text="Current Workspace:").pack(side=tk.LEFT)
        
        self.workspace_selector = ttk.Combobox(selector_row, state="readonly", width=30)
        self.workspace_selector.pack(side=tk.LEFT, padx=(10, 0))
        self.workspace_selector.bind("<<ComboboxSelected>>", self.on_workspace_selected)
        
        # Workspace actions
        actions_frame = ttk.Frame(selector_row)
        actions_frame.pack(side=tk.RIGHT)
        
        ttk.Button(actions_frame, text="New Workspace", 
                  command=self.create_workspace).pack(side=tk.LEFT, padx=2)
        ttk.Button(actions_frame, text="Edit Workspace", 
                  command=self.edit_workspace).pack(side=tk.LEFT, padx=2)
        ttk.Button(actions_frame, text="Delete Workspace", 
                  command=self.delete_workspace).pack(side=tk.LEFT, padx=2)
        
        # Main content area
        content_frame = ttk.Frame(parent)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - Workspace info
        left_panel = ttk.LabelFrame(content_frame, text="Workspace Information", padding=10)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        self.workspace_info_frame = ttk.Frame(left_panel)
        self.workspace_info_frame.pack(fill=tk.BOTH, expand=True)
        
        # Right panel - Team members
        right_panel = ttk.LabelFrame(content_frame, text="Team Members", padding=10)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        self.setup_members_section(right_panel)
    
    def setup_members_section(self, parent):
        """Set up team members management section."""
        # Members toolbar
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(toolbar, text="Add Member", 
                  command=self.add_member).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Edit Role", 
                  command=self.edit_member_role).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Remove Member", 
                  command=self.remove_member).pack(side=tk.LEFT, padx=2)
        
        # Members tree
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create treeview with scrollbar
        tree_scroll = ttk.Scrollbar(tree_frame)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.members_tree = ttk.Treeview(tree_frame, yscrollcommand=tree_scroll.set,
                                        columns=("username", "email", "role", "added_date"),
                                        show="tree headings")
        tree_scroll.config(command=self.members_tree.yview)
        
        # Configure columns
        self.members_tree.heading("#0", text="Full Name")
        self.members_tree.heading("username", text="Username")
        self.members_tree.heading("email", text="Email")
        self.members_tree.heading("role", text="Role")
        self.members_tree.heading("added_date", text="Added Date")
        
        self.members_tree.column("#0", width=150)
        self.members_tree.column("username", width=120)
        self.members_tree.column("email", width=180)
        self.members_tree.column("role", width=100)
        self.members_tree.column("added_date", width=120)
        
        self.members_tree.pack(fill=tk.BOTH, expand=True)
    
    def setup_approval_workflows(self, parent):
        """Set up approval workflows interface."""
        # Approval queue section
        queue_frame = ttk.LabelFrame(parent, text="Approval Queue", padding=10)
        queue_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Queue toolbar
        queue_toolbar = ttk.Frame(queue_frame)
        queue_toolbar.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(queue_toolbar, text="Approve Selected", 
                  command=self.approve_request).pack(side=tk.LEFT, padx=2)
        ttk.Button(queue_toolbar, text="Reject Selected", 
                  command=self.reject_request).pack(side=tk.LEFT, padx=2)
        ttk.Button(queue_toolbar, text="View Details", 
                  command=self.view_approval_details).pack(side=tk.LEFT, padx=2)
        ttk.Button(queue_toolbar, text="Refresh", 
                  command=self.refresh_approval_queue).pack(side=tk.RIGHT)
        
        # Approval queue tree
        queue_tree_frame = ttk.Frame(queue_frame)
        queue_tree_frame.pack(fill=tk.BOTH, expand=True)
        
        queue_scroll = ttk.Scrollbar(queue_tree_frame)
        queue_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.approval_queue_tree = ttk.Treeview(queue_tree_frame, yscrollcommand=queue_scroll.set,
                                               columns=("prompt", "requested_by", "priority", "status", "date"),
                                               show="tree headings")
        queue_scroll.config(command=self.approval_queue_tree.yview)
        
        # Configure approval queue columns
        self.approval_queue_tree.heading("#0", text="Request ID")
        self.approval_queue_tree.heading("prompt", text="Prompt")
        self.approval_queue_tree.heading("requested_by", text="Requested By")
        self.approval_queue_tree.heading("priority", text="Priority")
        self.approval_queue_tree.heading("status", text="Status")
        self.approval_queue_tree.heading("date", text="Request Date")
        
        self.approval_queue_tree.column("#0", width=120)
        self.approval_queue_tree.column("prompt", width=200)
        self.approval_queue_tree.column("requested_by", width=120)
        self.approval_queue_tree.column("priority", width=80)
        self.approval_queue_tree.column("status", width=120)
        self.approval_queue_tree.column("date", width=120)
        
        self.approval_queue_tree.pack(fill=tk.BOTH, expand=True)
        
        # Workflow configuration section
        config_frame = ttk.LabelFrame(parent, text="Workflow Configuration", padding=10)
        config_frame.pack(fill=tk.X)
        
        config_toolbar = ttk.Frame(config_frame)
        config_toolbar.pack(fill=tk.X)
        
        ttk.Button(config_toolbar, text="Configure Workflows", 
                  command=self.configure_workflows).pack(side=tk.LEFT, padx=2)
        ttk.Button(config_toolbar, text="View Workflow Status", 
                  command=self.view_workflow_status).pack(side=tk.LEFT, padx=2)
    
    def refresh_workspaces(self):
        """Refresh the workspace list."""
        try:
            self.workspaces = self.workspace_service.list_workspaces(self.current_user_id)
            
            # Update workspace selector
            workspace_names = [f"{ws.name} ({ws.id[:8]})" for ws in self.workspaces]
            self.workspace_selector['values'] = workspace_names
            
            if self.workspaces and not self.current_workspace:
                self.workspace_selector.current(0)
                self.on_workspace_selected()
                
        except Exception as e:
            self.logger.error(f"Error refreshing workspaces: {e}")
            messagebox.showerror("Error", f"Failed to refresh workspaces: {e}")
    
    def on_workspace_selected(self, event=None):
        """Handle workspace selection."""
        try:
            selection = self.workspace_selector.current()
            if selection >= 0 and selection < len(self.workspaces):
                self.current_workspace = self.workspaces[selection]
                self.refresh_workspace_info()
                self.refresh_members()
                self.refresh_approval_queue()
                
        except Exception as e:
            self.logger.error(f"Error selecting workspace: {e}")
    
    def refresh_workspace_info(self):
        """Refresh workspace information display."""
        # Clear existing info
        for widget in self.workspace_info_frame.winfo_children():
            widget.destroy()
        
        if not self.current_workspace:
            ttk.Label(self.workspace_info_frame, 
                     text="No workspace selected").pack(pady=20)
            return
        
        # Display workspace information
        info_text = f"""
Name: {self.current_workspace.name}
Description: {self.current_workspace.description}
Owner: {self.current_workspace.owner_id}
Public: {'Yes' if self.current_workspace.is_public else 'No'}
Created: {self.current_workspace.created_at.strftime('%Y-%m-%d %H:%M')}
Updated: {self.current_workspace.updated_at.strftime('%Y-%m-%d %H:%M')}
        """.strip()
        
        ttk.Label(self.workspace_info_frame, text=info_text, 
                 justify=tk.LEFT).pack(anchor=tk.W, pady=10)
        
        # Workspace settings
        settings_frame = ttk.LabelFrame(self.workspace_info_frame, text="Settings", padding=10)
        settings_frame.pack(fill=tk.X, pady=10)
        
        for key, value in self.current_workspace.settings.items():
            setting_row = ttk.Frame(settings_frame)
            setting_row.pack(fill=tk.X, pady=2)
            ttk.Label(setting_row, text=f"{key}:").pack(side=tk.LEFT)
            ttk.Label(setting_row, text=str(value)).pack(side=tk.RIGHT)
    
    def refresh_members(self):
        """Refresh team members list."""
        # Clear existing items
        for item in self.members_tree.get_children():
            self.members_tree.delete(item)
        
        if not self.current_workspace:
            return
        
        try:
            self.workspace_members = self.workspace_service.get_members(self.current_workspace.id)
            
            for member in self.workspace_members:
                self.members_tree.insert("", tk.END,
                                       text=member.get('full_name', 'Unknown'),
                                       values=(
                                           member.get('username', ''),
                                           member.get('email', ''),
                                           member.get('role', ''),
                                           member.get('added_at', '')[:10] if member.get('added_at') else ''
                                       ))
                
        except Exception as e:
            self.logger.error(f"Error refreshing members: {e}")
    
    def refresh_approval_queue(self):
        """Refresh approval queue."""
        # Clear existing items
        for item in self.approval_queue_tree.get_children():
            self.approval_queue_tree.delete(item)
        
        if not self.current_workspace:
            return
        
        try:
            # Get pending approval requests (all pending requests for now)
            requests = self.approval_service.list_requests(status=WorkflowStatus.PENDING_REVIEW)
            
            for request in requests:
                self.approval_queue_tree.insert("", tk.END,
                                               text=request.id[:8],
                                               values=(
                                                   request.prompt_id[:20] + "..." if len(request.prompt_id) > 20 else request.prompt_id,
                                                   request.requested_by,
                                                   request.priority,
                                                   request.status.value,
                                                   request.requested_at.strftime('%Y-%m-%d')
                                               ))
                
        except Exception as e:
            self.logger.error(f"Error refreshing approval queue: {e}")
    
    def create_workspace(self):
        """Create a new workspace."""
        dialog = WorkspaceDialog(self.parent, "Create Workspace")
        if dialog.result:
            try:
                workspace = self.workspace_service.create_workspace(
                    name=dialog.result['name'],
                    description=dialog.result['description'],
                    owner_id=self.current_user_id,
                    is_public=dialog.result['is_public']
                )
                
                messagebox.showinfo("Success", f"Workspace '{workspace.name}' created successfully!")
                self.refresh_workspaces()
                
            except Exception as e:
                self.logger.error(f"Error creating workspace: {e}")
                messagebox.showerror("Error", f"Failed to create workspace: {e}")
    
    def edit_workspace(self):
        """Edit current workspace."""
        if not self.current_workspace:
            messagebox.showwarning("Warning", "No workspace selected")
            return
        
        dialog = WorkspaceDialog(self.parent, "Edit Workspace", self.current_workspace)
        if dialog.result:
            try:
                success = self.workspace_service.update_workspace(
                    self.current_workspace.id,
                    dialog.result
                )
                
                if success:
                    messagebox.showinfo("Success", "Workspace updated successfully!")
                    self.refresh_workspaces()
                else:
                    messagebox.showerror("Error", "Failed to update workspace")
                    
            except Exception as e:
                self.logger.error(f"Error updating workspace: {e}")
                messagebox.showerror("Error", f"Failed to update workspace: {e}")
    
    def delete_workspace(self):
        """Delete current workspace."""
        if not self.current_workspace:
            messagebox.showwarning("Warning", "No workspace selected")
            return
        
        if messagebox.askyesno("Confirm Delete", 
                              f"Are you sure you want to delete workspace '{self.current_workspace.name}'?\n\n"
                              "This action cannot be undone."):
            try:
                success = self.workspace_service.delete_workspace(self.current_workspace.id)
                
                if success:
                    messagebox.showinfo("Success", "Workspace deleted successfully!")
                    self.current_workspace = None
                    self.refresh_workspaces()
                else:
                    messagebox.showerror("Error", "Failed to delete workspace")
                    
            except Exception as e:
                self.logger.error(f"Error deleting workspace: {e}")
                messagebox.showerror("Error", f"Failed to delete workspace: {e}")
    
    def add_member(self):
        """Add a new member to the workspace."""
        if not self.current_workspace:
            messagebox.showwarning("Warning", "No workspace selected")
            return
        
        dialog = AddMemberDialog(self.parent, self.user_service)
        if dialog.result:
            try:
                success = self.workspace_service.add_member(
                    self.current_workspace.id,
                    dialog.result['user_id'],
                    UserRole(dialog.result['role']),
                    self.current_user_id
                )
                
                if success:
                    messagebox.showinfo("Success", "Member added successfully!")
                    self.refresh_members()
                else:
                    messagebox.showerror("Error", "Failed to add member")
                    
            except Exception as e:
                self.logger.error(f"Error adding member: {e}")
                messagebox.showerror("Error", f"Failed to add member: {e}")
    
    def edit_member_role(self):
        """Edit a member's role."""
        selection = self.members_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a member to edit")
            return
        
        # Get selected member
        item = self.members_tree.item(selection[0])
        username = item['values'][0]
        current_role = item['values'][2]
        
        # Find member in list
        member = next((m for m in self.workspace_members if m['username'] == username), None)
        if not member:
            messagebox.showerror("Error", "Member not found")
            return
        
        # Show role selection dialog
        new_role = simpledialog.askstring("Edit Role", 
                                         f"Enter new role for {username}:\n"
                                         f"Current role: {current_role}\n"
                                         f"Available roles: viewer, editor, reviewer, admin",
                                         initialvalue=current_role)
        
        if new_role and new_role != current_role:
            try:
                if new_role not in ['viewer', 'editor', 'reviewer', 'admin']:
                    messagebox.showerror("Error", "Invalid role. Must be: viewer, editor, reviewer, or admin")
                    return
                
                success = self.workspace_service.update_member_role(
                    self.current_workspace.id,
                    member['user_id'],
                    UserRole(new_role)
                )
                
                if success:
                    messagebox.showinfo("Success", f"Role updated to {new_role}")
                    self.refresh_members()
                else:
                    messagebox.showerror("Error", "Failed to update role")
                    
            except Exception as e:
                self.logger.error(f"Error updating member role: {e}")
                messagebox.showerror("Error", f"Failed to update role: {e}")
    
    def remove_member(self):
        """Remove a member from the workspace."""
        selection = self.members_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a member to remove")
            return
        
        # Get selected member
        item = self.members_tree.item(selection[0])
        username = item['values'][0]
        
        # Find member in list
        member = next((m for m in self.workspace_members if m['username'] == username), None)
        if not member:
            messagebox.showerror("Error", "Member not found")
            return
        
        if messagebox.askyesno("Confirm Remove", 
                              f"Are you sure you want to remove {username} from this workspace?"):
            try:
                success = self.workspace_service.remove_member(
                    self.current_workspace.id,
                    member['user_id']
                )
                
                if success:
                    messagebox.showinfo("Success", "Member removed successfully!")
                    self.refresh_members()
                else:
                    messagebox.showerror("Error", "Failed to remove member")
                    
            except Exception as e:
                self.logger.error(f"Error removing member: {e}")
                messagebox.showerror("Error", f"Failed to remove member: {e}")
    
    def approve_request(self):
        """Approve selected approval request."""
        selection = self.approval_queue_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a request to approve")
            return
        
        # Get selected request
        item = self.approval_queue_tree.item(selection[0])
        request_id = item['text']
        
        # Show approval comment dialog
        comment = simpledialog.askstring("Approval Comment", 
                                        "Enter approval comment (optional):")
        
        try:
            success = self.approval_service.approve_request(
                request_id, self.current_user_id, comment or ""
            )
            
            if success:
                messagebox.showinfo("Success", "Request approved successfully!")
                self.refresh_approval_queue()
            else:
                messagebox.showerror("Error", "Failed to approve request")
                
        except Exception as e:
            self.logger.error(f"Error approving request: {e}")
            messagebox.showerror("Error", f"Failed to approve request: {e}")
    
    def reject_request(self):
        """Reject selected approval request."""
        selection = self.approval_queue_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a request to reject")
            return
        
        # Get selected request
        item = self.approval_queue_tree.item(selection[0])
        request_id = item['text']
        
        # Show rejection reason dialog
        reason = simpledialog.askstring("Rejection Reason", 
                                       "Enter rejection reason (required):")
        
        if not reason:
            messagebox.showwarning("Warning", "Rejection reason is required")
            return
        
        try:
            success = self.approval_service.reject_request(
                request_id, self.current_user_id, reason
            )
            
            if success:
                messagebox.showinfo("Success", "Request rejected successfully!")
                self.refresh_approval_queue()
            else:
                messagebox.showerror("Error", "Failed to reject request")
                
        except Exception as e:
            self.logger.error(f"Error rejecting request: {e}")
            messagebox.showerror("Error", f"Failed to reject request: {e}")
    
    def view_approval_details(self):
        """View details of selected approval request."""
        selection = self.approval_queue_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a request to view")
            return
        
        # Get selected request
        item = self.approval_queue_tree.item(selection[0])
        request_id = item['text']
        
        try:
            request = self.approval_service.get_request(request_id)
            if request:
                ApprovalDetailsDialog(self.parent, request)
            else:
                messagebox.showerror("Error", "Request not found")
                
        except Exception as e:
            self.logger.error(f"Error viewing request details: {e}")
            messagebox.showerror("Error", f"Failed to load request details: {e}")
    
    def configure_workflows(self):
        """Configure approval workflows."""
        try:
            WorkflowConfigurationDialog(self.parent, self.approval_service, self.current_user_id)
        except Exception as e:
            self.logger.error(f"Error opening workflow configuration: {e}")
            messagebox.showerror("Error", f"Failed to open workflow configuration: {e}")
    
    def view_workflow_status(self):
        """View workflow status and statistics."""
        try:
            WorkflowStatusDialog(self.parent, self.approval_service)
        except Exception as e:
            self.logger.error(f"Error opening workflow status: {e}")
            messagebox.showerror("Error", f"Failed to open workflow status: {e}")


class WorkspaceDialog:
    """Dialog for creating/editing workspaces."""
    
    def __init__(self, parent, title, workspace=None):
        self.result = None
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        # Form fields
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Name field
        ttk.Label(main_frame, text="Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.name_var = tk.StringVar(value=workspace.name if workspace else "")
        name_entry = ttk.Entry(main_frame, textvariable=self.name_var, width=40)
        name_entry.grid(row=0, column=1, pady=5, padx=(10, 0))
        
        # Description field
        ttk.Label(main_frame, text="Description:").grid(row=1, column=0, sticky=tk.NW, pady=5)
        self.description_text = tk.Text(main_frame, width=40, height=6)
        self.description_text.grid(row=1, column=1, pady=5, padx=(10, 0))
        if workspace:
            self.description_text.insert(tk.END, workspace.description)
        
        # Public checkbox
        self.is_public_var = tk.BooleanVar(value=workspace.is_public if workspace else False)
        public_check = ttk.Checkbutton(main_frame, text="Public workspace", 
                                      variable=self.is_public_var)
        public_check.grid(row=2, column=1, sticky=tk.W, pady=10, padx=(10, 0))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="OK", command=self.ok_clicked).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel_clicked).pack(side=tk.LEFT, padx=5)
        
        # Focus on name field
        name_entry.focus()
        
        # Wait for dialog to close
        self.dialog.wait_window()
    
    def ok_clicked(self):
        """Handle OK button click."""
        name = self.name_var.get().strip()
        description = self.description_text.get(1.0, tk.END).strip()
        
        if not name:
            messagebox.showerror("Error", "Name is required")
            return
        
        self.result = {
            'name': name,
            'description': description,
            'is_public': self.is_public_var.get()
        }
        
        self.dialog.destroy()
    
    def cancel_clicked(self):
        """Handle Cancel button click."""
        self.dialog.destroy()


class AddMemberDialog:
    """Dialog for adding members to workspace."""
    
    def __init__(self, parent, user_service: UserManagementService):
        self.result = None
        self.user_service = user_service
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Add Member")
        self.dialog.geometry("350x200")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        # Form fields
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # User selection
        ttk.Label(main_frame, text="User:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.user_combo = ttk.Combobox(main_frame, state="readonly", width=30)
        self.user_combo.grid(row=0, column=1, pady=5, padx=(10, 0))
        
        # Load users
        self.load_users()
        
        # Role selection
        ttk.Label(main_frame, text="Role:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.role_combo = ttk.Combobox(main_frame, state="readonly", width=30)
        self.role_combo['values'] = ['viewer', 'editor', 'reviewer', 'admin']
        self.role_combo.current(0)  # Default to viewer
        self.role_combo.grid(row=1, column=1, pady=5, padx=(10, 0))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="Add", command=self.add_clicked).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel_clicked).pack(side=tk.LEFT, padx=5)
        
        # Wait for dialog to close
        self.dialog.wait_window()
    
    def load_users(self):
        """Load available users."""
        try:
            users = self.user_service.list_users()
            user_options = [f"{user.username} ({user.full_name})" for user in users]
            self.user_combo['values'] = user_options
            self.users = users  # Store for reference
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load users: {e}")
    
    def add_clicked(self):
        """Handle Add button click."""
        user_selection = self.user_combo.current()
        role = self.role_combo.get()
        
        if user_selection < 0:
            messagebox.showerror("Error", "Please select a user")
            return
        
        if not role:
            messagebox.showerror("Error", "Please select a role")
            return
        
        selected_user = self.users[user_selection]
        
        self.result = {
            'user_id': selected_user.id,
            'role': role
        }
        
        self.dialog.destroy()
    
    def cancel_clicked(self):
        """Handle Cancel button click."""
        self.dialog.destroy()


class ApprovalDetailsDialog:
    """Dialog for viewing approval request details."""
    
    def __init__(self, parent, request):
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Approval Request Details")
        self.dialog.geometry("500x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        # Main content
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Request details
        details_text = f"""
Request ID: {request.id}
Prompt ID: {request.prompt_id}
Requested By: {request.requested_by}
Request Date: {request.requested_at.strftime('%Y-%m-%d %H:%M:%S')}
Priority: {request.priority}
Status: {request.status.value}
Reason: {request.reason}

Current Step: {request.current_step}
Approvals: {len(request.approvals)}
Rejections: {len(request.rejections)}
        """.strip()
        
        text_widget = tk.Text(main_frame, wrap=tk.WORD, height=15)
        text_widget.insert(tk.END, details_text)
        text_widget.config(state=tk.DISABLED)
        text_widget.pack(fill=tk.BOTH, expand=True)
        
        # Close button
        ttk.Button(main_frame, text="Close", 
                  command=self.dialog.destroy).pack(pady=10)
        
        # Wait for dialog to close
        self.dialog.wait_window()

class WorkflowConfigurationDialog:
    """Dialog for configuring approval workflows."""
    
    def __init__(self, parent, approval_service: ApprovalWorkflowService, current_user_id: str):
        self.result = None
        self.approval_service = approval_service
        self.current_user_id = current_user_id
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Workflow Configuration")
        self.dialog.geometry("600x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        # Main content
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create notebook for different sections
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Existing workflows tab
        existing_frame = ttk.Frame(notebook)
        notebook.add(existing_frame, text="Existing Workflows")
        self.setup_existing_workflows(existing_frame)
        
        # Create workflow tab
        create_frame = ttk.Frame(notebook)
        notebook.add(create_frame, text="Create Workflow")
        self.setup_create_workflow(create_frame)
        
        # Close button
        ttk.Button(main_frame, text="Close", 
                  command=self.dialog.destroy).pack(pady=10)
        
        # Load existing workflows
        self.refresh_workflows()
        
        # Wait for dialog to close
        self.dialog.wait_window()
    
    def setup_existing_workflows(self, parent):
        """Set up existing workflows display."""
        # Toolbar
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill=tk.X, pady=(10, 10))
        
        ttk.Button(toolbar, text="Refresh", 
                  command=self.refresh_workflows).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Edit Selected", 
                  command=self.edit_workflow).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Delete Selected", 
                  command=self.delete_workflow).pack(side=tk.LEFT, padx=2)
        
        # Workflows tree
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        tree_scroll = ttk.Scrollbar(tree_frame)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.workflows_tree = ttk.Treeview(tree_frame, yscrollcommand=tree_scroll.set,
                                          columns=("description", "approvers", "roles", "active"),
                                          show="tree headings")
        tree_scroll.config(command=self.workflows_tree.yview)
        
        # Configure columns
        self.workflows_tree.heading("#0", text="Name")
        self.workflows_tree.heading("description", text="Description")
        self.workflows_tree.heading("approvers", text="Required Approvers")
        self.workflows_tree.heading("roles", text="Approver Roles")
        self.workflows_tree.heading("active", text="Active")
        
        self.workflows_tree.column("#0", width=150)
        self.workflows_tree.column("description", width=200)
        self.workflows_tree.column("approvers", width=120)
        self.workflows_tree.column("roles", width=150)
        self.workflows_tree.column("active", width=80)
        
        self.workflows_tree.pack(fill=tk.BOTH, expand=True)
    
    def setup_create_workflow(self, parent):
        """Set up create workflow form."""
        # Form fields
        form_frame = ttk.Frame(parent, padding=10)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Name field
        ttk.Label(form_frame, text="Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.name_var = tk.StringVar()
        name_entry = ttk.Entry(form_frame, textvariable=self.name_var, width=40)
        name_entry.grid(row=0, column=1, pady=5, padx=(10, 0), sticky=tk.W)
        
        # Description field
        ttk.Label(form_frame, text="Description:").grid(row=1, column=0, sticky=tk.NW, pady=5)
        self.description_text = tk.Text(form_frame, width=40, height=4)
        self.description_text.grid(row=1, column=1, pady=5, padx=(10, 0), sticky=tk.W)
        
        # Required approvers
        ttk.Label(form_frame, text="Required Approvers:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.approvers_var = tk.StringVar(value="1")
        approvers_spin = ttk.Spinbox(form_frame, from_=1, to=10, textvariable=self.approvers_var, width=10)
        approvers_spin.grid(row=2, column=1, pady=5, padx=(10, 0), sticky=tk.W)
        
        # Approver roles
        ttk.Label(form_frame, text="Approver Roles:").grid(row=3, column=0, sticky=tk.NW, pady=5)
        roles_frame = ttk.Frame(form_frame)
        roles_frame.grid(row=3, column=1, pady=5, padx=(10, 0), sticky=tk.W)
        
        self.role_vars = {}
        for role in ['viewer', 'editor', 'reviewer', 'admin']:
            var = tk.BooleanVar(value=(role == 'reviewer'))
            self.role_vars[role] = var
            ttk.Checkbutton(roles_frame, text=role.title(), variable=var).pack(anchor=tk.W)
        
        # Workflow steps
        ttk.Label(form_frame, text="Workflow Steps:").grid(row=4, column=0, sticky=tk.NW, pady=5)
        self.steps_text = tk.Text(form_frame, width=40, height=6)
        self.steps_text.grid(row=4, column=1, pady=5, padx=(10, 0), sticky=tk.W)
        self.steps_text.insert(tk.END, "1. Security scan\n2. Quality review\n3. Final approval")
        
        # Create button
        ttk.Button(form_frame, text="Create Workflow", 
                  command=self.create_workflow).grid(row=5, column=1, pady=20, sticky=tk.W)
    
    def refresh_workflows(self):
        """Refresh workflows list."""
        if not hasattr(self, 'workflows_tree'):
            return
        
        # Clear existing items
        for item in self.workflows_tree.get_children():
            self.workflows_tree.delete(item)
        
        try:
            workflows = self.approval_service.list_workflows(active_only=False)
            
            for workflow in workflows:
                roles_text = ", ".join([role.value for role in workflow.approver_roles])
                
                self.workflows_tree.insert("", tk.END,
                                         text=workflow.name,
                                         values=(
                                             workflow.description[:50] + "..." if len(workflow.description) > 50 else workflow.description,
                                             str(workflow.required_approvers),
                                             roles_text,
                                             "Yes" if workflow.is_active else "No"
                                         ))
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load workflows: {e}")
    
    def create_workflow(self):
        """Create a new workflow."""
        name = self.name_var.get().strip()
        description = self.description_text.get(1.0, tk.END).strip()
        
        if not name:
            messagebox.showerror("Error", "Name is required")
            return
        
        try:
            required_approvers = int(self.approvers_var.get())
        except ValueError:
            messagebox.showerror("Error", "Required approvers must be a number")
            return
        
        # Get selected roles
        selected_roles = []
        for role, var in self.role_vars.items():
            if var.get():
                selected_roles.append(UserRole(role))
        
        if not selected_roles:
            messagebox.showerror("Error", "At least one approver role must be selected")
            return
        
        # Get workflow steps
        steps_text = self.steps_text.get(1.0, tk.END).strip()
        steps = [step.strip() for step in steps_text.split('\n') if step.strip()]
        
        try:
            workflow = self.approval_service.create_workflow(
                name=name,
                description=description,
                required_approvers=required_approvers,
                approver_roles=selected_roles,
                created_by=self.current_user_id,
                steps=steps
            )
            
            messagebox.showinfo("Success", f"Workflow '{workflow.name}' created successfully!")
            self.refresh_workflows()
            
            # Clear form
            self.name_var.set("")
            self.description_text.delete(1.0, tk.END)
            self.approvers_var.set("1")
            for var in self.role_vars.values():
                var.set(False)
            self.role_vars['reviewer'].set(True)
            self.steps_text.delete(1.0, tk.END)
            self.steps_text.insert(tk.END, "1. Security scan\n2. Quality review\n3. Final approval")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create workflow: {e}")
    
    def edit_workflow(self):
        """Edit selected workflow."""
        selection = self.workflows_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a workflow to edit")
            return
        
        messagebox.showinfo("Info", "Workflow editing feature coming soon!")
    
    def delete_workflow(self):
        """Delete selected workflow."""
        selection = self.workflows_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a workflow to delete")
            return
        
        messagebox.showinfo("Info", "Workflow deletion feature coming soon!")


class WorkflowStatusDialog:
    """Dialog for viewing workflow status and statistics."""
    
    def __init__(self, parent, approval_service: ApprovalWorkflowService):
        self.approval_service = approval_service
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Workflow Status")
        self.dialog.geometry("700x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        # Main content
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Statistics section
        stats_frame = ttk.LabelFrame(main_frame, text="Workflow Statistics", padding=10)
        stats_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.setup_statistics(stats_frame)
        
        # Recent requests section
        recent_frame = ttk.LabelFrame(main_frame, text="Recent Requests", padding=10)
        recent_frame.pack(fill=tk.BOTH, expand=True)
        
        self.setup_recent_requests(recent_frame)
        
        # Close button
        ttk.Button(main_frame, text="Close", 
                  command=self.dialog.destroy).pack(pady=10)
        
        # Load data
        self.refresh_data()
        
        # Wait for dialog to close
        self.dialog.wait_window()
    
    def setup_statistics(self, parent):
        """Set up statistics display."""
        # Create statistics labels
        self.stats_labels = {}
        
        stats_grid = ttk.Frame(parent)
        stats_grid.pack(fill=tk.X)
        
        # Row 1
        ttk.Label(stats_grid, text="Total Requests:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.stats_labels['total'] = ttk.Label(stats_grid, text="0")
        self.stats_labels['total'].grid(row=0, column=1, sticky=tk.W, padx=5)
        
        ttk.Label(stats_grid, text="Pending:").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.stats_labels['pending'] = ttk.Label(stats_grid, text="0")
        self.stats_labels['pending'].grid(row=0, column=3, sticky=tk.W, padx=5)
        
        # Row 2
        ttk.Label(stats_grid, text="Approved:").grid(row=1, column=0, sticky=tk.W, padx=5)
        self.stats_labels['approved'] = ttk.Label(stats_grid, text="0")
        self.stats_labels['approved'].grid(row=1, column=1, sticky=tk.W, padx=5)
        
        ttk.Label(stats_grid, text="Rejected:").grid(row=1, column=2, sticky=tk.W, padx=5)
        self.stats_labels['rejected'] = ttk.Label(stats_grid, text="0")
        self.stats_labels['rejected'].grid(row=1, column=3, sticky=tk.W, padx=5)
        
        # Row 3
        ttk.Label(stats_grid, text="Average Processing Time:").grid(row=2, column=0, sticky=tk.W, padx=5)
        self.stats_labels['avg_time'] = ttk.Label(stats_grid, text="N/A")
        self.stats_labels['avg_time'].grid(row=2, column=1, sticky=tk.W, padx=5)
        
        ttk.Label(stats_grid, text="Active Workflows:").grid(row=2, column=2, sticky=tk.W, padx=5)
        self.stats_labels['workflows'] = ttk.Label(stats_grid, text="0")
        self.stats_labels['workflows'].grid(row=2, column=3, sticky=tk.W, padx=5)
    
    def setup_recent_requests(self, parent):
        """Set up recent requests display."""
        # Recent requests tree
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        tree_scroll = ttk.Scrollbar(tree_frame)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.recent_tree = ttk.Treeview(tree_frame, yscrollcommand=tree_scroll.set,
                                       columns=("prompt", "requested_by", "status", "date", "workflow"),
                                       show="tree headings")
        tree_scroll.config(command=self.recent_tree.yview)
        
        # Configure columns
        self.recent_tree.heading("#0", text="Request ID")
        self.recent_tree.heading("prompt", text="Prompt")
        self.recent_tree.heading("requested_by", text="Requested By")
        self.recent_tree.heading("status", text="Status")
        self.recent_tree.heading("date", text="Date")
        self.recent_tree.heading("workflow", text="Workflow")
        
        self.recent_tree.column("#0", width=100)
        self.recent_tree.column("prompt", width=150)
        self.recent_tree.column("requested_by", width=120)
        self.recent_tree.column("status", width=100)
        self.recent_tree.column("date", width=100)
        self.recent_tree.column("workflow", width=120)
        
        self.recent_tree.pack(fill=tk.BOTH, expand=True)
    
    def refresh_data(self):
        """Refresh statistics and recent requests."""
        try:
            # Get all requests for statistics
            all_requests = self.approval_service.list_requests()
            
            # Calculate statistics
            total_requests = len(all_requests)
            pending_requests = len([r for r in all_requests if r.status == WorkflowStatus.PENDING_REVIEW])
            approved_requests = len([r for r in all_requests if r.status == WorkflowStatus.APPROVED])
            rejected_requests = len([r for r in all_requests if r.status == WorkflowStatus.REJECTED])
            
            # Update statistics labels
            self.stats_labels['total'].config(text=str(total_requests))
            self.stats_labels['pending'].config(text=str(pending_requests))
            self.stats_labels['approved'].config(text=str(approved_requests))
            self.stats_labels['rejected'].config(text=str(rejected_requests))
            
            # Calculate average processing time
            completed_requests = [r for r in all_requests if r.completed_at]
            if completed_requests:
                total_time = sum([(r.completed_at - r.requested_at).total_seconds() 
                                for r in completed_requests])
                avg_time_seconds = total_time / len(completed_requests)
                avg_time_hours = avg_time_seconds / 3600
                self.stats_labels['avg_time'].config(text=f"{avg_time_hours:.1f} hours")
            else:
                self.stats_labels['avg_time'].config(text="N/A")
            
            # Get workflow count
            workflows = self.approval_service.list_workflows()
            self.stats_labels['workflows'].config(text=str(len(workflows)))
            
            # Update recent requests (last 20)
            for item in self.recent_tree.get_children():
                self.recent_tree.delete(item)
            
            recent_requests = all_requests[:20]  # Already sorted by date DESC
            for request in recent_requests:
                workflow = self.approval_service.get_workflow(request.workflow_id)
                workflow_name = workflow.name if workflow else "Unknown"
                
                self.recent_tree.insert("", tk.END,
                                       text=request.id[:8],
                                       values=(
                                           request.prompt_id[:20] + "..." if len(request.prompt_id) > 20 else request.prompt_id,
                                           request.requested_by,
                                           request.status.value,
                                           request.requested_at.strftime('%Y-%m-%d'),
                                           workflow_name
                                       ))
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load workflow status: {e}")