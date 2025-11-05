"""
Prompt Management Page
======================

Main UI page for comprehensive prompt management with tabbed navigation
for templates, security, collaboration, analytics, and evaluation features.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import Dict, Optional, Any

from models.prompt import PromptTemplate
from models.base import RiskLevel


class PromptManagementPage(tk.Frame):
    """Main prompt management interface with tabbed navigation."""
    
    def __init__(self, parent, services: Dict[str, Any]):
        super().__init__(parent, bg="#f9f9f9")
        self.services = services
        self.logger = logging.getLogger(__name__)
        
        # Store tab pages
        self.tab_pages: Dict[str, tk.Frame] = {}
        self.current_tab: Optional[str] = None
        
        self._create_widgets()
        self.refresh()
    
    def _create_widgets(self):
        """Create the main prompt management interface."""
        # Header
        self._create_header()
        
        # Quick stats dashboard
        self._create_stats_dashboard()
        
        # Tabbed navigation
        self._create_tabbed_interface()
        
        # Status bar
        self._create_status_bar()
    
    def _create_header(self):
        """Create the page header with title and quick actions."""
        header_frame = tk.Frame(self, bg="#f9f9f9")
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        # Title section
        title_frame = tk.Frame(header_frame, bg="#f9f9f9")
        title_frame.pack(side="left", fill="x", expand=True)
        
        tk.Label(
            title_frame,
            text="Advanced Prompt Management",
            font=("Arial", 20, "bold"),
            bg="#f9f9f9",
            fg="#1a73e8"
        ).pack(anchor="w")
        
        tk.Label(
            title_frame,
            text="Enterprise-grade prompt templating, security, and collaboration",
            font=("Arial", 11),
            bg="#f9f9f9",
            fg="#666"
        ).pack(anchor="w", pady=(2, 0))
        
        # Quick actions
        actions_frame = tk.Frame(header_frame, bg="#f9f9f9")
        actions_frame.pack(side="right")
        
        tk.Button(
            actions_frame,
            text="+ New Template",
            bg="#1a73e8",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=15,
            pady=8,
            relief="flat",
            cursor="hand2",
            command=self._new_template_action
        ).pack(side="left", padx=(0, 10))
        
        tk.Button(
            actions_frame,
            text="🔄 Refresh",
            bg="#f8f9fa",
            fg="#333",
            font=("Arial", 10),
            padx=12,
            pady=8,
            relief="flat",
            cursor="hand2",
            command=self.refresh
        ).pack(side="left")
    
    def _create_stats_dashboard(self):
        """Create quick statistics dashboard."""
        stats_frame = tk.Frame(self, bg="#f9f9f9")
        stats_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        # Get statistics from services
        template_stats = self._get_template_statistics()
        security_stats = self._get_security_statistics()
        
        # Create stat cards
        self._create_stat_card(
            stats_frame, 
            str(template_stats.get('total', 0)), 
            "Total Templates", 
            "#ffffff"
        )
        
        self._create_stat_card(
            stats_frame, 
            str(template_stats.get('active', 0)), 
            "Active Templates", 
            "#e8f5e8", 
            "#34a853"
        )
        
        self._create_stat_card(
            stats_frame, 
            str(security_stats.get('scanned_today', 0)), 
            "Scanned Today", 
            "#e3f2fd", 
            "#1976d2"
        )
        
        self._create_stat_card(
            stats_frame, 
            str(security_stats.get('violations', 0)), 
            "Security Alerts", 
            "#ffebee" if security_stats.get('violations', 0) > 0 else "#e8f5e8", 
            "#f44336" if security_stats.get('violations', 0) > 0 else "#34a853"
        )
        
        self._create_stat_card(
            stats_frame, 
            str(template_stats.get('workspaces', 1)), 
            "Active Workspaces", 
            "#fff3e0", 
            "#ff9800"
        )
    
    def _create_stat_card(self, parent, value, label, bg_color, text_color="#1a73e8"):
        """Create a statistics card."""
        card = tk.Frame(parent, bg=bg_color, bd=1, relief="solid")
        card.pack(side="left", padx=8, ipadx=20, ipady=15, expand=True, fill="both")
        
        tk.Label(
            card,
            text=value,
            font=("Arial", 20, "bold"),
            fg=text_color,
            bg=bg_color
        ).pack()
        
        tk.Label(
            card,
            text=label,
            font=("Arial", 10),
            fg="#666",
            bg=bg_color
        ).pack()
    
    def _create_tabbed_interface(self):
        """Create the main tabbed interface for different feature areas."""
        # Tab navigation bar
        tab_nav_frame = tk.Frame(self, bg="#ffffff", bd=1, relief="solid")
        tab_nav_frame.pack(fill="x", padx=20, pady=(0, 0))
        
        # Tab buttons
        self.tab_buttons = {}
        tab_configs = [
            ("templates", "📝 Templates", "Template creation and management"),
            ("security", "🔒 Security", "Security scanning and compliance"),
            ("collaboration", "👥 Collaboration", "Team workspaces and workflows"),
            ("analytics", "📊 Analytics", "Performance insights and optimization"),
            ("evaluation", "🧪 Evaluation", "Testing and quality assurance")
        ]
        
        for tab_key, tab_label, tab_description in tab_configs:
            btn = tk.Button(
                tab_nav_frame,
                text=tab_label,
                anchor="w",
                padx=20,
                pady=12,
                relief="flat",
                bg="#ffffff",
                fg="#333",
                font=("Arial", 11),
                activebackground="#e8f0fe",
                activeforeground="#1a73e8",
                command=lambda k=tab_key: self.show_tab(k),
                cursor="hand2"
            )
            btn.pack(side="left", padx=2)
            self.tab_buttons[tab_key] = btn
        
        # Tab content area
        self.tab_content_frame = tk.Frame(self, bg="#ffffff", bd=1, relief="solid")
        self.tab_content_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        
        # Initialize tab pages (placeholder content for now)
        self._initialize_tab_pages()
        
        # Show default tab
        self.show_tab("templates")
    
    def _initialize_tab_pages(self):
        """Initialize placeholder content for each tab."""
        # Templates tab
        templates_frame = tk.Frame(self.tab_content_frame, bg="#ffffff")
        self._create_templates_tab_content(templates_frame)
        self.tab_pages["templates"] = templates_frame
        
        # Security tab
        security_frame = tk.Frame(self.tab_content_frame, bg="#ffffff")
        self._create_security_tab_content(security_frame)
        self.tab_pages["security"] = security_frame
        
        # Collaboration tab
        collaboration_frame = tk.Frame(self.tab_content_frame, bg="#ffffff")
        self._create_collaboration_tab_content(collaboration_frame)
        self.tab_pages["collaboration"] = collaboration_frame
        
        # Analytics tab
        analytics_frame = tk.Frame(self.tab_content_frame, bg="#ffffff")
        self._create_analytics_tab_content(analytics_frame)
        self.tab_pages["analytics"] = analytics_frame
        
        # Evaluation tab
        evaluation_frame = tk.Frame(self.tab_content_frame, bg="#ffffff")
        self._create_evaluation_tab_content(evaluation_frame)
        self.tab_pages["evaluation"] = evaluation_frame
    
    def _create_templates_tab_content(self, parent):
        """Create template management interface."""
        content_frame = tk.Frame(parent, bg="#ffffff")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Create paned window for list and editor
        paned_window = ttk.PanedWindow(content_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill="both", expand=True)
        
        # Left panel - Template list
        list_frame = tk.Frame(paned_window, bg="#ffffff")
        paned_window.add(list_frame, weight=1)
        
        # Template list header
        list_header = tk.Frame(list_frame, bg="#ffffff")
        list_header.pack(fill="x", pady=(0, 10))
        
        tk.Label(
            list_header,
            text="Templates",
            font=("Arial", 16, "bold"),
            bg="#ffffff",
            fg="#1a73e8"
        ).pack(side="left")
        
        tk.Button(
            list_header,
            text="+ New",
            bg="#1a73e8",
            fg="white",
            font=("Arial", 9, "bold"),
            padx=10,
            pady=5,
            relief="flat",
            cursor="hand2",
            command=self._create_new_template
        ).pack(side="right")
        
        # Template list widget
        from ui.prompt_components.template_list import TemplateListWidget
        self.template_list = TemplateListWidget(
            list_frame, 
            self.services.get('template_service'),
            on_select=self._on_template_selected
        )
        self.template_list.pack(fill="both", expand=True)
        
        # Right panel - Template editor
        editor_frame = tk.Frame(paned_window, bg="#ffffff")
        paned_window.add(editor_frame, weight=2)
        
        # Template editor
        from ui.template_editor_page import TemplateEditorPage
        self.template_editor = TemplateEditorPage(
            editor_frame,
            self.services.get('template_service'),
            on_save=self._on_template_saved
        )
        self.template_editor.pack(fill="both", expand=True)
    
    def _create_security_tab_content(self, parent):
        """Create security dashboard content."""
        from ui.security_dashboard_page import SecurityDashboardPage
        
        # Create security dashboard
        self.security_dashboard = SecurityDashboardPage(parent, self.services)
        self.security_dashboard.pack(fill="both", expand=True)
    
    def _create_collaboration_tab_content(self, parent):
        """Create placeholder content for collaboration tab."""
        content_frame = tk.Frame(parent, bg="#ffffff")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        tk.Label(
            content_frame,
            text="Team Collaboration",
            font=("Arial", 16, "bold"),
            bg="#ffffff",
            fg="#1a73e8"
        ).pack(anchor="w", pady=(0, 10))
        
        # Workspace selector
        workspace_frame = tk.Frame(content_frame, bg="#ffffff")
        workspace_frame.pack(fill="x", pady=(0, 20))
        
        tk.Label(
            workspace_frame,
            text="Current Workspace:",
            font=("Arial", 11, "bold"),
            bg="#ffffff"
        ).pack(side="left")
        
        workspace_var = tk.StringVar(value="Default Workspace")
        workspace_combo = ttk.Combobox(
            workspace_frame,
            textvariable=workspace_var,
            values=["Default Workspace", "Team Alpha", "Project Beta"],
            state="readonly",
            font=("Arial", 10)
        )
        workspace_combo.pack(side="left", padx=(10, 0))
        
        # Placeholder content
        placeholder_frame = tk.Frame(content_frame, bg="#f8f9fa", bd=1, relief="solid")
        placeholder_frame.pack(fill="both", expand=True)
        
        tk.Label(
            placeholder_frame,
            text="Collaboration features and workspace management will be implemented in subsequent tasks",
            font=("Arial", 12),
            fg="#666",
            bg="#f8f9fa"
        ).pack(expand=True)
    
    def _create_analytics_tab_content(self, parent):
        """Create placeholder content for analytics tab."""
        content_frame = tk.Frame(parent, bg="#ffffff")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        tk.Label(
            content_frame,
            text="Performance Analytics",
            font=("Arial", 16, "bold"),
            bg="#ffffff",
            fg="#1a73e8"
        ).pack(anchor="w", pady=(0, 10))
        
        # Quick metrics
        metrics_frame = tk.Frame(content_frame, bg="#ffffff")
        metrics_frame.pack(fill="x", pady=(0, 20))
        
        # Sample metrics cards
        self._create_metric_card(metrics_frame, "0", "Templates Used Today", "#e3f2fd")
        self._create_metric_card(metrics_frame, "$0.00", "Cost This Month", "#fff3e0")
        self._create_metric_card(metrics_frame, "0%", "Success Rate", "#e8f5e8")
        
        # Placeholder content
        placeholder_frame = tk.Frame(content_frame, bg="#f8f9fa", bd=1, relief="solid")
        placeholder_frame.pack(fill="both", expand=True)
        
        tk.Label(
            placeholder_frame,
            text="Analytics dashboard and insights will be implemented in subsequent tasks",
            font=("Arial", 12),
            fg="#666",
            bg="#f8f9fa"
        ).pack(expand=True)
    
    def _create_evaluation_tab_content(self, parent):
        """Create placeholder content for evaluation tab."""
        content_frame = tk.Frame(parent, bg="#ffffff")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        tk.Label(
            content_frame,
            text="Evaluation & Testing",
            font=("Arial", 16, "bold"),
            bg="#ffffff",
            fg="#1a73e8"
        ).pack(anchor="w", pady=(0, 10))
        
        # Test configuration
        config_frame = tk.Frame(content_frame, bg="#ffffff")
        config_frame.pack(fill="x", pady=(0, 20))
        
        tk.Label(
            config_frame,
            text="Test Configuration:",
            font=("Arial", 11, "bold"),
            bg="#ffffff"
        ).pack(anchor="w")
        
        tk.Label(
            config_frame,
            text="• Multi-model testing across providers",
            font=("Arial", 10),
            bg="#ffffff",
            fg="#666"
        ).pack(anchor="w", padx=(20, 0))
        
        tk.Label(
            config_frame,
            text="• Human rating and quality scoring",
            font=("Arial", 10),
            bg="#ffffff",
            fg="#666"
        ).pack(anchor="w", padx=(20, 0))
        
        tk.Label(
            config_frame,
            text="• Batch evaluation with datasets",
            font=("Arial", 10),
            bg="#ffffff",
            fg="#666"
        ).pack(anchor="w", padx=(20, 0))
        
        # Placeholder content
        placeholder_frame = tk.Frame(content_frame, bg="#f8f9fa", bd=1, relief="solid")
        placeholder_frame.pack(fill="both", expand=True)
        
        tk.Label(
            placeholder_frame,
            text="Evaluation framework and testing tools will be implemented in subsequent tasks",
            font=("Arial", 12),
            fg="#666",
            bg="#f8f9fa"
        ).pack(expand=True)
    
    def _create_metric_card(self, parent, value, label, bg_color):
        """Create a small metric card."""
        card = tk.Frame(parent, bg=bg_color, bd=1, relief="solid")
        card.pack(side="left", padx=5, ipadx=15, ipady=10, expand=True, fill="both")
        
        tk.Label(
            card,
            text=value,
            font=("Arial", 14, "bold"),
            fg="#1a73e8",
            bg=bg_color
        ).pack()
        
        tk.Label(
            card,
            text=label,
            font=("Arial", 9),
            fg="#666",
            bg=bg_color
        ).pack()
    
    def _create_status_bar(self):
        """Create status bar at bottom of page."""
        status_frame = tk.Frame(self, bg="#f8f9fa", bd=1, relief="solid")
        status_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        self.status_label = tk.Label(
            status_frame,
            text="Ready • All services operational",
            font=("Arial", 9),
            bg="#f8f9fa",
            fg="#666",
            padx=10,
            pady=5
        )
        self.status_label.pack(side="left")
        
        # Last updated indicator
        tk.Label(
            status_frame,
            text="Last updated: Just now",
            font=("Arial", 9),
            bg="#f8f9fa",
            fg="#999",
            padx=10,
            pady=5
        ).pack(side="right")
    
    def show_tab(self, tab_key: str):
        """Show the selected tab and hide others."""
        try:
            # Hide current tab
            if self.current_tab and self.current_tab in self.tab_pages:
                self.tab_pages[self.current_tab].pack_forget()
            
            # Show selected tab
            if tab_key in self.tab_pages:
                self.tab_pages[tab_key].pack(fill="both", expand=True)
                self.current_tab = tab_key
                
                # Update tab button states
                self._update_tab_buttons(tab_key)
                
                # Update status
                self._update_status(f"Viewing {tab_key.title()} • All services operational")
                
                self.logger.debug(f"Switched to tab: {tab_key}")
            else:
                self.logger.warning(f"Unknown tab requested: {tab_key}")
                
        except Exception as e:
            self.logger.error(f"Failed to show tab {tab_key}: {e}")
            messagebox.showerror("Navigation Error", f"Failed to navigate to {tab_key}")
    
    def _update_tab_buttons(self, active_tab: str):
        """Update tab button visual states."""
        for key, button in self.tab_buttons.items():
            if key == active_tab:
                button.configure(bg="#e8f0fe", fg="#1a73e8")
            else:
                button.configure(bg="#ffffff", fg="#333")
    
    def _update_status(self, message: str):
        """Update the status bar message."""
        if hasattr(self, 'status_label'):
            self.status_label.configure(text=message)
    
    def refresh(self):
        """Refresh the page data and statistics."""
        try:
            # Update statistics
            self._refresh_statistics()
            
            # Refresh current tab if it has a refresh method
            if self.current_tab and self.current_tab in self.tab_pages:
                tab_page = self.tab_pages[self.current_tab]
                if hasattr(tab_page, 'refresh'):
                    tab_page.refresh()
            
            self._update_status("Refreshed • All services operational")
            self.logger.debug("Prompt management page refreshed")
            
        except Exception as e:
            self.logger.error(f"Failed to refresh prompt management page: {e}")
            self._update_status(f"Error refreshing: {str(e)}")
    
    def _refresh_statistics(self):
        """Refresh the statistics dashboard."""
        # This would update the stat cards with fresh data
        # For now, this is a placeholder
        pass
    
    def _get_template_statistics(self) -> Dict[str, int]:
        """Get template-related statistics."""
        # Placeholder - would integrate with actual services
        return {
            'total': 0,
            'active': 0,
            'workspaces': 1
        }
    
    def _get_security_statistics(self) -> Dict[str, int]:
        """Get security-related statistics."""
        # Placeholder - would integrate with actual services
        return {
            'scanned_today': 0,
            'violations': 0
        }
    
    # Template management handlers
    def _create_new_template(self):
        """Handle new template creation."""
        if hasattr(self, 'template_editor'):
            self.template_editor._new_template()
    
    def _on_template_selected(self, template):
        """Handle template selection from list."""
        if hasattr(self, 'template_editor'):
            if template is None:
                # Create new template
                self.template_editor._new_template()
            else:
                # Load existing template
                self.template_editor.load_template(template)
    
    def _on_template_saved(self, template):
        """Handle template save event."""
        if hasattr(self, 'template_list'):
            self.template_list.refresh()
        self._update_status("Template saved successfully")
    
    # Legacy action handlers (for backward compatibility)
    def _new_template_action(self):
        """Handle new template creation."""
        self._create_new_template()
    
    def _create_template_action(self):
        """Handle create template action."""
        self._create_new_template()
    
    def _import_templates_action(self):
        """Handle template import action."""
        messagebox.showinfo("Import Templates", "Template import functionality is available through the template list widget.")
    
    def _export_templates_action(self):
        """Handle template export action."""
        messagebox.showinfo("Export Templates", "Template export functionality is available through the template list widget.")