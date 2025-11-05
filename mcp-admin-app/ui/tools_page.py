"""
Enhanced Tools Management Page
=============================

Comprehensive UI for managing MCP tools including discovery, registry management,
interactive testing, and configuration.
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import logging
import json
from datetime import datetime
from typing import Optional, List, Dict, Any

from models.tool import (
    ToolRegistryEntry, ToolFilters, ToolCategory, ToolStatus, 
    SecurityLevel
)
from services.tool_manager import AdvancedToolManager, ToolConfiguration
from services.tool_execution import ToolExecutionEngine, ExecutionRequest


class ToolsPage(tk.Frame):
    """Enhanced tools management page."""
    
    def __init__(self, parent, tool_manager: AdvancedToolManager, server_manager):
        super().__init__(parent, bg="#f9f9f9")
        self.tool_manager = tool_manager
        self.server_manager = server_manager
        self.execution_engine = ToolExecutionEngine(tool_manager.db_manager)
        self.logger = logging.getLogger(__name__)
        
        self.current_tools = []
        self.selected_tool = None
        
        self._create_widgets()
        self.refresh()
    
    def _create_widgets(self):
        """Create page widgets."""
        # Header
        header_frame = tk.Frame(self, bg="#f9f9f9")
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        tk.Label(
            header_frame,
            text="Tools Management",
            font=("Arial", 20, "bold"),
            bg="#f9f9f9"
        ).pack(side="left")
        
        # Action buttons
        btn_frame = tk.Frame(header_frame, bg="#f9f9f9")
        btn_frame.pack(side="right")
        
        ttk.Button(
            btn_frame,
            text="Discover Tools",
            command=self._discover_tools
        ).pack(side="left", padx=(0, 10))
        
        ttk.Button(
            btn_frame,
            text="Sync Tools",
            command=self._sync_tools
        ).pack(side="left", padx=(0, 10))
        
        ttk.Button(
            btn_frame,
            text="Statistics",
            command=self._show_statistics
        ).pack(side="left", padx=(0, 10))
        
        ttk.Button(
            btn_frame,
            text="Bulk Delete",
            command=self._bulk_delete_tools
        ).pack(side="left", padx=(0, 10))
        
        ttk.Button(
            btn_frame,
            text="Refresh",
            command=self.refresh
        ).pack(side="left")
        
        # Main content area
        main_frame = tk.Frame(self, bg="#f9f9f9")
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Left panel - Tool list and filters
        left_panel = tk.Frame(main_frame, bg="white", relief="solid", bd=1)
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        self._create_tool_list_panel(left_panel)
        
        # Right panel - Tool details and actions
        right_panel = tk.Frame(main_frame, bg="white", relief="solid", bd=1)
        right_panel.pack(side="right", fill="both", expand=True)
        
        self._create_tool_details_panel(right_panel)
    
    def _create_tool_list_panel(self, parent):
        """Create tool list and filter panel."""
        # Filter section
        filter_frame = tk.Frame(parent, bg="white")
        filter_frame.pack(fill="x", padx=10, pady=10)
        
        tk.Label(
            filter_frame,
            text="Filters",
            font=("Arial", 12, "bold"),
            bg="white"
        ).pack(anchor="w")
        
        # Search box with advanced options
        search_frame = tk.Frame(filter_frame, bg="white")
        search_frame.pack(fill="x", pady=(5, 0))
        
        tk.Label(search_frame, text="Search:", bg="white").pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self._on_search_changed)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=25)
        search_entry.pack(side="left", padx=(5, 0), fill="x", expand=True)
        
        # Advanced search button
        ttk.Button(
            search_frame,
            text="Advanced",
            command=self._show_advanced_search,
            width=8
        ).pack(side="right", padx=(5, 0))
        
        # Category filter
        category_frame = tk.Frame(filter_frame, bg="white")
        category_frame.pack(fill="x", pady=(5, 0))
        
        tk.Label(category_frame, text="Category:", bg="white").pack(side="left")
        self.category_var = tk.StringVar(value="All")
        category_combo = ttk.Combobox(
            category_frame,
            textvariable=self.category_var,
            values=["All"] + [cat.value for cat in ToolCategory],
            state="readonly",
            width=20
        )
        category_combo.pack(side="left", padx=(5, 0))
        category_combo.bind("<<ComboboxSelected>>", self._on_filter_changed)
        
        # Status filter
        status_frame = tk.Frame(filter_frame, bg="white")
        status_frame.pack(fill="x", pady=(5, 0))
        
        tk.Label(status_frame, text="Status:", bg="white").pack(side="left")
        self.status_var = tk.StringVar(value="All")
        status_combo = ttk.Combobox(
            status_frame,
            textvariable=self.status_var,
            values=["All"] + [status.value for status in ToolStatus],
            state="readonly",
            width=15
        )
        status_combo.pack(side="left", padx=(5, 0))
        status_combo.bind("<<ComboboxSelected>>", self._on_filter_changed)
        
        # Sort options
        sort_frame = tk.Frame(filter_frame, bg="white")
        sort_frame.pack(fill="x", pady=(5, 0))
        
        tk.Label(sort_frame, text="Sort by:", bg="white").pack(side="left")
        self.sort_var = tk.StringVar(value="name")
        sort_combo = ttk.Combobox(
            sort_frame,
            textvariable=self.sort_var,
            values=["name", "category", "usage_count", "success_rate", "created_at"],
            state="readonly",
            width=12
        )
        sort_combo.pack(side="left", padx=(5, 0))
        sort_combo.bind("<<ComboboxSelected>>", self._on_filter_changed)
        
        self.sort_order_var = tk.StringVar(value="asc")
        ttk.Checkbutton(
            sort_frame,
            text="Desc",
            variable=self.sort_order_var,
            onvalue="desc",
            offvalue="asc",
            command=self._on_filter_changed
        ).pack(side="left", padx=(5, 0))
        
        # Tool list
        list_frame = tk.Frame(parent, bg="white")
        list_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        tk.Label(
            list_frame,
            text="Tools",
            font=("Arial", 12, "bold"),
            bg="white"
        ).pack(anchor="w", pady=(0, 5))
        
        # Treeview for tools
        columns = ("Name", "Category", "Status", "Server", "Usage")
        self.tools_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15, selectmode="extended")
        
        # Configure columns
        self.tools_tree.heading("Name", text="Name")
        self.tools_tree.heading("Category", text="Category")
        self.tools_tree.heading("Status", text="Status")
        self.tools_tree.heading("Server", text="Server")
        self.tools_tree.heading("Usage", text="Usage Count")
        
        self.tools_tree.column("Name", width=150)
        self.tools_tree.column("Category", width=120)
        self.tools_tree.column("Status", width=100)
        self.tools_tree.column("Server", width=120)
        self.tools_tree.column("Usage", width=80)
        
        # Scrollbar for treeview
        tree_scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.tools_tree.yview)
        self.tools_tree.configure(yscrollcommand=tree_scroll.set)
        
        self.tools_tree.pack(side="left", fill="both", expand=True)
        tree_scroll.pack(side="right", fill="y")
        
        # Bind selection event
        self.tools_tree.bind("<<TreeviewSelect>>", self._on_tool_selected)
        
        # Create context menu
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Test Tool", command=self._test_tool)
        self.context_menu.add_command(label="Configure Tool", command=self._configure_tool)
        self.context_menu.add_command(label="View Schema", command=self._view_schema)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Delete Tool", command=self._delete_tool)
        self.context_menu.add_command(label="Delete Selected Tools", command=self._bulk_delete_tools)
        
        # Bind right-click
        self.tools_tree.bind("<Button-3>", self._show_context_menu)
        
        # Bind Delete key
        self.tools_tree.bind("<Delete>", self._on_delete_key)
        
        # Make sure the treeview can receive focus for keyboard events
        self.tools_tree.focus_set()
        
        # Status bar
        status_frame = tk.Frame(parent, bg="white")
        status_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.status_label = tk.Label(
            status_frame,
            text="No tools selected",
            font=("Arial", 9),
            fg="gray",
            bg="white"
        )
        self.status_label.pack(anchor="w")
    
    def _create_tool_details_panel(self, parent):
        """Create tool details and actions panel."""
        # Tool details section
        details_frame = tk.Frame(parent, bg="white")
        details_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        tk.Label(
            details_frame,
            text="Tool Details",
            font=("Arial", 12, "bold"),
            bg="white"
        ).pack(anchor="w", pady=(0, 10))
        
        # Create notebook for different detail tabs
        self.details_notebook = ttk.Notebook(details_frame)
        self.details_notebook.pack(fill="both", expand=True)
        
        # Overview tab
        overview_frame = tk.Frame(self.details_notebook, bg="white")
        self.details_notebook.add(overview_frame, text="Overview")
        self._create_overview_tab(overview_frame)
        
        # Parameters tab
        params_frame = tk.Frame(self.details_notebook, bg="white")
        self.details_notebook.add(params_frame, text="Parameters")
        self._create_parameters_tab(params_frame)
        
        # Configuration tab
        config_frame = tk.Frame(self.details_notebook, bg="white")
        self.details_notebook.add(config_frame, text="Configuration")
        self._create_configuration_tab(config_frame)
        
        # Testing tab
        testing_frame = tk.Frame(self.details_notebook, bg="white")
        self.details_notebook.add(testing_frame, text="Testing")
        self._create_testing_tab(testing_frame)
        
        # Tags tab
        tags_frame = tk.Frame(self.details_notebook, bg="white")
        self.details_notebook.add(tags_frame, text="Tags & Related")
        self._create_tags_tab(tags_frame)
        
        # Execution History tab
        history_frame = tk.Frame(self.details_notebook, bg="white")
        self.details_notebook.add(history_frame, text="Execution History")
        self._create_history_tab(history_frame)
        
        # Actions section
        actions_frame = tk.Frame(parent, bg="white")
        actions_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        tk.Label(
            actions_frame,
            text="Actions",
            font=("Arial", 12, "bold"),
            bg="white"
        ).pack(anchor="w", pady=(0, 5))
        
        # Action buttons
        btn_frame = tk.Frame(actions_frame, bg="white")
        btn_frame.pack(fill="x")
        
        self.enable_btn = ttk.Button(
            btn_frame,
            text="Enable",
            command=self._toggle_tool_enabled,
            state="disabled"
        )
        self.enable_btn.pack(side="left", padx=(0, 5))
        
        self.configure_btn = ttk.Button(
            btn_frame,
            text="Configure",
            command=self._configure_tool,
            state="disabled"
        )
        self.configure_btn.pack(side="left", padx=(0, 5))
        
        self.test_btn = ttk.Button(
            btn_frame,
            text="Test Tool",
            command=self._test_tool,
            state="disabled"
        )
        self.test_btn.pack(side="left", padx=(0, 5))
        
        ttk.Button(
            btn_frame,
            text="Batch Test",
            command=self._batch_test_tools,
            state="normal"
        ).pack(side="left", padx=(0, 5))
        
        self.schema_btn = ttk.Button(
            btn_frame,
            text="View Schema",
            command=self._view_schema,
            state="disabled"
        )
        self.schema_btn.pack(side="left", padx=(0, 5))
        
        self.delete_btn = ttk.Button(
            btn_frame,
            text="Delete Tool",
            command=self._delete_tool,
            state="disabled"
        )
        self.delete_btn.pack(side="left")
    
    def _create_overview_tab(self, parent):
        """Create overview tab content."""
        # Scrollable frame
        canvas = tk.Canvas(parent, bg="white")
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="white")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Tool information labels
        self.tool_name_label = tk.Label(
            scrollable_frame,
            text="No tool selected",
            font=("Arial", 14, "bold"),
            bg="white"
        )
        self.tool_name_label.pack(anchor="w", pady=(10, 5))
        
        self.tool_desc_label = tk.Label(
            scrollable_frame,
            text="",
            font=("Arial", 10),
            bg="white",
            wraplength=400,
            justify="left"
        )
        self.tool_desc_label.pack(anchor="w", pady=(0, 10))
        
        # Metadata frame
        self.metadata_frame = tk.Frame(scrollable_frame, bg="white")
        self.metadata_frame.pack(fill="x", pady=(0, 10))
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def _create_parameters_tab(self, parent):
        """Create parameters tab content."""
        # Parameters treeview
        param_columns = ("Name", "Type", "Required", "Description")
        self.params_tree = ttk.Treeview(parent, columns=param_columns, show="headings")
        
        for col in param_columns:
            self.params_tree.heading(col, text=col)
            self.params_tree.column(col, width=100)
        
        param_scroll = ttk.Scrollbar(parent, orient="vertical", command=self.params_tree.yview)
        self.params_tree.configure(yscrollcommand=param_scroll.set)
        
        self.params_tree.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        param_scroll.pack(side="right", fill="y", pady=10)
    
    def _create_configuration_tab(self, parent):
        """Create configuration tab content."""
        config_frame = tk.Frame(parent, bg="white")
        config_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Configuration options
        tk.Label(config_frame, text="Tool Configuration", font=("Arial", 12, "bold"), bg="white").pack(anchor="w")
        
        # Enabled checkbox
        self.enabled_var = tk.BooleanVar()
        tk.Checkbutton(
            config_frame,
            text="Enabled",
            variable=self.enabled_var,
            bg="white"
        ).pack(anchor="w", pady=(10, 5))
        
        # Security level
        security_frame = tk.Frame(config_frame, bg="white")
        security_frame.pack(fill="x", pady=(5, 0))
        
        tk.Label(security_frame, text="Security Level:", bg="white").pack(side="left")
        self.security_var = tk.StringVar()
        security_combo = ttk.Combobox(
            security_frame,
            textvariable=self.security_var,
            values=[level.value for level in SecurityLevel],
            state="readonly"
        )
        security_combo.pack(side="left", padx=(5, 0))
        
        # Rate limiting
        rate_frame = tk.Frame(config_frame, bg="white")
        rate_frame.pack(fill="x", pady=(10, 0))
        
        tk.Label(rate_frame, text="Rate Limit (per minute):", bg="white").pack(side="left")
        self.rate_limit_var = tk.StringVar(value="0")
        rate_entry = ttk.Entry(rate_frame, textvariable=self.rate_limit_var, width=10)
        rate_entry.pack(side="left", padx=(5, 0))
        
        # Daily quota
        quota_frame = tk.Frame(config_frame, bg="white")
        quota_frame.pack(fill="x", pady=(5, 0))
        
        tk.Label(quota_frame, text="Daily Quota:", bg="white").pack(side="left")
        self.daily_quota_var = tk.StringVar(value="0")
        quota_entry = ttk.Entry(quota_frame, textvariable=self.daily_quota_var, width=10)
        quota_entry.pack(side="left", padx=(5, 0))
        
        # Save button
        ttk.Button(
            config_frame,
            text="Save Configuration",
            command=self._save_configuration
        ).pack(anchor="w", pady=(20, 0))
    
    def _create_testing_tab(self, parent):
        """Create testing tab content."""
        test_frame = tk.Frame(parent, bg="white")
        test_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        tk.Label(test_frame, text="Tool Testing", font=("Arial", 12, "bold"), bg="white").pack(anchor="w")
        
        # Parameter input area
        tk.Label(test_frame, text="Parameters (JSON):", bg="white").pack(anchor="w", pady=(10, 5))
        
        self.test_params_text = tk.Text(test_frame, height=8, width=50)
        self.test_params_text.pack(fill="x", pady=(0, 10))
        
        # Test button
        ttk.Button(
            test_frame,
            text="Execute Test",
            command=self._execute_test
        ).pack(anchor="w")
        
        # Results area
        tk.Label(test_frame, text="Results:", bg="white").pack(anchor="w", pady=(20, 5))
        
        self.test_results_text = tk.Text(test_frame, height=8, width=50, state="disabled")
        self.test_results_text.pack(fill="both", expand=True)
    
    def _create_tags_tab(self, parent):
        """Create tags and related tools tab content."""
        # Tags section
        tags_section = tk.Frame(parent, bg="white")
        tags_section.pack(fill="x", padx=10, pady=10)
        
        tk.Label(tags_section, text="Tags", font=("Arial", 12, "bold"), bg="white").pack(anchor="w")
        
        # Current tags display
        self.tags_frame = tk.Frame(tags_section, bg="white")
        self.tags_frame.pack(fill="x", pady=(5, 10))
        
        # Tag management
        tag_mgmt_frame = tk.Frame(tags_section, bg="white")
        tag_mgmt_frame.pack(fill="x")
        
        tk.Label(tag_mgmt_frame, text="Add Tag:", bg="white").pack(side="left")
        self.new_tag_var = tk.StringVar()
        tag_entry = ttk.Entry(tag_mgmt_frame, textvariable=self.new_tag_var, width=20)
        tag_entry.pack(side="left", padx=(5, 0))
        
        ttk.Button(
            tag_mgmt_frame,
            text="Add",
            command=self._add_tag,
            width=8
        ).pack(side="left", padx=(5, 0))
        
        ttk.Button(
            tag_mgmt_frame,
            text="Suggest Tags",
            command=self._suggest_tags,
            width=12
        ).pack(side="left", padx=(5, 0))
        
        # Related tools section
        related_section = tk.Frame(parent, bg="white")
        related_section.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        tk.Label(related_section, text="Related Tools", font=("Arial", 12, "bold"), bg="white").pack(anchor="w")
        
        # Related tools list
        self.related_tree = ttk.Treeview(related_section, columns=("Name", "Similarity", "Shared Tags"), show="headings", height=6)
        
        self.related_tree.heading("Name", text="Tool Name")
        self.related_tree.heading("Similarity", text="Similarity")
        self.related_tree.heading("Shared Tags", text="Shared Tags")
        
        self.related_tree.column("Name", width=150)
        self.related_tree.column("Similarity", width=80)
        self.related_tree.column("Shared Tags", width=200)
        
        related_scroll = ttk.Scrollbar(related_section, orient="vertical", command=self.related_tree.yview)
        self.related_tree.configure(yscrollcommand=related_scroll.set)
        
        self.related_tree.pack(side="left", fill="both", expand=True, pady=(5, 0))
        related_scroll.pack(side="right", fill="y", pady=(5, 0))
        
        # Recommendations section
        rec_section = tk.Frame(parent, bg="white")
        rec_section.pack(fill="x", padx=10, pady=(0, 10))
        
        tk.Label(rec_section, text="Improvement Suggestions", font=("Arial", 12, "bold"), bg="white").pack(anchor="w")
        
        self.suggestions_text = tk.Text(rec_section, height=4, width=50, state="disabled", wrap="word")
        self.suggestions_text.pack(fill="x", pady=(5, 0))
    
    def _create_history_tab(self, parent):
        """Create execution history tab content."""
        # History controls
        controls_frame = tk.Frame(parent, bg="white")
        controls_frame.pack(fill="x", padx=10, pady=10)
        
        tk.Label(controls_frame, text="Execution History", font=("Arial", 12, "bold"), bg="white").pack(side="left")
        
        ttk.Button(
            controls_frame,
            text="Refresh",
            command=self._refresh_execution_history,
            width=10
        ).pack(side="right")
        
        # History table
        history_columns = ("Time", "Status", "Duration", "User", "Result")
        self.history_tree = ttk.Treeview(parent, columns=history_columns, show="headings", height=10)
        
        for col in history_columns:
            self.history_tree.heading(col, text=col)
        
        self.history_tree.column("Time", width=120)
        self.history_tree.column("Status", width=80)
        self.history_tree.column("Duration", width=80)
        self.history_tree.column("User", width=100)
        self.history_tree.column("Result", width=200)
        
        history_scroll = ttk.Scrollbar(parent, orient="vertical", command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=history_scroll.set)
        
        self.history_tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=(0, 10))
        history_scroll.pack(side="right", fill="y", pady=(0, 10))
        
        # Bind double-click to show details
        self.history_tree.bind("<Double-1>", self._show_execution_details)
    
    def _discover_tools(self):
        """Discover tools from all servers."""
        try:
            servers = self.server_manager.get_all_servers()
            if not servers:
                messagebox.showwarning("No Servers", "No MCP servers configured. Please add servers first.")
                return
            
            total_discovered = 0
            for server in servers:
                try:
                    tools = self.tool_manager.discover_tools(server.id)
                    
                    # Register discovered tools
                    for tool_info in tools:
                        try:
                            self.tool_manager.register_tool(tool_info)
                            total_discovered += 1
                        except Exception as e:
                            self.logger.error(f"Error registering tool {tool_info.name}: {e}")
                
                except Exception as e:
                    self.logger.error(f"Error discovering tools from server {server.id}: {e}")
            
            messagebox.showinfo("Discovery Complete", f"Discovered and registered {total_discovered} tools.")
            self.refresh()
            
        except Exception as e:
            self.logger.error(f"Error during tool discovery: {e}")
            messagebox.showerror("Discovery Error", f"Error discovering tools: {e}")
    
    def _on_search_changed(self, *args):
        """Handle search text change."""
        self._apply_filters()
    
    def _on_filter_changed(self, event=None):
        """Handle filter change."""
        self._apply_filters()
    
    def _apply_filters(self):
        """Apply current filters to tool list."""
        try:
            search_text = self.search_var.get().strip()
            
            if search_text:
                # Use advanced search for text queries
                filter_dict = {}
                
                # Category filter
                category_text = self.category_var.get()
                if category_text != "All":
                    filter_dict["category"] = category_text
                
                # Status filter
                status_text = self.status_var.get()
                if status_text != "All":
                    filter_dict["status"] = status_text
                
                # Get sort options
                sort_by = self.sort_var.get()
                sort_order = self.sort_order_var.get()
                
                filtered_tools = self.tool_manager.advanced_search_tools(
                    search_text, filter_dict, sort_by, sort_order
                )
            else:
                # Use regular filtering for non-text queries
                filters = ToolFilters()
                
                # Category filter
                category_text = self.category_var.get()
                if category_text != "All":
                    filters.category = ToolCategory(category_text)
                
                # Status filter
                status_text = self.status_var.get()
                if status_text != "All":
                    filters.status = ToolStatus(status_text)
                
                filtered_tools = self.tool_manager.get_tool_registry(filters)
                
                # Apply sorting
                sort_by = self.sort_var.get()
                sort_order = self.sort_order_var.get()
                reverse = sort_order == "desc"
                
                if sort_by == "name":
                    filtered_tools.sort(key=lambda x: x.name, reverse=reverse)
                elif sort_by == "category":
                    filtered_tools.sort(key=lambda x: x.category.value, reverse=reverse)
                elif sort_by == "usage_count":
                    filtered_tools.sort(key=lambda x: x.usage_count, reverse=reverse)
                elif sort_by == "success_rate":
                    filtered_tools.sort(key=lambda x: x.success_rate, reverse=reverse)
                elif sort_by == "created_at":
                    filtered_tools.sort(key=lambda x: x.created_at, reverse=reverse)
            
            self._update_tool_list(filtered_tools)
            
        except Exception as e:
            self.logger.error(f"Error applying filters: {e}")
    
    def _update_tool_list(self, tools: List[ToolRegistryEntry]):
        """Update the tool list display."""
        # Clear existing items
        for item in self.tools_tree.get_children():
            self.tools_tree.delete(item)
        
        # Add tools
        for tool in tools:
            server_name = "Unknown"
            try:
                server = self.server_manager.get_server(tool.server_id)
                if server:
                    server_name = server.name
            except:
                pass
            
            self.tools_tree.insert("", "end", values=(
                tool.name,
                tool.category.value,
                tool.status.value,
                server_name,
                tool.usage_count
            ), tags=(tool.id,))
        
        self.current_tools = tools
        self._update_status_bar()
    
    def _on_tool_selected(self, event):
        """Handle tool selection."""
        selection = self.tools_tree.selection()
        if not selection:
            self.selected_tool = None
            self._update_tool_details(None)
            return
        
        # Get selected tool ID from tags
        item = selection[0]
        tool_id = self.tools_tree.item(item, "tags")[0]
        
        # Find tool in current list
        selected_tool = None
        for tool in self.current_tools:
            if tool.id == tool_id:
                selected_tool = tool
                break
        
        self.selected_tool = selected_tool
        self._update_tool_details(selected_tool)
        self._update_status_bar()
    
    def _update_tool_details(self, tool: Optional[ToolRegistryEntry]):
        """Update tool details display."""
        if not tool:
            self.tool_name_label.config(text="No tool selected")
            self.tool_desc_label.config(text="")
            self._clear_metadata_display()
            self._clear_parameters_display()
            self._clear_configuration_display()
            
            # Disable action buttons
            self.enable_btn.config(state="disabled")
            self.configure_btn.config(state="disabled")
            self.test_btn.config(state="disabled")
            self.schema_btn.config(state="disabled")
            self.delete_btn.config(state="disabled")
            return
        
        # Update overview
        self.tool_name_label.config(text=tool.name)
        self.tool_desc_label.config(text=tool.description)
        self._update_metadata_display(tool)
        
        # Update parameters
        self._update_parameters_display(tool)
        
        # Update configuration
        self._update_configuration_display(tool)
        
        # Update tags and related tools
        self._update_tags_display(tool)
        self._update_related_tools_display(tool)
        self._update_suggestions_display(tool)
        
        # Update execution history
        self._refresh_execution_history()
        
        # Enable action buttons
        self.enable_btn.config(
            text="Disable" if tool.enabled else "Enable",
            state="normal"
        )
        
        # Enable action buttons
        self.configure_btn.config(state="normal")
        self.test_btn.config(state="normal")
        self.schema_btn.config(state="normal")
        self.delete_btn.config(state="normal")
    
    def _update_metadata_display(self, tool: ToolRegistryEntry):
        """Update metadata display."""
        # Clear existing metadata
        for widget in self.metadata_frame.winfo_children():
            widget.destroy()
        
        # Add metadata information
        metadata_info = [
            ("Category", tool.category.value),
            ("Status", tool.status.value),
            ("Security Level", tool.security_level.value),
            ("Usage Count", str(tool.usage_count)),
            ("Success Rate", f"{tool.success_rate:.2%}"),
            ("Avg Execution Time", f"{tool.average_execution_time:.2f}s"),
            ("Created", tool.created_at.strftime("%Y-%m-%d %H:%M")),
            ("Last Used", tool.last_used.strftime("%Y-%m-%d %H:%M") if tool.last_used else "Never")
        ]
        
        for i, (label, value) in enumerate(metadata_info):
            row_frame = tk.Frame(self.metadata_frame, bg="white")
            row_frame.pack(fill="x", pady=1)
            
            tk.Label(
                row_frame,
                text=f"{label}:",
                font=("Arial", 9, "bold"),
                bg="white",
                width=15,
                anchor="w"
            ).pack(side="left")
            
            tk.Label(
                row_frame,
                text=value,
                font=("Arial", 9),
                bg="white",
                anchor="w"
            ).pack(side="left")
    
    def _update_parameters_display(self, tool: ToolRegistryEntry):
        """Update parameters display."""
        # Clear existing parameters
        for item in self.params_tree.get_children():
            self.params_tree.delete(item)
        
        # Add parameters
        for param in tool.parameters:
            self.params_tree.insert("", "end", values=(
                param.name,
                param.type,
                "Yes" if param.required else "No",
                param.description[:50] + "..." if len(param.description) > 50 else param.description
            ))
    
    def _update_configuration_display(self, tool: ToolRegistryEntry):
        """Update configuration display."""
        self.enabled_var.set(tool.enabled)
        self.security_var.set(tool.security_level.value)
        
        # Set rate limiting info from permissions
        if tool.permissions:
            perm = tool.permissions[0]
            self.rate_limit_var.set(str(perm.rate_limit))
            self.daily_quota_var.set(str(perm.daily_quota))
        else:
            self.rate_limit_var.set("0")
            self.daily_quota_var.set("0")
    
    def _clear_metadata_display(self):
        """Clear metadata display."""
        for widget in self.metadata_frame.winfo_children():
            widget.destroy()
    
    def _clear_parameters_display(self):
        """Clear parameters display."""
        for item in self.params_tree.get_children():
            self.params_tree.delete(item)
    
    def _clear_configuration_display(self):
        """Clear configuration display."""
        self.enabled_var.set(False)
        self.security_var.set("")
        self.rate_limit_var.set("0")
        self.daily_quota_var.set("0")
    
    def _toggle_tool_enabled(self):
        """Toggle tool enabled status."""
        if not self.selected_tool:
            return
        
        try:
            config = ToolConfiguration(
                enabled=not self.selected_tool.enabled,
                security_level=self.selected_tool.security_level
            )
            
            success = self.tool_manager.configure_tool(self.selected_tool.id, config)
            if success:
                self.refresh()
                messagebox.showinfo("Success", f"Tool {'enabled' if config.enabled else 'disabled'} successfully.")
            else:
                messagebox.showerror("Error", "Failed to update tool configuration.")
        
        except Exception as e:
            self.logger.error(f"Error toggling tool enabled: {e}")
            messagebox.showerror("Error", f"Error updating tool: {e}")
    
    def _configure_tool(self):
        """Open tool configuration dialog."""
        if not self.selected_tool:
            return
        
        messagebox.showinfo("Configuration", "Advanced tool configuration dialog will be implemented.")
    
    def _test_tool(self):
        """Open tool testing interface."""
        if not self.selected_tool:
            return
        
        # Switch to testing tab
        self.details_notebook.select(3)  # Testing tab index
        
        # Populate test parameters with example
        example_params = {}
        for param in self.selected_tool.parameters:
            if param.default_value is not None:
                example_params[param.name] = param.default_value
            elif param.examples:
                example_params[param.name] = param.examples[0]
            else:
                example_params[param.name] = f"<{param.type}>"
        
        self.test_params_text.delete(1.0, tk.END)
        self.test_params_text.insert(1.0, json.dumps(example_params, indent=2))
    
    def _view_schema(self):
        """View tool schema."""
        if not self.selected_tool:
            return
        
        schema_window = tk.Toplevel(self)
        schema_window.title(f"Schema - {self.selected_tool.name}")
        schema_window.geometry("600x400")
        
        text_widget = tk.Text(schema_window, wrap="word")
        text_widget.pack(fill="both", expand=True, padx=10, pady=10)
        
        schema_json = json.dumps(self.selected_tool.schema, indent=2)
        text_widget.insert(1.0, schema_json)
        text_widget.config(state="disabled")
    
    def _save_configuration(self):
        """Save tool configuration."""
        if not self.selected_tool:
            return
        
        try:
            config = ToolConfiguration(
                enabled=self.enabled_var.get(),
                security_level=SecurityLevel(self.security_var.get()),
                rate_limit=int(self.rate_limit_var.get()),
                daily_quota=int(self.daily_quota_var.get())
            )
            
            success = self.tool_manager.configure_tool(self.selected_tool.id, config)
            if success:
                messagebox.showinfo("Success", "Configuration saved successfully.")
                self.refresh()
            else:
                messagebox.showerror("Error", "Failed to save configuration.")
        
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
            messagebox.showerror("Error", f"Error saving configuration: {e}")
    
    def _execute_test(self):
        """Execute tool test using the execution engine."""
        if not self.selected_tool:
            return
        
        try:
            # Get parameters from text widget
            params_text = self.test_params_text.get(1.0, tk.END).strip()
            if params_text:
                parameters = json.loads(params_text)
            else:
                parameters = {}
            
            # Show progress
            self.test_results_text.config(state="normal")
            self.test_results_text.delete(1.0, tk.END)
            self.test_results_text.insert(1.0, "Executing tool...\n")
            self.test_results_text.config(state="disabled")
            self.update()
            
            # Create execution request
            request = ExecutionRequest(
                tool_id=self.selected_tool.id,
                user_id="test_user",
                parameters=parameters,
                timeout=30
            )
            
            # Execute tool
            result = self.execution_engine.execute_tool(request, self.selected_tool)
            
            # Format results
            formatted_result = {
                "execution_id": result.execution_id,
                "success": result.success,
                "execution_time": f"{result.execution_time:.3f}s",
                "result": result.result,
                "error_message": result.error_message,
                "resource_usage": {
                    "memory_mb": f"{result.resource_usage.memory_mb:.2f}",
                    "cpu_time": f"{result.resource_usage.cpu_time:.3f}s",
                    "execution_time": f"{result.resource_usage.execution_time:.3f}s"
                },
                "parameters_used": parameters
            }
            
            # Display results
            self.test_results_text.config(state="normal")
            self.test_results_text.delete(1.0, tk.END)
            self.test_results_text.insert(1.0, json.dumps(formatted_result, indent=2))
            self.test_results_text.config(state="disabled")
            
            # Show success/error message
            if result.success:
                messagebox.showinfo("Test Complete", "Tool executed successfully!")
            else:
                messagebox.showerror("Test Failed", f"Tool execution failed: {result.error_message}")
            
        except json.JSONDecodeError as e:
            messagebox.showerror("Invalid JSON", f"Invalid JSON in parameters: {e}")
        except Exception as e:
            self.logger.error(f"Error executing test: {e}")
            messagebox.showerror("Test Error", f"Error executing test: {e}")
            
            # Show error in results
            self.test_results_text.config(state="normal")
            self.test_results_text.delete(1.0, tk.END)
            self.test_results_text.insert(1.0, f"Execution Error: {e}")
            self.test_results_text.config(state="disabled")
    
    def _show_advanced_search(self):
        """Show advanced search dialog."""
        dialog = tk.Toplevel(self)
        dialog.title("Advanced Tool Search")
        dialog.geometry("500x400")
        dialog.transient(self)
        dialog.grab_set()
        
        # Search criteria frame
        criteria_frame = tk.Frame(dialog)
        criteria_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        tk.Label(criteria_frame, text="Advanced Search Criteria", font=("Arial", 12, "bold")).pack(anchor="w")
        
        # Search text
        tk.Label(criteria_frame, text="Search Text:").pack(anchor="w", pady=(10, 0))
        search_entry = ttk.Entry(criteria_frame, width=50)
        search_entry.pack(fill="x", pady=(0, 10))
        search_entry.insert(0, self.search_var.get())
        
        # Filters frame
        filters_frame = tk.Frame(criteria_frame)
        filters_frame.pack(fill="x", pady=(0, 10))
        
        # Category filter
        tk.Label(filters_frame, text="Category:").grid(row=0, column=0, sticky="w", padx=(0, 10))
        category_var = tk.StringVar(value=self.category_var.get())
        category_combo = ttk.Combobox(
            filters_frame,
            textvariable=category_var,
            values=["All"] + [cat.value for cat in ToolCategory],
            state="readonly"
        )
        category_combo.grid(row=0, column=1, sticky="ew", padx=(0, 20))
        
        # Status filter
        tk.Label(filters_frame, text="Status:").grid(row=0, column=2, sticky="w", padx=(0, 10))
        status_var = tk.StringVar(value=self.status_var.get())
        status_combo = ttk.Combobox(
            filters_frame,
            textvariable=status_var,
            values=["All"] + [status.value for status in ToolStatus],
            state="readonly"
        )
        status_combo.grid(row=0, column=3, sticky="ew")
        
        # Security level filter
        tk.Label(filters_frame, text="Security Level:").grid(row=1, column=0, sticky="w", padx=(0, 10), pady=(10, 0))
        security_var = tk.StringVar(value="All")
        security_combo = ttk.Combobox(
            filters_frame,
            textvariable=security_var,
            values=["All"] + [level.value for level in SecurityLevel],
            state="readonly"
        )
        security_combo.grid(row=1, column=1, sticky="ew", padx=(0, 20), pady=(10, 0))
        
        # Success rate filter
        tk.Label(filters_frame, text="Min Success Rate:").grid(row=1, column=2, sticky="w", padx=(0, 10), pady=(10, 0))
        success_var = tk.StringVar(value="0.0")
        success_entry = ttk.Entry(filters_frame, textvariable=success_var, width=10)
        success_entry.grid(row=1, column=3, sticky="ew", pady=(10, 0))
        
        filters_frame.columnconfigure(1, weight=1)
        filters_frame.columnconfigure(3, weight=1)
        
        # Additional options
        options_frame = tk.Frame(criteria_frame)
        options_frame.pack(fill="x", pady=(10, 0))
        
        has_aliases_var = tk.BooleanVar()
        tk.Checkbutton(options_frame, text="Has aliases", variable=has_aliases_var).pack(side="left")
        
        recently_used_var = tk.BooleanVar()
        tk.Checkbutton(options_frame, text="Recently used (7 days)", variable=recently_used_var).pack(side="left", padx=(20, 0))
        
        # Buttons
        button_frame = tk.Frame(dialog)
        button_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        def apply_search():
            try:
                search_text = search_entry.get().strip()
                filters = {}
                
                if category_var.get() != "All":
                    filters["category"] = category_var.get()
                if status_var.get() != "All":
                    filters["status"] = status_var.get()
                if security_var.get() != "All":
                    filters["security_level"] = security_var.get()
                
                try:
                    min_success = float(success_var.get())
                    if min_success > 0:
                        filters["min_success_rate"] = min_success
                except ValueError:
                    pass
                
                if has_aliases_var.get():
                    filters["has_aliases"] = True
                if recently_used_var.get():
                    filters["recently_used"] = True
                
                # Apply search
                if search_text:
                    results = self.tool_manager.advanced_search_tools(
                        search_text, filters, self.sort_var.get(), self.sort_order_var.get()
                    )
                else:
                    # Update main filters
                    self.category_var.set(category_var.get())
                    self.status_var.set(status_var.get())
                    results = self.tool_manager.get_tool_registry()
                
                self._update_tool_list(results)
                self.search_var.set(search_text)
                
                dialog.destroy()
                
            except Exception as e:
                messagebox.showerror("Search Error", f"Error performing search: {e}")
        
        ttk.Button(button_frame, text="Search", command=apply_search).pack(side="right", padx=(10, 0))
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side="right")
    
    def _sync_tools(self):
        """Synchronize tools with all servers."""
        try:
            servers = self.server_manager.get_all_servers()
            if not servers:
                messagebox.showwarning("No Servers", "No MCP servers configured.")
                return
            
            total_stats = {"added": 0, "updated": 0, "removed": 0, "unchanged": 0}
            
            for server in servers:
                try:
                    stats = self.tool_manager.sync_tools_with_server(server.id)
                    for key in total_stats:
                        total_stats[key] += stats.get(key, 0)
                except Exception as e:
                    self.logger.error(f"Error syncing with server {server.name}: {e}")
            
            message = f"""Tool synchronization complete:
            
