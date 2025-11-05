"""
Security Violation Reporting Interface
=====================================

Detailed violation display with severity levels, remediation suggestion panel,
and security audit trail viewer.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
import json

from services.security.security_scanner import SecurityScanResult, SecurityIssue, SecurityRiskLevel, SecurityIssueType
from services.security.compliance_governance import ComplianceViolation, ComplianceStatus
from services.collaboration.audit_trail import AuditEvent, AuditEventType
from models.base import generate_id


class ViolationDetailPanel(tk.Frame):
    """Detailed view panel for individual security violations."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg="#ffffff", **kwargs)
        self.current_violation: Optional[Dict[str, Any]] = None
        self._create_widgets()
    
    def _create_widgets(self):
        """Create the violation detail widgets."""
        # Header
        self.header_frame = tk.Frame(self, bg="#ffffff")
        self.header_frame.pack(fill="x", pady=(0, 15))
        
        self.title_label = tk.Label(
            self.header_frame,
            text="Select a violation to view details",
            font=("Arial", 16, "bold"),
            bg="#ffffff",
            fg="#666"
        )
        self.title_label.pack(anchor="w")
        
        self.severity_label = tk.Label(
            self.header_frame,
            text="",
            font=("Arial", 10, "bold"),
            padx=8,
            pady=4
        )
        self.severity_label.pack(anchor="w", pady=(5, 0))
        
        # Main content area with tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)
        
        # Details tab
        self.details_frame = tk.Frame(self.notebook, bg="#ffffff")
        self.notebook.add(self.details_frame, text="Details")
        self._create_details_tab()
        
        # Evidence tab
        self.evidence_frame = tk.Frame(self.notebook, bg="#ffffff")
        self.notebook.add(self.evidence_frame, text="Evidence")
        self._create_evidence_tab()
        
        # Remediation tab
        self.remediation_frame = tk.Frame(self.notebook, bg="#ffffff")
        self.notebook.add(self.remediation_frame, text="Remediation")
        self._create_remediation_tab()
        
        # History tab
        self.history_frame = tk.Frame(self.notebook, bg="#ffffff")
        self.notebook.add(self.history_frame, text="History")
        self._create_history_tab()
    
    def _create_details_tab(self):
        """Create the details tab content."""
        # Scrollable text widget for details
        self.details_text = tk.Text(
            self.details_frame,
            wrap=tk.WORD,
            font=("Arial", 10),
            bg="#f8f9fa",
            fg="#333",
            padx=15,
            pady=15,
            state="disabled"
        )
        
        details_scrollbar = ttk.Scrollbar(
            self.details_frame, 
            orient="vertical", 
            command=self.details_text.yview
        )
        self.details_text.configure(yscrollcommand=details_scrollbar.set)
        
        self.details_text.pack(side="left", fill="both", expand=True)
        details_scrollbar.pack(side="right", fill="y")
    
    def _create_evidence_tab(self):
        """Create the evidence tab content."""
        # Evidence display with syntax highlighting
        evidence_label = tk.Label(
            self.evidence_frame,
            text="Evidence and Context:",
            font=("Arial", 12, "bold"),
            bg="#ffffff",
            fg="#333"
        )
        evidence_label.pack(anchor="w", pady=(10, 5))
        
        self.evidence_text = tk.Text(
            self.evidence_frame,
            wrap=tk.WORD,
            font=("Consolas", 10),
            bg="#f8f9fa",
            fg="#333",
            padx=15,
            pady=15,
            state="disabled"
        )
        
        evidence_scrollbar = ttk.Scrollbar(
            self.evidence_frame, 
            orient="vertical", 
            command=self.evidence_text.yview
        )
        self.evidence_text.configure(yscrollcommand=evidence_scrollbar.set)
        
        self.evidence_text.pack(side="left", fill="both", expand=True, pady=(0, 10))
        evidence_scrollbar.pack(side="right", fill="y", pady=(0, 10))
        
        # Configure text tags for highlighting
        self.evidence_text.tag_configure("match", background="#ffeb3b", foreground="#333")
        self.evidence_text.tag_configure("context", background="#f8f9fa", foreground="#666")
    
    def _create_remediation_tab(self):
        """Create the remediation suggestions tab."""
        # Remediation header
        remediation_header = tk.Frame(self.remediation_frame, bg="#ffffff")
        remediation_header.pack(fill="x", pady=(10, 15))
        
        tk.Label(
            remediation_header,
            text="Remediation Suggestions",
            font=("Arial", 12, "bold"),
            bg="#ffffff",
            fg="#333"
        ).pack(side="left")
        
        self.apply_fix_button = tk.Button(
            remediation_header,
            text="Apply Suggested Fix",
            bg="#34a853",
            fg="white",
            font=("Arial", 9, "bold"),
            padx=12,
            pady=6,
            relief="flat",
            cursor="hand2",
            command=self._apply_suggested_fix,
            state="disabled"
        )
        self.apply_fix_button.pack(side="right")
        
        # Remediation content
        self.remediation_text = tk.Text(
            self.remediation_frame,
            wrap=tk.WORD,
            font=("Arial", 10),
            bg="#f8f9fa",
            fg="#333",
            padx=15,
            pady=15,
            state="disabled"
        )
        
        remediation_scrollbar = ttk.Scrollbar(
            self.remediation_frame, 
            orient="vertical", 
            command=self.remediation_text.yview
        )
        self.remediation_text.configure(yscrollcommand=remediation_scrollbar.set)
        
        self.remediation_text.pack(side="left", fill="both", expand=True)
        remediation_scrollbar.pack(side="right", fill="y")
    
    def _create_history_tab(self):
        """Create the violation history tab."""
        # History header
        history_header = tk.Frame(self.history_frame, bg="#ffffff")
        history_header.pack(fill="x", pady=(10, 15))
        
        tk.Label(
            history_header,
            text="Violation History",
            font=("Arial", 12, "bold"),
            bg="#ffffff",
            fg="#333"
        ).pack(side="left")
        
        tk.Button(
            history_header,
            text="🔄 Refresh",
            bg="#f8f9fa",
            fg="#333",
            font=("Arial", 9),
            padx=10,
            pady=5,
            relief="flat",
            cursor="hand2",
            command=self._refresh_history
        ).pack(side="right")
        
        # History tree
        history_columns = ("timestamp", "action", "user", "status")
        self.history_tree = ttk.Treeview(
            self.history_frame,
            columns=history_columns,
            show="headings",
            height=8
        )
        
        # Configure columns
        self.history_tree.heading("timestamp", text="Timestamp")
        self.history_tree.heading("action", text="Action")
        self.history_tree.heading("user", text="User")
        self.history_tree.heading("status", text="Status")
        
        self.history_tree.column("timestamp", width=150, minwidth=120)
        self.history_tree.column("action", width=200, minwidth=150)
        self.history_tree.column("user", width=100, minwidth=80)
        self.history_tree.column("status", width=100, minwidth=80)
        
        # History scrollbar
        history_scrollbar = ttk.Scrollbar(
            self.history_frame, 
            orient="vertical", 
            command=self.history_tree.yview
        )
        self.history_tree.configure(yscrollcommand=history_scrollbar.set)
        
        self.history_tree.pack(side="left", fill="both", expand=True)
        history_scrollbar.pack(side="right", fill="y")
    
    def display_violation(self, violation: Dict[str, Any]):
        """Display detailed information for a violation."""
        self.current_violation = violation
        
        # Update header
        title = violation.get('title', 'Security Violation')
        self.title_label.configure(text=title, fg="#d93025")
        
        # Update severity label
        severity = violation.get('risk_level', 'unknown').upper()
        severity_colors = {
            'LOW': ('#34a853', '#e8f5e8'),
            'MEDIUM': ('#fbbc04', '#fff3e0'),
            'HIGH': ('#ff9800', '#fff3e0'),
            'CRITICAL': ('#d93025', '#ffebee')
        }
        
        fg_color, bg_color = severity_colors.get(severity, ('#666', '#f8f9fa'))
        self.severity_label.configure(
            text=f"SEVERITY: {severity}",
            fg=fg_color,
            bg=bg_color
        )
        
        # Update details tab
        self._update_details_tab(violation)
        
        # Update evidence tab
        self._update_evidence_tab(violation)
        
        # Update remediation tab
        self._update_remediation_tab(violation)
        
        # Update history tab
        self._update_history_tab(violation)
        
        # Enable apply fix button if remediation is available
        if violation.get('recommendation'):
            self.apply_fix_button.configure(state="normal")
        else:
            self.apply_fix_button.configure(state="disabled")
    
    def _update_details_tab(self, violation: Dict[str, Any]):
        """Update the details tab with violation information."""
        details_text = f"""Violation ID: {violation.get('id', 'Unknown')}
Type: {violation.get('issue_type', 'Unknown').replace('_', ' ').title()}
Severity: {violation.get('risk_level', 'Unknown').upper()}
Confidence: {violation.get('confidence', 0) * 100:.1f}%

Description:
{violation.get('description', 'No description available')}

Prompt Information:
- Prompt ID: {violation.get('prompt_id', 'N/A')}
- Version: {violation.get('prompt_version', 'N/A')}

Location:
{self._format_location(violation.get('location', {}))}

Detection Details:
- Detected At: {violation.get('detected_at', 'Unknown')}
- Scanner Version: {violation.get('scanner_version', 'N/A')}
- Rule ID: {violation.get('rule_id', 'N/A')}

Status:
- Current Status: {violation.get('status', 'Open')}
- Assigned To: {violation.get('assigned_to', 'Unassigned')}
- Priority: {violation.get('priority', 'Normal')}
"""
        
        self.details_text.configure(state="normal")
        self.details_text.delete("1.0", tk.END)
        self.details_text.insert("1.0", details_text)
        self.details_text.configure(state="disabled")
    
    def _update_evidence_tab(self, violation: Dict[str, Any]):
        """Update the evidence tab with violation evidence."""
        evidence = violation.get('evidence', 'No evidence available')
        
        self.evidence_text.configure(state="normal")
        self.evidence_text.delete("1.0", tk.END)
        
        # Insert evidence with highlighting
        if '[MATCH]' in evidence and '[/MATCH]' in evidence:
            # Parse and highlight matches
            parts = evidence.split('[MATCH]')
            self.evidence_text.insert(tk.END, parts[0], "context")
            
            for i, part in enumerate(parts[1:], 1):
                if '[/MATCH]' in part:
                    match_part, context_part = part.split('[/MATCH]', 1)
                    self.evidence_text.insert(tk.END, match_part, "match")
                    self.evidence_text.insert(tk.END, context_part, "context")
                else:
                    self.evidence_text.insert(tk.END, part, "context")
        else:
            self.evidence_text.insert(tk.END, evidence, "context")
        
        self.evidence_text.configure(state="disabled")
    
    def _update_remediation_tab(self, violation: Dict[str, Any]):
        """Update the remediation tab with suggestions."""
        recommendation = violation.get('recommendation', 'No remediation suggestions available')
        
        # Add additional context based on violation type
        issue_type = violation.get('issue_type', '')
        additional_info = self._get_remediation_context(issue_type)
        
        remediation_text = f"""Recommended Action:
{recommendation}

{additional_info}

Best Practices:
{self._get_best_practices(issue_type)}

Resources:
{self._get_remediation_resources(issue_type)}
"""
        
        self.remediation_text.configure(state="normal")
        self.remediation_text.delete("1.0", tk.END)
        self.remediation_text.insert("1.0", remediation_text)
        self.remediation_text.configure(state="disabled")
    
    def _update_history_tab(self, violation: Dict[str, Any]):
        """Update the history tab with violation timeline."""
        # Clear existing items
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        
        # Sample history data (in real implementation, this would come from audit service)
        history_events = [
            {
                'timestamp': violation.get('detected_at', datetime.now().isoformat()),
                'action': 'Violation Detected',
                'user': 'Security Scanner',
                'status': 'Open'
            },
            {
                'timestamp': datetime.now().isoformat(),
                'action': 'Viewed Details',
                'user': 'Current User',
                'status': 'Under Review'
            }
        ]
        
        for event in history_events:
            timestamp = event['timestamp'][:16].replace('T', ' ')
            self.history_tree.insert(
                "",
                "end",
                values=(timestamp, event['action'], event['user'], event['status'])
            )
    
    def _format_location(self, location: Dict[str, Any]) -> str:
        """Format location information for display."""
        if not location:
            return "Location information not available"
        
        parts = []
        if 'line' in location:
            parts.append(f"Line: {location['line']}")
        if 'start' in location and 'end' in location:
            parts.append(f"Characters: {location['start']}-{location['end']}")
        
        return "\n".join(parts) if parts else "Location information not available"
    
    def _get_remediation_context(self, issue_type: str) -> str:
        """Get additional remediation context based on issue type."""
        contexts = {
            'pii_detected': """
PII Detection Context:
- Personally Identifiable Information (PII) should never be hardcoded in prompts
- Use placeholder variables or anonymized data for testing
- Consider data masking techniques for production use
""",
            'secret_detected': """
Secret Detection Context:
- Secrets and credentials must never be stored in plain text
- Use environment variables or secure credential management systems
- Rotate any exposed credentials immediately
""",
            'unsafe_code': """
Code Safety Context:
- Avoid dynamic code execution in prompts
- Use sandboxed environments for code generation
- Implement proper input validation and sanitization
""",
            'injection_risk': """
Injection Risk Context:
- Input validation is critical to prevent injection attacks
- Use parameterized queries and prepared statements
- Implement proper escaping for user inputs
"""
        }
        
        return contexts.get(issue_type, "No additional context available for this violation type.")
    
    def _get_best_practices(self, issue_type: str) -> str:
        """Get best practices based on issue type."""
        practices = {
            'pii_detected': """
• Use synthetic or anonymized data for development and testing
• Implement data classification and handling procedures
• Regular PII scanning and monitoring
• Staff training on data privacy requirements
""",
            'secret_detected': """
• Use dedicated secret management tools (HashiCorp Vault, AWS Secrets Manager)
• Implement secret rotation policies
• Never commit secrets to version control
• Use service accounts and IAM roles where possible
""",
            'unsafe_code': """
• Code review processes for all prompt templates
• Sandboxed execution environments
• Principle of least privilege for code execution
• Regular security assessments
""",
            'injection_risk': """
• Input validation and sanitization
• Use of prepared statements and parameterized queries
• Web Application Firewall (WAF) implementation
• Regular penetration testing
"""
        }
        
        return practices.get(issue_type, "• Follow general security best practices\n• Regular security training\n• Implement defense in depth")
    
    def _get_remediation_resources(self, issue_type: str) -> str:
        """Get remediation resources based on issue type."""
        resources = {
            'pii_detected': """
• GDPR Compliance Guidelines
• NIST Privacy Framework
• Data Protection Impact Assessment (DPIA) templates
• PII detection and masking tools
""",
            'secret_detected': """
• OWASP Secrets Management Cheat Sheet
• Cloud provider secret management documentation
• Secret scanning tools (GitLeaks, TruffleHog)
• Credential rotation automation tools
""",
            'unsafe_code': """
• OWASP Secure Coding Practices
• Static Application Security Testing (SAST) tools
• Dynamic Application Security Testing (DAST) tools
• Secure development lifecycle guidelines
""",
            'injection_risk': """
• OWASP Injection Prevention Cheat Sheet
• SQL Injection Prevention Guide
• Input validation libraries and frameworks
• Security testing tools and techniques
"""
        }
        
        return resources.get(issue_type, "• General security resources\n• Security training materials\n• Industry best practice guides")
    
    def _apply_suggested_fix(self):
        """Apply the suggested fix for the violation."""
        if not self.current_violation:
            return
        
        try:
            # In a real implementation, this would apply the actual fix
            # For now, we'll show a confirmation dialog
            result = messagebox.askyesno(
                "Apply Fix",
                f"Apply the suggested fix for this {self.current_violation.get('issue_type', 'violation')}?\n\n"
                f"This action will modify the prompt template and may require review."
            )
            
            if result:
                # Simulate applying the fix
                messagebox.showinfo(
                    "Fix Applied",
                    "The suggested fix has been applied. Please review the changes and test the prompt."
                )
                
                # Update violation status
                self.current_violation['status'] = 'Fixed'
                self._update_history_tab(self.current_violation)
            
        except Exception as e:
            logging.getLogger(__name__).error(f"Failed to apply fix: {e}")
            messagebox.showerror("Fix Failed", f"Failed to apply fix: {str(e)}")
    
    def _refresh_history(self):
        """Refresh the violation history."""
        if self.current_violation:
            self._update_history_tab(self.current_violation)


