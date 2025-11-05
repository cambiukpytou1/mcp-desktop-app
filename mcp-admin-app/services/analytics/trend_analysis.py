"""
Trend Analysis and Monitoring Service
====================================

Provides historical performance tracking, model drift detection, and impact visualization.
"""

import logging
import statistics
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
import math


@dataclass
class TrendPoint:
    """A single point in a trend analysis."""
    timestamp: datetime
    value: float
    metadata: Dict[str, Any]


@dataclass
class TrendAnalysis:
    """Results of trend analysis."""
    trend_type: str  # 'improving', 'declining', 'stable', 'volatile'
    slope: float
    confidence: float
    r_squared: float
    data_points: List[TrendPoint]
    analysis_period: int  # days
    significance_level: float


@dataclass
class ModelDriftAlert:
    """Alert for detected model drift."""
    alert_id: str
    model_id: str
    prompt_id: str
    drift_type: str  # 'performance', 'output_quality', 'cost', 'response_time'
    severity: str  # 'low', 'medium', 'high', 'critical'
    current_value: float
    baseline_value: float
    drift_percentage: float
    detection_timestamp: datetime
    description: str
    recommended_actions: List[str]


@dataclass
class ImpactVisualization:
    """Data structure for impact visualization."""
    visualization_type: str  # 'line_chart', 'heatmap', 'scatter_plot', 'bar_chart'
    title: str
    x_axis_label: str
    y_axis_label: str
    data_series: List[Dict[str, Any]]
    annotations: List[Dict[str, Any]]
    metadata: Dict[str, Any]


