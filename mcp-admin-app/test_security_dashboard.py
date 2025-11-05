#!/usr/bin/env python3
"""
Test Security Dashboard Implementation
=====================================

Test script to verify the security dashboard and violation reporting functionality.
"""

import sys
import os
import tkinter as tk
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.security_dashboard_page import SecurityDashboardPage
from ui.security_violation_reporting import SecurityViolationReportingPage
from services.security.security_scanner import SecurityScanner
from services.security.compliance_governance import ComplianceGovernanceFramework
from models.base import generate_id


def create_sample_services():
    """Create sample services for testing."""
    return {
        'security_scanner': SecurityScanner(),
        'compliance_framework': ComplianceGovernanceFramework(),
        'template_service': None,  # Mock service
        'audit_service': None      # Mock service
    }


def create_sample_violations():
    """Create sample violations for testing."""
    return [
        {
            'id': generate_id(),
            'issue_type': 'pii_detected',
            'risk_level': 'high',
            'title': 'Email Address Detected',
            'description': 'Potential email address found in prompt content',
            'prompt_id': 'template_001',
            'prompt_version': '1.0',
            'evidence': 'Contact us at [MATCH]user@example.com[/MATCH] for support',
            'recommendation': 'Remove or replace the email address with a placeholder variable',
            'detected_at': datetime.now().isoformat(),
            'confidence': 0.95,
            'location': {'line': 5, 'start': 45, 'end': 62},
            'status': 'Open',
            'assigned_to': 'Unassigned',
            'priority': 'High'
        },
        {
            'id': generate_id(),
            'issue_type': 'secret_detected',
            'risk_level': 'critical',
            'title': 'API Key Detected',
            'description': 'Potential API key found in prompt content',
            'prompt_id': 'template_002',
            'prompt_version': '2.1',
            'evidence': '[REDACTED SECRET]',
            'recommendation': 'Remove the API key and use environment variables or secure credential management',
            'detected_at': datetime.now().isoformat(),
            'confidence': 0.98,
            'location': {'line': 12, 'start': 120, 'end': 155},
            'status': 'Open',
            'assigned_to': 'Security Team',
            'priority': 'Critical'
        },
        {
            'id': generate_id(),
            'issue_type': 'unsafe_code',
            'risk_level': 'medium',
            'title': 'System Command Detected',
            'description': 'Potentially unsafe system command execution pattern found',
            'prompt_id': 'template_003',
            'prompt_version': '1.5',
            'evidence': 'Execute the following: [MATCH]system("rm -rf /tmp")[/MATCH] to clean up',
            'recommendation': 'Replace with safe file operations or remove system command execution',
            'detected_at': datetime.now().isoformat(),
            'confidence': 0.85,
            'location': {'line': 8, 'start': 78, 'end': 95},
            'status': 'Under Review',
            'assigned_to': 'Development Team',
            'priority': 'Medium'
        }
    ]


def test_security_dashboard():
    """Test the security dashboard interface."""
    print("Testing Security Dashboard...")
    
    # Create main window
    root = tk.Tk()
    root.title("Security Dashboard Test")
    root.geometry("1200x800")
    
    # Create services
    services = create_sample_services()
    
    # Create security dashboard
    dashboard = SecurityDashboardPage(root, services)
    dashboard.pack(fill="both", expand=True)
    
    # Simulate violations
    sample_violations = create_sample_violations()
    dashboard.current_violations = sample_violations
    dashboard.violations_list.update_violations(sample_violations)
    
    # Update status based on violations
    from services.security.security_scanner import SecurityRiskLevel
    dashboard.status_indicator.update_status(SecurityRiskLevel.CRITICAL, "3 Security Issues Found")
    
    print("Security Dashboard created successfully!")
    print(f"- Loaded {len(sample_violations)} sample violations")
    print("- Status indicator updated")
    print("- Policy configuration panel loaded")
    
    # Start the GUI
    print("\nStarting GUI... Close the window to continue testing.")
    root.mainloop()


def test_violation_reporting():
    """Test the violation reporting interface."""
    print("\nTesting Violation Reporting Interface...")
    
    # Create main window
    root = tk.Tk()
    root.title("Violation Reporting Test")
    root.geometry("1000x700")
    
    # Create services
    services = create_sample_services()
    
    # Create violation reporting interface
    reporting = SecurityViolationReportingPage(root, services)
    reporting.pack(fill="both", expand=True)
    
    # Display a sample violation
    sample_violations = create_sample_violations()
    reporting.display_violation(sample_violations[0])
    
    print("Violation Reporting Interface created successfully!")
    print("- Violation details panel loaded")
    print("- Audit trail viewer initialized")
    print("- Sample violation displayed")
    
    # Start the GUI
    print("\nStarting GUI... Close the window to finish testing.")
    root.mainloop()


def test_security_scanner():
    """Test the security scanner functionality."""
    print("\nTesting Security Scanner...")
    
    # Create security scanner
    scanner = SecurityScanner()
    
    # Test content with various security issues
    test_content = """
    Welcome to our service! 
    
    For support, contact us at admin@company.com or call 555-123-4567.
    
    API Configuration:
    api_key = "sk-1234567890abcdef1234567890abcdef"
    
    Debug command: system("ls -la /etc/passwd")
    
    SQL Query: SELECT * FROM users WHERE id = 1 UNION SELECT password FROM admin
    """
    
    # Perform security scan
    result = scanner.scan_prompt(test_content, "test_prompt", "1.0")
    
    print(f"Security scan completed:")
    print(f"- Scan ID: {result.scan_id}")
    print(f"- Issues found: {len(result.issues)}")
    print(f"- Overall risk level: {result.overall_risk_level.value}")
    print(f"- Scan duration: {result.scan_duration:.3f} seconds")
    
    for i, issue in enumerate(result.issues, 1):
        print(f"\nIssue {i}:")
        print(f"  - Type: {issue.issue_type.value}")
        print(f"  - Risk Level: {issue.risk_level.value}")
        print(f"  - Title: {issue.title}")
        print(f"  - Confidence: {issue.confidence:.2%}")
    
    return result


def main():
    """Main test function."""
    print("=" * 60)
    print("Security Dashboard and Violation Reporting Test Suite")
    print("=" * 60)
    
    try:
        # Test security scanner
        scan_result = test_security_scanner()
        
        # Test security dashboard
        test_security_dashboard()
        
        # Test violation reporting
        test_violation_reporting()
        
        print("\n" + "=" * 60)
        print("All tests completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())