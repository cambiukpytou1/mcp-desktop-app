"""
Cost Monitoring UI Page
======================

User interface for cost tracking, monitoring, and visualization.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from services.evaluation.cost_tracking import CostTracker, CostAlert
from services.evaluation.cost_visualization import CostVisualizationService


class CostMonitoringPage:
    """Cost monitoring and visualization page."""
    
    def __init__(self, parent, config_manager, db_manager):
        self.parent = parent
        self.config_manager = config_manager
        self.db_manager = db_manager
        
        # Initialize services
        self.cost_tracker = CostTracker(config_manager, db_manager)
        self.visualization_service = CostVisualizationService(self.cost_tracker)
        
        # UI state
        self.refresh_interval = 30  # seconds
        self.auto_refresh = True
        self.refresh_job = None
        
        self.setup_ui()
        self.setup_alert_callbacks()
        self.refresh_data()
    
    def setup_ui(self):
        """Set up the user interface."""
        # Main container
        self.main_frame = ttk.Frame(self.parent)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(
            self.main_frame, 
            text="Cost Monitoring & Analytics", 
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self.create_overview_tab()
        self.create_real_time_tab()
        self.create_alerts_tab()
        self.create_reports_tab()
    
    def create_overview_tab(self):
        """Create cost overview tab."""
        overview_frame = ttk.Frame(self.notebook)
        self.notebook.add(overview_frame, text="Overview")
        
        # Control panel
        control_frame = ttk.LabelFrame(overview_frame, text="Controls", padding=10)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Time period selection
        ttk.Label(control_frame, text="Time Period:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.time_period_var = tk.StringVar(value="24")
        time_period_combo = ttk.Combobox(
            control_frame, 
            textvariable=self.time_period_var,
            values=["1", "6", "24", "168", "720"],  # 1h, 6h, 24h, 1w, 1m
            width=10,
            state="readonly"
        )
        time_period_combo.grid(row=0, column=1, padx=(0, 10))
        time_period_combo.bind("<<ComboboxSelected>>", self.on_time_period_changed)
        
        # Refresh button
        refresh_btn = ttk.Button(
            control_frame, 
            text="Refresh", 
            command=self.refresh_data
        )
        refresh_btn.grid(row=0, column=2, padx=(0, 10))
        
        # Auto-refresh toggle
        self.auto_refresh_var = tk.BooleanVar(value=True)
        auto_refresh_check = ttk.Checkbutton(
            control_frame,
            text="Auto-refresh",
            variable=self.auto_refresh_var,
            command=self.toggle_auto_refresh
        )
        auto_refresh_check.grid(row=0, column=3)
        
        # Metrics display
        metrics_frame = ttk.LabelFrame(overview_frame, text="Key Metrics", padding=10)
        metrics_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Create metric labels
        self.metric_labels = {}
        metrics = [
            ("total_cost", "Total Cost"),
            ("total_requests", "Total Requests"),
            ("total_tokens", "Total Tokens"),
            ("active_sessions", "Active Sessions"),
            ("avg_cost_per_request", "Avg Cost/Request"),
            ("avg_cost_per_token", "Avg Cost/Token")
        ]
        
        for i, (key, label) in enumerate(metrics):
            row = i // 3
            col = (i % 3) * 2
            
            ttk.Label(metrics_frame, text=f"{label}:").grid(
                row=row, column=col, sticky=tk.W, padx=(0, 5), pady=2
            )
            
            value_label = ttk.Label(metrics_frame, text="$0.00", font=("Arial", 10, "bold"))
            value_label.grid(row=row, column=col+1, sticky=tk.W, padx=(0, 20), pady=2)
            self.metric_labels[key] = value_label  
      
        # Chart display area (placeholder for now)
        chart_frame = ttk.LabelFrame(overview_frame, text="Cost Visualization", padding=10)
        chart_frame.pack(fill=tk.BOTH, expand=True)
        
        self.chart_text = tk.Text(chart_frame, height=15, wrap=tk.WORD)
        chart_scrollbar = ttk.Scrollbar(chart_frame, orient=tk.VERTICAL, command=self.chart_text.yview)
        self.chart_text.configure(yscrollcommand=chart_scrollbar.set)
        
        self.chart_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        chart_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_real_time_tab(self):
        """Create real-time monitoring tab."""
        realtime_frame = ttk.Frame(self.notebook)
        self.notebook.add(realtime_frame, text="Real-time")
        
        # Active sessions
        sessions_frame = ttk.LabelFrame(realtime_frame, text="Active Sessions", padding=10)
        sessions_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Sessions treeview
        columns = ("Session ID", "Provider", "Model", "Tokens", "Cost", "Duration")
        self.sessions_tree = ttk.Treeview(sessions_frame, columns=columns, show="headings", height=8)
        
        for col in columns:
            self.sessions_tree.heading(col, text=col)
            self.sessions_tree.column(col, width=120)
        
        sessions_scrollbar = ttk.Scrollbar(sessions_frame, orient=tk.VERTICAL, command=self.sessions_tree.yview)
        self.sessions_tree.configure(yscrollcommand=sessions_scrollbar.set)
        
        self.sessions_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sessions_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Real-time metrics
        rt_metrics_frame = ttk.LabelFrame(realtime_frame, text="Real-time Metrics", padding=10)
        rt_metrics_frame.pack(fill=tk.X)
        
        self.rt_metric_labels = {}
        rt_metrics = [
            ("rt_total_cost", "Current Total Cost"),
            ("rt_active_sessions", "Active Sessions"),
            ("rt_total_tokens", "Current Total Tokens")
        ]
        
        for i, (key, label) in enumerate(rt_metrics):
            ttk.Label(rt_metrics_frame, text=f"{label}:").grid(
                row=0, column=i*2, sticky=tk.W, padx=(0, 5)
            )
            
            value_label = ttk.Label(rt_metrics_frame, text="$0.00", font=("Arial", 10, "bold"))
            value_label.grid(row=0, column=i*2+1, sticky=tk.W, padx=(0, 20))
            self.rt_metric_labels[key] = value_label
    
    def create_alerts_tab(self):
        """Create cost alerts management tab."""
        alerts_frame = ttk.Frame(self.notebook)
        self.notebook.add(alerts_frame, text="Alerts")
        
        # Alert controls
        alert_controls = ttk.Frame(alerts_frame)
        alert_controls.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(
            alert_controls, 
            text="Create Alert", 
            command=self.create_alert_dialog
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            alert_controls, 
            text="Edit Alert", 
            command=self.edit_alert_dialog
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            alert_controls, 
            text="Delete Alert", 
            command=self.delete_alert
        ).pack(side=tk.LEFT)
        
        # Alerts list
        alerts_list_frame = ttk.LabelFrame(alerts_frame, text="Cost Alerts", padding=10)
        alerts_list_frame.pack(fill=tk.BOTH, expand=True)
        
        alert_columns = ("Name", "Type", "Threshold", "Status", "Triggered", "Last Triggered")
        self.alerts_tree = ttk.Treeview(alerts_list_frame, columns=alert_columns, show="headings")
        
        for col in alert_columns:
            self.alerts_tree.heading(col, text=col)
            self.alerts_tree.column(col, width=120)
        
        alerts_scrollbar = ttk.Scrollbar(alerts_list_frame, orient=tk.VERTICAL, command=self.alerts_tree.yview)
        self.alerts_tree.configure(yscrollcommand=alerts_scrollbar.set)
        
        self.alerts_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        alerts_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_reports_tab(self):
        """Create cost reports tab."""
        reports_frame = ttk.Frame(self.notebook)
        self.notebook.add(reports_frame, text="Reports")
        
        # Report controls
        report_controls = ttk.Frame(reports_frame)
        report_controls.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(report_controls, text="Report Type:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.report_type_var = tk.StringVar(value="summary")
        report_type_combo = ttk.Combobox(
            report_controls,
            textvariable=self.report_type_var,
            values=["summary", "detailed", "comparison"],
            width=15,
            state="readonly"
        )
        report_type_combo.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            report_controls,
            text="Generate Report",
            command=self.generate_report
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            report_controls,
            text="Export CSV",
            command=self.export_report
        ).pack(side=tk.LEFT)
        
        # Report display
        report_display_frame = ttk.LabelFrame(reports_frame, text="Report Data", padding=10)
        report_display_frame.pack(fill=tk.BOTH, expand=True)
        
        self.report_text = tk.Text(report_display_frame, wrap=tk.WORD)
        report_scrollbar = ttk.Scrollbar(report_display_frame, orient=tk.VERTICAL, command=self.report_text.yview)
        self.report_text.configure(yscrollcommand=report_scrollbar.set)
        
        self.report_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        report_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def setup_alert_callbacks(self):
        """Set up alert notification callbacks."""
        def alert_callback(alert: CostAlert, context: Dict[str, Any]):
            # Show alert notification
            self.show_alert_notification(alert, context)
        
        self.cost_tracker.add_alert_callback(alert_callback)
    
    def show_alert_notification(self, alert: CostAlert, context: Dict[str, Any]):
        """Show alert notification to user."""
        message = f"Cost Alert: {alert.name}\n\n"
        
        if alert.alert_type == "threshold":
            message += f"Current cost: ${context.get('current_cost', 0):.4f}\n"
            message += f"Threshold: ${context.get('threshold', 0):.4f}\n"
        elif alert.alert_type == "rate":
            message += f"Current rate: ${context.get('current_rate', 0):.4f}/min\n"
            message += f"Threshold rate: ${context.get('threshold_rate', 0):.4f}/min\n"
        elif alert.alert_type == "budget":
            message += f"Current spending: ${context.get('current_spending', 0):.4f}\n"
            message += f"Budget: ${context.get('budget', 0):.4f}\n"
        
        messagebox.showwarning("Cost Alert", message)
        
        # Refresh alerts display
        self.refresh_alerts()
    
    def on_time_period_changed(self, event=None):
        """Handle time period selection change."""
        self.refresh_data()
    
    def toggle_auto_refresh(self):
        """Toggle auto-refresh functionality."""
        self.auto_refresh = self.auto_refresh_var.get()
        
        if self.auto_refresh:
            self.schedule_refresh()
        else:
            if self.refresh_job:
                self.parent.after_cancel(self.refresh_job)
                self.refresh_job = None
    
    def schedule_refresh(self):
        """Schedule next auto-refresh."""
        if self.auto_refresh:
            self.refresh_job = self.parent.after(
                self.refresh_interval * 1000, 
                self.auto_refresh_data
            )
    
    def auto_refresh_data(self):
        """Auto-refresh data and schedule next refresh."""
        self.refresh_data()
        self.schedule_refresh()
    
    def refresh_data(self):
        """Refresh all cost monitoring data."""
        try:
            # Get time period
            hours = int(self.time_period_var.get())
            
            # Get cost summary
            summary = self.visualization_service.get_cost_summary(hours)
            
            # Update metrics
            self.update_metrics(summary)
            
            # Update real-time data
            self.update_real_time_data()
            
            # Update alerts
            self.refresh_alerts()
            
            # Update chart display
            self.update_chart_display(hours)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh data: {e}")
    
    def update_metrics(self, summary: Dict[str, Any]):
        """Update metric labels with current data."""
        historical = summary.get("historical", {})
        efficiency = summary.get("efficiency", {})
        real_time = summary.get("real_time", {})
        
        self.metric_labels["total_cost"].config(text=f"${historical.get('total_cost', 0):.4f}")
        self.metric_labels["total_requests"].config(text=f"{historical.get('total_requests', 0):,}")
        self.metric_labels["total_tokens"].config(text=f"{historical.get('total_tokens', 0):,}")
        self.metric_labels["active_sessions"].config(text=f"{real_time.get('active_sessions', 0)}")
        self.metric_labels["avg_cost_per_request"].config(text=f"${efficiency.get('cost_per_request', 0):.6f}")
        self.metric_labels["avg_cost_per_token"].config(text=f"${efficiency.get('cost_per_token', 0):.8f}")
    
    def update_real_time_data(self):
        """Update real-time monitoring data."""
        try:
            # Get real-time costs
            rt_data = self.cost_tracker.get_real_time_costs()
            
            # Update real-time metrics
            self.rt_metric_labels["rt_total_cost"].config(text=f"${rt_data.get('total_cost', 0):.4f}")
            self.rt_metric_labels["rt_active_sessions"].config(text=f"{rt_data.get('active_sessions', 0)}")
            self.rt_metric_labels["rt_total_tokens"].config(text=f"{rt_data.get('total_tokens', 0):,}")
            
            # Update sessions tree
            self.sessions_tree.delete(*self.sessions_tree.get_children())
            
            for session_data in rt_data.get("sessions", []):
                duration = (datetime.now() - datetime.fromisoformat(session_data["start_time"])).total_seconds() / 60
                
                self.sessions_tree.insert("", tk.END, values=(
                    session_data["session_id"][:8] + "...",
                    session_data["provider_id"],
                    session_data["model_id"],
                    f"{session_data['input_tokens'] + session_data['output_tokens']:,}",
                    f"${session_data['actual_cost']:.4f}",
                    f"{duration:.1f}m"
                ))
        
        except Exception as e:
            print(f"Error updating real-time data: {e}")
    
    def refresh_alerts(self):
        """Refresh alerts display."""
        try:
            # Clear existing items
            self.alerts_tree.delete(*self.alerts_tree.get_children())
            
            # Add current alerts
            for alert in self.cost_tracker.alerts.values():
                status = "Active" if alert.is_active else "Inactive"
                last_triggered = alert.last_triggered.strftime("%m/%d %H:%M") if alert.last_triggered else "Never"
                
                self.alerts_tree.insert("", tk.END, values=(
                    alert.name,
                    alert.alert_type.title(),
                    f"${alert.threshold_value:.4f}",
                    status,
                    alert.triggered_count,
                    last_triggered
                ))
        
        except Exception as e:
            print(f"Error refreshing alerts: {e}")
    
    def update_chart_display(self, hours: int):
        """Update chart display with visualization data."""
        try:
            # Generate dashboard
            dashboard = self.visualization_service.create_dashboard(hours)
            
            # Display chart data as text (in a real implementation, this would render actual charts)
            self.chart_text.delete(1.0, tk.END)
            
            chart_info = f"Cost Dashboard - Last {hours} Hours\n"
            chart_info += "=" * 50 + "\n\n"
            
            # Add metrics
            for key, value in dashboard.metrics.items():
                if isinstance(value, float):
                    chart_info += f"{key.replace('_', ' ').title()}: ${value:.4f}\n"
                else:
                    chart_info += f"{key.replace('_', ' ').title()}: {value}\n"
            
            chart_info += "\n" + "=" * 50 + "\n\n"
            
            # Add chart summaries
            for chart in dashboard.charts:
                chart_info += f"Chart: {chart.title}\n"
                chart_info += f"Type: {chart.chart_type}\n"
                if chart.labels:
                    chart_info += f"Data Points: {len(chart.labels)}\n"
                chart_info += "\n"
            
            self.chart_text.insert(1.0, chart_info)
        
        except Exception as e:
            self.chart_text.delete(1.0, tk.END)
            self.chart_text.insert(1.0, f"Error generating chart data: {e}")
    
    def create_alert_dialog(self):
        """Show create alert dialog."""
        dialog = AlertDialog(self.parent, self.cost_tracker)
        if dialog.result:
            self.refresh_alerts()
    
    def edit_alert_dialog(self):
        """Show edit alert dialog."""
        selection = self.alerts_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an alert to edit.")
            return
        
        # Get selected alert (simplified - would need proper alert lookup)
        messagebox.showinfo("Info", "Edit alert functionality would be implemented here.")
    
    def delete_alert(self):
        """Delete selected alert."""
        selection = self.alerts_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an alert to delete.")
            return
        
        if messagebox.askyesno("Confirm", "Are you sure you want to delete this alert?"):
            # Delete alert logic would be implemented here
            messagebox.showinfo("Info", "Delete alert functionality would be implemented here.")
            self.refresh_alerts()
    
    def generate_report(self):
        """Generate cost report."""
        try:
            hours = int(self.time_period_var.get())
            report_type = self.report_type_var.get()
            
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours)
            
            report = self.cost_tracker.generate_cost_report(start_time, end_time, report_type)
            
            # Display report
            self.report_text.delete(1.0, tk.END)
            
            report_content = f"Cost Report - {report_type.title()}\n"
            report_content += "=" * 50 + "\n\n"
            report_content += f"Period: {start_time.strftime('%Y-%m-%d %H:%M')} to {end_time.strftime('%Y-%m-%d %H:%M')}\n"
            report_content += f"Total Cost: ${report.total_cost:.4f}\n"
            report_content += f"Total Requests: {report.total_requests:,}\n"
            report_content += f"Total Tokens: {report.total_tokens:,}\n\n"
            
            # Provider breakdown
            if report.provider_breakdown:
                report_content += "Provider Breakdown:\n"
                report_content += "-" * 30 + "\n"
                for provider_id, breakdown in report.provider_breakdown.items():
                    report_content += f"{provider_id}: ${breakdown['cost']:.4f} ({breakdown['requests']} requests)\n"
                report_content += "\n"
            
            # Model breakdown
            if report.model_breakdown:
                report_content += "Top Models by Cost:\n"
                report_content += "-" * 30 + "\n"
                sorted_models = sorted(
                    report.model_breakdown.items(),
                    key=lambda x: x[1]["cost"],
                    reverse=True
                )[:10]
                
                for model_key, breakdown in sorted_models:
                    provider_id, model_id = model_key.split(":", 1)
                    report_content += f"{provider_id}:{model_id}: ${breakdown['cost']:.4f}\n"
            
            self.report_text.insert(1.0, report_content)
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate report: {e}")
    
    def export_report(self):
        """Export current report as CSV."""
        try:
            hours = int(self.time_period_var.get())
            report_type = self.report_type_var.get()
            
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours)
            
            report = self.cost_tracker.generate_cost_report(start_time, end_time, report_type)
            csv_data = self.visualization_service.export_report_data(report, "csv")
            
            # Save to file (simplified - would use file dialog in real implementation)
            filename = f"cost_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            with open(filename, 'w') as f:
                f.write(csv_data)
            
            messagebox.showinfo("Success", f"Report exported to {filename}")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export report: {e}")


class AlertDialog:
    """Dialog for creating/editing cost alerts."""
    
    def __init__(self, parent, cost_tracker: CostTracker):
        self.parent = parent
        self.cost_tracker = cost_tracker
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Create Cost Alert")
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.setup_dialog()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        self.dialog.wait_window()
    
    def setup_dialog(self):
        """Set up alert dialog UI."""
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Alert name
        ttk.Label(main_frame, text="Alert Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.name_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.name_var, width=30).grid(row=0, column=1, pady=5)
        
        # Alert type
        ttk.Label(main_frame, text="Alert Type:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.type_var = tk.StringVar(value="threshold")
        type_combo = ttk.Combobox(
            main_frame,
            textvariable=self.type_var,
            values=["threshold", "rate", "budget"],
            state="readonly",
            width=27
        )
        type_combo.grid(row=1, column=1, pady=5)
        
        # Threshold value
        ttk.Label(main_frame, text="Threshold ($):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.threshold_var = tk.StringVar(value="10.00")
        ttk.Entry(main_frame, textvariable=self.threshold_var, width=30).grid(row=2, column=1, pady=5)
        
        # Time window
        ttk.Label(main_frame, text="Time Window (min):").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.time_window_var = tk.StringVar(value="60")
        ttk.Entry(main_frame, textvariable=self.time_window_var, width=30).grid(row=3, column=1, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="Create", command=self.create_alert).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side=tk.LEFT, padx=5)
    
    def create_alert(self):
        """Create the alert."""
        try:
            alert = CostAlert(
                name=self.name_var.get(),
                alert_type=self.type_var.get(),
                threshold_value=float(self.threshold_var.get()),
                time_window_minutes=int(self.time_window_var.get())
            )
            
            if self.cost_tracker.create_alert(alert):
                self.result = alert
                self.dialog.destroy()
            else:
                messagebox.showerror("Error", "Failed to create alert")
        
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid input: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create alert: {e}")
    
    def cancel(self):
        """Cancel dialog."""
        self.dialog.destroy()