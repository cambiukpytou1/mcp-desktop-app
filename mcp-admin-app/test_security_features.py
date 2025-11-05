"""
Unit Tests for Security Features
===============================

Comprehensive tests for security scanning, quality assurance, and compliance governance.
"""

import unittest
from datetime import datetime
from unittest.mock import Mock, patch

# Import the security services
from services.security.security_scanner import (
    SecurityScanner, SecurityScanResult, SecurityIssue, 
    SecurityRiskLevel, SecurityIssueType
)
from services.security.quality_assurance import (
    QualityAssuranceFramework, QualityAssessmentResult, QualityIssue,
    QualityIssueType, QualitySeverity, BiasDetector, HallucinationDetector
)
from services.security.compliance_governance import (
    ComplianceGovernanceFramework, PolicyEngine, ChecklistManager,
    CompliancePolicy, PolicyRule, ComplianceAssessment, ComplianceViolation,
    ComplianceStandard, PolicyType, ComplianceStatus
)


class TestSecurityScanner(unittest.TestCase):
    """Test security scanner functionality."""
    
    def setUp(self):
        """Set up test security scanner."""
        self.scanner = SecurityScanner()
    
    def test_pii_detection(self):
        """Test PII detection in prompts."""
        # Test content with PII
        content_with_pii = """
        Please send the report to john.doe@example.com
        My SSN is 123-45-6789 and credit card is 4532-1234-5678-9012
        """
        
        result = self.scanner.scan_prompt(content_with_pii, "test_prompt", "v1.0")
        
        self.assertIsInstance(result, SecurityScanResult)
        self.assertGreater(len(result.issues), 0)
        
        # Check for PII issues
        pii_issues = [i for i in result.issues if i.issue_type == SecurityIssueType.PII_DETECTED]
        self.assertGreater(len(pii_issues), 0)
        
        # Should detect email, SSN, and credit card
        self.assertGreaterEqual(len(pii_issues), 3)
    
    def test_secret_detection(self):
        """Test secret detection in prompts."""
        content_with_secrets = """
        Use this API key: AKIA1234567890123456
        The password is: mySecretPassword123
        """
        
        result = self.scanner.scan_prompt(content_with_secrets)
        
        secret_issues = [i for i in result.issues if i.issue_type == SecurityIssueType.SECRET_DETECTED]
        self.assertGreater(len(secret_issues), 0)
        
        # Check that evidence is redacted
        for issue in secret_issues:
            self.assertEqual(issue.evidence, "[REDACTED SECRET]")
    
    def test_unsafe_code_detection(self):
        """Test unsafe code pattern detection."""
        content_with_unsafe_code = """
        Execute this: system('rm -rf /')
        Also run: eval(user_input)
        """
        
        result = self.scanner.scan_prompt(content_with_unsafe_code)
        
        unsafe_issues = [i for i in result.issues if i.issue_type == SecurityIssueType.UNSAFE_CODE]
        self.assertGreater(len(unsafe_issues), 0)
    
    def test_clean_content(self):
        """Test scanning clean content with no issues."""
        clean_content = "Please summarize the following document for our team meeting."
        
        result = self.scanner.scan_prompt(clean_content)
        
        self.assertEqual(len(result.issues), 0)
        self.assertEqual(result.overall_risk_level, SecurityRiskLevel.LOW)
    
    def test_risk_level_calculation(self):
        """Test overall risk level calculation."""
        # Critical risk content
        critical_content = "Use API key: AKIA1234567890123456 and run system('rm -rf /')"
        result = self.scanner.scan_prompt(critical_content)
        self.assertEqual(result.overall_risk_level, SecurityRiskLevel.CRITICAL)
        
        # Medium risk content
        medium_content = "Contact me at test@example.com for more information"
        result = self.scanner.scan_prompt(medium_content)
        self.assertIn(result.overall_risk_level, [SecurityRiskLevel.MEDIUM, SecurityRiskLevel.LOW])


