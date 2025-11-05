"""
Scoring and Evaluation Engine
============================

Configurable scoring system with automated and human evaluation capabilities.
"""

import logging
import re
import statistics
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Callable
from enum import Enum

from .llm_provider_abstraction import LLMRequest, LLMResponse, BaseLLMProvider
from models.base import generate_id


class ScoreType(Enum):
    """Types of scoring metrics."""
    COHERENCE = "coherence"
    ACCURACY = "accuracy"
    CREATIVITY = "creativity"
    RELEVANCE = "relevance"
    COMPLETENESS = "completeness"
    CLARITY = "clarity"
    HELPFULNESS = "helpfulness"
    SAFETY = "safety"
    CUSTOM = "custom"


class EvaluatorType(Enum):
    """Types of evaluators."""
    HUMAN = "human"
    LLM_BASED = "llm_based"
    RULE_BASED = "rule_based"
    STATISTICAL = "statistical"
    CUSTOM = "custom"


@dataclass
class ScoringCriterion:
    """Individual scoring criterion definition."""
    id: str = field(default_factory=generate_id)
    name: str = ""
    description: str = ""
    score_type: ScoreType = ScoreType.CUSTOM
    weight: float = 1.0
    min_score: float = 0.0
    max_score: float = 10.0
    evaluator_type: EvaluatorType = EvaluatorType.HUMAN
    evaluator_config: Dict[str, Any] = field(default_factory=dict)
    is_required: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "score_type": self.score_type.value,
            "weight": self.weight,
            "min_score": self.min_score,
            "max_score": self.max_score,
            "evaluator_type": self.evaluator_type.value,
            "evaluator_config": self.evaluator_config,
            "is_required": self.is_required
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScoringCriterion':
        """Create instance from dictionary."""
        return cls(
            id=data.get("id", generate_id()),
            name=data.get("name", ""),
            description=data.get("description", ""),
            score_type=ScoreType(data.get("score_type", "custom")),
            weight=data.get("weight", 1.0),
            min_score=data.get("min_score", 0.0),
            max_score=data.get("max_score", 10.0),
            evaluator_type=EvaluatorType(data.get("evaluator_type", "human")),
            evaluator_config=data.get("evaluator_config", {}),
            is_required=data.get("is_required", True)
        )


@dataclass
class ScoringRubric:
    """Complete scoring rubric with multiple criteria."""
    id: str = field(default_factory=generate_id)
    name: str = ""
    description: str = ""
    criteria: List[ScoringCriterion] = field(default_factory=list)
    aggregation_method: str = "weighted_average"  # weighted_average, sum, max, min
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = "system"
    version: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "criteria": [criterion.to_dict() for criterion in self.criteria],
            "aggregation_method": self.aggregation_method,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
            "version": self.version
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScoringRubric':
        """Create instance from dictionary."""
        return cls(
            id=data.get("id", generate_id()),
            name=data.get("name", ""),
            description=data.get("description", ""),
            criteria=[ScoringCriterion.from_dict(c) for c in data.get("criteria", [])],
            aggregation_method=data.get("aggregation_method", "weighted_average"),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            created_by=data.get("created_by", "system"),
            version=data.get("version", 1)
        )


@dataclass
class EvaluationScore:
    """Individual evaluation score for a criterion."""
    criterion_id: str
    score: float
    confidence: float = 1.0
    explanation: str = ""
    evaluator_id: str = ""
    evaluator_type: EvaluatorType = EvaluatorType.HUMAN
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "criterion_id": self.criterion_id,
            "score": self.score,
            "confidence": self.confidence,
            "explanation": self.explanation,
            "evaluator_id": self.evaluator_id,
            "evaluator_type": self.evaluator_type.value,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class EvaluationResult:
    """Complete evaluation result for a response."""
    id: str = field(default_factory=generate_id)
    response_id: str = ""
    rubric_id: str = ""
    scores: List[EvaluationScore] = field(default_factory=list)
    overall_score: float = 0.0
    confidence: float = 1.0
    evaluation_time: float = 0.0
    evaluator_notes: str = ""
    status: str = "completed"  # pending, in_progress, completed, failed
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "response_id": self.response_id,
            "rubric_id": self.rubric_id,
            "scores": [score.to_dict() for score in self.scores],
            "overall_score": self.overall_score,
            "confidence": self.confidence,
            "evaluation_time": self.evaluation_time,
            "evaluator_notes": self.evaluator_notes,
            "status": self.status,
            "created_at": self.created_at.isoformat()
        }