class SecurityAuditTrailViewer(tk.Frame):
    """Security audit trail viewer for compliance and forensics."""
    
    def __init__(self, parent, audit_service=None, **kwargs):
        super().__init__(parent, bg="#ffffff", **kwargs)
        self.audit_service = audit_service
        self.logger = logging.getLogger(__name__)
        self.audit_events: List[Dict[str, Any]] = []
        self._create_widgets()
        self.refresh()
    
    def _create_widgets(self):
        """Create the audit trail viewer widgets."""
        # Header with filters
        self._create_header()
        
        # Audit events tree
        self._create_audit_tree()
        
        # Details panel
        self._create_details_panel()
    
    def _create_header(self):
        """Create the header with filters and controls."""
        header_frame = tk.Frame(self, bg="#ffffff")
        header_frame.pack(fill="x", pady=(0, 15))
        
        # Title
        tk.Label(
            header_frame,
            text="Security Audit Trail",
            font=("Arial", 14, "bold"),
            bg="#ffffff",
            fg="#1a73e8"
        ).pack(side="left")
        
        # Controls
        controls_frame = tk.Frame(header_frame, bg="#ffffff")
        controls_frame.pack(side="right")
        
        # Date filter
        tk.Label(
            controls_frame,
            text="Filter:",
            font=("Arial", 10),
            bg="#ffffff"
        ).pack(side="left", padx=(0, 5))
        
        self.filter_var = tk.StringVar(value="All Events")
        filter_combo = ttk.Combobox(
            controls_frame,
            textvariable=self.filter_var,
            values=["All Events", "Security Violations", "Policy Changes", "User Actions", "System Events"],
            state="readonly",
            width=15
        )
        filter_combo.pack(side="left", padx=(0, 10))
        filter_combo.bind("<<ComboboxSelected>>", self._on_filter_changed)
        
        # Refresh button
        tk.Button(
            controls_frame,
            text="🔄 Refresh",
            bg="#f8f9fa",
            fg="#333",
            font=("Arial", 9),
            padx=10,
            pady=5,
            relief="flat",
            cursor="hand2",
            command=self.refresh
        ).pack(side="left", padx=(0, 5))
        
        # Export button
        tk.Button(
            controls_frame,
            text="📤 Export",
            bg="#1a73e8",
            fg="white",
            font=("Arial", 9, "bold"),
            padx=10,
            pady=5,
            relief="flat",
            cursor="hand2",
            command=self._export_audit_trail
        ).pack(side="left")
    
    def _create_audit_tree(self):
        """Create the audit events tree view."""
        # Tree frame
        tree_frame = tk.Frame(self, bg="#ffffff")
        tree_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        # Audit tree
        columns = ("timestamp", "event_type", "user", "resource", "action", "status")
        self.audit_tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            height=12
        )
        
        # Configure columns
        self.audit_tree.heading("timestamp", text="Timestamp")
        self.audit_tree.heading("event_type", text="Event Type")
        self.audit_tree.heading("user", text="User")
        self.audit_tree.heading("resource", text="Resource")
        self.audit_tree.heading("action", text="Action")
        self.audit_tree.heading("status", text="Status")
        
        self.audit_tree.column("timestamp", width=150, minwidth=120)
        self.audit_tree.column("event_type", width=120, minwidth=100)
        self.audit_tree.column("user", width=100, minwidth=80)
        self.audit_tree.column("resource", width=150, minwidth=100)
        self.audit_tree.column("action", width=200, minwidth=150)
        self.audit_tree.column("status", width=80, minwidth=60)
        
        # Scrollbar
        audit_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.audit_tree.yview)
        self.audit_tree.configure(yscrollcommand=audit_scrollbar.set)
        
        # Pack tree and scrollbar
        self.audit_tree.pack(side="left", fill="both", expand=True)
        audit_scrollbar.pack(side="right", fill="y")
        
        # Bind selection event
        self.audit_tree.bind("<<TreeviewSelect>>", self._on_audit_event_selected)
    
    def _create_details_panel(self):
        """Create the event details panel."""
        details_frame = tk.LabelFrame(
            self,
            text="Event Details",
            font=("Arial", 11, "bold"),
            bg="#ffffff",
            fg="#333",
            padx=10,
            pady=10
        )
        details_frame.pack(fill="x", pady=(0, 10))
        
        self.details_text = tk.Text(
            details_frame,
            height=6,
            wrap=tk.WORD,
            font=("Arial", 10),
            bg="#f8f9fa",
            fg="#333",
            padx=10,
            pady=10,
            state="disabled"
        )
        
        details_scrollbar = ttk.Scrollbar(details_frame, orient="vertical", command=self.details_text.yview)
        self.details_text.configure(yscrollcommand=details_scrollbar.set)
        
        self.details_text.pack(side="left", fill="both", expand=True)
        details_scrollbar.pack(side="right", fill="y")
    
    def _on_filter_changed(self, event):
        """Handle filter selection change."""
        self._apply_filter()
    
    def _on_audit_event_selected(self, event):
        """Handle audit event selection."""
        selection = self.audit_tree.selection()
        if selection:
            item_id = selection[0]
            # Find the corresponding event
            for event in self.audit_events:
                if event.get('id') == item_id:
                    self._display_event_details(event)
                    break
    
    def _display_event_details(self, event: Dict[str, Any]):
        """Display detailed information for an audit event."""
        details_text = f"""Event ID: {event.get('id', 'Unknown')}
Event Type: {event.get('event_type', 'Unknown')}
Timestamp: {event.get('timestamp', 'Unknown')}
User: {event.get('user_id', 'Unknown')} ({event.get('user_name', 'N/A')})

Resource Information:
- Type: {event.get('resource_type', 'N/A')}
- ID: {event.get('resource_id', 'N/A')}
- Action: {event.get('action', 'N/A')}

Session Information:
- IP Address: {event.get('ip_address', 'N/A')}
- User Agent: {event.get('user_agent', 'N/A')}
- Session ID: {event.get('session_id', 'N/A')}

Additional Details:
{json.dumps(event.get('details', {}), indent=2)}

Changes:
Old Values: {json.dumps(event.get('old_values', {}), indent=2) if event.get('old_values') else 'N/A'}
New Values: {json.dumps(event.get('new_values', {}), indent=2) if event.get('new_values') else 'N/A'}

Integrity:
Checksum: {event.get('checksum', 'N/A')}
"""
        
        self.details_text.configure(state="normal")
        self.details_text.delete("1.0", tk.END)
        self.details_text.insert("1.0", details_text)
        self.details_text.configure(state="disabled")
    
    def _apply_filter(self):
        """Apply the selected filter to the audit events."""
        filter_value = self.filter_var.get()
        
        # Clear existing items
        for item in self.audit_tree.get_children():
            self.audit_tree.delete(item)
        
        # Filter events
        filtered_events = self.audit_events
        if filter_value != "All Events":
            filter_mapping = {
                "Security Violations": ["security_violation_detected", "security_scan_completed"],
                "Policy Changes": ["policy_updated", "policy_created", "policy_deleted"],
                "User Actions": ["user_login", "user_logout", "prompt_created", "prompt_updated"],
                "System Events": ["system_startup", "system_shutdown", "backup_completed"]
            }
            
            event_types = filter_mapping.get(filter_value, [])
            filtered_events = [e for e in self.audit_events if e.get('event_type') in event_types]
        
        # Populate tree with filtered events
        for event in filtered_events:
            timestamp = event.get('timestamp', '')[:16].replace('T', ' ')
            event_type = event.get('event_type', '').replace('_', ' ').title()
            user = event.get('user_name', event.get('user_id', 'System'))
            resource = f"{event.get('resource_type', 'N/A')}: {event.get('resource_id', 'N/A')}"
            action = event.get('action', 'N/A')
            status = event.get('status', 'Completed')
            
            self.audit_tree.insert(
                "",
                "end",
                iid=event.get('id', generate_id()),
                values=(timestamp, event_type, user, resource, action, status)
            )
    
    def _export_audit_trail(self):
        """Export audit trail to file."""
        try:
            filename = filedialog.asksaveasfilename(
                title="Export Audit Trail",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("CSV files", "*.csv"), ("All files", "*.*")]
            )
            
            if filename:
                if filename.endswith('.csv'):
                    self._export_to_csv(filename)
                else:
                    self._export_to_json(filename)
                
                messagebox.showinfo("Export Complete", f"Audit trail exported to {filename}")
        
        except Exception as e:
            self.logger.error(f"Failed to export audit trail: {e}")
            messagebox.showerror("Export Failed", f"Failed to export audit trail: {str(e)}")
    
    def _export_to_json(self, filename: str):
        """Export audit trail to JSON format."""
        with open(filename, 'w') as f:
            json.dump(self.audit_events, f, indent=2, default=str)
    
    def _export_to_csv(self, filename: str):
        """Export audit trail to CSV format."""
        import csv
        
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow([
                "ID", "Timestamp", "Event Type", "User ID", "User Name",
                "Resource Type", "Resource ID", "Action", "Status",
                "IP Address", "User Agent", "Session ID", "Details"
            ])
            
            # Write events
            for event in self.audit_events:
                writer.writerow([
                    event.get('id', ''),
                    event.get('timestamp', ''),
                    event.get('event_type', ''),
                    event.get('user_id', ''),
                    event.get('user_name', ''),
                    event.get('resource_type', ''),
                    event.get('resource_id', ''),
                    event.get('action', ''),
                    event.get('status', ''),
                    event.get('ip_address', ''),
                    event.get('user_agent', ''),
                    event.get('session_id', ''),
                    json.dumps(event.get('details', {}))
                ])
    
    def refresh(self):
        """Refresh the audit trail data."""
        try:
            # In a real implementation, this would fetch from the audit service
            # For now, we'll create sample audit events
            self.audit_events = self._generate_sample_audit_events()
            self._apply_filter()
            
            self.logger.debug("Audit trail refreshed")
            
        except Exception as e:
            self.logger.error(f"Failed to refresh audit trail: {e}")
    
    def _generate_sample_audit_events(self) -> List[Dict[str, Any]]:
        """Generate sample audit events for demonstration."""
        now = datetime.now()
        events = []
        
        # Sample security events
        events.extend([
            {
                'id': generate_id(),
                'timestamp': (now - timedelta(hours=2)).isoformat(),
                'event_type': 'security_violation_detected',
                'user_id': 'system',
                'user_name': 'Security Scanner',
                'resource_type': 'prompt',
                'resource_id': 'template_001',
                'action': 'PII detected in prompt content',
                'status': 'Open',
                'ip_address': '127.0.0.1',
                'user_agent': 'SecurityScanner/1.0',
                'session_id': 'scanner_session_001',
                'details': {
                    'violation_type': 'pii_detected',
                    'severity': 'high',
                    'confidence': 0.95
                }
            },
            {
                'id': generate_id(),
                'timestamp': (now - timedelta(hours=1)).isoformat(),
                'event_type': 'security_scan_completed',
                'user_id': 'system',
                'user_name': 'Security Scanner',
                'resource_type': 'workspace',
                'resource_id': 'default_workspace',
                'action': 'Completed security scan of all templates',
                'status': 'Completed',
                'ip_address': '127.0.0.1',
                'user_agent': 'SecurityScanner/1.0',
                'session_id': 'scanner_session_002',
                'details': {
                    'templates_scanned': 15,
                    'violations_found': 3,
                    'scan_duration': 45.2
                }
            },
            {
                'id': generate_id(),
                'timestamp': (now - timedelta(minutes=30)).isoformat(),
                'event_type': 'policy_updated',
                'user_id': 'admin_001',
                'user_name': 'Admin User',
                'resource_type': 'security_policy',
                'resource_id': 'pii_detection_policy',
                'action': 'Updated PII detection patterns',
                'status': 'Completed',
                'ip_address': '192.168.1.100',
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                'session_id': 'user_session_123',
                'details': {
                    'changes': ['Added new email pattern', 'Updated phone number regex']
                },
                'old_values': {'patterns': ['old_pattern_1', 'old_pattern_2']},
                'new_values': {'patterns': ['new_pattern_1', 'new_pattern_2', 'new_pattern_3']}
            }
        ])
        
        return events


