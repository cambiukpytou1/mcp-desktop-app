"""
Compliance and Governance Tools for MCP Admin Application
========================================================

Tools for customizable review checklists, policy-as-code integration, and compliance reporting.
"""

import json
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import yaml

from models.base import generate_id


class ComplianceStandard(Enum):
    """Compliance standard enumeration."""
    GDPR = "gdpr"
    HIPAA = "hipaa"
    SOX = "sox"
    PCI_DSS = "pci_dss"
    ISO_27001 = "iso_27001"
    NIST = "nist"
    CUSTOM = "custom"


class PolicyType(Enum):
    """Policy type enumeration."""
    SECURITY = "security"
    PRIVACY = "privacy"
    QUALITY = "quality"
    ETHICAL = "ethical"
    OPERATIONAL = "operational"
    REGULATORY = "regulatory"


class ComplianceStatus(Enum):
    """Compliance status enumeration."""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    UNDER_REVIEW = "under_review"
    EXEMPT = "exempt"


@dataclass
class PolicyRule:

    """Individual policy rule definition."""
    id: str = field(default_factory=generate_id)
    name: str = ""
    description: str = ""
    rule_type: str = ""  # "regex", "function", "checklist"
    rule_definition: Dict[str, Any] = field(default_factory=dict)
    severity: str = "medium"  # "low", "medium", "high", "critical"
    enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "rule_type": self.rule_type,
            "rule_definition": self.rule_definition,
            "severity": self.severity,
            "enabled": self.enabled
        }


@dataclass
class CompliancePolicy:
    """Compliance policy definition."""
    id: str = field(default_factory=generate_id)
    name: str = ""
    description: str = ""
    policy_type: PolicyType = PolicyType.SECURITY
    compliance_standards: List[ComplianceStandard] = field(default_factory=list)
    rules: List[PolicyRule] = field(default_factory=list)
    version: str = "1.0.0"
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "policy_type": self.policy_type.value,
            "compliance_standards": [std.value for std in self.compliance_standards],
            "rules": [rule.to_dict() for rule in self.rules],
            "version": self.version,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "is_active": self.is_active
        }


@dataclass
class ChecklistItem:
    """Review checklist item."""
    id: str = field(default_factory=generate_id)
    title: str = ""
    description: str = ""
    category: str = ""
    required: bool = True
    compliance_standards: List[ComplianceStandard] = field(default_factory=list)
    validation_criteria: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "required": self.required,
            "compliance_standards": [std.value for std in self.compliance_standards],
            "validation_criteria": self.validation_criteria
        }


@dataclass
class ReviewChecklist:
    """Review checklist definition."""
    id: str = field(default_factory=generate_id)
    name: str = ""
    description: str = ""
    items: List[ChecklistItem] = field(default_factory=list)
    applicable_standards: List[ComplianceStandard] = field(default_factory=list)
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "items": [item.to_dict() for item in self.items],
            "applicable_standards": [std.value for std in self.applicable_standards],
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "is_active": self.is_active
        }


@dataclass
class ComplianceViolation:
    """Compliance violation record."""
    id: str = field(default_factory=generate_id)
    policy_id: str = ""
    rule_id: str = ""
    prompt_id: str = ""
    prompt_version: str = ""
    violation_type: str = ""
    severity: str = ""
    description: str = ""
    evidence: str = ""
    remediation: str = ""
    status: ComplianceStatus = ComplianceStatus.NON_COMPLIANT
    detected_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "policy_id": self.policy_id,
            "rule_id": self.rule_id,
            "prompt_id": self.prompt_id,
            "prompt_version": self.prompt_version,
            "violation_type": self.violation_type,
            "severity": self.severity,
            "description": self.description,
            "evidence": self.evidence,
            "remediation": self.remediation,
            "status": self.status.value,
            "detected_at": self.detected_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolved_by": self.resolved_by
        }