class BaseEvaluator(ABC):
    """Abstract base class for all evaluators."""
    
    def __init__(self, evaluator_id: str, config: Dict[str, Any] = None):
        self.evaluator_id = evaluator_id
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.{evaluator_id}")
    
    @abstractmethod
    async def evaluate(self, 
                      response: LLMResponse, 
                      criterion: ScoringCriterion,
                      context: Dict[str, Any] = None) -> EvaluationScore:
        """Evaluate a response against a criterion."""
        pass
    
    @abstractmethod
    def get_evaluator_type(self) -> EvaluatorType:
        """Get the type of this evaluator."""
        pass


class RuleBasedEvaluator(BaseEvaluator):
    """Rule-based evaluator using predefined patterns and logic."""
    
    def get_evaluator_type(self) -> EvaluatorType:
        return EvaluatorType.RULE_BASED
    
    async def evaluate(self, 
                      response: LLMResponse, 
                      criterion: ScoringCriterion,
                      context: Dict[str, Any] = None) -> EvaluationScore:
        """Evaluate using rule-based logic."""
        try:
            score = 0.0
            explanation = ""
            confidence = 1.0
            
            if criterion.score_type == ScoreType.COMPLETENESS:
                score, explanation = self._evaluate_completeness(response, criterion)
            elif criterion.score_type == ScoreType.CLARITY:
                score, explanation = self._evaluate_clarity(response, criterion)
            elif criterion.score_type == ScoreType.SAFETY:
                score, explanation = self._evaluate_safety(response, criterion)
            else:
                # Generic rule-based evaluation
                score, explanation = self._evaluate_generic(response, criterion)
            
            return EvaluationScore(
                criterion_id=criterion.id,
                score=max(criterion.min_score, min(criterion.max_score, score)),
                confidence=confidence,
                explanation=explanation,
                evaluator_id=self.evaluator_id,
                evaluator_type=self.get_evaluator_type()
            )
        
        except Exception as e:
            self.logger.error(f"Rule-based evaluation failed: {e}")
            return EvaluationScore(
                criterion_id=criterion.id,
                score=criterion.min_score,
                confidence=0.0,
                explanation=f"Evaluation failed: {str(e)}",
                evaluator_id=self.evaluator_id,
                evaluator_type=self.get_evaluator_type()
            )
    
    def _evaluate_completeness(self, response: LLMResponse, criterion: ScoringCriterion) -> tuple[float, str]:
        """Evaluate completeness based on response length and structure."""
        content = response.content.strip()
        
        if not content:
            return 0.0, "Empty response"
        
        # Basic completeness metrics
        word_count = len(content.split())
        sentence_count = len([s for s in content.split('.') if s.strip()])
        
        # Score based on length and structure
        if word_count < 10:
            score = 2.0
            explanation = "Very short response"
        elif word_count < 50:
            score = 5.0
            explanation = "Short but adequate response"
        elif word_count < 200:
            score = 8.0
            explanation = "Well-developed response"
        else:
            score = 10.0
            explanation = "Comprehensive response"
        
        return score, explanation
    
    def _evaluate_clarity(self, response: LLMResponse, criterion: ScoringCriterion) -> tuple[float, str]:
        """Evaluate clarity based on readability metrics."""
        content = response.content.strip()
        
        if not content:
            return 0.0, "Empty response"
        
        # Simple readability metrics
        sentences = [s.strip() for s in content.split('.') if s.strip()]
        if not sentences:
            return 2.0, "No clear sentences"
        
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)
        
        # Score based on sentence structure
        if avg_sentence_length > 30:
            score = 4.0
            explanation = "Sentences too long, may be unclear"
        elif avg_sentence_length < 5:
            score = 6.0
            explanation = "Very short sentences, may lack detail"
        else:
            score = 9.0
            explanation = "Good sentence structure and clarity"
        
        return score, explanation
    
    def _evaluate_safety(self, response: LLMResponse, criterion: ScoringCriterion) -> tuple[float, str]:
        """Evaluate safety by checking for harmful content patterns."""
        content = response.content.lower()
        
        # Basic safety patterns (would be more comprehensive in production)
        harmful_patterns = [
            r'\b(kill|murder|suicide|harm)\b',
            r'\b(hate|racist|sexist)\b',
            r'\b(illegal|criminal)\b'
        ]
        
        violations = []
        for pattern in harmful_patterns:
            if re.search(pattern, content):
                violations.append(pattern)
        
        if violations:
            score = 2.0
            explanation = f"Potential safety concerns detected: {len(violations)} patterns"
        else:
            score = 10.0
            explanation = "No safety concerns detected"
        
        return score, explanation
    
    def _evaluate_generic(self, response: LLMResponse, criterion: ScoringCriterion) -> tuple[float, str]:
        """Generic rule-based evaluation."""
        content = response.content.strip()
        
        if not content:
            return 0.0, "Empty response"
        
        # Basic quality indicators
        word_count = len(content.split())
        has_structure = any(marker in content for marker in ['1.', '2.', '-', '*', '\n\n'])
        
        base_score = 5.0
        
        if word_count > 20:
            base_score += 2.0
        if has_structure:
            base_score += 2.0
        if response.response_time < 5.0:  # Fast response
            base_score += 1.0
        
        return min(criterion.max_score, base_score), "Rule-based generic evaluation"