class TrendAnalysisService:
    """Handles trend analysis and monitoring for prompt performance."""
    
    def __init__(self, config_manager, db_manager):
        self.logger = logging.getLogger(__name__)
        self.config_manager = config_manager
        self.db_manager = db_manager
        
        # Configuration parameters
        self.drift_detection_threshold = 0.15  # 15% change triggers alert
        self.trend_analysis_window = 30  # days
        self.minimum_data_points = 5
        self.confidence_threshold = 0.7
        
        # Drift detection baselines (updated periodically)
        self.baselines = {}
        
        self.logger.info("Trend analysis service initialized")
    
    def track_historical_performance(self, prompt_id: str, 
                                   time_window_days: int = 90) -> Dict[str, Any]:
        """
        Track historical performance metrics for a prompt.
        
        Args:
            prompt_id: ID of the prompt to track
            time_window_days: Number of days to analyze
            
        Returns:
            Dictionary containing historical performance data
        """
        try:
            # Get historical evaluation data
            historical_data = self._get_historical_evaluation_data(prompt_id, time_window_days)
            
            if len(historical_data) < self.minimum_data_points:
                self.logger.warning(f"Insufficient data for trend analysis: {len(historical_data)} points")
                return {
                    'prompt_id': prompt_id,
                    'status': 'insufficient_data',
                    'data_points': len(historical_data),
                    'minimum_required': self.minimum_data_points
                }
            
            # Analyze different performance metrics
            performance_trends = {}
            
            # Score trend analysis
            score_trend = self._analyze_metric_trend(
                historical_data, 'score', 'Performance Score'
            )
            performance_trends['score'] = score_trend
            
            # Cost trend analysis
            cost_trend = self._analyze_metric_trend(
                historical_data, 'cost', 'Cost per Execution'
            )
            performance_trends['cost'] = cost_trend
            
            # Response time trend analysis
            response_time_trend = self._analyze_metric_trend(
                historical_data, 'response_time', 'Response Time (ms)'
            )
            performance_trends['response_time'] = response_time_trend
            
            # Token usage trend analysis
            token_trend = self._analyze_metric_trend(
                historical_data, 'tokens', 'Token Usage'
            )
            performance_trends['tokens'] = token_trend
            
            # Generate summary insights
            summary = self._generate_trend_summary(performance_trends)
            
            result = {
                'prompt_id': prompt_id,
                'analysis_period_days': time_window_days,
                'data_points': len(historical_data),
                'trends': performance_trends,
                'summary': summary,
                'last_updated': datetime.now().isoformat()
            }
            
            # Store trend analysis results
            self._store_trend_analysis(prompt_id, result)
            
            self.logger.info(f"Historical performance tracking completed for prompt {prompt_id}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error tracking historical performance: {e}")
            raise
    
    def detect_model_drift(self, model_id: str, 
                          lookback_days: int = 7) -> List[ModelDriftAlert]:
        """
        Detect model drift by comparing recent performance to baseline.
        
        Args:
            model_id: ID of the model to monitor
            lookback_days: Number of days to look back for recent data
            
        Returns:
            List of drift alerts
        """
        try:
            alerts = []
            
            # Get baseline performance for the model
            baseline = self._get_model_baseline(model_id)
            if not baseline:
                self.logger.warning(f"No baseline found for model {model_id}")
                return alerts
            
            # Get recent performance data
            recent_data = self._get_recent_model_performance(model_id, lookback_days)
            if not recent_data:
                self.logger.warning(f"No recent data found for model {model_id}")
                return alerts
            
            # Check for drift in different metrics
            drift_checks = [
                ('performance', 'avg_score', 'Performance Score'),
                ('cost', 'avg_cost', 'Average Cost'),
                ('response_time', 'avg_response_time', 'Response Time'),
                ('quality', 'success_rate', 'Success Rate')
            ]
            
            for drift_type, metric_key, metric_name in drift_checks:
                alert = self._check_metric_drift(
                    model_id, drift_type, metric_key, metric_name,
                    baseline.get(metric_key, 0), recent_data.get(metric_key, 0)
                )
                if alert:
                    alerts.append(alert)
            
            # Store drift detection results
            self._store_drift_alerts(model_id, alerts)
            
            self.logger.info(f"Model drift detection completed for {model_id}: {len(alerts)} alerts")
            return alerts
            
        except Exception as e:
            self.logger.error(f"Error detecting model drift: {e}")
            raise
    
    def generate_impact_visualization(self, prompt_id: str, 
                                    visualization_type: str = 'line_chart') -> ImpactVisualization:
        """
        Generate impact visualization for prompt performance.
        
        Args:
            prompt_id: ID of the prompt to visualize
            visualization_type: Type of visualization to generate
            
        Returns:
            ImpactVisualization object with chart data
        """
        try:
            # Get historical data for visualization
            historical_data = self._get_historical_evaluation_data(prompt_id, 90)
            
            if not historical_data:
                raise ValueError(f"No data available for visualization of prompt {prompt_id}")
            
            if visualization_type == 'line_chart':
                return self._create_line_chart_visualization(prompt_id, historical_data)
            elif visualization_type == 'heatmap':
                return self._create_heatmap_visualization(prompt_id, historical_data)
            elif visualization_type == 'scatter_plot':
                return self._create_scatter_plot_visualization(prompt_id, historical_data)
            elif visualization_type == 'bar_chart':
                return self._create_bar_chart_visualization(prompt_id, historical_data)
            else:
                raise ValueError(f"Unsupported visualization type: {visualization_type}")
                
        except Exception as e:
            self.logger.error(f"Error generating impact visualization: {e}")
            raise
    
    def monitor_performance_alerts(self) -> List[Dict[str, Any]]:
        """
        Monitor for performance alerts across all prompts and models.
        
        Returns:
            List of active alerts
        """
        try:
            alerts = []
            
            # Get all active prompts
            prompt_ids = self._get_active_prompt_ids()
            
            # Check each prompt for performance issues
            for prompt_id in prompt_ids:
                prompt_alerts = self._check_prompt_performance_alerts(prompt_id)
                alerts.extend(prompt_alerts)
            
            # Get all active models
            model_ids = self._get_active_model_ids()
            
            # Check each model for drift
            for model_id in model_ids:
                drift_alerts = self.detect_model_drift(model_id)
                for drift_alert in drift_alerts:
                    alerts.append({
                        'type': 'model_drift',
                        'alert_id': drift_alert.alert_id,
                        'model_id': drift_alert.model_id,
                        'severity': drift_alert.severity,
                        'description': drift_alert.description,
                        'timestamp': drift_alert.detection_timestamp.isoformat()
                    })
            
            # Sort alerts by severity and timestamp
            severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
            alerts.sort(key=lambda x: (
                severity_order.get(x.get('severity', 'low'), 3),
                x.get('timestamp', '')
            ))
            
            self.logger.info(f"Performance monitoring completed: {len(alerts)} alerts")
            return alerts
            
        except Exception as e:
            self.logger.error(f"Error monitoring performance alerts: {e}")
            raise
    
    def _get_historical_evaluation_data(self, prompt_id: str, 
                                      days_back: int) -> List[Dict[str, Any]]:
        """Get historical evaluation data for a prompt."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT er.scores, er.cost, er.token_usage, er.execution_time, 
                           er.created_at, er.model, er.error
                    FROM evaluation_results er
                    JOIN evaluation_runs run ON er.run_id = run.run_id
                    JOIN prompt_versions pv ON run.prompt_version_id = pv.version_id
                    WHERE pv.prompt_id = ? AND er.created_at >= ?
                    ORDER BY er.created_at ASC
                """, (prompt_id, cutoff_date.isoformat()))
                
                data = []
                for row in cursor.fetchall():
                    # Parse JSON fields
                    scores = json.loads(row[0] or '{}')
                    token_usage = json.loads(row[2] or '{}')
                    
                    # Extract score (use overall score or first available score)
                    score = scores.get('overall', scores.get('score', 0.0))
                    if isinstance(score, str):
                        try:
                            score = float(score)
                        except:
                            score = 0.0
                    
                    # Extract token count
                    tokens = token_usage.get('total_tokens', token_usage.get('tokens', 0))
                    
                    # Determine success (no error and score > 0)
                    success = row[6] is None and score > 0
                    
                    data.append({
                        'score': score,
                        'cost': row[1] or 0.0,
                        'tokens': tokens,
                        'response_time': row[3] or 0.0,
                        'timestamp': datetime.fromisoformat(row[4]),
                        'model': row[5],
                        'success': success
                    })
                
                return data
                
        except Exception as e:
            self.logger.error(f"Error getting historical evaluation data: {e}")
            return []
    
    def _analyze_metric_trend(self, data: List[Dict[str, Any]], 
                            metric_key: str, metric_name: str) -> TrendAnalysis:
        """Analyze trend for a specific metric."""
        try:
            # Extract metric values and timestamps
            points = []
            for item in data:
                if metric_key in item and item[metric_key] is not None:
                    points.append(TrendPoint(
                        timestamp=item['timestamp'],
                        value=float(item[metric_key]),
                        metadata={'model': item.get('model', 'unknown')}
                    ))
            
            if len(points) < self.minimum_data_points:
                return TrendAnalysis(
                    trend_type='insufficient_data',
                    slope=0.0,
                    confidence=0.0,
                    r_squared=0.0,
                    data_points=points,
                    analysis_period=self.trend_analysis_window,
                    significance_level=0.0
                )
            
            # Perform linear regression
            x_values = [(p.timestamp - points[0].timestamp).total_seconds() / 86400 
                       for p in points]  # Convert to days
            y_values = [p.value for p in points]
            
            slope, r_squared = self._calculate_linear_regression(x_values, y_values)
            
            # Determine trend type
            trend_type = self._classify_trend(slope, r_squared)
            
            # Calculate confidence based on R-squared and data points
            confidence = min(r_squared * (len(points) / 10), 1.0)
            
            return TrendAnalysis(
                trend_type=trend_type,
                slope=slope,
                confidence=confidence,
                r_squared=r_squared,
                data_points=points,
                analysis_period=self.trend_analysis_window,
                significance_level=r_squared
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing metric trend: {e}")
            return TrendAnalysis(
                trend_type='error',
                slope=0.0,
                confidence=0.0,
                r_squared=0.0,
                data_points=[],
                analysis_period=0,
                significance_level=0.0
            )
    
    def _calculate_linear_regression(self, x_values: List[float], 
                                   y_values: List[float]) -> Tuple[float, float]:
        """Calculate linear regression slope and R-squared."""
        n = len(x_values)
        if n < 2:
            return 0.0, 0.0
        
        # Calculate means
        x_mean = statistics.mean(x_values)
        y_mean = statistics.mean(y_values)
        
        # Calculate slope
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values))
        denominator = sum((x - x_mean) ** 2 for x in x_values)
        
        if denominator == 0:
            return 0.0, 0.0
        
        slope = numerator / denominator
        
        # Calculate R-squared
        y_pred = [slope * (x - x_mean) + y_mean for x in x_values]
        ss_res = sum((y - y_p) ** 2 for y, y_p in zip(y_values, y_pred))
        ss_tot = sum((y - y_mean) ** 2 for y in y_values)
        
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
        
        return slope, max(0.0, r_squared)  # Ensure R-squared is non-negative
    
    def _classify_trend(self, slope: float, r_squared: float) -> str:
        """Classify trend based on slope and R-squared."""
        if r_squared < 0.3:
            return 'volatile'
        elif abs(slope) < 0.001:
            return 'stable'
        elif slope > 0:
            return 'improving'
        else:
            return 'declining'
    
    def _generate_trend_summary(self, trends: Dict[str, TrendAnalysis]) -> Dict[str, Any]:
        """Generate summary of trend analysis."""
        summary = {
            'overall_health': 'unknown',
            'key_insights': [],
            'recommendations': []
        }
        
        # Analyze overall health
        improving_count = sum(1 for t in trends.values() if t.trend_type == 'improving')
        declining_count = sum(1 for t in trends.values() if t.trend_type == 'declining')
        stable_count = sum(1 for t in trends.values() if t.trend_type == 'stable')
        
        total_trends = len(trends)
        if total_trends == 0:
            return summary
        
        if improving_count > declining_count:
            summary['overall_health'] = 'improving'
        elif declining_count > improving_count:
            summary['overall_health'] = 'declining'
        else:
            summary['overall_health'] = 'stable'
        
        # Generate insights
        for metric, trend in trends.items():
            if trend.confidence > self.confidence_threshold:
                if trend.trend_type == 'improving':
                    summary['key_insights'].append(f"{metric.title()} is improving with high confidence")
                elif trend.trend_type == 'declining':
                    summary['key_insights'].append(f"{metric.title()} is declining with high confidence")
                elif trend.trend_type == 'volatile':
                    summary['key_insights'].append(f"{metric.title()} shows high volatility")
        
        # Generate recommendations
        if declining_count > 0:
            summary['recommendations'].append("Review prompts with declining performance")
        if any(t.trend_type == 'volatile' for t in trends.values()):
            summary['recommendations'].append("Investigate causes of performance volatility")
        if stable_count == total_trends:
            summary['recommendations'].append("Consider optimization experiments to improve performance")
        
        return summary
    
    def _get_model_baseline(self, model_id: str) -> Optional[Dict[str, float]]:
        """Get baseline performance metrics for a model."""
        try:
            # Check if we have cached baseline
            if model_id in self.baselines:
                baseline = self.baselines[model_id]
                # Check if baseline is recent (within 30 days)
                if (datetime.now() - baseline['last_updated']).days < 30:
                    return baseline['metrics']
            
            # Calculate new baseline from historical data (30-60 days ago)
            start_date = datetime.now() - timedelta(days=60)
            end_date = datetime.now() - timedelta(days=30)
            
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT er.scores, er.cost, er.execution_time, er.error, COUNT(*) as sample_size
                    FROM evaluation_results er
                    JOIN evaluation_runs run ON er.run_id = run.run_id
                    WHERE er.model = ? AND er.created_at BETWEEN ? AND ?
                """, (model_id, start_date.isoformat(), end_date.isoformat()))
                
                results = cursor.fetchall()
                if len(results) >= self.minimum_data_points:
                    # Process results to calculate averages
                    scores = []
                    costs = []
                    response_times = []
                    success_count = 0
                    
                    for row in results:
                        scores_json = json.loads(row[0] or '{}')
                        score = scores_json.get('overall', scores_json.get('score', 0.0))
                        if isinstance(score, str):
                            try:
                                score = float(score)
                            except:
                                score = 0.0
                        scores.append(score)
                        costs.append(row[1] or 0.0)
                        response_times.append(row[2] or 0.0)
                        if row[3] is None and score > 0:  # No error and positive score
                            success_count += 1
                    
                    baseline_metrics = {
                        'avg_score': statistics.mean(scores) if scores else 0.0,
                        'avg_cost': statistics.mean(costs) if costs else 0.0,
                        'avg_response_time': statistics.mean(response_times) if response_times else 0.0,
                        'success_rate': success_count / len(results) if results else 0.0
                    }
                    
                    # Cache the baseline
                    self.baselines[model_id] = {
                        'metrics': baseline_metrics,
                        'last_updated': datetime.now()
                    }
                    
                    return baseline_metrics
                
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting model baseline: {e}")
            return None
    
    def _get_recent_model_performance(self, model_id: str, 
                                    days_back: int) -> Optional[Dict[str, float]]:
        """Get recent performance metrics for a model."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT er.scores, er.cost, er.execution_time, er.error
                    FROM evaluation_results er
                    JOIN evaluation_runs run ON er.run_id = run.run_id
                    WHERE er.model = ? AND er.created_at >= ?
                """, (model_id, cutoff_date.isoformat()))
                
                results = cursor.fetchall()
                if len(results) >= self.minimum_data_points:
                    # Process results to calculate averages
                    scores = []
                    costs = []
                    response_times = []
                    success_count = 0
                    
                    for row in results:
                        scores_json = json.loads(row[0] or '{}')
                        score = scores_json.get('overall', scores_json.get('score', 0.0))
                        if isinstance(score, str):
                            try:
                                score = float(score)
                            except:
                                score = 0.0
                        scores.append(score)
                        costs.append(row[1] or 0.0)
                        response_times.append(row[2] or 0.0)
                        if row[3] is None and score > 0:  # No error and positive score
                            success_count += 1
                    
                    return {
                        'avg_score': statistics.mean(scores) if scores else 0.0,
                        'avg_cost': statistics.mean(costs) if costs else 0.0,
                        'avg_response_time': statistics.mean(response_times) if response_times else 0.0,
                        'success_rate': success_count / len(results) if results else 0.0
                    }
                
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting recent model performance: {e}")
            return None
    
    def _check_metric_drift(self, model_id: str, drift_type: str, metric_key: str,
                          metric_name: str, baseline_value: float, 
                          current_value: float) -> Optional[ModelDriftAlert]:
        """Check if a metric has drifted beyond threshold."""
        try:
            if baseline_value == 0:
                return None
            
            # Calculate drift percentage
            drift_percentage = abs((current_value - baseline_value) / baseline_value)
            
            if drift_percentage < self.drift_detection_threshold:
                return None
            
            # Determine severity
            if drift_percentage >= 0.5:
                severity = 'critical'
            elif drift_percentage >= 0.3:
                severity = 'high'
            elif drift_percentage >= 0.2:
                severity = 'medium'
            else:
                severity = 'low'
            
            # Generate recommendations
            recommendations = self._generate_drift_recommendations(drift_type, drift_percentage)
            
            alert_id = f"{model_id}_{drift_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            return ModelDriftAlert(
                alert_id=alert_id,
                model_id=model_id,
                prompt_id='',  # Model-level drift, not prompt-specific
                drift_type=drift_type,
                severity=severity,
                current_value=current_value,
                baseline_value=baseline_value,
                drift_percentage=drift_percentage,
                detection_timestamp=datetime.now(),
                description=f"{metric_name} has drifted {drift_percentage:.1%} from baseline",
                recommended_actions=recommendations
            )
            
        except Exception as e:
            self.logger.error(f"Error checking metric drift: {e}")
            return None
    
    def _generate_drift_recommendations(self, drift_type: str, 
                                      drift_percentage: float) -> List[str]:
        """Generate recommendations based on drift type and severity."""
        recommendations = []
        
        if drift_type == 'performance':
            recommendations.extend([
                "Review recent prompt changes",
                "Check for model updates or changes",
                "Analyze input data quality",
                "Consider prompt optimization"
            ])
        elif drift_type == 'cost':
            recommendations.extend([
                "Review token usage patterns",
                "Check for prompt length increases",
                "Analyze model pricing changes",
                "Consider cost optimization strategies"
            ])
        elif drift_type == 'response_time':
            recommendations.extend([
                "Check model service status",
                "Review network connectivity",
                "Analyze request complexity",
                "Consider load balancing"
            ])
        elif drift_type == 'quality':
            recommendations.extend([
                "Review output quality metrics",
                "Check for model degradation",
                "Analyze input data changes",
                "Consider model retraining"
            ])
        
        if drift_percentage >= 0.3:
            recommendations.append("Consider immediate investigation due to high drift")
        
        return recommendations
    
    def _create_line_chart_visualization(self, prompt_id: str, 
                                       data: List[Dict[str, Any]]) -> ImpactVisualization:
        """Create line chart visualization for prompt performance."""
        # Group data by metric
        metrics = ['score', 'cost', 'response_time', 'tokens']
        data_series = []
        
        for metric in metrics:
            series_data = []
            for item in data:
                if metric in item and item[metric] is not None:
                    series_data.append({
                        'x': item['timestamp'].isoformat(),
                        'y': float(item[metric])
                    })
            
            if series_data:
                data_series.append({
                    'name': metric.replace('_', ' ').title(),
                    'data': series_data,
                    'type': 'line'
                })
        
        return ImpactVisualization(
            visualization_type='line_chart',
            title=f'Performance Trends - Prompt {prompt_id}',
            x_axis_label='Time',
            y_axis_label='Value',
            data_series=data_series,
            annotations=[],
            metadata={'prompt_id': prompt_id, 'data_points': len(data)}
        )
    
    def _create_heatmap_visualization(self, prompt_id: str, 
                                    data: List[Dict[str, Any]]) -> ImpactVisualization:
        """Create heatmap visualization for model performance comparison."""
        # Group data by model and time period
        model_performance = {}
        
        for item in data:
            model = item.get('model', 'unknown')
            date = item['timestamp'].date()
            
            if model not in model_performance:
                model_performance[model] = {}
            
            if date not in model_performance[model]:
                model_performance[model][date] = []
            
            if item.get('score') is not None:
                model_performance[model][date].append(item['score'])
        
        # Calculate average scores for heatmap
        heatmap_data = []
        for model, dates in model_performance.items():
            for date, scores in dates.items():
                avg_score = statistics.mean(scores) if scores else 0
                heatmap_data.append({
                    'x': date.isoformat(),
                    'y': model,
                    'value': avg_score
                })
        
        return ImpactVisualization(
            visualization_type='heatmap',
            title=f'Model Performance Heatmap - Prompt {prompt_id}',
            x_axis_label='Date',
            y_axis_label='Model',
            data_series=[{
                'name': 'Performance Score',
                'data': heatmap_data,
                'type': 'heatmap'
            }],
            annotations=[],
            metadata={'prompt_id': prompt_id}
        )
    
    def _create_scatter_plot_visualization(self, prompt_id: str, 
                                         data: List[Dict[str, Any]]) -> ImpactVisualization:
        """Create scatter plot visualization for cost vs performance."""
        scatter_data = []
        
        for item in data:
            if item.get('score') is not None and item.get('cost') is not None:
                scatter_data.append({
                    'x': float(item['cost']),
                    'y': float(item['score']),
                    'metadata': {
                        'timestamp': item['timestamp'].isoformat(),
                        'model': item.get('model', 'unknown')
                    }
                })
        
        return ImpactVisualization(
            visualization_type='scatter_plot',
            title=f'Cost vs Performance - Prompt {prompt_id}',
            x_axis_label='Cost',
            y_axis_label='Performance Score',
            data_series=[{
                'name': 'Executions',
                'data': scatter_data,
                'type': 'scatter'
            }],
            annotations=[],
            metadata={'prompt_id': prompt_id}
        )
    
    def _create_bar_chart_visualization(self, prompt_id: str, 
                                      data: List[Dict[str, Any]]) -> ImpactVisualization:
        """Create bar chart visualization for model comparison."""
        # Group by model and calculate averages
        model_stats = {}
        
        for item in data:
            model = item.get('model', 'unknown')
            if model not in model_stats:
                model_stats[model] = {'scores': [], 'costs': [], 'response_times': []}
            
            if item.get('score') is not None:
                model_stats[model]['scores'].append(item['score'])
            if item.get('cost') is not None:
                model_stats[model]['costs'].append(item['cost'])
            if item.get('response_time') is not None:
                model_stats[model]['response_times'].append(item['response_time'])
        
        # Create bar chart data
        bar_data = []
        for model, stats in model_stats.items():
            if stats['scores']:
                bar_data.append({
                    'category': model,
                    'value': statistics.mean(stats['scores']),
                    'metadata': {
                        'avg_cost': statistics.mean(stats['costs']) if stats['costs'] else 0,
                        'avg_response_time': statistics.mean(stats['response_times']) if stats['response_times'] else 0,
                        'executions': len(stats['scores'])
                    }
                })
        
        return ImpactVisualization(
            visualization_type='bar_chart',
            title=f'Model Performance Comparison - Prompt {prompt_id}',
            x_axis_label='Model',
            y_axis_label='Average Performance Score',
            data_series=[{
                'name': 'Average Score',
                'data': bar_data,
                'type': 'bar'
            }],
            annotations=[],
            metadata={'prompt_id': prompt_id}
        )
    
    def _store_trend_analysis(self, prompt_id: str, analysis_result: Dict[str, Any]):
        """Store trend analysis results in database."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO trend_analysis_results 
                    (prompt_id, analysis_data, created_at)
                    VALUES (?, ?, ?)
                """, (prompt_id, json.dumps(analysis_result), datetime.now().isoformat()))
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error storing trend analysis: {e}")
    
    def _store_drift_alerts(self, model_id: str, alerts: List[ModelDriftAlert]):
        """Store drift alerts in database."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                for alert in alerts:
                    cursor.execute("""
                        INSERT INTO model_drift_alerts 
                        (alert_id, model_id, drift_type, severity, current_value,
                         baseline_value, drift_percentage, description, 
                         recommended_actions, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        alert.alert_id, alert.model_id, alert.drift_type,
                        alert.severity, alert.current_value, alert.baseline_value,
                        alert.drift_percentage, alert.description,
                        json.dumps(alert.recommended_actions),
                        alert.detection_timestamp.isoformat()
                    ))
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error storing drift alerts: {e}")
    
    def _get_active_prompt_ids(self) -> List[str]:
        """Get list of active prompt IDs."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM prompts")
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"Error getting active prompt IDs: {e}")
            return []
    
    def _get_active_model_ids(self) -> List[str]:
        """Get list of active model IDs."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT model FROM evaluation_results WHERE created_at >= ?",
                             ((datetime.now() - timedelta(days=7)).isoformat(),))
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"Error getting active model IDs: {e}")
            return []
    
    def _check_prompt_performance_alerts(self, prompt_id: str) -> List[Dict[str, Any]]:
        """Check for performance alerts for a specific prompt."""
        alerts = []
        
        try:
            # Get recent performance metrics
            metrics = self._get_recent_prompt_metrics(prompt_id)
            if not metrics:
                return alerts
            
            # Check for performance degradation
            if metrics.get('avg_score', 1.0) < 0.5:
                alerts.append({
                    'type': 'performance_degradation',
                    'prompt_id': prompt_id,
                    'severity': 'high',
                    'description': f"Performance score below threshold: {metrics['avg_score']:.2f}",
                    'timestamp': datetime.now().isoformat()
                })
            
            # Check for high cost
            if metrics.get('avg_cost', 0.0) > 0.1:  # Threshold for high cost
                alerts.append({
                    'type': 'high_cost',
                    'prompt_id': prompt_id,
                    'severity': 'medium',
                    'description': f"High average cost detected: ${metrics['avg_cost']:.4f}",
                    'timestamp': datetime.now().isoformat()
                })
            
            # Check for low success rate
            if metrics.get('success_rate', 1.0) < 0.8:
                alerts.append({
                    'type': 'low_success_rate',
                    'prompt_id': prompt_id,
                    'severity': 'high',
                    'description': f"Low success rate: {metrics['success_rate']:.1%}",
                    'timestamp': datetime.now().isoformat()
                })
            
        except Exception as e:
            self.logger.error(f"Error checking prompt performance alerts: {e}")
        
        return alerts
    
    def _get_recent_prompt_metrics(self, prompt_id: str) -> Optional[Dict[str, float]]:
        """Get recent performance metrics for a prompt."""
        try:
            cutoff_date = datetime.now() - timedelta(days=7)
            
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT er.scores, er.cost, er.error
                    FROM evaluation_results er
                    JOIN evaluation_runs run ON er.run_id = run.run_id
                    JOIN prompt_versions pv ON run.prompt_version_id = pv.version_id
                    WHERE pv.prompt_id = ? AND er.created_at >= ?
                """, (prompt_id, cutoff_date.isoformat()))
                
                results = cursor.fetchall()
                if len(results) >= 3:
                    # Process results to calculate averages
                    scores = []
                    costs = []
                    success_count = 0
                    
                    for row in results:
                        scores_json = json.loads(row[0] or '{}')
                        score = scores_json.get('overall', scores_json.get('score', 0.0))
                        if isinstance(score, str):
                            try:
                                score = float(score)
                            except:
                                score = 0.0
                        scores.append(score)
                        costs.append(row[1] or 0.0)
                        if row[2] is None and score > 0:  # No error and positive score
                            success_count += 1
                    
                    return {
                        'avg_score': statistics.mean(scores) if scores else 0.0,
                        'avg_cost': statistics.mean(costs) if costs else 0.0,
                        'success_rate': success_count / len(results) if results else 0.0
                    }
                
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting recent prompt metrics: {e}")
            return None