@dataclass
class ComplianceAssessment:
    """Compliance assessment result."""
    assessment_id: str = field(default_factory=generate_id)
    prompt_id: str = ""
    prompt_version: str = ""
    policies_evaluated: List[str] = field(default_factory=list)
    violations: List[ComplianceViolation] = field(default_factory=list)
    overall_status: ComplianceStatus = ComplianceStatus.COMPLIANT
    compliance_score: float = 1.0
    assessed_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "assessment_id": self.assessment_id,
            "prompt_id": self.prompt_id,
            "prompt_version": self.prompt_version,
            "policies_evaluated": self.policies_evaluated,
            "violations": [v.to_dict() for v in self.violations],
            "overall_status": self.overall_status.value,
            "compliance_score": self.compliance_score,
            "assessed_at": self.assessed_at.isoformat(),
            "violation_count": len(self.violations),
            "critical_violations": len([v for v in self.violations if v.severity == "critical"]),
            "high_violations": len([v for v in self.violations if v.severity == "high"])
        }


class PolicyEngine:
    """Policy-as-code engine for compliance evaluation."""
    
    def __init__(self):
        """Initialize policy engine."""
        self.logger = logging.getLogger(__name__)
        self.policies: Dict[str, CompliancePolicy] = {}
        self._init_default_policies()
    
    def _init_default_policies(self):
        """Initialize default compliance policies."""
        # GDPR Privacy Policy
        gdpr_policy = CompliancePolicy(
            name="GDPR Privacy Compliance",
            description="General Data Protection Regulation compliance policy",
            policy_type=PolicyType.PRIVACY,
            compliance_standards=[ComplianceStandard.GDPR],
            rules=[
                PolicyRule(
                    name="PII Detection",
                    description="Detect personally identifiable information",
                    rule_type="regex",
                    rule_definition={
                        "patterns": [
                            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
                            r'\b\d{3}-?\d{2}-?\d{4}\b',  # SSN
                            r'\b(?:\d{4}[-\s]?){3}\d{4}\b'  # Credit card
                        ]
                    },
                    severity="high"
                ),
                PolicyRule(
                    name="Consent Language",
                    description="Ensure proper consent language is present",
                    rule_type="checklist",
                    rule_definition={
                        "required_phrases": ["consent", "opt-in", "permission"]
                    },
                    severity="medium"
                )
            ]
        )
        self.policies[gdpr_policy.id] = gdpr_policy
        
        # Security Policy
        security_policy = CompliancePolicy(
            name="Security Compliance",
            description="General security compliance policy",
            policy_type=PolicyType.SECURITY,
            compliance_standards=[ComplianceStandard.ISO_27001, ComplianceStandard.NIST],
            rules=[
                PolicyRule(
                    name="Secret Detection",
                    description="Detect exposed secrets and credentials",
                    rule_type="regex",
                    rule_definition={
                        "patterns": [
                            r'(?i)(?:api[_-]?key|apikey)\s*[:=]\s*["\']?([a-zA-Z0-9_-]{20,})["\']?',
                            r'(?i)(?:password|passwd|pwd)\s*[:=]\s*["\']?([^\s"\']{8,})["\']?',
                            r'AKIA[0-9A-Z]{16}'  # AWS key
                        ]
                    },
                    severity="critical"
                ),
                PolicyRule(
                    name="Unsafe Code Detection",
                    description="Detect potentially unsafe code patterns",
                    rule_type="regex",
                    rule_definition={
                        "patterns": [
                            r'(?i)(?:system|exec|eval)\s*\(',
                            r'(?i)(?:rm\s+-rf|del\s+/|format\s+c:)'
                        ]
                    },
                    severity="high"
                )
            ]
        )
        self.policies[security_policy.id] = security_policy
        
        # Ethical AI Policy
        ethical_policy = CompliancePolicy(
            name="Ethical AI Compliance",
            description="Ethical AI and bias prevention policy",
            policy_type=PolicyType.ETHICAL,
            compliance_standards=[ComplianceStandard.CUSTOM],
            rules=[
                PolicyRule(
                    name="Bias Detection",
                    description="Detect potential bias in language",
                    rule_type="regex",
                    rule_definition={
                        "patterns": [
                            r'\b(?:he|she)\s+(?:is\s+)?(?:better|worse|more|less)\s+(?:at|in|with)',
                            r'\b(?:all|most)\s+(?:men|women|boys|girls)\s+(?:are|do|have)',
                            r'\b(?:typical|characteristic)\s+(?:of|for)\s+(?:race|ethnicity)'
                        ]
                    },
                    severity="high"
                ),
                PolicyRule(
                    name="Inclusive Language",
                    description="Ensure inclusive and respectful language",
                    rule_type="checklist",
                    rule_definition={
                        "prohibited_terms": ["guys", "mankind", "blacklist", "whitelist"],
                        "preferred_alternatives": ["everyone", "humanity", "blocklist", "allowlist"]
                    },
                    severity="medium"
                )
            ]
        )
        self.policies[ethical_policy.id] = ethical_policy
    
    def add_policy(self, policy: CompliancePolicy) -> bool:
        """Add a new compliance policy."""
        try:
            self.policies[policy.id] = policy
            self.logger.info(f"Added compliance policy: {policy.name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to add policy: {e}")
            return False
    
    def evaluate_compliance(self, content: str, prompt_id: str = "", 
                          prompt_version: str = "", policy_ids: List[str] = None) -> ComplianceAssessment:
        """Evaluate content against compliance policies."""
        assessment = ComplianceAssessment(
            prompt_id=prompt_id,
            prompt_version=prompt_version
        )
        
        # Determine which policies to evaluate
        policies_to_evaluate = policy_ids or list(self.policies.keys())
        assessment.policies_evaluated = policies_to_evaluate
        
        try:
            for policy_id in policies_to_evaluate:
                if policy_id not in self.policies:
                    continue
                
                policy = self.policies[policy_id]
                if not policy.is_active:
                    continue
                
                # Evaluate each rule in the policy
                for rule in policy.rules:
                    if not rule.enabled:
                        continue
                    
                    violations = self._evaluate_rule(rule, content, policy_id, prompt_id, prompt_version)
                    assessment.violations.extend(violations)
            
            # Calculate overall compliance status and score
            assessment.overall_status = self._calculate_compliance_status(assessment.violations)
            assessment.compliance_score = self._calculate_compliance_score(assessment.violations)
            
            self.logger.info(f"Compliance assessment completed: {len(assessment.violations)} violations found")
            
        except Exception as e:
            self.logger.error(f"Error during compliance evaluation: {e}")
            # Add error as critical violation
            error_violation = ComplianceViolation(
                policy_id="system",
                rule_id="error",
                prompt_id=prompt_id,
                prompt_version=prompt_version,
                violation_type="system_error",
                severity="critical",
                description=f"Compliance evaluation failed: {str(e)}",
                remediation="Review prompt manually for compliance issues"
            )
            assessment.violations.append(error_violation)
            assessment.overall_status = ComplianceStatus.NON_COMPLIANT
        
        return assessment 
   
    def _evaluate_rule(self, rule: PolicyRule, content: str, policy_id: str, 
                      prompt_id: str, prompt_version: str) -> List[ComplianceViolation]:
        """Evaluate a single policy rule against content."""
        violations = []
        
        try:
            if rule.rule_type == "regex":
                violations.extend(self._evaluate_regex_rule(rule, content, policy_id, prompt_id, prompt_version))
            elif rule.rule_type == "checklist":
                violations.extend(self._evaluate_checklist_rule(rule, content, policy_id, prompt_id, prompt_version))
            elif rule.rule_type == "function":
                violations.extend(self._evaluate_function_rule(rule, content, policy_id, prompt_id, prompt_version))
        
        except Exception as e:
            self.logger.error(f"Error evaluating rule {rule.name}: {e}")
            # Create violation for rule evaluation error
            violation = ComplianceViolation(
                policy_id=policy_id,
                rule_id=rule.id,
                prompt_id=prompt_id,
                prompt_version=prompt_version,
                violation_type="rule_evaluation_error",
                severity="medium",
                description=f"Failed to evaluate rule: {str(e)}",
                remediation="Review rule configuration and content manually"
            )
            violations.append(violation)
        
        return violations
    
    def _evaluate_regex_rule(self, rule: PolicyRule, content: str, policy_id: str, 
                           prompt_id: str, prompt_version: str) -> List[ComplianceViolation]:
        """Evaluate regex-based rule."""
        violations = []
        patterns = rule.rule_definition.get("patterns", [])
        
        import re
        for pattern in patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            
            for match in matches:
                violation = ComplianceViolation(
                    policy_id=policy_id,
                    rule_id=rule.id,
                    prompt_id=prompt_id,
                    prompt_version=prompt_version,
                    violation_type="pattern_match",
                    severity=rule.severity,
                    description=f"Rule '{rule.name}' violation detected",
                    evidence=self._get_context(content, match.start(), match.end()),
                    remediation=f"Review and address the issue identified by rule: {rule.description}"
                )
                violations.append(violation)
        
        return violations
    
    def _evaluate_checklist_rule(self, rule: PolicyRule, content: str, policy_id: str, 
                               prompt_id: str, prompt_version: str) -> List[ComplianceViolation]:
        """Evaluate checklist-based rule."""
        violations = []
        rule_def = rule.rule_definition
        
        # Check for required phrases
        required_phrases = rule_def.get("required_phrases", [])
        for phrase in required_phrases:
            if phrase.lower() not in content.lower():
                violation = ComplianceViolation(
                    policy_id=policy_id,
                    rule_id=rule.id,
                    prompt_id=prompt_id,
                    prompt_version=prompt_version,
                    violation_type="missing_required_phrase",
                    severity=rule.severity,
                    description=f"Required phrase '{phrase}' not found",
                    evidence=f"Missing: {phrase}",
                    remediation=f"Include the required phrase: {phrase}"
                )
                violations.append(violation)
        
        # Check for prohibited terms
        prohibited_terms = rule_def.get("prohibited_terms", [])
        for term in prohibited_terms:
            if term.lower() in content.lower():
                alternatives = rule_def.get("preferred_alternatives", [])
                alternative_text = f" Consider using: {', '.join(alternatives)}" if alternatives else ""
                
                violation = ComplianceViolation(
                    policy_id=policy_id,
                    rule_id=rule.id,
                    prompt_id=prompt_id,
                    prompt_version=prompt_version,
                    violation_type="prohibited_term",
                    severity=rule.severity,
                    description=f"Prohibited term '{term}' found",
                    evidence=f"Found: {term}",
                    remediation=f"Remove or replace the prohibited term.{alternative_text}"
                )
                violations.append(violation)
        
        return violations
    
    def _evaluate_function_rule(self, rule: PolicyRule, content: str, policy_id: str, 
                              prompt_id: str, prompt_version: str) -> List[ComplianceViolation]:
        """Evaluate function-based rule."""
        # This would implement custom function evaluation
        # For now, return empty list as placeholder
        return []
    
    def _calculate_compliance_status(self, violations: List[ComplianceViolation]) -> ComplianceStatus:
        """Calculate overall compliance status."""
        if not violations:
            return ComplianceStatus.COMPLIANT
        
        critical_violations = [v for v in violations if v.severity == "critical"]
        high_violations = [v for v in violations if v.severity == "high"]
        
        if critical_violations:
            return ComplianceStatus.NON_COMPLIANT
        elif high_violations:
            return ComplianceStatus.PARTIALLY_COMPLIANT
        else:
            return ComplianceStatus.PARTIALLY_COMPLIANT
    
    def _calculate_compliance_score(self, violations: List[ComplianceViolation]) -> float:
        """Calculate compliance score (0-1, where 1 is fully compliant)."""
        if not violations:
            return 1.0
        
        # Weight violations by severity
        severity_weights = {
            "critical": 1.0,
            "high": 0.8,
            "medium": 0.5,
            "low": 0.2
        }
        
        total_penalty = sum(severity_weights.get(v.severity, 0.5) for v in violations)
        
        # Normalize to 0-1 scale
        max_penalty = len(violations) * 1.0  # Assume all critical
        normalized_penalty = min(total_penalty / max_penalty, 1.0) if max_penalty > 0 else 0.0
        
        return max(0.0, 1.0 - normalized_penalty)
    
    def _get_context(self, content: str, start: int, end: int, context_size: int = 30) -> str:
        """Get context around a match."""
        context_start = max(0, start - context_size)
        context_end = min(len(content), end + context_size)
        return content[context_start:context_end]
    
    def get_policy(self, policy_id: str) -> Optional[CompliancePolicy]:
        """Get a policy by ID."""
        return self.policies.get(policy_id)
    
    def list_policies(self, policy_type: PolicyType = None, 
                     compliance_standard: ComplianceStandard = None) -> List[CompliancePolicy]:
        """List policies with optional filtering."""
        policies = list(self.policies.values())
        
        if policy_type:
            policies = [p for p in policies if p.policy_type == policy_type]
        
        if compliance_standard:
            policies = [p for p in policies if compliance_standard in p.compliance_standards]
        
        return policies