class TestQualityAssurance(unittest.TestCase):
    """Test quality assurance framework."""
    
    def setUp(self):
        """Set up test quality assurance framework."""
        self.qa_framework = QualityAssuranceFramework()
        self.bias_detector = BiasDetector()
        self.hallucination_detector = HallucinationDetector()
    
    def test_bias_detection(self):
        """Test bias detection in content."""
        biased_content = """
        Women are naturally better at nurturing roles.
        All men are more logical than emotional.
        """
        
        result = self.qa_framework.assess_quality(biased_content, "test_prompt", "v1.0")
        
        self.assertIsInstance(result, QualityAssessmentResult)
        bias_issues = [i for i in result.issues if i.issue_type == QualityIssueType.BIAS_DETECTED]
        self.assertGreater(len(bias_issues), 0)
        
        # Bias score should be lower for biased content
        self.assertLess(result.metrics.bias_score, 1.0)
    
    def test_hallucination_detection(self):
        """Test hallucination risk detection."""
        hallucination_content = """
        Studies definitely prove that 95% of people always prefer option A.
        It is absolutely certain that this will happen in the future.
        """
        
        result = self.qa_framework.assess_quality(hallucination_content)
        
        hallucination_issues = [i for i in result.issues if i.issue_type == QualityIssueType.HALLUCINATION_RISK]
        self.assertGreater(len(hallucination_issues), 0)
        
        # Hallucination risk should be higher
        self.assertGreater(result.metrics.hallucination_risk, 0.0)
    
    def test_coherence_analysis(self):
        """Test coherence analysis."""
        # Test with repetitive content
        repetitive_content = """
        This is a test. This is a test. This is a test. This is a test.
        The same word appears again and again and again and again.
        """
        
        result = self.qa_framework.assess_quality(repetitive_content)
        
        language_issues = [i for i in result.issues if i.issue_type == QualityIssueType.LANGUAGE_QUALITY]
        self.assertGreater(len(language_issues), 0)
    
    def test_quality_metrics_calculation(self):
        """Test quality metrics calculation."""
        good_content = "Please provide a clear and unbiased summary of the research findings."
        
        result = self.qa_framework.assess_quality(good_content)
        
        # Good content should have high scores
        self.assertGreater(result.metrics.overall_score, 0.7)
        self.assertGreater(result.metrics.bias_score, 0.8)
        self.assertLess(result.metrics.hallucination_risk, 0.3)
    
    def test_quality_report_generation(self):
        """Test quality report generation."""
        # Create multiple assessments
        assessments = []
        test_contents = [
            "Good quality content without issues.",
            "Women are always better at multitasking than men.",  # Biased
            "Studies definitely prove that 100% of users prefer this."  # Hallucination risk
        ]
        
        for i, content in enumerate(test_contents):
            assessment = self.qa_framework.assess_quality(content, f"prompt_{i}", "v1.0")
            assessments.append(assessment)
        
        report = self.qa_framework.generate_quality_report(assessments)
        
        self.assertIn("summary", report)
        self.assertIn("issue_breakdown", report)
        self.assertIn("recommendations", report)
        self.assertEqual(report["summary"]["total_assessments"], 3)



