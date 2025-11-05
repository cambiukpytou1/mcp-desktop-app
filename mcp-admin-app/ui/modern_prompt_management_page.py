"""
Modern Prompt Management Page
=============================

A redesigned prompt management page using the modern design system
with Substack-inspired aesthetics.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import Dict, Optional, Any

from models.prompt import PromptTemplate
from models.base import RiskLevel
from ui.design_system import DesignSystem, ModernScrollableFrame


class ModernPromptManagementPage(tk.Frame):
    """Modern prompt management interface with contemporary design."""
    
    def __init__(self, parent, services: Dict[str, Any]):
        super().__init__(parent, bg=DesignSystem.COLORS['background'])
        self.services = services
        self.logger = logging.getLogger(__name__)
        
        # Store tab pages
        self.tab_pages: Dict[str, tk.Frame] = {}
        self.current_tab: Optional[str] = None
        
        self._create_widgets()
        self.refresh()
    
    def _create_widgets(self):
        """Create the main prompt management interface with modern design."""
        # Main container with padding
        self.main_container = tk.Frame(self, bg=DesignSystem.COLORS['background'])
        self.main_container.pack(fill="both", expand=True, padx=DesignSystem.SPACING['xl'], pady=DesignSystem.SPACING['xl'])
        
        # Header
        self._create_header()
        
        # Quick stats dashboard
        self.stats_frame = tk.Frame(self.main_container, bg=DesignSystem.COLORS['background'])
        self.stats_frame.pack(fill="x", pady=(0, DesignSystem.SPACING['xl']))
        self._create_stats_dashboard()
        
        # Tabbed navigation
        self._create_tabbed_interface()
        
        # Status bar
        self._create_status_bar()
    
    def _create_header(self):
        """Create modern page header."""
        header_frame = tk.Frame(self.main_container, bg=DesignSystem.COLORS['background'])
        header_frame.pack(fill="x", pady=(0, DesignSystem.SPACING['xl']))
        
        # Title section
        title_section = DesignSystem.create_section_header(
            header_frame,
            "Prompt Studio",
            "Enterprise-grade prompt templating, security, and collaboration"
        )
        title_section.pack(side="left", fill="x", expand=True)     
   
        # Action buttons
        actions_frame = tk.Frame(header_frame, bg=DesignSystem.COLORS['background'])
        actions_frame.pack(side="right")
        
        # New template button
        new_btn = DesignSystem.create_button(
            actions_frame,
            "New Template",
            style='primary',
            command=self._new_template_action
        )
        new_btn.pack(side="left", padx=(0, DesignSystem.SPACING['sm']))
        
        # Refresh button
        refresh_btn = DesignSystem.create_button(
            actions_frame,
            "Refresh",
            style='secondary',
            command=self.refresh
        )
        refresh_btn.pack(side="left")
    
    def _create_stats_dashboard(self):
        """Create modern statistics dashboard."""
        # Clear existing stats
        for widget in self.stats_frame.winfo_children():
            widget.destroy()
        
        # Mock statistics - in real implementation, get from services
        total_templates = 7
        active_templates = 5
        security_alerts = 0
        active_experiments = 2
        
        # Create stats cards
        stats_container = tk.Frame(self.stats_frame, bg=DesignSystem.COLORS['background'])
        stats_container.pack(fill="x")
        
        # Total templates card
        total_card = DesignSystem.create_stats_card(
            stats_container,
            str(total_templates),
            "Total Templates",
            'text_primary'
        )
        total_card.pack(side="left", fill="both", expand=True, padx=(0, DesignSystem.SPACING['md']))
        
        # Active templates card
        active_card = DesignSystem.create_stats_card(
            stats_container,
            str(active_templates),
            "Active Templates",
            'success'
        )
        active_card.pack(side="left", fill="both", expand=True, padx=(0, DesignSystem.SPACING['md']))
        
        # Security alerts card
        security_card = DesignSystem.create_stats_card(
            stats_container,
            str(security_alerts),
            "Security Alerts",
            'success' if security_alerts == 0 else 'error'
        )
        security_card.pack(side="left", fill="both", expand=True, padx=(0, DesignSystem.SPACING['md']))
        
        # Active experiments card
        experiments_card = DesignSystem.create_stats_card(
            stats_container,
            str(active_experiments),
            "Active Experiments",
            'info'
        )
        experiments_card.pack(side="left", fill="both", expand=True)
    
    def _create_tabbed_interface(self):
        """Create modern tabbed interface."""
        # Tab container
        tab_container = tk.Frame(self.main_container, bg=DesignSystem.COLORS['background'])
        tab_container.pack(fill="both", expand=True)
        
        # Tab navigation
        tab_nav = tk.Frame(tab_container, bg=DesignSystem.COLORS['background'])
        tab_nav.pack(fill="x", pady=(0, DesignSystem.SPACING['md']))
        
        # Tab buttons
        tabs = [
            ("Templates", "templates", "📝"),
            ("Security", "security", "🛡️"),
            ("Collaboration", "collaboration", "👥"),
            ("Analytics", "analytics", "📊"),
            ("Evaluation", "evaluation", "🧪"),
        ]
        
        self.tab_buttons = {}
        
        for label, key, icon in tabs:
            def make_command(tab_key):
                return lambda: self._show_tab(tab_key)
            
            btn = DesignSystem.create_navigation_item(
                tab_nav,
                label,
                icon=icon,
                active=(key == "templates"),  # Default to templates tab
                command=make_command(key)
            )
            btn.pack(side="left", padx=(0, DesignSystem.SPACING['xs']))
            self.tab_buttons[key] = btn
        
        # Tab content area
        self.tab_content = tk.Frame(tab_container, bg=DesignSystem.COLORS['background'])
        self.tab_content.pack(fill="both", expand=True)
        
        # Initialize with templates tab
        self._show_tab("templates")
    
    def _show_tab(self, tab_key: str):
        """Show the selected tab."""
        # Update button states
        for key, button in self.tab_buttons.items():
            if key == tab_key:
                button.configure(
                    bg=DesignSystem.COLORS['accent_subtle'],
                    fg=DesignSystem.COLORS['accent_primary']
                )
            else:
                button.configure(
                    bg=DesignSystem.COLORS['surface'],
                    fg=DesignSystem.COLORS['text_secondary']
                )
        
        # Clear current content
        for widget in self.tab_content.winfo_children():
            widget.destroy()
        
        # Show selected tab content
        if tab_key == "templates":
            self._create_templates_tab()
        elif tab_key == "security":
            self._create_security_tab()
        elif tab_key == "collaboration":
            self._create_collaboration_tab()
        elif tab_key == "analytics":
            self._create_analytics_tab()
        elif tab_key == "evaluation":
            self._create_evaluation_tab()
        
        self.current_tab = tab_key
    
    def _create_templates_tab(self):
        """Create the templates tab content."""
        # Templates list with modern cards
        templates_frame = ModernScrollableFrame(self.tab_content)
        templates_frame.pack(fill="both", expand=True)
        
        # Mock template data
        templates = [
            {
                "name": "Customer Support Assistant",
                "description": "Template for customer information and complaint handling",
                "status": "Active",
                "tags": ["Customer Service", "Support"],
                "last_used": "2 hours ago"
            },
            {
                "name": "Code Review Helper",
                "description": "Assists with code review and compliance checks",
                "status": "Draft",
                "tags": ["Development", "Code Review"],
                "last_used": "1 day ago"
            }
        ]
        
        if not templates:
            # Empty state
            self._create_empty_templates_state(templates_frame.scrollable_frame)
        else:
            # Template cards
            for template in templates:
                template_card = self._create_template_card(templates_frame.scrollable_frame, template)
                template_card.pack(fill="x", pady=(0, DesignSystem.SPACING['md']))
    
    def _create_template_card(self, parent, template: dict) -> tk.Frame:
        """Create a modern template card."""
        card = DesignSystem.create_card(parent)
        card.configure(padx=DesignSystem.SPACING['lg'], pady=DesignSystem.SPACING['lg'])
        
        # Header row
        header_row = tk.Frame(card, bg=DesignSystem.COLORS['surface'])
        header_row.pack(fill="x", pady=(0, DesignSystem.SPACING['sm']))
        
        # Template name and status
        name_status_frame = tk.Frame(header_row, bg=DesignSystem.COLORS['surface'])
        name_status_frame.pack(side="left", fill="x", expand=True)
        
        # Template name
        DesignSystem.create_label(
            name_status_frame,
            template["name"],
            style='title_medium',
            bg=DesignSystem.COLORS['surface']
        ).pack(anchor="w")
        
        # Status and tags
        meta_frame = tk.Frame(name_status_frame, bg=DesignSystem.COLORS['surface'])
        meta_frame.pack(anchor="w", pady=(2, 0))
        
        # Status indicator
        status_color = DesignSystem.COLORS['success'] if template["status"] == "Active" else DesignSystem.COLORS['warning']
        status_text = f"● {template['status']}"
        
        DesignSystem.create_label(
            meta_frame,
            status_text,
            style='label_small',
            fg=status_color,
            bg=DesignSystem.COLORS['surface']
        ).pack(side="left", padx=(0, DesignSystem.SPACING['sm']))
        
        # Tags
        for tag in template["tags"]:
            tag_label = DesignSystem.create_label(
                meta_frame,
                tag,
                style='label_small',
                fg=DesignSystem.COLORS['text_secondary'],
                bg=DesignSystem.COLORS['surface_subtle']
            )
            tag_label.pack(side="left", padx=(0, DesignSystem.SPACING['xs']))
        
        # Actions
        actions_frame = tk.Frame(header_row, bg=DesignSystem.COLORS['surface'])
        actions_frame.pack(side="right")
        
        # Edit button
        edit_btn = DesignSystem.create_button(
            actions_frame,
            "Edit",
            style='primary',
            command=lambda: self._edit_template(template)
        )
        edit_btn.pack(side="left", padx=(0, DesignSystem.SPACING['sm']))
        
        # More actions button
        more_btn = DesignSystem.create_button(
            actions_frame,
            "⋯",
            style='ghost',
            command=lambda: self._show_template_menu(template)
        )
        more_btn.pack(side="left")
        
        # Description row
        if template["description"]:
            desc_row = tk.Frame(card, bg=DesignSystem.COLORS['surface'])
            desc_row.pack(fill="x", pady=(DesignSystem.SPACING['sm'], 0))
            
            DesignSystem.create_label(
                desc_row,
                template["description"],
                style='body_small',
                fg=DesignSystem.COLORS['text_secondary'],
                bg=DesignSystem.COLORS['surface']
            ).pack(anchor="w")
        
        # Add hover effect
        DesignSystem.apply_hover_effect(card, DesignSystem.COLORS['surface_subtle'])
        
        return card
    
    def _create_empty_templates_state(self, parent):
        """Create empty state for templates."""
        empty_frame = tk.Frame(parent, bg=DesignSystem.COLORS['background'])
        empty_frame.pack(fill="both", expand=True, pady=DesignSystem.SPACING['xl'])
        
        # Empty state card
        empty_card = DesignSystem.create_card(empty_frame)
        empty_card.pack(expand=True, padx=DesignSystem.SPACING['xl'], pady=DesignSystem.SPACING['xl'])
        empty_card.configure(padx=DesignSystem.SPACING['xxl'], pady=DesignSystem.SPACING['xxl'])
        
        # Icon
        DesignSystem.create_label(
            empty_card,
            "📝",
            style='display_large',
            fg=DesignSystem.COLORS['text_tertiary'],
            bg=DesignSystem.COLORS['surface']
        ).pack(pady=(0, DesignSystem.SPACING['md']))
        
        # Title
        DesignSystem.create_label(
            empty_card,
            "No templates yet",
            style='headline_medium',
            bg=DesignSystem.COLORS['surface']
        ).pack(pady=(0, DesignSystem.SPACING['sm']))
        
        # Description
        DesignSystem.create_label(
            empty_card,
            "Create your first prompt template to get started",
            style='body_medium',
            fg=DesignSystem.COLORS['text_secondary'],
            bg=DesignSystem.COLORS['surface']
        ).pack(pady=(0, DesignSystem.SPACING['lg']))
        
        # Create template button
        create_btn = DesignSystem.create_button(
            empty_card,
            "Create Your First Template",
            style='primary',
            command=self._new_template_action
        )
        create_btn.pack()
    
    def _create_security_tab(self):
        """Create the security tab content."""
        security_label = DesignSystem.create_label(
            self.tab_content,
            "Security monitoring and compliance features would be implemented here",
            style='body_large',
            fg=DesignSystem.COLORS['text_secondary'],
            bg=DesignSystem.COLORS['background']
        )
        security_label.pack(expand=True)
    
    def _create_collaboration_tab(self):
        """Create the collaboration tab content."""
        collab_label = DesignSystem.create_label(
            self.tab_content,
            "Team collaboration and sharing features would be implemented here",
            style='body_large',
            fg=DesignSystem.COLORS['text_secondary'],
            bg=DesignSystem.COLORS['background']
        )
        collab_label.pack(expand=True)
    
    def _create_analytics_tab(self):
        """Create the analytics tab content."""
        analytics_label = DesignSystem.create_label(
            self.tab_content,
            "Analytics and performance metrics would be implemented here",
            style='body_large',
            fg=DesignSystem.COLORS['text_secondary'],
            bg=DesignSystem.COLORS['background']
        )
        analytics_label.pack(expand=True)
    
    def _create_evaluation_tab(self):
        """Create the evaluation tab content."""
        eval_label = DesignSystem.create_label(
            self.tab_content,
            "A/B testing and evaluation framework would be implemented here",
            style='body_large',
            fg=DesignSystem.COLORS['text_secondary'],
            bg=DesignSystem.COLORS['background']
        )
        eval_label.pack(expand=True)
    
    def _create_status_bar(self):
        """Create modern status bar."""
        status_frame = tk.Frame(self.main_container, bg=DesignSystem.COLORS['background'])
        status_frame.pack(fill="x", pady=(DesignSystem.SPACING['md'], 0))
        
        # Add subtle divider above status
        divider = DesignSystem.create_divider(status_frame)
        divider.pack(fill="x", pady=(0, DesignSystem.SPACING['sm']))
        
        # Status content
        status_content = tk.Frame(status_frame, bg=DesignSystem.COLORS['background'])
        status_content.pack(fill="x")
        
        # Last updated
        DesignSystem.create_label(
            status_content,
            "Last updated: Just now",
            style='label_small',
            fg=DesignSystem.COLORS['text_tertiary'],
            bg=DesignSystem.COLORS['background']
        ).pack(side="left")
        
        # System status
        DesignSystem.create_label(
            status_content,
            "● All systems operational",
            style='label_small',
            fg=DesignSystem.COLORS['success'],
            bg=DesignSystem.COLORS['background']
        ).pack(side="right")
    
    def _new_template_action(self):
        """Handle new template action."""
        messagebox.showinfo("New Template", "Template creation dialog would be implemented here")
    
    def _edit_template(self, template: dict):
        """Handle edit template action."""
        messagebox.showinfo("Edit Template", f"Edit dialog for '{template['name']}' would be implemented here")
    
    def _show_template_menu(self, template: dict):
        """Show template context menu."""
        messagebox.showinfo("Template Menu", f"Context menu for '{template['name']}' would be implemented here")
    
    def refresh(self):
        """Refresh the page data."""
        try:
            # Refresh stats dashboard
            if hasattr(self, 'stats_frame'):
                self._create_stats_dashboard()
            
            # Refresh current tab
            if self.current_tab:
                self._show_tab(self.current_tab)
            
        except Exception as e:
            self.logger.error(f"Failed to refresh prompt management page: {e}")