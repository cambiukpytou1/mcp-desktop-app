"""
Simple Demo Runner for Prompt Management UI
===========================================

Runs a simplified version of the prompt management interface for demonstration.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class SimpleMockService:
    """Simple mock service for demo purposes."""
    
    def __init__(self, config_manager=None, db_manager=None):
        self.config_manager = config_manager
        self.db_manager = db_manager
    
    def get(self, key, default=None):
        return default or {}


class PromptManagementDemo:
    """Simple demo of the prompt management UI."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Prompt Management UI Demo")
        self.root.geometry("1200x800")
        
        # Mock services
        self.mock_config = SimpleMockService()
        self.mock_db = SimpleMockService()
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the demo UI."""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(
            main_frame, 
            text="Prompt Management UI - Demo", 
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Create notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create demo tabs
        self.create_template_editor_tab(notebook)
        self.create_security_dashboard_tab(notebook)
        self.create_collaboration_tab(notebook)
        self.create_analytics_tab(notebook)
        self.create_evaluation_tab(notebook)
    
    def create_template_editor_tab(self, notebook):
        """Create template editor demo tab."""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Template Editor")
        
        # Template editor demo
        editor_frame = ttk.LabelFrame(frame, text="Template Editor", padding=10)
        editor_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Template name
        name_frame = ttk.Frame(editor_frame)
        name_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(name_frame, text="Template Name:").pack(side=tk.LEFT)
        name_entry = ttk.Entry(name_frame, width=40)
        name_entry.pack(side=tk.LEFT, padx=(10, 0))
        name_entry.insert(0, "Customer Support Response Template")
        
        # Template content
        ttk.Label(editor_frame, text="Template Content:").pack(anchor=tk.W)
        
        content_text = tk.Text(editor_frame, height=15, wrap=tk.WORD)
        content_scrollbar = ttk.Scrollbar(editor_frame, orient=tk.VERTICAL, command=content_text.yview)
        content_text.configure(yscrollcommand=content_scrollbar.set)
        
        # Sample template content
        sample_content = """Dear {{customer_name}},

Thank you for contacting us regarding {{issue_type}}.

{{issue_description}}

To resolve this issue, please follow these steps:
{{resolution_steps}}

If you continue to experience problems, please don't hesitate to reach out.

