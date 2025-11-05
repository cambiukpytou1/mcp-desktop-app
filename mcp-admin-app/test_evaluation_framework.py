"""
Unit Tests for Evaluation Framework
==================================

Test suite for multi-model testing, scoring algorithms, and cost tracking accuracy.
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

# Import evaluation framework components
try:
    from services.evaluation.multi_model_testing import (
        MultiModelTestingInfrastructure, TestConfiguration, TestSession
    )
    from services.evaluation.scoring_engine import (
        ScoringEngine, ScoringRubric, ScoringCriterion, EvaluationResult,
        RuleBasedEvaluator, StatisticalEvaluator, LLMBasedEvaluator,
        ScoreType, EvaluatorType
    )
    from services.evaluation.cost_tracking import (
        CostTracker, TokenCounter, CostEstimator, CostAlert, RealTimeTokenCount
    )
    from models.llm import LLMProviderConfig, ModelConfig, LLMUsageRecord, TestStatus, TestType
    from models.base import LLMProviderType, ErrorType
except ImportError as e:
    print(f"Import error: {e}")
    print("Creating minimal test implementation...")
    
    # Create minimal implementations for testing
    class MockTestConfiguration:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    
    class MockTestSession:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    
    TestConfiguration = MockTestConfiguration
    TestSession = MockTestSession


class MockLLMProvider(BaseLLMProvider):
    """Mock LLM provider for testing."""
    
    def __init__(self, config, response_content="Test response", response_cost=0.01):
        super().__init__(config)
        self.response_content = response_content
        self.response_cost = response_cost
        self.call_count = 0
        self._initialized = True
    
    async def initialize(self) -> bool:
        return True
    
    def is_initialized(self) -> bool:
        return self._initialized
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        self.call_count += 1
        return LLMResponse(
            content=self.response_content,
            model_id=request.model_id,
            provider_id=self.config.id,
            input_tokens=len(request.prompt.split()) * 1.3,
            output_tokens=len(self.response_content.split()) * 1.3,
            total_tokens=len(request.prompt.split()) * 1.3 + len(self.response_content.split()) * 1.3,
            response_time=0.5,
            cost=self.response_cost,
            success=True
        )
    
    async def test_connection(self) -> bool:
        return True
    
    def get_available_models(self):
        return [ModelConfig(
            model_id="test-model",
            display_name="Test Model",
            max_tokens=4096,
            input_cost_per_token=0.00001,
            output_cost_per_token=0.00002
        )]


class TestMultiModelTesting(unittest.TestCase):
    """Test multi-model execution and comparison functionality."""
    
    def setUp(self):
        self.config_manager = Mock()
        self.config_manager.get.return_value = {}
        
        self.db_manager = Mock()
        self.infrastructure = MultiModelTestingInfrastructure(self.config_manager, self.db_manager)
    
    def test_provider_management(self):
        """Test adding and removing providers."""
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
        
        # Test adding provider
        asyncio.run(self._test_add_provider(config))
        
        # Test removing provider
        result = self.infrastructure.remove_provider("test_provider")
        self.assertTrue(result)
        self.assertNotIn("test_provider", self.infrastructure.providers)
    
    async def _test_add_provider(self, config):
        """Helper method for async provider addition test."""
        with patch.object(self.infrastructure, '_create_provider') as mock_create:
            mock_provider = MockLLMProvider(config)
            mock_create.return_value = mock_provider
            
            result = await self.infrastructure.add_provider(config)
            self.assertTrue(result)
            self.assertIn("test_provider", self.infrastructure.providers)
    
    def test_test_configuration_creation(self):
        """Test creating test configurations."""
        config = self.infrastructure.create_test_configuration(
            prompt_template_id="test_prompt",
            provider_ids=["provider1", "provider2"],
            model_configs={"provider1": "model1", "provider2": "model2"},
            name="Test Configuration",
            iterations=3
        )
        
        self.assertEqual(config.prompt_template_id, "test_prompt")
        self.assertEqual(config.provider_configs, ["provider1", "provider2"])
        self.assertEqual(config.model_configs, {"provider1": "model1", "provider2": "model2"})
        self.assertEqual(config.iterations, 3)
        self.assertEqual(config.name, "Test Configuration")
    
    def test_test_execution(self):
        """Test executing test configurations."""
        asyncio.run(self._test_execution_async())
    
    async def _test_execution_async(self):
        """Async test execution helper."""
        # Add mock providers
        provider1 = MockLLMProvider(LLMProviderConfig(
            id="provider1", name="Provider 1", provider_type=LLMProviderType.OPENAI
        ), "Response from provider 1", 0.01)
        
        provider2 = MockLLMProvider(LLMProviderConfig(
            id="provider2", name="Provider 2", provider_type=LLMProviderType.ANTHROPIC
        ), "Response from provider 2", 0.02)
        
        self.infrastructure.providers["provider1"] = provider1
        self.infrastructure.providers["provider2"] = provider2
        
        # Create test configuration
        config = TestConfiguration(
            prompt_template_id="test_prompt",
            provider_configs=["provider1", "provider2"],
            model_configs={"provider1": "model1", "provider2": "model2"},
            iterations=2
        )
        
        # Execute test
        session = await self.infrastructure.execute_test_configuration(config)
        
        # Verify results
        self.assertEqual(session.status, TestStatus.COMPLETED)
        self.assertEqual(len(session.results), 4)  # 2 providers × 2 iterations
        self.assertEqual(session.successful_executions, 4)
        self.assertEqual(session.failed_executions, 0)
        self.assertGreater(session.total_cost, 0)
        
        # Verify provider calls
        self.assertEqual(provider1.call_count, 2)
        self.assertEqual(provider2.call_count, 2)
    
    def test_quick_test(self):
        """Test quick testing functionality."""
        asyncio.run(self._test_quick_test_async())
    
    async def _test_quick_test_async(self):
        """Async quick test helper."""
        # Add mock provider
        provider = MockLLMProvider(LLMProviderConfig(
            id="test_provider", name="Test Provider", provider_type=LLMProviderType.OPENAI
        ))
        self.infrastructure.providers["test_provider"] = provider
        
        # Run quick test
        responses = await self.infrastructure.run_quick_test(
            "Test prompt", ["test_provider"]
        )
        
        self.assertEqual(len(responses), 1)
        self.assertTrue(responses[0].success)
        self.assertEqual(responses[0].content, "Test response")
    
    def test_session_management(self):
        """Test session management functionality."""
        # Create mock session
        session = TestSession(name="Test Session")
        self.infrastructure.active_sessions[session.session_id] = session
        
        # Test getting session
        retrieved = self.infrastructure.get_test_session(session.session_id)
        self.assertEqual(retrieved.session_id, session.session_id)
        
        # Test getting active sessions
        active = self.infrastructure.get_active_sessions()
        self.assertEqual(len(active), 1)
        
        # Test canceling session
        session.status = TestStatus.RUNNING
        result = self.infrastructure.cancel_session(session.session_id)
        self.assertTrue(result)
        self.assertEqual(session.status, TestStatus.CANCELLED)


class TestScoringEngine(unittest.TestCase):
    """Test scoring algorithms and statistical analysis."""
    
    def setUp(self):
        self.config_manager = Mock()
        self.config_manager.get.return_value = {}
        self.config_manager.set = Mock()
        
        self.db_manager = Mock()
        self.scoring_engine = ScoringEngine(self.config_manager, self.db_manager)
    
    def test_rule_based_evaluator(self):
        """Test rule-based evaluation algorithms."""
        asyncio.run(self._test_rule_based_async())
    
    async def _test_rule_based_async(self):
        """Async rule-based evaluator test."""
        evaluator = RuleBasedEvaluator("test_rule_evaluator")
        
        # Test completeness evaluation
        response = LLMResponse(
            content="This is a comprehensive response with multiple sentences. It provides detailed information and covers various aspects of the topic.",
            model_id="test-model",
            provider_id="test-provider",
            input_tokens=50,
            output_tokens=100,
            total_tokens=150,
            response_time=1.0,
            cost=0.01,
            success=True
        )
        
        criterion = ScoringCriterion(
            name="Completeness",
            score_type=ScoreType.COMPLETENESS,
            min_score=0.0,
            max_score=10.0
        )
        
        score = await evaluator.evaluate(response, criterion)
        
        self.assertEqual(score.criterion_id, criterion.id)
        self.assertGreaterEqual(score.score, criterion.min_score)
        self.assertLessEqual(score.score, criterion.max_score)
        self.assertGreater(len(score.explanation), 0)
        self.assertEqual(score.evaluator_type, EvaluatorType.RULE_BASED)
    
    def test_statistical_evaluator(self):
        """Test statistical evaluation algorithms."""
        asyncio.run(self._test_statistical_async())
    
    async def _test_statistical_async(self):
        """Async statistical evaluator test."""
        evaluator = StatisticalEvaluator("test_stat_evaluator")
        
        # Test relevance evaluation with context
        response = LLMResponse(
            content="Machine learning algorithms include supervised learning, unsupervised learning, and reinforcement learning approaches.",
            model_id="test-model",
            provider_id="test-provider",
            input_tokens=20,
            output_tokens=40,
            total_tokens=60,
            response_time=0.8,
            cost=0.005,
            success=True
        )
        
        criterion = ScoringCriterion(
            name="Relevance",
            score_type=ScoreType.RELEVANCE,
            min_score=0.0,
            max_score=10.0
        )
        
        context = {
            "original_prompt": "Explain different types of machine learning algorithms"
        }
        
        score = await evaluator.evaluate(response, criterion, context)
        
        self.assertEqual(score.criterion_id, criterion.id)
        self.assertGreaterEqual(score.score, criterion.min_score)
        self.assertLessEqual(score.score, criterion.max_score)
        self.assertGreater(score.confidence, 0.0)
        self.assertEqual(score.evaluator_type, EvaluatorType.STATISTICAL)
    
    def test_llm_based_evaluator(self):
        """Test LLM-based evaluation."""
        asyncio.run(self._test_llm_based_async())
    
    async def _test_llm_based_async(self):
        """Async LLM-based evaluator test."""
        # Create mock evaluator provider
        mock_provider = MockLLMProvider(
            LLMProviderConfig(id="evaluator", name="Evaluator", provider_type=LLMProviderType.OPENAI),
            response_content="SCORE: 8.5\nCONFIDENCE: 0.9\nEXPLANATION: The response is well-structured and informative."
        )
        
        evaluator = LLMBasedEvaluator("test_llm_evaluator", {}, mock_provider)
        
        response = LLMResponse(
            content="This is a well-written response that addresses the question comprehensively.",
            model_id="test-model",
            provider_id="test-provider",
            input_tokens=30,
            output_tokens=60,
            total_tokens=90,
            response_time=1.2,
            cost=0.008,
            success=True
        )
        
        criterion = ScoringCriterion(
            name="Quality",
            score_type=ScoreType.COHERENCE,
            min_score=0.0,
            max_score=10.0
        )
        
        score = await evaluator.evaluate(response, criterion)
        
        self.assertEqual(score.criterion_id, criterion.id)
        self.assertEqual(score.score, 8.5)
        self.assertEqual(score.confidence, 0.9)
        self.assertIn("well-structured", score.explanation)
        self.assertEqual(score.evaluator_type, EvaluatorType.LLM_BASED)
    
    def test_rubric_creation_and_evaluation(self):
        """Test creating rubrics and running evaluations."""
        asyncio.run(self._test_rubric_evaluation_async())
    
    async def _test_rubric_evaluation_async(self):
        """Async rubric evaluation test."""
        # Create test rubric
        rubric = ScoringRubric(
            name="Test Rubric",
            description="Test evaluation rubric",
            criteria=[
                ScoringCriterion(
                    name="Clarity",
                    score_type=ScoreType.CLARITY,
                    weight=2.0,
                    evaluator_type=EvaluatorType.RULE_BASED
                ),
                ScoringCriterion(
                    name="Completeness",
                    score_type=ScoreType.COMPLETENESS,
                    weight=1.5,
                    evaluator_type=EvaluatorType.RULE_BASED
                )
            ]
        )
        
        # Add rubric to engine
        result = self.scoring_engine.create_rubric(rubric)
        self.assertTrue(result)
        
        # Test evaluation
        response = LLMResponse(
            content="This is a clear and complete response that addresses all aspects of the question with appropriate detail.",
            model_id="test-model",
            provider_id="test-provider",
            input_tokens=25,
            output_tokens=50,
            total_tokens=75,
            response_time=1.0,
            cost=0.006,
            success=True
        )
        
        evaluation = await self.scoring_engine.evaluate_response(response, rubric.id)
        
        self.assertEqual(evaluation.rubric_id, rubric.id)
        self.assertEqual(len(evaluation.scores), 2)  # Two criteria
        self.assertGreater(evaluation.overall_score, 0)
        self.assertGreater(evaluation.confidence, 0)
        self.assertGreater(evaluation.evaluation_time, 0)
    
    def test_score_aggregation(self):
        """Test different score aggregation methods."""
        from services.evaluation.scoring_engine import EvaluationScore
        
        # Create test scores
        scores = [
            EvaluationScore(criterion_id="c1", score=8.0, confidence=0.9),
            EvaluationScore(criterion_id="c2", score=6.0, confidence=0.8),
            EvaluationScore(criterion_id="c3", score=9.0, confidence=0.95)
        ]
        
        # Create rubric with different weights
        rubric = ScoringRubric(
            criteria=[
                ScoringCriterion(id="c1", weight=2.0),
                ScoringCriterion(id="c2", weight=1.0),
                ScoringCriterion(id="c3", weight=3.0)
            ],
            aggregation_method="weighted_average"
        )
        
        # Test weighted average
        overall_score = self.scoring_engine._calculate_overall_score(scores, rubric)
        expected = (8.0*2.0 + 6.0*1.0 + 9.0*3.0) / (2.0 + 1.0 + 3.0)
        self.assertAlmostEqual(overall_score, expected, places=2)
        
        # Test confidence calculation
        overall_confidence = self.scoring_engine._calculate_overall_confidence(scores)
        expected_confidence = (0.9 + 0.8 + 0.95) / 3
        self.assertAlmostEqual(overall_confidence, expected_confidence, places=2)


class TestCostTracking(unittest.TestCase):
    """Test cost tracking accuracy and functionality."""
    
    def setUp(self):
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        
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
        
        self.db_manager = Mock()
        self.db_manager.get_connection.return_value.__enter__ = Mock(return_value=sqlite3.connect(self.temp_db.name))
        self.db_manager.get_connection.return_value.__exit__ = Mock(return_value=None)
    
    def tearDown(self):
        os.unlink(self.temp_db.name)
    
    def test_token_counter_accuracy(self):
        """Test token counting accuracy."""
        counter = TokenCounter()
        
        # Start session
        session = counter.start_session("test_session", "openai", "gpt-4")
        self.assertEqual(session.input_tokens, 0)
        self.assertEqual(session.output_tokens, 0)
        self.assertEqual(session.actual_cost, 0.0)
        
        # Update with precise token counts
        counter.update_session("test_session", input_tokens=1000, output_tokens=500, actual_cost=0.06)
        
        updated_session = counter.get_session("test_session")
        self.assertEqual(updated_session.input_tokens, 1000)
        self.assertEqual(updated_session.output_tokens, 500)
        self.assertEqual(updated_session.actual_cost, 0.06)
        
        # Multiple updates should accumulate
        counter.update_session("test_session", input_tokens=200, output_tokens=100, actual_cost=0.012)
        
        final_session = counter.get_session("test_session")
        self.assertEqual(final_session.input_tokens, 1200)
        self.assertEqual(final_session.output_tokens, 600)
        self.assertEqual(final_session.actual_cost, 0.072)
    
    def test_cost_estimation_accuracy(self):
        """Test cost estimation accuracy."""
        estimator = CostEstimator(self.config_manager)
        
        # Test precise cost calculation
        estimate = estimator.estimate_cost("openai", "gpt-4", 1000, 500)
        
        expected_input_cost = 1000 * 0.00003  # 0.03
        expected_output_cost = 500 * 0.00006  # 0.03
        expected_total = 0.06
        
        self.assertEqual(estimate.input_cost, expected_input_cost)
        self.assertEqual(estimate.estimated_output_cost, expected_output_cost)
        self.assertEqual(estimate.total_estimated_cost, expected_total)
        self.assertEqual(estimate.confidence_level, 0.95)
        
        # Test edge cases
        zero_estimate = estimator.estimate_cost("openai", "gpt-4", 0, 0)
        self.assertEqual(zero_estimate.total_estimated_cost, 0.0)
        
        # Test large numbers
        large_estimate = estimator.estimate_cost("openai", "gpt-4", 100000, 50000)
        expected_large = 100000 * 0.00003 + 50000 * 0.00006
        self.assertEqual(large_estimate.total_estimated_cost, expected_large)
    
    def test_cost_tracking_integration(self):
        """Test end-to-end cost tracking accuracy."""
        tracker = CostTracker(self.config_manager, self.db_manager)
        
        # Start session
        session_id = tracker.start_session("openai", "gpt-4")
        self.assertIsNotNone(session_id)
        
        # Record usage
        usage_record = LLMUsageRecord(
            provider_id="openai",
            model_id="gpt-4",
            input_tokens=1500,
            output_tokens=750,
            estimated_cost=0.09,
            actual_cost=0.09,
            response_time_ms=1200,
            success=True,
            session_id=session_id
        )
        
        result = tracker.record_usage(usage_record)
        self.assertTrue(result)
        
        # Check session cost
        session_cost = tracker.get_session_cost(session_id)
        self.assertIsNotNone(session_cost)
        self.assertEqual(session_cost["input_tokens"], 1500)
        self.assertEqual(session_cost["output_tokens"], 750)
        self.assertEqual(session_cost["total_tokens"], 2250)
        self.assertEqual(session_cost["actual_cost"], 0.09)
        
        # End session
        final_session = tracker.end_session(session_id)
        self.assertIsNotNone(final_session)
        self.assertEqual(final_session.actual_cost, 0.09)
    
    def test_cost_alert_accuracy(self):
        """Test cost alert threshold accuracy."""
        tracker = CostTracker(self.config_manager, self.db_manager)
        
        # Create threshold alert
        alert = CostAlert(
            name="Test Threshold Alert",
            alert_type="threshold",
            threshold_value=0.10,
            time_window_minutes=60
        )
        
        result = tracker.create_alert(alert)
        self.assertTrue(result)
        
        # Test alert callback
        triggered_alerts = []
        def alert_callback(alert, context):
            triggered_alerts.append((alert, context))
        
        tracker.add_alert_callback(alert_callback)
        
        # Simulate usage that should trigger alert
        for i in range(5):
            usage = LLMUsageRecord(
                provider_id="openai",
                model_id="gpt-4",
                input_tokens=500,
                output_tokens=250,
                actual_cost=0.025,  # 5 × 0.025 = 0.125 > 0.10 threshold
                success=True
            )
            tracker.record_usage(usage)
        
        # Manually trigger alert check (normally done by background thread)
        tracker._check_alerts()
        
        # Verify alert was triggered
        self.assertGreater(len(triggered_alerts), 0)
        triggered_alert, context = triggered_alerts[0]
        self.assertEqual(triggered_alert.name, "Test Threshold Alert")
        self.assertGreaterEqual(context["current_cost"], 0.10)
    
    def test_cost_report_accuracy(self):
        """Test cost report generation accuracy."""
        tracker = CostTracker(self.config_manager, self.db_manager)
        
        # Record multiple usage records
        usage_records = [
            LLMUsageRecord(
                provider_id="openai",
                model_id="gpt-4",
                input_tokens=1000,
                output_tokens=500,
                actual_cost=0.06,
                success=True
            ),
            LLMUsageRecord(
                provider_id="openai",
                model_id="gpt-3.5-turbo",
                input_tokens=2000,
                output_tokens=1000,
                actual_cost=0.003,
                success=True
            ),
            LLMUsageRecord(
                provider_id="anthropic",
                model_id="claude-3",
                input_tokens=1500,
                output_tokens=750,
                actual_cost=0.045,
                success=True
            )
        ]
        
        for record in usage_records:
            tracker.record_usage(record)
        
        # Generate report
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=1)
        report = tracker.generate_cost_report(start_time, end_time)
        
        # Verify report accuracy
        self.assertEqual(report.total_requests, 3)
        self.assertAlmostEqual(report.total_cost, 0.108, places=3)  # 0.06 + 0.003 + 0.045
        self.assertEqual(report.total_tokens, 6750)  # Sum of all tokens
        
        # Verify provider breakdown
        self.assertIn("openai", report.provider_breakdown)
        self.assertIn("anthropic", report.provider_breakdown)
        
        openai_breakdown = report.provider_breakdown["openai"]
        self.assertEqual(openai_breakdown["requests"], 2)
        self.assertAlmostEqual(openai_breakdown["cost"], 0.063, places=3)
        
        anthropic_breakdown = report.provider_breakdown["anthropic"]
        self.assertEqual(anthropic_breakdown["requests"], 1)
        self.assertAlmostEqual(anthropic_breakdown["cost"], 0.045, places=3)
    
    def test_real_time_cost_monitoring(self):
        """Test real-time cost monitoring accuracy."""
        tracker = CostTracker(self.config_manager, self.db_manager)
        
        # Start multiple sessions
        session1 = tracker.start_session("openai", "gpt-4", "session1")
        session2 = tracker.start_session("anthropic", "claude-3", "session2")
        
        # Update sessions with costs
        tracker.token_counter.update_session("session1", input_tokens=1000, output_tokens=500, actual_cost=0.06)
        tracker.token_counter.update_session("session2", input_tokens=800, output_tokens=400, actual_cost=0.04)
        
        # Get real-time costs
        real_time_costs = tracker.get_real_time_costs()
        
        self.assertEqual(real_time_costs["active_sessions"], 2)
        self.assertAlmostEqual(real_time_costs["total_cost"], 0.10, places=2)
        self.assertEqual(real_time_costs["total_tokens"], 2700)  # 1500 + 1200
        
        # Verify session details
        sessions = real_time_costs["sessions"]
        self.assertEqual(len(sessions), 2)
        
        session1_data = next(s for s in sessions if s["session_id"] == "session1")
        self.assertEqual(session1_data["provider_id"], "openai")
        self.assertEqual(session1_data["model_id"], "gpt-4")
        self.assertEqual(session1_data["actual_cost"], 0.06)


def run_tests():
    """Run all evaluation framework tests."""
    # Create test suite
    loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTests(loader.loadTestsFromTestCase(TestMultiModelTesting))
    test_suite.addTests(loader.loadTestsFromTestCase(TestScoringEngine))
    test_suite.addTests(loader.loadTestsFromTestCase(TestCostTracking))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)