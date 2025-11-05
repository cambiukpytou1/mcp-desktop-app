"""
Trend Monitoring Dashboard UI
============================

User interface for trend analysis and performance monitoring.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json


class TrendMonitoringPage:
    """UI page for trend analysis and monitoring dashboard."""
    
    def __init__(self, parent, config_manager, db_manager, trend_service):
        self.parent = parent
        self.config_manager = config_manager
        self.db_manager = db_manager
        self.trend_service = trend_service
        self.logger = logging.getLogger(__name__)
        
        # UI state
        self.selected_prompt_id = None
        self.selected_model_id = None
        self.auto_refresh_enabled = False
        self.refresh_interval = 30000  # 30 seconds
        
        self.setup_ui()
        self.load_initial_data()
    
    def setup_ui(self):
        """Set up the user interface."""
        # Main container
        self.main_frame = ttk.Frame(self.parent)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(
            self.main_frame, 
            text="Trend Analysis & Performance Monitoring",
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Create notebook for different views
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Performance Trends Tab
        self.trends_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.trends_frame, text="Performance Trends")
        self.setup_trends_tab()
        
        # Model Drift Tab
        self.drift_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.drift_frame, text="Model Drift Detection")
        self.setup_drift_tab()
        
        # Alerts Tab
        self.alerts_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.alerts_frame, text="Active Alerts")
        self.setup_alerts_tab()
        
        # Visualizations Tab
        self.viz_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.viz_frame, text="Impact Visualizations")
        self.setup_visualizations_tab()
        
        # Control panel at bottom
        self.setup_control_panel()
    
    def setup_trends_tab(self):
        """Set up the performance trends tab."""
        # Selection frame
        selection_frame = ttk.LabelFrame(self.trends_frame, text="Analysis Selection")
        selection_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Prompt selection
        ttk.Label(selection_frame, text="Prompt:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.prompt_var = tk.StringVar()
        self.prompt_combo = ttk.Combobox(selection_frame, textvariable=self.prompt_var, width=40)
        self.prompt_combo.grid(row=0, column=1, padx=5, pady=5)
        self.prompt_combo.bind('<<ComboboxSelected>>', self.on_prompt_selected)
        
        # Time window selection
        ttk.Label(selection_frame, text="Time Window:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.time_window_var = tk.StringVar(value="30 days")
        time_window_combo = ttk.Combobox(
            selection_frame, 
            textvariable=self.time_window_var,
            values=["7 days", "30 days", "90 days", "180 days"],
            width=15
        )
        time_window_combo.grid(row=0, column=3, padx=5, pady=5)
        
        # Analyze button
        analyze_btn = ttk.Button(
            selection_frame, 
            text="Analyze Trends",
            command=self.analyze_trends
        )
        analyze_btn.grid(row=0, column=4, padx=5, pady=5)
        
        # Results frame
        results_frame = ttk.LabelFrame(self.trends_frame, text="Trend Analysis Results")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create treeview for trend results
        columns = ("Metric", "Trend", "Slope", "Confidence", "Status")
        self.trends_tree = ttk.Treeview(results_frame, columns=columns, show="headings", height=8)
        
        for col in columns:
            self.trends_tree.heading(col, text=col)
            self.trends_tree.column(col, width=120)
        
        # Scrollbar for trends tree
        trends_scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.trends_tree.yview)
        self.trends_tree.configure(yscrollcommand=trends_scrollbar.set)
        
        self.trends_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        trends_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Summary text area
        summary_frame = ttk.LabelFrame(self.trends_frame, text="Analysis Summary")
        summary_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.summary_text = tk.Text(summary_frame, height=6, wrap=tk.WORD)
        summary_scrollbar = ttk.Scrollbar(summary_frame, orient=tk.VERTICAL, command=self.summary_text.yview)
        self.summary_text.configure(yscrollcommand=summary_scrollbar.set)
        
        self.summary_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        summary_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def setup_drift_tab(self):
        """Set up the model drift detection tab."""
        # Model selection frame
        model_frame = ttk.LabelFrame(self.drift_frame, text="Model Selection")
        model_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(model_frame, text="Model:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.model_var = tk.StringVar()
        self.model_combo = ttk.Combobox(model_frame, textvariable=self.model_var, width=30)
        self.model_combo.grid(row=0, column=1, padx=5, pady=5)
        
        # Detection settings
        ttk.Label(model_frame, text="Lookback Days:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.lookback_var = tk.StringVar(value="7")
        lookback_spin = ttk.Spinbox(model_frame, from_=1, to=30, textvariable=self.lookback_var, width=10)
        lookback_spin.grid(row=0, column=3, padx=5, pady=5)
        
        # Detect drift button
        detect_btn = ttk.Button(
            model_frame, 
            text="Detect Drift",
            command=self.detect_model_drift
        )
        detect_btn.grid(row=0, column=4, padx=5, pady=5)
        
        # Drift results frame
        drift_results_frame = ttk.LabelFrame(self.drift_frame, text="Drift Detection Results")
        drift_results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create treeview for drift alerts
        drift_columns = ("Alert ID", "Drift Type", "Severity", "Current", "Baseline", "Drift %", "Status")
        self.drift_tree = ttk.Treeview(drift_results_frame, columns=drift_columns, show="headings", height=10)
        
        for col in drift_columns:
            self.drift_tree.heading(col, text=col)
            self.drift_tree.column(col, width=100)
        
        # Scrollbar for drift tree
        drift_scrollbar = ttk.Scrollbar(drift_results_frame, orient=tk.VERTICAL, command=self.drift_tree.yview)
        self.drift_tree.configure(yscrollcommand=drift_scrollbar.set)
        
        self.drift_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        drift_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind double-click to show alert details
        self.drift_tree.bind("<Double-1>", self.show_drift_alert_details)
        
        # Baseline management frame
        baseline_frame = ttk.LabelFrame(self.drift_frame, text="Baseline Management")
        baseline_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(
            baseline_frame, 
            text="Update Baselines",
            command=self.update_baselines
        ).pack(side=tk.LEFT, padx=5, pady=5)
        
        ttk.Button(
            baseline_frame, 
            text="View Baseline History",
            command=self.view_baseline_history
        ).pack(side=tk.LEFT, padx=5, pady=5)
    
    def setup_alerts_tab(self):
        """Set up the active alerts tab."""
        # Alert filters frame
        filter_frame = ttk.LabelFrame(self.alerts_frame, text="Alert Filters")
        filter_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(filter_frame, text="Severity:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.severity_filter_var = tk.StringVar(value="All")
        severity_combo = ttk.Combobox(
            filter_frame, 
            textvariable=self.severity_filter_var,
            values=["All", "Critical", "High", "Medium", "Low"],
            width=15
        )
        severity_combo.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(filter_frame, text="Type:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.type_filter_var = tk.StringVar(value="All")
        type_combo = ttk.Combobox(
            filter_frame, 
            textvariable=self.type_filter_var,
            values=["All", "Model Drift", "Performance", "Cost", "Quality"],
            width=15
        )
        type_combo.grid(row=0, column=3, padx=5, pady=5)
        
        # Refresh alerts button
        refresh_btn = ttk.Button(
            filter_frame, 
            text="Refresh Alerts",
            command=self.refresh_alerts
        )
        refresh_btn.grid(row=0, column=4, padx=5, pady=5)
        
        # Alerts list frame
        alerts_list_frame = ttk.LabelFrame(self.alerts_frame, text="Active Alerts")
        alerts_list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create treeview for alerts
        alert_columns = ("Timestamp", "Type", "Severity", "Description", "Source", "Status")
        self.alerts_tree = ttk.Treeview(alerts_list_frame, columns=alert_columns, show="headings", height=12)
        
        for col in alert_columns:
            self.alerts_tree.heading(col, text=col)
            self.alerts_tree.column(col, width=120)
        
        # Scrollbar for alerts tree
        alerts_scrollbar = ttk.Scrollbar(alerts_list_frame, orient=tk.VERTICAL, command=self.alerts_tree.yview)
        self.alerts_tree.configure(yscrollcommand=alerts_scrollbar.set)
        
        self.alerts_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        alerts_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind double-click to show alert details
        self.alerts_tree.bind("<Double-1>", self.show_alert_details)
        
        # Alert actions frame
        actions_frame = ttk.LabelFrame(self.alerts_frame, text="Alert Actions")
        actions_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(
            actions_frame, 
            text="Acknowledge Selected",
            command=self.acknowledge_alert
        ).pack(side=tk.LEFT, padx=5, pady=5)
        
        ttk.Button(
            actions_frame, 
            text="Dismiss Selected",
            command=self.dismiss_alert
        ).pack(side=tk.LEFT, padx=5, pady=5)
        
        ttk.Button(
            actions_frame, 
            text="Export Alerts",
            command=self.export_alerts
        ).pack(side=tk.LEFT, padx=5, pady=5)
    
    def setup_visualizations_tab(self):
        """Set up the impact visualizations tab."""
        # Visualization controls frame
        viz_controls_frame = ttk.LabelFrame(self.viz_frame, text="Visualization Controls")
        viz_controls_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Prompt selection for visualization
        ttk.Label(viz_controls_frame, text="Prompt:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.viz_prompt_var = tk.StringVar()
        self.viz_prompt_combo = ttk.Combobox(viz_controls_frame, textvariable=self.viz_prompt_var, width=30)
        self.viz_prompt_combo.grid(row=0, column=1, padx=5, pady=5)
        
        # Visualization type selection
        ttk.Label(viz_controls_frame, text="Type:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.viz_type_var = tk.StringVar(value="line_chart")
        viz_type_combo = ttk.Combobox(
            viz_controls_frame, 
            textvariable=self.viz_type_var,
            values=["line_chart", "heatmap", "scatter_plot", "bar_chart"],
            width=15
        )
        viz_type_combo.grid(row=0, column=3, padx=5, pady=5)
        
        # Generate visualization button
        generate_btn = ttk.Button(
            viz_controls_frame, 
            text="Generate Visualization",
            command=self.generate_visualization
        )
        generate_btn.grid(row=0, column=4, padx=5, pady=5)
        
        # Visualization display frame
        viz_display_frame = ttk.LabelFrame(self.viz_frame, text="Visualization")
        viz_display_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Text area to display visualization data (in a real implementation, this would be a chart)
        self.viz_text = tk.Text(viz_display_frame, wrap=tk.WORD)
        viz_text_scrollbar = ttk.Scrollbar(viz_display_frame, orient=tk.VERTICAL, command=self.viz_text.yview)
        self.viz_text.configure(yscrollcommand=viz_text_scrollbar.set)
        
        self.viz_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        viz_text_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Export visualization button
        export_viz_frame = ttk.Frame(self.viz_frame)
        export_viz_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(
            export_viz_frame, 
            text="Export Visualization Data",
            command=self.export_visualization
        ).pack(side=tk.RIGHT, padx=5, pady=5)
    
    def setup_control_panel(self):
        """Set up the control panel at the bottom."""
        control_frame = ttk.LabelFrame(self.main_frame, text="Monitoring Controls")
        control_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Auto-refresh controls
        self.auto_refresh_var = tk.BooleanVar()
        auto_refresh_check = ttk.Checkbutton(
            control_frame, 
            text="Auto-refresh",
            variable=self.auto_refresh_var,
            command=self.toggle_auto_refresh
        )
        auto_refresh_check.pack(side=tk.LEFT, padx=5, pady=5)
        
        ttk.Label(control_frame, text="Interval (seconds):").pack(side=tk.LEFT, padx=5, pady=5)
        self.refresh_interval_var = tk.StringVar(value="30")
        interval_spin = ttk.Spinbox(
            control_frame, 
            from_=10, 
            to=300, 
            textvariable=self.refresh_interval_var,
            width=10,
            command=self.update_refresh_interval
        )
        interval_spin.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Manual refresh button
        ttk.Button(
            control_frame, 
            text="Refresh All",
            command=self.refresh_all_data
        ).pack(side=tk.LEFT, padx=10, pady=5)
        
        # Status label
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(control_frame, textvariable=self.status_var)
        status_label.pack(side=tk.RIGHT, padx=5, pady=5)
    
    def load_initial_data(self):
        """Load initial data for the dashboard."""
        try:
            self.status_var.set("Loading data...")
            
            # Load prompts for selection
            self.load_prompts()
            
            # Load models for selection
            self.load_models()
            
            # Load initial alerts
            self.refresh_alerts()
            
            self.status_var.set("Ready")
            
        except Exception as e:
            self.logger.error(f"Error loading initial data: {e}")
            self.status_var.set("Error loading data")
            messagebox.showerror("Error", f"Failed to load initial data: {e}")
    
    def load_prompts(self):
        """Load available prompts for selection."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, name FROM prompts ORDER BY name")
                prompts = cursor.fetchall()
                
                prompt_values = [f"{row[1]} ({row[0]})" for row in prompts]
                self.prompt_combo['values'] = prompt_values
                self.viz_prompt_combo['values'] = prompt_values
                
        except Exception as e:
            self.logger.error(f"Error loading prompts: {e}")
    
    def load_models(self):
        """Load available models for selection."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT DISTINCT model FROM evaluation_results 
                    WHERE created_at >= ? 
                    ORDER BY model
                """, ((datetime.now() - timedelta(days=30)).isoformat(),))
                models = cursor.fetchall()
                
                model_values = [row[0] for row in models]
                self.model_combo['values'] = model_values
                
        except Exception as e:
            self.logger.error(f"Error loading models: {e}")
    
    def on_prompt_selected(self, event=None):
        """Handle prompt selection."""
        selection = self.prompt_var.get()
        if selection and "(" in selection:
            # Extract prompt ID from selection
            self.selected_prompt_id = selection.split("(")[-1].rstrip(")")
    
    def analyze_trends(self):
        """Analyze trends for the selected prompt."""
        if not self.selected_prompt_id:
            messagebox.showwarning("Warning", "Please select a prompt first.")
            return
        
        try:
            self.status_var.set("Analyzing trends...")
            
            # Parse time window
            time_window_str = self.time_window_var.get()
            days = int(time_window_str.split()[0])
            
            # Perform trend analysis
            results = self.trend_service.track_historical_performance(
                self.selected_prompt_id, days
            )
            
            # Display results
            self.display_trend_results(results)
            
            self.status_var.set("Trend analysis completed")
            
        except Exception as e:
            self.logger.error(f"Error analyzing trends: {e}")
            self.status_var.set("Error analyzing trends")
            messagebox.showerror("Error", f"Failed to analyze trends: {e}")
    
    def display_trend_results(self, results: Dict[str, Any]):
        """Display trend analysis results."""
        # Clear existing results
        for item in self.trends_tree.get_children():
            self.trends_tree.delete(item)
        
        if results.get('status') == 'insufficient_data':
            self.trends_tree.insert('', 'end', values=(
                "Insufficient Data", 
                f"{results.get('data_points', 0)} points",
                f"Need {results.get('minimum_required', 5)}",
                "N/A", "N/A"
            ))
            self.summary_text.delete(1.0, tk.END)
            self.summary_text.insert(tk.END, "Insufficient data for trend analysis. More evaluation runs needed.")
            return
        
        # Display trend results
        trends = results.get('trends', {})
        for metric, trend_analysis in trends.items():
            trend_type = trend_analysis.get('trend_type', 'unknown')
            slope = trend_analysis.get('slope', 0.0)
            confidence = trend_analysis.get('confidence', 0.0)
            
            # Determine status color/indicator
            if trend_type == 'improving':
                status = "↗ Good"
            elif trend_type == 'declining':
                status = "↘ Concerning"
            elif trend_type == 'stable':
                status = "→ Stable"
            else:
                status = "? Volatile"
            
            self.trends_tree.insert('', 'end', values=(
                metric.title(),
                trend_type.title(),
                f"{slope:.4f}",
                f"{confidence:.2%}",
                status
            ))
        
        # Display summary
        summary = results.get('summary', {})
        self.summary_text.delete(1.0, tk.END)
        
        summary_text = f"Overall Health: {summary.get('overall_health', 'Unknown').title()}\n\n"
        
        insights = summary.get('key_insights', [])
        if insights:
            summary_text += "Key Insights:\n"
            for insight in insights:
                summary_text += f"• {insight}\n"
            summary_text += "\n"
        
        recommendations = summary.get('recommendations', [])
        if recommendations:
            summary_text += "Recommendations:\n"
            for rec in recommendations:
                summary_text += f"• {rec}\n"
        
        self.summary_text.insert(tk.END, summary_text)
    
    def detect_model_drift(self):
        """Detect drift for the selected model."""
        model_id = self.model_var.get()
        if not model_id:
            messagebox.showwarning("Warning", "Please select a model first.")
            return
        
        try:
            self.status_var.set("Detecting model drift...")
            
            lookback_days = int(self.lookback_var.get())
            
            # Detect drift
            drift_alerts = self.trend_service.detect_model_drift(model_id, lookback_days)
            
            # Display results
            self.display_drift_results(drift_alerts)
            
            self.status_var.set(f"Drift detection completed: {len(drift_alerts)} alerts")
            
        except Exception as e:
            self.logger.error(f"Error detecting model drift: {e}")
            self.status_var.set("Error detecting drift")
            messagebox.showerror("Error", f"Failed to detect model drift: {e}")
    
    def display_drift_results(self, drift_alerts: List):
        """Display drift detection results."""
        # Clear existing results
        for item in self.drift_tree.get_children():
            self.drift_tree.delete(item)
        
        # Display drift alerts
        for alert in drift_alerts:
            status = "🔴 Active" if alert.severity in ['critical', 'high'] else "🟡 Monitor"
            
            self.drift_tree.insert('', 'end', values=(
                alert.alert_id[:20] + "...",
                alert.drift_type.title(),
                alert.severity.title(),
                f"{alert.current_value:.4f}",
                f"{alert.baseline_value:.4f}",
                f"{alert.drift_percentage:.1%}",
                status
            ))
    
    def show_drift_alert_details(self, event):
        """Show detailed information about a drift alert."""
        selection = self.drift_tree.selection()
        if not selection:
            return
        
        item = self.drift_tree.item(selection[0])
        alert_id = item['values'][0]
        
        # In a real implementation, you would fetch full alert details
        # For now, show a simple message
        messagebox.showinfo("Alert Details", f"Alert ID: {alert_id}\n\nDetailed information would be displayed here.")
    
    def refresh_alerts(self):
        """Refresh the active alerts list."""
        try:
            self.status_var.set("Refreshing alerts...")
            
            # Get active alerts
            alerts = self.trend_service.monitor_performance_alerts()
            
            # Clear existing alerts
            for item in self.alerts_tree.get_children():
                self.alerts_tree.delete(item)
            
            # Display alerts
            for alert in alerts:
                severity = alert.get('severity', 'low')
                alert_type = alert.get('type', 'unknown')
                
                # Apply filters
                if (self.severity_filter_var.get() != "All" and 
                    severity.title() != self.severity_filter_var.get()):
                    continue
                
                if (self.type_filter_var.get() != "All" and 
                    alert_type.replace('_', ' ').title() != self.type_filter_var.get()):
                    continue
                
                # Status indicator
                if severity == 'critical':
                    status = "🔴 Critical"
                elif severity == 'high':
                    status = "🟠 High"
                elif severity == 'medium':
                    status = "🟡 Medium"
                else:
                    status = "🔵 Low"
                
                self.alerts_tree.insert('', 'end', values=(
                    alert.get('timestamp', '')[:19],  # Truncate timestamp
                    alert_type.replace('_', ' ').title(),
                    severity.title(),
                    alert.get('description', '')[:50] + "...",
                    alert.get('model_id', alert.get('prompt_id', 'Unknown')),
                    status
                ))
            
            self.status_var.set(f"Alerts refreshed: {len(alerts)} total")
            
        except Exception as e:
            self.logger.error(f"Error refreshing alerts: {e}")
            self.status_var.set("Error refreshing alerts")
            messagebox.showerror("Error", f"Failed to refresh alerts: {e}")
    
    def show_alert_details(self, event):
        """Show detailed information about an alert."""
        selection = self.alerts_tree.selection()
        if not selection:
            return
        
        item = self.alerts_tree.item(selection[0])
        alert_info = item['values']
        
        details = f"Timestamp: {alert_info[0]}\n"
        details += f"Type: {alert_info[1]}\n"
        details += f"Severity: {alert_info[2]}\n"
        details += f"Description: {alert_info[3]}\n"
        details += f"Source: {alert_info[4]}\n"
        details += f"Status: {alert_info[5]}"
        
        messagebox.showinfo("Alert Details", details)
    
    def acknowledge_alert(self):
        """Acknowledge the selected alert."""
        selection = self.alerts_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an alert first.")
            return
        
        # In a real implementation, you would update the alert status in the database
        messagebox.showinfo("Success", "Alert acknowledged.")
        self.refresh_alerts()
    
    def dismiss_alert(self):
        """Dismiss the selected alert."""
        selection = self.alerts_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an alert first.")
            return
        
        # In a real implementation, you would remove or mark the alert as dismissed
        messagebox.showinfo("Success", "Alert dismissed.")
        self.refresh_alerts()
    
    def export_alerts(self):
        """Export alerts to a file."""
        try:
            from tkinter import filedialog
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filename:
                alerts = self.trend_service.monitor_performance_alerts()
                with open(filename, 'w') as f:
                    json.dump(alerts, f, indent=2, default=str)
                
                messagebox.showinfo("Success", f"Alerts exported to {filename}")
                
        except Exception as e:
            self.logger.error(f"Error exporting alerts: {e}")
            messagebox.showerror("Error", f"Failed to export alerts: {e}")
    
    def generate_visualization(self):
        """Generate impact visualization."""
        prompt_selection = self.viz_prompt_var.get()
        if not prompt_selection or "(" not in prompt_selection:
            messagebox.showwarning("Warning", "Please select a prompt first.")
            return
        
        try:
            self.status_var.set("Generating visualization...")
            
            # Extract prompt ID
            prompt_id = prompt_selection.split("(")[-1].rstrip(")")
            viz_type = self.viz_type_var.get()
            
            # Generate visualization
            visualization = self.trend_service.generate_impact_visualization(prompt_id, viz_type)
            
            # Display visualization data
            self.display_visualization(visualization)
            
            self.status_var.set("Visualization generated")
            
        except Exception as e:
            self.logger.error(f"Error generating visualization: {e}")
            self.status_var.set("Error generating visualization")
            messagebox.showerror("Error", f"Failed to generate visualization: {e}")
    
    def display_visualization(self, visualization):
        """Display visualization data."""
        self.viz_text.delete(1.0, tk.END)
        
        viz_text = f"Visualization: {visualization.title}\n"
        viz_text += f"Type: {visualization.visualization_type}\n"
        viz_text += f"X-Axis: {visualization.x_axis_label}\n"
        viz_text += f"Y-Axis: {visualization.y_axis_label}\n\n"
        
        viz_text += "Data Series:\n"
        for series in visualization.data_series:
            viz_text += f"- {series['name']}: {len(series['data'])} points\n"
        
        viz_text += f"\nMetadata: {json.dumps(visualization.metadata, indent=2)}"
        
        # In a real implementation, this would render an actual chart
        viz_text += "\n\n[Chart would be displayed here in a real implementation]"
        
        self.viz_text.insert(tk.END, viz_text)
    
    def export_visualization(self):
        """Export visualization data."""
        try:
            from tkinter import filedialog
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filename:
                viz_data = self.viz_text.get(1.0, tk.END)
                with open(filename, 'w') as f:
                    f.write(viz_data)
                
                messagebox.showinfo("Success", f"Visualization data exported to {filename}")
                
        except Exception as e:
            self.logger.error(f"Error exporting visualization: {e}")
            messagebox.showerror("Error", f"Failed to export visualization: {e}")
    
    def update_baselines(self):
        """Update performance baselines."""
        try:
            self.status_var.set("Updating baselines...")
            
            # In a real implementation, this would trigger baseline recalculation
            # For now, show a confirmation
            messagebox.showinfo("Success", "Baselines updated successfully.")
            
            self.status_var.set("Baselines updated")
            
        except Exception as e:
            self.logger.error(f"Error updating baselines: {e}")
            messagebox.showerror("Error", f"Failed to update baselines: {e}")
    
    def view_baseline_history(self):
        """View baseline history."""
        messagebox.showinfo("Baseline History", "Baseline history viewer would be displayed here.")
    
    def toggle_auto_refresh(self):
        """Toggle auto-refresh functionality."""
        self.auto_refresh_enabled = self.auto_refresh_var.get()
        
        if self.auto_refresh_enabled:
            self.schedule_refresh()
            self.status_var.set("Auto-refresh enabled")
        else:
            self.status_var.set("Auto-refresh disabled")
    
    def update_refresh_interval(self):
        """Update the refresh interval."""
        try:
            self.refresh_interval = int(self.refresh_interval_var.get()) * 1000  # Convert to milliseconds
        except ValueError:
            self.refresh_interval = 30000  # Default to 30 seconds
    
    def schedule_refresh(self):
        """Schedule the next auto-refresh."""
        if self.auto_refresh_enabled:
            self.parent.after(self.refresh_interval, self.auto_refresh)
    
    def auto_refresh(self):
        """Perform auto-refresh of data."""
        if self.auto_refresh_enabled:
            try:
                self.refresh_alerts()
                self.schedule_refresh()
            except Exception as e:
                self.logger.error(f"Error during auto-refresh: {e}")
                self.schedule_refresh()  # Continue refreshing even if there's an error
    
    def refresh_all_data(self):
        """Refresh all data in the dashboard."""
        try:
            self.status_var.set("Refreshing all data...")
            
            self.load_prompts()
            self.load_models()
            self.refresh_alerts()
            
            # Refresh current analysis if available
            if self.selected_prompt_id:
                self.analyze_trends()
            
            self.status_var.set("All data refreshed")
            
        except Exception as e:
            self.logger.error(f"Error refreshing all data: {e}")
            self.status_var.set("Error refreshing data")
            messagebox.showerror("Error", f"Failed to refresh data: {e}")