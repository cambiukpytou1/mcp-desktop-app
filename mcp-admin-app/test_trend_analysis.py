"""
Test Trend Analysis and Monitoring
==================================

Test suite for trend analysis and monitoring functionality.
"""

import unittest
import tempfile
import os
from datetime import datetime, timedelta
from pathlib import Path
import json

# Import the modules to test
from core.config import ConfigurationManager
from data.database import DatabaseManager
from services.analytics.trend_analysis import TrendAnalysisService, TrendPoint, TrendAnalysis, ModelDriftAlert


class TestTrendAnalysis(unittest.TestCase):
    """Test cases for trend analysis functionality."""
    
    def setUp(self):
        """Set up test environment."""
        # Create temporary directory for test database
        self.test_dir = tempfile.mkdtemp()
        self.db_path = Path(self.test_dir) / "test_admin.db"
        
        # Initialize managers
        self.config_manager = ConfigurationManager()
        self.db_manager = DatabaseManager(self.db_path)
        self.db_manager.initialize()
        
        # Initialize trend analysis service
        self.trend_service = TrendAnalysisService(self.config_manager, self.db_manager)
        
        # Create test data
        self.setup_test_data()
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def setup_test_data(self):
        """Set up test data in the database."""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create test prompt
            cursor.execute("""
                INSERT INTO prompts (id, name, content, created_at, updated_at)
                VALUES ('test-prompt-1', 'Test Prompt', 'This is a test prompt content', ?, ?)
            """, (datetime.now().isoformat(), datetime.now().isoformat()))
            
            # Create test prompt version
            cursor.execute("""
                INSERT INTO prompt_versions (version_id, prompt_id, content, created_at)
                VALUES ('test-version-1', 'test-prompt-1', 'This is a test prompt content', ?)
            """, (datetime.now().isoformat(),))
            
            # Create test evaluation run
            cursor.execute("""
                INSERT INTO evaluation_runs (run_id, prompt_version_id, created_at)
                VALUES ('test-run-1', 'test-version-1', ?)
            """, (datetime.now().isoformat(),))
            
            # Create test evaluation results with trend data
            base_time = datetime.now() - timedelta(days=30)
            for i in range(20):
                timestamp = base_time + timedelta(days=i)
                # Create improving trend in score
                score = 0.5 + (i * 0.02)  # Improving from 0.5 to 0.9
                cost = 0.01 + (i * 0.0005)  # Slightly increasing cost
                response_time = 1000 - (i * 10)  # Improving response time
                
                cursor.execute("""
                    INSERT INTO evaluation_results 
                    (result_id, run_id, prompt_version_id, model, scores, cost, 
                     token_usage, execution_time, created_at)
                    VALUES (?, 'test-run-1', 'test-version-1', 'gpt-4', ?, ?, ?, ?, ?)
                """, (f'result-{i}', json.dumps({'overall': score}), cost, 
                      json.dumps({'total_tokens': 100}), response_time, timestamp.isoformat()))
            
            conn.commit()
    
    def test_historical_performance_tracking(self):
        """Test historical performance tracking."""
        # Test with sufficient data
        result = self.trend_service.track_historical_performance('test-prompt-1', 30)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result['prompt_id'], 'test-prompt-1')
        self.assertIn('trends', result)
        self.assertIn('summary', result)
        
        # Check that trends were analyzed
        trends = result['trends']
        self.assertIn('score', trends)
        self.assertIn('cost', trends)
        self.assertIn('response_time', trends)
        
        # Score should show improving trend
        score_trend = trends['score']
        self.assertEqual(score_trend['trend_type'], 'improving')
        self.assertGreater(score_trend['slope'], 0)
        
        # Test with insufficient data
        result_insufficient = self.trend_service.track_historical_performance('nonexistent-prompt', 30)
        self.assertEqual(result_insufficient['status'], 'insufficient_data')
    
    def test_trend_analysis_calculations(self):
        """Test trend analysis calculations."""
        # Create test data points
        test_data = []
        base_time = datetime.now()
        for i in range(10):
            test_data.append({
                'score': 0.5 + (i * 0.05),  # Improving trend
                'cost': 0.01,
                'tokens': 100,
                'response_time': 1000,
                'timestamp': base_time + timedelta(days=i),
                'model': 'test-model',
                'success': True
            })
        
        # Analyze score trend
        trend_analysis = self.trend_service._analyze_metric_trend(test_data, 'score', 'Test Score')
        
        self.assertIsInstance(trend_analysis, TrendAnalysis)
        self.assertEqual(trend_analysis.trend_type, 'improving')
        self.assertGreater(trend_analysis.slope, 0)
        self.assertGreater(trend_analysis.confidence, 0)
        self.assertEqual(len(trend_analysis.data_points), 10)
    
    def test_linear_regression_calculation(self):
        """Test linear regression calculations."""
        # Test with perfect positive correlation
        x_values = [1, 2, 3, 4, 5]
        y_values = [2, 4, 6, 8, 10]  # y = 2x
        
        slope, r_squared = self.trend_service._calculate_linear_regression(x_values, y_values)
        
        self.assertAlmostEqual(slope, 2.0, places=2)
        self.assertAlmostEqual(r_squared, 1.0, places=2)
        
        # Test with no correlation
        x_values = [1, 2, 3, 4, 5]
        y_values = [5, 5, 5, 5, 5]  # Flat line
        
        slope, r_squared = self.trend_service._calculate_linear_regression(x_values, y_values)
        
        self.assertAlmostEqual(slope, 0.0, places=2)
        self.assertAlmostEqual(r_squared, 0.0, places=2)
    
    def test_trend_classification(self):
        """Test trend classification logic."""
        # Test improving trend
        trend_type = self.trend_service._classify_trend(0.05, 0.8)
        self.assertEqual(trend_type, 'improving')
        
        # Test declining trend
        trend_type = self.trend_service._classify_trend(-0.05, 0.8)
        self.assertEqual(trend_type, 'declining')
        
        # Test stable trend
        trend_type = self.trend_service._classify_trend(0.0005, 0.8)
        self.assertEqual(trend_type, 'stable')
        
        # Test volatile trend (low R-squared)
        trend_type = self.trend_service._classify_trend(0.05, 0.2)
        self.assertEqual(trend_type, 'volatile')
    
    def test_model_drift_detection(self):
        """Test model drift detection."""
        # Set up baseline for test model
        self.trend_service.baselines['gpt-4'] = {
            'metrics': {
                'avg_score': 0.7,
                'avg_cost': 0.02,
                'avg_response_time': 800,
                'success_rate': 0.95
            },
            'last_updated': datetime.now()
        }
        
        # Add recent data that shows drift
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Add recent evaluation results with significant drift
            recent_time = datetime.now() - timedelta(days=3)
            for i in range(5):
                timestamp = recent_time + timedelta(hours=i)
                # Significant performance drop
                score = 0.4  # Down from baseline of 0.7
                cost = 0.035  # Up from baseline of 0.02
                
                cursor.execute("""
                    INSERT INTO evaluation_results 
                    (result_id, run_id, prompt_version_id, model, scores, cost, 
                     token_usage, execution_time, created_at)
                    VALUES (?, 'test-run-1', 'test-version-1', 'gpt-4', ?, ?, ?, 800, ?)
                """, (f'drift-result-{i}', json.dumps({'overall': score}), cost,
                      json.dumps({'total_tokens': 100}), timestamp.isoformat()))
            
            conn.commit()
        
        # Detect drift
        drift_alerts = self.trend_service.detect_model_drift('gpt-4', 7)
        
        self.assertIsInstance(drift_alerts, list)
        # Should detect drift in performance and cost
        self.assertGreater(len(drift_alerts), 0)
        
        # Check alert properties
        for alert in drift_alerts:
            self.assertIsInstance(alert, ModelDriftAlert)
            self.assertEqual(alert.model_id, 'gpt-4')
            self.assertIn(alert.severity, ['low', 'medium', 'high', 'critical'])
            self.assertGreater(alert.drift_percentage, 0)
    
    def test_impact_visualization_generation(self):
        """Test impact visualization generation."""
        # Test line chart generation
        visualization = self.trend_service.generate_impact_visualization('test-prompt-1', 'line_chart')
        
        self.assertEqual(visualization.visualization_type, 'line_chart')
        self.assertIn('Prompt test-prompt-1', visualization.title)
        self.assertIsInstance(visualization.data_series, list)
        self.assertGreater(len(visualization.data_series), 0)
        
        # Test heatmap generation
        heatmap_viz = self.trend_service.generate_impact_visualization('test-prompt-1', 'heatmap')
        self.assertEqual(heatmap_viz.visualization_type, 'heatmap')
        
        # Test scatter plot generation
        scatter_viz = self.trend_service.generate_impact_visualization('test-prompt-1', 'scatter_plot')
        self.assertEqual(scatter_viz.visualization_type, 'scatter_plot')
        
        # Test bar chart generation
        bar_viz = self.trend_service.generate_impact_visualization('test-prompt-1', 'bar_chart')
        self.assertEqual(bar_viz.visualization_type, 'bar_chart')
        
        # Test invalid visualization type
        with self.assertRaises(ValueError):
            self.trend_service.generate_impact_visualization('test-prompt-1', 'invalid_type')
    
    def test_performance_alerts_monitoring(self):
        """Test performance alerts monitoring."""
        # Add a prompt with poor performance
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create another test prompt
            cursor.execute("""
                INSERT INTO prompts (id, name, content, created_at, updated_at)
                VALUES ('poor-prompt', 'Poor Prompt', 'Poor performing prompt content', ?, ?)
            """, (datetime.now().isoformat(), datetime.now().isoformat()))
            
            # Create version and run
            cursor.execute("""
                INSERT INTO prompt_versions (version_id, prompt_id, content, created_at)
                VALUES ('poor-version', 'poor-prompt', 'Poor performing prompt content', ?)
            """, (datetime.now().isoformat(),))
            
            cursor.execute("""
                INSERT INTO evaluation_runs (run_id, prompt_version_id, created_at)
                VALUES ('poor-run', 'poor-version', ?)
            """, (datetime.now().isoformat(),))
            
            # Add poor performance results
            recent_time = datetime.now() - timedelta(days=3)
            for i in range(5):
                timestamp = recent_time + timedelta(hours=i)
                cursor.execute("""
                    INSERT INTO evaluation_results 
                    (result_id, run_id, prompt_version_id, model, scores, cost, 
                     token_usage, execution_time, error, created_at)
                    VALUES (?, 'poor-run', 'poor-version', 'gpt-4', ?, 0.15, ?, 2000, 'Test error', ?)
                """, (f'poor-result-{i}', json.dumps({'overall': 0.3}), 
                      json.dumps({'total_tokens': 100}), timestamp.isoformat()))
            
            conn.commit()
        
        # Monitor for alerts
        alerts = self.trend_service.monitor_performance_alerts()
        
        self.assertIsInstance(alerts, list)
        # Should find alerts for the poor-performing prompt
        alert_types = [alert.get('type') for alert in alerts]
        self.assertIn('performance_degradation', alert_types)
    
    def test_drift_recommendations(self):
        """Test drift recommendation generation."""
        # Test performance drift recommendations
        recommendations = self.trend_service._generate_drift_recommendations('performance', 0.25)
        
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)
        self.assertTrue(any('prompt' in rec.lower() for rec in recommendations))
        
        # Test cost drift recommendations
        cost_recommendations = self.trend_service._generate_drift_recommendations('cost', 0.35)
        self.assertIsInstance(cost_recommendations, list)
        self.assertTrue(any('cost' in rec.lower() for rec in cost_recommendations))
        
        # Test high drift recommendations
        high_drift_recs = self.trend_service._generate_drift_recommendations('performance', 0.4)
        self.assertTrue(any('immediate' in rec.lower() for rec in high_drift_recs))
    
    def test_trend_summary_generation(self):
        """Test trend summary generation."""
        # Create mock trend analyses
        trends = {
            'score': TrendAnalysis(
                trend_type='improving',
                slope=0.05,
                confidence=0.8,
                r_squared=0.8,
                data_points=[],
                analysis_period=30,
                significance_level=0.8
            ),
            'cost': TrendAnalysis(
                trend_type='declining',
                slope=-0.02,
                confidence=0.9,
                r_squared=0.9,
                data_points=[],
                analysis_period=30,
                significance_level=0.9
            )
        }
        
        summary = self.trend_service._generate_trend_summary(trends)
        
        self.assertIsInstance(summary, dict)
        self.assertIn('overall_health', summary)
        self.assertIn('key_insights', summary)
        self.assertIn('recommendations', summary)
        
        # Should identify mixed health (improving score, declining cost)
        self.assertEqual(summary['overall_health'], 'stable')  # Equal improving/declining
        
        # Should have insights for high-confidence trends
        insights = summary['key_insights']
        self.assertTrue(any('score' in insight.lower() for insight in insights))
        self.assertTrue(any('cost' in insight.lower() for insight in insights))
    
    def test_database_storage_operations(self):
        """Test database storage operations for trend analysis."""
        # Test storing trend analysis results
        test_result = {
            'prompt_id': 'test-prompt-1',
            'trends': {'score': {'trend_type': 'improving'}},
            'summary': {'overall_health': 'good'}
        }
        
        # This should not raise an exception
        self.trend_service._store_trend_analysis('test-prompt-1', test_result)
        
        # Test storing drift alerts
        test_alert = ModelDriftAlert(
            alert_id='test-alert-1',
            model_id='gpt-4',
            prompt_id='',
            drift_type='performance',
            severity='medium',
            current_value=0.5,
            baseline_value=0.7,
            drift_percentage=0.29,
            detection_timestamp=datetime.now(),
            description='Test drift alert',
            recommended_actions=['Test action']
        )
        
        # This should not raise an exception
        self.trend_service._store_drift_alerts('gpt-4', [test_alert])
    
    def test_edge_cases(self):
        """Test edge cases and error handling."""
        # Test with empty data
        empty_result = self.trend_service.track_historical_performance('nonexistent', 30)
        self.assertEqual(empty_result['status'], 'insufficient_data')
        
        # Test drift detection with no baseline
        no_baseline_alerts = self.trend_service.detect_model_drift('nonexistent-model', 7)
        self.assertEqual(len(no_baseline_alerts), 0)
        
        # Test visualization with no data
        with self.assertRaises(ValueError):
            self.trend_service.generate_impact_visualization('nonexistent', 'line_chart')
        
        # Test linear regression with insufficient data
        slope, r_squared = self.trend_service._calculate_linear_regression([1], [1])
        self.assertEqual(slope, 0.0)
        self.assertEqual(r_squared, 0.0)