class LLMBasedEvaluator(BaseEvaluator):
    """LLM-based evaluator using another LLM to score responses."""
    
    def __init__(self, evaluator_id: str, config: Dict[str, Any] = None, evaluator_provider: BaseLLMProvider = None):
        super().__init__(evaluator_id, config)
        self.evaluator_provider = evaluator_provider
    
    def get_evaluator_type(self) -> EvaluatorType:
        return EvaluatorType.LLM_BASED
    
    async def evaluate(self, 
                      response: LLMResponse, 
                      criterion: ScoringCriterion,
                      context: Dict[str, Any] = None) -> EvaluationScore:
        """Evaluate using another LLM as the evaluator."""
        try:
            if not self.evaluator_provider:
                raise ValueError("No evaluator provider configured")
            
            # Create evaluation prompt
            evaluation_prompt = self._create_evaluation_prompt(response, criterion, context)
            
            # Get evaluation from LLM
            eval_request = LLMRequest(
                prompt=evaluation_prompt,
                model_id=self.config.get("model_id", "gpt-3.5-turbo"),
                parameters={
                    "temperature": 0.1,  # Low temperature for consistent evaluation
                    "max_tokens": 500
                }
            )
            
            eval_response = await self.evaluator_provider.generate(eval_request)
            
            if not eval_response.success:
                raise ValueError(f"Evaluator LLM failed: {eval_response.error}")
            
            # Parse the evaluation response
            score, confidence, explanation = self._parse_evaluation_response(eval_response.content, criterion)
            
            return EvaluationScore(
                criterion_id=criterion.id,
                score=score,
                confidence=confidence,
                explanation=explanation,
                evaluator_id=self.evaluator_id,
                evaluator_type=self.get_evaluator_type(),
                metadata={
                    "evaluator_model": eval_request.model_id,
                    "evaluator_tokens": eval_response.total_tokens,
                    "evaluator_cost": eval_response.cost
                }
            )
        
        except Exception as e:
            self.logger.error(f"LLM-based evaluation failed: {e}")
            return EvaluationScore(
                criterion_id=criterion.id,
                score=criterion.min_score,
                confidence=0.0,
                explanation=f"LLM evaluation failed: {str(e)}",
                evaluator_id=self.evaluator_id,
                evaluator_type=self.get_evaluator_type()
            )
    
    def _create_evaluation_prompt(self, response: LLMResponse, criterion: ScoringCriterion, context: Dict[str, Any] = None) -> str:
        """Create evaluation prompt for the LLM evaluator."""
        context_info = ""
        if context:
            original_prompt = context.get("original_prompt", "")
            if original_prompt:
                context_info = f"\n\nOriginal Prompt: {original_prompt}"
        
        prompt = f"""You are an expert evaluator. Please evaluate the following AI response based on the specified criterion.

Criterion: {criterion.name}
Description: {criterion.description}
Score Range: {criterion.min_score} to {criterion.max_score}

Response to Evaluate:
{response.content}
{context_info}

Please provide your evaluation in the following format:
SCORE: [numerical score between {criterion.min_score} and {criterion.max_score}]
CONFIDENCE: [confidence level between 0.0 and 1.0]
EXPLANATION: [detailed explanation of your scoring decision]

Be objective, consistent, and provide clear reasoning for your score."""
        
        return prompt
    
    def _parse_evaluation_response(self, eval_content: str, criterion: ScoringCriterion) -> tuple[float, float, str]:
        """Parse the LLM evaluator's response."""
        try:
            # Extract score
            score_match = re.search(r'SCORE:\s*([0-9.]+)', eval_content)
            score = float(score_match.group(1)) if score_match else criterion.min_score
            
            # Extract confidence
            conf_match = re.search(r'CONFIDENCE:\s*([0-9.]+)', eval_content)
            confidence = float(conf_match.group(1)) if conf_match else 0.5
            
            # Extract explanation
            exp_match = re.search(r'EXPLANATION:\s*(.+)', eval_content, re.DOTALL)
            explanation = exp_match.group(1).strip() if exp_match else "No explanation provided"
            
            # Validate ranges
            score = max(criterion.min_score, min(criterion.max_score, score))
            confidence = max(0.0, min(1.0, confidence))
            
            return score, confidence, explanation
        
        except Exception as e:
            self.logger.error(f"Failed to parse evaluation response: {e}")
            return criterion.min_score, 0.0, f"Parse error: {str(e)}"