Added: {total_stats['added']} tools
Updated: {total_stats['updated']} tools  
Removed: {total_stats['removed']} tools
Unchanged: {total_stats['unchanged']} tools"""
            
            messagebox.showinfo("Sync Complete", message)
            self.refresh()
            
        except Exception as e:
            self.logger.error(f"Error during tool sync: {e}")
            messagebox.showerror("Sync Error", f"Error synchronizing tools: {e}")
    
    def _show_statistics(self):
        """Show tool registry statistics."""
        try:
            stats = self.tool_manager.get_tool_statistics()
            
            stats_window = tk.Toplevel(self)
            stats_window.title("Tool Registry Statistics")
            stats_window.geometry("600x500")
            stats_window.transient(self)
            
            # Create notebook for different stat categories
            notebook = ttk.Notebook(stats_window)
            notebook.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Overview tab
            overview_frame = tk.Frame(notebook)
            notebook.add(overview_frame, text="Overview")
            
            overview_text = tk.Text(overview_frame, wrap="word", state="disabled")
            overview_scroll = ttk.Scrollbar(overview_frame, orient="vertical", command=overview_text.yview)
            overview_text.configure(yscrollcommand=overview_scroll.set)
            
            overview_content = f"""Tool Registry Statistics

Total Tools: {stats.get('total_tools', 0)}
Enabled Tools: {stats.get('enabled_tools', 0)}
Disabled Tools: {stats.get('disabled_tools', 0)}

