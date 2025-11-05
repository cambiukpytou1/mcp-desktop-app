"""
Test Cost Tracking and Monitoring System
========================================

Test suite for cost tracking, monitoring, and visualization functionality.
"""

import unittest
import tempfile
import os
import sqlite3
import sys
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.evaluation.cost_tracking import (
    CostTracker, TokenCounter, CostEstimator, CostAlert, RealTimeTokenCount
)
from services.evaluation.cost_visualization import CostVisualizationService
from models.llm import LLMUsageRecord, LLMProviderConfig, ModelConfig
from models.base import ErrorType, LLMProviderType


class TestTokenCounter(unittest.TestCase):
    """Test token counting functionality."""
    
    def setUp(self):
        self.counter = TokenCounter()
    
    def test_session_lifecycle(self):
        """Test complete session lifecycle."""
        # Start session
        session = self.counter.start_session("test_session", "openai", "gpt-4")
        self.assertIsNotNone(session)
        self.assertEqual(session.session_id, "test_session")
        self.assertEqual(session.provider_id, "openai")
        self.assertEqual(session.model_id, "gpt-4")
        
        # Update session
        updated = self.counter.update_session("test_session", input_tokens=100, output_tokens=50, actual_cost=0.05)
        self.assertIsNotNone(updated)
        self.assertEqual(updated.input_tokens, 100)
        self.assertEqual(updated.output_tokens, 50)
        self.assertEqual(updated.actual_cost, 0.05)
        
        # End session
        final = self.counter.end_session("test_session")
        self.assertIsNotNone(final)
        self.assertEqual(final.input_tokens, 100)
        self.assertEqual(final.output_tokens, 50)
        
        # Session should be removed
        self.assertIsNone(self.counter.get_session("test_session"))
    
    def test_multiple_sessions(self):
        """Test handling multiple concurrent sessions."""
        # Start multiple sessions
        session1 = self.counter.start_session("session1", "openai", "gpt-4")
        session2 = self.counter.start_session("session2", "anthropic", "claude-3")
        
        # Update both
        self.counter.update_session("session1", input_tokens=100, actual_cost=0.05)
        self.counter.update_session("session2", input_tokens=200, actual_cost=0.10)
        
        # Check all sessions
        all_sessions = self.counter.get_all_sessions()
        self.assertEqual(len(all_sessions), 2)
        
        # End one session
        self.counter.end_session("session1")
        all_sessions = self.counter.get_all_sessions()
        self.assertEqual(len(all_sessions), 1)
        self.assertEqual(all_sessions[0].session_id, "session2")


class TestCostEstimator(unittest.TestCase):
    """Test cost estimation functionality."""
    
    def setUp(self):
        self.config_manager = Mock()
        self.config_manager.get.return_value = {
            "openai": {
                "id": "openai",
                "name": "OpenAI",
                "provider_type": "openai",
                "models": [
                    {
                        "model_id": "gpt-4",
                        "display_name": "GPT-4",
                        "max_tokens": 8192,
                        "input_cost_per_token": 0.00003,
                        "output_cost_per_token": 0.00006,
                        "context_window": 8192
                    }
                ]
            }
        }
        self.estimator = CostEstimator(self.config_manager)
    
    def test_cost_estimation(self):
        """Test basic cost estimation."""
        estimate = self.estimator.estimate_cost("openai", "gpt-4", 1000, 500)
        
        expected_input_cost = 1000 * 0.00003
        expected_output_cost = 500 * 0.00006
        expected_total = expected_input_cost + expected_output_cost
        
        self.assertEqual(estimate.input_cost, expected_input_cost)
        self.assertEqual(estimate.estimated_output_cost, expected_output_cost)
        self.assertEqual(estimate.total_estimated_cost, expected_total)
        self.assertEqual(estimate.confidence_level, 0.95)
    
    def test_prompt_cost_estimation(self):
        """Test prompt-based cost estimation."""
        prompt = "This is a test prompt with multiple words"
        estimate = self.estimator.estimate_prompt_cost("openai", "gpt-4", prompt)
        
        self.assertGreater(estimate.total_estimated_cost, 0)
        self.assertGreater(estimate.confidence_level, 0)
    
    def test_unknown_provider(self):
        """Test estimation with unknown provider."""
        estimate = self.estimator.estimate_cost("unknown", "model", 1000, 500)
        
        self.assertEqual(estimate.total_estimated_cost, 0.0)
        self.assertEqual(estimate.confidence_level, 0.0)


