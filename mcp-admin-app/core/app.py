"""
Enhanced MCP Admin Application
==============================

Main application class extending the original prototype with comprehensive
server management, security logging, audit trails, and LLM provider integration.
Features a modern, Substack-inspired design system.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import Dict, Optional

from .config import ConfigurationManager
from data.database import DatabaseManager
from services.server_manager import ServerManager
from services.tool_manager import AdvancedToolManager
from services.prompt_manager import PromptManager
from services.security_service import SecurityService
from services.audit_service import AuditService
from services.llm_manager import LLMManager
from services.monitoring_service import MonitoringService

from ui.modern_servers_page import ModernServersPage
from ui.tools_page import ToolsPage
from ui.prompts_page import PromptsPage
from ui.modern_prompt_management_page import ModernPromptManagementPage
from ui.security_page import SecurityPage
from ui.security_dashboard_page import SecurityDashboardPage
from ui.audit_page import AuditPage
from ui.llm_page import LLMPage
from ui.monitoring_page import MonitoringPage
from ui.collaboration_page import CollaborationPage
from ui.analytics_dashboard_page import AnalyticsDashboardPage
from ui.evaluation_testing_page import EvaluationTestingPage
from ui.service_bridge import UIServiceBridge
from ui.state_manager import initialize_state_manager
from ui.accessibility_utils import setup_accessibility
from ui.design_system import DesignSystem


class MCPAdminApp(tk.Tk):
    """Enhanced MCP Administration Application."""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # Initialize configuration and database
        self.config_manager = ConfigurationManager()
        self.db_manager = DatabaseManager(self.config_manager.database_path)
        
        # Initialize UI infrastructure
        self.state_manager = initialize_state_manager()
        self.service_bridge = UIServiceBridge(self.config_manager, self.db_manager)
        
        # Initialize services
        self._initialize_services()
        
        # Setup UI
        self._setup_ui()
        
        # Setup accessibility
        self.accessibility = setup_accessibility(self)
        
        # Initialize pages
        self._initialize_pages()
        
        # Start monitoring
        self._start_monitoring()
        
        self.logger.info("MCP Admin Application initialized")
    
    def _initialize_services(self):
        """Initialize all application services."""
        try:
            # Initialize database
            self.db_manager.initialize()
            
            # Initialize core services
            self.server_manager = ServerManager(self.config_manager, self.db_manager)
            self.tool_manager = AdvancedToolManager(self.db_manager)
            self.prompt_manager = PromptManager(self.config_manager, self.db_manager)
            self.security_service = SecurityService(self.db_manager)
            self.audit_service = AuditService(self.db_manager)
            self.llm_manager = LLMManager(self.config_manager, self.db_manager)
            self.monitoring_service = MonitoringService(self.db_manager, self.server_manager)
            
            self.logger.info("All services initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize services: {e}")
            messagebox.showerror("Initialization Error", f"Failed to initialize application services: {e}")
            raise
    
    def _setup_ui(self):
        """Setup the main application UI with modern design."""
        self.title("MCP Admin")
        self.geometry("1400x900")
        self.configure(bg=DesignSystem.COLORS['background'])
        
        # Set minimum size for responsive design
        self.minsize(1200, 700)
        
        # Create main layout with modern styling
        self.sidebar = tk.Frame(
            self, 
            width=280, 
            bg=DesignSystem.COLORS['surface'],
            relief="flat",
            bd=0
        )
        self.sidebar.pack(side="left", fill="y", padx=(0, 1))
        self.sidebar.pack_propagate(False)  # Maintain fixed width
        
        # Add subtle border to sidebar
        border = tk.Frame(self, width=1, bg=DesignSystem.COLORS['border'])
        border.pack(side="left", fill="y")
        
        self.content = tk.Frame(self, bg=DesignSystem.COLORS['background'])
        self.content.pack(side="right", fill="both", expand=True)
        
        # Dictionary to store page instances
        self.pages: Dict[str, tk.Frame] = {}
        self.current_page: Optional[str] = None
        
        # Create navigation
        self._create_navigation()
    
    def _create_navigation(self):
        """Create modern navigation sidebar."""
        # Application header
        header_frame = tk.Frame(self.sidebar, bg=DesignSystem.COLORS['surface'])
        header_frame.pack(fill="x", padx=DesignSystem.SPACING['lg'], pady=(DesignSystem.SPACING['xl'], DesignSystem.SPACING['lg']))
        
        # Logo/Brand area
        brand_frame = tk.Frame(header_frame, bg=DesignSystem.COLORS['surface'])
        brand_frame.pack(fill="x")
        
        DesignSystem.create_label(
            brand_frame,
            "MCP Admin",
            style='headline_large',
            fg=DesignSystem.COLORS['accent_primary'],
            bg=DesignSystem.COLORS['surface']
        ).pack(anchor="w")
        
        DesignSystem.create_label(
            brand_frame,
            "Modern server management",
            style='body_small',
            fg=DesignSystem.COLORS['text_secondary'],
            bg=DesignSystem.COLORS['surface']
        ).pack(anchor="w", pady=(2, 0))
        
        # Add subtle divider
        divider = DesignSystem.create_divider(self.sidebar)
        divider.pack(fill="x", padx=DesignSystem.SPACING['lg'], pady=DesignSystem.SPACING['md'])
        
        # Navigation section
        nav_frame = tk.Frame(self.sidebar, bg=DesignSystem.COLORS['surface'])
        nav_frame.pack(fill="both", expand=True, padx=DesignSystem.SPACING['md'])
        
        # Navigation items with modern icons
        nav_items = [
            ("Servers", "servers", "⚡"),
            ("Tools", "tools", "🔧"),
            ("Prompts", "prompts", "✨"),
            ("Prompt Studio", "prompt_management", "🎨"),
            ("LLM Providers", "llm", "🤖"),
            ("Security Center", "security_dashboard", "🛡️"),
            ("Security Logs", "security", "🔒"),
            ("Collaboration", "collaboration", "👥"),
            ("Analytics", "analytics", "📊"),
            ("Testing Lab", "evaluation", "🧪"),
            ("Monitoring", "monitoring", "📈"),
            ("Audit Trail", "audit", "📋"),
        ]
        
        self.nav_buttons = {}
        
        for label, key, icon in nav_items:
            def make_command(page_key):
                return lambda: self.show_page(page_key)
            
            btn = DesignSystem.create_navigation_item(
                nav_frame,
                label,
                icon=icon,
                active=False,
                command=make_command(key)
            )
            btn.pack(fill="x", pady=1)
            self.nav_buttons[key] = btn
            
            # Add hover effect
            DesignSystem.apply_hover_effect(btn)
        
        # Status indicator at bottom
        self._create_status_indicator()
    
    def _create_status_indicator(self):
        """Create modern status indicator at bottom of sidebar."""
        status_frame = tk.Frame(self.sidebar, bg=DesignSystem.COLORS['surface'])
        status_frame.pack(side="bottom", fill="x", padx=DesignSystem.SPACING['lg'], pady=DesignSystem.SPACING['lg'])
        
        # Add subtle divider above status
        divider = DesignSystem.create_divider(self.sidebar)
        divider.pack(side="bottom", fill="x", padx=DesignSystem.SPACING['lg'], pady=(0, DesignSystem.SPACING['md']))
        
        # Status indicator with modern styling
        status_container = DesignSystem.create_card(status_frame)
        status_container.pack(fill="x")
        status_container.configure(padx=DesignSystem.SPACING['md'], pady=DesignSystem.SPACING['sm'])
        
        self.status_label = DesignSystem.create_label(
            status_container,
            "● System Ready",
            style='label_small',
            fg=DesignSystem.COLORS['success'],
            bg=DesignSystem.COLORS['surface']
        )
        self.status_label.pack()
        
        # Database status with modern styling
        db_size = self.db_manager.get_database_size()
        size_text = f"Database: {db_size // 1024}KB" if db_size > 0 else "Database: Empty"
        
        self.db_status_label = DesignSystem.create_label(
            status_container,
            size_text,
            style='label_small',
            fg=DesignSystem.COLORS['text_tertiary'],
            bg=DesignSystem.COLORS['surface']
        )
        self.db_status_label.pack()
    
    def _initialize_pages(self):
        """Initialize all application pages."""
        try:
            print("DEBUG: Starting page initialization...")
            
            # Create page instances
            try:
                print("DEBUG: Creating modern servers page...")
                self.pages["servers"] = ModernServersPage(self.content, self.server_manager, self.monitoring_service)
                print("DEBUG: Modern servers page created successfully")
            except Exception as e:
                print(f"DEBUG: Failed to create modern servers page: {e}")
            
            try:
                print("DEBUG: Creating tools page...")
                self.pages["tools"] = ToolsPage(self.content, self.tool_manager, self.server_manager)
                print("DEBUG: Tools page created successfully")
            except Exception as e:
                print(f"DEBUG: Failed to create tools page: {e}")
            
            try:
                print("DEBUG: Creating prompts page...")
                self.pages["prompts"] = PromptsPage(self.content, self.prompt_manager, self.tool_manager)
                print("DEBUG: Prompts page created successfully")
            except Exception as e:
                print(f"DEBUG: Failed to create prompts page: {e}")
            
            # Advanced prompt management with all services
            try:
                print("DEBUG: Creating modern prompt management page...")
                prompt_services = {
                    'template_service': self.prompt_manager,
                    'security_service': self.security_service,
                    'collaboration_service': None,  # Placeholder for collaboration service
                    'analytics_service': None,      # Placeholder for analytics service
                    'evaluation_service': None      # Placeholder for evaluation service
                }
                self.pages["prompt_management"] = ModernPromptManagementPage(self.content, prompt_services)
                print("DEBUG: Modern prompt management page created successfully")
            except Exception as e:
                print(f"DEBUG: Failed to create modern prompt management page: {e}")
            
            # New integrated pages
            try:
                print("DEBUG: Creating security dashboard page...")
                security_services = {
                    'security_scanner': self.security_service,
                    'config_manager': self.config_manager,
                    'db_manager': self.db_manager
                }
                self.pages["security_dashboard"] = SecurityDashboardPage(self.content, security_services)
                print("DEBUG: Security dashboard page created successfully")
            except Exception as e:
                print(f"DEBUG: Failed to create security dashboard page: {e}")
            
            try:
                print("DEBUG: Creating analytics page...")
                self.pages["analytics"] = AnalyticsDashboardPage(self.content, self.config_manager, self.db_manager)
                print("DEBUG: Analytics page created successfully")
            except Exception as e:
                print(f"DEBUG: Failed to create analytics page: {e}")
            
            try:
                print("DEBUG: Creating evaluation page...")
                self.pages["evaluation"] = EvaluationTestingPage(self.content, self.config_manager, self.db_manager)
                print("DEBUG: Evaluation page created successfully")
            except Exception as e:
                print(f"DEBUG: Failed to create evaluation page: {e}")
            
            # Existing pages
            try:
                print("DEBUG: Creating LLM page...")
                self.pages["llm"] = LLMPage(self.content, self.llm_manager)
                print("DEBUG: LLM page created successfully")
            except Exception as e:
                print(f"DEBUG: Failed to create LLM page: {e}")
            
            try:
                print("DEBUG: Creating security page...")
                self.pages["security"] = SecurityPage(self.content, self.security_service)
                print("DEBUG: Security page created successfully")
            except Exception as e:
                print(f"DEBUG: Failed to create security page: {e}")
            
            try:
                print("DEBUG: Creating audit page...")
                self.pages["audit"] = AuditPage(self.content, self.audit_service)
                print("DEBUG: Audit page created successfully")
            except Exception as e:
                print(f"DEBUG: Failed to create audit page: {e}")
            
            try:
                print("DEBUG: Creating monitoring page...")
                self.pages["monitoring"] = MonitoringPage(self.content, self.monitoring_service, self.server_manager)
                print("DEBUG: Monitoring page created successfully")
            except Exception as e:
                print(f"DEBUG: Failed to create monitoring page: {e}")
            
            print(f"DEBUG: Successfully created pages: {list(self.pages.keys())}")
            
            # Show initial page
            print("DEBUG: Showing initial page: prompt_management")
            self.show_page("prompt_management")
            
            self.logger.info("All pages initialized successfully")
            
        except Exception as e:
            print(f"DEBUG: Failed to initialize pages: {e}")
            self.logger.error(f"Failed to initialize pages: {e}")
            messagebox.showerror("UI Error", f"Failed to initialize user interface: {e}")
    
    def show_page(self, page_key: str):
        """Display the selected page and hide others."""
        try:
            print(f"DEBUG: Attempting to show page: {page_key}")
            print(f"DEBUG: Available pages: {list(self.pages.keys())}")
            print(f"DEBUG: Current page: {self.current_page}")
            
            # Hide current page
            if self.current_page and self.current_page in self.pages:
                print(f"DEBUG: Hiding current page: {self.current_page}")
                self.pages[self.current_page].pack_forget()
            
            # Show selected page
            if page_key in self.pages:
                print(f"DEBUG: Showing page: {page_key}")
                self.pages[page_key].pack(fill="both", expand=True)
                self.current_page = page_key
                
                # Update navigation button states
                self._update_nav_buttons(page_key)
                
                # Refresh page data
                if hasattr(self.pages[page_key], 'refresh'):
                    print(f"DEBUG: Refreshing page: {page_key}")
                    self.pages[page_key].refresh()
                
                print(f"DEBUG: Successfully switched to page: {page_key}")
                self.logger.debug(f"Switched to page: {page_key}")
            else:
                print(f"DEBUG: Page {page_key} not found in pages dictionary")
                self.logger.warning(f"Unknown page requested: {page_key}")
                
        except Exception as e:
            print(f"DEBUG: Error showing page {page_key}: {e}")
            self.logger.error(f"Failed to show page {page_key}: {e}")
            messagebox.showerror("Navigation Error", f"Failed to navigate to {page_key}")
    
    def _update_nav_buttons(self, active_page: str):
        """Update navigation button visual states with modern styling."""
        for key, button in self.nav_buttons.items():
            if key == active_page:
                button.configure(
                    bg=DesignSystem.COLORS['accent_subtle'],
                    fg=DesignSystem.COLORS['accent_primary']
                )
            else:
                button.configure(
                    bg=DesignSystem.COLORS['surface'],
                    fg=DesignSystem.COLORS['text_secondary']
                )
    
    def _start_monitoring(self):
        """Start background monitoring services."""
        try:
            # Start server health monitoring
            self.monitoring_service.start_monitoring()
            
            # Schedule periodic updates
            self._schedule_updates()
            
            self.logger.info("Monitoring services started")
            
        except Exception as e:
            self.logger.error(f"Failed to start monitoring: {e}")
    
    def _schedule_updates(self):
        """Schedule periodic UI updates."""
        # Update status every 5 seconds
        self.after(5000, self._update_status)
        
        # Refresh current page every 10 seconds
        self.after(10000, self._refresh_current_page)
    
    def _update_status(self):
        """Update application status indicator."""
        try:
            # Update database size
            db_size = self.db_manager.get_database_size()
            size_text = f"Database: {db_size // 1024}KB" if db_size > 0 else "Database: Empty"
            
            # Update the status label directly
            if hasattr(self, 'db_status_label'):
                self.db_status_label.configure(text=size_text)
            
            # Schedule next update
            self.after(5000, self._update_status)
            
        except Exception as e:
            self.logger.error(f"Failed to update status: {e}")
    
    def _refresh_current_page(self):
        """Refresh the currently displayed page."""
        try:
            if self.current_page and self.current_page in self.pages:
                page = self.pages[self.current_page]
                if hasattr(page, 'refresh'):
                    page.refresh()
            
            # Schedule next refresh
            self.after(10000, self._refresh_current_page)
            
        except Exception as e:
            self.logger.error(f"Failed to refresh current page: {e}")
    
    def on_closing(self):
        """Handle application closing."""
        try:
            self.logger.info("Application closing")
            
            # Stop monitoring services
            if hasattr(self, 'monitoring_service'):
                self.monitoring_service.stop_monitoring()
            
            # Close database connections
            # (Connections are closed automatically with context managers)
            
            self.destroy()
            
        except Exception as e:
            self.logger.error(f"Error during application shutdown: {e}")
            self.destroy()
    
    def show_error(self, title: str, message: str):
        """Show error dialog."""
        messagebox.showerror(title, message)
    
    def show_info(self, title: str, message: str):
        """Show info dialog."""
        messagebox.showinfo(title, message)
    
    def show_warning(self, title: str, message: str):
        """Show warning dialog."""
        messagebox.showwarning(title, message)