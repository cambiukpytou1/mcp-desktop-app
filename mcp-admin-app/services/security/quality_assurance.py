"""
Quality Assurance Framework for MCP Admin Application
====================================================

Framework for automated bias detection, hallucination analysis, and quality scoring.
"""

import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import statistics

from models.base import generate_id


class QualityIssueType(Enum):
    """Quality issue type enumeration."""
    BIAS_DETECTED = "bias_detected"
    HALLUCINATION_RISK = "hallucination_risk"
    COHERENCE_ISSUE = "coherence_issue"
    FACTUAL_ACCURACY = "factual_accuracy"
    LANGUAGE_QUALITY = "language_quality"
    ETHICAL_CONCERN = "ethical_concern"
    CULTURAL_SENSITIVITY = "cultural_sensitivity"


class QualitySeverity(Enum):
    """Quality issue severity enumeration."""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class QualityIssue:
    """Quality issue detection result."""
    id: str = field(default_factory=generate_id)
    issue_type: QualityIssueType = QualityIssueType.BIAS_DETECTED
    severity: QualitySeverity = QualitySeverity.MEDIUM
    title: str = ""
    description: str = ""
    location: Dict[str, Any] = field(default_factory=dict)
    evidence: str = ""
    suggestion: str = ""
    confidence: float = 0.8
    detected_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "issue_type": self.issue_type.value,
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "location": self.location,
            "evidence": self.evidence,
            "suggestion": self.suggestion,
            "confidence": self.confidence,
            "detected_at": self.detected_at.isoformat()
        }


@dataclass
class QualityMetrics:
    """Quality metrics for a prompt."""
    overall_score: float = 0.0
    bias_score: float = 0.0
    coherence_score: float = 0.0
    factual_score: float = 0.0
    language_score: float = 0.0
    ethical_score: float = 0.0
    hallucination_risk: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "overall_score": self.overall_score,
            "bias_score": self.bias_score,
            "coherence_score": self.coherence_score,
            "factual_score": self.factual_score,
            "language_score": self.language_score,
            "ethical_score": self.ethical_score,
            "hallucination_risk": self.hallucination_risk
        }


@dataclass
class QualityAssessmentResult:
    """Quality assessment result containing all detected issues and metrics."""
    assessment_id: str = field(default_factory=generate_id)
    prompt_id: str = ""
    prompt_version: str = ""
    issues: List[QualityIssue] = field(default_factory=list)
    metrics: QualityMetrics = field(default_factory=QualityMetrics)
    assessment_duration: float = 0.0
    assessed_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "assessment_id": self.assessment_id,
            "prompt_id": self.prompt_id,
            "prompt_version": self.prompt_version,
            "issues": [issue.to_dict() for issue in self.issues],
            "metrics": self.metrics.to_dict(),
            "assessment_duration": self.assessment_duration,
            "assessed_at": self.assessed_at.isoformat(),
            "issue_count": len(self.issues),
            "critical_issues": len([i for i in self.issues if i.severity == QualitySeverity.CRITICAL]),
            "high_issues": len([i for i in self.issues if i.severity == QualitySeverity.HIGH])
        }


