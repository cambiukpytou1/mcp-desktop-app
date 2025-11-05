"""
Security Dashboard Page
======================

Security status dashboard with traffic light indicators, real-time scan results,
and security policy configuration interface.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta

from services.security.security_scanner import SecurityScanner, SecurityScanResult, SecurityRiskLevel, SecurityIssueType
from services.security.compliance_governance import ComplianceGovernanceFramework, ComplianceAssessment, ComplianceStatus
from models.base import generate_id


class SecurityStatusIndicator(tk.Frame):
    """Traffic light style security status indicator."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg="#ffffff", **kwargs)
        self.current_status = SecurityRiskLevel.LOW
        self._create_widgets()
    
    def _create_widgets(self):
        """Create the status indicator widgets."""
        # Status circle
        self.status_canvas = tk.Canvas(self, width=40, height=40, bg="#ffffff", highlightthickness=0)
        self.status_canvas.pack(side="left", padx=(0, 10))
        
        # Status text
        self.status_label = tk.Label(
            self,
            text="Security Status: All Clear",
            font=("Arial", 12, "bold"),
            bg="#ffffff",
            fg="#34a853"
        )
        self.status_label.pack(side="left", anchor="w")
        
        # Update display
        self.update_status(SecurityRiskLevel.LOW)
    
    def update_status(self, risk_level: SecurityRiskLevel, message: str = None):
        """Update the security status indicator."""
        self.current_status = risk_level
        
        # Clear canvas
        self.status_canvas.delete("all")
        
        # Color mapping
        colors = {
            SecurityRiskLevel.LOW: ("#34a853", "All Clear"),
            SecurityRiskLevel.MEDIUM: ("#fbbc04", "Medium Risk"),
            SecurityRiskLevel.HIGH: ("#ea4335", "High Risk"),
            SecurityRiskLevel.CRITICAL: ("#d93025", "Critical Risk")
        }
        
        color, default_message = colors.get(risk_level, ("#666", "Unknown"))
        display_message = message or default_message
        
        # Draw status circle
        self.status_canvas.create_oval(8, 8, 32, 32, fill=color, outline=color)
        
        # Update text
        self.status_label.configure(
            text=f"Security Status: {display_message}",
            fg=color
        )


class SecurityViolationsList(tk.Frame):
    """List widget for displaying security violations with severity levels."""
    
    def __init__(self, parent, on_violation_select: Callable = None, **kwargs):
        super().__init__(parent, **kwargs)
        self.on_violation_select = on_violation_select
        self.violations: List[Dict[str, Any]] = []
        self._create_widgets()
    
    def _create_widgets(self):
        """Create the violations list widgets."""
        # Header
        header_frame = tk.Frame(self, bg="#f8f9fa")
        header_frame.pack(fill="x", pady=(0, 1))
        
        tk.Label(
            header_frame,
            text="Security Violations",
            font=("Arial", 12, "bold"),
            bg="#f8f9fa",
            fg="#333",
            padx=10,
            pady=8
        ).pack(side="left")
        
        # Violations tree
        columns = ("severity", "type", "description", "prompt", "detected")
        self.violations_tree = ttk.Treeview(
            self,
            columns=columns,
            show="headings",
            height=8
        )
        
        # Configure columns
        self.violations_tree.heading("severity", text="Severity")
        self.violations_tree.heading("type", text="Type")
        self.violations_tree.heading("description", text="Description")
        self.violations_tree.heading("prompt", text="Prompt")
        self.violations_tree.heading("detected", text="Detected")
        
        self.violations_tree.column("severity", width=80, minwidth=80)
        self.violations_tree.column("type", width=120, minwidth=100)
        self.violations_tree.column("description", width=300, minwidth=200)
        self.violations_tree.column("prompt", width=150, minwidth=100)
        self.violations_tree.column("detected", width=120, minwidth=100)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.violations_tree.yview)
        self.violations_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack widgets
        self.violations_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind selection event
        if self.on_violation_select:
            self.violations_tree.bind("<<TreeviewSelect>>", self._on_violation_selected)
    
    def _on_violation_selected(self, event):
        """Handle violation selection."""
        selection = self.violations_tree.selection()
        if selection and self.on_violation_select:
            item_id = selection[0]
            violation_data = self.violations_tree.item(item_id)
            # Find the full violation data
            for violation in self.violations:
                if violation.get('id') == item_id:
                    self.on_violation_select(violation)
                    break
    
    def update_violations(self, violations: List[Dict[str, Any]]):
        """Update the violations list."""
        # Clear existing items
        for item in self.violations_tree.get_children():
            self.violations_tree.delete(item)
        
        self.violations = violations
        
        # Add new violations
        for violation in violations:
            severity = violation.get('risk_level', 'unknown').upper()
            issue_type = violation.get('issue_type', 'unknown').replace('_', ' ').title()
            description = violation.get('title', 'Unknown Issue')
            prompt_id = violation.get('prompt_id', 'N/A')[:15] + "..." if len(violation.get('prompt_id', '')) > 15 else violation.get('prompt_id', 'N/A')
            detected = violation.get('detected_at', datetime.now().isoformat())[:16].replace('T', ' ')
            
            # Insert with severity-based tag for coloring
            item_id = self.violations_tree.insert(
                "",
                "end",
                iid=violation.get('id', generate_id()),
                values=(severity, issue_type, description, prompt_id, detected),
                tags=(severity.lower(),)
            )
        
        # Configure severity colors
        self.violations_tree.tag_configure("critical", background="#ffebee", foreground="#d32f2f")
        self.violations_tree.tag_configure("high", background="#fff3e0", foreground="#f57c00")
        self.violations_tree.tag_configure("medium", background="#f3e5f5", foreground="#7b1fa2")
        self.violations_tree.tag_configure("low", background="#e8f5e8", foreground="#388e3c")


