"""
Optimization Recommendations UI Component
=========================================

UI component for displaying optimization recommendations and semantic clustering insights.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

from services.analytics.semantic_clustering import SemanticClustering
from services.analytics.performance_analytics import PerformanceAnalytics


class OptimizationRecommendationsWidget:
    """Widget for displaying optimization recommendations."""
    
    def __init__(self, parent, config_manager, db_manager):
        self.parent = parent
        self.config_manager = config_manager
        self.db_manager = db_manager
        
        # Initialize services
        try:
            self.semantic_clustering = SemanticClustering(config_manager, db_manager, None)
            self.performance_analytics = PerformanceAnalytics(config_manager, db_manager)
        except Exception as e:
            print(f"Warning: Could not initialize analytics services: {e}")
            self.semantic_clustering = None
            self.performance_analytics = None
        
        # UI state
        self.current_recommendations = []
        self.current_clusters = []
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the optimization recommendations UI."""
        # Main container
        self.main_frame = ttk.Frame(self.parent)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create notebook for different recommendation types
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self.create_recommendations_tab()
        self.create_clustering_tab()
        self.create_export_tab()
    
    def create_recommendations_tab(self):
        """Create recommendations panel tab."""
        rec_frame = ttk.Frame(self.notebook)
        self.notebook.add(rec_frame, text="Recommendations")
        
        # Control panel
        control_frame = ttk.LabelFrame(rec_frame, text="Recommendation Controls", padding=10)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Generate recommendations button
        generate_btn = ttk.Button(
            control_frame,
            text="Generate Recommendations",
            command=self.generate_recommendations
        )
        generate_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Recommendations display
        rec_display_frame = ttk.LabelFrame(rec_frame, text="Optimization Recommendations", padding=10)
        rec_display_frame.pack(fill=tk.BOTH, expand=True)
        
        # Recommendations text area
        self.rec_text = tk.Text(rec_display_frame, wrap=tk.WORD)
        rec_scrollbar = ttk.Scrollbar(rec_display_frame, orient=tk.VERTICAL, command=self.rec_text.yview)
        self.rec_text.configure(yscrollcommand=rec_scrollbar.set)
        
        self.rec_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        rec_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_clustering_tab(self):
        """Create semantic clustering visualization tab."""
        cluster_frame = ttk.Frame(self.notebook)
        self.notebook.add(cluster_frame, text="Semantic Clustering")
        
        # Clustering controls
        cluster_control_frame = ttk.LabelFrame(cluster_frame, text="Clustering Controls", padding=10)
        cluster_control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Generate clusters button
        cluster_btn = ttk.Button(
            cluster_control_frame,
            text="Generate Clusters",
            command=self.generate_clusters
        )
        cluster_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Clusters display
        cluster_display_frame = ttk.LabelFrame(cluster_frame, text="Semantic Clusters", padding=10)
        cluster_display_frame.pack(fill=tk.BOTH, expand=True)
        
        # Clusters text area
        self.cluster_text = tk.Text(cluster_display_frame, wrap=tk.WORD)
        cluster_scrollbar = ttk.Scrollbar(cluster_display_frame, orient=tk.VERTICAL, command=self.cluster_text.yview)
        self.cluster_text.configure(yscrollcommand=cluster_scrollbar.set)
        
        self.cluster_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        cluster_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_export_tab(self):
        """Create export capabilities tab."""
        export_frame = ttk.Frame(self.notebook)
        self.notebook.add(export_frame, text="Export & Reports")
        
        # Export controls
        export_control_frame = ttk.LabelFrame(export_frame, text="Export Controls", padding=10)
        export_control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Export button
        export_btn = ttk.Button(
            export_control_frame,
            text="Export Report",
            command=self.export_report
        )
        export_btn.pack(side=tk.LEFT)
        
        # Report preview
        preview_frame = ttk.LabelFrame(export_frame, text="Report Preview", padding=10)
        preview_frame.pack(fill=tk.BOTH, expand=True)
        
        self.preview_text = tk.Text(preview_frame, wrap=tk.WORD)
        preview_scrollbar = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self.preview_text.yview)
        self.preview_text.configure(yscrollcommand=preview_scrollbar.set)
        
        self.preview_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        preview_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def generate_recommendations(self):
        """Generate optimization recommendations."""
        try:
            self.rec_text.delete(1.0, tk.END)
            
            if not self.performance_analytics:
                self.rec_text.insert(1.0, "Performance analytics service not available.")
                return
            
            # Generate performance insights
            insights = self.performance_analytics.generate_performance_insights()
            
            # Convert insights to recommendations
            recommendations = self._convert_insights_to_recommendations(insights)
            self.current_recommendations = recommendations
            
            # Display recommendations
            self.display_recommendations(recommendations)
            
            messagebox.showinfo("Success", f"Generated {len(recommendations)} recommendations")
            
        except Exception as e:
            error_msg = f"Failed to generate recommendations: {e}"
            self.rec_text.insert(1.0, error_msg)
            messagebox.showerror("Error", error_msg)
    
    def _convert_insights_to_recommendations(self, insights: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert performance insights to actionable recommendations."""
        recommendations = []
        
        # Process improvement opportunities
        opportunities = insights.get("improvement_opportunities", [])
        for opp in opportunities:
            rec = {
                "priority": "high" if opp.get("improvement_potential") == "high" else "medium",
                "type": "performance",
                "prompt_id": opp["prompt_id"],
                "recommendation": opp["recommendation"],
                "expected_impact": opp.get("improvement_potential", "medium"),
                "details": f"Current score: {opp.get('current_score', 0):.3f}"
            }
            recommendations.append(rec)
        
        # Process patterns
        patterns = insights.get("patterns", [])
        for pattern in patterns:
            rec = {
                "priority": "medium",
                "type": "patterns",
                "prompt_id": "multiple",
                "recommendation": f"Apply '{pattern.pattern_description}' pattern to more prompts",
                "expected_impact": f"+{pattern.avg_performance_boost:.3f}",
                "details": f"Pattern found in {pattern.frequency} high-performing prompts"
            }
            recommendations.append(rec)
        
        return recommendations
    
    def display_recommendations(self, recommendations: List[Dict[str, Any]]):
        """Display recommendations in the text area."""
        content = "OPTIMIZATION RECOMMENDATIONS\n"
        content += "=" * 40 + "\n\n"
        
        if not recommendations:
            content += "No recommendations available.\n"
        else:
            for i, rec in enumerate(recommendations, 1):
                content += f"{i}. {rec['recommendation']}\n"
                content += f"   Priority: {rec['priority'].title()}\n"
                content += f"   Type: {rec['type'].title()}\n"
                content += f"   Target: {rec['prompt_id']}\n"
                content += f"   Expected Impact: {rec['expected_impact']}\n"
                content += f"   Details: {rec['details']}\n\n"
        
        self.rec_text.insert(1.0, content)
    
    def generate_clusters(self):
        """Generate semantic clusters."""
        try:
            self.cluster_text.delete(1.0, tk.END)
            
            if not self.semantic_clustering:
                self.cluster_text.insert(1.0, "Semantic clustering service not available.")
                return
            
            # Generate clusters based on intent categories
            intent_categories = self.semantic_clustering.categorize_prompts_by_intent()
            
            # Convert to cluster format
            clusters = []
            for category in intent_categories:
                cluster = {
                    "name": category.name,
                    "intent": category.name,
                    "prompt_count": category.prompt_count,
                    "avg_performance": category.avg_performance
                }
                clusters.append(cluster)
            
            self.current_clusters = clusters
            self.display_clusters(clusters)
            
            messagebox.showinfo("Success", f"Generated {len(clusters)} semantic clusters")
            
        except Exception as e:
            error_msg = f"Failed to generate clusters: {e}"
            self.cluster_text.insert(1.0, error_msg)
            messagebox.showerror("Error", error_msg)
    
    def display_clusters(self, clusters: List[Dict[str, Any]]):
        """Display clusters in the text area."""
        content = "SEMANTIC CLUSTERS\n"
        content += "=" * 25 + "\n\n"
        
        if not clusters:
            content += "No clusters available.\n"
        else:
            for i, cluster in enumerate(clusters, 1):
                content += f"{i}. {cluster['name']}\n"
                content += f"   Intent: {cluster['intent']}\n"
                content += f"   Prompts: {cluster['prompt_count']}\n"
                content += f"   Performance: {cluster['avg_performance']:.3f}\n\n"
        
        self.cluster_text.insert(1.0, content)
    
    def export_report(self):
        """Export analytics report."""
        try:
            # Generate report content
            report_content = self._generate_export_content()
            
            # Save to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"optimization_report_{timestamp}.txt"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            # Show preview
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(1.0, report_content)
            
            messagebox.showinfo("Success", f"Report exported to {filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export report: {e}")
    
    def _generate_export_content(self) -> str:
        """Generate export content."""
        content = f"OPTIMIZATION ANALYTICS REPORT\n"
        content += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        content += "=" * 50 + "\n\n"
        
        # Add recommendations
        if self.current_recommendations:
            content += "OPTIMIZATION RECOMMENDATIONS\n"
            content += "-" * 30 + "\n\n"
            
            for i, rec in enumerate(self.current_recommendations, 1):
                content += f"{i}. {rec['recommendation']}\n"
                content += f"   Priority: {rec['priority'].title()}\n"
                content += f"   Type: {rec['type'].title()}\n"
                content += f"   Target: {rec['prompt_id']}\n"
                content += f"   Expected Impact: {rec['expected_impact']}\n"
                content += f"   Details: {rec['details']}\n\n"
        
        # Add clusters
        if self.current_clusters:
            content += "SEMANTIC CLUSTERS\n"
            content += "-" * 20 + "\n\n"
            
            for i, cluster in enumerate(self.current_clusters, 1):
                content += f"{i}. {cluster['name']}\n"
                content += f"   Intent: {cluster['intent']}\n"
                content += f"   Prompts: {cluster['prompt_count']}\n"
                content += f"   Performance: {cluster['avg_performance']:.3f}\n\n"
        
        return content