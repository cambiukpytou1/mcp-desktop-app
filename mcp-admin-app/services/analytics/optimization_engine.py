"""
Optimization Suggestion Engine
==============================

Provides meta-LLM based improvement suggestions and automated optimization.
"""

import logging
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import re


@dataclass
class OptimizationSuggestion:
    """Represents an optimization suggestion for a prompt."""
    suggestion_id: str
    prompt_id: str
    suggestion_type: str  # 'structure', 'clarity', 'specificity', 'examples', 'constraints'
    priority: str  # 'high', 'medium', 'low'
    description: str
    rationale: str
    expected_improvement: float  # Expected performance boost (0.0-1.0)
    implementation_effort: str  # 'low', 'medium', 'high'
    suggested_changes: List[str]
    before_example: str
    after_example: str
    confidence_score: float
    created_at: datetime


@dataclass
class OptimizationReport:
    """Comprehensive optimization report for a prompt."""
    prompt_id: str
    current_performance: Dict[str, float]
    optimization_potential: float
    suggestions: List[OptimizationSuggestion]
    quick_wins: List[OptimizationSuggestion]
    long_term_improvements: List[OptimizationSuggestion]
    overall_recommendation: str
    generated_at: datetime


@dataclass
class PerformanceBasedOptimization:
    """Performance-based optimization recommendation."""
    optimization_id: str
    prompt_id: str
    performance_issue: str
    root_cause_analysis: str
    optimization_strategy: str
    expected_metrics_improvement: Dict[str, float]
    implementation_steps: List[str]
    success_criteria: List[str]
    risk_assessment: str


class OptimizationEngine:
    """Handles automated prompt optimization suggestions."""
    
    def __init__(self, config_manager, db_manager, llm_manager):
        self.logger = logging.getLogger(__name__)
        self.config_manager = config_manager
        self.db_manager = db_manager
        self.llm_manager = llm_manager
        
        # Optimization parameters
        self.min_confidence_threshold = 0.6
        self.high_priority_threshold = 0.8
        self.performance_improvement_threshold = 0.1
        
        # Optimization patterns and rules
        self.optimization_rules = self._initialize_optimization_rules()
        self.meta_prompts = self._initialize_meta_prompts()
        
        self.logger.info("Optimization engine initialized")
    
    def 