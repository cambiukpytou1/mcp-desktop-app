"""
Template List Widget
====================

Reusable widget for displaying and managing prompt templates with
search, filtering, and quick actions.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import List, Optional, Callable, Dict, Any

from models.prompt import PromptTemplate


class TemplateListWidget(tk.Frame):
    """Reusable template list widget with search and filtering."""
    
    def __init__(self, parent, template_service, on_select: Optional[Callable] = None):
        super().__init__(parent, bg="#ffffff")
        self.template_service = template_service
        self.on_select = on_select
        self.logger = logging.getLogger(__name__)
        
        self.templates: List[PromptTemplate] = []
        self.filtered_templates: List[PromptTemplate] = []
        self.selected_template: Optional[PromptTemplate] = None
        
        self._create_widgets()
        self.refresh()
    
    def _create_widgets(self):
        """Create the widget components."""
        # Search and filter bar
        self._create_search_bar()
        
        # Template list
        self._create_template_list()
        
        # Quick actions
        self._create_quick_actions()
    
    def _create_search_bar(self):
        """Create search and filter controls."""
        search_frame = tk.Frame(self, bg="#ffffff")
        search_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        # Search entry
        tk.Label(
            search_frame,
            text="Search:",
            font=("Arial", 10, "bold"),
            bg="#ffffff"
        ).pack(side="left")
        
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self._on_search_changed)
        
        search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            font=("Arial", 10),
            width=30
        )
        search_entry.pack(side="left", padx=(5, 15))
        
        # Filter dropdown
        tk.Label(
            search_frame,
            text="Filter:",
            font=("Arial", 10, "bold"),
            bg="#ffffff"
        ).pack(side="left")
        
        self.filter_var = tk.StringVar(value="All")
        filter_combo = ttk.Combobox(
            search_frame,
            textvariable=self.filter_var,
            values=["All", "Active", "Draft", "Archived"],
            state="readonly",
            width=12
        )
        filter_combo.pack(side="left", padx=(5, 0))
        filter_combo.bind("<<ComboboxSelected>>", self._on_filter_changed)
    
    def _create_template_list(self):
        """Create the scrollable template list."""
        # List container with scrollbar
        list_container = tk.Frame(self, bg="#ffffff")
        list_container.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Create scrollable frame
        canvas = tk.Canvas(list_container, bg="#ffffff", highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=canvas.yview)
        self.list_frame = tk.Frame(canvas, bg="#ffffff")
        
        self.list_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.list_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def _create_quick_actions(self):
        """Create quick action buttons."""
        actions_frame = tk.Frame(self, bg="#ffffff")
        actions_frame.pack(fill="x", padx=10, pady=(5, 10))
        
        tk.Button(
            actions_frame,
            text="New Template",
            bg="#1a73e8",
            fg="white",
            font=("Arial", 9, "bold"),
            padx=12,
            pady=6,
            relief="flat",
            cursor="hand2",
            command=self._new_template
        ).pack(side="left", padx=(0, 5))
        
        tk.Button(
            actions_frame,
            text="Import",
            bg="#34a853",
            fg="white",
            font=("Arial", 9, "bold"),
            padx=12,
            pady=6,
            relief="flat",
            cursor="hand2",
            command=self._import_templates
        ).pack(side="left", padx=(0, 5))
        
        tk.Button(
            actions_frame,
            text="Export Selected",
            bg="#ff9800",
            fg="white",
            font=("Arial", 9, "bold"),
            padx=12,
            pady=6,
            relief="flat",
            cursor="hand2",
            command=self._export_selected
        ).pack(side="left")
        
        # Selection info
        self.selection_label = tk.Label(
            actions_frame,
            text="No template selected",
            font=("Arial", 9),
            fg="#666",
            bg="#ffffff"
        )
        self.selection_label.pack(side="right")
    
    def _create_template_row(self, template: PromptTemplate):
        """Create a template row widget."""
        row = tk.Frame(self.list_frame, bg="#f8f9fa", bd=1, relief="solid")
        row.pack(fill="x", pady=2)
        
        # Make row clickable
        row.bind("<Button-1>", lambda e: self._select_template(template))
        
        # Template info
        info_frame = tk.Frame(row, bg="#f8f9fa")
        info_frame.pack(side="left", fill="x", expand=True, padx=10, pady=8)
        info_frame.bind("<Button-1>", lambda e: self._select_template(template))
        
        # Template name and status
        name_frame = tk.Frame(info_frame, bg="#f8f9fa")
        name_frame.pack(fill="x")
        name_frame.bind("<Button-1>", lambda e: self._select_template(template))
        
        name_label = tk.Label(
            name_frame,
            text=template.name,
            font=("Arial", 12, "bold"),
            bg="#f8f9fa",
            anchor="w"
        )
        name_label.pack(side="left")
        name_label.bind("<Button-1>", lambda e: self._select_template(template))
        
        # Status indicator
        status_colors = {
            "active": "#34a853",
            "draft": "#ff9800",
            "archived": "#9e9e9e"
        }
        status_color = status_colors.get(template.status, "#9e9e9e")
        
        status_label = tk.Label(
            name_frame,
            text=template.status.title(),
            font=("Arial", 8, "bold"),
            fg="white",
            bg=status_color,
            padx=6,
            pady=2
        )
        status_label.pack(side="left", padx=(10, 0))
        
        # Template description
        if template.description:
            desc_label = tk.Label(
                info_frame,
                text=template.description[:100] + ("..." if len(template.description) > 100 else ""),
                font=("Arial", 10),
                fg="#666",
                bg="#f8f9fa",
                anchor="w"
            )
            desc_label.pack(fill="x", pady=(2, 0))
            desc_label.bind("<Button-1>", lambda e: self._select_template(template))
        
        # Template metadata
        meta_frame = tk.Frame(info_frame, bg="#f8f9fa")
        meta_frame.pack(fill="x", pady=(2, 0))
        meta_frame.bind("<Button-1>", lambda e: self._select_template(template))
        
        meta_text = f"Created: {template.created_at.strftime('%Y-%m-%d')}"
        if template.tags:
            meta_text += f" • Tags: {', '.join(template.tags[:3])}"
            if len(template.tags) > 3:
                meta_text += f" (+{len(template.tags) - 3} more)"
        
        meta_label = tk.Label(
            meta_frame,
            text=meta_text,
            font=("Arial", 9),
            fg="#999",
            bg="#f8f9fa",
            anchor="w"
        )
        meta_label.pack(side="left")
        meta_label.bind("<Button-1>", lambda e: self._select_template(template))
        
        # Quick actions
        actions_frame = tk.Frame(row, bg="#f8f9fa")
        actions_frame.pack(side="right", padx=10, pady=8)
        
        tk.Button(
            actions_frame,
            text="Edit",
            bg="#1a73e8",
            fg="white",
            font=("Arial", 8, "bold"),
            padx=8,
            pady=4,
            relief="flat",
            cursor="hand2",
            command=lambda: self._edit_template(template)
        ).pack(side="left", padx=2)
        
        tk.Button(
            actions_frame,
            text="Copy",
            bg="#34a853",
            fg="white",
            font=("Arial", 8, "bold"),
            padx=8,
            pady=4,
            relief="flat",
            cursor="hand2",
            command=lambda: self._copy_template(template)
        ).pack(side="left", padx=2)
        
        tk.Button(
            actions_frame,
            text="Delete",
            bg="#d93025",
            fg="white",
            font=("Arial", 8, "bold"),
            padx=8,
            pady=4,
            relief="flat",
            cursor="hand2",
            command=lambda: self._delete_template(template)
        ).pack(side="left", padx=2)
    
    def _select_template(self, template: PromptTemplate):
        """Select a template."""
        self.selected_template = template
        self.selection_label.configure(text=f"Selected: {template.name}")
        
        # Highlight selected row (would need more complex implementation)
        # For now, just call the callback
        if self.on_select:
            self.on_select(template)
        
        self.logger.debug(f"Selected template: {template.name}")
    
    def _on_search_changed(self, *args):
        """Handle search text changes."""
        self._apply_filters()
    
    def _on_filter_changed(self, event=None):
        """Handle filter changes."""
        self._apply_filters()
    
    def _apply_filters(self):
        """Apply search and filter criteria."""
        search_text = self.search_var.get().lower()
        filter_value = self.filter_var.get()
        
        self.filtered_templates = []
        
        for template in self.templates:
            # Apply search filter
            if search_text and search_text not in template.name.lower():
                if not template.description or search_text not in template.description.lower():
                    continue
            
            # Apply status filter
            if filter_value != "All" and template.status != filter_value.lower():
                continue
            
            self.filtered_templates.append(template)
        
        self._refresh_list()
    
    def _refresh_list(self):
        """Refresh the template list display."""
        # Clear existing rows
        for widget in self.list_frame.winfo_children():
            widget.destroy()
        
        if not self.filtered_templates:
            # Show empty state
            empty_frame = tk.Frame(self.list_frame, bg="#ffffff")
            empty_frame.pack(fill="both", expand=True, pady=20)
            
            tk.Label(
                empty_frame,
                text="No templates found",
                font=("Arial", 12),
                fg="#666",
                bg="#ffffff"
            ).pack()
        else:
            # Create template rows
            for template in self.filtered_templates:
                self._create_template_row(template)
    
    def refresh(self):
        """Refresh the template list from the service."""
        try:
            # This would get templates from the actual service
            # For now, using sample data for demonstration
            self.templates = self._get_sample_templates()
            self._apply_filters()
            
            self.logger.debug("Template list refreshed")
            
        except Exception as e:
            self.logger.error(f"Failed to refresh template list: {e}")
            messagebox.showerror("Error", f"Failed to refresh templates: {e}")
    
    def _get_sample_templates(self) -> List[PromptTemplate]:
        """Get sample templates for demonstration."""
        from datetime import datetime, timedelta
        
        return [
            PromptTemplate(
                name="Customer Support Assistant",
                content="You are a helpful customer support assistant. Please help the customer with their inquiry: {{user_question}}",
                description="Template for customer support interactions with empathetic and helpful responses",
                tags=["customer-support", "assistant", "help"],
                status="active",
                created_at=datetime.now() - timedelta(days=5)
            ),
            PromptTemplate(
                name="Code Review Helper",
                content="Please review the following code and provide feedback:\n\n{{code}}\n\nFocus on: {{review_criteria}}",
                description="Template for automated code review assistance",
                tags=["code-review", "development", "quality"],
                status="active",
                created_at=datetime.now() - timedelta(days=3)
            ),
            PromptTemplate(
                name="Meeting Summary Generator",
                content="Please create a summary of the following meeting:\n\nParticipants: {{participants}}\nDate: {{date}}\nNotes: {{meeting_notes}}",
                description="Generate structured meeting summaries from notes",
                tags=["meetings", "summary", "productivity"],
                status="draft",
                created_at=datetime.now() - timedelta(days=1)
            ),
            PromptTemplate(
                name="Email Response Template",
                content="Draft a professional email response to: {{original_email}}\n\nTone: {{tone}}\nKey points to address: {{key_points}}",
                description="Professional email response generator",
                tags=["email", "communication", "professional"],
                status="active",
                created_at=datetime.now() - timedelta(hours=6)
            ),
            PromptTemplate(
                name="Data Analysis Report",
                content="Analyze the following data and create a report:\n\nData: {{dataset}}\nAnalysis type: {{analysis_type}}\nTarget audience: {{audience}}",
                description="Generate data analysis reports with insights",
                tags=["data", "analysis", "reporting"],
                status="archived",
                created_at=datetime.now() - timedelta(days=10)
            )
        ]
    
    # Action handlers
    def _new_template(self):
        """Handle new template creation."""
        if self.on_select:
            # Signal to create new template
            self.on_select(None)
    
    def _import_templates(self):
        """Handle template import."""
        from tkinter import filedialog
        
        file_path = filedialog.askopenfilename(
            title="Import Templates",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                # This would implement actual import logic
                messagebox.showinfo("Import", f"Template import from {file_path} will be implemented in a future update.")
            except Exception as e:
                messagebox.showerror("Import Error", f"Failed to import templates: {str(e)}")
    
    def _export_selected(self):
        """Handle export of selected template."""
        if not self.selected_template:
            messagebox.showwarning("No Selection", "Please select a template to export.")
            return
        
        from tkinter import filedialog
        
        file_path = filedialog.asksaveasfilename(
            title="Export Template",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                # This would implement actual export logic
                messagebox.showinfo("Export", f"Template export to {file_path} will be implemented in a future update.")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export template: {str(e)}")
    
    def _edit_template(self, template: PromptTemplate):
        """Handle template editing."""
        if self.on_select:
            self.on_select(template)
    
    def _copy_template(self, template: PromptTemplate):
        """Handle template copying."""
        try:
            # Create a copy with modified name
            if self.on_select:
                # Signal to create a copy
                copy_template = PromptTemplate(
                    name=f"{template.name} (Copy)",
                    content=template.content,
                    description=template.description,
                    tags=template.tags.copy() if template.tags else []
                )
                self.on_select(copy_template)
        except Exception as e:
            messagebox.showerror("Copy Error", f"Failed to copy template: {str(e)}")
    
    def _delete_template(self, template: PromptTemplate):
        """Handle template deletion."""
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{template.name}'?"):
            try:
                # This would implement actual deletion logic
                messagebox.showinfo("Delete", f"Template '{template.name}' deletion will be implemented in a future update.")
                self.refresh()
            except Exception as e:
                messagebox.showerror("Delete Error", f"Failed to delete template: {str(e)}")