Performance Metrics:
- Average Execution Time: {stats.get('performance_metrics', {}).get('average_execution_time', 0):.3f}s
- Average Success Rate: {stats.get('performance_metrics', {}).get('average_success_rate', 0):.1%}
- Total Executions: {stats.get('performance_metrics', {}).get('total_executions', 0)}

Category Breakdown:"""
            
            for category, count in stats.get('categories', {}).items():
                overview_content += f"\n- {category}: {count}"
            
            overview_content += "\n\nSecurity Level Breakdown:"
            for level, count in stats.get('security_levels', {}).items():
                overview_content += f"\n- {level}: {count}"
            
            overview_text.config(state="normal")
            overview_text.insert(1.0, overview_content)
            overview_text.config(state="disabled")
            
            overview_text.pack(side="left", fill="both", expand=True)
            overview_scroll.pack(side="right", fill="y")
            
            # Most used tab
            usage_frame = tk.Frame(notebook)
            notebook.add(usage_frame, text="Usage")
            
            usage_text = tk.Text(usage_frame, wrap="word", state="disabled")
            usage_scroll = ttk.Scrollbar(usage_frame, orient="vertical", command=usage_text.yview)
            usage_text.configure(yscrollcommand=usage_scroll.set)
            
            usage_content = "Most Used Tools:\n\n"
            for tool in stats.get('most_used_tools', []):
                usage_content += f"- {tool['name']}: {tool['usage_count']} executions\n"
            
            usage_content += "\n\nRecently Added Tools:\n\n"
            for tool in stats.get('recently_added', []):
                usage_content += f"- {tool['name']}: {tool['created_at']}\n"
            
            usage_text.config(state="normal")
            usage_text.insert(1.0, usage_content)
            usage_text.config(state="disabled")
            
            usage_text.pack(side="left", fill="both", expand=True)
            usage_scroll.pack(side="right", fill="y")
            
        except Exception as e:
            self.logger.error(f"Error showing statistics: {e}")
            messagebox.showerror("Statistics Error", f"Error loading statistics: {e}")
    
    def refresh(self):
        """Refresh the page."""
        try:
            # Get all tools
            tools = self.tool_manager.get_tool_registry()
            self._update_tool_list(tools)
            
            # Clear selection
            self.selected_tool = None
            self._update_tool_details(None)
            
        except Exception as e:
            self.logger.error(f"Error refreshing tools page: {e}")
    
    def _add_tag(self):
        """Add a tag to the selected tool."""
        if not self.selected_tool:
            return
        
        tag = self.new_tag_var.get().strip()
        if not tag:
            return
        
        try:
            success = self.tool_manager.add_tool_tags(self.selected_tool.id, [tag])
            if success:
                self.new_tag_var.set("")
                # Refresh the tool details to show new tag
                updated_tool = self.tool_manager.get_tool_by_id(self.selected_tool.id)
                if updated_tool:
                    self.selected_tool = updated_tool
                    self._update_tags_display(updated_tool)
                messagebox.showinfo("Success", f"Tag '{tag}' added successfully.")
            else:
                messagebox.showerror("Error", "Failed to add tag.")
        
        except Exception as e:
            self.logger.error(f"Error adding tag: {e}")
            messagebox.showerror("Error", f"Error adding tag: {e}")
    
    def _suggest_tags(self):
        """Suggest tags for the selected tool."""
        if not self.selected_tool:
            return
        
        try:
            # Get suggestions from discovery engine
            analysis = self.tool_manager.discovery_engine.analyze_tool_schema(self.selected_tool.schema)
            suggested_tags = self.tool_manager.discovery_engine._generate_tags(self.selected_tool.schema)
            
            # Show suggestion dialog
            dialog = tk.Toplevel(self)
            dialog.title("Suggested Tags")
            dialog.geometry("400x300")
            dialog.transient(self)
            dialog.grab_set()
            
            tk.Label(dialog, text="Suggested Tags", font=("Arial", 12, "bold")).pack(pady=10)
            
            # Tags listbox with checkboxes
            tags_frame = tk.Frame(dialog)
            tags_frame.pack(fill="both", expand=True, padx=20, pady=10)
            
            self.tag_vars = {}
            for tag in suggested_tags:
                var = tk.BooleanVar()
                self.tag_vars[tag] = var
                tk.Checkbutton(tags_frame, text=tag, variable=var).pack(anchor="w")
            
            # Buttons
            btn_frame = tk.Frame(dialog)
            btn_frame.pack(fill="x", padx=20, pady=10)
            
            def apply_suggestions():
                selected_tags = [tag for tag, var in self.tag_vars.items() if var.get()]
                if selected_tags:
                    success = self.tool_manager.add_tool_tags(self.selected_tool.id, selected_tags)
                    if success:
                        # Refresh display
                        updated_tool = self.tool_manager.get_tool_by_id(self.selected_tool.id)
                        if updated_tool:
                            self.selected_tool = updated_tool
                            self._update_tags_display(updated_tool)
                        messagebox.showinfo("Success", f"Added {len(selected_tags)} tags.")
                    else:
                        messagebox.showerror("Error", "Failed to add tags.")
                dialog.destroy()
            
            ttk.Button(btn_frame, text="Apply Selected", command=apply_suggestions).pack(side="right", padx=(10, 0))
            ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side="right")
        
        except Exception as e:
            self.logger.error(f"Error suggesting tags: {e}")
            messagebox.showerror("Error", f"Error suggesting tags: {e}")
    
    def _remove_tag(self, tag):
        """Remove a tag from the selected tool."""
        if not self.selected_tool:
            return
        
        try:
            success = self.tool_manager.remove_tool_tags(self.selected_tool.id, [tag])
            if success:
                # Refresh display
                updated_tool = self.tool_manager.get_tool_by_id(self.selected_tool.id)
                if updated_tool:
                    self.selected_tool = updated_tool
                    self._update_tags_display(updated_tool)
                messagebox.showinfo("Success", f"Tag '{tag}' removed successfully.")
            else:
                messagebox.showerror("Error", "Failed to remove tag.")
        
        except Exception as e:
            self.logger.error(f"Error removing tag: {e}")
            messagebox.showerror("Error", f"Error removing tag: {e}")
    
    def _update_tags_display(self, tool: ToolRegistryEntry):
        """Update the tags display."""
        # Clear existing tags
        for widget in self.tags_frame.winfo_children():
            widget.destroy()
        
        # Display current tags
        if tool.metadata.tags:
            for tag in tool.metadata.tags:
                tag_frame = tk.Frame(self.tags_frame, bg="lightblue", relief="raised", bd=1)
                tag_frame.pack(side="left", padx=2, pady=2)
                
                tk.Label(tag_frame, text=tag, bg="lightblue", padx=5, pady=2).pack(side="left")
                
                # Remove button
                remove_btn = tk.Button(
                    tag_frame,
                    text="×",
                    bg="lightblue",
                    fg="red",
                    font=("Arial", 8, "bold"),
                    bd=0,
                    padx=2,
                    pady=0,
                    command=lambda t=tag: self._remove_tag(t)
                )
                remove_btn.pack(side="right")
        else:
            tk.Label(self.tags_frame, text="No tags", fg="gray", bg="white").pack(side="left")
    
    def _update_related_tools_display(self, tool: ToolRegistryEntry):
        """Update the related tools display."""
        # Clear existing items
        for item in self.related_tree.get_children():
            self.related_tree.delete(item)
        
        try:
            # Get related tools
            related = self.tool_manager.get_related_tools(tool.id)
            
            for rel in related:
                self.related_tree.insert("", "end", values=(
                    rel["name"],
                    f"{rel['similarity']:.2%}",
                    ", ".join(rel["shared_tags"])
                ))
        
        except Exception as e:
            self.logger.error(f"Error updating related tools: {e}")
    
    def _update_suggestions_display(self, tool: ToolRegistryEntry):
        """Update the improvement suggestions display."""
        try:
            suggestions = self.tool_manager.suggest_tool_improvements(tool.id)
            
            self.suggestions_text.config(state="normal")
            self.suggestions_text.delete(1.0, tk.END)
            
            if suggestions:
                for i, suggestion in enumerate(suggestions, 1):
                    self.suggestions_text.insert(tk.END, f"{i}. {suggestion}\n")
            else:
                self.suggestions_text.insert(tk.END, "No improvement suggestions available.")
            
            self.suggestions_text.config(state="disabled")
        
        except Exception as e:
            self.logger.error(f"Error updating suggestions: {e}")
    
    def _refresh_execution_history(self):
        """Refresh execution history for the selected tool."""
        if not self.selected_tool:
            return
        
        try:
            # Clear existing items
            for item in self.history_tree.get_children():
                self.history_tree.delete(item)
            
            # Get execution history for this tool
            filters = {"tool_id": self.selected_tool.id}
            executions = self.execution_engine.get_execution_history(filters)
            
            for execution in executions:
                # Format execution time
                exec_time = f"{execution.execution_time:.3f}s" if execution.execution_time else "N/A"
                
                # Format start time
                start_time = execution.start_time.strftime("%H:%M:%S") if execution.start_time else "N/A"
                
                # Format result
                result_text = "Success" if execution.result else "Failed"
                if execution.error_message:
                    result_text = execution.error_message[:50] + "..." if len(execution.error_message) > 50 else execution.error_message
                
                self.history_tree.insert("", "end", values=(
                    start_time,
                    execution.status.value,
                    exec_time,
                    execution.user_id,
                    result_text
                ), tags=(execution.id,))
        
        except Exception as e:
            self.logger.error(f"Error refreshing execution history: {e}")
    
    def _show_execution_details(self, event):
        """Show detailed execution information."""
        selection = self.history_tree.selection()
        if not selection:
            return
        
        try:
            # Get execution ID from tags
            item = selection[0]
            execution_id = self.history_tree.item(item, "tags")[0]
            
            # Get execution details
            executions = self.execution_engine.get_execution_history()
            execution = None
            for exec in executions:
                if exec.id == execution_id:
                    execution = exec
                    break
            
            if not execution:
                messagebox.showerror("Error", "Execution details not found")
                return
            
            # Show details dialog
            details_window = tk.Toplevel(self)
            details_window.title(f"Execution Details - {execution_id}")
            details_window.geometry("600x500")
            details_window.transient(self)
            
            # Create text widget with scrollbar
            text_frame = tk.Frame(details_window)
            text_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            details_text = tk.Text(text_frame, wrap="word", state="disabled")
            details_scroll = ttk.Scrollbar(text_frame, orient="vertical", command=details_text.yview)
            details_text.configure(yscrollcommand=details_scroll.set)
            
            # Format execution details
            details_content = f"""Execution Details

