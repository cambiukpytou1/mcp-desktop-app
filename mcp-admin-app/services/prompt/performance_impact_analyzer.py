"""
Performance Impact Analysis Service
===================================

Service for analyzing performance impact of prompt changes and providing
comprehensive reporting and recommendations.
"""

import logging
import json
import statistics
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

from ...models.prompt_advanced.models import PerformanceMetrics, EvaluationResult
from .performance_tracker import PerformanceTracker, PerformanceImpact, PerformanceTrend, MetricType, TrendDirection


class ImpactSeverity(Enum):
    """Severity levels for performance impact."""
    CRITICAL = "critical"      # >50% change
    HIGH = "high"             # 25-50% change
    MEDIUM = "medium"         # 10-25% change
    LOW = "low"              # 5-10% change
    MINIMAL = "minimal"       # <5% change


class RecommendationType(Enum):
    """Types of recommendations."""
    ROLLBACK = "rollback"
    OPTIMIZE = "optimize"
    MONITOR = "monitor"
    INVESTIGATE = "investigate"
    CONTINUE = "continue"


@dataclass
class ImpactAlert:
    """Alert for significant performance impact."""
    version_id: str
    severity: ImpactSeverity
    affected_metrics: List[str]
    impact_summary: str
    recommendation: RecommendationType
    details: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "version_id": self.version_id,
            "severity": self.severity.value,
            "affected_metrics": self.affected_metrics,
            "impact_summary": self.impact_summary,
            "recommendation": self.recommendation.value,
            "details": self.details,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class PerformanceRegression:
    """Detected performance regression."""
    from_version: str
    to_version: str
    regression_metrics: Dict[str, float]  # metric -> percentage change
    severity: ImpactSeverity
    root_cause_analysis: Dict[str, Any]
    mitigation_suggestions: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "from_version": self.from_version,
            "to_version": self.to_version,
            "regression_metrics": self.regression_metrics,
            "severity": self.severity.value,
            "root_cause_analysis": self.root_cause_analysis,
            "mitigation_suggestions": self.mitigation_suggestions
        }


@dataclass
class PerformanceImprovement:
    """Detected performance improvement."""
    from_version: str
    to_version: str
    improvement_metrics: Dict[str, float]  # metric -> percentage change
    impact_magnitude: float
    success_factors: List[str]
    replication_suggestions: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "from_version": self.from_version,
            "to_version": self.to_version,
            "improvement_metrics": self.improvement_metrics,
            "impact_magnitude": self.impact_magnitude,
            "success_factors": self.success_factors,
            "replication_suggestions": self.replication_suggestions
        }


