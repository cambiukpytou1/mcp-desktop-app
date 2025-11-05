"""
Security Scanner Service for MCP Admin Application
=================================================

Service for detecting security issues, PII, secrets, and unsafe content in prompts.
"""

import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from models.base import generate_id


class SecurityRiskLevel(Enum):
    """Security risk level enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SecurityIssueType(Enum):
    """Security issue type enumeration."""
    PII_DETECTED = "pii_detected"
    SECRET_DETECTED = "secret_detected"
    UNSAFE_CODE = "unsafe_code"
    INJECTION_RISK = "injection_risk"
    PRIVACY_VIOLATION = "privacy_violation"
    COMPLIANCE_VIOLATION = "compliance_violation"
    MALICIOUS_CONTENT = "malicious_content"


@dataclass
class SecurityIssue:
    """Security issue detection result."""
    id: str = field(default_factory=generate_id)
    issue_type: SecurityIssueType = SecurityIssueType.PII_DETECTED
    risk_level: SecurityRiskLevel = SecurityRiskLevel.MEDIUM
    title: str = ""
    description: str = ""
    location: Dict[str, Any] = field(default_factory=dict)  # Line, column, context
    evidence: str = ""  # Redacted evidence
    recommendation: str = ""
    confidence: float = 0.8
    detected_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "issue_type": self.issue_type.value,
            "risk_level": self.risk_level.value,
            "title": self.title,
            "description": self.description,
            "location": self.location,
            "evidence": self.evidence,
            "recommendation": self.recommendation,
            "confidence": self.confidence,
            "detected_at": self.detected_at.isoformat()
        }


@dataclass
class SecurityScanResult:
    """Security scan result containing all detected issues."""
    scan_id: str = field(default_factory=generate_id)
    prompt_id: str = ""
    prompt_version: str = ""
    issues: List[SecurityIssue] = field(default_factory=list)
    overall_risk_level: SecurityRiskLevel = SecurityRiskLevel.LOW
    scan_duration: float = 0.0
    scanned_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "scan_id": self.scan_id,
            "prompt_id": self.prompt_id,
            "prompt_version": self.prompt_version,
            "issues": [issue.to_dict() for issue in self.issues],
            "overall_risk_level": self.overall_risk_level.value,
            "scan_duration": self.scan_duration,
            "scanned_at": self.scanned_at.isoformat(),
            "issue_count": len(self.issues),
            "critical_issues": len([i for i in self.issues if i.risk_level == SecurityRiskLevel.CRITICAL]),
            "high_issues": len([i for i in self.issues if i.risk_level == SecurityRiskLevel.HIGH])
        }


class SecurityScanner:
    """Security scanner for detecting various security issues in prompts."""
    
    def __init__(self):
        """Initialize the security scanner."""
        self.logger = logging.getLogger(__name__)
        self._init_patterns()
    
    def _init_patterns(self):
        """Initialize security detection patterns."""
        # PII patterns
        self.pii_patterns = {
            "ssn": {
                "pattern": r'\b\d{3}-?\d{2}-?\d{4}\b',
                "description": "Social Security Number",
                "risk_level": SecurityRiskLevel.HIGH
            },
            "credit_card": {
                "pattern": r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
                "description": "Credit Card Number",
                "risk_level": SecurityRiskLevel.HIGH
            },
            "email": {
                "pattern": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                "description": "Email Address",
                "risk_level": SecurityRiskLevel.MEDIUM
            },
            "phone": {
                "pattern": r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b',
                "description": "Phone Number",
                "risk_level": SecurityRiskLevel.MEDIUM
            },
            "ip_address": {
                "pattern": r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
                "description": "IP Address",
                "risk_level": SecurityRiskLevel.LOW
            }
        }
        
        # Secret patterns
        self.secret_patterns = {
            "api_key": {
                "pattern": r'(?i)(?:api[_-]?key|apikey)\s*[:=]\s*["\']?([a-zA-Z0-9_-]{20,})["\']?',
                "description": "API Key",
                "risk_level": SecurityRiskLevel.CRITICAL
            },
            "password": {
                "pattern": r'(?i)(?:password|passwd|pwd)\s*[:=]\s*["\']?([^\s"\']{8,})["\']?',
                "description": "Password",
                "risk_level": SecurityRiskLevel.CRITICAL
            },
            "token": {
                "pattern": r'(?i)(?:token|auth[_-]?token)\s*[:=]\s*["\']?([a-zA-Z0-9_-]{20,})["\']?',
                "description": "Authentication Token",
                "risk_level": SecurityRiskLevel.CRITICAL
            },
            "aws_key": {
                "pattern": r'AKIA[0-9A-Z]{16}',
                "description": "AWS Access Key",
                "risk_level": SecurityRiskLevel.CRITICAL
            },
            "github_token": {
                "pattern": r'ghp_[a-zA-Z0-9]{36}',
                "description": "GitHub Personal Access Token",
                "risk_level": SecurityRiskLevel.CRITICAL
            }
        }
        
        # Unsafe code patterns
        self.unsafe_code_patterns = {
            "system_call": {
                "pattern": r'(?i)(?:system|exec|eval|subprocess|os\.system)\s*\(',
                "description": "System Command Execution",
                "risk_level": SecurityRiskLevel.HIGH
            },
            "file_access": {
                "pattern": r'(?i)(?:open|file|read|write)\s*\(["\']?(?:/|\\|\.\.)',
                "description": "File System Access",
                "risk_level": SecurityRiskLevel.MEDIUM
            },
            "network_call": {
                "pattern": r'(?i)(?:requests|urllib|http|socket)\.',
                "description": "Network Operation",
                "risk_level": SecurityRiskLevel.MEDIUM
            },
            "shell_injection": {
                "pattern": r'(?i)(?:;|\||&|`|\$\()',
                "description": "Shell Injection Risk",
                "risk_level": SecurityRiskLevel.HIGH
            }
        }
        
        # Injection patterns
        self.injection_patterns = {
            "sql_injection": {
                "pattern": r'(?i)(?:union|select|insert|update|delete|drop|create|alter)\s+(?:all\s+)?(?:distinct\s+)?(?:from|into|table|database)',
                "description": "SQL Injection Pattern",
                "risk_level": SecurityRiskLevel.HIGH
            },
            "xss_pattern": {
                "pattern": r'(?i)<script[^>]*>|javascript:|on\w+\s*=',
                "description": "Cross-Site Scripting (XSS) Pattern",
                "risk_level": SecurityRiskLevel.HIGH
            },
            "command_injection": {
                "pattern": r'(?i)(?:rm\s+-rf|del\s+/|format\s+c:|shutdown|reboot)',
                "description": "Command Injection Pattern",
                "risk_level": SecurityRiskLevel.CRITICAL
            }
        }
        
        # Malicious content patterns
        self.malicious_patterns = {
            "phishing": {
                "pattern": r'(?i)(?:click\s+here|verify\s+account|urgent\s+action|suspended\s+account)',
                "description": "Phishing Content",
                "risk_level": SecurityRiskLevel.MEDIUM
            },
            "social_engineering": {
                "pattern": r'(?i)(?:don\'t\s+tell|keep\s+secret|between\s+us|confidential)',
                "description": "Social Engineering Pattern",
                "risk_level": SecurityRiskLevel.MEDIUM
            }
        }
    
    def scan_prompt(self, prompt_content: str, prompt_id: str = "", 
                   prompt_version: str = "") -> SecurityScanResult:
        """Scan a prompt for security issues."""
        start_time = datetime.now()
        
        result = SecurityScanResult(
            prompt_id=prompt_id,
            prompt_version=prompt_version
        )
        
        try:
            # Scan for different types of security issues
            result.issues.extend(self._scan_pii(prompt_content))
            result.issues.extend(self._scan_secrets(prompt_content))
            result.issues.extend(self._scan_unsafe_code(prompt_content))
            result.issues.extend(self._scan_injection_risks(prompt_content))
            result.issues.extend(self._scan_malicious_content(prompt_content))
            
            # Determine overall risk level
            result.overall_risk_level = self._calculate_overall_risk(result.issues)
            
            # Calculate scan duration
            end_time = datetime.now()
            result.scan_duration = (end_time - start_time).total_seconds()
            
            self.logger.info(f"Security scan completed for prompt {prompt_id}: {len(result.issues)} issues found")
            
        except Exception as e:
            self.logger.error(f"Error during security scan: {e}")
            # Add error as critical issue
            error_issue = SecurityIssue(
                issue_type=SecurityIssueType.COMPLIANCE_VIOLATION,
                risk_level=SecurityRiskLevel.CRITICAL,
                title="Security Scan Error",
                description=f"Failed to complete security scan: {str(e)}",
                recommendation="Review prompt manually for security issues"
            )
            result.issues.append(error_issue)
            result.overall_risk_level = SecurityRiskLevel.CRITICAL
        
        return result
    
    def _scan_pii(self, content: str) -> List[SecurityIssue]:
        """Scan for Personally Identifiable Information (PII)."""
        issues = []
        
        for pii_type, pattern_info in self.pii_patterns.items():
            matches = re.finditer(pattern_info["pattern"], content, re.IGNORECASE)
            
            for match in matches:
                # Redact the actual PII for evidence
                evidence = self._redact_sensitive_data(match.group(0))
                
                issue = SecurityIssue(
                    issue_type=SecurityIssueType.PII_DETECTED,
                    risk_level=pattern_info["risk_level"],
                    title=f"{pattern_info['description']} Detected",
                    description=f"Potential {pattern_info['description'].lower()} found in prompt content",
                    location={
                        "start": match.start(),
                        "end": match.end(),
                        "line": self._get_line_number(content, match.start())
                    },
                    evidence=evidence,
                    recommendation=f"Remove or replace the {pattern_info['description'].lower()} with a placeholder",
                    confidence=0.9
                )
                issues.append(issue)
        
        return issues
    
    def _scan_secrets(self, content: str) -> List[SecurityIssue]:
        """Scan for secrets and credentials."""
        issues = []
        
        for secret_type, pattern_info in self.secret_patterns.items():
            matches = re.finditer(pattern_info["pattern"], content, re.IGNORECASE)
            
            for match in matches:
                # Completely redact secrets
                evidence = "[REDACTED SECRET]"
                
                issue = SecurityIssue(
                    issue_type=SecurityIssueType.SECRET_DETECTED,
                    risk_level=pattern_info["risk_level"],
                    title=f"{pattern_info['description']} Detected",
                    description=f"Potential {pattern_info['description'].lower()} found in prompt content",
                    location={
                        "start": match.start(),
                        "end": match.end(),
                        "line": self._get_line_number(content, match.start())
                    },
                    evidence=evidence,
                    recommendation=f"Remove the {pattern_info['description'].lower()} and use environment variables or secure storage",
                    confidence=0.95
                )
                issues.append(issue)
        
        return issues
    
    def _scan_unsafe_code(self, content: str) -> List[SecurityIssue]:
        """Scan for unsafe code patterns."""
        issues = []
        
        for code_type, pattern_info in self.unsafe_code_patterns.items():
            matches = re.finditer(pattern_info["pattern"], content, re.IGNORECASE)
            
            for match in matches:
                issue = SecurityIssue(
                    issue_type=SecurityIssueType.UNSAFE_CODE,
                    risk_level=pattern_info["risk_level"],
                    title=f"{pattern_info['description']} Detected",
                    description=f"Potentially unsafe code pattern: {pattern_info['description'].lower()}",
                    location={
                        "start": match.start(),
                        "end": match.end(),
                        "line": self._get_line_number(content, match.start())
                    },
                    evidence=self._get_context(content, match.start(), match.end()),
                    recommendation="Review and sanitize code execution patterns",
                    confidence=0.8
                )
                issues.append(issue)
        
        return issues
    
    def _scan_injection_risks(self, content: str) -> List[SecurityIssue]:
        """Scan for injection attack patterns."""
        issues = []
        
        for injection_type, pattern_info in self.injection_patterns.items():
            matches = re.finditer(pattern_info["pattern"], content, re.IGNORECASE)
            
            for match in matches:
                issue = SecurityIssue(
                    issue_type=SecurityIssueType.INJECTION_RISK,
                    risk_level=pattern_info["risk_level"],
                    title=f"{pattern_info['description']} Detected",
                    description=f"Potential injection attack pattern: {pattern_info['description'].lower()}",
                    location={
                        "start": match.start(),
                        "end": match.end(),
                        "line": self._get_line_number(content, match.start())
                    },
                    evidence=self._get_context(content, match.start(), match.end()),
                    recommendation="Sanitize input and use parameterized queries or safe APIs",
                    confidence=0.85
                )
                issues.append(issue)
        
        return issues
    
    def _scan_malicious_content(self, content: str) -> List[SecurityIssue]:
        """Scan for malicious content patterns."""
        issues = []
        
        for malicious_type, pattern_info in self.malicious_patterns.items():
            matches = re.finditer(pattern_info["pattern"], content, re.IGNORECASE)
            
            for match in matches:
                issue = SecurityIssue(
                    issue_type=SecurityIssueType.MALICIOUS_CONTENT,
                    risk_level=pattern_info["risk_level"],
                    title=f"{pattern_info['description']} Detected",
                    description=f"Potentially malicious content: {pattern_info['description'].lower()}",
                    location={
                        "start": match.start(),
                        "end": match.end(),
                        "line": self._get_line_number(content, match.start())
                    },
                    evidence=self._get_context(content, match.start(), match.end()),
                    recommendation="Review content for malicious intent and remove if necessary",
                    confidence=0.7
                )
                issues.append(issue)
        
        return issues
    
    def _calculate_overall_risk(self, issues: List[SecurityIssue]) -> SecurityRiskLevel:
        """Calculate overall risk level based on detected issues."""
        if not issues:
            return SecurityRiskLevel.LOW
        
        # Count issues by risk level
        critical_count = sum(1 for issue in issues if issue.risk_level == SecurityRiskLevel.CRITICAL)
        high_count = sum(1 for issue in issues if issue.risk_level == SecurityRiskLevel.HIGH)
        medium_count = sum(1 for issue in issues if issue.risk_level == SecurityRiskLevel.MEDIUM)
        
        # Determine overall risk
        if critical_count > 0:
            return SecurityRiskLevel.CRITICAL
        elif high_count > 0:
            return SecurityRiskLevel.HIGH
        elif medium_count > 2:  # Multiple medium issues = high risk
            return SecurityRiskLevel.HIGH
        elif medium_count > 0:
            return SecurityRiskLevel.MEDIUM
        else:
            return SecurityRiskLevel.LOW
    
    def _redact_sensitive_data(self, data: str) -> str:
        """Redact sensitive data for evidence."""
        if len(data) <= 4:
            return "*" * len(data)
        
        # Show first and last 2 characters, redact middle
        return data[:2] + "*" * (len(data) - 4) + data[-2:]
    
    def _get_line_number(self, content: str, position: int) -> int:
        """Get line number for a given position in content."""
        return content[:position].count('\n') + 1
    
    def _get_context(self, content: str, start: int, end: int, context_size: int = 50) -> str:
        """Get context around a match for evidence."""
        context_start = max(0, start - context_size)
        context_end = min(len(content), end + context_size)
        
        context = content[context_start:context_end]
        
        # Highlight the match
        match_start = start - context_start
        match_end = end - context_start
        
        return (
            context[:match_start] + 
            "[MATCH]" + 
            context[match_start:match_end] + 
            "[/MATCH]" + 
            context[match_end:]
        )
    
    def get_security_policy(self) -> Dict[str, Any]:
        """Get current security policy configuration."""
        return {
            "pii_detection": {
                "enabled": True,
                "patterns": list(self.pii_patterns.keys()),
                "risk_levels": {k: v["risk_level"].value for k, v in self.pii_patterns.items()}
            },
            "secret_detection": {
                "enabled": True,
                "patterns": list(self.secret_patterns.keys()),
                "risk_levels": {k: v["risk_level"].value for k, v in self.secret_patterns.items()}
            },
            "code_analysis": {
                "enabled": True,
                "patterns": list(self.unsafe_code_patterns.keys()),
                "risk_levels": {k: v["risk_level"].value for k, v in self.unsafe_code_patterns.items()}
            },
            "injection_detection": {
                "enabled": True,
                "patterns": list(self.injection_patterns.keys()),
                "risk_levels": {k: v["risk_level"].value for k, v in self.injection_patterns.items()}
            },
            "malicious_content": {
                "enabled": True,
                "patterns": list(self.malicious_patterns.keys()),
                "risk_levels": {k: v["risk_level"].value for k, v in self.malicious_patterns.items()}
            }
        }
    
    def update_security_policy(self, policy_updates: Dict[str, Any]) -> bool:
        """Update security policy configuration."""
        try:
            # This would typically update a configuration file or database
            # For now, we'll just log the update
            self.logger.info(f"Security policy update requested: {policy_updates}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to update security policy: {e}")
            return False
    
    def generate_security_report(self, scan_results: List[SecurityScanResult]) -> Dict[str, Any]:
        """Generate a comprehensive security report from multiple scan results."""
        if not scan_results:
            return {
                "summary": "No scan results provided",
                "total_scans": 0,
                "total_issues": 0
            }
        
        # Aggregate statistics
        total_issues = sum(len(result.issues) for result in scan_results)
        issue_types = {}
        risk_levels = {}
        
        for result in scan_results:
            for issue in result.issues:
                # Count by issue type
                issue_type = issue.issue_type.value
                issue_types[issue_type] = issue_types.get(issue_type, 0) + 1
                
                # Count by risk level
                risk_level = issue.risk_level.value
                risk_levels[risk_level] = risk_levels.get(risk_level, 0) + 1
        
        # Calculate risk distribution
        total_prompts = len(scan_results)
        clean_prompts = len([r for r in scan_results if not r.issues])
        risky_prompts = total_prompts - clean_prompts
        
        return {
            "summary": {
                "total_scans": total_prompts,
                "total_issues": total_issues,
                "clean_prompts": clean_prompts,
                "risky_prompts": risky_prompts,
                "risk_percentage": (risky_prompts / total_prompts * 100) if total_prompts > 0 else 0
            },
            "issue_breakdown": {
                "by_type": issue_types,
                "by_risk_level": risk_levels
            },
            "recommendations": self._generate_recommendations(issue_types, risk_levels),
            "generated_at": datetime.now().isoformat()
        }
    
    def _generate_recommendations(self, issue_types: Dict[str, int], 
                                risk_levels: Dict[str, int]) -> List[str]:
        """Generate security recommendations based on detected issues."""
        recommendations = []
        
        # PII recommendations
        if issue_types.get("pii_detected", 0) > 0:
            recommendations.append(
                "Implement PII detection and redaction in your prompt development workflow"
            )
        
        # Secret recommendations
        if issue_types.get("secret_detected", 0) > 0:
            recommendations.append(
                "Use environment variables or secure vaults for storing secrets and credentials"
            )
        
        # Code safety recommendations
        if issue_types.get("unsafe_code", 0) > 0:
            recommendations.append(
                "Review code execution patterns and implement sandboxing for dynamic code"
            )
        
        # Injection recommendations
        if issue_types.get("injection_risk", 0) > 0:
            recommendations.append(
                "Implement input validation and sanitization to prevent injection attacks"
            )
        
        # Critical risk recommendations
        if risk_levels.get("critical", 0) > 0:
            recommendations.append(
                "Address critical security issues immediately before deploying to production"
            )
        
        # High risk recommendations
        if risk_levels.get("high", 0) > 2:
            recommendations.append(
                "Implement mandatory security review process for prompts with high-risk issues"
            )
        
        return recommendations