"""
Security Indicator Widget
=========================

Reusable widget for displaying security status and alerts
with visual indicators and quick actions.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from models.base import RiskLevel


class SecurityIndicatorWidget(tk.Frame):
    """Reusable security status indicator widget."""
    
    def __init__(self, parent, security_service=None):
        super().__init__(parent, bg="#ffffff")
        self.security_service = security_service
        self.logger = logging.getLogger(__name__)
        
        self.security_status = "safe"  # safe, warning, critical
        self.alert_count = 0
        self.last_scan = None
        
        self._create_widgets()
        self.refresh()
    
    def _create_widgets(self):
        """Create the security indicator components."""
        # Main status indicator
        self._create_status_indicator()
        
        # Alert summary
        self._create_alert_summary()
        
        # Quick actions
        self._create_quick_actions()
    
    def _create_status_indicator(self):
        """Create the main security status indicator."""
        status_frame = tk.Frame(self, bg="#ffffff")
        status_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        # Status icon and text
        self.status_icon_label = tk.Label(
            status_frame,
            text="🛡️",
            font=("Arial", 20),
            bg="#ffffff"
        )
        self.status_icon_label.pack(side="left", padx=(0, 10))
        
        status_text_frame = tk.Frame(status_frame, bg="#ffffff")
        status_text_frame.pack(side="left", fill="x", expand=True)
        
        self.status_title_label = tk.Label(
            status_text_frame,
            text="Security Status",
            font=("Arial", 12, "bold"),
            bg="#ffffff",
            anchor="w"
        )
        self.status_title_label.pack(fill="x")
        
        self.status_detail_label = tk.Label(
            status_text_frame,
            text="All systems secure",
            font=("Arial", 10),
            fg="#34a853",
            bg="#ffffff",
            anchor="w"
        )
        self.status_detail_label.pack(fill="x")
        
        # Status indicator light
        self.status_light = tk.Label(
            status_frame,
            text="●",
            font=("Arial", 16),
            fg="#34a853",
            bg="#ffffff"
        )
        self.status_light.pack(side="right")
    
    def _create_alert_summary(self):
        """Create alert summary section."""
        alert_frame = tk.Frame(self, bg="#f8f9fa", bd=1, relief="solid")
        alert_frame.pack(fill="x", padx=10, pady=5)
        
        # Alert counts
        counts_frame = tk.Frame(alert_frame, bg="#f8f9fa")
        counts_frame.pack(fill="x", padx=10, pady=8)
        
        # Critical alerts
        self._create_alert_count(counts_frame, "critical", "Critical", "#d93025")
        
        # Warning alerts  
        self._create_alert_count(counts_frame, "warning", "Warnings", "#ff9800")
        
        # Info alerts
        self._create_alert_count(counts_frame, "info", "Info", "#1976d2")
        
        # Last scan info
        scan_frame = tk.Frame(alert_frame, bg="#f8f9fa")
        scan_frame.pack(fill="x", padx=10, pady=(0, 8))
        
        self.last_scan_label = tk.Label(
            scan_frame,
            text="Last scan: Never",
            font=("Arial", 9),
            fg="#666",
            bg="#f8f9fa"
        )
        self.last_scan_label.pack(side="left")
        
        # Scan status
        self.scan_status_label = tk.Label(
            scan_frame,
            text="Ready to scan",
            font=("Arial", 9),
            fg="#666",
            bg="#f8f9fa"
        )
        self.scan_status_label.pack(side="right")
    
    def _create_alert_count(self, parent, alert_type: str, label: str, color: str):
        """Create an alert count indicator."""
        count_frame = tk.Frame(parent, bg="#f8f9fa")
        count_frame.pack(side="left", padx=(0, 15))
        
        count_label = tk.Label(
            count_frame,
            text="0",
            font=("Arial", 14, "bold"),
            fg=color,
            bg="#f8f9fa"
        )
        count_label.pack()
        
        type_label = tk.Label(
            count_frame,
            text=label,
            font=("Arial", 9),
            fg="#666",
            bg="#f8f9fa"
        )
        type_label.pack()
        
        # Store references for updates
        setattr(self, f"{alert_type}_count_label", count_label)
    
    def _create_quick_actions(self):
        """Create quick action buttons."""
        actions_frame = tk.Frame(self, bg="#ffffff")
        actions_frame.pack(fill="x", padx=10, pady=(5, 10))
        
        tk.Button(
            actions_frame,
            text="Run Security Scan",
            bg="#1a73e8",
            fg="white",
            font=("Arial", 9, "bold"),
            padx=12,
            pady=6,
            relief="flat",
            cursor="hand2",
            command=self._run_security_scan
        ).pack(side="left", padx=(0, 5))
        
        tk.Button(
            actions_frame,
            text="View Alerts",
            bg="#ff9800",
            fg="white",
            font=("Arial", 9, "bold"),
            padx=12,
            pady=6,
            relief="flat",
            cursor="hand2",
            command=self._view_alerts
        ).pack(side="left", padx=(0, 5))
        
        tk.Button(
            actions_frame,
            text="Security Settings",
            bg="#666",
            fg="white",
            font=("Arial", 9, "bold"),
            padx=12,
            pady=6,
            relief="flat",
            cursor="hand2",
            command=self._security_settings
        ).pack(side="left")
        
        # Auto-scan toggle
        self.auto_scan_var = tk.BooleanVar(value=True)
        auto_scan_check = tk.Checkbutton(
            actions_frame,
            text="Auto-scan",
            variable=self.auto_scan_var,
            font=("Arial", 9),
            bg="#ffffff",
            command=self._toggle_auto_scan
        )
        auto_scan_check.pack(side="right")
    
    def update_status(self, status: str, message: str, alert_counts: Dict[str, int] = None):
        """Update the security status display."""
        self.security_status = status
        
        # Update status colors and icons
        status_colors = {
            "safe": ("#34a853", "🛡️", "All systems secure"),
            "warning": ("#ff9800", "⚠️", "Security warnings detected"),
            "critical": ("#d93025", "🚨", "Critical security issues found")
        }
        
        color, icon, default_message = status_colors.get(status, status_colors["safe"])
        
        self.status_icon_label.configure(text=icon)
        self.status_detail_label.configure(text=message or default_message, fg=color)
        self.status_light.configure(fg=color)
        
        # Update alert counts
        if alert_counts:
            for alert_type, count in alert_counts.items():
                if hasattr(self, f"{alert_type}_count_label"):
                    getattr(self, f"{alert_type}_count_label").configure(text=str(count))
        
        # Update last scan time
        self.last_scan = datetime.now()
        self.last_scan_label.configure(
            text=f"Last scan: {self.last_scan.strftime('%H:%M:%S')}"
        )
        
        self.logger.debug(f"Security status updated: {status}")
    
    def set_scanning(self, is_scanning: bool):
        """Update the scanning status."""
        if is_scanning:
            self.scan_status_label.configure(text="Scanning...", fg="#1976d2")
        else:
            self.scan_status_label.configure(text="Ready to scan", fg="#666")
    
    def refresh(self):
        """Refresh the security status from the service."""
        try:
            # This would get actual security status from the service
            # For now, using placeholder data
            self.update_status("safe", "All systems secure", {
                "critical": 0,
                "warning": 0,
                "info": 0
            })
            
            self.logger.debug("Security indicator refreshed")
            
        except Exception as e:
            self.logger.error(f"Failed to refresh security indicator: {e}")
            self.update_status("warning", f"Error checking security: {str(e)}")
    
    # Action handlers (placeholders)
    def _run_security_scan(self):
        """Handle security scan request."""
        self.set_scanning(True)
        
        # Simulate scan
        self.after(2000, lambda: [
            self.set_scanning(False),
            self.update_status("safe", "Scan completed - no issues found", {
                "critical": 0,
                "warning": 0,
                "info": 1
            })
        ])
        
        messagebox.showinfo("Security Scan", "Security scan started. This will be implemented in subsequent tasks.")
    
    def _view_alerts(self):
        """Handle view alerts request."""
        messagebox.showinfo("Coming Soon", "Alert viewer will be implemented in subsequent tasks.")
    
    def _security_settings(self):
        """Handle security settings request."""
        messagebox.showinfo("Coming Soon", "Security settings will be implemented in subsequent tasks.")
    
    def _toggle_auto_scan(self):
        """Handle auto-scan toggle."""
        enabled = self.auto_scan_var.get()
        status = "enabled" if enabled else "disabled"
        messagebox.showinfo("Auto-scan", f"Auto-scan {status}. This will be implemented in subsequent tasks.")