class PerformanceImpactAnalyzer:
    """Service for analyzing performance impact and generating insights."""
    
    def __init__(self, config_manager, db_manager):
        self.logger = logging.getLogger(__name__)
        self.config_manager = config_manager
        self.db_manager = db_manager
        
        # Initialize performance tracker
        self.performance_tracker = PerformanceTracker(config_manager, db_manager)
        
        # Configuration thresholds
        self.regression_threshold = 0.1  # 10% degradation threshold
        self.improvement_threshold = 0.05  # 5% improvement threshold
        self.critical_threshold = 0.5  # 50% change threshold
        self.min_executions_for_analysis = 5
        
        self.logger.info("Performance impact analyzer initialized")
    
    def analyze_version_impact(self, version_id: str) -> Dict[str, Any]:
        """Comprehensive impact analysis for a version."""
        try:
            analysis = {
                "version_id": version_id,
                "timestamp": datetime.now().isoformat(),
                "impact_summary": {},
                "regressions": [],
                "improvements": [],
                "alerts": [],
                "recommendations": [],
                "trend_analysis": {}
            }
            
            # Get version information
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT parent_version, prompt_id, created_at, commit_message
                    FROM prompt_versions 
                    WHERE version_id = ?
                """, (version_id,))
                
                version_info = cursor.fetchone()
                if not version_info:
                    return {"error": "Version not found"}
                
                prompt_id = version_info["prompt_id"]
                parent_version = version_info["parent_version"]
                
                # Analyze impact compared to parent version
                if parent_version:
                    impact = self.performance_tracker.analyze_performance_impact(
                        parent_version, version_id
                    )
                    if impact:
                        analysis["impact_summary"] = impact.to_dict()
                        
                        # Detect regressions and improvements
                        regression = self._detect_regression(impact)
                        if regression:
                            analysis["regressions"].append(regression.to_dict())
                            
                            # Create alert for significant regressions
                            alert = self._create_impact_alert(version_id, regression)
                            if alert:
                                analysis["alerts"].append(alert.to_dict())
                        
                        improvement = self._detect_improvement(impact)
                        if improvement:
                            analysis["improvements"].append(improvement.to_dict())
                
                # Analyze trends for the prompt
                trend_analysis = self._analyze_prompt_trends(prompt_id)
                analysis["trend_analysis"] = trend_analysis
                
                # Generate recommendations
                analysis["recommendations"] = self._generate_impact_recommendations(analysis)
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Failed to analyze version impact: {e}")
            return {"error": str(e)}
    
    def detect_performance_anomalies(self, prompt_id: str, days: int = 7) -> List[Dict[str, Any]]:
        """Detect performance anomalies in recent versions."""
        try:
            anomalies = []
            
            # Get recent performance history
            history = self.performance_tracker.get_prompt_performance_history(prompt_id, limit=20)
            
            if len(history) < 3:
                return anomalies
            
            # Analyze each metric for anomalies
            metrics_to_check = ["average_score", "success_rate", "average_cost", "average_response_time"]
            
            for metric in metrics_to_check:
                metric_values = []
                for snapshot in history:
                    value = getattr(snapshot.metrics, metric, 0)
                    if value > 0:  # Only include valid values
                        metric_values.append((snapshot.timestamp, value, snapshot.version_id))
                
                if len(metric_values) < 3:
                    continue
                
                # Calculate statistical thresholds
                values = [v[1] for v in metric_values]
                mean_val = statistics.mean(values)
                std_dev = statistics.stdev(values) if len(values) > 1 else 0
                
                # Detect outliers (values beyond 2 standard deviations)
                threshold = 2 * std_dev
                
                for timestamp, value, version_id in metric_values:
                    if abs(value - mean_val) > threshold and std_dev > 0:
                        anomaly_type = "spike" if value > mean_val else "drop"
                        severity = self._calculate_anomaly_severity(abs(value - mean_val) / mean_val)
                        
                        anomalies.append({
                            "version_id": version_id,
                            "metric": metric,
                            "anomaly_type": anomaly_type,
                            "severity": severity.value,
                            "value": value,
                            "expected_range": (mean_val - threshold, mean_val + threshold),
                            "deviation_percent": ((value - mean_val) / mean_val) * 100,
                            "timestamp": timestamp.isoformat()
                        })
            
            return anomalies
            
        except Exception as e:
            self.logger.error(f"Failed to detect performance anomalies: {e}")
            return []
    
    def generate_performance_insights(self, prompt_id: str) -> Dict[str, Any]:
        """Generate comprehensive performance insights for a prompt."""
        try:
            insights = {
                "prompt_id": prompt_id,
                "timestamp": datetime.now().isoformat(),
                "performance_summary": {},
                "trend_insights": [],
                "optimization_opportunities": [],
                "risk_factors": [],
                "best_practices": []
            }
            
            # Get performance history
            history = self.performance_tracker.get_prompt_performance_history(prompt_id)
            
            if not history:
                return {"error": "No performance data available"}
            
            # Calculate performance summary
            latest_metrics = history[0].metrics if history else None
            if latest_metrics:
                insights["performance_summary"] = {
                    "current_metrics": latest_metrics.to_dict(),
                    "total_versions": len(history),
                    "versions_with_data": len([h for h in history if h.execution_count > 0])
                }
            
            # Analyze trends for each metric
            for metric_type in MetricType:
                trend = self.performance_tracker.get_performance_trend(prompt_id, metric_type)
                if trend:
                    trend_insight = {
                        "metric": metric_type.value,
                        "direction": trend.direction.value,
                        "strength": trend.trend_strength,
                        "confidence": "high" if abs(trend.regression_slope) > 0.1 else "medium"
                    }
                    
                    # Add interpretation
                    if trend.direction == TrendDirection.IMPROVING:
                        trend_insight["interpretation"] = f"{metric_type.value} is consistently improving"
                    elif trend.direction == TrendDirection.DECLINING:
                        trend_insight["interpretation"] = f"{metric_type.value} is declining - needs attention"
                    elif trend.direction == TrendDirection.VOLATILE:
                        trend_insight["interpretation"] = f"{metric_type.value} is highly variable - consider stabilization"
                    else:
                        trend_insight["interpretation"] = f"{metric_type.value} is stable"
                    
                    insights["trend_insights"].append(trend_insight)
            
            # Identify optimization opportunities
            insights["optimization_opportunities"] = self._identify_optimization_opportunities(history)
            
            # Identify risk factors
            insights["risk_factors"] = self._identify_risk_factors(history)
            
            # Generate best practices
            insights["best_practices"] = self._generate_best_practices(history)
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Failed to generate performance insights: {e}")
            return {"error": str(e)}
    
    def compare_prompt_performance(self, prompt_ids: List[str]) -> Dict[str, Any]:
        """Compare performance across multiple prompts."""
        try:
            comparison = {
                "prompt_ids": prompt_ids,
                "timestamp": datetime.now().isoformat(),
                "performance_comparison": {},
                "rankings": {},
                "insights": []
            }
            
            prompt_metrics = {}
            
            # Get latest performance for each prompt
            for prompt_id in prompt_ids:
                history = self.performance_tracker.get_prompt_performance_history(prompt_id, limit=1)
                if history and history[0].execution_count > 0:
                    prompt_metrics[prompt_id] = history[0].metrics
            
            if len(prompt_metrics) < 2:
                return {"error": "Need at least 2 prompts with performance data"}
            
            # Compare metrics
            metrics_to_compare = ["average_score", "success_rate", "average_cost", "average_response_time"]
            
            for metric in metrics_to_compare:
                metric_values = {}
                for prompt_id, metrics in prompt_metrics.items():
                    value = getattr(metrics, metric, 0)
                    metric_values[prompt_id] = value
                
                # Rank prompts for this metric
                if metric in ["average_score", "success_rate"]:
                    # Higher is better
                    ranked = sorted(metric_values.items(), key=lambda x: x[1], reverse=True)
                else:
                    # Lower is better
                    ranked = sorted(metric_values.items(), key=lambda x: x[1])
                
                comparison["rankings"][metric] = [{"prompt_id": pid, "value": val} for pid, val in ranked]
            
            # Generate comparative insights
            comparison["insights"] = self._generate_comparative_insights(prompt_metrics)
            
            return comparison
            
        except Exception as e:
            self.logger.error(f"Failed to compare prompt performance: {e}")
            return {"error": str(e)}
    
    def _detect_regression(self, impact: PerformanceImpact) -> Optional[PerformanceRegression]:
        """Detect performance regression from impact analysis."""
        regression_metrics = {}
        
        for metric, changes in impact.metric_changes.items():
            change_percent = changes["change_percent"]
            
            # Check for regression (negative change in positive metrics, positive change in negative metrics)
            is_regression = False
            if metric in ["average_score", "success_rate"] and change_percent < -self.regression_threshold * 100:
                is_regression = True
            elif metric in ["average_cost", "average_response_time", "average_tokens"] and change_percent > self.regression_threshold * 100:
                is_regression = True
            
            if is_regression:
                regression_metrics[metric] = change_percent
        
        if not regression_metrics:
            return None
        
        # Determine severity
        max_regression = max(abs(change) for change in regression_metrics.values())
        severity = self._calculate_impact_severity(max_regression / 100)
        
        # Generate root cause analysis
        root_cause = self._analyze_regression_root_cause(impact, regression_metrics)
        
        # Generate mitigation suggestions
        mitigation = self._generate_mitigation_suggestions(regression_metrics)
        
        return PerformanceRegression(
            from_version=impact.from_version,
            to_version=impact.to_version,
            regression_metrics=regression_metrics,
            severity=severity,
            root_cause_analysis=root_cause,
            mitigation_suggestions=mitigation
        )
    
    def _detect_improvement(self, impact: PerformanceImpact) -> Optional[PerformanceImprovement]:
        """Detect performance improvement from impact analysis."""
        improvement_metrics = {}
        
        for metric, changes in impact.metric_changes.items():
            change_percent = changes["change_percent"]
            
            # Check for improvement (positive change in positive metrics, negative change in negative metrics)
            is_improvement = False
            if metric in ["average_score", "success_rate"] and change_percent > self.improvement_threshold * 100:
                is_improvement = True
            elif metric in ["average_cost", "average_response_time", "average_tokens"] and change_percent < -self.improvement_threshold * 100:
                is_improvement = True
            
            if is_improvement:
                improvement_metrics[metric] = change_percent
        
        if not improvement_metrics:
            return None
        
        # Calculate impact magnitude
        impact_magnitude = sum(abs(change) for change in improvement_metrics.values()) / len(improvement_metrics)
        
        # Analyze success factors
        success_factors = self._analyze_improvement_factors(impact, improvement_metrics)
        
        # Generate replication suggestions
        replication = self._generate_replication_suggestions(improvement_metrics)
        
        return PerformanceImprovement(
            from_version=impact.from_version,
            to_version=impact.to_version,
            improvement_metrics=improvement_metrics,
            impact_magnitude=impact_magnitude,
            success_factors=success_factors,
            replication_suggestions=replication
        )
    
    def _create_impact_alert(self, version_id: str, regression: PerformanceRegression) -> Optional[ImpactAlert]:
        """Create alert for significant performance impact."""
        if regression.severity in [ImpactSeverity.CRITICAL, ImpactSeverity.HIGH]:
            affected_metrics = list(regression.regression_metrics.keys())
            
            # Generate impact summary
            max_regression = max(abs(change) for change in regression.regression_metrics.values())
            impact_summary = f"Performance regression detected: {max_regression:.1f}% degradation in {', '.join(affected_metrics)}"
            
            # Determine recommendation
            recommendation = RecommendationType.ROLLBACK if regression.severity == ImpactSeverity.CRITICAL else RecommendationType.INVESTIGATE
            
            return ImpactAlert(
                version_id=version_id,
                severity=regression.severity,
                affected_metrics=affected_metrics,
                impact_summary=impact_summary,
                recommendation=recommendation,
                details=regression.to_dict()
            )
        
        return None
    
    def _calculate_impact_severity(self, change_ratio: float) -> ImpactSeverity:
        """Calculate severity based on change ratio."""
        if change_ratio >= 0.5:
            return ImpactSeverity.CRITICAL
        elif change_ratio >= 0.25:
            return ImpactSeverity.HIGH
        elif change_ratio >= 0.1:
            return ImpactSeverity.MEDIUM
        elif change_ratio >= 0.05:
            return ImpactSeverity.LOW
        else:
            return ImpactSeverity.MINIMAL
    
    def _calculate_anomaly_severity(self, deviation_ratio: float) -> ImpactSeverity:
        """Calculate anomaly severity based on deviation ratio."""
        return self._calculate_impact_severity(deviation_ratio)
    
    def _analyze_prompt_trends(self, prompt_id: str) -> Dict[str, Any]:
        """Analyze trends for all metrics of a prompt."""
        trends = {}
        
        for metric_type in MetricType:
            trend = self.performance_tracker.get_performance_trend(prompt_id, metric_type)
            if trend:
                trends[metric_type.value] = trend.to_dict()
        
        return trends
    
    def _generate_impact_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on impact analysis."""
        recommendations = []
        
        # Check for critical regressions
        for regression in analysis.get("regressions", []):
            if regression.get("severity") == "critical":
                recommendations.append("URGENT: Critical performance regression detected - consider immediate rollback")
            elif regression.get("severity") == "high":
                recommendations.append("High impact regression detected - investigate and consider rollback")
        
        # Check for improvements
        for improvement in analysis.get("improvements", []):
            recommendations.append("Performance improvement detected - document changes for future reference")
        
        # Check trends
        trend_analysis = analysis.get("trend_analysis", {})
        declining_trends = [metric for metric, trend in trend_analysis.items() 
                          if trend.get("direction") == "declining"]
        
        if declining_trends:
            recommendations.append(f"Declining trends detected in: {', '.join(declining_trends)} - monitor closely")
        
        if not recommendations:
            recommendations.append("Performance impact within acceptable ranges - continue monitoring")
        
        return recommendations
    
    def _identify_optimization_opportunities(self, history: List) -> List[str]:
        """Identify optimization opportunities from performance history."""
        opportunities = []
        
        if not history:
            return opportunities
        
        latest = history[0].metrics
        
        # Check for optimization opportunities
        if latest.average_score < 0.8:
            opportunities.append("Quality optimization: Average score below 80% - review prompt effectiveness")
        
        if latest.success_rate < 0.95:
            opportunities.append("Reliability optimization: Success rate below 95% - improve error handling")
        
        if latest.average_cost > 0.05:  # Arbitrary threshold
            opportunities.append("Cost optimization: High average cost - consider prompt length or model optimization")
        
        if latest.average_response_time > 5.0:  # 5 seconds threshold
            opportunities.append("Speed optimization: Slow response times - optimize prompt complexity")
        
        return opportunities
    
    def _identify_risk_factors(self, history: List) -> List[str]:
        """Identify risk factors from performance history."""
        risks = []
        
        if len(history) < 3:
            risks.append("Limited performance data - increase testing frequency for better insights")
            return risks
        
        # Check for volatility
        scores = [h.metrics.average_score for h in history[:5] if h.execution_count > 0]
        if len(scores) > 2:
            score_std = statistics.stdev(scores)
            score_mean = statistics.mean(scores)
            if score_std / score_mean > 0.2:  # High coefficient of variation
                risks.append("High performance volatility - results are inconsistent")
        
        # Check for declining trends
        recent_scores = [h.metrics.average_score for h in history[:3] if h.execution_count > 0]
        if len(recent_scores) >= 3 and all(recent_scores[i] > recent_scores[i+1] for i in range(len(recent_scores)-1)):
            risks.append("Declining performance trend - recent versions performing worse")
        
        return risks
    
    def _generate_best_practices(self, history: List) -> List[str]:
        """Generate best practices based on performance history."""
        practices = []
        
        if not history:
            return practices
        
        # Analyze what works well
        high_performing = [h for h in history if h.metrics.average_score > 0.8 and h.execution_count >= 3]
        
        if high_performing:
            practices.append("Continue testing with sufficient sample sizes (3+ executions) for reliable metrics")
            practices.append("Monitor performance trends after each change to catch regressions early")
        
        practices.append("Establish performance baselines before making significant changes")
        practices.append("Use A/B testing to validate improvements before full deployment")
        
        return practices
    
    def _analyze_regression_root_cause(self, impact: PerformanceImpact, regression_metrics: Dict[str, float]) -> Dict[str, Any]:
        """Analyze potential root causes of regression."""
        return {
            "affected_metrics": list(regression_metrics.keys()),
            "severity_assessment": "high" if max(abs(v) for v in regression_metrics.values()) > 25 else "medium",
            "potential_causes": [
                "Prompt content changes affecting model performance",
                "Parameter adjustments (temperature, max_tokens) impacting output quality",
                "Model version changes or API updates",
                "Test data or evaluation criteria changes"
            ]
        }
    
    def _generate_mitigation_suggestions(self, regression_metrics: Dict[str, float]) -> List[str]:
        """Generate mitigation suggestions for regressions."""
        suggestions = []
        
        if "average_score" in regression_metrics:
            suggestions.append("Review prompt content changes and consider reverting problematic modifications")
        
        if "success_rate" in regression_metrics:
            suggestions.append("Investigate error patterns and improve prompt reliability")
        
        if "average_cost" in regression_metrics:
            suggestions.append("Optimize prompt length or consider alternative model configurations")
        
        suggestions.append("Compare with previous high-performing versions to identify successful patterns")
        suggestions.append("Consider gradual rollback or A/B testing to validate fixes")
        
        return suggestions
    
    def _analyze_improvement_factors(self, impact: PerformanceImpact, improvement_metrics: Dict[str, float]) -> List[str]:
        """Analyze factors contributing to performance improvement."""
        factors = []
        
        if "average_score" in improvement_metrics:
            factors.append("Prompt content optimization improved output quality")
        
        if "success_rate" in improvement_metrics:
            factors.append("Enhanced error handling or prompt reliability")
        
        if "average_cost" in improvement_metrics:
            factors.append("More efficient prompt structure or parameter tuning")
        
        factors.append("Systematic testing and iteration approach")
        
        return factors
    
    def _generate_replication_suggestions(self, improvement_metrics: Dict[str, float]) -> List[str]:
        """Generate suggestions for replicating improvements."""
        suggestions = []
        
        suggestions.append("Document the specific changes that led to improvement")
        suggestions.append("Apply similar optimization patterns to other prompts")
        suggestions.append("Establish this version as a performance baseline")
        suggestions.append("Share successful techniques with the team")
        
        return suggestions
    
    def _generate_comparative_insights(self, prompt_metrics: Dict[str, Any]) -> List[str]:
        """Generate insights from comparing multiple prompts."""
        insights = []
        
        if len(prompt_metrics) < 2:
            return insights
        
        # Find best and worst performers
        scores = {pid: metrics.average_score for pid, metrics in prompt_metrics.items()}
        best_prompt = max(scores, key=scores.get)
        worst_prompt = min(scores, key=scores.get)
        
        score_diff = scores[best_prompt] - scores[worst_prompt]
        
        if score_diff > 0.2:  # 20% difference
            insights.append(f"Significant quality gap: {best_prompt} outperforms {worst_prompt} by {score_diff:.1%}")
            insights.append("Consider analyzing high-performing prompt patterns for optimization opportunities")
        
        # Check cost efficiency
        costs = {pid: metrics.average_cost for pid, metrics in prompt_metrics.items()}
        most_efficient = min(costs, key=costs.get)
        least_efficient = max(costs, key=costs.get)
        
        cost_ratio = costs[least_efficient] / costs[most_efficient] if costs[most_efficient] > 0 else 1
        
        if cost_ratio > 2:  # 2x cost difference
            insights.append(f"Cost efficiency opportunity: {most_efficient} is {cost_ratio:.1f}x more cost-effective than {least_efficient}")
        
        return insights