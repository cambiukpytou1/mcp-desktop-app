"""
Prompt Performance Tracking Service
===================================

Service for tracking and analyzing prompt performance across versions with
comprehensive metrics and impact analysis.
"""

import logging
import json
import statistics
import sqlite3
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

from models.prompt_advanced.models import (
    PerformanceMetrics, EvaluationResult, TokenUsage
)


class MetricType(Enum):
    """Types of performance metrics."""
    QUALITY_SCORE = "quality_score"
    SUCCESS_RATE = "success_rate"
    TOKEN_USAGE = "token_usage"
    COST = "cost"
    RESPONSE_TIME = "response_time"
    ERROR_RATE = "error_rate"


class TrendDirection(Enum):
    """Direction of performance trends."""
    IMPROVING = "improving"
    DECLINING = "declining"
    STABLE = "stable"
    VOLATILE = "volatile"


@dataclass
class PerformanceSnapshot:
    """Snapshot of performance metrics at a specific point in time."""
    version_id: str
    timestamp: datetime
    metrics: PerformanceMetrics
    execution_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "version_id": self.version_id,
            "timestamp": self.timestamp.isoformat(),
            "metrics": self.metrics.to_dict(),
            "execution_count": self.execution_count
        }


@dataclass
class PerformanceImpact:
    """Analysis of performance impact between versions."""
    from_version: str
    to_version: str
    metric_changes: Dict[str, Dict[str, float]]  # metric_name -> {old_value, new_value, change_percent}
    overall_impact: str  # "positive", "negative", "neutral"
    significance_score: float  # 0.0 to 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "from_version": self.from_version,
            "to_version": self.to_version,
            "metric_changes": self.metric_changes,
            "overall_impact": self.overall_impact,
            "significance_score": self.significance_score
        }


@dataclass
class PerformanceTrend:
    """Performance trend analysis over time."""
    metric_type: MetricType
    direction: TrendDirection
    trend_strength: float  # 0.0 to 1.0
    data_points: List[Tuple[datetime, float]]
    regression_slope: float
    confidence_interval: Tuple[float, float]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "metric_type": self.metric_type.value,
            "direction": self.direction.value,
            "trend_strength": self.trend_strength,
            "data_points": [(dt.isoformat(), val) for dt, val in self.data_points],
            "regression_slope": self.regression_slope,
            "confidence_interval": list(self.confidence_interval)
        }


