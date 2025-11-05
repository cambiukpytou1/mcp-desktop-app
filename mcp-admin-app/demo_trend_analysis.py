"""
Trend Analysis and Monitoring Demo
==================================

Demonstrates the trend analysis and monitoring capabilities.
"""

import json
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

from core.config import ConfigurationManager
from data.database import DatabaseManager
from services.analytics.trend_analysis import TrendAnalysisService


def create_demo_data(db_manager):
    """Create demo data for trend analysis."""
    print("Creating demo data...")
    
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        
        # Create demo prompts
        prompts = [
            ('demo-prompt-1', 'Summarization Prompt', 'Summarize the following text in 3 sentences: {text}'),
            ('demo-prompt-2', 'Translation Prompt', 'Translate the following text to French: {text}'),
            ('demo-prompt-3', 'Analysis Prompt', 'Analyze the sentiment of this text: {text}')
        ]
        
        for prompt_id, name, content in prompts:
            cursor.execute("""
                INSERT OR REPLACE INTO prompts (id, name, content, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (prompt_id, name, content, datetime.now(), datetime.now()))
            
            # Create version
            cursor.execute("""
                INSERT OR REPLACE INTO prompt_versions 
                (version_id, prompt_id, content, created_at)
                VALUES (?, ?, ?, ?)
            """, (f'{prompt_id}-v1', prompt_id, content, datetime.now()))
            
            # Create evaluation run
            cursor.execute("""
                INSERT OR REPLACE INTO evaluation_runs 
                (run_id, prompt_version_id, created_at)
                VALUES (?, ?, ?)
            """, (f'{prompt_id}-run', f'{prompt_id}-v1', datetime.now()))
        
        # Create evaluation results with different trends
        models = ['gpt-4', 'gpt-3.5-turbo', 'claude-3']
        base_time = datetime.now() - timedelta(days=30)
        
        for i in range(30):  # 30 days of data
            timestamp = base_time + timedelta(days=i)
            
            for j, (prompt_id, _, _) in enumerate(prompts):
                for model in models:
                    # Create different trend patterns
                    if prompt_id == 'demo-prompt-1':
                        # Improving trend
                        score = 0.6 + (i * 0.01) + (j * 0.05)
                        cost = 0.02 - (i * 0.0002)
                    elif prompt_id == 'demo-prompt-2':
                        # Declining trend
                        score = 0.8 - (i * 0.005)
                        cost = 0.015 + (i * 0.0003)
                    else:
                        # Volatile trend
                        score = 0.7 + (0.1 * ((i + j) % 5 - 2) / 5)
                        cost = 0.018 + (0.005 * ((i + j) % 3 - 1) / 3)
                    
                    # Add some model-specific variation
                    if model == 'gpt-4':
                        score += 0.05
                        cost += 0.005
                    elif model == 'claude-3':
                        score += 0.02
                        cost += 0.002
                    
                    # Ensure reasonable bounds
                    score = max(0.1, min(1.0, score))
                    cost = max(0.005, cost)
                    
                    cursor.execute("""
                        INSERT INTO evaluation_results 
                        (result_id, run_id, prompt_version_id, model, scores, cost, 
                         token_usage, execution_time, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        f'{prompt_id}-{model}-{i}',
                        f'{prompt_id}-run',
                        f'{prompt_id}-v1',
                        model,
                        json.dumps({'overall': score}),
                        cost,
                        json.dumps({'total_tokens': 100 + i * 2}),
                        1000 + i * 10,
                        timestamp
                    ))
        
        conn.commit()
    
    print("Demo data created successfully!")


def demonstrate_trend_analysis(trend_service):
    """Demonstrate trend analysis functionality."""
    print("\n" + "="*60)
    print("TREND ANALYSIS DEMONSTRATION")
    print("="*60)
    
    # Analyze trends for each demo prompt
    prompt_ids = ['demo-prompt-1', 'demo-prompt-2', 'demo-prompt-3']
    prompt_names = ['Summarization', 'Translation', 'Analysis']
    
    for prompt_id, prompt_name in zip(prompt_ids, prompt_names):
        print(f"\n--- {prompt_name} Prompt Trends ---")
        
        try:
            # Track historical performance
            results = trend_service.track_historical_performance(prompt_id, 30)
            
            if results.get('status') == 'insufficient_data':
                print(f"Insufficient data for {prompt_name} prompt")
                continue
            
            # Display trend results
            trends = results.get('trends', {})
            summary = results.get('summary', {})
            
            print(f"Data Points: {results.get('data_points', 0)}")
            print(f"Overall Health: {summary.get('overall_health', 'Unknown').title()}")
            
            for metric, trend_data in trends.items():
                trend_type = trend_data.get('trend_type', 'unknown')
                slope = trend_data.get('slope', 0)
                confidence = trend_data.get('confidence', 0)
                
                trend_symbol = {
                    'improving': '↗️',
                    'declining': '↘️',
                    'stable': '→',
                    'volatile': '📈'
                }.get(trend_type, '?')
                
                print(f"  {metric.title()}: {trend_symbol} {trend_type.title()} "
                      f"(slope: {slope:.4f}, confidence: {confidence:.1%})")
            
            # Display insights
            insights = summary.get('key_insights', [])
            if insights:
                print("  Key Insights:")
                for insight in insights:
                    print(f"    • {insight}")
            
            # Display recommendations
            recommendations = summary.get('recommendations', [])
            if recommendations:
                print("  Recommendations:")
                for rec in recommendations:
                    print(f"    • {rec}")
        
        except Exception as e:
            print(f"Error analyzing {prompt_name} prompt: {e}")


