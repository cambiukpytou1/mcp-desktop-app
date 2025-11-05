"""
Simple Optimization Recommendations UI Component
===============================================

Simplified UI component for displaying optimization recommendations.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Optional, Any
from datetime import datetime


class OptimizationRecommendationsWidget:
    """Widget for displaying optimization recommendations."""
    
    def __init__(self, parent, config_manager, db_manager):
        self.parent = parent
        self.config_manager = config_manager
        self.db_manager = db_manager
        
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
    
    def generate_recommendations(self):
        """Generate optimization recommendations."""
        try:
            self.rec_text.delete(1.0, tk.END)
            
            # Generate mock recommendations for demonstration
            recommendations = [
                {
                    "priority": "high",
                    "type": "performance",
                    "prompt_id": "prompt_001",
                    "recommendation": "Improve prompt clarity and specificity",
                    "expected_impact": "high",
                    "details": "Current score: 0.65"
                },
                {
                    "priority": "medium",
                    "type": "patterns",
                    "prompt_id": "multiple",
                    "recommendation": "Apply 'use examples' pattern to more prompts",
                    "expected_impact": "+0.15",
                    "details": "Pattern found in 8 high-performing prompts"
                },
                {
                    "priority": "medium",
                    "type": "cost",
                    "prompt_id": "all",
                    "recommendation": "Optimize prompts for cost efficiency",
                    "expected_impact": "medium",
                    "details": "Average cost per execution: $0.0125"
                }
            ]
            
            self.current_recommendations = recommendations
            self.display_recommendations(recommendations)
            
            messagebox.showinfo("Success", f"Generated {len(recommendations)} recommendations")
            
        except Exception as e:
            error_msg = f"Failed to generate recommendations: {e}"
            self.rec_text.insert(1.0, error_msg)
            messagebox.showerror("Error", error_msg)
    
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
            
            # Generate mock clusters for demonstration
            clusters = [
                {
                    "name": "Analysis Prompts",
                    "intent": "analysis",
                    "prompt_count": 12,
                    "avg_performance": 0.82
                },
                {
                    "name": "Generation Prompts",
                    "intent": "generation",
                    "prompt_count": 8,
                    "avg_performance": 0.75
                },
                {
                    "name": "Summarization Prompts",
                    "intent": "summarization",
                    "prompt_count": 6,
                    "avg_performance": 0.78
                }
            ]
            
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
                
                # Add performance assessment
                if cluster['avg_performance'] >= 0.8:
                    content += f"   Assessment: Excellent performance\n"
                elif cluster['avg_performance'] >= 0.7:
                    content += f"   Assessment: Good performance\n"
                else:
                    content += f"   Assessment: Needs improvement\n"
                content += "\n"
        
        self.cluster_text.insert(1.0, content)