class PerformanceTracker:
    """Service for tracking and analyzing prompt performance across versions."""
    
    def __init__(self, config_manager, db_manager):
        self.logger = logging.getLogger(__name__)
        self.config_manager = config_manager
        self.db_manager = db_manager
        
        # Performance tracking configuration
        self.min_executions_for_analysis = 5
        self.significance_threshold = 0.1  # 10% change threshold
        self.trend_analysis_window_days = 30
        
        self.logger.info("Performance tracker initialized")
    
    def record_execution_metrics(self, version_id: str, result: EvaluationResult) -> bool:
        """Record performance metrics for a version execution."""
        try:
            with self.db_manager.get_connection() as conn:
                # Insert execution record
                conn.execute("""
                    INSERT INTO prompt_executions 
                    (id, prompt_id, version_id, model, input_variables, output, success,
                     error, tokens_used, cost, execution_time, quality_score, executed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    result.result_id,
                    result.prompt_version_id.split('-')[0],  # Extract prompt_id from version_id
                    version_id,
                    result.model,
                    json.dumps(result.input_variables),
                    result.output,
                    result.error is None,
                    result.error,
                    result.token_usage.total_tokens if result.token_usage else 0,
                    result.cost,
                    result.execution_time,
                    result.scores.get('overall', 0.0) if result.scores else None,
                    result.created_at
                ))
                
                # Update aggregated performance metrics
                self._update_version_performance_metrics(conn, version_id)
                
                conn.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to record execution metrics for version {version_id}: {e}")
            return False
    
    def get_version_performance(self, version_id: str) -> Optional[PerformanceMetrics]:
        """Get performance metrics for a specific version."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT average_score, total_executions, success_rate,
                           average_tokens, average_cost, average_response_time
                    FROM prompt_performance_metrics 
                    WHERE version_id = ?
                """, (version_id,))
                
                row = cursor.fetchone()
                if row:
                    return PerformanceMetrics(
                        average_score=row["average_score"],
                        total_executions=row["total_executions"],
                        success_rate=row["success_rate"],
                        average_tokens=row["average_tokens"],
                        average_cost=row["average_cost"],
                        average_response_time=row["average_response_time"]
                    )
                
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get performance for version {version_id}: {e}")
            return None
    
    def analyze_performance_impact(self, from_version: str, to_version: str) -> Optional[PerformanceImpact]:
        """Analyze performance impact between two versions."""
        try:
            from_metrics = self.get_version_performance(from_version)
            to_metrics = self.get_version_performance(to_version)
            
            if not from_metrics or not to_metrics:
                return None
            
            # Calculate metric changes
            metric_changes = {}
            metrics_to_compare = [
                ("average_score", from_metrics.average_score, to_metrics.average_score),
                ("success_rate", from_metrics.success_rate, to_metrics.success_rate),
                ("average_tokens", from_metrics.average_tokens, to_metrics.average_tokens),
                ("average_cost", from_metrics.average_cost, to_metrics.average_cost),
                ("average_response_time", from_metrics.average_response_time, to_metrics.average_response_time)
            ]
            
            total_impact_score = 0.0
            significant_changes = 0
            
            for metric_name, old_val, new_val in metrics_to_compare:
                if old_val > 0:  # Avoid division by zero
                    change_percent = ((new_val - old_val) / old_val) * 100
                    metric_changes[metric_name] = {
                        "old_value": old_val,
                        "new_value": new_val,
                        "change_percent": change_percent
                    }
                    
                    # Weight different metrics for overall impact
                    weight = self._get_metric_weight(metric_name)
                    if abs(change_percent) > self.significance_threshold * 100:
                        significant_changes += 1
                        total_impact_score += change_percent * weight
            
            # Determine overall impact
            overall_impact = "neutral"
            if total_impact_score > 5:  # 5% weighted improvement
                overall_impact = "positive"
            elif total_impact_score < -5:  # 5% weighted degradation
                overall_impact = "negative"
            
            # Calculate significance score
            significance_score = min(1.0, significant_changes / len(metrics_to_compare))
            
            return PerformanceImpact(
                from_version=from_version,
                to_version=to_version,
                metric_changes=metric_changes,
                overall_impact=overall_impact,
                significance_score=significance_score
            )
            
        except Exception as e:
            self.logger.error(f"Failed to analyze performance impact: {e}")
            return None
    
    def get_performance_trend(self, prompt_id: str, metric_type: MetricType, 
                            days: int = None) -> Optional[PerformanceTrend]:
        """Get performance trend for a prompt over time."""
        try:
            if days is None:
                days = self.trend_analysis_window_days
            
            start_date = datetime.now() - timedelta(days=days)
            
            with self.db_manager.get_connection() as conn:
                # Get metric values over time
                metric_column = self._get_metric_column(metric_type)
                cursor = conn.execute(f"""
                    SELECT pv.created_at, ppm.{metric_column}
                    FROM prompt_versions pv
                    JOIN prompt_performance_metrics ppm ON pv.version_id = ppm.version_id
                    WHERE pv.prompt_id = ? AND pv.created_at >= ?
                    ORDER BY pv.created_at
                """, (prompt_id, start_date))
                
                data_points = []
                for row in cursor.fetchall():
                    timestamp = datetime.fromisoformat(row["created_at"])
                    value = row[metric_column]
                    if value is not None:
                        data_points.append((timestamp, float(value)))
                
                if len(data_points) < 2:
                    return None
                
                # Calculate trend
                trend_analysis = self._calculate_trend(data_points)
                
                return PerformanceTrend(
                    metric_type=metric_type,
                    direction=trend_analysis["direction"],
                    trend_strength=trend_analysis["strength"],
                    data_points=data_points,
                    regression_slope=trend_analysis["slope"],
                    confidence_interval=trend_analysis["confidence_interval"]
                )
                
        except Exception as e:
            self.logger.error(f"Failed to get performance trend: {e}")
            return None
    
    def get_version_performance_report(self, version_id: str) -> Dict[str, Any]:
        """Generate comprehensive performance report for a version."""
        try:
            report = {
                "version_id": version_id,
                "timestamp": datetime.now().isoformat(),
                "metrics": None,
                "comparisons": [],
                "trends": [],
                "recommendations": []
            }
            
            # Get current metrics
            metrics = self.get_version_performance(version_id)
            if metrics:
                report["metrics"] = metrics.to_dict()
            
            # Get parent version for comparison
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT parent_version, prompt_id FROM prompt_versions 
                    WHERE version_id = ?
                """, (version_id,))
                version_info = cursor.fetchone()
                
                if version_info and version_info["parent_version"]:
                    # Compare with parent version
                    impact = self.analyze_performance_impact(
                        version_info["parent_version"], version_id
                    )
                    if impact:
                        report["comparisons"].append({
                            "type": "parent_version",
                            "comparison": impact.to_dict()
                        })
                
                # Get trends for the prompt
                if version_info:
                    prompt_id = version_info["prompt_id"]
                    for metric_type in MetricType:
                        trend = self.get_performance_trend(prompt_id, metric_type)
                        if trend:
                            report["trends"].append(trend.to_dict())
            
            # Generate recommendations
            report["recommendations"] = self._generate_recommendations(report)
            
            return report
            
        except Exception as e:
            self.logger.error(f"Failed to generate performance report: {e}")
            return {"error": str(e)}
    
    def get_prompt_performance_history(self, prompt_id: str, limit: int = 50) -> List[PerformanceSnapshot]:
        """Get performance history for a prompt across all versions."""
        try:
            snapshots = []
            
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT pv.version_id, pv.created_at, 
                           ppm.average_score, ppm.total_executions, ppm.success_rate,
                           ppm.average_tokens, ppm.average_cost, ppm.average_response_time
                    FROM prompt_versions pv
                    LEFT JOIN prompt_performance_metrics ppm ON pv.version_id = ppm.version_id
                    WHERE pv.prompt_id = ?
                    ORDER BY pv.created_at DESC
                    LIMIT ?
                """, (prompt_id, limit))
                
                for row in cursor.fetchall():
                    metrics = PerformanceMetrics(
                        average_score=row["average_score"] or 0.0,
                        total_executions=row["total_executions"] or 0,
                        success_rate=row["success_rate"] or 0.0,
                        average_tokens=row["average_tokens"] or 0,
                        average_cost=row["average_cost"] or 0.0,
                        average_response_time=row["average_response_time"] or 0.0
                    )
                    
                    snapshot = PerformanceSnapshot(
                        version_id=row["version_id"],
                        timestamp=datetime.fromisoformat(row["created_at"]),
                        metrics=metrics,
                        execution_count=row["total_executions"] or 0
                    )
                    snapshots.append(snapshot)
            
            return snapshots
            
        except Exception as e:
            self.logger.error(f"Failed to get performance history: {e}")
            return []
    
    def _update_version_performance_metrics(self, conn: sqlite3.Connection, version_id: str):
        """Update aggregated performance metrics for a version."""
        # Calculate aggregated metrics from executions
        cursor = conn.execute("""
            SELECT 
                COUNT(*) as total_executions,
                AVG(CASE WHEN success = 1 THEN 1.0 ELSE 0.0 END) as success_rate,
                AVG(quality_score) as average_score,
                AVG(tokens_used) as average_tokens,
                AVG(cost) as average_cost,
                AVG(execution_time) as average_response_time
            FROM prompt_executions 
            WHERE version_id = ? AND quality_score IS NOT NULL
        """, (version_id,))
        
        stats = cursor.fetchone()
        if stats and stats["total_executions"] > 0:
            conn.execute("""
                INSERT OR REPLACE INTO prompt_performance_metrics 
                (version_id, average_score, total_executions, success_rate,
                 average_tokens, average_cost, average_response_time, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                version_id,
                stats["average_score"] or 0.0,
                stats["total_executions"],
                stats["success_rate"] or 0.0,
                int(stats["average_tokens"] or 0),
                stats["average_cost"] or 0.0,
                stats["average_response_time"] or 0.0,
                datetime.now()
            ))
    
    def _get_metric_weight(self, metric_name: str) -> float:
        """Get weight for metric in overall impact calculation."""
        weights = {
            "average_score": 0.4,      # Quality is most important
            "success_rate": 0.3,       # Reliability is critical
            "average_cost": 0.2,       # Cost efficiency matters
            "average_response_time": 0.1,  # Speed is less critical
            "average_tokens": 0.05     # Token usage is least critical
        }
        return weights.get(metric_name, 0.1)
    
    def _get_metric_column(self, metric_type: MetricType) -> str:
        """Get database column name for metric type."""
        column_mapping = {
            MetricType.QUALITY_SCORE: "average_score",
            MetricType.SUCCESS_RATE: "success_rate",
            MetricType.TOKEN_USAGE: "average_tokens",
            MetricType.COST: "average_cost",
            MetricType.RESPONSE_TIME: "average_response_time"
        }
        return column_mapping.get(metric_type, "average_score")
    
    def _calculate_trend(self, data_points: List[Tuple[datetime, float]]) -> Dict[str, Any]:
        """Calculate trend analysis for data points."""
        if len(data_points) < 2:
            return {
                "direction": TrendDirection.STABLE,
                "strength": 0.0,
                "slope": 0.0,
                "confidence_interval": (0.0, 0.0)
            }
        
        # Convert timestamps to numeric values (days since first point)
        start_time = data_points[0][0]
        x_values = [(point[0] - start_time).days for point in data_points]
        y_values = [point[1] for point in data_points]
        
        # Simple linear regression
        n = len(data_points)
        x_mean = statistics.mean(x_values)
        y_mean = statistics.mean(y_values)
        
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values))
        denominator = sum((x - x_mean) ** 2 for x in x_values)
        
        if denominator == 0:
            slope = 0.0
        else:
            slope = numerator / denominator
        
        # Determine trend direction and strength
        if abs(slope) < 0.01:  # Very small slope
            direction = TrendDirection.STABLE
            strength = 0.0
        elif slope > 0:
            direction = TrendDirection.IMPROVING
            strength = min(1.0, abs(slope) * 10)  # Scale slope to 0-1 range
        else:
            direction = TrendDirection.DECLINING
            strength = min(1.0, abs(slope) * 10)
        
        # Simple confidence interval (±2 standard errors)
        if n > 2:
            y_pred = [y_mean + slope * (x - x_mean) for x in x_values]
            residuals = [y - y_pred[i] for i, y in enumerate(y_values)]
            std_error = statistics.stdev(residuals) if len(residuals) > 1 else 0.0
            confidence_interval = (slope - 2 * std_error, slope + 2 * std_error)
        else:
            confidence_interval = (slope, slope)
        
        # Check for volatility
        if len(y_values) > 3:
            volatility = statistics.stdev(y_values) / y_mean if y_mean != 0 else 0
            if volatility > 0.3:  # High volatility threshold
                direction = TrendDirection.VOLATILE
        
        return {
            "direction": direction,
            "strength": strength,
            "slope": slope,
            "confidence_interval": confidence_interval
        }
    
    def _generate_recommendations(self, report: Dict[str, Any]) -> List[str]:
        """Generate performance recommendations based on report data."""
        recommendations = []
        
        if not report.get("metrics"):
            return ["Insufficient data for recommendations. Execute more tests to gather performance metrics."]
        
        metrics = report["metrics"]
        
        # Quality recommendations
        if metrics["average_score"] < 0.7:
            recommendations.append("Consider improving prompt quality - average score is below 70%")
        
        # Success rate recommendations
        if metrics["success_rate"] < 0.9:
            recommendations.append("Success rate is below 90% - review error patterns and improve prompt reliability")
        
        # Cost recommendations
        if metrics["average_cost"] > 0.1:  # Arbitrary threshold
            recommendations.append("High average cost detected - consider optimizing prompt length or model selection")
        
        # Token usage recommendations
        if metrics["average_tokens"] > 2000:
            recommendations.append("High token usage - consider breaking down complex prompts or using more efficient phrasing")
        
        # Comparison-based recommendations
        for comparison in report.get("comparisons", []):
            comp_data = comparison.get("comparison", {})
            if comp_data.get("overall_impact") == "negative":
                recommendations.append("Performance regression detected compared to previous version - consider reverting changes")
            elif comp_data.get("overall_impact") == "positive":
                recommendations.append("Performance improvement detected - consider applying similar changes to other prompts")
        
        # Trend-based recommendations
        for trend in report.get("trends", []):
            if trend.get("direction") == "declining" and trend.get("trend_strength", 0) > 0.5:
                metric_type = trend.get("metric_type", "")
                recommendations.append(f"Declining trend detected in {metric_type} - investigate recent changes")
        
        if not recommendations:
            recommendations.append("Performance metrics look good - continue monitoring for any changes")
        
        return recommendations