class BiasDetector:
    """Bias detection component."""
    
    def __init__(self):
        """Initialize bias detector."""
        self.logger = logging.getLogger(__name__)
        self._init_bias_patterns()
    
    def _init_bias_patterns(self):
        """Initialize bias detection patterns."""
        self.bias_patterns = {
            "gender_bias": {
                "patterns": [
                    r'\b(?:he|she)\s+(?:is\s+)?(?:better|worse|more|less)\s+(?:at|in|with)',
                    r'\b(?:men|women|boys|girls)\s+(?:are|can\'t|cannot|should|shouldn\'t)',
                    r'\b(?:male|female)\s+(?:dominated|oriented|typical)'
                ],
                "description": "Gender-based stereotyping or assumptions",
                "severity": QualitySeverity.HIGH
            },
            "racial_bias": {
                "patterns": [
                    r'\b(?:race|ethnicity|nationality)\s+(?:determines|affects|influences)',
                    r'\b(?:typical|characteristic)\s+(?:of|for)\s+(?:asian|black|white|hispanic|latino)',
                    r'\b(?:all|most)\s+(?:asians|blacks|whites|hispanics|latinos)\s+(?:are|do|have)'
                ],
                "description": "Racial or ethnic stereotyping",
                "severity": QualitySeverity.CRITICAL
            },
            "age_bias": {
                "patterns": [
                    r'\b(?:old|young)\s+people\s+(?:are|can\'t|cannot|should)',
                    r'\b(?:millennials|boomers|gen\s*z)\s+(?:are|always|never)',
                    r'\b(?:too\s+old|too\s+young)\s+(?:for|to)'
                ],
                "description": "Age-based discrimination or stereotyping",
                "severity": QualitySeverity.MEDIUM
            },
            "cultural_bias": {
                "patterns": [
                    r'\b(?:western|eastern)\s+(?:values|culture)\s+(?:is|are)\s+(?:better|superior)',
                    r'\b(?:primitive|backward|advanced)\s+(?:culture|society)',
                    r'\b(?:all|most)\s+(?:cultures|countries)\s+(?:should|must)'
                ],
                "description": "Cultural superiority or ethnocentrism",
                "severity": QualitySeverity.HIGH
            },
            "socioeconomic_bias": {
                "patterns": [
                    r'\b(?:poor|rich)\s+people\s+(?:are|always|never)',
                    r'\b(?:low|high)\s+(?:class|income)\s+(?:families|individuals)\s+(?:tend\s+to|usually)',
                    r'\b(?:welfare|benefits)\s+(?:recipients|users)\s+(?:are|should)'
                ],
                "description": "Socioeconomic stereotyping",
                "severity": QualitySeverity.MEDIUM
            }
        }
    
    def detect_bias(self, content: str) -> List[QualityIssue]:
        """Detect bias in content."""
        issues = []
        
        for bias_type, bias_info in self.bias_patterns.items():
            for pattern in bias_info["patterns"]:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                
                for match in matches:
                    issue = QualityIssue(
                        issue_type=QualityIssueType.BIAS_DETECTED,
                        severity=bias_info["severity"],
                        title=f"{bias_type.replace('_', ' ').title()} Detected",
                        description=bias_info["description"],
                        location={
                            "start": match.start(),
                            "end": match.end(),
                            "line": self._get_line_number(content, match.start())
                        },
                        evidence=self._get_context(content, match.start(), match.end()),
                        suggestion="Consider rephrasing to avoid stereotyping or biased assumptions",
                        confidence=0.8
                    )
                    issues.append(issue)
        
        return issues
    
    def calculate_bias_score(self, content: str, issues: List[QualityIssue]) -> float:
        """Calculate bias score (0-1, where 1 is no bias)."""
        bias_issues = [i for i in issues if i.issue_type == QualityIssueType.BIAS_DETECTED]
        
        if not bias_issues:
            return 1.0
        
        # Weight by severity
        severity_weights = {
            QualitySeverity.CRITICAL: 1.0,
            QualitySeverity.HIGH: 0.8,
            QualitySeverity.MEDIUM: 0.5,
            QualitySeverity.LOW: 0.2
        }
        
        total_penalty = sum(severity_weights.get(issue.severity, 0.5) for issue in bias_issues)
        content_length = len(content.split())
        
        # Normalize by content length
        penalty_per_word = total_penalty / max(content_length, 1)
        
        # Convert to score (0-1)
        return max(0.0, 1.0 - min(penalty_per_word * 100, 1.0))
    
    def _get_line_number(self, content: str, position: int) -> int:
        """Get line number for a given position."""
        return content[:position].count('\n') + 1
    
    def _get_context(self, content: str, start: int, end: int, context_size: int = 30) -> str:
        """Get context around a match."""
        context_start = max(0, start - context_size)
        context_end = min(len(content), end + context_size)
        return content[context_start:context_end]