class TestTrendAnalysisIntegration(unittest.TestCase):
    """Integration tests for trend analysis with other components."""
    
    def setUp(self):
        """Set up integration test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.db_path = Path(self.test_dir) / "integration_test.db"
        
        self.config_manager = ConfigurationManager()
        self.db_manager = DatabaseManager(self.db_path)
        self.db_manager.initialize()
        
        self.trend_service = TrendAnalysisService(self.config_manager, self.db_manager)
    
    def tearDown(self):
        """Clean up integration test environment."""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_end_to_end_trend_analysis(self):
        """Test complete end-to-end trend analysis workflow."""
        # This test would simulate a complete workflow from data creation
        # through trend analysis to visualization generation
        
        # Create comprehensive test data
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create multiple prompts and models
            prompts = ['prompt-1', 'prompt-2', 'prompt-3']
            models = ['gpt-4', 'gpt-3.5-turbo', 'claude-3']
            
            for prompt_id in prompts:
                cursor.execute("""
                    INSERT INTO prompts (id, name, content, created_at, updated_at)
                    VALUES (?, ?, 'Test prompt content', ?, ?)
                """, (prompt_id, f'Test {prompt_id}', datetime.now().isoformat(), datetime.now().isoformat()))
                
                cursor.execute("""
                    INSERT INTO prompt_versions (version_id, prompt_id, content, created_at)
                    VALUES (?, ?, 'Test prompt content', ?)
                """, (f'{prompt_id}-v1', prompt_id, datetime.now().isoformat()))
                
                cursor.execute("""
                    INSERT INTO evaluation_runs (run_id, prompt_version_id, created_at)
                    VALUES (?, ?, ?)
                """, (f'{prompt_id}-run', f'{prompt_id}-v1', datetime.now().isoformat()))
                
                # Create varied performance data for each model
                base_time = datetime.now() - timedelta(days=60)
                for i in range(30):
                    for model in models:
                        timestamp = base_time + timedelta(days=i, hours=models.index(model))
                        
                        # Create different trend patterns for different prompts
                        if prompt_id == 'prompt-1':
                            score = 0.6 + (i * 0.01)  # Improving
                        elif prompt_id == 'prompt-2':
                            score = 0.8 - (i * 0.005)  # Declining
                        else:
                            score = 0.7 + (0.1 * (i % 5 - 2) / 5)  # Volatile
                        
                        cursor.execute("""
                            INSERT INTO evaluation_results 
                            (result_id, run_id, prompt_version_id, model, scores, cost, 
                             token_usage, execution_time, created_at)
                            VALUES (?, ?, ?, ?, ?, 0.02, ?, 1000, ?)
                        """, (f'{prompt_id}-{model}-{i}', f'{prompt_id}-run', f'{prompt_id}-v1', 
                              model, json.dumps({'overall': score}), 
                              json.dumps({'total_tokens': 100}), timestamp.isoformat()))
            
            conn.commit()
        
        # Perform comprehensive analysis
        for prompt_id in prompts:
            # Track historical performance
            performance_result = self.trend_service.track_historical_performance(prompt_id, 60)
            self.assertIn('trends', performance_result)
            
            # Generate visualizations
            for viz_type in ['line_chart', 'heatmap', 'scatter_plot', 'bar_chart']:
                visualization = self.trend_service.generate_impact_visualization(prompt_id, viz_type)
                self.assertEqual(visualization.visualization_type, viz_type)
        
        # Test model drift detection for all models
        for model in models:
            drift_alerts = self.trend_service.detect_model_drift(model, 7)
            self.assertIsInstance(drift_alerts, list)
        
        # Test comprehensive monitoring
        all_alerts = self.trend_service.monitor_performance_alerts()
        self.assertIsInstance(all_alerts, list)


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)