Execution ID: {execution.id}
Tool ID: {execution.tool_id}
User ID: {execution.user_id}
Status: {execution.status.value}

Timing:
- Start Time: {execution.start_time}
- End Time: {execution.end_time or 'N/A'}
- Execution Time: {execution.execution_time:.3f}s

Parameters:
{json.dumps(execution.parameters, indent=2)}

Result:
{json.dumps(execution.result, indent=2) if execution.result else 'No result'}

Resource Usage:
- Memory: {execution.resource_usage.memory_mb:.2f} MB
- CPU Time: {execution.resource_usage.cpu_time:.3f}s
- Network Bytes: {execution.resource_usage.network_bytes}
- Disk I/O: {execution.resource_usage.disk_io_bytes}

Error Message:
{execution.error_message or 'None'}

Sandbox ID: {execution.sandbox_id or 'N/A'}
Workflow ID: {execution.workflow_id or 'N/A'}
Parent Execution: {execution.parent_execution_id or 'N/A'}
"""
            
            details_text.config(state="normal")
            details_text.insert(1.0, details_content)
            details_text.config(state="disabled")
            
            details_text.pack(side="left", fill="both", expand=True)
            details_scroll.pack(side="right", fill="y")
        
        except Exception as e:
            self.logger.error(f"Error showing execution details: {e}")
            messagebox.showerror("Error", f"Error loading execution details: {e}")
    
    def _batch_test_tools(self):
        """Open batch testing dialog."""
        try:
            from services.tool_execution import BatchExecutionRequest, ExecutionRequest
            
            dialog = tk.Toplevel(self)
            dialog.title("Batch Tool Testing")
            dialog.geometry("700x600")
            dialog.transient(self)
            dialog.grab_set()
            
            # Main frame
            main_frame = tk.Frame(dialog)
            main_frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            tk.Label(main_frame, text="Batch Tool Testing", font=("Arial", 14, "bold")).pack(anchor="w")
            
            # Tool selection frame
            selection_frame = tk.LabelFrame(main_frame, text="Tool Selection", padx=10, pady=10)
            selection_frame.pack(fill="x", pady=(10, 0))
            
            # Available tools list
            tk.Label(selection_frame, text="Available Tools:").pack(anchor="w")
            
            tools_frame = tk.Frame(selection_frame)
            tools_frame.pack(fill="both", expand=True, pady=(5, 10))
            
            # Tools listbox with checkboxes
            self.batch_tools_frame = tk.Frame(tools_frame)
            self.batch_tools_frame.pack(fill="both", expand=True)
            
            # Populate with available tools
            self.batch_tool_vars = {}
            tools = self.tool_manager.get_tool_registry()
            
            # Create scrollable frame
            canvas = tk.Canvas(self.batch_tools_frame, height=150)
            scrollbar = ttk.Scrollbar(self.batch_tools_frame, orient="vertical", command=canvas.yview)
            scrollable_frame = tk.Frame(canvas)
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            for tool in tools[:20]:  # Limit to first 20 tools for demo
                var = tk.BooleanVar()
                self.batch_tool_vars[tool.id] = {"var": var, "tool": tool}
                
                tool_frame = tk.Frame(scrollable_frame)
                tool_frame.pack(fill="x", pady=1)
                
                tk.Checkbutton(
                    tool_frame,
                    text=f"{tool.name} ({tool.category.value})",
                    variable=var
                ).pack(side="left")
                
                tk.Label(
                    tool_frame,
                    text=tool.description[:50] + "..." if len(tool.description) > 50 else tool.description,
                    fg="gray",
                    font=("Arial", 8)
                ).pack(side="left", padx=(10, 0))
            
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # Enable mouse wheel scrolling
            def _on_mousewheel(event):
                canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            
            def _bind_to_mousewheel(event):
                canvas.bind_all("<MouseWheel>", _on_mousewheel)
            
            def _unbind_from_mousewheel(event):
                canvas.unbind_all("<MouseWheel>")
            
            canvas.bind('<Enter>', _bind_to_mousewheel)
            canvas.bind('<Leave>', _unbind_from_mousewheel)
            
            # Batch options frame
            options_frame = tk.LabelFrame(main_frame, text="Batch Options", padx=10, pady=10)
            options_frame.pack(fill="x", pady=(10, 0))
            
            # Parallel execution
            parallel_var = tk.BooleanVar(value=True)
            tk.Checkbutton(options_frame, text="Execute in parallel", variable=parallel_var).pack(anchor="w")
            
            # Max concurrent
            concurrent_frame = tk.Frame(options_frame)
            concurrent_frame.pack(fill="x", pady=(5, 0))
            tk.Label(concurrent_frame, text="Max concurrent:").pack(side="left")
            concurrent_var = tk.StringVar(value="3")
            concurrent_entry = ttk.Entry(concurrent_frame, textvariable=concurrent_var, width=5)
            concurrent_entry.pack(side="left", padx=(5, 0))
            
            # Stop on error
            stop_on_error_var = tk.BooleanVar(value=False)
            tk.Checkbutton(options_frame, text="Stop on first error", variable=stop_on_error_var).pack(anchor="w", pady=(5, 0))
            
            # Timeout
            timeout_frame = tk.Frame(options_frame)
            timeout_frame.pack(fill="x", pady=(5, 0))
            tk.Label(timeout_frame, text="Timeout (seconds):").pack(side="left")
            timeout_var = tk.StringVar(value="60")
            timeout_entry = ttk.Entry(timeout_frame, textvariable=timeout_var, width=10)
            timeout_entry.pack(side="left", padx=(5, 0))
            
            # Results frame
            results_frame = tk.LabelFrame(main_frame, text="Results", padx=10, pady=10)
            results_frame.pack(fill="both", expand=True, pady=(10, 0))
            
            results_text = tk.Text(results_frame, height=10, state="disabled")
            results_scroll = ttk.Scrollbar(results_frame, orient="vertical", command=results_text.yview)
            results_text.configure(yscrollcommand=results_scroll.set)
            
            results_text.pack(side="left", fill="both", expand=True)
            results_scroll.pack(side="right", fill="y")
            
            # Buttons frame
            buttons_frame = tk.Frame(main_frame)
            buttons_frame.pack(fill="x", pady=(10, 0))
            
            def execute_batch():
                try:
                    # Get selected tools
                    selected_tools = []
                    for tool_id, tool_data in self.batch_tool_vars.items():
                        if tool_data["var"].get():
                            selected_tools.append(tool_data["tool"])
                    
                    if not selected_tools:
                        messagebox.showwarning("No Tools Selected", "Please select at least one tool to test.")
                        return
                    
                    # Show progress
                    results_text.config(state="normal")
                    results_text.delete(1.0, tk.END)
                    results_text.insert(1.0, f"Starting batch execution of {len(selected_tools)} tools...\n\n")
                    results_text.config(state="disabled")
                    dialog.update()
                    
                    # Create batch request
                    requests = []
                    tools_dict = {}
                    
                    for tool in selected_tools:
                        # Create basic parameters for each tool
                        parameters = {}
                        for param in tool.parameters:
                            if param.required:
                                if param.type == "str":
                                    parameters[param.name] = "batch_test_value"
                                elif param.type == "int":
                                    parameters[param.name] = 42
                                elif param.type == "bool":
                                    parameters[param.name] = True
                                else:
                                    parameters[param.name] = "default"
                        
                        request = ExecutionRequest(
                            tool_id=tool.id,
                            user_id="batch_test_user",
                            parameters=parameters,
                            timeout=int(timeout_var.get())
                        )
                        requests.append(request)
                        tools_dict[tool.id] = tool
                    
                    batch_request = BatchExecutionRequest(
                        requests=requests,
                        user_id="batch_test_user",
                        parallel=parallel_var.get(),
                        max_concurrent=int(concurrent_var.get()),
                        stop_on_error=stop_on_error_var.get(),
                        timeout=int(timeout_var.get()) * len(selected_tools)
                    )
                    
                    # Execute batch
                    batch_result = self.execution_engine.execute_batch(batch_request, tools_dict)
                    
                    # Display results
                    results_content = f"""Batch Execution Complete!

