"""
Analytics Dashboard UI Page
===========================

User interface for performance analytics visualization, cost tracking, and insights.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from services.analytics.performance_analytics import PerformanceAnalytics
from services.analytics.trend_analysis import TrendAnalysisService
from services.evaluation.cost_tracking import CostTracker
from ui.prompt_components.optimization_recommendations_simple import OptimizationRecommendationsWidget


import tkinter as tk

class AnalyticsDashboardPage(tk.Frame):
    """Analytics dashboard and visualization page."""
    
    def __init__(self, parent, config_manager, db_manager):
        super().__init__(parent, bg="#f9f9f9")
        self.parent = parent
        self.config_manager = config_manager
        self.db_manager = db_manager
        
        # Initialize services
        self.performance_analytics = PerformanceAnalytics(config_manager, db_manager)
        self.trend_analysis = TrendAnalysisService(config_manager, db_manager)
        self.cost_tracker = CostTracker(config_manager, db_manager)
        
        # UI state
        self.refresh_interval = 60  # seconds
        self.auto_refresh = True
        self.refresh_job = None
        self.current_insights = {}
        
        self.setup_ui()
        self.refresh_data()
    
    def setup_ui(self):
        """Set up the user interface."""
        # Main container
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(
            self.main_frame, 
            text="Analytics Dashboard & Insights", 
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self.create_performance_tab()
        self.create_cost_analytics_tab()
        self.create_trends_tab()
        self.create_insights_tab()
        self.create_optimization_tab()
    
    def create_performance_tab(self):
        """Create performance analytics visualization tab."""
        perf_frame = ttk.Frame(self.notebook)
        self.notebook.add(perf_frame, text="Performance Analytics")
        
        # Control panel
        control_frame = ttk.LabelFrame(perf_frame, text="Controls", padding=10)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Time period selection
        ttk.Label(control_frame, text="Analysis Period:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.perf_period_var = tk.StringVar(value="30")
        period_combo = ttk.Combobox(
            control_frame, 
            textvariable=self.perf_period_var,
            values=["7", "30", "90", "180"],  # days
            width=10,
            state="readonly"
        )
        period_combo.grid(row=0, column=1, padx=(0, 10))
        period_combo.bind("<<ComboboxSelected>>", self.on_period_changed)
        
        # Prompt selection
        ttk.Label(control_frame, text="Prompt:").grid(row=0, column=2, sticky=tk.W, padx=(10, 5))
        self.prompt_var = tk.StringVar(value="All Prompts")
        self.prompt_combo = ttk.Combobox(
            control_frame, 
            textvariable=self.prompt_var,
            width=20,
            state="readonly"
        )
        self.prompt_combo.grid(row=0, column=3, padx=(0, 10))
        self.prompt_combo.bind("<<ComboboxSelected>>", self.on_prompt_changed)
        
        # Refresh button
        refresh_btn = ttk.Button(
            control_frame, 
            text="Refresh", 
            command=self.refresh_performance_data
        )
        refresh_btn.grid(row=0, column=4, padx=(0, 10))
        
        # Auto-refresh toggle
        self.auto_refresh_var = tk.BooleanVar(value=True)
        auto_refresh_check = ttk.Checkbutton(
            control_frame,
            text="Auto-refresh",
            variable=self.auto_refresh_var,
            command=self.toggle_auto_refresh
        )
        auto_refresh_check.grid(row=0, column=5)
        
        # Performance metrics display
        metrics_frame = ttk.LabelFrame(perf_frame, text="Performance Metrics", padding=10)
        metrics_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Create metric labels
        self.perf_metric_labels = {}
        perf_metrics = [
            ("avg_score", "Average Score"),
            ("success_rate", "Success Rate"),
            ("execution_count", "Total Executions"),
            ("avg_response_time", "Avg Response Time (ms)"),
            ("score_variance", "Score Variance"),
            ("quality_trend", "Quality Trend")
        ]
        
        for i, (key, label) in enumerate(perf_metrics):
            row = i // 3
            col = (i % 3) * 2
            
            ttk.Label(metrics_frame, text=f"{label}:").grid(
                row=row, column=col, sticky=tk.W, padx=(0, 5), pady=2
            )
            
            value_label = ttk.Label(metrics_frame, text="N/A", font=("Arial", 10, "bold"))
            value_label.grid(row=row, column=col+1, sticky=tk.W, padx=(0, 20), pady=2)
            self.perf_metric_labels[key] = value_label
        
        # Performance visualization area
        viz_frame = ttk.LabelFrame(perf_frame, text="Performance Visualization", padding=10)
        viz_frame.pack(fill=tk.BOTH, expand=True)
        
        self.perf_viz_text = tk.Text(viz_frame, height=15, wrap=tk.WORD)
        perf_viz_scrollbar = ttk.Scrollbar(viz_frame, orient=tk.VERTICAL, command=self.perf_viz_text.yview)
        self.perf_viz_text.configure(yscrollcommand=perf_viz_scrollbar.set)
        
        self.perf_viz_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        perf_viz_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_cost_analytics_tab(self):
        """Create cost tracking and breakdown displays tab."""
        cost_frame = ttk.Frame(self.notebook)
        self.notebook.add(cost_frame, text="Cost Analytics")
        
        # Cost control panel
        cost_control_frame = ttk.LabelFrame(cost_frame, text="Cost Analysis Controls", padding=10)
        cost_control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Time period for cost analysis
        ttk.Label(cost_control_frame, text="Time Period:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.cost_period_var = tk.StringVar(value="24")
        cost_period_combo = ttk.Combobox(
            cost_control_frame, 
            textvariable=self.cost_period_var,
            values=["1", "6", "24", "168", "720"],  # 1h, 6h, 24h, 1w, 1m
            width=10,
            state="readonly"
        )
        cost_period_combo.grid(row=0, column=1, padx=(0, 10))
        cost_period_combo.bind("<<ComboboxSelected>>", self.on_cost_period_changed)
        
        # Provider filter
        ttk.Label(cost_control_frame, text="Provider:").grid(row=0, column=2, sticky=tk.W, padx=(10, 5))
        self.provider_var = tk.StringVar(value="All Providers")
        self.provider_combo = ttk.Combobox(
            cost_control_frame, 
            textvariable=self.provider_var,
            width=15,
            state="readonly"
        )
        self.provider_combo.grid(row=0, column=3, padx=(0, 10))
        self.provider_combo.bind("<<ComboboxSelected>>", self.on_provider_changed)
        
        # Refresh cost data button
        refresh_cost_btn = ttk.Button(
            cost_control_frame, 
            text="Refresh Cost Data", 
            command=self.refresh_cost_data
        )
        refresh_cost_btn.grid(row=0, column=4)
        
        # Cost metrics display
        cost_metrics_frame = ttk.LabelFrame(cost_frame, text="Cost Metrics", padding=10)
        cost_metrics_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.cost_metric_labels = {}
        cost_metrics = [
            ("total_cost", "Total Cost"),
            ("avg_cost_per_request", "Avg Cost/Request"),
            ("avg_cost_per_token", "Avg Cost/Token"),
            ("total_tokens", "Total Tokens"),
            ("cost_trend", "Cost Trend"),
            ("efficiency_score", "Efficiency Score")
        ]
        
        for i, (key, label) in enumerate(cost_metrics):
            row = i // 3
            col = (i % 3) * 2
            
            ttk.Label(cost_metrics_frame, text=f"{label}:").grid(
                row=row, column=col, sticky=tk.W, padx=(0, 5), pady=2
            )
            
            value_label = ttk.Label(cost_metrics_frame, text="$0.00", font=("Arial", 10, "bold"))
            value_label.grid(row=row, column=col+1, sticky=tk.W, padx=(0, 20), pady=2)
            self.cost_metric_labels[key] = value_label
        
        # Cost breakdown visualization
        cost_viz_frame = ttk.LabelFrame(cost_frame, text="Cost Breakdown & Comparison", padding=10)
        cost_viz_frame.pack(fill=tk.BOTH, expand=True)
        
        self.cost_viz_text = tk.Text(cost_viz_frame, height=15, wrap=tk.WORD)
        cost_viz_scrollbar = ttk.Scrollbar(cost_viz_frame, orient=tk.VERTICAL, command=self.cost_viz_text.yview)
        self.cost_viz_text.configure(yscrollcommand=cost_viz_scrollbar.set)
        
        self.cost_viz_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        cost_viz_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_trends_tab(self):
        """Create performance comparison tables and insights tab."""
        trends_frame = ttk.Frame(self.notebook)
        self.notebook.add(trends_frame, text="Trends & Comparisons")
        
        # Trends control panel
        trends_control_frame = ttk.LabelFrame(trends_frame, text="Trend Analysis Controls", padding=10)
        trends_control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Analysis type
        ttk.Label(trends_control_frame, text="Analysis Type:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.trend_type_var = tk.StringVar(value="performance")
        trend_type_combo = ttk.Combobox(
            trends_control_frame, 
            textvariable=self.trend_type_var,
            values=["performance", "cost", "usage", "quality"],
            width=12,
            state="readonly"
        )
        trend_type_combo.grid(row=0, column=1, padx=(0, 10))
        trend_type_combo.bind("<<ComboboxSelected>>", self.on_trend_type_changed)
        
        # Comparison period
        ttk.Label(trends_control_frame, text="Period:").grid(row=0, column=2, sticky=tk.W, padx=(10, 5))
        self.trend_period_var = tk.StringVar(value="30")
        trend_period_combo = ttk.Combobox(
            trends_control_frame, 
            textvariable=self.trend_period_var,
            values=["7", "30", "90"],
            width=8,
            state="readonly"
        )
        trend_period_combo.grid(row=0, column=3, padx=(0, 10))
        trend_period_combo.bind("<<ComboboxSelected>>", self.on_trend_period_changed)
        
        # Generate trends button
        generate_trends_btn = ttk.Button(
            trends_control_frame, 
            text="Generate Analysis", 
            command=self.generate_trend_analysis
        )
        generate_trends_btn.grid(row=0, column=4)
        
        # Performance comparison table
        comparison_frame = ttk.LabelFrame(trends_frame, text="Performance Comparison Table", padding=10)
        comparison_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Comparison treeview
        comparison_columns = ("Prompt ID", "Avg Score", "Success Rate", "Executions", "Trend", "Change %")
        self.comparison_tree = ttk.Treeview(comparison_frame, columns=comparison_columns, show="headings", height=8)
        
        for col in comparison_columns:
            self.comparison_tree.heading(col, text=col)
            self.comparison_tree.column(col, width=100)
        
        comparison_scrollbar = ttk.Scrollbar(comparison_frame, orient=tk.VERTICAL, command=self.comparison_tree.yview)
        self.comparison_tree.configure(yscrollcommand=comparison_scrollbar.set)
        
        self.comparison_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        comparison_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Insights display
        insights_frame = ttk.LabelFrame(trends_frame, text="Trend Insights", padding=10)
        insights_frame.pack(fill=tk.X)
        
        self.trends_insights_text = tk.Text(insights_frame, height=6, wrap=tk.WORD)
        trends_insights_scrollbar = ttk.Scrollbar(insights_frame, orient=tk.VERTICAL, command=self.trends_insights_text.yview)
        self.trends_insights_text.configure(yscrollcommand=trends_insights_scrollbar.set)
        
        self.trends_insights_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        trends_insights_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_insights_tab(self):
        """Create optimization recommendations interface tab."""
        insights_frame = ttk.Frame(self.notebook)
        self.notebook.add(insights_frame, text="Insights & Recommendations")
        
        # Insights control panel
        insights_control_frame = ttk.LabelFrame(insights_frame, text="Insights Controls", padding=10)
        insights_control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Insight type
        ttk.Label(insights_control_frame, text="Insight Type:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.insight_type_var = tk.StringVar(value="all")
        insight_type_combo = ttk.Combobox(
            insights_control_frame, 
            textvariable=self.insight_type_var,
            values=["all", "performance", "cost", "patterns", "opportunities"],
            width=15,
            state="readonly"
        )
        insight_type_combo.grid(row=0, column=1, padx=(0, 10))
        insight_type_combo.bind("<<ComboboxSelected>>", self.on_insight_type_changed)
        
        # Generate insights button
        generate_insights_btn = ttk.Button(
            insights_control_frame, 
            text="Generate Insights", 
            command=self.generate_insights
        )
        generate_insights_btn.grid(row=0, column=2, padx=(0, 10))
        
        # Export insights button
        export_insights_btn = ttk.Button(
            insights_control_frame, 
            text="Export Report", 
            command=self.export_insights
        )
        export_insights_btn.grid(row=0, column=3)
        
        # Recommendations panel
        recommendations_frame = ttk.LabelFrame(insights_frame, text="Optimization Recommendations", padding=10)
        recommendations_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.recommendations_text = tk.Text(recommendations_frame, height=10, wrap=tk.WORD)
        recommendations_scrollbar = ttk.Scrollbar(recommendations_frame, orient=tk.VERTICAL, command=self.recommendations_text.yview)
        self.recommendations_text.configure(yscrollcommand=recommendations_scrollbar.set)
        
        self.recommendations_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        recommendations_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Patterns and insights display
        patterns_frame = ttk.LabelFrame(insights_frame, text="Identified Patterns & Insights", padding=10)
        patterns_frame.pack(fill=tk.BOTH, expand=True)
        
        self.patterns_text = tk.Text(patterns_frame, height=10, wrap=tk.WORD)
        patterns_scrollbar = ttk.Scrollbar(patterns_frame, orient=tk.VERTICAL, command=self.patterns_text.yview)
        self.patterns_text.configure(yscrollcommand=patterns_scrollbar.set)
        
        self.patterns_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        patterns_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def on_period_changed(self, event=None):
        """Handle analysis period change."""
        self.refresh_performance_data()
    
    def on_prompt_changed(self, event=None):
        """Handle prompt selection change."""
        self.refresh_performance_data()
    
    def on_cost_period_changed(self, event=None):
        """Handle cost period change."""
        self.refresh_cost_data()
    
    def on_provider_changed(self, event=None):
        """Handle provider filter change."""
        self.refresh_cost_data()
    
    def on_trend_type_changed(self, event=None):
        """Handle trend analysis type change."""
        self.generate_trend_analysis()
    
    def on_trend_period_changed(self, event=None):
        """Handle trend period change."""
        self.generate_trend_analysis()
    
    def on_insight_type_changed(self, event=None):
        """Handle insight type change."""
        self.filter_insights()
    
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
        """Refresh all analytics data."""
        try:
            self.refresh_performance_data()
            self.refresh_cost_data()
            self.generate_trend_analysis()
            self.load_prompt_list()
            self.load_provider_list()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh data: {e}")
    
    def load_prompt_list(self):
        """Load available prompts for selection."""
        try:
            # Get all prompt IDs
            prompt_ids = self.performance_analytics._get_all_prompt_ids()
            
            # Update prompt combo
            values = ["All Prompts"] + prompt_ids[:20]  # Limit to first 20 for UI
            self.prompt_combo['values'] = values
            
        except Exception as e:
            print(f"Error loading prompt list: {e}")
    
    def load_provider_list(self):
        """Load available providers for filtering."""
        try:
            # Get providers from config
            providers = list(self.config_manager.get("llm_providers", {}).keys())
            
            # Update provider combo
            values = ["All Providers"] + providers
            self.provider_combo['values'] = values
            
        except Exception as e:
            print(f"Error loading provider list: {e}")
    
    def refresh_performance_data(self):
        """Refresh performance analytics data."""
        try:
            # Get selected prompt and period
            selected_prompt = self.prompt_var.get()
            period_days = int(self.perf_period_var.get())
            
            if selected_prompt == "All Prompts":
                # Generate insights for all prompts
                insights = self.performance_analytics.generate_performance_insights()
                self.update_performance_metrics_from_insights(insights)
                self.update_performance_visualization(insights)
            else:
                # Analyze specific prompt
                metrics = self.performance_analytics.analyze_prompt_effectiveness(
                    selected_prompt, period_days
                )
                self.update_performance_metrics(metrics)
                self.update_single_prompt_visualization(selected_prompt, metrics)
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh performance data: {e}")
    
    def update_performance_metrics(self, metrics):
        """Update performance metric labels."""
        self.perf_metric_labels["avg_score"].config(text=f"{metrics.avg_score:.3f}")
        self.perf_metric_labels["success_rate"].config(text=f"{metrics.success_rate:.1%}")
        self.perf_metric_labels["execution_count"].config(text=f"{metrics.execution_count:,}")
        self.perf_metric_labels["avg_response_time"].config(text=f"{metrics.avg_response_time:.0f}")
        self.perf_metric_labels["score_variance"].config(text=f"{metrics.score_variance:.3f}")
        self.perf_metric_labels["quality_trend"].config(text=metrics.quality_trend.title())
    
    def update_performance_metrics_from_insights(self, insights):
        """Update performance metrics from insights data."""
        summary = insights.get("summary", {})
        
        self.perf_metric_labels["avg_score"].config(
            text=f"{summary.get('overall_avg_score', 0):.3f}"
        )
        self.perf_metric_labels["success_rate"].config(
            text=f"{summary.get('overall_success_rate', 0):.1%}"
        )
        self.perf_metric_labels["execution_count"].config(
            text=f"{summary.get('analyzed_prompts', 0):,}"
        )
        self.perf_metric_labels["avg_response_time"].config(text="N/A")
        self.perf_metric_labels["score_variance"].config(text="N/A")
        self.perf_metric_labels["quality_trend"].config(text="Mixed")
    
    def update_performance_visualization(self, insights):
        """Update performance visualization with insights data."""
        try:
            self.perf_viz_text.delete(1.0, tk.END)
            
            viz_content = "Performance Analytics Dashboard\n"
            viz_content += "=" * 50 + "\n\n"
            
            # Summary statistics
            summary = insights.get("summary", {})
            viz_content += "SUMMARY STATISTICS\n"
            viz_content += "-" * 20 + "\n"
            viz_content += f"Total Prompts: {summary.get('total_prompts', 0)}\n"
            viz_content += f"Analyzed Prompts: {summary.get('analyzed_prompts', 0)}\n"
            viz_content += f"Overall Avg Score: {summary.get('overall_avg_score', 0):.3f}\n"
            viz_content += f"Overall Success Rate: {summary.get('overall_success_rate', 0):.1%}\n"
            viz_content += f"Overall Avg Cost: ${summary.get('overall_avg_cost', 0):.4f}\n\n"
            
            # Top performers
            top_performers = insights.get("top_performers", [])
            if top_performers:
                viz_content += "TOP PERFORMING PROMPTS\n"
                viz_content += "-" * 25 + "\n"
                for i, prompt in enumerate(top_performers[:5], 1):
                    viz_content += f"{i}. {prompt['prompt_id'][:20]}... "
                    viz_content += f"(Score: {prompt['avg_score']:.3f}, "
                    viz_content += f"Success: {prompt['success_rate']:.1%})\n"
                viz_content += "\n"
            
            # Improvement opportunities
            opportunities = insights.get("improvement_opportunities", [])
            if opportunities:
                viz_content += "IMPROVEMENT OPPORTUNITIES\n"
                viz_content += "-" * 30 + "\n"
                for opp in opportunities[:5]:
                    viz_content += f"• {opp['prompt_id'][:20]}... "
                    viz_content += f"({opp['opportunity_type'].replace('_', ' ').title()})\n"
                    viz_content += f"  Recommendation: {opp['recommendation']}\n"
                viz_content += "\n"
            
            # Patterns
            patterns = insights.get("patterns", [])
            if patterns:
                viz_content += "IDENTIFIED PATTERNS\n"
                viz_content += "-" * 20 + "\n"
                for pattern in patterns[:3]:
                    viz_content += f"• {pattern.pattern_description}\n"
                    viz_content += f"  Frequency: {pattern.frequency}, "
                    viz_content += f"Performance Boost: {pattern.avg_performance_boost:+.3f}\n"
                viz_content += "\n"
            
            # Trends
            trends = insights.get("trends", {})
            if trends:
                viz_content += "PERFORMANCE TRENDS\n"
                viz_content += "-" * 20 + "\n"
                trend_counts = trends.get("trend_counts", {})
                for trend, count in trend_counts.items():
                    if count > 0:
                        viz_content += f"• {trend.replace('_', ' ').title()}: {count} prompts\n"
                viz_content += f"Overall Health: {trends.get('overall_health', 'unknown').title()}\n"
            
            self.perf_viz_text.insert(1.0, viz_content)
            
        except Exception as e:
            self.perf_viz_text.delete(1.0, tk.END)
            self.perf_viz_text.insert(1.0, f"Error generating visualization: {e}")
    
    def update_single_prompt_visualization(self, prompt_id, metrics):
        """Update visualization for single prompt analysis."""
        try:
            self.perf_viz_text.delete(1.0, tk.END)
            
            viz_content = f"Performance Analysis: {prompt_id}\n"
            viz_content += "=" * 50 + "\n\n"
            
            viz_content += "PERFORMANCE METRICS\n"
            viz_content += "-" * 20 + "\n"
            viz_content += f"Average Score: {metrics.avg_score:.3f}\n"
            viz_content += f"Score Variance: {metrics.score_variance:.3f}\n"
            viz_content += f"Execution Count: {metrics.execution_count:,}\n"
            viz_content += f"Success Rate: {metrics.success_rate:.1%}\n"
            viz_content += f"Average Cost: ${metrics.avg_cost:.4f}\n"
            viz_content += f"Average Tokens: {metrics.avg_tokens:,}\n"
            viz_content += f"Average Response Time: {metrics.avg_response_time:.0f}ms\n"
            viz_content += f"Quality Trend: {metrics.quality_trend.title()}\n\n"
            
            # Performance assessment
            viz_content += "PERFORMANCE ASSESSMENT\n"
            viz_content += "-" * 25 + "\n"
            
            if metrics.avg_score >= 0.8:
                assessment = "Excellent"
            elif metrics.avg_score >= 0.6:
                assessment = "Good"
            elif metrics.avg_score >= 0.4:
                assessment = "Fair"
            else:
                assessment = "Needs Improvement"
            
            viz_content += f"Overall Assessment: {assessment}\n"
            
            if metrics.score_variance > 0.1:
                viz_content += "• High variance detected - consider improving consistency\n"
            
            if metrics.quality_trend == "declining":
                viz_content += "• Declining trend detected - investigate recent changes\n"
            elif metrics.quality_trend == "improving":
                viz_content += "• Improving trend detected - good progress\n"
            
            if metrics.success_rate < 0.7:
                viz_content += "• Low success rate - review prompt effectiveness\n"
            
            self.perf_viz_text.insert(1.0, viz_content)
            
        except Exception as e:
            self.perf_viz_text.delete(1.0, tk.END)
            self.perf_viz_text.insert(1.0, f"Error generating single prompt visualization: {e}")
    
    def refresh_cost_data(self):
        """Refresh cost analytics data."""
        try:
            # Get selected period and provider
            hours = int(self.cost_period_var.get())
            selected_provider = self.provider_var.get()
            
            # Generate cost report
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours)
            
            report = self.cost_tracker.generate_cost_report(start_time, end_time, "detailed")
            
            # Update cost metrics
            self.update_cost_metrics(report, selected_provider)
            
            # Update cost visualization
            self.update_cost_visualization(report, selected_provider)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh cost data: {e}")
    
    def update_cost_metrics(self, report, selected_provider):
        """Update cost metric labels."""
        # Filter data by provider if selected
        if selected_provider != "All Providers":
            provider_data = report.provider_breakdown.get(selected_provider, {})
            total_cost = provider_data.get("cost", 0)
            total_requests = provider_data.get("requests", 0)
            total_tokens = provider_data.get("tokens", 0)
        else:
            total_cost = report.total_cost
            total_requests = report.total_requests
            total_tokens = report.total_tokens
        
        # Calculate derived metrics
        avg_cost_per_request = total_cost / total_requests if total_requests > 0 else 0
        avg_cost_per_token = total_cost / total_tokens if total_tokens > 0 else 0
        
        # Update labels
        self.cost_metric_labels["total_cost"].config(text=f"${total_cost:.4f}")
        self.cost_metric_labels["avg_cost_per_request"].config(text=f"${avg_cost_per_request:.6f}")
        self.cost_metric_labels["avg_cost_per_token"].config(text=f"${avg_cost_per_token:.8f}")
        self.cost_metric_labels["total_tokens"].config(text=f"{total_tokens:,}")
        self.cost_metric_labels["cost_trend"].config(text="Stable")  # Placeholder
        self.cost_metric_labels["efficiency_score"].config(text="85%")  # Placeholder
    
    def update_cost_visualization(self, report, selected_provider):
        """Update cost visualization display."""
        try:
            self.cost_viz_text.delete(1.0, tk.END)
            
            viz_content = f"Cost Analytics Dashboard\n"
            viz_content += "=" * 50 + "\n\n"
            
            # Report summary
            viz_content += "COST SUMMARY\n"
            viz_content += "-" * 15 + "\n"
            viz_content += f"Report Period: {report.time_period_start.strftime('%Y-%m-%d %H:%M')} to "
            viz_content += f"{report.time_period_end.strftime('%Y-%m-%d %H:%M')}\n"
            viz_content += f"Total Cost: ${report.total_cost:.4f}\n"
            viz_content += f"Total Requests: {report.total_requests:,}\n"
            viz_content += f"Total Tokens: {report.total_tokens:,}\n\n"
            
            # Provider breakdown
            if report.provider_breakdown:
                viz_content += "PROVIDER BREAKDOWN\n"
                viz_content += "-" * 20 + "\n"
                
                # Sort providers by cost
                sorted_providers = sorted(
                    report.provider_breakdown.items(),
                    key=lambda x: x[1].get("cost", 0),
                    reverse=True
                )
                
                for provider_id, breakdown in sorted_providers:
                    cost = breakdown.get("cost", 0)
                    requests = breakdown.get("requests", 0)
                    tokens = breakdown.get("tokens", 0)
                    percentage = (cost / report.total_cost * 100) if report.total_cost > 0 else 0
                    
                    viz_content += f"• {provider_id}: ${cost:.4f} ({percentage:.1f}%)\n"
                    viz_content += f"  Requests: {requests:,}, Tokens: {tokens:,}\n"
                
                viz_content += "\n"
            
            # Model breakdown (top 10)
            if report.model_breakdown:
                viz_content += "TOP MODELS BY COST\n"
                viz_content += "-" * 20 + "\n"
                
                sorted_models = sorted(
                    report.model_breakdown.items(),
                    key=lambda x: x[1].get("cost", 0),
                    reverse=True
                )[:10]
                
                for model_key, breakdown in sorted_models:
                    cost = breakdown.get("cost", 0)
                    requests = breakdown.get("requests", 0)
                    percentage = (cost / report.total_cost * 100) if report.total_cost > 0 else 0
                    
                    viz_content += f"• {model_key}: ${cost:.4f} ({percentage:.1f}%)\n"
                    viz_content += f"  Requests: {requests:,}\n"
                
                viz_content += "\n"
            
            # Hourly breakdown (if available)
            if report.hourly_breakdown:
                viz_content += "HOURLY COST PATTERN\n"
                viz_content += "-" * 20 + "\n"
                
                for hour_data in report.hourly_breakdown[-12:]:  # Last 12 hours
                    hour = hour_data.get("hour", "")
                    cost = hour_data.get("cost", 0)
                    requests = hour_data.get("requests", 0)
                    
                    viz_content += f"• {hour}: ${cost:.4f} ({requests} requests)\n"
            
            self.cost_viz_text.insert(1.0, viz_content)
            
        except Exception as e:
            self.cost_viz_text.delete(1.0, tk.END)
            self.cost_viz_text.insert(1.0, f"Error generating cost visualization: {e}")
    
    def generate_trend_analysis(self):
        """Generate trend analysis and comparison tables."""
        try:
            # Get analysis parameters
            trend_type = self.trend_type_var.get()
            period_days = int(self.trend_period_var.get())
            
            # Clear existing data
            self.comparison_tree.delete(*self.comparison_tree.get_children())
            
            # Get prompt IDs for analysis
            prompt_ids = self.performance_analytics._get_all_prompt_ids()[:20]  # Limit for performance
            
            # Generate comparison data
            comparison_data = []
            
            for prompt_id in prompt_ids:
                try:
                    # Get current metrics
                    metrics = self.performance_analytics.analyze_prompt_effectiveness(prompt_id, period_days)
                    
                    if metrics.execution_count >= 3:  # Minimum for reliable data
                        # Get historical tracking for trend
                        historical = self.trend_analysis.track_historical_performance(prompt_id, period_days)
                        
                        # Calculate change percentage (placeholder)
                        change_pct = 0.0
                        if historical.get("status") == "success":
                            trends = historical.get("trends", {})
                            score_trend = trends.get("score", {})
                            if score_trend.get("trend_type") == "improving":
                                change_pct = 5.0
                            elif score_trend.get("trend_type") == "declining":
                                change_pct = -5.0
                        
                        comparison_data.append({
                            "prompt_id": prompt_id,
                            "avg_score": metrics.avg_score,
                            "success_rate": metrics.success_rate,
                            "execution_count": metrics.execution_count,
                            "quality_trend": metrics.quality_trend,
                            "change_pct": change_pct
                        })
                
                except Exception as e:
                    print(f"Error analyzing prompt {prompt_id}: {e}")
                    continue
            
            # Sort by average score
            comparison_data.sort(key=lambda x: x["avg_score"], reverse=True)
            
            # Populate comparison tree
            for data in comparison_data:
                trend_symbol = {
                    "improving": "↗",
                    "declining": "↘",
                    "stable": "→",
                    "volatile": "↕"
                }.get(data["quality_trend"], "?")
                
                change_text = f"{data['change_pct']:+.1f}%" if data["change_pct"] != 0 else "0.0%"
                
                self.comparison_tree.insert("", tk.END, values=(
                    data["prompt_id"][:15] + "..." if len(data["prompt_id"]) > 15 else data["prompt_id"],
                    f"{data['avg_score']:.3f}",
                    f"{data['success_rate']:.1%}",
                    f"{data['execution_count']:,}",
                    f"{trend_symbol} {data['quality_trend'].title()}",
                    change_text
                ))
            
            # Generate trend insights
            self.generate_trend_insights(comparison_data)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate trend analysis: {e}")
    
    def generate_trend_insights(self, comparison_data):
        """Generate insights from trend analysis."""
        try:
            self.trends_insights_text.delete(1.0, tk.END)
            
            if not comparison_data:
                self.trends_insights_text.insert(1.0, "No data available for trend analysis.")
                return
            
            insights_content = "TREND ANALYSIS INSIGHTS\n"
            insights_content += "=" * 30 + "\n\n"
            
            # Count trends
            trend_counts = {}
            for data in comparison_data:
                trend = data["quality_trend"]
                trend_counts[trend] = trend_counts.get(trend, 0) + 1
            
            total_prompts = len(comparison_data)
            
            # Overall assessment
            improving = trend_counts.get("improving", 0)
            declining = trend_counts.get("declining", 0)
            stable = trend_counts.get("stable", 0)
            
            insights_content += f"Analyzed {total_prompts} prompts:\n"
            insights_content += f"• Improving: {improving} ({improving/total_prompts:.1%})\n"
            insights_content += f"• Declining: {declining} ({declining/total_prompts:.1%})\n"
            insights_content += f"• Stable: {stable} ({stable/total_prompts:.1%})\n\n"
            
            # Key insights
            if improving > declining:
                insights_content += "✓ Overall positive trend - most prompts are improving\n"
            elif declining > improving:
                insights_content += "⚠ Concerning trend - more prompts declining than improving\n"
            else:
                insights_content += "→ Mixed trends - balanced improvement and decline\n"
            
            # Top and bottom performers
            if comparison_data:
                best = comparison_data[0]
                worst = comparison_data[-1]
                
                insights_content += f"\nBest Performer: {best['prompt_id'][:20]}... "
                insights_content += f"(Score: {best['avg_score']:.3f})\n"
                
                insights_content += f"Needs Attention: {worst['prompt_id'][:20]}... "
                insights_content += f"(Score: {worst['avg_score']:.3f})\n"
            
            self.trends_insights_text.insert(1.0, insights_content)
            
        except Exception as e:
            self.trends_insights_text.delete(1.0, tk.END)
            self.trends_insights_text.insert(1.0, f"Error generating trend insights: {e}")
    
    def generate_insights(self):
        """Generate comprehensive insights and recommendations."""
        try:
            # Generate performance insights
            insights = self.performance_analytics.generate_performance_insights()
            self.current_insights = insights
            
            # Update recommendations
            self.update_recommendations(insights)
            
            # Update patterns display
            self.update_patterns_display(insights)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate insights: {e}")
    
    def update_recommendations(self, insights):
        """Update optimization recommendations display."""
        try:
            self.recommendations_text.delete(1.0, tk.END)
            
            recommendations_content = "OPTIMIZATION RECOMMENDATIONS\n"
            recommendations_content += "=" * 35 + "\n\n"
            
            # Improvement opportunities
            opportunities = insights.get("improvement_opportunities", [])
            if opportunities:
                recommendations_content += "IMMEDIATE ACTIONS\n"
                recommendations_content += "-" * 20 + "\n"
                
                for i, opp in enumerate(opportunities[:5], 1):
                    recommendations_content += f"{i}. {opp['recommendation']}\n"
                    recommendations_content += f"   Target: {opp['prompt_id'][:25]}...\n"
                    recommendations_content += f"   Impact: {opp['improvement_potential'].title()}\n\n"
            
            # Pattern-based recommendations
            patterns = insights.get("patterns", [])
            if patterns:
                recommendations_content += "PATTERN-BASED RECOMMENDATIONS\n"
                recommendations_content += "-" * 35 + "\n"
                
                for pattern in patterns[:3]:
                    recommendations_content += f"• Apply '{pattern.pattern_description}' pattern\n"
                    recommendations_content += f"  Expected boost: {pattern.avg_performance_boost:+.3f}\n"
                    recommendations_content += f"  Frequency in high performers: {pattern.frequency}\n\n"
            
            # General recommendations
            summary = insights.get("summary", {})
            overall_score = summary.get("overall_avg_score", 0)
            
            recommendations_content += "GENERAL RECOMMENDATIONS\n"
            recommendations_content += "-" * 25 + "\n"
            
            if overall_score < 0.6:
                recommendations_content += "• Focus on improving prompt clarity and specificity\n"
                recommendations_content += "• Review and update underperforming prompts\n"
                recommendations_content += "• Consider A/B testing different prompt variations\n"
            elif overall_score < 0.8:
                recommendations_content += "• Fine-tune high-variance prompts for consistency\n"
                recommendations_content += "• Implement successful patterns across more prompts\n"
                recommendations_content += "• Monitor and address declining trends quickly\n"
            else:
                recommendations_content += "• Maintain current high performance standards\n"
                recommendations_content += "• Experiment with advanced optimization techniques\n"
                recommendations_content += "• Share successful patterns with team\n"
            
            self.recommendations_text.insert(1.0, recommendations_content)
            
        except Exception as e:
            self.recommendations_text.delete(1.0, tk.END)
            self.recommendations_text.insert(1.0, f"Error generating recommendations: {e}")
    
    def update_patterns_display(self, insights):
        """Update patterns and insights display."""
        try:
            self.patterns_text.delete(1.0, tk.END)
            
            patterns_content = "IDENTIFIED PATTERNS & INSIGHTS\n"
            patterns_content += "=" * 40 + "\n\n"
            
            # High-performing patterns
            patterns = insights.get("patterns", [])
            if patterns:
                patterns_content += "HIGH-PERFORMING PATTERNS\n"
                patterns_content += "-" * 30 + "\n"
                
                for pattern in patterns:
                    patterns_content += f"Pattern: {pattern.pattern_description}\n"
                    patterns_content += f"Type: {pattern.pattern_type.title()}\n"
                    patterns_content += f"Frequency: {pattern.frequency} prompts\n"
                    patterns_content += f"Performance Boost: {pattern.avg_performance_boost:+.3f}\n"
                    
                    if pattern.examples:
                        patterns_content += "Examples:\n"
                        for example in pattern.examples[:2]:
                            patterns_content += f"  • {example}\n"
                    
                    patterns_content += "\n"
            
            # Summary insights
            summary = insights.get("summary", {})
            if summary:
                patterns_content += "SUMMARY INSIGHTS\n"
                patterns_content += "-" * 20 + "\n"
                
                total_prompts = summary.get("total_prompts", 0)
                analyzed_prompts = summary.get("analyzed_prompts", 0)
                
                patterns_content += f"Dataset: {analyzed_prompts} of {total_prompts} prompts analyzed\n"
                patterns_content += f"Overall Performance: {summary.get('overall_avg_score', 0):.3f}\n"
                patterns_content += f"Success Rate: {summary.get('overall_success_rate', 0):.1%}\n"
                patterns_content += f"Average Cost: ${summary.get('overall_avg_cost', 0):.4f}\n\n"
            
            # Trend insights
            trends = insights.get("trends", {})
            if trends:
                patterns_content += "TREND INSIGHTS\n"
                patterns_content += "-" * 15 + "\n"
                
                overall_health = trends.get("overall_health", "unknown")
                patterns_content += f"Overall Health: {overall_health.title()}\n"
                
                trend_percentages = trends.get("trend_percentages", {})
                for trend, percentage in trend_percentages.items():
                    if percentage > 0:
                        patterns_content += f"{trend.replace('_', ' ').title()}: {percentage:.1f}%\n"
            
            self.patterns_text.insert(1.0, patterns_content)
            
        except Exception as e:
            self.patterns_text.delete(1.0, tk.END)
            self.patterns_text.insert(1.0, f"Error displaying patterns: {e}")
    
    def filter_insights(self):
        """Filter insights based on selected type."""
        if not self.current_insights:
            return
        
        insight_type = self.insight_type_var.get()
        
        if insight_type == "all":
            self.update_recommendations(self.current_insights)
            self.update_patterns_display(self.current_insights)
        else:
            # Filter and display specific insight type
            # This would be implemented based on specific filtering needs
            pass
    
    def export_insights(self):
        """Export insights and recommendations as a report."""
        try:
            if not self.current_insights:
                messagebox.showwarning("Warning", "No insights available to export. Generate insights first.")
                return
            
            # Generate export content
            export_content = "ANALYTICS INSIGHTS REPORT\n"
            export_content += "=" * 50 + "\n"
            export_content += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            # Add all insights content
            export_content += self.recommendations_text.get(1.0, tk.END)
            export_content += "\n" + "=" * 50 + "\n\n"
            export_content += self.patterns_text.get(1.0, tk.END)
            
            # Save to file
            filename = f"analytics_insights_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(export_content)
            
            messagebox.showinfo("Success", f"Insights exported to {filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export insights: {e}")
    
    def create_optimization_tab(self):
        """Create optimization recommendations tab."""
        optimization_frame = ttk.Frame(self.notebook)
        self.notebook.add(optimization_frame, text="Optimization")
        
        # Create optimization recommendations widget
        self.optimization_widget = OptimizationRecommendationsWidget(
            optimization_frame, 
            self.config_manager, 
            self.db_manager
        )