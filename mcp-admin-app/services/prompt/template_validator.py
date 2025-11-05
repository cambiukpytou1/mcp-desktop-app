"""
Template Validation Service
==========================

Service for validating prompt templates and their variable usage.
"""

import re
import json
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime

from .templating_engine import TemplateVariable, TemplateValidationResult, AdvancedTemplatingEngine


@dataclass
class ValidationRule:
    """Template validation rule definition."""
    name: str
    description: str
    severity: str  # 'error', 'warning', 'info'
    pattern: Optional[str] = None
    check_function: Optional[str] = None


@dataclass
class TemplateAnalysis:
    """Comprehensive template analysis result."""
    template_id: str
    content: str
    variables: List[TemplateVariable] = field(default_factory=list)
    validation_result: Optional[TemplateValidationResult] = None
    security_issues: List[str] = field(default_factory=list)
    performance_warnings: List[str] = field(default_factory=list)
    best_practice_violations: List[str] = field(default_factory=list)
    complexity_score: int = 0
    readability_score: float = 0.0
    analyzed_at: datetime = field(default_factory=datetime.now)


class TemplateValidator:
    """
    Comprehensive template validation service.
    
    Provides validation, security checking, and best practice analysis
    for prompt templates.
    """
    
    def __init__(self):
        """Initialize the template validator."""
        self.templating_engine = AdvancedTemplatingEngine()
        self.validation_rules = self._load_validation_rules()
        
        # Security patterns to detect
        self.security_patterns = {
            'potential_injection': r'(eval|exec|import|__|\bfile\b|\bopen\b)',
            'system_commands': r'(system|subprocess|os\.)',
            'sensitive_data': r'(password|secret|key|token|credential)',
            'external_calls': r'(http|ftp|ssh|telnet)://',
        }
        
        # Performance warning patterns
        self.performance_patterns = {
            'complex_loops': r'\{%\s*for\s+\w+\s+in\s+\w+\s*%\}.*?\{%\s*for',
            'nested_conditions': r'\{%\s*if.*?\{%\s*if',
            'heavy_filters': r'\|\s*(sort|reverse|group)',
        }
    
    def _load_validation_rules(self) -> List[ValidationRule]:
        """Load validation rules."""
        return [
            ValidationRule(
                name="variable_naming",
                description="Variables should use snake_case naming",
                severity="warning",
                pattern=r'^[a-z][a-z0-9_]*$'
            ),
            ValidationRule(
                name="no_empty_variables",
                description="Variables should not be empty",
                severity="error"
            ),
            ValidationRule(
                name="balanced_braces",
                description="Template braces should be balanced",
                severity="error"
            ),
            ValidationRule(
                name="no_undefined_filters",
                description="All filters should be defined",
                severity="error"
            ),
        ]    
    