class SecurityPolicyPanel(tk.Frame):
    """Panel for configuring security policies."""
    
    def __init__(self, parent, security_scanner: SecurityScanner, **kwargs):
        super().__init__(parent, bg="#ffffff", **kwargs)
        self.security_scanner = security_scanner
        self.policy_vars = {}
        self._create_widgets()
        self._load_current_policy()
    
    def _create_widgets(self):
        """Create the policy configuration widgets."""
        # Header
        header_frame = tk.Frame(self, bg="#ffffff")
        header_frame.pack(fill="x", pady=(0, 15))
        
        tk.Label(
            header_frame,
            text="Security Policy Configuration",
            font=("Arial", 14, "bold"),
            bg="#ffffff",
            fg="#1a73e8"
        ).pack(side="left")
        
        tk.Button(
            header_frame,
            text="Save Policy",
            bg="#1a73e8",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=15,
            pady=6,
            relief="flat",
            cursor="hand2",
            command=self._save_policy
        ).pack(side="right")
        
        # Scrollable frame for policy options
        canvas = tk.Canvas(self, bg="#ffffff")
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#ffffff")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Policy sections
        self._create_pii_policy_section(scrollable_frame)
        self._create_secret_policy_section(scrollable_frame)
        self._create_code_policy_section(scrollable_frame)
        self._create_injection_policy_section(scrollable_frame)
        self._create_malicious_policy_section(scrollable_frame)
        
        # Pack scrollable components
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def _create_policy_section(self, parent, title: str, policies: Dict[str, Dict]):
        """Create a policy configuration section."""
        section_frame = tk.LabelFrame(
            parent,
            text=title,
            font=("Arial", 11, "bold"),
            bg="#ffffff",
            fg="#333",
            padx=10,
            pady=10
        )
        section_frame.pack(fill="x", pady=(0, 15), padx=5)
        
        for policy_key, policy_info in policies.items():
            policy_frame = tk.Frame(section_frame, bg="#ffffff")
            policy_frame.pack(fill="x", pady=2)
            
            # Checkbox for enabling/disabling
            var = tk.BooleanVar(value=True)
            self.policy_vars[f"{title.lower()}_{policy_key}"] = var
            
            checkbox = tk.Checkbutton(
                policy_frame,
                text=policy_info.get('description', policy_key.replace('_', ' ').title()),
                variable=var,
                bg="#ffffff",
                font=("Arial", 10),
                anchor="w"
            )
            checkbox.pack(side="left", fill="x", expand=True)
            
            # Risk level indicator
            risk_level = policy_info.get('risk_level', 'medium')
            risk_level_str = risk_level.value if hasattr(risk_level, 'value') else str(risk_level)
            risk_colors = {
                'low': '#34a853',
                'medium': '#fbbc04',
                'high': '#ea4335',
                'critical': '#d93025'
            }
            
            tk.Label(
                policy_frame,
                text=risk_level_str.upper(),
                font=("Arial", 8, "bold"),
                bg=risk_colors.get(risk_level_str, '#666'),
                fg="white",
                padx=6,
                pady=2
            ).pack(side="right")
    
    def _create_pii_policy_section(self, parent):
        """Create PII detection policy section."""
        if hasattr(self.security_scanner, 'pii_patterns'):
            self._create_policy_section(parent, "PII Detection", self.security_scanner.pii_patterns)
    
    def _create_secret_policy_section(self, parent):
        """Create secret detection policy section."""
        if hasattr(self.security_scanner, 'secret_patterns'):
            self._create_policy_section(parent, "Secret Detection", self.security_scanner.secret_patterns)
    
    def _create_code_policy_section(self, parent):
        """Create code analysis policy section."""
        if hasattr(self.security_scanner, 'unsafe_code_patterns'):
            self._create_policy_section(parent, "Code Analysis", self.security_scanner.unsafe_code_patterns)
    
    def _create_injection_policy_section(self, parent):
        """Create injection detection policy section."""
        if hasattr(self.security_scanner, 'injection_patterns'):
            self._create_policy_section(parent, "Injection Detection", self.security_scanner.injection_patterns)
    
    def _create_malicious_policy_section(self, parent):
        """Create malicious content policy section."""
        if hasattr(self.security_scanner, 'malicious_patterns'):
            self._create_policy_section(parent, "Malicious Content", self.security_scanner.malicious_patterns)
    
    def _load_current_policy(self):
        """Load current security policy settings."""
        try:
            policy = self.security_scanner.get_security_policy()
            # Update checkboxes based on current policy
            # This is a simplified implementation
            for key, var in self.policy_vars.items():
                var.set(True)  # Default to enabled
        except Exception as e:
            logging.getLogger(__name__).error(f"Failed to load security policy: {e}")
    
    def _save_policy(self):
        """Save security policy changes."""
        try:
            # Collect policy updates
            policy_updates = {}
            for key, var in self.policy_vars.items():
                policy_updates[key] = var.get()
            
            # Update security scanner policy
            success = self.security_scanner.update_security_policy(policy_updates)
            
            if success:
                messagebox.showinfo("Policy Saved", "Security policy has been updated successfully.")
            else:
                messagebox.showerror("Save Failed", "Failed to save security policy changes.")
                
        except Exception as e:
            logging.getLogger(__name__).error(f"Failed to save security policy: {e}")
            messagebox.showerror("Save Error", f"Error saving policy: {str(e)}")