Best regards,
{{agent_name}}
Customer Support Team"""
        
        content_text.insert(1.0, sample_content)
        content_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=(5, 0))
        content_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=(5, 0))
        
        # Buttons
        button_frame = ttk.Frame(editor_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="Save Template", command=self.save_template).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Validate", command=self.validate_template).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Preview", command=self.preview_template).pack(side=tk.LEFT)
    
    def create_security_dashboard_tab(self, notebook):
        """Create security dashboard demo tab."""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Security Dashboard")
        
        # Security status
        status_frame = ttk.LabelFrame(frame, text="Security Status", padding=10)
        status_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Status indicators
        indicators = [
            ("Overall Security", "🟢 Good", "green"),
            ("Template Scanning", "🟡 In Progress", "orange"),
            ("Policy Compliance", "🟢 Compliant", "green"),
            ("Vulnerability Count", "2 Low Risk", "blue")
        ]
        
        for i, (label, status, color) in enumerate(indicators):
            row = i // 2
            col = (i % 2) * 2
            
            ttk.Label(status_frame, text=f"{label}:").grid(row=row, column=col, sticky=tk.W, padx=(0, 10), pady=5)
            status_label = ttk.Label(status_frame, text=status, foreground=color)
            status_label.grid(row=row, column=col+1, sticky=tk.W, padx=(0, 20), pady=5)
        
        # Recent scans
        scans_frame = ttk.LabelFrame(frame, text="Recent Security Scans", padding=10)
        scans_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Scans treeview
        columns = ("Template", "Status", "Issues", "Last Scan")
        scans_tree = ttk.Treeview(scans_frame, columns=columns, show="headings", height=8)
        
        for col in columns:
            scans_tree.heading(col, text=col)
            scans_tree.column(col, width=150)
        
        # Sample data
        sample_scans = [
            ("Customer Support Template", "✓ Clean", "0", "2024-01-15 10:30"),
            ("Code Review Template", "⚠ Warning", "1", "2024-01-15 09:45"),
            ("Meeting Summary Template", "✓ Clean", "0", "2024-01-15 08:20"),
        ]
        
        for scan in sample_scans:
            scans_tree.insert("", tk.END, values=scan)
        
        scans_tree.pack(fill=tk.BOTH, expand=True)
    
    def create_collaboration_tab(self, notebook):
        """Create collaboration demo tab."""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Collaboration")
        
        # Workspaces
        workspace_frame = ttk.LabelFrame(frame, text="Workspaces", padding=10)
        workspace_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Workspace list
        workspaces = ["Development Team", "Customer Success", "Marketing", "Sales"]
        
        ttk.Label(workspace_frame, text="Active Workspace:").pack(side=tk.LEFT)
        workspace_combo = ttk.Combobox(workspace_frame, values=workspaces, state="readonly", width=20)
        workspace_combo.pack(side=tk.LEFT, padx=(10, 0))
        workspace_combo.set("Development Team")
        
        # Approval queue
        approval_frame = ttk.LabelFrame(frame, text="Pending Approvals", padding=10)
        approval_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Approval treeview
        approval_columns = ("Template", "Author", "Status", "Submitted")
        approval_tree = ttk.Treeview(approval_frame, columns=approval_columns, show="headings", height=6)
        
        for col in approval_columns:
            approval_tree.heading(col, text=col)
            approval_tree.column(col, width=150)
        
        # Sample approval data
        sample_approvals = [
            ("API Documentation Template", "Alice Johnson", "Pending Review", "2024-01-15 14:30"),
            ("Bug Report Template", "Bob Smith", "Approved", "2024-01-15 13:15"),
            ("Feature Request Template", "Carol Davis", "Needs Changes", "2024-01-15 11:45"),
        ]
        
        for approval in sample_approvals:
            approval_tree.insert("", tk.END, values=approval)
        
        approval_tree.pack(fill=tk.BOTH, expand=True)
    
    def create_analytics_tab(self, notebook):
        """Create analytics demo tab."""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Analytics")
        
        # Performance metrics
        metrics_frame = ttk.LabelFrame(frame, text="Performance Metrics", padding=10)
        metrics_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Metrics display
        metrics = [
            ("Total Templates", "47"),
            ("Active Users", "23"),
            ("Avg Performance Score", "0.87"),
            ("Cost per Execution", "$0.0045"),
            ("Success Rate", "94.2%"),
            ("Response Time", "1.2s")
        ]
        
        for i, (metric, value) in enumerate(metrics):
            row = i // 3
            col = (i % 3) * 2
            
            ttk.Label(metrics_frame, text=f"{metric}:").grid(row=row, column=col, sticky=tk.W, padx=(0, 10), pady=5)
            value_label = ttk.Label(metrics_frame, text=value, font=("Arial", 10, "bold"))
            value_label.grid(row=row, column=col+1, sticky=tk.W, padx=(0, 20), pady=5)
        
        # Top performers
        performers_frame = ttk.LabelFrame(frame, text="Top Performing Templates", padding=10)
        performers_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Performers treeview
        perf_columns = ("Template", "Score", "Usage", "Cost")
        perf_tree = ttk.Treeview(performers_frame, columns=perf_columns, show="headings", height=6)
        
        for col in perf_columns:
            perf_tree.heading(col, text=col)
            perf_tree.column(col, width=150)
        
        # Sample performance data
        sample_performance = [
            ("Customer Support Template", "0.94", "156 uses", "$0.003"),
            ("Code Review Template", "0.91", "89 uses", "$0.005"),
            ("Meeting Summary Template", "0.88", "234 uses", "$0.004"),
            ("Bug Report Template", "0.85", "67 uses", "$0.006"),
        ]
        
        for perf in sample_performance:
            perf_tree.insert("", tk.END, values=perf)
        
        perf_tree.pack(fill=tk.BOTH, expand=True)
    
    def create_evaluation_tab(self, notebook):
        """Create evaluation demo tab."""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Evaluation & Testing")
        
        # Test configuration
        config_frame = ttk.LabelFrame(frame, text="Multi-Model Test Configuration", padding=10)
        config_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Test settings
        ttk.Label(config_frame, text="Template:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        template_combo = ttk.Combobox(config_frame, values=["Customer Support Template", "Code Review Template"], state="readonly", width=25)
        template_combo.grid(row=0, column=1, padx=(0, 20))
        template_combo.set("Customer Support Template")
        
        ttk.Label(config_frame, text="Providers:").grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        providers_frame = ttk.Frame(config_frame)
        providers_frame.grid(row=0, column=3)
        
        # Provider checkboxes
        providers = ["OpenAI GPT-4", "Anthropic Claude", "Google Gemini"]
        for i, provider in enumerate(providers):
            var = tk.BooleanVar(value=True)
            ttk.Checkbutton(providers_frame, text=provider, variable=var).pack(anchor=tk.W)
        
        # Test results
        results_frame = ttk.LabelFrame(frame, text="Test Results", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Results treeview
        result_columns = ("Provider", "Score", "Cost", "Response Time", "Status")
        result_tree = ttk.Treeview(results_frame, columns=result_columns, show="headings", height=6)
        
        for col in result_columns:
            result_tree.heading(col, text=col)
            result_tree.column(col, width=120)
        
        # Sample test results
        sample_results = [
            ("OpenAI GPT-4", "0.92", "$0.0045", "1250ms", "✓ Complete"),
            ("Anthropic Claude", "0.89", "$0.0032", "980ms", "✓ Complete"),
            ("Google Gemini", "0.87", "$0.0028", "1100ms", "✓ Complete"),
        ]
        
        for result in sample_results:
            result_tree.insert("", tk.END, values=result)
        
        result_tree.pack(fill=tk.BOTH, expand=True)
        
        # Test controls
        control_frame = ttk.Frame(results_frame)
        control_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(control_frame, text="Run Test", command=self.run_test).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(control_frame, text="Export Results", command=self.export_results).pack(side=tk.LEFT)
    
    def save_template(self):
        """Demo save template action."""
        messagebox.showinfo("Success", "Template saved successfully!")
    
    def validate_template(self):
        """Demo validate template action."""
        messagebox.showinfo("Validation", "✓ Template validation passed!\n\nFound variables: customer_name, issue_type, issue_description, resolution_steps, agent_name")
    
    def preview_template(self):
        """Demo preview template action."""
        messagebox.showinfo("Preview", "Template preview would open in a new window with sample data filled in.")
    
    def run_test(self):
        """Demo run test action."""
        messagebox.showinfo("Test Started", "Multi-model test started! Results will appear in the table when complete.")
    
    def export_results(self):
        """Demo export results action."""
        messagebox.showinfo("Export", "Test results exported to test_results_20240115.json")
    
    def run(self):
        """Run the demo."""
        # Show welcome message
        messagebox.showinfo(
            "Prompt Management UI Demo",
            "Welcome to the Prompt Management UI Demo!\n\n"
            "This demo showcases the key features:\n"
            "• Template Editor with syntax highlighting\n"
            "• Security Dashboard with scanning\n"
            "• Collaboration and approval workflows\n"
            "• Analytics and performance insights\n"
            "• Multi-model evaluation and testing\n\n"
            "Explore the tabs to see the different features!"
        )
        
        self.root.mainloop()


def main():
    """Run the demo."""
    print("Starting Prompt Management UI Demo...")
    
    try:
        demo = PromptManagementDemo()
        demo.run()
    except Exception as e:
        print(f"Demo failed: {e}")
        messagebox.showerror("Error", f"Demo failed to start: {e}")


if __name__ == "__main__":
    main()