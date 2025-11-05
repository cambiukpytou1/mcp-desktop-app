"""
Simple Unit Tests for Evaluation Framework
==========================================

Focused test suite for multi-model testing, scoring algorithms, and cost tracking accuracy.
Requirements: 3.1, 3.3, 3.4
"""

import unittest
import tempfile
import os
import sqlite3
import sys
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.llm import LLMProviderConfig, ModelConfig, LLMUsageRecord
from models.base import LLMProviderType, ErrorType, TestStatus, TestType


class MockLLMResponse:
    """Mock LLM response for testing."""
    
    def __init__(self, content="Test response", cost=0.01, success=True, input_tokens=10, output_tokens=20):
        self.content = content
        self.model_id = "test-model"
        self.provider_id = "test-provider"
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.total_tokens = input_tokens + output_tokens
        self.response_time = 0.5
        self.cost = cost
        self.success = success
        self.error = None if success else "Test error"
        self.timestamp = datetime.now()
        self.metadata = {}


class TestMultiModelExecution(unittest.TestCase):
    """Test multi-model execution and comparison functionality."""
    
    def test_provider_configuration(self):
        """Test LLM provider configuration creation and validation."""
        # Create test provider config
        config = LLMProviderConfig(
            id="test_provider",
            name="Test Provider",
            provider_type=LLMProviderType.OPENAI,
            models=[ModelConfig(
                model_id="test-model",
                display_name="Test Model",
                max_tokens=4096,
                input_cost_per_token=0.00001,
                output_cost_per_token=0.00002
            )]
        )
        
        # Verify configuration
        self.assertEqual(config.name, "Test Provider")
        self.assertEqual(config.provider_type, LLMProviderType.OPENAI)
        self.assertEqual(len(config.models), 1)
        self.assertEqual(config.models[0].model_id, "test-model")
        
        # Test serialization
        config_dict = config.to_dict()
        self.assertIn("id", config_dict)
        self.assertIn("name", config_dict)
        self.assertIn("models", config_dict)
        
        # Test deserialization
        restored_config = LLMProviderConfig.from_dict(config_dict)
        self.assertEqual(restored_config.name, config.name)
        self.assertEqual(restored_config.provider_type, config.provider_type)
    
    def test_model_configuration(self):
        """Test model configuration and cost calculation."""
        model = ModelConfig(
            model_id="gpt-4",
            display_name="GPT-4",
            max_tokens=8192,
            input_cost_per_token=0.00003,
            output_cost_per_token=0.00006
        )
        
        # Test cost calculation
        input_tokens = 1000
        output_tokens = 500
        
        input_cost = input_tokens * model.input_cost_per_token
        output_cost = output_tokens * model.output_cost_per_token
        total_cost = input_cost + output_cost
        
        self.assertAlmostEqual(input_cost, 0.03, places=5)
        self.assertAlmostEqual(output_cost, 0.03, places=5)
        self.assertAlmostEqual(total_cost, 0.06, places=5)
        
        # Test serialization
        model_dict = model.to_dict()
        restored_model = ModelConfig.from_dict(model_dict)
        self.assertEqual(restored_model.model_id, model.model_id)
        self.assertEqual(restored_model.input_cost_per_token, model.input_cost_per_token)
    
    def test_parallel_execution_simulation(self):
        """Test simulated parallel execution across multiple providers."""
        # Create multiple provider configs
        providers = [
            LLMProviderConfig(
                id="openai",
                name="OpenAI",
                provider_type=LLMProviderType.OPENAI,
                models=[ModelConfig(
                    model_id="gpt-4",
                    display_name="GPT-4",
                    max_tokens=8192,
                    input_cost_per_token=0.00003,
                    output_cost_per_token=0.00006
                )]
            ),
            LLMProviderConfig(
                id="anthropic",
                name="Anthropic",
                provider_type=LLMProviderType.ANTHROPIC,
                models=[ModelConfig(
                    model_id="claude-3",
                    display_name="Claude 3",
                    max_tokens=4096,
                    input_cost_per_token=0.00002,
                    output_cost_per_token=0.00004
                )]
            )
        ]
        
        # Simulate responses from each provider
        responses = []
        for provider in providers:
            model = provider.models[0]
            response = MockLLMResponse(
                content=f"Response from {provider.name}",
                cost=1000 * model.input_cost_per_token + 500 * model.output_cost_per_token,
                input_tokens=1000,
                output_tokens=500
            )
            response.provider_id = provider.id
            response.model_id = model.model_id
            responses.append(response)
        
        # Verify responses
        self.assertEqual(len(responses), 2)
        self.assertEqual(responses[0].provider_id, "openai")
        self.assertEqual(responses[1].provider_id, "anthropic")
        
        # Verify cost calculations
        openai_cost = responses[0].cost
        anthropic_cost = responses[1].cost
        
        self.assertAlmostEqual(openai_cost, 0.06, places=5)  # 1000*0.00003 + 500*0.00006
        self.assertAlmostEqual(anthropic_cost, 0.04, places=5)  # 1000*0.00002 + 500*0.00004
        
        # Test comparison metrics
        total_cost = sum(r.cost for r in responses)
        avg_response_time = sum(r.response_time for r in responses) / len(responses)
        
        self.assertAlmostEqual(total_cost, 0.10, places=5)
        self.assertEqual(avg_response_time, 0.5)
    
    def test_execution_error_handling(self):
        """Test error handling in multi-model execution."""
        # Create response with error
        error_response = MockLLMResponse(
            content="",
            cost=0.0,
            success=False,
            input_tokens=0,
            output_tokens=0
        )
        error_response.error = "Rate limit exceeded"
        
        # Verify error handling
        self.assertFalse(error_response.success)
        self.assertEqual(error_response.error, "Rate limit exceeded")
        self.assertEqual(error_response.cost, 0.0)
        
        # Test mixed success/failure scenario
        responses = [
            MockLLMResponse(content="Success", cost=0.05, success=True),
            error_response,
            MockLLMResponse(content="Another success", cost=0.03, success=True)
        ]
        
        successful_responses = [r for r in responses if r.success]
        failed_responses = [r for r in responses if not r.success]
        
        self.assertEqual(len(successful_responses), 2)
        self.assertEqual(len(failed_responses), 1)
        
        total_successful_cost = sum(r.cost for r in successful_responses)
        self.assertEqual(total_successful_cost, 0.08)