class SecurityDashboardPage(tk.Frame):
    """Main security dashboard page with status overview and configuration."""
    
    def __init__(self, parent, services: Dict[str, Any], **kwargs):
        super().__init__(parent, bg="#ffffff", **kwargs)
        self.services = services
        self.logger = logging.getLogger(__name__)
        
        # Initialize security services
        self.security_scanner = services.get('security_scanner') or SecurityScanner()
        self.compliance_framework = services.get('compliance_framework') or ComplianceGovernanceFramework()
        
        # Current data
        self.current_violations: List[Dict[str, Any]] = []
        self.current_assessments: List[ComplianceAssessment] = []
        
        self._create_widgets()
        self.refresh()
    
    def _create_widgets(self):
        """Create the security dashboard widgets."""
        # Header with status indicator
        self._create_header()
        
        # Main content area with paned window
        self._create_main_content()
        
        # Action buttons
        self._create_action_buttons()
    
    def _create_header(self):
        """Create the dashboard header with status indicator."""
        header_frame = tk.Frame(self, bg="#ffffff")
        header_frame.pack(fill="x", padx=20, pady=(20, 15))
        
        # Title section
        title_frame = tk.Frame(header_frame, bg="#ffffff")
        title_frame.pack(side="left", fill="x", expand=True)
        
        tk.Label(
            title_frame,
            text="Security Dashboard",
            font=("Arial", 18, "bold"),
            bg="#ffffff",
            fg="#1a73e8"
        ).pack(anchor="w")
        
        tk.Label(
            title_frame,
            text="Real-time security monitoring and policy management",
            font=("Arial", 11),
            bg="#ffffff",
            fg="#666"
        ).pack(anchor="w", pady=(2, 0))
        
        # Status indicator
        status_frame = tk.Frame(header_frame, bg="#ffffff")
        status_frame.pack(side="right")
        
        self.status_indicator = SecurityStatusIndicator(status_frame)
        self.status_indicator.pack()
    
    def _create_main_content(self):
        """Create the main content area with paned layout."""
        # Create paned window for layout
        paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned_window.pack(fill="both", expand=True, padx=20, pady=(0, 15))
        
        # Left panel - Violations and scan results
        left_panel = tk.Frame(paned_window, bg="#ffffff")
        paned_window.add(left_panel, weight=2)
        
        self._create_violations_panel(left_panel)
        
        # Right panel - Policy configuration
        right_panel = tk.Frame(paned_window, bg="#ffffff")
        paned_window.add(right_panel, weight=1)
        
        self._create_policy_panel(right_panel)
    
    def _create_violations_panel(self, parent):
        """Create the violations display panel."""
        # Panel header
        header_frame = tk.Frame(parent, bg="#ffffff")
        header_frame.pack(fill="x", pady=(0, 10))
        
        tk.Label(
            header_frame,
            text="Security Scan Results",
            font=("Arial", 14, "bold"),
            bg="#ffffff",
            fg="#333"
        ).pack(side="left")
        
        tk.Button(
            header_frame,
            text="🔄 Refresh",
            bg="#f8f9fa",
            fg="#333",
            font=("Arial", 9),
            padx=10,
            pady=5,
            relief="flat",
            cursor="hand2",
            command=self.refresh
        ).pack(side="right")
        
        # Violations list
        self.violations_list = SecurityViolationsList(
            parent,
            on_violation_select=self._on_violation_selected
        )
        self.violations_list.pack(fill="both", expand=True)
    
    def _create_policy_panel(self, parent):
        """Create the policy configuration panel."""
        self.policy_panel = SecurityPolicyPanel(parent, self.security_scanner)
        self.policy_panel.pack(fill="both", expand=True)
    
    def _create_action_buttons(self):
        """Create action buttons at the bottom."""
        actions_frame = tk.Frame(self, bg="#ffffff")
        actions_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        # Scan actions
        tk.Button(
            actions_frame,
            text="🔍 Scan All Templates",
            bg="#1a73e8",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=15,
            pady=8,
            relief="flat",
            cursor="hand2",
            command=self._scan_all_templates
        ).pack(side="left", padx=(0, 10))
        
        tk.Button(
            actions_frame,
            text="📊 Generate Report",
            bg="#34a853",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=15,
            pady=8,
            relief="flat",
            cursor="hand2",
            command=self._generate_security_report
        ).pack(side="left", padx=(0, 10))
        
        tk.Button(
            actions_frame,
            text="📤 Export Violations",
            bg="#fbbc04",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=15,
            pady=8,
            relief="flat",
            cursor="hand2",
            command=self._export_violations
        ).pack(side="left")
        
        # Status info
        self.last_scan_label = tk.Label(
            actions_frame,
            text="Last scan: Never",
            font=("Arial", 9),
            bg="#ffffff",
            fg="#666"
        )
        self.last_scan_label.pack(side="right")
    
    def _on_violation_selected(self, violation: Dict[str, Any]):
        """Handle violation selection for detailed view."""
        try:
            # Open detailed violation reporting interface
            self._open_violation_reporting(violation)
        except Exception as e:
            self.logger.error(f"Failed to show violation details: {e}")
            messagebox.showerror("Error", f"Failed to display violation details: {str(e)}")
    
    def _open_violation_reporting(self, violation: Dict[str, Any]):
        """Open the detailed violation reporting interface."""
        from ui.security_violation_reporting import SecurityViolationReportingPage
        
        # Create violation reporting window
        reporting_window = tk.Toplevel(self)
        reporting_window.title("Security Violation Analysis")
        reporting_window.geometry("1000x700")
        reporting_window.configure(bg="#ffffff")
        
        # Make window modal
        reporting_window.transient(self)
        reporting_window.grab_set()
        
        # Center the window
        reporting_window.update_idletasks()
        x = (reporting_window.winfo_screenwidth() // 2) - (1000 // 2)
        y = (reporting_window.winfo_screenheight() // 2) - (700 // 2)
        reporting_window.geometry(f"1000x700+{x}+{y}")
        
        # Create reporting interface
        reporting_page = SecurityViolationReportingPage(reporting_window, self.services)
        reporting_page.pack(fill="both", expand=True)
        
        # Display the selected violation
        reporting_page.display_violation(violation)
    
    def _scan_all_templates(self):
        """Scan all templates for security issues."""
        try:
            # Get template service
            template_service = self.services.get('template_service')
            if not template_service:
                messagebox.showwarning("Service Unavailable", "Template service is not available.")
                return
            
            # Show progress dialog
            progress_dialog = self._create_progress_dialog("Scanning Templates", "Scanning templates for security issues...")
            
            # Simulate scanning (in real implementation, this would scan actual templates)
            violations = []
            
            # Sample violations for demonstration
            sample_violations = [
                {
                    'id': generate_id(),
                    'issue_type': 'pii_detected',
                    'risk_level': 'high',
                    'title': 'Email Address Detected',
                    'description': 'Potential email address found in prompt content',
                    'prompt_id': 'template_001',
                    'evidence': 'user@example.com',
                    'recommendation': 'Remove or replace the email address with a placeholder',
                    'detected_at': datetime.now().isoformat(),
                    'confidence': 0.95,
                    'location': {'line': 5, 'start': 45, 'end': 62}
                },
                {
                    'id': generate_id(),
                    'issue_type': 'secret_detected',
                    'risk_level': 'critical',
                    'title': 'API Key Detected',
                    'description': 'Potential API key found in prompt content',
                    'prompt_id': 'template_002',
                    'evidence': '[REDACTED SECRET]',
                    'recommendation': 'Remove the API key and use environment variables',
                    'detected_at': datetime.now().isoformat(),
                    'confidence': 0.98,
                    'location': {'line': 12, 'start': 120, 'end': 155}
                }
            ]
            
            violations.extend(sample_violations)
            
            # Close progress dialog
            progress_dialog.destroy()
            
            # Update violations list
            self.current_violations = violations
            self.violations_list.update_violations(violations)
            
            # Update status
            if violations:
                critical_count = len([v for v in violations if v.get('risk_level') == 'critical'])
                high_count = len([v for v in violations if v.get('risk_level') == 'high'])
                
                if critical_count > 0:
                    self.status_indicator.update_status(SecurityRiskLevel.CRITICAL, f"{critical_count} Critical Issues")
                elif high_count > 0:
                    self.status_indicator.update_status(SecurityRiskLevel.HIGH, f"{high_count} High Risk Issues")
                else:
                    self.status_indicator.update_status(SecurityRiskLevel.MEDIUM, f"{len(violations)} Issues Found")
            else:
                self.status_indicator.update_status(SecurityRiskLevel.LOW, "All Clear")
            
            # Update last scan time
            self.last_scan_label.configure(text=f"Last scan: {datetime.now().strftime('%H:%M:%S')}")
            
            messagebox.showinfo("Scan Complete", f"Security scan completed. Found {len(violations)} issues.")
            
        except Exception as e:
            self.logger.error(f"Failed to scan templates: {e}")
            messagebox.showerror("Scan Failed", f"Failed to scan templates: {str(e)}")
    
    def _create_progress_dialog(self, title: str, message: str) -> tk.Toplevel:
        """Create a progress dialog."""
        dialog = tk.Toplevel(self)
        dialog.title(title)
        dialog.geometry("300x100")
        dialog.configure(bg="#ffffff")
        dialog.transient(self)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (300 // 2)
        y = (dialog.winfo_screenheight() // 2) - (100 // 2)
        dialog.geometry(f"300x100+{x}+{y}")
        
        tk.Label(
            dialog,
            text=message,
            font=("Arial", 11),
            bg="#ffffff",
            fg="#333"
        ).pack(expand=True)
        
        # Progress bar
        progress = ttk.Progressbar(dialog, mode='indeterminate')
        progress.pack(pady=10, padx=20, fill="x")
        progress.start()
        
        dialog.update()
        return dialog
    
    def _generate_security_report(self):
        """Generate comprehensive security report."""
        try:
            if not self.current_violations:
                messagebox.showinfo("No Data", "No security violations found. Run a scan first.")
                return
            
            # Generate report using compliance framework
            if self.current_assessments:
                report = self.compliance_framework.generate_compliance_report(
                    self.current_assessments, 
                    "json"
                )
            else:
                # Create a basic report from current violations
                import json
                report_data = {
                    "report_metadata": {
                        "generated_at": datetime.now().isoformat(),
                        "report_type": "security_violations"
                    },
                    "summary": {
                        "total_violations": len(self.current_violations),
                        "critical_violations": len([v for v in self.current_violations if v.get('risk_level') == 'critical']),
                        "high_violations": len([v for v in self.current_violations if v.get('risk_level') == 'high'])
                    },
                    "violations": self.current_violations
                }
                report = json.dumps(report_data, indent=2, default=str)
            
            # Save report to file
            filename = filedialog.asksaveasfilename(
                title="Save Security Report",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filename:
                with open(filename, 'w') as f:
                    f.write(report)
                
                messagebox.showinfo("Report Saved", f"Security report saved to {filename}")
            
        except Exception as e:
            self.logger.error(f"Failed to generate security report: {e}")
            messagebox.showerror("Report Failed", f"Failed to generate report: {str(e)}")
    
    def _export_violations(self):
        """Export violations to CSV format."""
        try:
            if not self.current_violations:
                messagebox.showinfo("No Data", "No security violations found. Run a scan first.")
                return
            
            # Convert violations to CSV format
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                "ID", "Type", "Severity", "Title", "Description", 
                "Prompt ID", "Evidence", "Recommendation", "Detected At", "Confidence"
            ])
            
            # Write violations
            for violation in self.current_violations:
                writer.writerow([
                    violation.get('id', ''),
                    violation.get('issue_type', ''),
                    violation.get('risk_level', ''),
                    violation.get('title', ''),
                    violation.get('description', ''),
                    violation.get('prompt_id', ''),
                    violation.get('evidence', ''),
                    violation.get('recommendation', ''),
                    violation.get('detected_at', ''),
                    violation.get('confidence', '')
                ])
            
            # Save to file
            filename = filedialog.asksaveasfilename(
                title="Export Violations",
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )
            
            if filename:
                with open(filename, 'w', newline='') as f:
                    f.write(output.getvalue())
                
                messagebox.showinfo("Export Complete", f"Violations exported to {filename}")
            
        except Exception as e:
            self.logger.error(f"Failed to export violations: {e}")
            messagebox.showerror("Export Failed", f"Failed to export violations: {str(e)}")
    
    def refresh(self):
        """Refresh the security dashboard data."""
        try:
            # Refresh violations list (in real implementation, this would fetch from database)
            self.violations_list.update_violations(self.current_violations)
            
            # Update status based on current violations
            if self.current_violations:
                critical_count = len([v for v in self.current_violations if v.get('risk_level') == 'critical'])
                high_count = len([v for v in self.current_violations if v.get('risk_level') == 'high'])
                
                if critical_count > 0:
                    self.status_indicator.update_status(SecurityRiskLevel.CRITICAL, f"{critical_count} Critical Issues")
                elif high_count > 0:
                    self.status_indicator.update_status(SecurityRiskLevel.HIGH, f"{high_count} High Risk Issues")
                else:
                    self.status_indicator.update_status(SecurityRiskLevel.MEDIUM, f"{len(self.current_violations)} Issues Found")
            else:
                self.status_indicator.update_status(SecurityRiskLevel.LOW, "All Clear")
            
            self.logger.debug("Security dashboard refreshed")
            
        except Exception as e:
            self.logger.error(f"Failed to refresh security dashboard: {e}")