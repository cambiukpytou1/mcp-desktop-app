"""
Quality Gate Service for MCP Admin Application
==============================================

Service for managing quality gates and prompt certification.
"""

import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging
import json

from models.collaboration import QualityGate
from data.database import DatabaseManager


class QualityGateService:
    """Service for quality gates and prompt certification."""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize the quality gate service."""
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
        self._init_database()
        self._init_default_gates()
    
    def _init_database(self):
        """Initialize database tables for quality gates."""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Quality gates table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS quality_gates (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    criteria TEXT DEFAULT '[]',
                    required_score REAL DEFAULT 0.8,
                    auto_pass_conditions TEXT DEFAULT '{}',
                    created_by TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            """)
            
            conn.commit()
    
    def _init_default_gates(self):
        """Initialize default quality gates."""
        try:
            # Initialize database tables first
            self._init_database()
            
            # Check if default gates exist
            existing_gates = self.list_gates()
            if existing_gates:
                return
            
            # Create default quality gates
            default_gates = [
                {
                    "name": "Security Check",
                    "description": "Checks for security issues and PII leakage",
                    "criteria": [
                        {"type": "security_scan", "weight": 1.0, "threshold": 0.0},
                        {"type": "pii_detection", "weight": 1.0, "threshold": 0.0}
                    ],
                    "required_score": 1.0
                },
                {
                    "name": "Quality Assurance",
                    "description": "Checks for bias, hallucination, and quality metrics",
                    "criteria": [
                        {"type": "bias_detection", "weight": 0.3, "threshold": 0.8},
                        {"type": "hallucination_rate", "weight": 0.3, "threshold": 0.1},
                        {"type": "coherence_score", "weight": 0.2, "threshold": 0.7},
                        {"type": "factual_accuracy", "weight": 0.2, "threshold": 0.8}
                    ],
                    "required_score": 0.8
                },
                {
                    "name": "Performance Gate",
                    "description": "Checks performance metrics and cost efficiency",
                    "criteria": [
                        {"type": "response_time", "weight": 0.3, "threshold": 5.0},
                        {"type": "token_efficiency", "weight": 0.3, "threshold": 0.7},
                        {"type": "cost_per_request", "weight": 0.2, "threshold": 0.1},
                        {"type": "success_rate", "weight": 0.2, "threshold": 0.95}
                    ],
                    "required_score": 0.8
                },
                {
                    "name": "Production Readiness",
                    "description": "Comprehensive check for production deployment",
                    "criteria": [
                        {"type": "security_scan", "weight": 0.2, "threshold": 0.0},
                        {"type": "quality_score", "weight": 0.3, "threshold": 0.8},
                        {"type": "performance_score", "weight": 0.2, "threshold": 0.8},
                        {"type": "test_coverage", "weight": 0.1, "threshold": 0.8},
                        {"type": "documentation", "weight": 0.1, "threshold": 0.8},
                        {"type": "approval_status", "weight": 0.1, "threshold": 1.0}
                    ],
                    "required_score": 0.85
                }
            ]
            
            for gate_config in default_gates:
                self.create_gate(
                    name=gate_config["name"],
                    description=gate_config["description"],
                    criteria=gate_config["criteria"],
                    required_score=gate_config["required_score"],
                    created_by="system"
                )
            
            self.logger.info("Created default quality gates")
            
        except Exception as e:
            self.logger.error(f"Error initializing default quality gates: {e}")
    
    def create_gate(self, name: str, description: str, criteria: List[Dict[str, Any]],
                   required_score: float, created_by: str,
                   auto_pass_conditions: Dict[str, Any] = None) -> QualityGate:
        """Create a new quality gate."""
        try:
            gate = QualityGate(
                name=name,
                description=description,
                criteria=criteria,
                required_score=required_score,
                auto_pass_conditions=auto_pass_conditions or {},
                created_by=created_by
            )
            
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO quality_gates (
                        id, name, description, criteria, required_score,
                        auto_pass_conditions, created_by, created_at, updated_at, is_active
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    gate.id, gate.name, gate.description,
                    json.dumps(gate.criteria), gate.required_score,
                    json.dumps(gate.auto_pass_conditions),
                    gate.created_by, gate.created_at.isoformat(),
                    gate.updated_at.isoformat(), gate.is_active
                ))
                conn.commit()
            
            self.logger.info(f"Created quality gate: {name} ({gate.id})")
            return gate
            
        except Exception as e:
            self.logger.error(f"Error creating quality gate {name}: {e}")
            raise
    
    def get_gate(self, gate_id: str) -> Optional[QualityGate]:
        """Get a quality gate by ID."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, name, description, criteria, required_score,
                           auto_pass_conditions, created_by, created_at, updated_at, is_active
                    FROM quality_gates 
                    WHERE id = ?
                """, (gate_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                return QualityGate(
                    id=row[0],
                    name=row[1],
                    description=row[2],
                    criteria=json.loads(row[3]),
                    required_score=row[4],
                    auto_pass_conditions=json.loads(row[5]),
                    created_by=row[6],
                    created_at=datetime.fromisoformat(row[7]),
                    updated_at=datetime.fromisoformat(row[8]),
                    is_active=bool(row[9])
                )
                
        except Exception as e:
            self.logger.error(f"Error getting quality gate {gate_id}: {e}")
            return None
    
    def list_gates(self, active_only: bool = True) -> List[QualityGate]:
        """List all quality gates."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT id, name, description, criteria, required_score,
                           auto_pass_conditions, created_by, created_at, updated_at, is_active
                    FROM quality_gates
                """
                
                if active_only:
                    query += " WHERE is_active = 1"
                
                query += " ORDER BY name"
                cursor.execute(query)
                
                gates = []
                for row in cursor.fetchall():
                    gate = QualityGate(
                        id=row[0],
                        name=row[1],
                        description=row[2],
                        criteria=json.loads(row[3]),
                        required_score=row[4],
                        auto_pass_conditions=json.loads(row[5]),
                        created_by=row[6],
                        created_at=datetime.fromisoformat(row[7]),
                        updated_at=datetime.fromisoformat(row[8]),
                        is_active=bool(row[9])
                    )
                    gates.append(gate)
                
                return gates
                
        except Exception as e:
            self.logger.error(f"Error listing quality gates: {e}")
            return []
    
    def evaluate_prompt(self, gate_id: str, prompt_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a prompt against a quality gate."""
        try:
            gate = self.get_gate(gate_id)
            if not gate:
                raise ValueError(f"Quality gate {gate_id} not found")
            
            results = {
                "gate_id": gate_id,
                "gate_name": gate.name,
                "criteria_results": [],
                "overall_score": 0.0,
                "passed": False,
                "evaluated_at": datetime.now().isoformat()
            }
            
            total_weight = 0.0
            weighted_score = 0.0
            
            for criterion in gate.criteria:
                criterion_result = self._evaluate_criterion(criterion, prompt_data)
                results["criteria_results"].append(criterion_result)
                
                weight = criterion.get("weight", 1.0)
                total_weight += weight
                weighted_score += criterion_result["score"] * weight
            
            # Calculate overall score
            if total_weight > 0:
                results["overall_score"] = weighted_score / total_weight
            
            # Check if passed
            results["passed"] = results["overall_score"] >= gate.required_score
            
            # Check auto-pass conditions
            if not results["passed"] and gate.auto_pass_conditions:
                results["passed"] = self._check_auto_pass(gate.auto_pass_conditions, prompt_data)
                if results["passed"]:
                    results["auto_passed"] = True
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error evaluating prompt against gate {gate_id}: {e}")
            return {
                "gate_id": gate_id,
                "error": str(e),
                "passed": False,
                "evaluated_at": datetime.now().isoformat()
            }
    
    def _evaluate_criterion(self, criterion: Dict[str, Any], prompt_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a single criterion."""
        try:
            criterion_type = criterion.get("type", "unknown")
            threshold = criterion.get("threshold", 0.5)
            
            result = {
                "type": criterion_type,
                "threshold": threshold,
                "score": 0.0,
                "passed": False,
                "details": {}
            }
            
            # Implement criterion evaluation logic
            if criterion_type == "security_scan":
                result.update(self._evaluate_security(prompt_data))
            elif criterion_type == "pii_detection":
                result.update(self._evaluate_pii(prompt_data))
            elif criterion_type == "bias_detection":
                result.update(self._evaluate_bias(prompt_data))
            elif criterion_type == "hallucination_rate":
                result.update(self._evaluate_hallucination(prompt_data))
            elif criterion_type == "coherence_score":
                result.update(self._evaluate_coherence(prompt_data))
            elif criterion_type == "factual_accuracy":
                result.update(self._evaluate_accuracy(prompt_data))
            elif criterion_type == "response_time":
                result.update(self._evaluate_response_time(prompt_data))
            elif criterion_type == "token_efficiency":
                result.update(self._evaluate_token_efficiency(prompt_data))
            elif criterion_type == "cost_per_request":
                result.update(self._evaluate_cost(prompt_data))
            elif criterion_type == "success_rate":
                result.update(self._evaluate_success_rate(prompt_data))
            elif criterion_type == "test_coverage":
                result.update(self._evaluate_test_coverage(prompt_data))
            elif criterion_type == "documentation":
                result.update(self._evaluate_documentation(prompt_data))
            elif criterion_type == "approval_status":
                result.update(self._evaluate_approval_status(prompt_data))
            else:
                result["score"] = 0.5  # Default neutral score
                result["details"]["message"] = f"Unknown criterion type: {criterion_type}"
            
            # Determine if criterion passed
            if criterion_type in ["security_scan", "pii_detection"]:
                # For security criteria, lower scores are better (0 = no issues)
                result["passed"] = result["score"] <= threshold
            else:
                # For quality criteria, higher scores are better
                result["passed"] = result["score"] >= threshold
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error evaluating criterion {criterion.get('type', 'unknown')}: {e}")
            return {
                "type": criterion.get("type", "unknown"),
                "score": 0.0,
                "passed": False,
                "error": str(e)
            }
    
    def _evaluate_security(self, prompt_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate security aspects of a prompt."""
        # Simplified security evaluation
        # In practice, this would use sophisticated security scanning
        content = prompt_data.get("content", "")
        
        security_issues = 0
        details = {"issues": []}
        
        # Check for potential security issues
        security_patterns = [
            "system(",
            "exec(",
            "eval(",
            "import os",
            "subprocess",
            "shell=True",
            "password",
            "secret",
            "api_key"
        ]
        
        for pattern in security_patterns:
            if pattern.lower() in content.lower():
                security_issues += 1
                details["issues"].append(f"Potential security issue: {pattern}")
        
        # Score: 0 = no issues, 1 = many issues
        score = min(security_issues / 5.0, 1.0)
        
        return {
            "score": score,
            "details": details
        }
    
    def _evaluate_pii(self, prompt_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate PII detection in a prompt."""
        # Simplified PII detection
        content = prompt_data.get("content", "")
        
        pii_issues = 0
        details = {"issues": []}
        
        # Check for potential PII patterns
        import re
        
        pii_patterns = [
            (r'\b\d{3}-\d{2}-\d{4}\b', "SSN"),
            (r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', "Credit Card"),
            (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', "Email"),
            (r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', "Phone Number")
        ]
        
        for pattern, pii_type in pii_patterns:
            matches = re.findall(pattern, content)
            if matches:
                pii_issues += len(matches)
                details["issues"].append(f"Potential {pii_type}: {len(matches)} instances")
        
        # Score: 0 = no PII, 1 = many PII instances
        score = min(pii_issues / 3.0, 1.0)
        
        return {
            "score": score,
            "details": details
        }
    
    def _evaluate_bias(self, prompt_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate bias in prompt responses."""
        # Simplified bias evaluation
        # In practice, this would use ML models for bias detection
        
        evaluation_results = prompt_data.get("evaluation_results", [])
        if not evaluation_results:
            return {"score": 0.5, "details": {"message": "No evaluation results available"}}
        
        # Look for bias-related metrics in evaluation results
        bias_scores = []
        for result in evaluation_results:
            scores = result.get("scores", {})
            if "bias_score" in scores:
                bias_scores.append(scores["bias_score"])
        
        if bias_scores:
            avg_bias_score = sum(bias_scores) / len(bias_scores)
            return {"score": avg_bias_score, "details": {"bias_scores": bias_scores}}
        
        return {"score": 0.8, "details": {"message": "Default bias score (no specific evaluation)"}}
    
    def _evaluate_hallucination(self, prompt_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate hallucination rate in prompt responses."""
        # Simplified hallucination evaluation
        evaluation_results = prompt_data.get("evaluation_results", [])
        if not evaluation_results:
            return {"score": 0.9, "details": {"message": "No evaluation results available"}}
        
        hallucination_rates = []
        for result in evaluation_results:
            scores = result.get("scores", {})
            if "hallucination_rate" in scores:
                hallucination_rates.append(scores["hallucination_rate"])
        
        if hallucination_rates:
            avg_rate = sum(hallucination_rates) / len(hallucination_rates)
            # Convert rate to score (lower rate = higher score)
            score = max(0.0, 1.0 - avg_rate)
            return {"score": score, "details": {"hallucination_rates": hallucination_rates}}
        
        return {"score": 0.9, "details": {"message": "Default hallucination score"}}
    
    def _evaluate_coherence(self, prompt_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate coherence of prompt responses."""
        evaluation_results = prompt_data.get("evaluation_results", [])
        if not evaluation_results:
            return {"score": 0.7, "details": {"message": "No evaluation results available"}}
        
        coherence_scores = []
        for result in evaluation_results:
            scores = result.get("scores", {})
            if "coherence" in scores:
                coherence_scores.append(scores["coherence"])
        
        if coherence_scores:
            avg_score = sum(coherence_scores) / len(coherence_scores)
            return {"score": avg_score, "details": {"coherence_scores": coherence_scores}}
        
        return {"score": 0.7, "details": {"message": "Default coherence score"}}
    
    def _evaluate_accuracy(self, prompt_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate factual accuracy of prompt responses."""
        evaluation_results = prompt_data.get("evaluation_results", [])
        if not evaluation_results:
            return {"score": 0.8, "details": {"message": "No evaluation results available"}}
        
        accuracy_scores = []
        for result in evaluation_results:
            scores = result.get("scores", {})
            if "factual_accuracy" in scores:
                accuracy_scores.append(scores["factual_accuracy"])
        
        if accuracy_scores:
            avg_score = sum(accuracy_scores) / len(accuracy_scores)
            return {"score": avg_score, "details": {"accuracy_scores": accuracy_scores}}
        
        return {"score": 0.8, "details": {"message": "Default accuracy score"}}
    
    def _evaluate_response_time(self, prompt_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate response time performance."""
        evaluation_results = prompt_data.get("evaluation_results", [])
        if not evaluation_results:
            return {"score": 0.8, "details": {"message": "No evaluation results available"}}
        
        response_times = []
        for result in evaluation_results:
            if "execution_time" in result:
                response_times.append(result["execution_time"])
        
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            # Convert time to score (faster = higher score)
            # Assume 5 seconds is the threshold for good performance
            score = max(0.0, min(1.0, (5.0 - avg_time) / 5.0))
            return {"score": score, "details": {"avg_response_time": avg_time}}
        
        return {"score": 0.8, "details": {"message": "Default response time score"}}
    
    def _evaluate_token_efficiency(self, prompt_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate token efficiency."""
        evaluation_results = prompt_data.get("evaluation_results", [])
        if not evaluation_results:
            return {"score": 0.7, "details": {"message": "No evaluation results available"}}
        
        # Calculate token efficiency based on output quality vs token usage
        efficiency_scores = []
        for result in evaluation_results:
            token_usage = result.get("token_usage", {})
            scores = result.get("scores", {})
            
            if token_usage and scores:
                total_tokens = token_usage.get("total_tokens", 1)
                quality_score = scores.get("overall", 0.5)
                
                # Efficiency = quality per token (normalized)
                efficiency = quality_score / (total_tokens / 1000.0)  # per 1k tokens
                efficiency_scores.append(min(efficiency, 1.0))
        
        if efficiency_scores:
            avg_efficiency = sum(efficiency_scores) / len(efficiency_scores)
            return {"score": avg_efficiency, "details": {"efficiency_scores": efficiency_scores}}
        
        return {"score": 0.7, "details": {"message": "Default efficiency score"}}
    
    def _evaluate_cost(self, prompt_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate cost per request."""
        evaluation_results = prompt_data.get("evaluation_results", [])
        if not evaluation_results:
            return {"score": 0.8, "details": {"message": "No evaluation results available"}}
        
        costs = []
        for result in evaluation_results:
            if "cost" in result:
                costs.append(result["cost"])
        
        if costs:
            avg_cost = sum(costs) / len(costs)
            # Convert cost to score (lower cost = higher score)
            # Assume $0.10 is the threshold for acceptable cost
            score = max(0.0, min(1.0, (0.10 - avg_cost) / 0.10))
            return {"score": score, "details": {"avg_cost": avg_cost}}
        
        return {"score": 0.8, "details": {"message": "Default cost score"}}
    
    def _evaluate_success_rate(self, prompt_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate success rate of prompt executions."""
        evaluation_results = prompt_data.get("evaluation_results", [])
        if not evaluation_results:
            return {"score": 0.9, "details": {"message": "No evaluation results available"}}
        
        successful_runs = sum(1 for result in evaluation_results if not result.get("error"))
        total_runs = len(evaluation_results)
        
        if total_runs > 0:
            success_rate = successful_runs / total_runs
            return {"score": success_rate, "details": {"successful_runs": successful_runs, "total_runs": total_runs}}
        
        return {"score": 0.9, "details": {"message": "Default success rate"}}
    
    def _evaluate_test_coverage(self, prompt_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate test coverage for the prompt."""
        # Simplified test coverage evaluation
        test_cases = prompt_data.get("test_cases", [])
        evaluation_results = prompt_data.get("evaluation_results", [])
        
        if not test_cases:
            return {"score": 0.0, "details": {"message": "No test cases defined"}}
        
        coverage_score = min(len(evaluation_results) / len(test_cases), 1.0)
        return {"score": coverage_score, "details": {"test_cases": len(test_cases), "evaluations": len(evaluation_results)}}
    
    def _evaluate_documentation(self, prompt_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate documentation quality."""
        # Check for documentation completeness
        score = 0.0
        details = {"checks": []}
        
        if prompt_data.get("description"):
            score += 0.3
            details["checks"].append("Has description")
        
        if prompt_data.get("usage_examples"):
            score += 0.3
            details["checks"].append("Has usage examples")
        
        if prompt_data.get("parameters"):
            score += 0.2
            details["checks"].append("Has parameter documentation")
        
        if prompt_data.get("expected_outputs"):
            score += 0.2
            details["checks"].append("Has expected output documentation")
        
        return {"score": score, "details": details}
    
    def _evaluate_approval_status(self, prompt_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate approval status."""
        approval_status = prompt_data.get("approval_status", "pending")
        
        if approval_status == "approved":
            return {"score": 1.0, "details": {"status": "approved"}}
        elif approval_status == "rejected":
            return {"score": 0.0, "details": {"status": "rejected"}}
        else:
            return {"score": 0.5, "details": {"status": "pending"}}
    
    def _check_auto_pass(self, conditions: Dict[str, Any], prompt_data: Dict[str, Any]) -> bool:
        """Check if auto-pass conditions are met."""
        try:
            # Implement auto-pass logic based on conditions
            # This is a simplified implementation
            
            if conditions.get("author_role") == "admin":
                author_role = prompt_data.get("author_role")
                if author_role == "admin":
                    return True
            
            if conditions.get("minor_changes_only"):
                # Check if changes are minor (simplified)
                change_score = prompt_data.get("change_score", 1.0)
                if change_score < 0.1:  # Less than 10% change
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking auto-pass conditions: {e}")
            return False