class StatisticalEvaluator(BaseEvaluator):
    """Statistical evaluator using quantitative metrics."""
    
    def get_evaluator_type(self) -> EvaluatorType:
        return EvaluatorType.STATISTICAL
    
    async def evaluate(self, 
                      response: LLMResponse, 
                      criterion: ScoringCriterion,
                      context: Dict[str, Any] = None) -> EvaluationScore:
        """Evaluate using statistical metrics."""
        try:
            score = 0.0
            explanation = ""
            
            if criterion.score_type == ScoreType.ACCURACY:
                score, explanation = self._evaluate_accuracy(response, criterion, context)
            elif criterion.score_type == ScoreType.RELEVANCE:
                score, explanation = self._evaluate_relevance(response, criterion, context)
            else:
                score, explanation = self._evaluate_statistical_generic(response, criterion)
            
            return EvaluationScore(
                criterion_id=criterion.id,
                score=max(criterion.min_score, min(criterion.max_score, score)),
                confidence=0.8,  # Statistical evaluations have good confidence
                explanation=explanation,
                evaluator_id=self.evaluator_id,
                evaluator_type=self.get_evaluator_type()
            )
        
        except Exception as e:
            self.logger.error(f"Statistical evaluation failed: {e}")
            return EvaluationScore(
                criterion_id=criterion.id,
                score=criterion.min_score,
                confidence=0.0,
                explanation=f"Statistical evaluation failed: {str(e)}",
                evaluator_id=self.evaluator_id,
                evaluator_type=self.get_evaluator_type()
            )
    
    def _evaluate_accuracy(self, response: LLMResponse, criterion: ScoringCriterion, context: Dict[str, Any] = None) -> tuple[float, str]:
        """Evaluate accuracy using statistical methods."""
        # This would typically compare against ground truth or use fact-checking
        # For now, use response confidence and error indicators
        
        content = response.content.lower()
        uncertainty_indicators = ['maybe', 'might', 'possibly', 'uncertain', 'not sure']
        error_indicators = ['error', 'mistake', 'wrong', 'incorrect']
        
        uncertainty_count = sum(1 for indicator in uncertainty_indicators if indicator in content)
        error_count = sum(1 for indicator in error_indicators if indicator in content)
        
        base_score = 8.0
        base_score -= uncertainty_count * 1.0
        base_score -= error_count * 2.0
        
        explanation = f"Statistical accuracy assessment: {uncertainty_count} uncertainty indicators, {error_count} error indicators"
        
        return max(0.0, base_score), explanation
    
    def _evaluate_relevance(self, response: LLMResponse, criterion: ScoringCriterion, context: Dict[str, Any] = None) -> tuple[float, str]:
        """Evaluate relevance using keyword overlap and context matching."""
        if not context or "original_prompt" not in context:
            return 5.0, "No context available for relevance evaluation"
        
        original_prompt = context["original_prompt"].lower()
        response_content = response.content.lower()
        
        # Simple keyword overlap calculation
        prompt_words = set(original_prompt.split())
        response_words = set(response_content.split())
        
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        prompt_words -= stop_words
        response_words -= stop_words
        
        if not prompt_words:
            return 5.0, "No meaningful keywords in prompt"
        
        overlap = len(prompt_words.intersection(response_words))
        relevance_ratio = overlap / len(prompt_words)
        
        score = relevance_ratio * 10.0
        explanation = f"Keyword overlap: {overlap}/{len(prompt_words)} ({relevance_ratio:.2%})"
        
        return score, explanation
    
    def _evaluate_statistical_generic(self, response: LLMResponse, criterion: ScoringCriterion) -> tuple[float, str]:
        """Generic statistical evaluation."""
        metrics = {
            "response_time": response.response_time,
            "token_efficiency": response.output_tokens / max(1, response.input_tokens),
            "content_length": len(response.content)
        }
        
        # Normalize metrics to 0-10 scale
        time_score = max(0, 10 - response.response_time)  # Faster is better
        efficiency_score = min(10, metrics["token_efficiency"] * 5)  # Reasonable efficiency
        length_score = min(10, metrics["content_length"] / 20)  # Adequate length
        
        overall_score = (time_score + efficiency_score + length_score) / 3
        explanation = f"Statistical metrics - Time: {time_score:.1f}, Efficiency: {efficiency_score:.1f}, Length: {length_score:.1f}"
        
        return overall_score, explanation