class HallucinationDetector:
    """Hallucination risk detection component."""
    
    def __init__(self):
        """Initialize hallucination detector."""
        self.logger = logging.getLogger(__name__)
        self._init_hallucination_patterns()
    
    def _init_hallucination_patterns(self):
        """Initialize hallucination detection patterns."""
        self.hallucination_patterns = {
            "absolute_claims": {
                "patterns": [
                    r'\b(?:always|never|all|none|every|no\s+one)\s+(?:is|are|do|does|will|can)',
                    r'\b(?:definitely|certainly|absolutely|guaranteed|proven)\s+(?:true|false|correct)',
                    r'\b(?:impossible|certain|sure)\s+(?:that|to)'
                ],
                "description": "Absolute claims that may not be verifiable",
                "severity": QualitySeverity.MEDIUM
            },
            "specific_statistics": {
                "patterns": [
                    r'\b\d+(?:\.\d+)?%\s+of\s+(?:people|users|customers)',
                    r'\b(?:studies\s+show|research\s+proves)\s+that',
                    r'\b(?:according\s+to|based\s+on)\s+(?:recent|latest)\s+(?:data|research)'
                ],
                "description": "Specific statistics or research claims without sources",
                "severity": QualitySeverity.HIGH
            },
            "future_predictions": {
                "patterns": [
                    r'\b(?:will\s+definitely|will\s+certainly|guaranteed\s+to)\s+(?:happen|occur|be)',
                    r'\b(?:in\s+the\s+future|by\s+\d{4}|within\s+\d+\s+years)',
                    r'\b(?:predict|forecast|expect)\s+(?:that|to)'
                ],
                "description": "Definitive future predictions",
                "severity": QualitySeverity.MEDIUM
            },
            "unverifiable_facts": {
                "patterns": [
                    r'\b(?:it\s+is\s+known|everyone\s+knows|obviously|clearly)\s+that',
                    r'\b(?:fact|truth)\s+(?:is|that)',
                    r'\b(?:scientists|experts|researchers)\s+(?:agree|confirm|prove)'
                ],
                "description": "Claims presented as facts without verification",
                "severity": QualitySeverity.MEDIUM
            }
        }
    
    def detect_hallucination_risk(self, content: str) -> List[QualityIssue]:
        """Detect hallucination risks in content."""
        issues = []
        
        for risk_type, risk_info in self.hallucination_patterns.items():
            for pattern in risk_info["patterns"]:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                
                for match in matches:
                    issue = QualityIssue(
                        issue_type=QualityIssueType.HALLUCINATION_RISK,
                        severity=risk_info["severity"],
                        title=f"{risk_type.replace('_', ' ').title()} Risk",
                        description=risk_info["description"],
                        location={
                            "start": match.start(),
                            "end": match.end(),
                            "line": self._get_line_number(content, match.start())
                        },
                        evidence=self._get_context(content, match.start(), match.end()),
                        suggestion="Consider adding qualifiers or sources to support claims",
                        confidence=0.7
                    )
                    issues.append(issue)
        
        return issues
    
    def calculate_hallucination_risk(self, content: str, issues: List[QualityIssue]) -> float:
        """Calculate hallucination risk score (0-1, where 0 is no risk)."""
        hallucination_issues = [i for i in issues if i.issue_type == QualityIssueType.HALLUCINATION_RISK]
        
        if not hallucination_issues:
            return 0.0
        
        # Weight by severity
        severity_weights = {
            QualitySeverity.CRITICAL: 1.0,
            QualitySeverity.HIGH: 0.8,
            QualitySeverity.MEDIUM: 0.5,
            QualitySeverity.LOW: 0.2
        }
        
        total_risk = sum(severity_weights.get(issue.severity, 0.5) for issue in hallucination_issues)
        content_length = len(content.split())
        
        # Normalize by content length
        risk_per_word = total_risk / max(content_length, 1)
        
        # Convert to risk score (0-1)
        return min(risk_per_word * 50, 1.0)
    
    def _get_line_number(self, content: str, position: int) -> int:
        """Get line number for a given position."""
        return content[:position].count('\n') + 1
    
    def _get_context(self, content: str, start: int, end: int, context_size: int = 30) -> str:
        """Get context around a match."""
        context_start = max(0, start - context_size)
        context_end = min(len(content), end + context_size)
        return content[context_start:context_end]