def demonstrate_drift_detection(trend_service):
    """Demonstrate model drift detection."""
    print("\n" + "="*60)
    print("MODEL DRIFT DETECTION DEMONSTRATION")
    print("="*60)
    
    models = ['gpt-4', 'gpt-3.5-turbo', 'claude-3']
    
    for model in models:
        print(f"\n--- {model} Drift Detection ---")
        
        try:
            # Detect drift for the model
            drift_alerts = trend_service.detect_model_drift(model, 7)
            
            if not drift_alerts:
                print(f"No drift detected for {model}")
                continue
            
            print(f"Found {len(drift_alerts)} drift alerts:")
            
            for alert in drift_alerts:
                severity_symbol = {
                    'critical': '🔴',
                    'high': '🟠',
                    'medium': '🟡',
                    'low': '🔵'
                }.get(alert.severity, '⚪')
                
                print(f"  {severity_symbol} {alert.drift_type.title()} Drift:")
                print(f"    Severity: {alert.severity.title()}")
                print(f"    Current: {alert.current_value:.4f}")
                print(f"    Baseline: {alert.baseline_value:.4f}")
                print(f"    Drift: {alert.drift_percentage:.1%}")
                print(f"    Description: {alert.description}")
                
                if alert.recommended_actions:
                    print("    Recommended Actions:")
                    for action in alert.recommended_actions[:3]:  # Show first 3
                        print(f"      • {action}")
        
        except Exception as e:
            print(f"Error detecting drift for {model}: {e}")


def demonstrate_visualizations(trend_service):
    """Demonstrate impact visualizations."""
    print("\n" + "="*60)
    print("IMPACT VISUALIZATION DEMONSTRATION")
    print("="*60)
    
    prompt_id = 'demo-prompt-1'  # Use the improving prompt
    viz_types = ['line_chart', 'heatmap', 'scatter_plot', 'bar_chart']
    
    for viz_type in viz_types:
        print(f"\n--- {viz_type.replace('_', ' ').title()} ---")
        
        try:
            visualization = trend_service.generate_impact_visualization(prompt_id, viz_type)
            
            print(f"Title: {visualization.title}")
            print(f"Type: {visualization.visualization_type}")
            print(f"X-Axis: {visualization.x_axis_label}")
            print(f"Y-Axis: {visualization.y_axis_label}")
            print(f"Data Series: {len(visualization.data_series)}")
            
            for series in visualization.data_series:
                print(f"  • {series['name']}: {len(series['data'])} data points")
            
            print(f"Metadata: {visualization.metadata}")
        
        except Exception as e:
            print(f"Error generating {viz_type}: {e}")


def demonstrate_monitoring(trend_service):
    """Demonstrate performance monitoring."""
    print("\n" + "="*60)
    print("PERFORMANCE MONITORING DEMONSTRATION")
    print("="*60)
    
    try:
        # Monitor for performance alerts
        alerts = trend_service.monitor_performance_alerts()
        
        if not alerts:
            print("No performance alerts detected")
            return
        
        print(f"Found {len(alerts)} performance alerts:")
        
        # Group alerts by type
        alert_types = {}
        for alert in alerts:
            alert_type = alert.get('type', 'unknown')
            if alert_type not in alert_types:
                alert_types[alert_type] = []
            alert_types[alert_type].append(alert)
        
        for alert_type, type_alerts in alert_types.items():
            print(f"\n{alert_type.replace('_', ' ').title()} Alerts: {len(type_alerts)}")
            
            for alert in type_alerts[:3]:  # Show first 3 of each type
                severity = alert.get('severity', 'low')
                severity_symbol = {
                    'critical': '🔴',
                    'high': '🟠',
                    'medium': '🟡',
                    'low': '🔵'
                }.get(severity, '⚪')
                
                print(f"  {severity_symbol} {alert.get('description', 'No description')}")
                print(f"    Source: {alert.get('model_id', alert.get('prompt_id', 'Unknown'))}")
                print(f"    Severity: {severity.title()}")
    
    except Exception as e:
        print(f"Error monitoring performance: {e}")


def main():
    """Run the trend analysis demo."""
    print("Trend Analysis and Monitoring Demo")
    print("=" * 40)
    
    # Create temporary database for demo
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "demo.db"
        
        # Initialize components
        config_manager = ConfigurationManager()
        db_manager = DatabaseManager(db_path)
        db_manager.initialize()
        
        trend_service = TrendAnalysisService(config_manager, db_manager)
        
        # Create demo data
        create_demo_data(db_manager)
        
        # Run demonstrations
        demonstrate_trend_analysis(trend_service)
        demonstrate_drift_detection(trend_service)
        demonstrate_visualizations(trend_service)
        demonstrate_monitoring(trend_service)
        
        print("\n" + "="*60)
        print("DEMO COMPLETED")
        print("="*60)
        print("\nThis demo showcased:")
        print("• Historical performance tracking with trend analysis")
        print("• Model drift detection with severity classification")
        print("• Impact visualization generation for different chart types")
        print("• Performance monitoring and alerting")
        print("\nThe trend analysis service provides comprehensive")
        print("monitoring capabilities for prompt performance optimization.")


if __name__ == '__main__':
    main()