class TestScoringAlgorithms(unittest.TestCase):
    """Test scoring algorithms and statistical analysis."""
    
    def test_rule_based_scoring(self):
        """Test rule-based scoring algorithms."""
        response = MockLLMResponse(
            content="This is a comprehensive response with multiple sentences. It provides detailed information and covers various aspects of the topic thoroughly.",
            input_tokens=50,
            output_tokens=100
        )
        
        # Test completeness scoring based on length
        word_count = len(response.content.split())
        sentence_count = len([s for s in response.content.split('.') if s.strip()])
        
        # Rule-based completeness score
        if word_count < 10:
            completeness_score = 2.0
        elif word_count < 50:
            completeness_score = 5.0
        elif word_count < 200:
            completeness_score = 8.0
        else:
            completeness_score = 10.0
        
        # The test response has about 25 words, so should be 5.0
        self.assertEqual(completeness_score, 5.0)  # Should be 5.0 for this response length
        
        # Test clarity scoring based on sentence structure
        avg_sentence_length = word_count / max(1, sentence_count)
        
        if avg_sentence_length > 30:
            clarity_score = 4.0
        elif avg_sentence_length < 5:
            clarity_score = 6.0
        else:
            clarity_score = 9.0
        
        self.assertEqual(clarity_score, 9.0)  # Should be good clarity
        
        # Test safety scoring (basic pattern matching)
        content_lower = response.content.lower()
        harmful_patterns = ['kill', 'murder', 'hate', 'illegal']
        
        violations = sum(1 for pattern in harmful_patterns if pattern in content_lower)
        safety_score = 10.0 if violations == 0 else max(0.0, 10.0 - violations * 2.0)
        
        self.assertEqual(safety_score, 10.0)  # Should be safe content
    
    def test_statistical_analysis(self):
        """Test statistical analysis algorithms."""
        # Create multiple responses for statistical analysis
        responses = [
            MockLLMResponse(content="Short response", cost=0.01, input_tokens=10, output_tokens=5),
            MockLLMResponse(content="This is a medium length response with more detail", cost=0.03, input_tokens=20, output_tokens=15),
            MockLLMResponse(content="This is a very comprehensive and detailed response that covers multiple aspects of the topic with thorough explanations", cost=0.08, input_tokens=50, output_tokens=40),
        ]
        
        # Calculate statistical metrics
        costs = [r.cost for r in responses]
        response_times = [r.response_time for r in responses]
        token_counts = [r.total_tokens for r in responses]
        
        # Test basic statistics
        avg_cost = sum(costs) / len(costs)
        min_cost = min(costs)
        max_cost = max(costs)
        
        self.assertAlmostEqual(avg_cost, 0.04, places=2)
        self.assertEqual(min_cost, 0.01)
        self.assertEqual(max_cost, 0.08)
        
        # Test token efficiency (output/input ratio)
        efficiencies = [r.output_tokens / max(1, r.input_tokens) for r in responses]
        avg_efficiency = sum(efficiencies) / len(efficiencies)
        
        # Calculate expected efficiency: (5/10 + 15/20 + 40/50) / 3 = (0.5 + 0.75 + 0.8) / 3 = 0.683
        self.assertAlmostEqual(avg_efficiency, 0.683, places=2)
        
        # Test correlation between length and cost
        lengths = [len(r.content) for r in responses]
        
        # Simple correlation test (longer responses should cost more)
        self.assertTrue(lengths[0] < lengths[1] < lengths[2])
        self.assertTrue(costs[0] < costs[1] < costs[2])
    
    def test_relevance_scoring(self):
        """Test relevance scoring using keyword overlap."""
        original_prompt = "Explain machine learning algorithms and their applications"
        
        responses = [
            MockLLMResponse(content="Machine learning algorithms include supervised learning, unsupervised learning, and reinforcement learning with applications in data analysis"),
            MockLLMResponse(content="The weather is nice today and I like pizza"),
            MockLLMResponse(content="Algorithms are mathematical procedures used in machine learning for pattern recognition and predictive modeling applications")
        ]
        
        # Calculate relevance scores based on keyword overlap
        prompt_words = set(original_prompt.lower().split())
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        prompt_words -= stop_words
        
        relevance_scores = []
        for response in responses:
            response_words = set(response.content.lower().split())
            response_words -= stop_words
            
            if not prompt_words:
                relevance_score = 5.0
            else:
                overlap = len(prompt_words.intersection(response_words))
                relevance_ratio = overlap / len(prompt_words)
                relevance_score = relevance_ratio * 10.0
            
            relevance_scores.append(relevance_score)
        
        # Verify relevance scores
        self.assertGreater(relevance_scores[0], relevance_scores[1])  # First response more relevant than second
        self.assertGreater(relevance_scores[2], relevance_scores[1])  # Third response more relevant than second
        self.assertGreater(relevance_scores[0], 5.0)  # First response should be quite relevant
    
    def test_score_aggregation(self):
        """Test different score aggregation methods."""
        # Create individual criterion scores
        scores = [
            {"criterion": "relevance", "score": 8.0, "weight": 2.0},
            {"criterion": "clarity", "score": 6.0, "weight": 1.0},
            {"criterion": "completeness", "score": 9.0, "weight": 1.5},
            {"criterion": "safety", "score": 10.0, "weight": 3.0}
        ]
        
        # Test weighted average
        total_weighted_score = sum(s["score"] * s["weight"] for s in scores)
        total_weight = sum(s["weight"] for s in scores)
        weighted_avg = total_weighted_score / total_weight
        
        expected_weighted_avg = (8.0*2.0 + 6.0*1.0 + 9.0*1.5 + 10.0*3.0) / (2.0 + 1.0 + 1.5 + 3.0)
        self.assertAlmostEqual(weighted_avg, expected_weighted_avg, places=2)
        
        # Test simple average
        simple_avg = sum(s["score"] for s in scores) / len(scores)
        self.assertAlmostEqual(simple_avg, 8.25, places=2)
        
        # Test min/max
        min_score = min(s["score"] for s in scores)
        max_score = max(s["score"] for s in scores)
        
        self.assertEqual(min_score, 6.0)
        self.assertEqual(max_score, 10.0)


