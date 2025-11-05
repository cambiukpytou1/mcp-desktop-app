"""
Version History Widget
======================

Reusable widget for displaying version control history
with diff visualization and rollback capabilities.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import List, Optional, Callable, Dict, Any
from datetime import datetime


class VersionHistoryWidget(tk.Frame):
    """Reusable version history widget with diff display."""
    
    def __init__(self, parent, version_service=None, template_id: Optional[str] = None):
        super().__init__(parent, bg="#ffffff")
        self.version_service = version_service
        self.template_id = template_id
        self.logger = logging.getLogger(__name__)
        
        self.versions: List[Dict[str, Any]] = []
        self.selected_version: Optional[Dict[str, Any]] = None
        
        self._create_widgets()
        if template_id:
            self.load_versions(template_id)
    
    def _create_widgets(self):
        """Create the version history components."""
        # Header
        self._create_header()
        
        # Version list
        self._create_version_list()
        
        # Diff viewer
        self._create_diff_viewer()
        
        # Actions
        self._create_actions()
    
    def _create_header(self):
        """Create the header with title and controls."""
        header_frame = tk.Frame(self, bg="#ffffff")
        header_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        tk.Label(
            header_frame,
            text="Version History",
            font=("Arial", 12, "bold"),
            bg="#ffffff"
        ).pack(side="left")
        
        # Branch selector (placeholder)
        tk.Label(
            header_frame,
            text="Branch:",
            font=("Arial", 10),
            bg="#ffffff"
        ).pack(side="right", padx=(0, 5))
        
        self.branch_var = tk.StringVar(value="main")
        branch_combo = ttk.Combobox(
            header_frame,
            textvariable=self.branch_var,
            values=["main", "development", "feature/new-template"],
            state="readonly",
            width=15
        )
        branch_combo.pack(side="right")
        branch_combo.bind("<<ComboboxSelected>>", self._on_branch_changed)
    
    def _create_version_list(self):
        """Create the scrollable version list."""
        # List header
        list_header = tk.Frame(self, bg="#f8f9fa", bd=1, relief="solid")
        list_header.pack(fill="x", padx=10, pady=(5, 0))
        
        tk.Label(
            list_header,
            text="Versions",
            font=("Arial", 10, "bold"),
            bg="#f8f9fa",
            padx=10,
            pady=5
        ).pack(side="left")
        
        tk.Button(
            list_header,
            text="🔄",
            bg="#f8f9fa",
            fg="#666",
            font=("Arial", 8),
            padx=5,
            pady=2,
            relief="flat",
            cursor="hand2",
            command=self.refresh
        ).pack(side="right", padx=5)
        
        # List container with scrollbar
        list_container = tk.Frame(self, bg="#ffffff")
        list_container.pack(fill="both", expand=True, padx=10, pady=(0, 5))
        
        # Create scrollable frame
        canvas = tk.Canvas(list_container, bg="#ffffff", highlightthickness=0, height=200)
        scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=canvas.yview)
        self.versions_frame = tk.Frame(canvas, bg="#ffffff")
        
        self.versions_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.versions_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def _create_diff_viewer(self):
        """Create the diff viewer section."""
        diff_header = tk.Frame(self, bg="#f8f9fa", bd=1, relief="solid")
        diff_header.pack(fill="x", padx=10, pady=(5, 0))
        
        tk.Label(
            diff_header,
            text="Changes",
            font=("Arial", 10, "bold"),
            bg="#f8f9fa",
            padx=10,
            pady=5
        ).pack(side="left")
        
        # Diff display
        diff_container = tk.Frame(self, bg="#ffffff")
        diff_container.pack(fill="both", expand=True, padx=10, pady=(0, 5))
        
        # Create text widget with scrollbar for diff
        diff_canvas = tk.Canvas(diff_container, bg="#ffffff", highlightthickness=0, height=150)
        diff_scrollbar = ttk.Scrollbar(diff_container, orient="vertical", command=diff_canvas.yview)
        
        self.diff_text = tk.Text(
            diff_canvas,
            bg="#ffffff",
            fg="#333",
            font=("Consolas", 9),
            wrap=tk.NONE,
            state=tk.DISABLED,
            yscrollcommand=diff_scrollbar.set
        )
        
        diff_canvas.create_window((0, 0), window=self.diff_text, anchor="nw")
        diff_canvas.configure(yscrollcommand=diff_scrollbar.set)
        
        diff_canvas.pack(side="left", fill="both", expand=True)
        diff_scrollbar.pack(side="right", fill="y")
    
    def _create_actions(self):
        """Create action buttons."""
        actions_frame = tk.Frame(self, bg="#ffffff")
        actions_frame.pack(fill="x", padx=10, pady=(5, 10))
        
        tk.Button(
            actions_frame,
            text="Rollback to Selected",
            bg="#ff9800",
            fg="white",
            font=("Arial", 9, "bold"),
            padx=12,
            pady=6,
            relief="flat",
            cursor="hand2",
            command=self._rollback_to_selected
        ).pack(side="left", padx=(0, 5))
        
        tk.Button(
            actions_frame,
            text="Create Branch",
            bg="#1a73e8",
            fg="white",
            font=("Arial", 9, "bold"),
            padx=12,
            pady=6,
            relief="flat",
            cursor="hand2",
            command=self._create_branch
        ).pack(side="left", padx=(0, 5))
        
        tk.Button(
            actions_frame,
            text="Compare Versions",
            bg="#34a853",
            fg="white",
            font=("Arial", 9, "bold"),
            padx=12,
            pady=6,
            relief="flat",
            cursor="hand2",
            command=self._compare_versions
        ).pack(side="left")
        
        # Selection info
        self.selection_info = tk.Label(
            actions_frame,
            text="No version selected",
            font=("Arial", 9),
            fg="#666",
            bg="#ffffff"
        )
        self.selection_info.pack(side="right")
    
    def _create_version_row(self, version: Dict[str, Any]):
        """Create a version row widget."""
        row = tk.Frame(self.versions_frame, bg="#f8f9fa", bd=1, relief="solid")
        row.pack(fill="x", pady=1)
        
        # Make row clickable
        row.bind("<Button-1>", lambda e: self._select_version(version))
        
        # Version info
        info_frame = tk.Frame(row, bg="#f8f9fa")
        info_frame.pack(side="left", fill="x", expand=True, padx=10, pady=6)
        info_frame.bind("<Button-1>", lambda e: self._select_version(version))
        
        # Version ID and timestamp
        header_frame = tk.Frame(info_frame, bg="#f8f9fa")
        header_frame.pack(fill="x")
        header_frame.bind("<Button-1>", lambda e: self._select_version(version))
        
        version_id = version.get('id', 'unknown')[:8]  # Short hash
        timestamp = version.get('timestamp', datetime.now())
        
        id_label = tk.Label(
            header_frame,
            text=f"#{version_id}",
            font=("Consolas", 10, "bold"),
            bg="#f8f9fa",
            fg="#1a73e8"
        )
        id_label.pack(side="left")
        id_label.bind("<Button-1>", lambda e: self._select_version(version))
        
        time_label = tk.Label(
            header_frame,
            text=timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            font=("Arial", 9),
            bg="#f8f9fa",
            fg="#666"
        )
        time_label.pack(side="right")
        time_label.bind("<Button-1>", lambda e: self._select_version(version))
        
        # Commit message
        message = version.get('message', 'No commit message')
        message_label = tk.Label(
            info_frame,
            text=message,
            font=("Arial", 10),
            bg="#f8f9fa",
            anchor="w"
        )
        message_label.pack(fill="x", pady=(2, 0))
        message_label.bind("<Button-1>", lambda e: self._select_version(version))
        
        # Author and changes
        meta_frame = tk.Frame(info_frame, bg="#f8f9fa")
        meta_frame.pack(fill="x", pady=(2, 0))
        meta_frame.bind("<Button-1>", lambda e: self._select_version(version))
        
        author = version.get('author', 'Unknown')
        changes = version.get('changes_count', 0)
        
        meta_text = f"By {author}"
        if changes > 0:
            meta_text += f" • {changes} changes"
        
        meta_label = tk.Label(
            meta_frame,
            text=meta_text,
            font=("Arial", 9),
            bg="#f8f9fa",
            fg="#999",
            anchor="w"
        )
        meta_label.pack(side="left")
        meta_label.bind("<Button-1>", lambda e: self._select_version(version))
        
        # Current version indicator
        if version.get('is_current', False):
            current_label = tk.Label(
                meta_frame,
                text="CURRENT",
                font=("Arial", 8, "bold"),
                bg="#34a853",
                fg="white",
                padx=4,
                pady=1
            )
            current_label.pack(side="right")
    
    def _select_version(self, version: Dict[str, Any]):
        """Select a version and show its diff."""
        self.selected_version = version
        version_id = version.get('id', 'unknown')[:8]
        self.selection_info.configure(text=f"Selected: #{version_id}")
        
        # Show diff for this version
        self._show_version_diff(version)
        
        self.logger.debug(f"Selected version: {version_id}")
    
    def _show_version_diff(self, version: Dict[str, Any]):
        """Show the diff for the selected version."""
        # Enable text widget for editing
        self.diff_text.configure(state=tk.NORMAL)
        self.diff_text.delete(1.0, tk.END)
        
        # Get diff content (placeholder)
        diff_content = version.get('diff', 'No changes available for this version.')
        
        if not diff_content or diff_content == 'No changes available for this version.':
            # Show placeholder diff
            diff_content = """--- Previous Version
