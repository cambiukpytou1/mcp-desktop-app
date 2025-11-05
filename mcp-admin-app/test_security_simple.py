"""
Simple Security Tests
====================

Basic tests for security features to verify functionality.
"""

import unittest
from datetime import datetime

# Direct imports to avoid module issues
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.security.security_scanner import (
    SecurityScanner, SecurityScanResult, SecurityIssue, 
    SecurityRiskLevel, SecurityIssueType
)


class TestSecurityScanner(unittest.TestCase):
    """Test security scanner functionality."""
    
    def setUp(self):
        """Set up test security scanner."""
        self.scanner = SecurityScanner()
    
    def test_pii_detection(self):
        """Test PII detection in prompts."""
        content_with_pii = "Please send the report to john.doe@example.com"
        
        result = self.scanner.scan_prompt(content_with_pii, "test_prompt", "v1.0")
        
        self.assertIsInstance(result, SecurityScanResult)
        self.assertGreater(len(result.issues), 0)
        
        # Check for PII issues
        pii_issues = [i for i in result.issues if i.issue_type == SecurityIssueType.PII_DETECTED]
        self.assertGreater(len(pii_issues), 0)
    
    def test_secret_detection(self):
        """Test secret detection in prompts."""
        content_with_secrets = "Use this API key: AKIA1234567890123456"
        
        result = self.scanner.scan_prompt(content_with_secrets)
        
        secret_issues = [i for i in result.issues if i.issue_type == SecurityIssueType.SECRET_DETECTED]
        self.assertGreater(len(secret_issues), 0)
        
        # Check that evidence is redacted
        for issue in secret_issues:
            self.assertEqual(issue.evidence, "[REDACTED SECRET]")
    
    def test_clean_content(self):
        """Test scanning clean content with no issues."""
        clean_content = "Please summarize the following document for our team meeting."
        
        result = self.scanner.scan_prompt(clean_content)
        
        self.assertEqual(len(result.issues), 0)
        self.assertEqual(result.overall_risk_level, SecurityRiskLevel.LOW)
    
    def test_security_policy(self):
        """Test security policy retrieval."""
        policy = self.scanner.get_security_policy()
        
        self.assertIsInstance(policy, dict)
        self.assertIn("pii_detection", policy)
        self.assertIn("secret_detection", policy)
        self.assertIn("code_analysis", policy)
    
    def test_security_report_generation(self):
        """Test security report generation."""
        # Create multiple scan results
        test_contents = [
            "Clean content with no issues.",
            "Contact john.doe@example.com for support.",
            "Use API key: AKIA1234567890123456"
        ]
        
        scan_results = []
        for i, content in enumerate(test_contents):
            result = self.scanner.scan_prompt(content, f"prompt_{i}", "v1.0")
            scan_results.append(result)
        
        report = self.scanner.generate_security_report(scan_results)
        
        self.assertIsInstance(report, dict)
        self.assertIn("summary", report)
        self.assertIn("issue_breakdown", report)
        self.assertIn("recommendations", report)
        self.assertEqual(report["summary"]["total_scans"], 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)