def validate_template_comprehensive(
        self, 
        template_id: str,
        content: str, 
        variable_definitions: Optional[List[TemplateVariable]] = None
    ) -> TemplateAnalysis:
        """
        Perform comprehensive template validation and analysis.
        
        Args:
            template_id: Unique template identifier
            content: Template content to validate
            variable_definitions: Optional variable definitions
            
        Returns:
            TemplateAnalysis with comprehensive validation results
        """
        analysis = TemplateAnalysis(
            template_id=template_id,
            content=content
        )
        
        # Basic template validation
        analysis.validation_result = self.templating_engine.validate_template(
            content, variable_definitions
        )
        
        # Extract and analyze variables
        if variable_definitions:
            analysis.variables = variable_definitions
        else:
            # Auto-detect variables
            var_names = self.templating_engine.extract_variables(content)
            analysis.variables = [
                TemplateVariable(name=name, type='string', description=f"Auto-detected: {name}")
                for name in var_names
            ]
        
        # Security analysis
        analysis.security_issues = self._check_security_issues(content)
        
        # Performance analysis
        analysis.performance_warnings = self._check_performance_issues(content)
        
        # Best practices analysis
        analysis.best_practice_violations = self._check_best_practices(content, analysis.variables)
        
        # Calculate metrics
        analysis.complexity_score = self._calculate_complexity_score(content)
        analysis.readability_score = self._calculate_readability_score(content)
        
        return analysis
    
    def _check_security_issues(self, content: str) -> List[str]:
        """Check for potential security issues in template."""
        issues = []
        
        for issue_type, pattern in self.security_patterns.items():
            if re.search(pattern, content, re.IGNORECASE):
                issues.append(f"Potential {issue_type.replace('_', ' ')} detected")
        
        # Check for dangerous Jinja2 constructs
        if '{{' in content and '}}' in content:
            # Check for attribute access that might be dangerous
            if re.search(r'\{\{\s*\w+\.__', content):
                issues.append("Potentially unsafe attribute access detected")
            
            # Check for method calls
            if re.search(r'\{\{\s*\w+\.\w+\(', content):
                issues.append("Method calls in templates should be avoided")
        
        return issues
    
    def _check_performance_issues(self, content: str) -> List[str]:
        """Check for potential performance issues."""
        warnings = []
        
        for issue_type, pattern in self.performance_patterns.items():
            if re.search(pattern, content, re.DOTALL):
                warnings.append(f"Performance concern: {issue_type.replace('_', ' ')}")
        
        # Check template length
        if len(content) > 10000:
            warnings.append("Template is very large, consider breaking into smaller parts")
        
        # Check variable count
        var_count = len(self.templating_engine.extract_variables(content))
        if var_count > 20:
            warnings.append(f"High number of variables ({var_count}), consider simplification")
        
        return warnings
    
    def _check_best_practices(self, content: str, variables: List[TemplateVariable]) -> List[str]:
        """Check for best practice violations."""
        violations = []
        
        # Check variable naming
        for var in variables:
            if not re.match(r'^[a-z][a-z0-9_]*$', var.name):
                violations.append(f"Variable '{var.name}' should use snake_case naming")
        
        # Check for hardcoded values that should be variables
        if re.search(r'\b(https?://[^\s]+|[A-Z]{2,}|[0-9]{4,})\b', content):
            violations.append("Consider using variables for hardcoded values")
        
        # Check for missing descriptions
        undefined_vars = [var for var in variables if not var.description]
        if undefined_vars:
            violations.append(f"Variables missing descriptions: {[v.name for v in undefined_vars]}")
        
        # Check for unused complexity
        if '{%' in content and '%}' in content:
            # Simple check for potentially unnecessary logic
            logic_blocks = re.findall(r'\{%.*?%\}', content, re.DOTALL)
            if len(logic_blocks) > 5:
                violations.append("Template has complex logic, consider moving to code")
        
        return violations
    
    def _calculate_complexity_score(self, content: str) -> int:
        """Calculate template complexity score."""
        score = 0
        
        # Variable count
        score += len(self.templating_engine.extract_variables(content))
        
        # Control structures
        score += len(re.findall(r'\{%\s*(if|for|while|with)', content)) * 2
        
        # Filters
        score += len(re.findall(r'\|', content))
        
        # Nested structures
        score += len(re.findall(r'\{%.*?\{%', content, re.DOTALL)) * 3
        
        # Template length factor
        score += len(content) // 1000
        
        return score
    
    def _calculate_readability_score(self, content: str) -> float:
        """Calculate template readability score (0-100)."""
        score = 100.0
        
        # Penalize for length
        if len(content) > 1000:
            score -= min(30, (len(content) - 1000) / 100)
        
        # Penalize for complexity
        complexity = self._calculate_complexity_score(content)
        score -= min(40, complexity * 2)
        
        # Penalize for poor formatting
        lines = content.split('\n')
        avg_line_length = sum(len(line) for line in lines) / max(len(lines), 1)
        if avg_line_length > 100:
            score -= 10
        
        # Reward for comments and documentation
        comment_count = len(re.findall(r'\{#.*?#\}', content, re.DOTALL))
        score += min(10, comment_count * 2)
        
        return max(0.0, score)