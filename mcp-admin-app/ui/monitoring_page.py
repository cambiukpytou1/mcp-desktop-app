"""
Monitoring Dashboard Page - Placeholder
=======================================

Placeholder UI page for system monitoring dashboard.
"""

import tkinter as tk
from tkinter import ttk
import logging


class MonitoringPage(tk.Frame):
    """System monitoring dashboard page."""
    
    def __init__(self, parent, monitoring_service, server_manager):
        super().__init__(parent, bg="#f9f9f9")
        self.monitoring_service = monitoring_service
        self.server_manager = server_manager
        self.logger = logging.getLogger(__name__)
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create page widgets."""
        tk.Label(
            self,
            text="System Monitoring",
            font=("Arial", 20, "bold"),
            bg="#f9f9f9"
        ).pack(anchor="w", padx=20, pady=(20, 10))
        
        tk.Label(
            self,
            text="Real-time monitoring dashboard will be implemented here.",
            font=("Arial", 12),
            fg="#666",
            bg="#f9f9f9"
        ).pack(anchor="w", padx=20, pady=10)
    
    def refresh(self):
        """Refresh the page."""
        pass