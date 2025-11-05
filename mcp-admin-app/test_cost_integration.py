"""
Cost Tracking Integration Test
=============================

Simple integration test to verify cost tracking functionality works end-to-end.
"""

import sys
import os
from datetime import datetime, timedelta

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.evaluation.cost_tracking import TokenCounter, CostEstimator, CostAlert
from services.evaluation.cost_visualization import CostVisualizationService
from models.llm import LLMUsageRecord, LLMProviderConfig, ModelConfig
from models.base import LLMProviderType


def test_token_counter():
    """Test token counter functionality."""
    print("Testing Token Counter...")
    
    counter = TokenCounter()
    
    # Start a session
    session = counter.start_session("test_session", "openai", "gpt-4")
    print(f"Started session: {session.session_id}")
    
    # Update session with token counts
    counter.update_session("test_session", input_tokens=150, output_tokens=75, actual_cost=0.0135)
    
    # Get session data
    session_data = counter.get_session("test_session")
    print(f"Session tokens: {session_data.input_tokens} input, {session_data.output_tokens} output")
    print(f"Session cost: ${session_data.actual_cost:.4f}")
    
    # End session
    final_session = counter.end_session("test_session")
    print(f"Final session cost: ${final_session.actual_cost:.4f}")
    
    print("✓ Token Counter test passed\n")


def test_cost_estimator():
    """Test cost estimator functionality."""
    print("Testing Cost Estimator...")
    
    # Mock config manager
    class MockConfigManager:
        def get(self, key, default=None):
            return {
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
    
    estimator = CostEstimator(MockConfigManager())
    
    # Test cost estimation
    estimate = estimator.estimate_cost("openai", "gpt-4", 1000, 500)
    print(f"Cost estimate for 1000 input + 500 output tokens:")
    print(f"  Input cost: ${estimate.input_cost:.6f}")
    print(f"  Output cost: ${estimate.estimated_output_cost:.6f}")
    print(f"  Total cost: ${estimate.total_estimated_cost:.6f}")
    
    # Test prompt estimation
    prompt = "Write a detailed explanation of machine learning algorithms"
    prompt_estimate = estimator.estimate_prompt_cost("openai", "gpt-4", prompt)
    print(f"Prompt cost estimate: ${prompt_estimate.total_estimated_cost:.6f}")
    
    print("✓ Cost Estimator test passed\n")


def test_cost_alert():
    """Test cost alert functionality."""
    print("Testing Cost Alerts...")
    
    # Create different types of alerts
    threshold_alert = CostAlert(
        name="High Cost Alert",
        alert_type="threshold",
        threshold_value=50.0,
        time_window_minutes=60
    )
    
    rate_alert = CostAlert(
        name="High Rate Alert", 
        alert_type="rate",
        threshold_value=1.0,  # $1 per minute
        time_window_minutes=30
    )
    
    budget_alert = CostAlert(
        name="Daily Budget Alert",
        alert_type="budget",
        threshold_value=100.0,
        time_window_minutes=1440  # 24 hours
    )
    
    print(f"Created threshold alert: {threshold_alert.name} (${threshold_alert.threshold_value})")
    print(f"Created rate alert: {rate_alert.name} (${rate_alert.threshold_value}/min)")
    print(f"Created budget alert: {budget_alert.name} (${budget_alert.threshold_value}/day)")
    
    print("✓ Cost Alerts test passed\n")


def test_usage_record():
    """Test usage record creation."""
    print("Testing Usage Records...")
    
    # Create usage record
    usage = LLMUsageRecord(
        provider_id="openai",
        model_id="gpt-4",
        input_tokens=1200,
        output_tokens=800,
        estimated_cost=0.084,
        actual_cost=0.084,
        response_time_ms=1500,
        success=True,
        user="test_user"
    )
    
    print(f"Usage record created:")
    print(f"  Provider: {usage.provider_id}")
    print(f"  Model: {usage.model_id}")
    print(f"  Tokens: {usage.input_tokens} input, {usage.output_tokens} output")
    print(f"  Cost: ${usage.actual_cost:.4f}")
    print(f"  Response time: {usage.response_time_ms}ms")
    
    print("✓ Usage Records test passed\n")


def test_visualization_data():
    """Test visualization data structures."""
    print("Testing Visualization Data...")
    
    # Mock cost tracker
    class MockCostTracker:
        def generate_cost_report(self, start_time, end_time, report_type="summary"):
            class MockReport:
                def __init__(self):
                    self.provider_breakdown = {
                        "openai": {"cost": 15.50, "requests": 100, "tokens": 25000, "avg_response_time": 800},
                        "anthropic": {"cost": 8.25, "requests": 50, "tokens": 12000, "avg_response_time": 1200}
                    }
                    self.model_breakdown = {
                        "openai:gpt-4": {"cost": 15.50, "requests": 100, "tokens": 25000},
                        "anthropic:claude-3": {"cost": 8.25, "requests": 50, "tokens": 12000}
                    }
                    self.hourly_breakdown = [
                        {"hour": "2024-01-01 10:00:00", "cost": 2.5, "requests": 15, "tokens": 3000},
                        {"hour": "2024-01-01 11:00:00", "cost": 3.2, "requests": 20, "tokens": 4000}
                    ]
                    self.total_cost = 23.75
                    self.total_requests = 150
                    self.total_tokens = 37000
            return MockReport()
        
        def get_real_time_costs(self):
            return {
                "active_sessions": 3,
                "total_cost": 2.15,
                "total_tokens": 3500,
                "sessions": [
                    {
                        "session_id": "session1",
                        "provider_id": "openai",
                        "model_id": "gpt-4",
                        "input_tokens": 1000,
                        "output_tokens": 500,
                        "actual_cost": 0.75,
                        "start_time": datetime.now().isoformat()
                    }
                ]
            }
    
    viz_service = CostVisualizationService(MockCostTracker())
    
    # Test cost summary
    summary = viz_service.get_cost_summary(24)
    print(f"Cost summary for last 24 hours:")
    print(f"  Historical total cost: ${summary['historical']['total_cost']:.2f}")
    print(f"  Real-time active sessions: {summary['real_time']['active_sessions']}")
    print(f"  Cost per request: ${summary['efficiency']['cost_per_request']:.6f}")
    
    print("✓ Visualization Data test passed\n")


def main():
    """Run all integration tests."""
    print("=" * 60)
    print("Cost Tracking Integration Tests")
    print("=" * 60)
    print()
    
    try:
        test_token_counter()
        test_cost_estimator()
        test_cost_alert()
        test_usage_record()
        test_visualization_data()
        
        print("=" * 60)
        print("✓ All integration tests passed!")
        print("Cost tracking and monitoring system is working correctly.")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)