class CoherenceAnalyzer:
    """Coherence and language quality analyzer."""
    
    def __init__(self):
        """Initialize coherence analyzer."""
        self.logger = logging.getLogger(__name__)
    
    def analyze_coherence(self, content: str) -> Tuple[List[QualityIssue], float]:
        """Analyze content coherence and return issues and score."""
        issues = []
        
        # Check for basic coherence issues
        sentences = self._split_sentences(content)
        
        # Check sentence length variation
        sentence_lengths = [len(sentence.split()) for sentence in sentences]
        if sentence_lengths:
            avg_length = statistics.mean(sentence_lengths)
            
            # Flag very long sentences
            for i, length in enumerate(sentence_lengths):
                if length > 40:  # Very long sentence
                    issue = QualityIssue(
                        issue_type=QualityIssueType.COHERENCE_ISSUE,
                        severity=QualitySeverity.LOW,
                        title="Long Sentence Detected",
                        description="Sentence may be too long and complex",
                        location={"sentence": i + 1},
                        evidence=sentences[i][:100] + "..." if len(sentences[i]) > 100 else sentences[i],
                        suggestion="Consider breaking into shorter sentences for better readability",
                        confidence=0.8
                    )
                    issues.append(issue)
        
        # Check for repetitive patterns
        words = content.lower().split()
        word_freq = {}
        for word in words:
            if len(word) > 3:  # Only check meaningful words
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Flag excessive repetition
        total_words = len(words)
        for word, freq in word_freq.items():
            if freq > 5 and freq / total_words > 0.05:  # More than 5% repetition
                issue = QualityIssue(
                    issue_type=QualityIssueType.LANGUAGE_QUALITY,
                    severity=QualitySeverity.LOW,
                    title="Excessive Word Repetition",
                    description=f"Word '{word}' appears {freq} times ({freq/total_words:.1%})",
                    location={"word": word},
                    evidence=f"'{word}' repeated {freq} times",
                    suggestion="Consider using synonyms or rephrasing to reduce repetition",
                    confidence=0.9
                )
                issues.append(issue)
        
        # Calculate coherence score
        coherence_score = self._calculate_coherence_score(content, issues)
        
        return issues, coherence_score
    
    def _split_sentences(self, content: str) -> List[str]:
        """Split content into sentences."""
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', content)
        return [s.strip() for s in sentences if s.strip()]
    
    def _calculate_coherence_score(self, content: str, issues: List[QualityIssue]) -> float:
        """Calculate coherence score (0-1, where 1 is most coherent)."""
        coherence_issues = [i for i in issues if i.issue_type == QualityIssueType.COHERENCE_ISSUE]
        language_issues = [i for i in issues if i.issue_type == QualityIssueType.LANGUAGE_QUALITY]
        
        total_issues = len(coherence_issues) + len(language_issues)
        
        if total_issues == 0:
            return 1.0
        
        # Penalty based on number of issues
        content_length = len(content.split())
        issue_density = total_issues / max(content_length / 100, 1)  # Issues per 100 words
        
        return max(0.0, 1.0 - min(issue_density * 0.2, 1.0))


