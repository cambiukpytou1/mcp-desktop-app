"""
Test Analytics Dashboard Implementation
======================================

Basic tests for the analytics dashboard and optimization recommendations.
"""

import unittest
import tkinter as tk
from unittest.mock import Mock, patch
import sys
import os

# Add the parent directory to the path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.analytics_dashboard_page import AnalyticsDashboardPage
from ui.prompt_components.optimization_recommendations import OptimizationRecommendationsWidget


class TestAnalyticsDashboard(unittest.TestCase):
    """Test cases for analytics dashboard functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the window during testing
        
        # Mock dependencies
        self.mock_config_manager = Mock()
        self.mock_db_manager = Mock()
        
        # Mock database connection
        self.mock_connection = Mock()
        self.mock_cursor = Mock()
        self.mock_db_manager.get_connection.return_value.__enter__.return_value = self.mock_connection
        self.mock_connection.cursor.return_value = self.mock_cursor
        
        # Mock config data
        self.mock_config_manager.get.return_value = {}
    
    def tearDown(self):
        """Clean up after tests."""
        self.root.destroy()
    
    def test_analytics_dashboard_initialization(self):
        """Test that analytics dashboard initializes correctly."""
        try:
            dashboard = AnalyticsDashboardPage(
                self.root, 
                self.mock_config_manager, 
                self.mock_db_manager
            )
            
            # Check that main components exist
            self.assertIsNotNone(dashboard.main_frame)
            self.assertIsNotNone(dashboard.notebook)
            self.assertIsNotNone(dashboard.performance_analytics)
            self.assertIsNotNone(dashboard.trend_analysis)
            self.assertIsNotNone(dashboard.cost_tracker)
            
            print("✓ Analytics dashboard initialization test passed")
            
        except Exception as e:
            self.fail(f"Analytics dashboard initialization failed: {e}")
    
    def test_optimization_widget_initialization(self):
        """Test that optimization recommendations widget initializes correctly."""
        try:
            widget = OptimizationRecommendationsWidget(
                self.root,
                self.mock_config_manager,
                self.mock_db_manager
            )
            
            # Check that main components exist
            self.assertIsNotNone(widget.main_frame)
            self.assertIsNotNone(widget.notebook)
            self.assertIsNotNone(widget.semantic_clustering)
            self.assertIsNotNone(widget.performance_analytics)
            
            print("✓ Optimization widget initialization test passed")
            
        except Exception as e:
            self.fail(f"Optimization widget initialization failed: {e}")
    
    @patch('services.analytics.performance_analytics.PerformanceAnalytics.generate_performance_insights')
    def test_generate_recommendations(self, mock_generate_insights):
        """Test recommendation generation."""
        try:
            # Mock insights data
            mock_insights = {
                "improvement_opportunities": [
                    {
                        "prompt_id": "test_prompt_1",
                        "recommendation": "Improve clarity",
                        "improvement_potential": "high",
                        "current_score": 0.5,
                        "opportunity_type": "low_performance"
                    }
                ],
                "patterns": [
                    {
                        "pattern_description": "Use examples",
                        "pattern_type": "structural",
                        "frequency": 5,
                        "avg_performance_boost": 0.1
                    }
                ],
                "summary": {
                    "overall_avg_score": 0.7,
                    "overall_avg_cost": 0.005
                }
            }
            mock_generate_insights.return_value = mock_insights
            
            widget = OptimizationRecommendationsWidget(
                self.root,
                self.mock_config_manager,
                self.mock_db_manager
            )
            
            # Test recommendation generation
            widget.generate_recommendations()
            
            # Check that recommendations were generated
            self.assertGreater(len(widget.current_recommendations), 0)
            
            print("✓ Recommendation generation test passed")
            
        except Exception as e:
            self.fail(f"Recommendation generation test failed: {e}")
    
    @patch('services.analytics.semantic_clustering.SemanticClustering.categorize_prompts_by_intent')
    def test_generate_clusters(self, mock_categorize):
        """Test cluster generation."""
        try:
            # Mock intent categories
            mock_category = Mock()
            mock_category.category_id = "intent_analysis"
            mock_category.name = "Analysis"
            mock_category.prompt_count = 5
            mock_category.avg_performance = 0.8
            
            mock_categorize.return_value = [mock_category]
            
            widget = OptimizationRecommendationsWidget(
                self.root,
                self.mock_config_manager,
                self.mock_db_manager
            )
            
            # Test cluster generation
            widget.generate_clusters()
            
            # Check that clusters were generated
            self.assertGreater(len(widget.current_clusters), 0)
            
            print("✓ Cluster generation test passed")
            
        except Exception as e:
            self.fail(f"Cluster generation test failed: {e}")
    
    def test_export_functionality(self):
        """Test export functionality."""
        try:
            widget = OptimizationRecommendationsWidget(
                self.root,
                self.mock_config_manager,
                self.mock_db_manager
            )
            
            # Add some mock data
            widget.current_recommendations = [
                {
                    "priority": "high",
                    "type": "performance",
                    "prompt_id": "test_prompt",
                    "recommendation": "Test recommendation",
                    "expected_impact": "high",
                    "effort": "medium",
                    "details": "Test details",
                    "rationale": "Test rationale"
                }
            ]
            
            widget.current_clusters = [
                {
                    "name": "Test Cluster",
                    "intent": "analysis",
                    "prompt_count": 3,
                    "avg_performance": 0.8,
                    "similarity_threshold": 0.7
                }
            ]
            
            # Test different export formats
            for format_type in ["txt", "csv", "json"]:
                widget.export_format_var.set(format_type)
                content = widget._generate_export_content("both", format_type)
                self.assertIsNotNone(content)
                self.assertGreater(len(content), 0)
            
            print("✓ Export functionality test passed")
            
        except Exception as e:
            self.fail(f"Export functionality test failed: {e}")
    
    def test_performance_metrics_display(self):
        """Test performance metrics display functionality."""
        try:
            dashboard = AnalyticsDashboardPage(
                self.root,
                self.mock_config_manager,
                self.mock_db_manager
            )
            
            # Mock performance metrics
            mock_metrics = Mock()
            mock_metrics.avg_score = 0.75
            mock_metrics.success_rate = 0.85
            mock_metrics.execution_count = 100
            mock_metrics.avg_response_time = 1500
            mock_metrics.score_variance = 0.05
            mock_metrics.quality_trend = "improving"
            
            # Test metrics update
            dashboard.update_performance_metrics(mock_metrics)
            
            # Verify metrics were updated (basic check)
            self.assertIsNotNone(dashboard.perf_metric_labels)
            
            print("✓ Performance metrics display test passed")
            
        except Exception as e:
            self.fail(f"Performance metrics display test failed: {e}")


def run_tests():
    """Run all analytics dashboard tests."""
    print("Running Analytics Dashboard Tests...")
    print("=" * 50)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAnalyticsDashboard)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=0)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print(f"✓ All {result.testsRun} analytics dashboard tests passed!")
    else:
        print(f"✗ {len(result.failures + result.errors)} test(s) failed out of {result.testsRun}")
        
        if result.failures:
            print("\nFailures:")
            for test, traceback in result.failures:
                print(f"- {test}: {traceback}")
        
        if result.errors:
            print("\nErrors:")
            for test, traceback in result.errors:
                print(f"- {test}: {traceback}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)