class TestComplianceGovernance(unittest.TestCase):
    """Test compliance governance framework."""
    
    def setUp(self):
        """Set up test compliance governance framework."""
        self.governance_framework = ComplianceGovernanceFramework()
        self.policy_engine = PolicyEngine()
        self.checklist_manager = ChecklistManager()
    
    def test_policy_evaluation(self):
        """Test policy evaluation against content."""
        # Content that violates multiple policies
        violating_content = """
        Contact john.doe@example.com with API key: AKIA1234567890123456
        All women are naturally better at customer service roles.
        """
        
        assessment = self.governance_framework.evaluate_prompt_compliance(
            violating_content, "test_prompt", "v1.0"
        )
        
        self.assertIsInstance(assessment, ComplianceAssessment)
        self.assertGreater(len(assessment.violations), 0)
        self.assertNotEqual(assessment.overall_status, ComplianceStatus.COMPLIANT)
        self.assertLess(assessment.compliance_score, 1.0)
    
    def test_gdpr_compliance(self):
        """Test GDPR compliance evaluation."""
        # Content with PII
        pii_content = "Please send the report to user@example.com and call 555-123-4567"
        
        assessment = self.policy_engine.evaluate_compliance(pii_content)
        
        # Should detect PII violations
        pii_violations = [v for v in assessment.violations if "PII" in v.description]
        self.assertGreater(len(pii_violations), 0)
    
    def test_security_compliance(self):
        """Test security compliance evaluation."""
        # Content with security issues
        security_content = """
        Use this password: mySecretPass123
        Execute: system('dangerous_command')
        """
        
        assessment = self.policy_engine.evaluate_compliance(security_content)
        
        # Should detect security violations
        security_violations = [v for v in assessment.violations 
                             if v.severity in ["critical", "high"]]
        self.assertGreater(len(security_violations), 0)
    
    def test_ethical_compliance(self):
        """Test ethical AI compliance evaluation."""
        # Content with bias
        biased_content = """
        Men are typically better at technical roles.
        Use the term 'guys' to address the team.
        """
        
        assessment = self.policy_engine.evaluate_compliance(biased_content)
        
        # Should detect bias violations
        bias_violations = [v for v in assessment.violations 
                          if "bias" in v.description.lower() or "inclusive" in v.description.lower()]
        self.assertGreater(len(bias_violations), 0)
    
    def test_custom_policy_creation(self):
        """Test creating and using custom policies."""
        # Create custom policy
        custom_policy = CompliancePolicy(
            name="Custom Test Policy",
            description="Test policy for unit testing",
            policy_type=PolicyType.CUSTOM,
            compliance_standards=[ComplianceStandard.CUSTOM],
            rules=[
                PolicyRule(
                    name="Forbidden Word Detection",
                    description="Detect forbidden test words",
                    rule_type="regex",
                    rule_definition={
                        "patterns": [r'\bforbidden\b', r'\bbanned\b']
                    },
                    severity="medium"
                )
            ]
        )
        
        # Add policy to engine
        success = self.policy_engine.add_policy(custom_policy)
        self.assertTrue(success)
        
        # Test content with forbidden words
        test_content = "This content contains a forbidden word and a banned term."
        
        assessment = self.policy_engine.evaluate_compliance(
            test_content, policy_ids=[custom_policy.id]
        )
        
        # Should detect violations
        self.assertGreater(len(assessment.violations), 0)
        
        # Check that violations are from our custom policy
        custom_violations = [v for v in assessment.violations if v.policy_id == custom_policy.id]
        self.assertGreater(len(custom_violations), 0)
    
    def test_checklist_management(self):
        """Test review checklist management."""
        # Get default checklists
        checklists = self.checklist_manager.list_checklists()
        self.assertGreater(len(checklists), 0)
        
        # Get security checklist
        security_checklists = self.checklist_manager.list_checklists(
            compliance_standard=ComplianceStandard.ISO_27001
        )
        self.assertGreater(len(security_checklists), 0)
        
        # Test getting specific checklist
        first_checklist = checklists[0]
        retrieved_checklist = self.checklist_manager.get_checklist(first_checklist.id)
        self.assertIsNotNone(retrieved_checklist)
        self.assertEqual(retrieved_checklist.id, first_checklist.id)
    
    def test_compliance_reporting(self):
        """Test compliance report generation."""
        # Create test assessments
        assessments = []
        
        test_cases = [
            ("Clean content with no issues", ComplianceStatus.COMPLIANT),
            ("Content with john.doe@example.com", ComplianceStatus.PARTIALLY_COMPLIANT),
            ("Content with API key: AKIA1234567890123456", ComplianceStatus.NON_COMPLIANT)
        ]
        
        for i, (content, expected_status) in enumerate(test_cases):
            assessment = self.governance_framework.evaluate_prompt_compliance(
                content, f"test_prompt_{i}", "v1.0"
            )
            assessments.append(assessment)
        
        # Generate report
        report_json = self.governance_framework.generate_compliance_report(assessments, "json")
        self.assertIsInstance(report_json, str)
        
        # Parse and validate report structure
        import json
        report_data = json.loads(report_json)
        
        self.assertIn("report_metadata", report_data)
        self.assertIn("executive_summary", report_data)
        self.assertIn("compliance_status_distribution", report_data)
        self.assertIn("violation_analysis", report_data)
        self.assertIn("recommendations", report_data)
        
        # Check executive summary
        summary = report_data["executive_summary"]
        self.assertEqual(summary["total_violations"], sum(len(a.violations) for a in assessments))
        self.assertGreaterEqual(summary["compliance_rate"], 0)
        self.assertLessEqual(summary["compliance_rate"], 100)
    
    def test_violation_export(self):
        """Test violation export functionality."""
        # Create assessment with violations
        violating_content = "Contact user@example.com with password: secret123"
        assessment = self.governance_framework.evaluate_prompt_compliance(violating_content)
        
        # Export violations as CSV
        csv_export = self.governance_framework.export_violations([assessment], "csv")
        self.assertIsInstance(csv_export, str)
        self.assertIn("Assessment ID", csv_export)  # Header should be present
        self.assertIn(assessment.assessment_id, csv_export)  # Data should be present
        
        # Export violations as JSON
        json_export = self.governance_framework.export_violations([assessment], "json")
        self.assertIsInstance(json_export, str)
        
        # Parse and validate JSON
        import json
        violations_data = json.loads(json_export)
        self.assertIsInstance(violations_data, list)
        if violations_data:  # If there are violations
            self.assertIn("id", violations_data[0])
            self.assertIn("severity", violations_data[0])
    
    def test_compliance_score_calculation(self):
        """Test compliance score calculation accuracy."""
        # Test with no violations
        clean_content = "This is clean content with no compliance issues."
        assessment = self.policy_engine.evaluate_compliance(clean_content)
        self.assertEqual(assessment.compliance_score, 1.0)
        self.assertEqual(assessment.overall_status, ComplianceStatus.COMPLIANT)
        
        # Test with critical violations
        critical_content = "API key: AKIA1234567890123456 and password: secret123"
        assessment = self.policy_engine.evaluate_compliance(critical_content)
        self.assertLess(assessment.compliance_score, 1.0)
        self.assertEqual(assessment.overall_status, ComplianceStatus.NON_COMPLIANT)
        
        # Test with medium violations
        medium_content = "Contact support at help@example.com for assistance."
        assessment = self.policy_engine.evaluate_compliance(medium_content)
        self.assertLess(assessment.compliance_score, 1.0)
        self.assertIn(assessment.overall_status, [
            ComplianceStatus.PARTIALLY_COMPLIANT, 
            ComplianceStatus.COMPLIANT
        ])