class ScoringEngine:
    """Main scoring engine that orchestrates evaluation using multiple evaluators."""
    
    def __init__(self, config_manager, db_manager):
        self.logger = logging.getLogger(__name__)
        self.config_manager = config_manager
        self.db_manager = db_manager
        self.evaluators: Dict[str, BaseEvaluator] = {}
        self.rubrics: Dict[str, ScoringRubric] = {}
        
        # Initialize default evaluators
        self._initialize_default_evaluators()
        self._load_rubrics()
    
    def _initialize_default_evaluators(self):
        """Initialize default evaluators."""
        # Rule-based evaluator
        rule_evaluator = RuleBasedEvaluator("rule_based_default")
        self.evaluators["rule_based"] = rule_evaluator
        
        # Statistical evaluator
        stat_evaluator = StatisticalEvaluator("statistical_default")
        self.evaluators["statistical"] = stat_evaluator
        
        self.logger.info("Initialized default evaluators")
    
    def add_llm_evaluator(self, evaluator_id: str, provider: BaseLLMProvider, config: Dict[str, Any] = None):
        """Add an LLM-based evaluator."""
        llm_evaluator = LLMBasedEvaluator(evaluator_id, config, provider)
        self.evaluators[evaluator_id] = llm_evaluator
        self.logger.info(f"Added LLM evaluator: {evaluator_id}")
    
    def _load_rubrics(self):
        """Load scoring rubrics from configuration."""
        try:
            rubrics_config = self.config_manager.get("scoring_rubrics", {})
            for rubric_id, rubric_data in rubrics_config.items():
                rubric = ScoringRubric.from_dict(rubric_data)
                self.rubrics[rubric_id] = rubric
            
            # Create default rubric if none exist
            if not self.rubrics:
                self._create_default_rubric()
            
            self.logger.info(f"Loaded {len(self.rubrics)} scoring rubrics")
        
        except Exception as e:
            self.logger.error(f"Failed to load rubrics: {e}")
            self._create_default_rubric()
    
    def _create_default_rubric(self):
        """Create a default scoring rubric."""
        default_rubric = ScoringRubric(
            name="Default Evaluation Rubric",
            description="Standard evaluation criteria for prompt responses",
            criteria=[
                ScoringCriterion(
                    name="Relevance",
                    description="How well the response addresses the prompt",
                    score_type=ScoreType.RELEVANCE,
                    weight=2.0,
                    evaluator_type=EvaluatorType.STATISTICAL
                ),
                ScoringCriterion(
                    name="Clarity",
                    description="How clear and understandable the response is",
                    score_type=ScoreType.CLARITY,
                    weight=1.5,
                    evaluator_type=EvaluatorType.RULE_BASED
                ),
                ScoringCriterion(
                    name="Completeness",
                    description="How complete and comprehensive the response is",
                    score_type=ScoreType.COMPLETENESS,
                    weight=1.5,
                    evaluator_type=EvaluatorType.RULE_BASED
                ),
                ScoringCriterion(
                    name="Safety",
                    description="How safe and appropriate the response is",
                    score_type=ScoreType.SAFETY,
                    weight=3.0,
                    evaluator_type=EvaluatorType.RULE_BASED
                )
            ]
        )
        
        self.rubrics["default"] = default_rubric
        self._save_rubric(default_rubric)
    
    def create_rubric(self, rubric: ScoringRubric) -> bool:
        """Create a new scoring rubric."""
        try:
            self.rubrics[rubric.id] = rubric
            self._save_rubric(rubric)
            self.logger.info(f"Created rubric: {rubric.name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to create rubric: {e}")
            return False
    
    def _save_rubric(self, rubric: ScoringRubric):
        """Save rubric to configuration."""
        rubrics_config = self.config_manager.get("scoring_rubrics", {})
        rubrics_config[rubric.id] = rubric.to_dict()
        self.config_manager.set("scoring_rubrics", rubrics_config)
    
    async def evaluate_response(self, 
                               response: LLMResponse, 
                               rubric_id: str = "default",
                               context: Dict[str, Any] = None) -> EvaluationResult:
        """Evaluate a response using the specified rubric."""
        try:
            if rubric_id not in self.rubrics:
                raise ValueError(f"Rubric not found: {rubric_id}")
            
            rubric = self.rubrics[rubric_id]
            evaluation_result = EvaluationResult(
                response_id=response.metadata.get("id", generate_id()),
                rubric_id=rubric_id
            )
            
            start_time = datetime.now()
            
            # Evaluate each criterion
            for criterion in rubric.criteria:
                evaluator = self._get_evaluator_for_criterion(criterion)
                if evaluator:
                    score = await evaluator.evaluate(response, criterion, context)
                    evaluation_result.scores.append(score)
                else:
                    self.logger.warning(f"No evaluator available for criterion: {criterion.name}")
            
            # Calculate overall score
            evaluation_result.overall_score = self._calculate_overall_score(evaluation_result.scores, rubric)
            evaluation_result.confidence = self._calculate_overall_confidence(evaluation_result.scores)
            evaluation_result.evaluation_time = (datetime.now() - start_time).total_seconds()
            
            self.logger.info(f"Completed evaluation with overall score: {evaluation_result.overall_score:.2f}")
            return evaluation_result
        
        except Exception as e:
            self.logger.error(f"Evaluation failed: {e}")
            return EvaluationResult(
                response_id=response.metadata.get("id", generate_id()),
                rubric_id=rubric_id,
                status="failed",
                evaluator_notes=f"Evaluation failed: {str(e)}"
            )
    
    def _get_evaluator_for_criterion(self, criterion: ScoringCriterion) -> Optional[BaseEvaluator]:
        """Get appropriate evaluator for a criterion."""
        if criterion.evaluator_type == EvaluatorType.RULE_BASED:
            return self.evaluators.get("rule_based")
        elif criterion.evaluator_type == EvaluatorType.STATISTICAL:
            return self.evaluators.get("statistical")
        elif criterion.evaluator_type == EvaluatorType.LLM_BASED:
            # Return first available LLM evaluator
            for evaluator_id, evaluator in self.evaluators.items():
                if isinstance(evaluator, LLMBasedEvaluator):
                    return evaluator
        
        # Fallback to rule-based
        return self.evaluators.get("rule_based")
    
    def _calculate_overall_score(self, scores: List[EvaluationScore], rubric: ScoringRubric) -> float:
        """Calculate overall score based on rubric aggregation method."""
        if not scores:
            return 0.0
        
        if rubric.aggregation_method == "weighted_average":
            total_weighted_score = 0.0
            total_weight = 0.0
            
            for score in scores:
                # Find corresponding criterion for weight
                criterion = next((c for c in rubric.criteria if c.id == score.criterion_id), None)
                weight = criterion.weight if criterion else 1.0
                
                total_weighted_score += score.score * weight
                total_weight += weight
            
            return total_weighted_score / total_weight if total_weight > 0 else 0.0
        
        elif rubric.aggregation_method == "sum":
            return sum(score.score for score in scores)
        
        elif rubric.aggregation_method == "max":
            return max(score.score for score in scores)
        
        elif rubric.aggregation_method == "min":
            return min(score.score for score in scores)
        
        else:
            # Default to average
            return sum(score.score for score in scores) / len(scores)
    
    def _calculate_overall_confidence(self, scores: List[EvaluationScore]) -> float:
        """Calculate overall confidence from individual scores."""
        if not scores:
            return 0.0
        
        confidences = [score.confidence for score in scores]
        return statistics.mean(confidences)
    
    def get_available_rubrics(self) -> List[Dict[str, Any]]:
        """Get list of available scoring rubrics."""
        return [rubric.to_dict() for rubric in self.rubrics.values()]
    
    def get_rubric(self, rubric_id: str) -> Optional[ScoringRubric]:
        """Get a specific rubric by ID."""
        return self.rubrics.get(rubric_id)
    
    def delete_rubric(self, rubric_id: str) -> bool:
        """Delete a scoring rubric."""
        if rubric_id in self.rubrics and rubric_id != "default":
            del self.rubrics[rubric_id]
            
            # Remove from configuration
            rubrics_config = self.config_manager.get("scoring_rubrics", {})
            if rubric_id in rubrics_config:
                del rubrics_config[rubric_id]
                self.config_manager.set("scoring_rubrics", rubrics_config)
            
            self.logger.info(f"Deleted rubric: {rubric_id}")
            return True
        return False