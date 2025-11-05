"""
Cost Visualization and Reporting Service
=======================================

Visual cost reporting with charts, graphs, and real-time monitoring displays.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import json

from .cost_tracking import CostTracker, CostReport, RealTimeTokenCount, CostAlert


@dataclass
class ChartData:
    """Chart data structure for visualization."""
    chart_type: str  # line, bar, pie, gauge
    title: str
    labels: List[str] = field(default_factory=list)
    datasets: List[Dict[str, Any]] = field(default_factory=list)
    options: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "chart_type": self.chart_type,
            "title": self.title,
            "labels": self.labels,
            "datasets": self.datasets,
            "options": self.options
        }


@dataclass
class Dashboard:
    """Cost monitoring dashboard data."""
    dashboard_id: str
    title: str
    charts: List[ChartData] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    alerts: List[Dict[str, Any]] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "dashboard_id": self.dashboard_id,
            "title": self.title,
            "charts": [chart.to_dict() for chart in self.charts],
            "metrics": self.metrics,
            "alerts": self.alerts,
            "last_updated": self.last_updated.isoformat()
        }


class CostVisualizationService:
    """Service for generating cost visualizations and reports."""
    
    def __init__(self, cost_tracker: CostTracker):
        self.logger = logging.getLogger(__name__)
        self.cost_tracker = cost_tracker
        
        # Color schemes for charts
        self.colors = {
            "primary": "#1a73e8",
            "success": "#34a853",
            "warning": "#fbbc04",
            "danger": "#ea4335",
            "info": "#4285f4",
            "secondary": "#9aa0a6"
        }
        
        self.provider_colors = {
            "openai": "#10a37f",
            "anthropic": "#d97706",
            "gemini": "#4285f4",
            "local": "#6b7280"
        }
    
    def create_cost_overview_chart(self, report: CostReport) -> ChartData:
        """Create cost overview chart from report data."""
        try:
            # Create pie chart for provider cost breakdown
            labels = []
            data = []
            colors = []
            
            for provider_id, breakdown in report.provider_breakdown.items():
                labels.append(provider_id.title())
                data.append(breakdown["cost"])
                colors.append(self.provider_colors.get(provider_id, self.colors["secondary"]))
            
            chart = ChartData(
                chart_type="pie",
                title="Cost by Provider",
                labels=labels,
                datasets=[{
                    "label": "Cost ($)",
                    "data": data,
                    "backgroundColor": colors,
                    "borderWidth": 2
                }],
                options={
                    "responsive": True,
                    "plugins": {
                        "legend": {
                            "position": "right"
                        },
                        "tooltip": {
                            "callbacks": {
                                "label": "function(context) { return context.label + ': $' + context.parsed.toFixed(4); }"
                            }
                        }
                    }
                }
            )
            
            return chart
        
        except Exception as e:
            self.logger.error(f"Failed to create cost overview chart: {e}")
            return ChartData(chart_type="pie", title="Cost Overview - Error")
    
    def create_hourly_cost_chart(self, report: CostReport) -> ChartData:
        """Create hourly cost trend chart."""
        try:
            if not report.hourly_breakdown:
                return ChartData(chart_type="line", title="Hourly Cost Trend - No Data")
            
            labels = []
            costs = []
            requests = []
            
            for hour_data in report.hourly_breakdown:
                # Format hour for display
                hour_dt = datetime.fromisoformat(hour_data["hour"])
                labels.append(hour_dt.strftime("%m/%d %H:00"))
                costs.append(hour_data["cost"])
                requests.append(hour_data["requests"])
            
            chart = ChartData(
                chart_type="line",
                title="Hourly Cost and Request Trends",
                labels=labels,
                datasets=[
                    {
                        "label": "Cost ($)",
                        "data": costs,
                        "borderColor": self.colors["primary"],
                        "backgroundColor": self.colors["primary"] + "20",
                        "yAxisID": "y",
                        "tension": 0.4
                    },
                    {
                        "label": "Requests",
                        "data": requests,
                        "borderColor": self.colors["success"],
                        "backgroundColor": self.colors["success"] + "20",
                        "yAxisID": "y1",
                        "tension": 0.4
                    }
                ],
                options={
                    "responsive": True,
                    "interaction": {
                        "mode": "index",
                        "intersect": False
                    },
                    "scales": {
                        "x": {
                            "display": True,
                            "title": {
                                "display": True,
                                "text": "Time"
                            }
                        },
                        "y": {
                            "type": "linear",
                            "display": True,
                            "position": "left",
                            "title": {
                                "display": True,
                                "text": "Cost ($)"
                            }
                        },
                        "y1": {
                            "type": "linear",
                            "display": True,
                            "position": "right",
                            "title": {
                                "display": True,
                                "text": "Requests"
                            },
                            "grid": {
                                "drawOnChartArea": False
                            }
                        }
                    }
                }
            )
            
            return chart
        
        except Exception as e:
            self.logger.error(f"Failed to create hourly cost chart: {e}")
            return ChartData(chart_type="line", title="Hourly Cost Trend - Error")
    
    def create_model_comparison_chart(self, report: CostReport) -> ChartData:
        """Create model cost comparison chart."""
        try:
            if not report.model_breakdown:
                return ChartData(chart_type="bar", title="Model Cost Comparison - No Data")
            
            labels = []
            costs = []
            tokens = []
            colors = []
            
            # Sort by cost descending
            sorted_models = sorted(
                report.model_breakdown.items(),
                key=lambda x: x[1]["cost"],
                reverse=True
            )
            
            for model_key, breakdown in sorted_models[:10]:  # Top 10 models
                provider_id, model_id = model_key.split(":", 1)
                labels.append(f"{provider_id}:{model_id}")
                costs.append(breakdown["cost"])
                tokens.append(breakdown["tokens"])
                colors.append(self.provider_colors.get(provider_id, self.colors["secondary"]))
            
            chart = ChartData(
                chart_type="bar",
                title="Top Models by Cost",
                labels=labels,
                datasets=[
                    {
                        "label": "Cost ($)",
                        "data": costs,
                        "backgroundColor": colors,
                        "borderWidth": 1,
                        "yAxisID": "y"
                    }
                ],
                options={
                    "responsive": True,
                    "plugins": {
                        "legend": {
                            "display": False
                        },
                        "tooltip": {
                            "callbacks": {
                                "label": "function(context) { return 'Cost: $' + context.parsed.y.toFixed(4); }"
                            }
                        }
                    },
                    "scales": {
                        "x": {
                            "display": True,
                            "title": {
                                "display": True,
                                "text": "Model"
                            }
                        },
                        "y": {
                            "display": True,
                            "title": {
                                "display": True,
                                "text": "Cost ($)"
                            }
                        }
                    }
                }
            )
            
            return chart
        
        except Exception as e:
            self.logger.error(f"Failed to create model comparison chart: {e}")
            return ChartData(chart_type="bar", title="Model Cost Comparison - Error")
    
    def create_real_time_gauge(self, current_cost: float, budget_limit: float = None) -> ChartData:
        """Create real-time cost gauge chart."""
        try:
            # Determine gauge color based on cost level
            if budget_limit:
                percentage = (current_cost / budget_limit) * 100
                if percentage >= 90:
                    color = self.colors["danger"]
                elif percentage >= 75:
                    color = self.colors["warning"]
                else:
                    color = self.colors["success"]
            else:
                color = self.colors["primary"]
                percentage = min(current_cost * 10, 100)  # Scale for display
            
            chart = ChartData(
                chart_type="gauge",
                title="Real-time Cost",
                datasets=[{
                    "label": "Current Cost",
                    "data": [current_cost],
                    "backgroundColor": color,
                    "borderWidth": 2
                }],
                options={
                    "responsive": True,
                    "plugins": {
                        "legend": {
                            "display": False
                        }
                    },
                    "gauge": {
                        "min": 0,
                        "max": budget_limit or (current_cost * 2) or 10,
                        "value": current_cost,
                        "label": f"${current_cost:.4f}",
                        "color": color
                    }
                }
            )
            
            return chart
        
        except Exception as e:
            self.logger.error(f"Failed to create real-time gauge: {e}")
            return ChartData(chart_type="gauge", title="Real-time Cost - Error")
    
    def create_token_usage_chart(self, report: CostReport) -> ChartData:
        """Create token usage breakdown chart."""
        try:
            if not report.provider_breakdown:
                return ChartData(chart_type="bar", title="Token Usage - No Data")
            
            labels = []
            input_tokens = []
            output_tokens = []
            
            for provider_id, breakdown in report.provider_breakdown.items():
                labels.append(provider_id.title())
                # Estimate input/output split (would need actual data in production)
                total_tokens = breakdown["tokens"]
                input_tokens.append(int(total_tokens * 0.6))  # Assume 60% input
                output_tokens.append(int(total_tokens * 0.4))  # Assume 40% output
            
            chart = ChartData(
                chart_type="bar",
                title="Token Usage by Provider",
                labels=labels,
                datasets=[
                    {
                        "label": "Input Tokens",
                        "data": input_tokens,
                        "backgroundColor": self.colors["primary"],
                        "stack": "tokens"
                    },
                    {
                        "label": "Output Tokens",
                        "data": output_tokens,
                        "backgroundColor": self.colors["info"],
                        "stack": "tokens"
                    }
                ],
                options={
                    "responsive": True,
                    "plugins": {
                        "legend": {
                            "position": "top"
                        }
                    },
                    "scales": {
                        "x": {
                            "stacked": True,
                            "title": {
                                "display": True,
                                "text": "Provider"
                            }
                        },
                        "y": {
                            "stacked": True,
                            "title": {
                                "display": True,
                                "text": "Tokens"
                            }
                        }
                    }
                }
            )
            
            return chart
        
        except Exception as e:
            self.logger.error(f"Failed to create token usage chart: {e}")
            return ChartData(chart_type="bar", title="Token Usage - Error")
    
    def create_cost_efficiency_chart(self, report: CostReport) -> ChartData:
        """Create cost efficiency chart (cost per token)."""
        try:
            if not report.model_breakdown:
                return ChartData(chart_type="scatter", title="Cost Efficiency - No Data")
            
            data_points = []
            colors = []
            
            for model_key, breakdown in report.model_breakdown.items():
                provider_id, model_id = model_key.split(":", 1)
                
                if breakdown["tokens"] > 0:
                    cost_per_token = breakdown["cost"] / breakdown["tokens"]
                    data_points.append({
                        "x": breakdown["tokens"],
                        "y": cost_per_token,
                        "label": f"{provider_id}:{model_id}"
                    })
                    colors.append(self.provider_colors.get(provider_id, self.colors["secondary"]))
            
            chart = ChartData(
                chart_type="scatter",
                title="Cost Efficiency (Cost per Token vs Volume)",
                datasets=[{
                    "label": "Models",
                    "data": data_points,
                    "backgroundColor": colors,
                    "borderColor": colors,
                    "pointRadius": 8,
                    "pointHoverRadius": 10
                }],
                options={
                    "responsive": True,
                    "plugins": {
                        "legend": {
                            "display": False
                        },
                        "tooltip": {
                            "callbacks": {
                                "label": "function(context) { return context.raw.label + ': $' + context.parsed.y.toFixed(6) + ' per token'; }"
                            }
                        }
                    },
                    "scales": {
                        "x": {
                            "title": {
                                "display": True,
                                "text": "Total Tokens"
                            }
                        },
                        "y": {
                            "title": {
                                "display": True,
                                "text": "Cost per Token ($)"
                            }
                        }
                    }
                }
            )
            
            return chart
        
        except Exception as e:
            self.logger.error(f"Failed to create cost efficiency chart: {e}")
            return ChartData(chart_type="scatter", title="Cost Efficiency - Error")
    
    def create_dashboard(self, time_period_hours: int = 24) -> Dashboard:
        """Create comprehensive cost monitoring dashboard."""
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=time_period_hours)
            
            # Generate report for the time period
            report = self.cost_tracker.generate_cost_report(start_time, end_time, "detailed")
            
            # Get real-time data
            real_time_data = self.cost_tracker.get_real_time_costs()
            
            # Create dashboard
            dashboard = Dashboard(
                dashboard_id=f"cost_dashboard_{int(datetime.now().timestamp())}",
                title=f"Cost Dashboard - Last {time_period_hours} Hours"
            )
            
            # Add charts
            dashboard.charts.extend([
                self.create_cost_overview_chart(report),
                self.create_hourly_cost_chart(report),
                self.create_model_comparison_chart(report),
                self.create_real_time_gauge(real_time_data["total_cost"]),
                self.create_token_usage_chart(report),
                self.create_cost_efficiency_chart(report)
            ])
            
            # Add key metrics
            dashboard.metrics = {
                "total_cost": report.total_cost,
                "total_requests": report.total_requests,
                "total_tokens": report.total_tokens,
                "active_sessions": real_time_data["active_sessions"],
                "real_time_cost": real_time_data["total_cost"],
                "average_cost_per_request": report.total_cost / report.total_requests if report.total_requests > 0 else 0,
                "average_cost_per_token": report.total_cost / report.total_tokens if report.total_tokens > 0 else 0,
                "time_period": f"{time_period_hours} hours"
            }
            
            # Add active alerts
            for alert in self.cost_tracker.alerts.values():
                if alert.is_active and alert.triggered_count > 0:
                    dashboard.alerts.append({
                        "alert_id": alert.alert_id,
                        "name": alert.name,
                        "type": alert.alert_type,
                        "triggered_count": alert.triggered_count,
                        "last_triggered": alert.last_triggered.isoformat() if alert.last_triggered else None
                    })
            
            self.logger.info(f"Created cost dashboard with {len(dashboard.charts)} charts")
            return dashboard
        
        except Exception as e:
            self.logger.error(f"Failed to create dashboard: {e}")
            return Dashboard(
                dashboard_id="error_dashboard",
                title="Cost Dashboard - Error"
            )
    
    def export_report_data(self, report: CostReport, format: str = "json") -> str:
        """Export report data in specified format."""
        try:
            if format.lower() == "json":
                return json.dumps(report.to_dict(), indent=2)
            elif format.lower() == "csv":
                return self._export_csv(report)
            else:
                raise ValueError(f"Unsupported export format: {format}")
        
        except Exception as e:
            self.logger.error(f"Failed to export report data: {e}")
            return ""
    
    def _export_csv(self, report: CostReport) -> str:
        """Export report data as CSV."""
        try:
            lines = []
            
            # Header
            lines.append("Report Summary")
            lines.append(f"Period,{report.time_period_start.isoformat()},{report.time_period_end.isoformat()}")
            lines.append(f"Total Cost,${report.total_cost:.4f}")
            lines.append(f"Total Requests,{report.total_requests}")
            lines.append(f"Total Tokens,{report.total_tokens}")
            lines.append("")
            
            # Provider breakdown
            lines.append("Provider Breakdown")
            lines.append("Provider,Requests,Cost,Tokens,Avg Response Time")
            for provider_id, breakdown in report.provider_breakdown.items():
                lines.append(f"{provider_id},{breakdown['requests']},${breakdown['cost']:.4f},{breakdown['tokens']},{breakdown['avg_response_time']:.2f}ms")
            lines.append("")
            
            # Model breakdown
            lines.append("Model Breakdown")
            lines.append("Provider,Model,Requests,Cost,Tokens")
            for model_key, breakdown in report.model_breakdown.items():
                provider_id, model_id = model_key.split(":", 1)
                lines.append(f"{provider_id},{model_id},{breakdown['requests']},${breakdown['cost']:.4f},{breakdown['tokens']}")
            
            return "\n".join(lines)
        
        except Exception as e:
            self.logger.error(f"Failed to export CSV: {e}")
            return ""
    
    def get_cost_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get cost summary for specified time period."""
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours)
            
            report = self.cost_tracker.generate_cost_report(start_time, end_time)
            real_time_data = self.cost_tracker.get_real_time_costs()
            
            return {
                "period_hours": hours,
                "historical": {
                    "total_cost": report.total_cost,
                    "total_requests": report.total_requests,
                    "total_tokens": report.total_tokens,
                    "providers": len(report.provider_breakdown),
                    "models": len(report.model_breakdown)
                },
                "real_time": {
                    "active_sessions": real_time_data["active_sessions"],
                    "current_cost": real_time_data["total_cost"],
                    "current_tokens": real_time_data["total_tokens"]
                },
                "efficiency": {
                    "cost_per_request": report.total_cost / report.total_requests if report.total_requests > 0 else 0,
                    "cost_per_token": report.total_cost / report.total_tokens if report.total_tokens > 0 else 0,
                    "tokens_per_request": report.total_tokens / report.total_requests if report.total_requests > 0 else 0
                }
            }
        
        except Exception as e:
            self.logger.error(f"Failed to get cost summary: {e}")
            return {}