+++ Current Version
@@ -1,3 +1,4 @@
 This is a sample template
-Old content here
+New improved content here
+Additional line added
 End of template"""
        
        self.diff_text.insert(tk.END, diff_content)
        
        # Apply syntax highlighting (basic)
        self._apply_diff_highlighting()
        
        # Disable editing
        self.diff_text.configure(state=tk.DISABLED)
    
    def _apply_diff_highlighting(self):
        """Apply basic syntax highlighting to diff text."""
        # Configure tags for diff highlighting
        self.diff_text.tag_configure("added", foreground="#34a853", background="#e8f5e8")
        self.diff_text.tag_configure("removed", foreground="#d93025", background="#ffebee")
        self.diff_text.tag_configure("header", foreground="#1976d2", font=("Consolas", 9, "bold"))
        self.diff_text.tag_configure("location", foreground="#ff9800", background="#fff3e0")
        
        # Apply tags to lines
        content = self.diff_text.get(1.0, tk.END)
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            line_start = f"{i+1}.0"
            line_end = f"{i+1}.end"
            
            if line.startswith('+++') or line.startswith('---'):
                self.diff_text.tag_add("header", line_start, line_end)
            elif line.startswith('@@'):
                self.diff_text.tag_add("location", line_start, line_end)
            elif line.startswith('+'):
                self.diff_text.tag_add("added", line_start, line_end)
            elif line.startswith('-'):
                self.diff_text.tag_add("removed", line_start, line_end)
    
    def load_versions(self, template_id: str):
        """Load version history for a template."""
        self.template_id = template_id
        self.refresh()
    
    def refresh(self):
        """Refresh the version history."""
        try:
            # Clear existing versions
            for widget in self.versions_frame.winfo_children():
                widget.destroy()
            
            # Get versions from service (placeholder data)
            self.versions = self._get_placeholder_versions()
            
            if not self.versions:
                # Show empty state
                empty_frame = tk.Frame(self.versions_frame, bg="#ffffff")
                empty_frame.pack(fill="both", expand=True, pady=20)
                
                tk.Label(
                    empty_frame,
                    text="No version history available",
                    font=("Arial", 11),
                    fg="#666",
                    bg="#ffffff"
                ).pack()
            else:
                # Create version rows
                for version in self.versions:
                    self._create_version_row(version)
                
                # Auto-select the current version
                current_version = next((v for v in self.versions if v.get('is_current')), None)
                if current_version:
                    self._select_version(current_version)
            
            self.logger.debug(f"Version history refreshed with {len(self.versions)} versions")
            
        except Exception as e:
            self.logger.error(f"Failed to refresh version history: {e}")
            messagebox.showerror("Error", f"Failed to refresh version history: {e}")
    
    def _get_placeholder_versions(self) -> List[Dict[str, Any]]:
        """Get placeholder version data."""
        return [
            {
                'id': 'a1b2c3d4e5f6g7h8',
                'timestamp': datetime.now(),
                'message': 'Initial template creation',
                'author': 'John Doe',
                'changes_count': 1,
                'is_current': True,
                'diff': None
            },
            {
                'id': 'b2c3d4e5f6g7h8i9',
                'timestamp': datetime.now(),
                'message': 'Updated template variables',
                'author': 'Jane Smith',
                'changes_count': 3,
                'is_current': False,
                'diff': None
            },
            {
                'id': 'c3d4e5f6g7h8i9j0',
                'timestamp': datetime.now(),
                'message': 'Fixed template syntax',
                'author': 'Bob Wilson',
                'changes_count': 2,
                'is_current': False,
                'diff': None
            }
        ]
    
    def _on_branch_changed(self, event=None):
        """Handle branch selection change."""
        branch = self.branch_var.get()
        messagebox.showinfo("Branch Changed", f"Switched to branch: {branch}. This will be implemented in subsequent tasks.")
        self.refresh()
    
    # Action handlers (placeholders)
    def _rollback_to_selected(self):
        """Handle rollback to selected version."""
        if not self.selected_version:
            messagebox.showwarning("No Selection", "Please select a version to rollback to.")
            return
        
        version_id = self.selected_version.get('id', 'unknown')[:8]
        if messagebox.askyesno("Confirm Rollback", f"Are you sure you want to rollback to version #{version_id}?"):
            messagebox.showinfo("Coming Soon", "Version rollback will be implemented in subsequent tasks.")
    
    def _create_branch(self):
        """Handle branch creation."""
        messagebox.showinfo("Coming Soon", "Branch creation will be implemented in subsequent tasks.")
    
    def _compare_versions(self):
        """Handle version comparison."""
        messagebox.showinfo("Coming Soon", "Version comparison will be implemented in subsequent tasks.")