class ChecklistManager:
    """Manager for review checklists."""
    
    def __init__(self):
        """Initialize checklist manager."""
        self.logger = logging.getLogger(__name__)
        self.checklists: Dict[str, ReviewChecklist] = {}
        self._init_default_checklists()
    
    def _init_default_checklists(self):
        """Initialize default review checklists."""
        # Security Review Checklist
        security_checklist = ReviewChecklist(
            name="Security Review Checklist",
            description="Comprehensive security review checklist",
            applicable_standards=[ComplianceStandard.ISO_27001, ComplianceStandard.NIST],
            items=[
                ChecklistItem(
                    title="PII Data Review",
                    description="Verify no personally identifiable information is exposed",
                    category="Privacy",
                    required=True,
                    compliance_standards=[ComplianceStandard.GDPR],
                    validation_criteria="No email addresses, SSNs, or other PII detected"
                ),
                ChecklistItem(
                    title="Secret Scanning",
                    description="Ensure no secrets or credentials are exposed",
                    category="Security",
                    required=True,
                    compliance_standards=[ComplianceStandard.ISO_27001],
                    validation_criteria="No API keys, passwords, or tokens detected"
                ),
                ChecklistItem(
                    title="Code Injection Review",
                    description="Check for potential code injection vulnerabilities",
                    category="Security",
                    required=True,
                    validation_criteria="No unsafe code execution patterns detected"
                )
            ]
        )
        self.checklists[security_checklist.id] = security_checklist
        
        # Quality Review Checklist
        quality_checklist = ReviewChecklist(
            name="Quality Review Checklist",
            description="Quality and bias review checklist",
            applicable_standards=[ComplianceStandard.CUSTOM],
            items=[
                ChecklistItem(
                    title="Bias Assessment",
                    description="Review for potential bias in language and assumptions",
                    category="Ethics",
                    required=True,
                    validation_criteria="No gender, racial, or cultural bias detected"
                ),
                ChecklistItem(
                    title="Factual Accuracy",
                    description="Verify factual claims and avoid hallucination risks",
                    category="Quality",
                    required=True,
                    validation_criteria="All factual claims are verifiable or appropriately qualified"
                ),
                ChecklistItem(
                    title="Language Quality",
                    description="Ensure clear, coherent, and professional language",
                    category="Quality",
                    required=False,
                    validation_criteria="Language is clear, coherent, and appropriate for audience"
                )
            ]
        )
        self.checklists[quality_checklist.id] = quality_checklist
    
    def add_checklist(self, checklist: ReviewChecklist) -> bool:
        """Add a new review checklist."""
        try:
            self.checklists[checklist.id] = checklist
            self.logger.info(f"Added review checklist: {checklist.name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to add checklist: {e}")
            return False
    
    def get_checklist(self, checklist_id: str) -> Optional[ReviewChecklist]:
        """Get a checklist by ID."""
        return self.checklists.get(checklist_id)
    
    def list_checklists(self, compliance_standard: ComplianceStandard = None) -> List[ReviewChecklist]:
        """List checklists with optional filtering."""
        checklists = list(self.checklists.values())
        
        if compliance_standard:
            checklists = [c for c in checklists if compliance_standard in c.applicable_standards]
        
        return checklists