Batch ID: {batch_result.batch_id}
Total Tools: {batch_result.total_requests}
Completed: {batch_result.completed}
Failed: {batch_result.failed}
Cancelled: {batch_result.cancelled}
Total Time: {batch_result.total_time:.2f}s

Individual Results:
"""
                    
                    for i, result in enumerate(batch_result.results):
                        tool_name = "Unknown"
                        for tool in selected_tools:
                            if any(req.tool_id == tool.id for req in requests if req.tool_id == tool.id):
                                tool_name = tool.name
                                break
                        
                        status = "✓ SUCCESS" if result.success else "✗ FAILED"
                        results_content += f"\n{i+1}. {tool_name}: {status} ({result.execution_time:.3f}s)"
                        if result.error_message:
                            results_content += f"\n   Error: {result.error_message}"
                    
                    if batch_result.errors:
                        results_content += f"\n\nBatch Errors:\n"
                        for error in batch_result.errors:
                            results_content += f"- {error}\n"
                    
                    results_text.config(state="normal")
                    results_text.delete(1.0, tk.END)
                    results_text.insert(1.0, results_content)
                    results_text.config(state="disabled")
                    
                    messagebox.showinfo("Batch Complete", f"Batch execution completed!\n{batch_result.completed} successful, {batch_result.failed} failed")
                
                except Exception as e:
                    self.logger.error(f"Batch execution error: {e}")
                    messagebox.showerror("Batch Error", f"Error during batch execution: {e}")
            
            ttk.Button(buttons_frame, text="Execute Batch", command=execute_batch).pack(side="left")
            ttk.Button(buttons_frame, text="Close", command=dialog.destroy).pack(side="right")
        
        except Exception as e:
            self.logger.error(f"Error opening batch test dialog: {e}")
            messagebox.showerror("Error", f"Error opening batch test dialog: {e}")
    
    def _delete_tool(self):
        """Delete the selected tool."""
        if not self.selected_tool:
            return
        
        try:
            # Confirm deletion
            result = messagebox.askyesno(
                "Confirm Deletion",
                f"Are you sure you want to delete the tool '{self.selected_tool.name}'?\n\n"
                f"This will also delete all execution history for this tool.\n"
                f"This action cannot be undone.",
                icon="warning"
            )
            
            if not result:
                return
            
            # Delete the tool
            success = self.tool_manager.delete_tool(self.selected_tool.id)
            
            if success:
                messagebox.showinfo("Success", f"Tool '{self.selected_tool.name}' has been deleted successfully.")
                
                # Clear selection and refresh
                self.selected_tool = None
                self._update_tool_details(None)
                self.refresh()
            else:
                messagebox.showerror("Error", "Failed to delete the tool. Please try again.")
        
        except Exception as e:
            self.logger.error(f"Error deleting tool: {e}")
            messagebox.showerror("Error", f"Error deleting tool: {e}")
    
    def _bulk_delete_tools(self):
        """Delete multiple selected tools."""
        try:
            # Get selected tools from the tree
            selected_items = self.tools_tree.selection()
            if not selected_items:
                messagebox.showwarning("No Selection", "Please select one or more tools to delete.")
                return
            
            # Get tool IDs and names
            tools_to_delete = []
            for item in selected_items:
                tool_id = self.tools_tree.item(item, "tags")[0]
                tool_name = self.tools_tree.item(item, "values")[0]
                tools_to_delete.append({"id": tool_id, "name": tool_name})
            
            # Confirm deletion
            tool_names = [tool["name"] for tool in tools_to_delete]
            result = messagebox.askyesno(
                "Confirm Bulk Deletion",
                f"Are you sure you want to delete {len(tools_to_delete)} tools?\n\n"
                f"Tools to delete:\n" + "\n".join(f"- {name}" for name in tool_names[:10]) +
                (f"\n... and {len(tool_names) - 10} more" if len(tool_names) > 10 else "") +
                f"\n\nThis will also delete all execution history for these tools.\n"
                f"This action cannot be undone.",
                icon="warning"
            )
            
            if not result:
                return
            
            # Delete the tools
            tool_ids = [tool["id"] for tool in tools_to_delete]
            results = self.tool_manager.bulk_delete_tools(tool_ids)
            
            # Count successes and failures
            successful = sum(1 for success in results.values() if success)
            failed = len(results) - successful
            
            if successful > 0:
                message = f"Successfully deleted {successful} tools."
                if failed > 0:
                    message += f"\nFailed to delete {failed} tools."
                messagebox.showinfo("Deletion Complete", message)
            else:
                messagebox.showerror("Deletion Failed", "Failed to delete any tools.")
            
            # Clear selection and refresh
            self.selected_tool = None
            self._update_tool_details(None)
            self.refresh()
        
        except Exception as e:
            self.logger.error(f"Error in bulk delete: {e}")
            messagebox.showerror("Error", f"Error deleting tools: {e}")
    
    def _show_context_menu(self, event):
        """Show context menu on right-click."""
        try:
            # Select the item under cursor
            item = self.tools_tree.identify_row(event.y)
            if item:
                self.tools_tree.selection_set(item)
                self.tools_tree.focus(item)
                
                # Update context menu state based on selection
                selected_items = self.tools_tree.selection()
                single_selected = len(selected_items) == 1
                any_selected = len(selected_items) > 0
                
                # Enable/disable menu items
                self.context_menu.entryconfig("Test Tool", state="normal" if single_selected else "disabled")
                self.context_menu.entryconfig("Configure Tool", state="normal" if single_selected else "disabled")
                self.context_menu.entryconfig("View Schema", state="normal" if single_selected else "disabled")
                self.context_menu.entryconfig("Delete Tool", state="normal" if single_selected else "disabled")
                self.context_menu.entryconfig("Delete Selected Tools", state="normal" if any_selected else "disabled")
                
                # Show menu
                self.context_menu.post(event.x_root, event.y_root)
        
        except Exception as e:
            self.logger.error(f"Error showing context menu: {e}")
    
    def _on_delete_key(self, event):
        """Handle Delete key press."""
        try:
            selected_items = self.tools_tree.selection()
            if not selected_items:
                return
            
            if len(selected_items) == 1:
                # Single tool deletion
                self._delete_tool()
            else:
                # Multiple tool deletion
                self._bulk_delete_tools()
        
        except Exception as e:
            self.logger.error(f"Error handling delete key: {e}")
    
    def _update_status_bar(self):
        """Update the status bar with selection information."""
        try:
            selected_items = self.tools_tree.selection()
            selected_count = len(selected_items)
            total_count = len(self.current_tools)
            
            if selected_count == 0:
                status_text = f"No tools selected ({total_count} total)"
            elif selected_count == 1:
                tool_name = self.tools_tree.item(selected_items[0], "values")[0]
                status_text = f"Selected: {tool_name} (1 of {total_count})"
            else:
                status_text = f"Selected {selected_count} tools ({total_count} total) - Press Delete to remove"
            
            self.status_label.config(text=status_text)
        
        except Exception as e:
            self.logger.error(f"Error updating status bar: {e}")
            self.status_label.config(text="Status update error")