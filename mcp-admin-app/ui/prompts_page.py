"""
Prompts Management Page
======================

Comprehensive UI for managing prompt templates with version control and testing.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import logging
import json
from datetime import datetime
from typing import Optional, Dict, Any, List

from models.prompt import PromptTemplate, TestResult
from models.base import PromptParameter


class PromptsPage(tk.Frame):
    """Prompts management page with full functionality."""
    
    def __init__(self, parent, prompt_manager, tool_manager):
        super().__init__(parent, bg="#f9f9f9")
        self.prompt_manager = prompt_manager
        self.tool_manager = tool_manager
        self.logger = logging.getLogger(__name__)
        
        self.selected_template: Optional[PromptTemplate] = None
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self._on_search_change)
        
        self._create_widgets()
        self.refresh()
    
    def _create_widgets(self):
        """Create page widgets."""
        # Header
        header_frame = tk.Frame(self, bg="#f9f9f9")
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        tk.Label(
            header_frame,
            text="Prompt Library",
            font=("Arial", 20, "bold"),
            bg="#f9f9f9"
        ).pack(side="left")
        
        # Action buttons
        btn_frame = tk.Frame(header_frame, bg="#f9f9f9")
        btn_frame.pack(side="right")
        
        ttk.Button(
            btn_frame,
            text="New Template",
            command=self._create_template
        ).pack(side="left", padx=(0, 5))
        
        ttk.Button(
            btn_frame,
            text="Import",
            command=self._import_templates
        ).pack(side="left", padx=(0, 5))
        
        ttk.Button(
            btn_frame,
            text="Export",
            command=self._export_templates
        ).pack(side="left")
        
        # Search and filter frame
        search_frame = tk.Frame(self, bg="#f9f9f9")
        search_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        tk.Label(search_frame, text="Search:", bg="#f9f9f9").pack(side="left")
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side="left", padx=(5, 10))
        
        tk.Label(search_frame, text="Filter by tags:", bg="#f9f9f9").pack(side="left")
        self.tag_filter = ttk.Combobox(search_frame, width=20, state="readonly")
        self.tag_filter.pack(side="left", padx=(5, 0))
        self.tag_filter.bind('<<ComboboxSelected>>', self._on_filter_change)
        
        # Main content area
        main_frame = tk.Frame(self, bg="#f9f9f9")
        main_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Left panel - Template list
        left_panel = tk.Frame(main_frame, bg="white", relief="solid", bd=1)
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # Template list
        list_frame = tk.Frame(left_panel, bg="white")
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        tk.Label(
            list_frame,
            text="Templates",
            font=("Arial", 14, "bold"),
            bg="white"
        ).pack(anchor="w", pady=(0, 10))
        
        # Treeview for templates
        columns = ("name", "version", "tags", "usage", "updated")
        self.template_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        
        self.template_tree.heading("name", text="Name")
        self.template_tree.heading("version", text="Version")
        self.template_tree.heading("tags", text="Tags")
        self.template_tree.heading("usage", text="Usage")
        self.template_tree.heading("updated", text="Updated")
        
        self.template_tree.column("name", width=200)
        self.template_tree.column("version", width=80)
        self.template_tree.column("tags", width=150)
        self.template_tree.column("usage", width=80)
        self.template_tree.column("updated", width=120)
        
        # Scrollbar for treeview
        tree_scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.template_tree.yview)
        self.template_tree.configure(yscrollcommand=tree_scroll.set)
        
        self.template_tree.pack(side="left", fill="both", expand=True)
        tree_scroll.pack(side="right", fill="y")
        
        self.template_tree.bind('<<TreeviewSelect>>', self._on_template_select)
        self.template_tree.bind('<Double-1>', self._edit_template)
        
        # Right panel - Template details and actions
        right_panel = tk.Frame(main_frame, bg="white", relief="solid", bd=1)
        right_panel.pack(side="right", fill="both", expand=True)
        
        # Notebook for different views
        self.notebook = ttk.Notebook(right_panel)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Details tab
        self.details_frame = tk.Frame(self.notebook, bg="white")
        self.notebook.add(self.details_frame, text="Details")
        self._create_details_tab()
        
        # Test tab
        self.test_frame = tk.Frame(self.notebook, bg="white")
        self.notebook.add(self.test_frame, text="Test")
        self._create_test_tab()
        
        # Versions tab
        self.versions_frame = tk.Frame(self.notebook, bg="white")
        self.notebook.add(self.versions_frame, text="Versions")
        self._create_versions_tab()
    
    def _create_details_tab(self):
        """Create the details tab."""
        # Template info
        info_frame = tk.Frame(self.details_frame, bg="white")
        info_frame.pack(fill="x", pady=(0, 10))
        
        self.name_label = tk.Label(info_frame, text="Select a template", font=("Arial", 16, "bold"), bg="white")
        self.name_label.pack(anchor="w")
        
        self.desc_label = tk.Label(info_frame, text="", font=("Arial", 10), fg="#666", bg="white", wraplength=400)
        self.desc_label.pack(anchor="w", pady=(5, 0))
        
        # Template content
        content_frame = tk.Frame(self.details_frame, bg="white")
        content_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        tk.Label(content_frame, text="Content:", font=("Arial", 12, "bold"), bg="white").pack(anchor="w")
        
        self.content_text = tk.Text(content_frame, height=10, wrap="word", state="disabled")
        content_scroll = ttk.Scrollbar(content_frame, orient="vertical", command=self.content_text.yview)
        self.content_text.configure(yscrollcommand=content_scroll.set)
        
        self.content_text.pack(side="left", fill="both", expand=True)
        content_scroll.pack(side="right", fill="y")
        
        # Parameters
        params_frame = tk.Frame(self.details_frame, bg="white")
        params_frame.pack(fill="x", pady=(0, 10))
        
        tk.Label(params_frame, text="Parameters:", font=("Arial", 12, "bold"), bg="white").pack(anchor="w")
        
        self.params_tree = ttk.Treeview(params_frame, columns=("type", "required", "default"), show="headings", height=4)
        self.params_tree.heading("#0", text="Name")
        self.params_tree.heading("type", text="Type")
        self.params_tree.heading("required", text="Required")
        self.params_tree.heading("default", text="Default")
        
        self.params_tree.column("#0", width=100)
        self.params_tree.column("type", width=80)
        self.params_tree.column("required", width=80)
        self.params_tree.column("default", width=100)
        
        self.params_tree.pack(fill="x")
        
        # Action buttons
        action_frame = tk.Frame(self.details_frame, bg="white")
        action_frame.pack(fill="x", pady=(10, 0))
        
        ttk.Button(action_frame, text="Edit", command=self._edit_template).pack(side="left", padx=(0, 5))
        ttk.Button(action_frame, text="Duplicate", command=self._duplicate_template).pack(side="left", padx=(0, 5))
        ttk.Button(action_frame, text="Delete", command=self._delete_template).pack(side="left")
    
    def _create_test_tab(self):
        """Create the test tab."""
        # Parameter inputs
        inputs_frame = tk.Frame(self.test_frame, bg="white")
        inputs_frame.pack(fill="x", pady=(0, 10))
        
        tk.Label(inputs_frame, text="Test Parameters:", font=("Arial", 12, "bold"), bg="white").pack(anchor="w")
        
        self.param_inputs_frame = tk.Frame(inputs_frame, bg="white")
        self.param_inputs_frame.pack(fill="x", pady=(5, 0))
        
        # Test button
        test_btn_frame = tk.Frame(self.test_frame, bg="white")
        test_btn_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Button(test_btn_frame, text="Test Template", command=self._test_template).pack(side="left")
        
        # Results
        results_frame = tk.Frame(self.test_frame, bg="white")
        results_frame.pack(fill="both", expand=True)
        
        tk.Label(results_frame, text="Test Results:", font=("Arial", 12, "bold"), bg="white").pack(anchor="w")
        
        self.results_text = tk.Text(results_frame, height=15, wrap="word", state="disabled")
        results_scroll = ttk.Scrollbar(results_frame, orient="vertical", command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=results_scroll.set)
        
        self.results_text.pack(side="left", fill="both", expand=True)
        results_scroll.pack(side="right", fill="y")
    
    def _create_versions_tab(self):
        """Create the versions tab."""
        # Version list
        versions_list_frame = tk.Frame(self.versions_frame, bg="white")
        versions_list_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        tk.Label(versions_list_frame, text="Version History:", font=("Arial", 12, "bold"), bg="white").pack(anchor="w")
        
        columns = ("version", "created_by", "created_at", "notes")
        self.versions_tree = ttk.Treeview(versions_list_frame, columns=columns, show="headings", height=8)
        
        self.versions_tree.heading("version", text="Version")
        self.versions_tree.heading("created_by", text="Created By")
        self.versions_tree.heading("created_at", text="Created At")
        self.versions_tree.heading("notes", text="Notes")
        
        self.versions_tree.column("version", width=80)
        self.versions_tree.column("created_by", width=100)
        self.versions_tree.column("created_at", width=150)
        self.versions_tree.column("notes", width=200)
        
        versions_scroll = ttk.Scrollbar(versions_list_frame, orient="vertical", command=self.versions_tree.yview)
        self.versions_tree.configure(yscrollcommand=versions_scroll.set)
        
        self.versions_tree.pack(side="left", fill="both", expand=True)
        versions_scroll.pack(side="right", fill="y")
        
        # Version actions
        version_actions = tk.Frame(self.versions_frame, bg="white")
        version_actions.pack(fill="x")
        
        ttk.Button(version_actions, text="View Version", command=self._view_version).pack(side="left", padx=(0, 5))
        ttk.Button(version_actions, text="Revert to Version", command=self._revert_version).pack(side="left")
    
    def _on_search_change(self, *args):
        """Handle search text change."""
        self._filter_templates()
    
    def _on_filter_change(self, event):
        """Handle tag filter change."""
        self._filter_templates()
    
    def _filter_templates(self):
        """Filter templates based on search and tag filter."""
        search_text = self.search_var.get().strip()
        selected_tag = self.tag_filter.get()
        
        if selected_tag == "All Tags":
            selected_tag = None
        
        tags = [selected_tag] if selected_tag else None
        templates = self.prompt_manager.search_templates(search_text, tags)
        
        self._populate_template_list(templates)
    
    def _populate_template_list(self, templates: List[PromptTemplate] = None):
        """Populate the template list."""
        # Clear existing items
        for item in self.template_tree.get_children():
            self.template_tree.delete(item)
        
        if templates is None:
            templates = self.prompt_manager.get_all_templates()
        
        for template in templates:
            tags_str = ", ".join(template.tags[:3])  # Show first 3 tags
            if len(template.tags) > 3:
                tags_str += "..."
            
            updated_str = template.updated_at.strftime("%Y-%m-%d %H:%M") if template.updated_at else ""
            
            self.template_tree.insert("", "end", values=(
                template.name,
                f"v{template.version}",
                tags_str,
                template.usage_count,
                updated_str
            ), tags=(template.id,))
    
    def _on_template_select(self, event):
        """Handle template selection."""
        selection = self.template_tree.selection()
        if not selection:
            self.selected_template = None
            self._update_details_view()
            return
        
        item = self.template_tree.item(selection[0])
        template_id = item['tags'][0] if item['tags'] else None
        
        if template_id:
            self.selected_template = self.prompt_manager.get_template(template_id)
            self._update_details_view()
            self._update_test_view()
            self._update_versions_view()
    
    def _update_details_view(self):
        """Update the details view."""
        if not self.selected_template:
            self.name_label.config(text="Select a template")
            self.desc_label.config(text="")
            self.content_text.config(state="normal")
            self.content_text.delete(1.0, "end")
            self.content_text.config(state="disabled")
            
            # Clear parameters
            for item in self.params_tree.get_children():
                self.params_tree.delete(item)
            return
        
        template = self.selected_template
        
        # Update labels
        self.name_label.config(text=template.name)
        self.desc_label.config(text=template.description)
        
        # Update content
        self.content_text.config(state="normal")
        self.content_text.delete(1.0, "end")
        self.content_text.insert(1.0, template.content)
        self.content_text.config(state="disabled")
        
        # Update parameters
        for item in self.params_tree.get_children():
            self.params_tree.delete(item)
        
        for param in template.parameters:
            self.params_tree.insert("", "end", text=param.name, values=(
                param.type,
                "Yes" if param.required else "No",
                param.default or ""
            ))
    
    def _update_test_view(self):
        """Update the test view with parameter inputs."""
        # Clear existing inputs
        for widget in self.param_inputs_frame.winfo_children():
            widget.destroy()
        
        if not self.selected_template:
            return
        
        self.param_entries = {}
        
        for i, param in enumerate(self.selected_template.parameters):
            row_frame = tk.Frame(self.param_inputs_frame, bg="white")
            row_frame.pack(fill="x", pady=2)
            
            label_text = f"{param.name}:"
            if param.required:
                label_text += " *"
            
            tk.Label(row_frame, text=label_text, width=15, anchor="w", bg="white").pack(side="left")
            
            entry = ttk.Entry(row_frame, width=30)
            entry.pack(side="left", padx=(5, 0))
            
            if param.default:
                entry.insert(0, param.default)
            
            self.param_entries[param.name] = entry
            
            # Add description
            if param.description:
                tk.Label(row_frame, text=f"({param.description})", fg="#666", bg="white").pack(side="left", padx=(5, 0))
    
    def _update_versions_view(self):
        """Update the versions view."""
        # Clear existing items
        for item in self.versions_tree.get_children():
            self.versions_tree.delete(item)
        
        if not self.selected_template:
            return
        
        versions = self.prompt_manager.get_template_versions(self.selected_template.id)
        
        for version in sorted(versions, key=lambda v: v.version, reverse=True):
            created_at_str = version.created_at.strftime("%Y-%m-%d %H:%M")
            
            self.versions_tree.insert("", "end", values=(
                f"v{version.version}",
                version.created_by,
                created_at_str,
                version.change_notes
            ), tags=(str(version.version),))
    
    def _create_template(self):
        """Create a new template."""
        TemplateDialog(self, self.prompt_manager, callback=self.refresh)
    
    def _edit_template(self, event=None):
        """Edit the selected template."""
        if not self.selected_template:
            messagebox.showwarning("No Selection", "Please select a template to edit.")
            return
        
        TemplateDialog(self, self.prompt_manager, template=self.selected_template, callback=self.refresh)
    
    def _duplicate_template(self):
        """Duplicate the selected template."""
        if not self.selected_template:
            messagebox.showwarning("No Selection", "Please select a template to duplicate.")
            return
        
        # Create a copy with new ID and name
        template_copy = PromptTemplate()
        template_copy.name = f"{self.selected_template.name} (Copy)"
        template_copy.description = self.selected_template.description
        template_copy.content = self.selected_template.content
        template_copy.target_tools = self.selected_template.target_tools.copy()
        template_copy.parameters = self.selected_template.parameters.copy()
        template_copy.tags = self.selected_template.tags.copy()
        
        TemplateDialog(self, self.prompt_manager, template=template_copy, callback=self.refresh)
    
    def _delete_template(self):
        """Delete the selected template."""
        if not self.selected_template:
            messagebox.showwarning("No Selection", "Please select a template to delete.")
            return
        
        result = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete '{self.selected_template.name}'?\n\nThis action cannot be undone."
        )
        
        if result:
            success = self.prompt_manager.delete_template(self.selected_template.id)
            if success:
                messagebox.showinfo("Success", "Template deleted successfully.")
                self.selected_template = None
                self.refresh()
            else:
                messagebox.showerror("Error", "Failed to delete template.")
    
    def _test_template(self):
        """Test the selected template."""
        if not self.selected_template:
            messagebox.showwarning("No Selection", "Please select a template to test.")
            return
        
        # Collect parameters
        parameters = {}
        for param_name, entry in self.param_entries.items():
            value = entry.get().strip()
            if value:
                parameters[param_name] = value
        
        # Test the template
        result = self.prompt_manager.test_template(self.selected_template.id, parameters)
        
        # Display results
        self.results_text.config(state="normal")
        self.results_text.delete(1.0, "end")
        
        if result.success:
            self.results_text.insert("end", "✅ Test Successful\n\n", "success")
            self.results_text.insert("end", f"Execution Time: {result.execution_time:.3f}s\n\n")
            self.results_text.insert("end", "Generated Output:\n")
            self.results_text.insert("end", "-" * 50 + "\n")
            self.results_text.insert("end", result.output)
        else:
            self.results_text.insert("end", "❌ Test Failed\n\n", "error")
            self.results_text.insert("end", f"Error: {result.error}\n\n")
            if result.output:
                self.results_text.insert("end", "Partial Output:\n")
                self.results_text.insert("end", "-" * 50 + "\n")
                self.results_text.insert("end", result.output)
        
        self.results_text.config(state="disabled")
    
    def _view_version(self):
        """View a specific version."""
        selection = self.versions_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a version to view.")
            return
        
        item = self.versions_tree.item(selection[0])
        version_num = int(item['tags'][0])
        
        versions = self.prompt_manager.get_template_versions(self.selected_template.id)
        version = next((v for v in versions if v.version == version_num), None)
        
        if version:
            VersionViewDialog(self, version)
    
    def _revert_version(self):
        """Revert to a specific version."""
        selection = self.versions_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a version to revert to.")
            return
        
        item = self.versions_tree.item(selection[0])
        version_num = int(item['tags'][0])
        
        result = messagebox.askyesno(
            "Confirm Revert",
            f"Are you sure you want to revert to version {version_num}?\n\nThis will create a new version with the old content."
        )
        
        if result:
            success = self.prompt_manager.revert_to_version(self.selected_template.id, version_num)
            if success:
                messagebox.showinfo("Success", f"Reverted to version {version_num}.")
                self.refresh()
                self._on_template_select(None)  # Refresh details
            else:
                messagebox.showerror("Error", "Failed to revert version.")
    
    def _import_templates(self):
        """Import templates from file."""
        filename = filedialog.askopenfilename(
            title="Import Templates",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    import_data = json.load(f)
                
                imported, skipped = self.prompt_manager.import_templates(import_data)
                messagebox.showinfo(
                    "Import Complete",
                    f"Imported {imported} templates.\nSkipped {skipped} existing templates."
                )
                self.refresh()
                
            except Exception as e:
                messagebox.showerror("Import Error", f"Failed to import templates:\n{str(e)}")
    
    def _export_templates(self):
        """Export templates to file."""
        filename = filedialog.asksaveasfilename(
            title="Export Templates",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                export_data = self.prompt_manager.export_templates()
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
                
                messagebox.showinfo("Export Complete", f"Exported {len(export_data['templates'])} templates.")
                
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export templates:\n{str(e)}")
    
    def refresh(self):
        """Refresh the page."""
        # Update tag filter
        tags = ["All Tags"] + self.prompt_manager.get_available_tags()
        self.tag_filter['values'] = tags
        if not self.tag_filter.get():
            self.tag_filter.set("All Tags")
        
        # Refresh template list
        self._populate_template_list()


class TemplateDialog:
    """Dialog for creating/editing templates."""
    
    def __init__(self, parent, prompt_manager, template=None, callback=None):
        self.parent = parent
        self.prompt_manager = prompt_manager
        self.template = template
        self.callback = callback
        self.is_edit = template is not None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Edit Template" if self.is_edit else "New Template")
        self.dialog.geometry("800x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.parameters = []
        if self.is_edit:
            self.parameters = template.parameters.copy()
        
        self._create_widgets()
        self._populate_fields()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
    
    def _create_widgets(self):
        """Create dialog widgets."""
        main_frame = tk.Frame(self.dialog, padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)
        
        # Basic info
        info_frame = tk.Frame(main_frame)
        info_frame.pack(fill="x", pady=(0, 10))
        
        tk.Label(info_frame, text="Name:").grid(row=0, column=0, sticky="w", pady=2)
        self.name_entry = ttk.Entry(info_frame, width=50)
        self.name_entry.grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=2)
        
        tk.Label(info_frame, text="Description:").grid(row=1, column=0, sticky="nw", pady=2)
        self.desc_entry = tk.Text(info_frame, height=3, width=50)
        self.desc_entry.grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=2)
        
        tk.Label(info_frame, text="Tags (comma-separated):").grid(row=2, column=0, sticky="w", pady=2)
        self.tags_entry = ttk.Entry(info_frame, width=50)
        self.tags_entry.grid(row=2, column=1, sticky="ew", padx=(10, 0), pady=2)
        
        info_frame.columnconfigure(1, weight=1)
        
        # Content
        content_frame = tk.Frame(main_frame)
        content_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        tk.Label(content_frame, text="Template Content:").pack(anchor="w")
        
        self.content_text = tk.Text(content_frame, height=15, wrap="word")
        content_scroll = ttk.Scrollbar(content_frame, orient="vertical", command=self.content_text.yview)
        self.content_text.configure(yscrollcommand=content_scroll.set)
        
        self.content_text.pack(side="left", fill="both", expand=True)
        content_scroll.pack(side="right", fill="y")
        
        # Parameters
        params_frame = tk.Frame(main_frame)
        params_frame.pack(fill="x", pady=(0, 10))
        
        params_header = tk.Frame(params_frame)
        params_header.pack(fill="x")
        
        tk.Label(params_header, text="Parameters:", font=("Arial", 12, "bold")).pack(side="left")
        ttk.Button(params_header, text="Add Parameter", command=self._add_parameter).pack(side="right")
        
        self.params_frame = tk.Frame(params_frame)
        self.params_frame.pack(fill="x", pady=(5, 0))
        
        # Buttons
        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(fill="x", pady=(10, 0))
        
        ttk.Button(btn_frame, text="Cancel", command=self.dialog.destroy).pack(side="right")
        ttk.Button(btn_frame, text="Save", command=self._save_template).pack(side="right", padx=(0, 10))
        
        if self.is_edit:
            ttk.Button(btn_frame, text="Save as New Version", command=self._save_as_version).pack(side="right", padx=(0, 10))
    
    def _populate_fields(self):
        """Populate fields with template data."""
        if not self.is_edit:
            return
        
        self.name_entry.insert(0, self.template.name)
        self.desc_entry.insert(1.0, self.template.description)
        self.tags_entry.insert(0, ", ".join(self.template.tags))
        self.content_text.insert(1.0, self.template.content)
        
        self._refresh_parameters()
    
    def _refresh_parameters(self):
        """Refresh the parameters display."""
        for widget in self.params_frame.winfo_children():
            widget.destroy()
        
        for i, param in enumerate(self.parameters):
            param_frame = tk.Frame(self.params_frame, relief="solid", bd=1, padx=5, pady=5)
            param_frame.pack(fill="x", pady=2)
            
            # Parameter info
            info_frame = tk.Frame(param_frame)
            info_frame.pack(fill="x")
            
            tk.Label(info_frame, text=f"Name: {param.name}", font=("Arial", 10, "bold")).pack(side="left")
            tk.Label(info_frame, text=f"Type: {param.type}").pack(side="left", padx=(10, 0))
            tk.Label(info_frame, text="Required" if param.required else "Optional", 
                    fg="red" if param.required else "blue").pack(side="left", padx=(10, 0))
            
            ttk.Button(info_frame, text="Edit", command=lambda idx=i: self._edit_parameter(idx)).pack(side="right")
            ttk.Button(info_frame, text="Delete", command=lambda idx=i: self._delete_parameter(idx)).pack(side="right", padx=(0, 5))
            
            if param.description:
                tk.Label(param_frame, text=param.description, fg="#666").pack(anchor="w")
            
            if param.default:
                tk.Label(param_frame, text=f"Default: {param.default}", fg="#666").pack(anchor="w")
    
    def _add_parameter(self):
        """Add a new parameter."""
        ParameterDialog(self.dialog, callback=self._on_parameter_added)
    
    def _edit_parameter(self, index):
        """Edit a parameter."""
        param = self.parameters[index]
        ParameterDialog(self.dialog, param, callback=lambda p: self._on_parameter_edited(index, p))
    
    def _delete_parameter(self, index):
        """Delete a parameter."""
        del self.parameters[index]
        self._refresh_parameters()
    
    def _on_parameter_added(self, param):
        """Handle parameter addition."""
        self.parameters.append(param)
        self._refresh_parameters()
    
    def _on_parameter_edited(self, index, param):
        """Handle parameter edit."""
        self.parameters[index] = param
        self._refresh_parameters()
    
    def _save_template(self):
        """Save the template."""
        try:
            name = self.name_entry.get().strip()
            if not name:
                messagebox.showerror("Error", "Template name is required.")
                return
            
            description = self.desc_entry.get(1.0, "end").strip()
            content = self.content_text.get(1.0, "end").strip()
            tags = [tag.strip() for tag in self.tags_entry.get().split(",") if tag.strip()]
            
            if self.is_edit:
                # Update existing template
                self.template.name = name
                self.template.description = description
                self.template.content = content
                self.template.tags = tags
                self.template.parameters = self.parameters
                
                success = self.prompt_manager.update_template(self.template.id, self.template)
                if success:
                    messagebox.showinfo("Success", "Template updated successfully.")
                else:
                    messagebox.showerror("Error", "Failed to update template.")
                    return
            else:
                # Create new template
                template = PromptTemplate()
                template.name = name
                template.description = description
                template.content = content
                template.tags = tags
                template.parameters = self.parameters
                
                template_id = self.prompt_manager.create_template(template)
                messagebox.showinfo("Success", "Template created successfully.")
            
            if self.callback:
                self.callback()
            
            self.dialog.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save template:\n{str(e)}")
    
    def _save_as_version(self):
        """Save as a new version."""
        # This would open a dialog to get change notes
        notes = tk.simpledialog.askstring("Version Notes", "Enter notes for this version:")
        if notes is not None:
            # Update content and save
            self.template.content = self.content_text.get(1.0, "end").strip()
            success = self.prompt_manager.update_template(
                self.template.id, 
                self.template, 
                change_notes=notes
            )
            
            if success:
                messagebox.showinfo("Success", "New version saved successfully.")
                if self.callback:
                    self.callback()
                self.dialog.destroy()
            else:
                messagebox.showerror("Error", "Failed to save new version.")


class ParameterDialog:
    """Dialog for creating/editing parameters."""
    
    def __init__(self, parent, parameter=None, callback=None):
        self.parent = parent
        self.parameter = parameter
        self.callback = callback
        self.is_edit = parameter is not None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Edit Parameter" if self.is_edit else "New Parameter")
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self._create_widgets()
        self._populate_fields()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
    
    def _create_widgets(self):
        """Create dialog widgets."""
        main_frame = tk.Frame(self.dialog, padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)
        
        # Fields
        tk.Label(main_frame, text="Name:").grid(row=0, column=0, sticky="w", pady=5)
        self.name_entry = ttk.Entry(main_frame, width=30)
        self.name_entry.grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=5)
        
        tk.Label(main_frame, text="Type:").grid(row=1, column=0, sticky="w", pady=5)
        self.type_combo = ttk.Combobox(main_frame, values=["string", "number", "boolean", "list"], width=27)
        self.type_combo.grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=5)
        self.type_combo.set("string")
        
        tk.Label(main_frame, text="Description:").grid(row=2, column=0, sticky="nw", pady=5)
        self.desc_text = tk.Text(main_frame, height=4, width=30)
        self.desc_text.grid(row=2, column=1, sticky="ew", padx=(10, 0), pady=5)
        
        self.required_var = tk.BooleanVar(value=True)
        self.required_check = tk.Checkbutton(main_frame, text="Required", variable=self.required_var)
        self.required_check.grid(row=3, column=1, sticky="w", padx=(10, 0), pady=5)
        
        tk.Label(main_frame, text="Default Value:").grid(row=4, column=0, sticky="w", pady=5)
        self.default_entry = ttk.Entry(main_frame, width=30)
        self.default_entry.grid(row=4, column=1, sticky="ew", padx=(10, 0), pady=5)
        
        main_frame.columnconfigure(1, weight=1)
        
        # Buttons
        btn_frame = tk.Frame(main_frame)
        btn_frame.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(20, 0))
        
        ttk.Button(btn_frame, text="Cancel", command=self.dialog.destroy).pack(side="right")
        ttk.Button(btn_frame, text="Save", command=self._save_parameter).pack(side="right", padx=(0, 10))
    
    def _populate_fields(self):
        """Populate fields with parameter data."""
        if not self.is_edit:
            return
        
        self.name_entry.insert(0, self.parameter.name)
        self.type_combo.set(self.parameter.type)
        self.desc_text.insert(1.0, self.parameter.description)
        self.required_var.set(self.parameter.required)
        if self.parameter.default:
            self.default_entry.insert(0, self.parameter.default)
    
    def _save_parameter(self):
        """Save the parameter."""
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showerror("Error", "Parameter name is required.")
            return
        
        param_type = self.type_combo.get()
        description = self.desc_text.get(1.0, "end").strip()
        required = self.required_var.get()
        default = self.default_entry.get().strip() or None
        
        parameter = PromptParameter(
            name=name,
            type=param_type,
            description=description,
            required=required,
            default=default
        )
        
        if self.callback:
            self.callback(parameter)
        
        self.dialog.destroy()


class VersionViewDialog:
    """Dialog for viewing a specific version."""
    
    def __init__(self, parent, version):
        self.parent = parent
        self.version = version
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"Version {version.version}")
        self.dialog.geometry("600x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self._create_widgets()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
    
    def _create_widgets(self):
        """Create dialog widgets."""
        main_frame = tk.Frame(self.dialog, padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)
        
        # Version info
        info_frame = tk.Frame(main_frame)
        info_frame.pack(fill="x", pady=(0, 10))
        
        tk.Label(info_frame, text=f"Version {self.version.version}", font=("Arial", 16, "bold")).pack(anchor="w")
        tk.Label(info_frame, text=f"Created by: {self.version.created_by}").pack(anchor="w")
        tk.Label(info_frame, text=f"Created at: {self.version.created_at.strftime('%Y-%m-%d %H:%M:%S')}").pack(anchor="w")
        
        if self.version.change_notes:
            tk.Label(info_frame, text=f"Notes: {self.version.change_notes}").pack(anchor="w")
        
        # Content
        tk.Label(main_frame, text="Content:", font=("Arial", 12, "bold")).pack(anchor="w", pady=(10, 5))
        
        content_text = tk.Text(main_frame, wrap="word", state="disabled")
        content_scroll = ttk.Scrollbar(main_frame, orient="vertical", command=content_text.yview)
        content_text.configure(yscrollcommand=content_scroll.set)
        
        content_text.pack(side="left", fill="both", expand=True)
        content_scroll.pack(side="right", fill="y")
        
        content_text.config(state="normal")
        content_text.insert(1.0, self.version.content)
        content_text.config(state="disabled")
        
        # Close button
        ttk.Button(main_frame, text="Close", command=self.dialog.destroy).pack(pady=(10, 0))