class ComplianceReporter:
    """Compliance reporting and export functionality."""
    
    def __init__(self):
        """Initialize compliance reporter."""
        self.logger = logging.getLogger(__name__)
    
    def generate_compliance_report(self, assessments: List[ComplianceAssessment], 
                                 report_format: str = "json") -> Union[str, Dict[str, Any]]:
        """Generate comprehensive compliance report."""
        if not assessments:
            return {"error": "No assessments provided"}
        
        # Aggregate statistics
        total_assessments = len(assessments)
        total_violations = sum(len(a.violations) for a in assessments)
        
        # Status distribution
        status_counts = {}
        for assessment in assessments:
            status = assessment.overall_status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Violation breakdown
        violation_by_severity = {}
        violation_by_type = {}
        violation_by_policy = {}
        
        for assessment in assessments:
            for violation in assessment.violations:
                # By severity
                severity = violation.severity
                violation_by_severity[severity] = violation_by_severity.get(severity, 0) + 1
                
                # By type
                v_type = violation.violation_type
                violation_by_type[v_type] = violation_by_type.get(v_type, 0) + 1
                
                # By policy
                policy = violation.policy_id
                violation_by_policy[policy] = violation_by_policy.get(policy, 0) + 1
        
        # Calculate compliance metrics
        compliant_count = status_counts.get("compliant", 0)
        compliance_rate = (compliant_count / total_assessments * 100) if total_assessments > 0 else 0
        
        avg_compliance_score = sum(a.compliance_score for a in assessments) / total_assessments if assessments else 0
        
        report_data = {
            "report_metadata": {
                "generated_at": datetime.now().isoformat(),
                "report_period": {
                    "start": min(a.assessed_at for a in assessments).isoformat(),
                    "end": max(a.assessed_at for a in assessments).isoformat()
                },
                "total_assessments": total_assessments,
                "report_format": report_format
            },
            "executive_summary": {
                "compliance_rate": compliance_rate,
                "average_compliance_score": avg_compliance_score,
                "total_violations": total_violations,
                "critical_violations": violation_by_severity.get("critical", 0),
                "high_violations": violation_by_severity.get("high", 0)
            },
            "compliance_status_distribution": status_counts,
            "violation_analysis": {
                "by_severity": violation_by_severity,
                "by_type": violation_by_type,
                "by_policy": violation_by_policy
            },
            "detailed_assessments": [a.to_dict() for a in assessments],
            "recommendations": self._generate_compliance_recommendations(
                violation_by_severity, violation_by_type, compliance_rate
            )
        }
        
        if report_format.lower() == "json":
            return json.dumps(report_data, indent=2, default=str)
        elif report_format.lower() == "yaml":
            return yaml.dump(report_data, default_flow_style=False)
        else:
            return report_data
    
    def export_violations_csv(self, assessments: List[ComplianceAssessment]) -> str:
        """Export violations to CSV format."""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            "Assessment ID", "Prompt ID", "Prompt Version", "Policy ID", "Rule ID",
            "Violation Type", "Severity", "Description", "Evidence", "Remediation",
            "Status", "Detected At"
        ])
        
        # Write violations
        for assessment in assessments:
            for violation in assessment.violations:
                writer.writerow([
                    assessment.assessment_id,
                    assessment.prompt_id,
                    assessment.prompt_version,
                    violation.policy_id,
                    violation.rule_id,
                    violation.violation_type,
                    violation.severity,
                    violation.description,
                    violation.evidence,
                    violation.remediation,
                    violation.status.value,
                    violation.detected_at.isoformat()
                ])
        
        return output.getvalue()
    
    def _generate_compliance_recommendations(self, violation_by_severity: Dict[str, int], 
                                          violation_by_type: Dict[str, int], 
                                          compliance_rate: float) -> List[str]:
        """Generate compliance improvement recommendations."""
        recommendations = []
        
        # Critical violations
        if violation_by_severity.get("critical", 0) > 0:
            recommendations.append(
                "Immediately address all critical compliance violations before production deployment"
            )
        
        # High violations
        if violation_by_severity.get("high", 0) > 5:
            recommendations.append(
                "Implement mandatory compliance review process for high-risk content"
            )
        
        # Low compliance rate
        if compliance_rate < 70:
            recommendations.append(
                "Establish comprehensive compliance training and automated checking processes"
            )
        
        # Specific violation types
        if violation_by_type.get("pattern_match", 0) > 10:
            recommendations.append(
                "Review and update content guidelines to prevent common pattern violations"
            )
        
        if violation_by_type.get("missing_required_phrase", 0) > 5:
            recommendations.append(
                "Implement template-based content creation to ensure required elements are included"
            )
        
        # General recommendations
        if not recommendations:
            recommendations.append("Continue monitoring compliance and maintain current standards")
        
        return recommendations