class TestIntegratedSecurityWorkflow(unittest.TestCase):
    """Test integrated security workflow combining all components."""
    
    def setUp(self):
        """Set up integrated security testing."""
        self.security_scanner = SecurityScanner()
        self.qa_framework = QualityAssuranceFramework()
        self.governance_framework = ComplianceGovernanceFramework()
    
    def test_comprehensive_security_assessment(self):
        """Test comprehensive security assessment workflow."""
        # Test content with multiple security, quality, and compliance issues
        problematic_content = """
        Dear team,
        
        Please use the API key AKIA1234567890123456 to access the system.
        Contact john.doe@example.com if you have issues.
        
        Studies definitely prove that women are always better at customer service.
        All men are naturally more technical and logical.
        
        Execute this command: system('rm -rf /tmp')
        
        It is absolutely certain that 100% of users will prefer this approach.
        """
        
        # Run security scan
        security_result = self.security_scanner.scan_prompt(
            problematic_content, "test_prompt", "v1.0"
        )
        
        # Run quality assessment
        quality_result = self.qa_framework.assess_quality(
            problematic_content, "test_prompt", "v1.0"
        )
        
        # Run compliance assessment
        compliance_result = self.governance_framework.evaluate_prompt_compliance(
            problematic_content, "test_prompt", "v1.0"
        )
        
        # Verify all assessments found issues
        self.assertGreater(len(security_result.issues), 0)
        self.assertGreater(len(quality_result.issues), 0)
        self.assertGreater(len(compliance_result.violations), 0)
        
        # Verify risk levels are appropriate
        self.assertIn(security_result.overall_risk_level, [
            SecurityRiskLevel.HIGH, SecurityRiskLevel.CRITICAL
        ])
        self.assertLess(quality_result.metrics.overall_score, 0.7)
        self.assertNotEqual(compliance_result.overall_status, ComplianceStatus.COMPLIANT)
        
        # Test that different components detect different types of issues
        security_issue_types = {issue.issue_type for issue in security_result.issues}
        quality_issue_types = {issue.issue_type for issue in quality_result.issues}
        
        # Should detect secrets, PII, unsafe code in security scan
        self.assertTrue(any(SecurityIssueType.SECRET_DETECTED in str(t) or 
                          SecurityIssueType.PII_DETECTED in str(t) or
                          SecurityIssueType.UNSAFE_CODE in str(t) 
                          for t in security_issue_types))
        
        # Should detect bias and hallucination in quality assessment
        self.assertTrue(any(QualityIssueType.BIAS_DETECTED in str(t) or 
                          QualityIssueType.HALLUCINATION_RISK in str(t)
                          for t in quality_issue_types))
    
    def test_clean_content_workflow(self):
        """Test workflow with clean, compliant content."""
        clean_content = """
        Please provide a comprehensive and unbiased analysis of the market trends.
        Ensure all data sources are properly cited and verified.
        Consider multiple perspectives in your evaluation.
        """
        
        # Run all assessments
        security_result = self.security_scanner.scan_prompt(clean_content)
        quality_result = self.qa_framework.assess_quality(clean_content)
        compliance_result = self.governance_framework.evaluate_prompt_compliance(clean_content)
        
        # Clean content should pass all assessments
        self.assertEqual(len(security_result.issues), 0)
        self.assertEqual(security_result.overall_risk_level, SecurityRiskLevel.LOW)
        
        self.assertGreater(quality_result.metrics.overall_score, 0.8)
        self.assertLess(quality_result.metrics.hallucination_risk, 0.2)
        
        self.assertEqual(compliance_result.overall_status, ComplianceStatus.COMPLIANT)
        self.assertEqual(compliance_result.compliance_score, 1.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)