class TestCostTracker(unittest.TestCase):
    """Test cost tracking functionality."""
    
    def setUp(self):
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        
        self.config_manager = Mock()
        self.config_manager.get.return_value = {}
        
        self.db_manager = Mock()
        self.db_manager.get_connection.return_value.__enter__ = Mock(return_value=sqlite3.connect(self.temp_db.name))
        self.db_manager.get_connection.return_value.__exit__ = Mock(return_value=None)
        
        self.tracker = CostTracker(self.config_manager, self.db_manager)
    
    def tearDown(self):
        os.unlink(self.temp_db.name)
    
    def test_usage_recording(self):
        """Test recording LLM usage."""
        usage_record = LLMUsageRecord(
            provider_id="openai",
            model_id="gpt-4",
            input_tokens=100,
            output_tokens=50,
            actual_cost=0.05,
            success=True
        )
        
        result = self.tracker.record_usage(usage_record)
        self.assertTrue(result)
    
    def test_session_management(self):
        """Test session management."""
        session_id = self.tracker.start_session("openai", "gpt-4")
        self.assertIsNotNone(session_id)
        
        session_cost = self.tracker.get_session_cost(session_id)
        self.assertIsNotNone(session_cost)
        self.assertEqual(session_cost["provider_id"], "openai")
        self.assertEqual(session_cost["model_id"], "gpt-4")
        
        final_session = self.tracker.end_session(session_id)
        self.assertIsNotNone(final_session)
    
    def test_alert_creation(self):
        """Test cost alert creation."""
        alert = CostAlert(
            name="Test Alert",
            alert_type="threshold",
            threshold_value=10.0,
            time_window_minutes=60
        )
        
        result = self.tracker.create_alert(alert)
        self.assertTrue(result)
        self.assertIn(alert.alert_id, self.tracker.alerts)
    
    def test_report_generation(self):
        """Test cost report generation."""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        report = self.tracker.generate_cost_report(start_time, end_time)
        
        self.assertIsNotNone(report)
        self.assertEqual(report.time_period_start, start_time)
        self.assertEqual(report.time_period_end, end_time)
        self.assertIsInstance(report.provider_breakdown, dict)
        self.assertIsInstance(report.model_breakdown, dict)


class TestCostVisualization(unittest.TestCase):
    """Test cost visualization functionality."""
    
    def setUp(self):
        self.cost_tracker = Mock()
        self.visualization = CostVisualizationService(self.cost_tracker)
    
    def test_dashboard_creation(self):
        """Test dashboard creation."""
        # Mock report data
        mock_report = Mock()
        mock_report.provider_breakdown = {
            "openai": {"cost": 5.0, "requests": 100, "tokens": 10000, "avg_response_time": 500}
        }
        mock_report.model_breakdown = {
            "openai:gpt-4": {"cost": 5.0, "requests": 100, "tokens": 10000}
        }
        mock_report.hourly_breakdown = [
            {"hour": "2024-01-01 10:00:00", "cost": 1.0, "requests": 20, "tokens": 2000}
        ]
        mock_report.total_cost = 5.0
        mock_report.total_requests = 100
        mock_report.total_tokens = 10000
        
        self.cost_tracker.generate_cost_report.return_value = mock_report
        self.cost_tracker.get_real_time_costs.return_value = {
            "active_sessions": 2,
            "total_cost": 1.0,
            "total_tokens": 1000,
            "sessions": []
        }
        
        dashboard = self.visualization.create_dashboard(24)
        
        self.assertIsNotNone(dashboard)
        self.assertGreater(len(dashboard.charts), 0)
        self.assertIn("total_cost", dashboard.metrics)
        self.assertIn("total_requests", dashboard.metrics)
    
    def test_chart_creation(self):
        """Test individual chart creation."""
        mock_report = Mock()
        mock_report.provider_breakdown = {
            "openai": {"cost": 5.0, "requests": 100, "tokens": 10000}
        }
        
        chart = self.visualization.create_cost_overview_chart(mock_report)
        
        self.assertEqual(chart.chart_type, "pie")
        self.assertEqual(chart.title, "Cost by Provider")
        self.assertGreater(len(chart.labels), 0)
        self.assertGreater(len(chart.datasets), 0)
    
    def test_cost_summary(self):
        """Test cost summary generation."""
        mock_report = Mock()
        mock_report.total_cost = 10.0
        mock_report.total_requests = 200
        mock_report.total_tokens = 20000
        mock_report.provider_breakdown = {"openai": {}}
        mock_report.model_breakdown = {"openai:gpt-4": {}}
        
        self.cost_tracker.generate_cost_report.return_value = mock_report
        self.cost_tracker.get_real_time_costs.return_value = {
            "active_sessions": 1,
            "total_cost": 0.5,
            "total_tokens": 500
        }
        
        summary = self.visualization.get_cost_summary(24)
        
        self.assertIn("historical", summary)
        self.assertIn("real_time", summary)
        self.assertIn("efficiency", summary)
        self.assertEqual(summary["historical"]["total_cost"], 10.0)


def run_tests():
    """Run all cost tracking tests."""
    # Create test suite
    loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTests(loader.loadTestsFromTestCase(TestTokenCounter))
    test_suite.addTests(loader.loadTestsFromTestCase(TestCostEstimator))
    test_suite.addTests(loader.loadTestsFromTestCase(TestCostTracker))
    test_suite.addTests(loader.loadTestsFromTestCase(TestCostVisualization))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)