class QualityAssuranceFramework:
    """Main quality assurance framework."""
    
    def __init__(self):
        """Initialize quality assurance framework."""
        self.logger = logging.getLogger(__name__)
        self.bias_detector = BiasDetector()
        self.hallucination_detector = HallucinationDetector()
        self.coherence_analyzer = CoherenceAnalyzer()
    
    def assess_quality(self, prompt_content: str, prompt_id: str = "", 
                      prompt_version: str = "") -> QualityAssessmentResult:
        """Perform comprehensive quality assessment of a prompt."""
        start_time = datetime.now()
        
        result = QualityAssessmentResult(
            prompt_id=prompt_id,
            prompt_version=prompt_version
        )
        
        try:
            # Detect bias
            bias_issues = self.bias_detector.detect_bias(prompt_content)
            result.issues.extend(bias_issues)
            
            # Detect hallucination risks
            hallucination_issues = self.hallucination_detector.detect_hallucination_risk(prompt_content)
            result.issues.extend(hallucination_issues)
            
            # Analyze coherence
            coherence_issues, coherence_score = self.coherence_analyzer.analyze_coherence(prompt_content)
            result.issues.extend(coherence_issues)
            
            # Calculate metrics
            result.metrics = QualityMetrics(
                bias_score=self.bias_detector.calculate_bias_score(prompt_content, result.issues),
                hallucination_risk=self.hallucination_detector.calculate_hallucination_risk(prompt_content, result.issues),
                coherence_score=coherence_score,
                factual_score=self._calculate_factual_score(prompt_content, result.issues),
                language_score=self._calculate_language_score(prompt_content, result.issues),
                ethical_score=self._calculate_ethical_score(prompt_content, result.issues)
            )
            
            # Calculate overall score
            result.metrics.overall_score = self._calculate_overall_score(result.metrics)
            
            # Calculate assessment duration
            end_time = datetime.now()
            result.assessment_duration = (end_time - start_time).total_seconds()
            
            self.logger.info(f"Quality assessment completed for prompt {prompt_id}: {len(result.issues)} issues found")
            
        except Exception as e:
            self.logger.error(f"Error during quality assessment: {e}")
            # Add error as critical issue
            error_issue = QualityIssue(
                issue_type=QualityIssueType.ETHICAL_CONCERN,
                severity=QualitySeverity.CRITICAL,
                title="Quality Assessment Error",
                description=f"Failed to complete quality assessment: {str(e)}",
                suggestion="Review prompt manually for quality issues"
            )
            result.issues.append(error_issue)
        
        return result
    
    def _calculate_factual_score(self, content: str, issues: List[QualityIssue]) -> float:
        """Calculate factual accuracy score."""
        # This is a simplified implementation
        # In practice, this would use more sophisticated fact-checking
        hallucination_risk = sum(1 for i in issues if i.issue_type == QualityIssueType.HALLUCINATION_RISK)
        
        if hallucination_risk == 0:
            return 1.0
        
        content_length = len(content.split())
        risk_density = hallucination_risk / max(content_length / 100, 1)
        
        return max(0.0, 1.0 - min(risk_density * 0.3, 1.0))
    
    def _calculate_language_score(self, content: str, issues: List[QualityIssue]) -> float:
        """Calculate language quality score."""
        language_issues = [i for i in issues if i.issue_type == QualityIssueType.LANGUAGE_QUALITY]
        
        if not language_issues:
            return 1.0
        
        content_length = len(content.split())
        issue_density = len(language_issues) / max(content_length / 100, 1)
        
        return max(0.0, 1.0 - min(issue_density * 0.2, 1.0))
    
    def _calculate_ethical_score(self, content: str, issues: List[QualityIssue]) -> float:
        """Calculate ethical score."""
        ethical_issues = [i for i in issues if i.issue_type in [
            QualityIssueType.BIAS_DETECTED,
            QualityIssueType.ETHICAL_CONCERN,
            QualityIssueType.CULTURAL_SENSITIVITY
        ]]
        
        if not ethical_issues:
            return 1.0
        
        # Weight by severity
        severity_weights = {
            QualitySeverity.CRITICAL: 1.0,
            QualitySeverity.HIGH: 0.8,
            QualitySeverity.MEDIUM: 0.5,
            QualitySeverity.LOW: 0.2
        }
        
        total_penalty = sum(severity_weights.get(issue.severity, 0.5) for issue in ethical_issues)
        
        return max(0.0, 1.0 - min(total_penalty * 0.3, 1.0))
    
    def _calculate_overall_score(self, metrics: QualityMetrics) -> float:
        """Calculate overall quality score."""
        # Weighted average of all metrics
        weights = {
            'bias_score': 0.25,
            'coherence_score': 0.20,
            'factual_score': 0.20,
            'language_score': 0.15,
            'ethical_score': 0.20
        }
        
        # Hallucination risk is inverted (lower risk = higher score)
        hallucination_score = 1.0 - metrics.hallucination_risk
        
        overall = (
            metrics.bias_score * weights['bias_score'] +
            metrics.coherence_score * weights['coherence_score'] +
            metrics.factual_score * weights['factual_score'] +
            metrics.language_score * weights['language_score'] +
            metrics.ethical_score * weights['ethical_score']
        )
        
        # Apply hallucination penalty
        overall *= (1.0 - metrics.hallucination_risk * 0.3)
        
        return max(0.0, min(overall, 1.0))
    
    def generate_quality_report(self, assessment_results: List[QualityAssessmentResult]) -> Dict[str, Any]:
        """Generate a comprehensive quality report from multiple assessments."""
        if not assessment_results:
            return {
                "summary": "No assessment results provided",
                "total_assessments": 0,
                "average_score": 0.0
            }
        
        # Aggregate statistics
        total_issues = sum(len(result.issues) for result in assessment_results)
        overall_scores = [result.metrics.overall_score for result in assessment_results]
        
        # Calculate averages
        avg_overall_score = statistics.mean(overall_scores)
        avg_bias_score = statistics.mean([r.metrics.bias_score for r in assessment_results])
        avg_coherence_score = statistics.mean([r.metrics.coherence_score for r in assessment_results])
        avg_hallucination_risk = statistics.mean([r.metrics.hallucination_risk for r in assessment_results])
        
        # Issue breakdown
        issue_types = {}
        severity_levels = {}
        
        for result in assessment_results:
            for issue in result.issues:
                issue_type = issue.issue_type.value
                issue_types[issue_type] = issue_types.get(issue_type, 0) + 1
                
                severity = issue.severity.value
                severity_levels[severity] = severity_levels.get(severity, 0) + 1
        
        return {
            "summary": {
                "total_assessments": len(assessment_results),
                "total_issues": total_issues,
                "average_overall_score": avg_overall_score,
                "average_bias_score": avg_bias_score,
                "average_coherence_score": avg_coherence_score,
                "average_hallucination_risk": avg_hallucination_risk
            },
            "issue_breakdown": {
                "by_type": issue_types,
                "by_severity": severity_levels
            },
            "score_distribution": {
                "excellent": len([s for s in overall_scores if s >= 0.9]),
                "good": len([s for s in overall_scores if 0.7 <= s < 0.9]),
                "fair": len([s for s in overall_scores if 0.5 <= s < 0.7]),
                "poor": len([s for s in overall_scores if s < 0.5])
            },
            "recommendations": self._generate_quality_recommendations(issue_types, severity_levels),
            "generated_at": datetime.now().isoformat()
        }
    
    def _generate_quality_recommendations(self, issue_types: Dict[str, int], 
                                        severity_levels: Dict[str, int]) -> List[str]:
        """Generate quality improvement recommendations."""
        recommendations = []
        
        # Bias recommendations
        if issue_types.get("bias_detected", 0) > 0:
            recommendations.append(
                "Implement bias review process and diverse perspective validation"
            )
        
        # Hallucination recommendations
        if issue_types.get("hallucination_risk", 0) > 0:
            recommendations.append(
                "Add fact-checking and source verification to your prompt development process"
            )
        
        # Coherence recommendations
        if issue_types.get("coherence_issue", 0) > 0:
            recommendations.append(
                "Focus on improving prompt structure and clarity"
            )
        
        # Language quality recommendations
        if issue_types.get("language_quality", 0) > 0:
            recommendations.append(
                "Implement language quality checks and style guidelines"
            )
        
        # Critical severity recommendations
        if severity_levels.get("critical", 0) > 0:
            recommendations.append(
                "Address critical quality issues immediately before deployment"
            )
        
        return recommendations