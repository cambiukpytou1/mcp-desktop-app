"""
LLM Providers Page - Placeholder
================================

Placeholder UI page for managing LLM providers.
"""

import tkinter as tk
from tkinter import ttk
import logging


class LLMPage(tk.Frame):
    """LLM providers management page."""
    
    def __init__(self, parent, llm_manager):
        super().__init__(parent, bg="#f9f9f9")
        self.llm_manager = llm_manager
        self.logger = logging.getLogger(__name__)
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create page widgets."""
        tk.Label(
            self,
            text="LLM Providers",
            font=("Arial", 20, "bold"),
            bg="#f9f9f9"
        ).pack(anchor="w", padx=20, pady=(20, 10))
        
        tk.Label(
            self,
            text="LLM provider management features will be implemented here.",
            font=("Arial", 12),
            fg="#666",
            bg="#f9f9f9"
        ).pack(anchor="w", padx=20, pady=10)
    
    def refresh(self):
        """Refresh the page."""
        pass