class ComplianceGovernanceFramework:
    """Main compliance and governance framework."""
    
    def __init__(self):
        """Initialize compliance governance framework."""
        self.logger = logging.getLogger(__name__)
        self.policy_engine = PolicyEngine()
        self.checklist_manager = ChecklistManager()
        self.reporter = ComplianceReporter()
    
    def evaluate_prompt_compliance(self, prompt_content: str, prompt_id: str = "", 
                                 prompt_version: str = "") -> ComplianceAssessment:
        """Evaluate a prompt for compliance violations."""
        return self.policy_engine.evaluate_compliance(
            prompt_content, prompt_id, prompt_version
        )
    
    def get_review_checklist(self, compliance_standards: List[ComplianceStandard] = None) -> ReviewChecklist:
        """Get appropriate review checklist for given compliance standards."""
        checklists = self.checklist_manager.list_checklists()
        
        if not compliance_standards:
            # Return default comprehensive checklist
            return checklists[0] if checklists else ReviewChecklist(name="Default Checklist")
        
        # Find best matching checklist
        best_match = None
        max_overlap = 0
        
        for checklist in checklists:
            overlap = len(set(compliance_standards) & set(checklist.applicable_standards))
            if overlap > max_overlap:
                max_overlap = overlap
                best_match = checklist
        
        return best_match or checklists[0] if checklists else ReviewChecklist(name="Default Checklist")
    
    def generate_compliance_report(self, assessments: List[ComplianceAssessment], 
                                 format_type: str = "json") -> str:
        """Generate compliance report in specified format."""
        return self.reporter.generate_compliance_report(assessments, format_type)
    
    def export_violations(self, assessments: List[ComplianceAssessment], 
                         format_type: str = "csv") -> str:
        """Export violations in specified format."""
        if format_type.lower() == "csv":
            return self.reporter.export_violations_csv(assessments)
        else:
            # Default to JSON
            violations = []
            for assessment in assessments:
                violations.extend([v.to_dict() for v in assessment.violations])
            return json.dumps(violations, indent=2, default=str)