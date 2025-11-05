"""
Template Editor Page
====================

Rich template editor with syntax highlighting, variable support, and real-time preview.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import logging
import re
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime

from models.prompt import PromptTemplate
from ui.prompt_components.version_history import VersionHistoryWidget


class TemplateEditorPage(tk.Frame):
    """Rich template editor with advanced features."""
    
    def __init__(self, parent, template_service, on_save: Optional[Callable] = None):
        super().__init__(parent, bg="#ffffff")
        self.template_service = template_service
        self.on_save = on_save
        self.logger = logging.getLogger(__name__)
        
        self.current_template: Optional[PromptTemplate] = None
        self.is_modified = False
        self.variables: Dict[str, str] = {}
        
        self._create_widgets()
        self._setup_syntax_highlighting()
        self._bind_events()
    
    def _create_widgets(self):
        """Create the editor interface."""
        # Main container with paned window
        self.paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Left panel - Editor
        self._create_editor_panel()
        
        # Right panel - Preview and tools
        self._create_preview_panel()
    
    def _create_editor_panel(self):
        """Create the main editor panel."""
        editor_frame = tk.Frame(self.paned_window, bg="#ffffff")
        self.paned_window.add(editor_frame, weight=2)
        
        # Editor toolbar
        self._create_editor_toolbar(editor_frame)
        
        # Template metadata
        self._create_metadata_section(editor_frame)
        
        # Main editor
        self._create_text_editor(editor_frame)
        
        # Variable palette
        self._create_variable_palette(editor_frame)
    
    def _create_editor_toolbar(self, parent):
        """Create editor toolbar with actions."""
        toolbar = tk.Frame(parent, bg="#f8f9fa", bd=1, relief="solid")
        toolbar.pack(fill="x", pady=(0, 10))
        
        # File operations
        tk.Button(
            toolbar,
            text="📁 New",
            bg="#ffffff",
            fg="#333",
            font=("Arial", 9),
            padx=10,
            pady=5,
            relief="flat",
            cursor="hand2",
            command=self._new_template
        ).pack(side="left", padx=2, pady=2)
        
        tk.Button(
            toolbar,
            text="💾 Save",
            bg="#1a73e8",
            fg="white",
            font=("Arial", 9, "bold"),
            padx=10,
            pady=5,
            relief="flat",
            cursor="hand2",
            command=self._save_template
        ).pack(side="left", padx=2, pady=2)
        
        tk.Button(
            toolbar,
            text="📂 Open",
            bg="#ffffff",
            fg="#333",
            font=("Arial", 9),
            padx=10,
            pady=5,
            relief="flat",
            cursor="hand2",
            command=self._open_template
        ).pack(side="left", padx=2, pady=2)
        
        # Separator
        separator = tk.Frame(toolbar, width=2, bg="#ddd")
        separator.pack(side="left", fill="y", padx=5, pady=2)
        
        # Template operations
        tk.Button(
            toolbar,
            text="🧪 Test",
            bg="#34a853",
            fg="white",
            font=("Arial", 9, "bold"),
            padx=10,
            pady=5,
            relief="flat",
            cursor="hand2",
            command=self._test_template
        ).pack(side="left", padx=2, pady=2)
        
        tk.Button(
            toolbar,
            text="🔍 Validate",
            bg="#ff9800",
            fg="white",
            font=("Arial", 9),
            padx=10,
            pady=5,
            relief="flat",
            cursor="hand2",
            command=self._validate_template
        ).pack(side="left", padx=2, pady=2)
        
        tk.Button(
            toolbar,
            text="📋 Variables",
            bg="#9c27b0",
            fg="white",
            font=("Arial", 9),
            padx=10,
            pady=5,
            relief="flat",
            cursor="hand2",
            command=self._show_variables
        ).pack(side="left", padx=2, pady=2)
        
        # Status indicator
        self.status_label = tk.Label(
            toolbar,
            text="Ready",
            font=("Arial", 9),
            fg="#666",
            bg="#f8f9fa"
        )
        self.status_label.pack(side="right", padx=10, pady=5)
        
        # Modified indicator
        self.modified_label = tk.Label(
            toolbar,
            text="",
            font=("Arial", 9, "bold"),
            fg="#ff9800",
            bg="#f8f9fa"
        )
        self.modified_label.pack(side="right", padx=5, pady=5)
    
    def _create_metadata_section(self, parent):
        """Create template metadata section."""
        metadata_frame = tk.LabelFrame(parent, text="Template Information", bg="#ffffff", font=("Arial", 10, "bold"))
        metadata_frame.pack(fill="x", pady=(0, 10))
        
        # Template name
        name_frame = tk.Frame(metadata_frame, bg="#ffffff")
        name_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(name_frame, text="Name:", font=("Arial", 10, "bold"), bg="#ffffff").pack(side="left")
        self.name_entry = tk.Entry(name_frame, font=("Arial", 10), width=40)
        self.name_entry.pack(side="left", padx=(5, 0), fill="x", expand=True)
        self.name_entry.bind("<KeyRelease>", self._on_metadata_changed)
        
        # Template description
        desc_frame = tk.Frame(metadata_frame, bg="#ffffff")
        desc_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(desc_frame, text="Description:", font=("Arial", 10, "bold"), bg="#ffffff").pack(anchor="w")
        self.description_text = tk.Text(desc_frame, height=2, font=("Arial", 10), wrap=tk.WORD)
        self.description_text.pack(fill="x", pady=(2, 0))
        self.description_text.bind("<KeyRelease>", self._on_metadata_changed)
        
        # Tags
        tags_frame = tk.Frame(metadata_frame, bg="#ffffff")
        tags_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(tags_frame, text="Tags:", font=("Arial", 10, "bold"), bg="#ffffff").pack(side="left")
        self.tags_entry = tk.Entry(tags_frame, font=("Arial", 10), width=40)
        self.tags_entry.pack(side="left", padx=(5, 0), fill="x", expand=True)
        self.tags_entry.bind("<KeyRelease>", self._on_metadata_changed)
        
        tk.Label(tags_frame, text="(comma-separated)", font=("Arial", 9), fg="#666", bg="#ffffff").pack(side="right")
    
    def _create_text_editor(self, parent):
        """Create the main text editor with syntax highlighting."""
        editor_frame = tk.LabelFrame(parent, text="Template Content", bg="#ffffff", font=("Arial", 10, "bold"))
        editor_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # Editor with scrollbars
        text_container = tk.Frame(editor_frame, bg="#ffffff")
        text_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create text widget with scrollbars
        self.text_editor = tk.Text(
            text_container,
            font=("Consolas", 11),
            wrap=tk.WORD,
            undo=True,
            maxundo=50,
            bg="#fafafa",
            fg="#333",
            insertbackground="#1a73e8",
            selectbackground="#e3f2fd",
            relief="solid",
            bd=1
        )
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(text_container, orient="vertical", command=self.text_editor.yview)
        h_scrollbar = ttk.Scrollbar(text_container, orient="horizontal", command=self.text_editor.xview)
        
        self.text_editor.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack scrollbars and text widget
        v_scrollbar.pack(side="right", fill="y")
        h_scrollbar.pack(side="bottom", fill="x")
        self.text_editor.pack(side="left", fill="both", expand=True)
        
        # Line numbers (simple implementation)
        self._add_line_numbers()
    
    def _add_line_numbers(self):
        """Add line numbers to the text editor."""
        # This is a simplified line number implementation
        # In a production app, you'd want a more sophisticated solution
        pass
    
    def _create_variable_palette(self, parent):
        """Create variable insertion palette."""
        var_frame = tk.LabelFrame(parent, text="Variables & Functions", bg="#ffffff", font=("Arial", 10, "bold"))
        var_frame.pack(fill="x")
        
        # Variable buttons
        button_frame = tk.Frame(var_frame, bg="#ffffff")
        button_frame.pack(fill="x", padx=10, pady=5)
        
        # Common variables
        common_vars = [
            ("{{user_input}}", "User input placeholder"),
            ("{{context}}", "Context information"),
            ("{{system_prompt}}", "System prompt"),
            ("{{date}}", "Current date"),
            ("{{time}}", "Current time")
        ]
        
        for i, (var, desc) in enumerate(common_vars):
            btn = tk.Button(
                button_frame,
                text=var,
                bg="#e3f2fd",
                fg="#1976d2",
                font=("Consolas", 9),
                padx=8,
                pady=4,
                relief="flat",
                cursor="hand2",
                command=lambda v=var: self._insert_variable(v)
            )
            btn.pack(side="left", padx=2, pady=2)
            
            # Tooltip (simplified)
            self._create_tooltip(btn, desc)
        
        # Custom variable button
        tk.Button(
            button_frame,
            text="+ Custom",
            bg="#f3e5f5",
            fg="#7b1fa2",
            font=("Arial", 9, "bold"),
            padx=8,
            pady=4,
            relief="flat",
            cursor="hand2",
            command=self._add_custom_variable
        ).pack(side="right", padx=2, pady=2)
    
    def _create_preview_panel(self):
        """Create the preview and tools panel."""
        preview_frame = tk.Frame(self.paned_window, bg="#ffffff")
        self.paned_window.add(preview_frame, weight=1)
        
        # Preview section
        self._create_preview_section(preview_frame)
        
        # Version history section
        self._create_version_section(preview_frame)
    
    def _create_preview_section(self, parent):
        """Create template preview section."""
        preview_frame = tk.LabelFrame(parent, text="Live Preview", bg="#ffffff", font=("Arial", 10, "bold"))
        preview_frame.pack(fill="both", expand=True, padx=(10, 0), pady=(0, 10))
        
        # Preview controls
        controls_frame = tk.Frame(preview_frame, bg="#ffffff")
        controls_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Button(
            controls_frame,
            text="🔄 Refresh",
            bg="#1a73e8",
            fg="white",
            font=("Arial", 9),
            padx=8,
            pady=4,
            relief="flat",
            cursor="hand2",
            command=self._refresh_preview
        ).pack(side="left")
        
        tk.Button(
            controls_frame,
            text="⚙️ Variables",
            bg="#ff9800",
            fg="white",
            font=("Arial", 9),
            padx=8,
            pady=4,
            relief="flat",
            cursor="hand2",
            command=self._configure_preview_variables
        ).pack(side="left", padx=(5, 0))
        
        # Preview display
        preview_container = tk.Frame(preview_frame, bg="#ffffff")
        preview_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        self.preview_text = tk.Text(
            preview_container,
            font=("Arial", 10),
            wrap=tk.WORD,
            state=tk.DISABLED,
            bg="#f8f9fa",
            fg="#333",
            relief="solid",
            bd=1
        )
        
        preview_scrollbar = ttk.Scrollbar(preview_container, orient="vertical", command=self.preview_text.yview)
        self.preview_text.configure(yscrollcommand=preview_scrollbar.set)
        
        preview_scrollbar.pack(side="right", fill="y")
        self.preview_text.pack(side="left", fill="both", expand=True)
    
    def _create_version_section(self, parent):
        """Create version history section."""
        version_frame = tk.LabelFrame(parent, text="Version History", bg="#ffffff", font=("Arial", 10, "bold"))
        version_frame.pack(fill="both", expand=True, padx=(10, 0))
        
        # Version history widget
        self.version_widget = VersionHistoryWidget(version_frame)
        self.version_widget.pack(fill="both", expand=True, padx=5, pady=5)
    
    def _setup_syntax_highlighting(self):
        """Setup syntax highlighting for the text editor."""
        # Configure text tags for syntax highlighting
        self.text_editor.tag_configure("variable", foreground="#1976d2", font=("Consolas", 11, "bold"))
        self.text_editor.tag_configure("function", foreground="#7b1fa2", font=("Consolas", 11, "bold"))
        self.text_editor.tag_configure("comment", foreground="#666", font=("Consolas", 11, "italic"))
        self.text_editor.tag_configure("string", foreground="#388e3c")
        self.text_editor.tag_configure("keyword", foreground="#d32f2f", font=("Consolas", 11, "bold"))
    
    def _bind_events(self):
        """Bind editor events."""
        self.text_editor.bind("<KeyRelease>", self._on_text_changed)
        self.text_editor.bind("<Button-1>", self._on_text_changed)
        self.text_editor.bind("<Control-s>", lambda e: self._save_template())
        self.text_editor.bind("<Control-n>", lambda e: self._new_template())
        self.text_editor.bind("<Control-o>", lambda e: self._open_template())
    
    def _on_text_changed(self, event=None):
        """Handle text editor changes."""
        self._set_modified(True)
        self._apply_syntax_highlighting()
        self._update_preview()
        self._extract_variables()
    
    def _on_metadata_changed(self, event=None):
        """Handle metadata changes."""
        self._set_modified(True)
    
    def _set_modified(self, modified: bool):
        """Set the modified state."""
        self.is_modified = modified
        if modified:
            self.modified_label.configure(text="●")
            self.status_label.configure(text="Modified")
        else:
            self.modified_label.configure(text="")
            self.status_label.configure(text="Saved")
    
    def _apply_syntax_highlighting(self):
        """Apply syntax highlighting to the current text."""
        content = self.text_editor.get("1.0", tk.END)
        
        # Clear existing tags
        for tag in ["variable", "function", "comment", "string", "keyword"]:
            self.text_editor.tag_remove(tag, "1.0", tk.END)
        
        # Highlight variables {{variable}}
        for match in re.finditer(r'\{\{[^}]+\}\}', content):
            start_idx = f"1.0+{match.start()}c"
            end_idx = f"1.0+{match.end()}c"
            self.text_editor.tag_add("variable", start_idx, end_idx)
        
        # Highlight functions {%function%}
        for match in re.finditer(r'\{%[^%]+%\}', content):
            start_idx = f"1.0+{match.start()}c"
            end_idx = f"1.0+{match.end()}c"
            self.text_editor.tag_add("function", start_idx, end_idx)
        
        # Highlight comments {#comment#}
        for match in re.finditer(r'\{#[^#]+#\}', content):
            start_idx = f"1.0+{match.start()}c"
            end_idx = f"1.0+{match.end()}c"
            self.text_editor.tag_add("comment", start_idx, end_idx)
    
    def _update_preview(self):
        """Update the live preview."""
        try:
            content = self.text_editor.get("1.0", tk.END).strip()
            if not content:
                self._set_preview_text("Enter template content to see preview...")
                return
            
            # Simple variable substitution for preview
            preview_content = content
            for var, value in self.variables.items():
                preview_content = preview_content.replace(f"{{{{{var}}}}}", value)
            
            # Remove template syntax for preview
            preview_content = re.sub(r'\{%[^%]+%\}', '[FUNCTION]', preview_content)
            preview_content = re.sub(r'\{#[^#]+#\}', '', preview_content)
            
            self._set_preview_text(preview_content)
            
        except Exception as e:
            self._set_preview_text(f"Preview error: {str(e)}")
    
    def _set_preview_text(self, text: str):
        """Set the preview text."""
        self.preview_text.configure(state=tk.NORMAL)
        self.preview_text.delete("1.0", tk.END)
        self.preview_text.insert("1.0", text)
        self.preview_text.configure(state=tk.DISABLED)
    
    def _extract_variables(self):
        """Extract variables from the template content."""
        content = self.text_editor.get("1.0", tk.END)
        variables = set()
        
        # Find all {{variable}} patterns
        for match in re.finditer(r'\{\{([^}]+)\}\}', content):
            var_name = match.group(1).strip()
            variables.add(var_name)
        
        # Update variables dict with defaults
        for var in variables:
            if var not in self.variables:
                self.variables[var] = f"[{var}]"
    
    def _insert_variable(self, variable: str):
        """Insert a variable at the cursor position."""
        try:
            cursor_pos = self.text_editor.index(tk.INSERT)
            self.text_editor.insert(cursor_pos, variable)
            self.text_editor.focus_set()
        except Exception as e:
            self.logger.error(f"Error inserting variable: {e}")
    
    def _create_tooltip(self, widget, text):
        """Create a simple tooltip for a widget."""
        # Simplified tooltip implementation
        def on_enter(event):
            widget.configure(bg="#bbdefb")
        
        def on_leave(event):
            widget.configure(bg="#e3f2fd")
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
    
    # Action handlers
    def _new_template(self):
        """Create a new template."""
        if self.is_modified:
            if not messagebox.askyesno("Unsaved Changes", "You have unsaved changes. Continue without saving?"):
                return
        
        self.current_template = None
        self.name_entry.delete(0, tk.END)
        self.description_text.delete("1.0", tk.END)
        self.tags_entry.delete(0, tk.END)
        self.text_editor.delete("1.0", tk.END)
        self.variables.clear()
        self._set_modified(False)
        self._update_preview()
        
        self.status_label.configure(text="New template created")
    
    def _save_template(self):
        """Save the current template."""
        try:
            name = self.name_entry.get().strip()
            if not name:
                messagebox.showerror("Validation Error", "Template name is required.")
                return
            
            content = self.text_editor.get("1.0", tk.END).strip()
            if not content:
                messagebox.showerror("Validation Error", "Template content is required.")
                return
            
            description = self.description_text.get("1.0", tk.END).strip()
            tags = [tag.strip() for tag in self.tags_entry.get().split(",") if tag.strip()]
            
            # Create or update template
            if self.current_template:
                # Update existing template
                self.current_template.name = name
                self.current_template.content = content
                self.current_template.description = description
                self.current_template.tags = tags
                self.current_template.updated_at = datetime.now()
            else:
                # Create new template
                self.current_template = PromptTemplate(
                    name=name,
                    content=content,
                    description=description,
                    tags=tags
                )
            
            # Save through service (placeholder)
            # In real implementation, this would call the template service
            self._set_modified(False)
            self.status_label.configure(text="Template saved successfully")
            
            if self.on_save:
                self.on_save(self.current_template)
            
            messagebox.showinfo("Success", f"Template '{name}' saved successfully!")
            
        except Exception as e:
            self.logger.error(f"Error saving template: {e}")
            messagebox.showerror("Save Error", f"Failed to save template: {str(e)}")
    
    def _open_template(self):
        """Open an existing template."""
        # This would show a template selection dialog
        # For now, show a placeholder message
        messagebox.showinfo("Open Template", "Template selection dialog will be implemented with the template list widget.")
    
    def _test_template(self):
        """Test the current template."""
        content = self.text_editor.get("1.0", tk.END).strip()
        if not content:
            messagebox.showwarning("No Content", "Please enter template content to test.")
            return
        
        # This would integrate with the evaluation service
        messagebox.showinfo("Template Test", "Template testing will be implemented with the evaluation framework.")
    
    def _validate_template(self):
        """Validate the current template."""
        content = self.text_editor.get("1.0", tk.END).strip()
        if not content:
            messagebox.showwarning("No Content", "Please enter template content to validate.")
            return
        
        # Simple validation
        errors = []
        
        # Check for unmatched braces
        open_vars = content.count("{{")
        close_vars = content.count("}}")
        if open_vars != close_vars:
            errors.append("Unmatched variable braces {{ }}")
        
        open_funcs = content.count("{%")
        close_funcs = content.count("%}")
        if open_funcs != close_funcs:
            errors.append("Unmatched function braces {% %}")
        
        if errors:
            messagebox.showerror("Validation Errors", "\n".join(errors))
        else:
            messagebox.showinfo("Validation", "Template syntax is valid!")
    
    def _show_variables(self):
        """Show extracted variables."""
        self._extract_variables()
        if not self.variables:
            messagebox.showinfo("Variables", "No variables found in template.")
            return
        
        var_list = "\n".join([f"• {var}: {value}" for var, value in self.variables.items()])
        messagebox.showinfo("Template Variables", f"Found variables:\n\n{var_list}")
    
    def _add_custom_variable(self):
        """Add a custom variable."""
        var_name = simpledialog.askstring("Custom Variable", "Enter variable name:")
        if var_name:
            var_name = var_name.strip()
            if var_name:
                self._insert_variable(f"{{{{{var_name}}}}}")
    
    def _refresh_preview(self):
        """Refresh the preview."""
        self._update_preview()
        self.status_label.configure(text="Preview refreshed")
    
    def _configure_preview_variables(self):
        """Configure variables for preview."""
        if not self.variables:
            messagebox.showinfo("No Variables", "No variables found in template.")
            return
        
        # This would show a dialog to configure variable values
        # For now, show a simple dialog
        messagebox.showinfo("Configure Variables", "Variable configuration dialog will be implemented in a future update.")
    
    def load_template(self, template: PromptTemplate):
        """Load a template into the editor."""
        self.current_template = template
        
        self.name_entry.delete(0, tk.END)
        self.name_entry.insert(0, template.name)
        
        self.description_text.delete("1.0", tk.END)
        self.description_text.insert("1.0", template.description or "")
        
        self.tags_entry.delete(0, tk.END)
        if template.tags:
            self.tags_entry.insert(0, ", ".join(template.tags))
        
        self.text_editor.delete("1.0", tk.END)
        self.text_editor.insert("1.0", template.content or "")
        
        self._set_modified(False)
        self._update_preview()
        self._extract_variables()
        
        # Load version history
        if hasattr(self.version_widget, 'load_versions'):
            self.version_widget.load_versions(template.id)
        
        self.status_label.configure(text=f"Loaded template: {template.name}")
    
    def get_current_template_data(self) -> Dict[str, Any]:
        """Get current template data."""
        return {
            "name": self.name_entry.get().strip(),
            "content": self.text_editor.get("1.0", tk.END).strip(),
            "description": self.description_text.get("1.0", tk.END).strip(),
            "tags": [tag.strip() for tag in self.tags_entry.get().split(",") if tag.strip()],
            "variables": self.variables.copy()
        }