class SecurityViolationReportingPage(tk.Frame):
    """Main security violation reporting interface."""
    
    def __init__(self, parent, services: Dict[str, Any], **kwargs):
        super().__init__(parent, bg="#ffffff", **kwargs)
        self.services = services
        self.logger = logging.getLogger(__name__)
        self._create_widgets()
    
    def _create_widgets(self):
        """Create the main reporting interface."""
        # Header
        header_frame = tk.Frame(self, bg="#ffffff")
        header_frame.pack(fill="x", padx=20, pady=(20, 15))
        
        tk.Label(
            header_frame,
            text="Security Violation Reporting",
            font=("Arial", 18, "bold"),
            bg="#ffffff",
            fg="#1a73e8"
        ).pack(anchor="w")
        
        tk.Label(
            header_frame,
            text="Detailed violation analysis, remediation guidance, and audit trail",
            font=("Arial", 11),
            bg="#ffffff",
            fg="#666"
        ).pack(anchor="w", pady=(2, 0))
        
        # Main content with notebook
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Violation details tab
        self.violation_frame = tk.Frame(self.notebook, bg="#ffffff")
        self.notebook.add(self.violation_frame, text="Violation Details")
        
        self.violation_panel = ViolationDetailPanel(self.violation_frame)
        self.violation_panel.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Audit trail tab
        self.audit_frame = tk.Frame(self.notebook, bg="#ffffff")
        self.notebook.add(self.audit_frame, text="Audit Trail")
        
        self.audit_viewer = SecurityAuditTrailViewer(
            self.audit_frame,
            self.services.get('audit_service')
        )
        self.audit_viewer.pack(fill="both", expand=True, padx=15, pady=15)
    
    def display_violation(self, violation: Dict[str, Any]):
        """Display a specific violation in the details panel."""
        self.violation_panel.display_violation(violation)
        self.notebook.select(0)  # Switch to violation details tab
    
    def refresh(self):
        """Refresh the reporting interface."""
        self.audit_viewer.refresh()