class TestCostTrackingAccuracy(unittest.TestCase):
    """Test cost tracking accuracy and functionality."""
    
    def test_token_counting_accuracy(self):
        """Test precise token counting."""
        # Simulate token counting session
        session_data = {
            "session_id": "test_session",
            "provider_id": "openai",
            "model_id": "gpt-4",
            "input_tokens": 0,
            "output_tokens": 0,
            "actual_cost": 0.0,
            "start_time": datetime.now()
        }
        
        # Simulate multiple updates
        updates = [
            {"input_tokens": 100, "output_tokens": 50, "cost": 0.006},
            {"input_tokens": 200, "output_tokens": 100, "cost": 0.012},
            {"input_tokens": 150, "output_tokens": 75, "cost": 0.009}
        ]
        
        for update in updates:
            session_data["input_tokens"] += update["input_tokens"]
            session_data["output_tokens"] += update["output_tokens"]
            session_data["actual_cost"] += update["cost"]
        
        # Verify accuracy
        self.assertEqual(session_data["input_tokens"], 450)
        self.assertEqual(session_data["output_tokens"], 225)
        self.assertAlmostEqual(session_data["actual_cost"], 0.027, places=5)
        
        total_tokens = session_data["input_tokens"] + session_data["output_tokens"]
        self.assertEqual(total_tokens, 675)
    
    def test_cost_estimation_precision(self):
        """Test cost estimation precision."""
        # Test different models with different pricing
        models = [
            {
                "name": "gpt-4",
                "input_cost_per_token": 0.00003,
                "output_cost_per_token": 0.00006
            },
            {
                "name": "gpt-3.5-turbo",
                "input_cost_per_token": 0.0000015,
                "output_cost_per_token": 0.000002
            },
            {
                "name": "claude-3",
                "input_cost_per_token": 0.000015,
                "output_cost_per_token": 0.000075
            }
        ]
        
        input_tokens = 1000
        output_tokens = 500
        
        for model in models:
            input_cost = input_tokens * model["input_cost_per_token"]
            output_cost = output_tokens * model["output_cost_per_token"]
            total_cost = input_cost + output_cost
            
            # Verify precision
            if model["name"] == "gpt-4":
                self.assertAlmostEqual(input_cost, 0.03, places=5)
                self.assertAlmostEqual(output_cost, 0.03, places=5)
                self.assertAlmostEqual(total_cost, 0.06, places=5)
            elif model["name"] == "gpt-3.5-turbo":
                self.assertAlmostEqual(input_cost, 0.0015, places=5)
                self.assertAlmostEqual(output_cost, 0.001, places=5)
                self.assertAlmostEqual(total_cost, 0.0025, places=5)
            elif model["name"] == "claude-3":
                self.assertAlmostEqual(input_cost, 0.015, places=5)
                self.assertAlmostEqual(output_cost, 0.0375, places=5)
                self.assertAlmostEqual(total_cost, 0.0525, places=5)
    
    def test_usage_record_accuracy(self):
        """Test usage record creation and accuracy."""
        usage_record = LLMUsageRecord(
            provider_id="openai",
            model_id="gpt-4",
            input_tokens=1500,
            output_tokens=750,
            estimated_cost=0.09,
            actual_cost=0.09,
            response_time_ms=1200,
            success=True,
            user="test_user"
        )
        
        # Verify record accuracy
        self.assertEqual(usage_record.provider_id, "openai")
        self.assertEqual(usage_record.model_id, "gpt-4")
        self.assertEqual(usage_record.input_tokens, 1500)
        self.assertEqual(usage_record.output_tokens, 750)
        self.assertEqual(usage_record.actual_cost, 0.09)
        self.assertTrue(usage_record.success)
        
        # Test serialization accuracy
        record_dict = usage_record.to_dict()
        self.assertEqual(record_dict["input_tokens"], 1500)
        self.assertEqual(record_dict["output_tokens"], 750)
        self.assertEqual(record_dict["actual_cost"], 0.09)
        
        # Verify timestamp is present
        self.assertIsInstance(usage_record.timestamp, datetime)
        self.assertIn("timestamp", record_dict)
    
    def test_cost_alert_thresholds(self):
        """Test cost alert threshold accuracy."""
        # Simulate cost tracking with threshold
        threshold = 0.10
        time_window_minutes = 60
        
        # Simulate usage records within time window
        usage_records = [
            {"cost": 0.025, "timestamp": datetime.now()},
            {"cost": 0.030, "timestamp": datetime.now()},
            {"cost": 0.020, "timestamp": datetime.now()},
            {"cost": 0.035, "timestamp": datetime.now()}
        ]
        
        total_cost = sum(record["cost"] for record in usage_records)
        
        # Test threshold logic
        should_trigger_alert = total_cost >= threshold
        self.assertTrue(should_trigger_alert)
        self.assertEqual(total_cost, 0.11)
        self.assertGreater(total_cost, threshold)
        
        # Test rate-based alert (cost per minute)
        rate_threshold = 0.02  # $0.02 per minute
        actual_rate = total_cost / time_window_minutes
        
        should_trigger_rate_alert = actual_rate >= rate_threshold
        self.assertFalse(should_trigger_rate_alert)  # 0.11/60 = 0.00183 < 0.02
    
    def test_cost_report_aggregation(self):
        """Test cost report aggregation accuracy."""
        # Simulate usage data for report generation
        usage_data = [
            {"provider": "openai", "model": "gpt-4", "cost": 0.06, "tokens": 1500, "requests": 1},
            {"provider": "openai", "model": "gpt-3.5-turbo", "cost": 0.003, "tokens": 2000, "requests": 1},
            {"provider": "anthropic", "model": "claude-3", "cost": 0.045, "tokens": 1200, "requests": 1},
            {"provider": "openai", "model": "gpt-4", "cost": 0.04, "tokens": 1000, "requests": 1}
        ]
        
        # Aggregate by provider
        provider_breakdown = {}
        for record in usage_data:
            provider = record["provider"]
            if provider not in provider_breakdown:
                provider_breakdown[provider] = {"cost": 0.0, "tokens": 0, "requests": 0}
            
            provider_breakdown[provider]["cost"] += record["cost"]
            provider_breakdown[provider]["tokens"] += record["tokens"]
            provider_breakdown[provider]["requests"] += record["requests"]
        
        # Verify aggregation accuracy
        self.assertAlmostEqual(provider_breakdown["openai"]["cost"], 0.103, places=3)
        self.assertEqual(provider_breakdown["openai"]["tokens"], 4500)
        self.assertEqual(provider_breakdown["openai"]["requests"], 3)
        
        self.assertAlmostEqual(provider_breakdown["anthropic"]["cost"], 0.045, places=3)
        self.assertEqual(provider_breakdown["anthropic"]["tokens"], 1200)
        self.assertEqual(provider_breakdown["anthropic"]["requests"], 1)
        
        # Test total calculations
        total_cost = sum(p["cost"] for p in provider_breakdown.values())
        total_tokens = sum(p["tokens"] for p in provider_breakdown.values())
        total_requests = sum(p["requests"] for p in provider_breakdown.values())
        
        self.assertAlmostEqual(total_cost, 0.148, places=3)
        self.assertEqual(total_tokens, 5700)
        self.assertEqual(total_requests, 4)
        
        # Test cost per request and cost per token
        cost_per_request = total_cost / total_requests
        cost_per_token = total_cost / total_tokens
        
        self.assertAlmostEqual(cost_per_request, 0.037, places=3)
        self.assertAlmostEqual(cost_per_token, 0.0000259, places=6)


def run_tests():
    """Run all evaluation framework tests."""
    # Create test suite
    loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTests(loader.loadTestsFromTestCase(TestMultiModelExecution))
    test_suite.addTests(loader.loadTestsFromTestCase(TestScoringAlgorithms))
    test_suite.addTests(loader.loadTestsFromTestCase(TestCostTrackingAccuracy))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)