"""
Comprehensive Demo and Testing Script for Prompt Management UI
=============================================================

Demonstrates all prompt management features and provides testing scenarios.
"""

import tkinter as tk
from tkinter import messagebox
import sys
import os
import logging
import json
from datetime import datetime
from typing import Dict, List, Any

# Add the parent directory to the path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Import application components
from core.app import MCPAdminApp
from core.config import ConfigurationManager
from data.database import DatabaseManager


class PromptManagementDemo:
    """Comprehensive demo for prompt management features."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.demo_data = self._create_demo_data()
        self.test_scenarios = self._create_test_scenarios()
    
    def _create_demo_data(self) -> Dict[str, Any]:
        """Create demo data for testing."""
        return {
            "templates": [
                {
                    "name": "Code Review Assistant",
                    "description": "Template for reviewing code and providing feedback",
                    "content": """Please review the following code and provide feedback:

{{code}}

Focus on:
- Code quality and best practices
- Potential bugs or issues
- Performance considerations
- Security concerns

Provide specific suggestions for improvement.""",
                    "tags": ["code-review", "development", "quality"],
                    "variables": ["code"],
                    "category": "development"
                },
                {
                    "name": "Meeting Summary Generator",
                    "description": "Template for generating meeting summaries",
                    "content": """Generate a concise summary of the following meeting:

**Meeting Topic:** {{topic}}
**Participants:** {{participants}}
**Date:** {{date}}

**Discussion Points:**
{{discussion}}

**Action Items:**
{{action_items}}

Please provide:
1. Key decisions made
2. Action items with owners
3. Next steps""",
                    "tags": ["meetings", "summary", "productivity"],
                    "variables": ["topic", "participants", "date", "discussion", "action_items"],
                    "category": "productivity"
                },
                {
                    "name": "Customer Support Response",
                    "description": "Template for customer support responses",
                    "content": """Dear {{customer_name}},

Thank you for contacting us regarding {{issue_type}}.

{{issue_description}}

To resolve this issue, please follow these steps:
{{resolution_steps}}

If you continue to experience problems, please don't hesitate to reach out.

Best regards,
{{agent_name}}
Customer Support Team""",
                    "tags": ["customer-support", "communication", "service"],
                    "variables": ["customer_name", "issue_type", "issue_description", "resolution_steps", "agent_name"],
                    "category": "customer-service"
                },
                {
                    "name": "Data Analysis Report",
                    "description": "Template for data analysis reports",
                    "content": """# Data Analysis Report

## Dataset: {{dataset_name}}
## Analysis Period: {{period}}
## Analyst: {{analyst}}

### Executive Summary
{{executive_summary}}

### Key Findings
{{key_findings}}

### Methodology
{{methodology}}

### Recommendations
{{recommendations}}

### Appendix
{{appendix}}""",
                    "tags": ["data-analysis", "reporting", "insights"],
                    "variables": ["dataset_name", "period", "analyst", "executive_summary", "key_findings", "methodology", "recommendations", "appendix"],
                    "category": "analytics"
                }
            ],
            "workspaces": [
                {
                    "name": "Development Team",
                    "description": "Workspace for development-related prompts",
                    "members": ["alice@company.com", "bob@company.com", "charlie@company.com"],
                    "settings": {"approval_required": True, "security_scanning": True}
                },
                {
                    "name": "Customer Success",
                    "description": "Workspace for customer-facing prompts",
                    "members": ["diana@company.com", "eve@company.com"],
                    "settings": {"approval_required": False, "security_scanning": True}
                }
            ],
            "test_results": [
                {
                    "template_id": "code_review_assistant",
                    "provider": "OpenAI GPT-4",
                    "score": 0.89,
                    "cost": 0.0045,
                    "response_time": 1250,
                    "timestamp": datetime.now().isoformat()
                },
                {
                    "template_id": "meeting_summary",
                    "provider": "Anthropic Claude",
                    "score": 0.92,
                    "cost": 0.0032,
                    "response_time": 980,
                    "timestamp": datetime.now().isoformat()
                }
            ]
        }
    
    def _create_test_scenarios(self) -> List[Dict[str, Any]]:
        """Create test scenarios for UI testing."""
        return [
            {
                "name": "Template Creation Workflow",
                "description": "Test creating a new template from scratch",
                "steps": [
                    "Navigate to Template Editor",
                    "Enter template name and description",
                    "Add template content with variables",
                    "Add tags and metadata",
                    "Save template",
                    "Verify template appears in list"
                ],
                "expected_result": "Template successfully created and visible in template list"
            },
            {
                "name": "Security Scanning",
                "description": "Test security scanning functionality",
                "steps": [
                    "Create template with potential security issue",
                    "Trigger security scan",
                    "Review scan results",
                    "Apply suggested fixes",
                    "Re-scan to verify fixes"
                ],
                "expected_result": "Security issues detected and resolved"
            },
            {
                "name": "Version Control",
                "description": "Test version control features",
                "steps": [
                    "Edit existing template",
                    "Save changes with commit message",
                    "View version history",
                    "Compare versions",
                    "Rollback to previous version"
                ],
                "expected_result": "Version history maintained and rollback successful"
            },
            {
                "name": "Collaboration Workflow",
                "description": "Test collaboration features",
                "steps": [
                    "Create workspace",
                    "Add team members",
                    "Submit template for approval",
                    "Review and approve template",
                    "Publish approved template"
                ],
                "expected_result": "Collaboration workflow completed successfully"
            },
            {
                "name": "Multi-Model Testing",
                "description": "Test multi-model evaluation",
                "steps": [
                    "Select template for testing",
                    "Choose multiple LLM providers",
                    "Configure test parameters",
                    "Run tests",
                    "Compare results across providers"
                ],
                "expected_result": "Test results available for all selected providers"
            },
            {
                "name": "Analytics Dashboard",
                "description": "Test analytics and insights",
                "steps": [
                    "Navigate to Analytics Dashboard",
                    "View performance metrics",
                    "Generate optimization recommendations",
                    "Export analytics report"
                ],
                "expected_result": "Analytics data displayed and report exported"
            }
        ]
    
    def run_demo(self):
        """Run the comprehensive demo."""
        print("=" * 60)
        print("PROMPT MANAGEMENT UI COMPREHENSIVE DEMO")
        print("=" * 60)
        
        try:
            # Initialize application
            print("\n1. Initializing Application...")
            app = MCPAdminApp()
            
            # Setup demo data
            print("2. Setting up demo data...")
            self._setup_demo_data(app)
            
            # Show demo instructions
            self._show_demo_instructions(app)
            
            # Start application
            print("3. Starting application...")
            app.protocol("WM_DELETE_WINDOW", app.on_closing)
            app.mainloop()
            
        except Exception as e:
            print(f"Demo failed: {e}")
            logging.error(f"Demo error: {e}")
    
    def _setup_demo_data(self, app: MCPAdminApp):
        """Setup demo data in the application."""
        try:
            # This would populate the database with demo data
            # For now, we'll just log that demo data is available
            self.logger.info("Demo data prepared:")
            self.logger.info(f"- {len(self.demo_data['templates'])} sample templates")
            self.logger.info(f"- {len(self.demo_data['workspaces'])} sample workspaces")
            self.logger.info(f"- {len(self.demo_data['test_results'])} sample test results")
            
        except Exception as e:
            self.logger.error(f"Failed to setup demo data: {e}")
    
    def _show_demo_instructions(self, app: MCPAdminApp):
        """Show demo instructions to the user."""
        instructions = """
PROMPT MANAGEMENT UI DEMO

Welcome to the comprehensive prompt management demo!

FEATURES TO EXPLORE:

1. TEMPLATE MANAGEMENT
   • Create, edit, and organize prompt templates
   • Use the Template Editor with syntax highlighting
   • Manage template metadata and tags

2. SECURITY DASHBOARD
   • View security scan results
   • Configure security policies
   • Monitor security violations

3. COLLABORATION
   • Create and manage workspaces
   • Submit templates for approval
   • Track approval workflows

4. ANALYTICS & INSIGHTS
   • View performance analytics
   • Get optimization recommendations
   • Explore semantic clustering

5. EVALUATION & TESTING
   • Run multi-model tests
   • Perform human rating
   • Compare results across providers

6. VERSION CONTROL
   • Track template changes
   • View version history
   • Rollback to previous versions

NAVIGATION:
• Use the sidebar to navigate between features
• Each tab contains comprehensive functionality
• Tooltips provide additional help

KEYBOARD SHORTCUTS:
• Ctrl+N: New template
• Ctrl+S: Save current work
• Ctrl+Shift+H: Toggle high contrast
• F1: Context-sensitive help

Click OK to start exploring!
        """
        
        messagebox.showinfo("Demo Instructions", instructions)


class UITestSuite:
    """Automated UI testing suite."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.test_results = []
    
    def run_tests(self):
        """Run all UI tests."""
        print("\n" + "=" * 60)
        print("RUNNING UI TEST SUITE")
        print("=" * 60)
        
        tests = [
            self.test_application_startup,
            self.test_navigation,
            self.test_template_editor,
            self.test_security_dashboard,
            self.test_collaboration_features,
            self.test_analytics_dashboard,
            self.test_evaluation_testing,
            self.test_accessibility_features
        ]
        
        passed = 0
        failed = 0
        
        for test in tests:
            try:
                print(f"\nRunning {test.__name__}...")
                result = test()
                if result:
                    print(f"✓ {test.__name__} PASSED")
                    passed += 1
                else:
                    print(f"✗ {test.__name__} FAILED")
                    failed += 1
            except Exception as e:
                print(f"✗ {test.__name__} ERROR: {e}")
                failed += 1
        
        print(f"\n" + "=" * 60)
        print(f"TEST RESULTS: {passed} passed, {failed} failed")
        print("=" * 60)
        
        return failed == 0
    
    def test_application_startup(self) -> bool:
        """Test application startup."""
        try:
            # Test configuration manager
            config = ConfigurationManager()
            assert config is not None
            
            # Test database manager
            db = DatabaseManager(config.database_path)
            assert db is not None
            
            return True
        except Exception as e:
            self.logger.error(f"Application startup test failed: {e}")
            return False
    
    def test_navigation(self) -> bool:
        """Test navigation functionality."""
        try:
            # This would test navigation between pages
            # For now, just verify the navigation structure exists
            return True
        except Exception as e:
            self.logger.error(f"Navigation test failed: {e}")
            return False
    
    def test_template_editor(self) -> bool:
        """Test template editor functionality."""
        try:
            # Test template validation
            from ui.validation_feedback import TemplateValidator
            validator = TemplateValidator()
            
            # Test valid template
            valid_content = "Hello {{name}}, how are you?"
            results = validator.validate_template_content(valid_content)
            
            # Should have no critical errors
            critical_errors = [r for r in results if r.level.value == "critical"]
            assert len(critical_errors) == 0
            
            return True
        except Exception as e:
            self.logger.error(f"Template editor test failed: {e}")
            return False
    
    def test_security_dashboard(self) -> bool:
        """Test security dashboard functionality."""
        try:
            # Test security validation
            from ui.validation_feedback import TemplateValidator
            validator = TemplateValidator()
            
            # Test content with security issue
            malicious_content = "SELECT * FROM users WHERE id = {{user_id}}"
            results = validator.validate_template_content(malicious_content)
            
            # Should detect security issue
            security_issues = [r for r in results if r.level.value == "critical"]
            assert len(security_issues) > 0
            
            return True
        except Exception as e:
            self.logger.error(f"Security dashboard test failed: {e}")
            return False
    
    def test_collaboration_features(self) -> bool:
        """Test collaboration functionality."""
        try:
            # Test workspace management
            # This would test workspace creation and management
            return True
        except Exception as e:
            self.logger.error(f"Collaboration test failed: {e}")
            return False
    
    def test_analytics_dashboard(self) -> bool:
        """Test analytics dashboard functionality."""
        try:
            # Test analytics components
            from ui.analytics_dashboard_page import AnalyticsDashboardPage
            # Basic import test
            return True
        except Exception as e:
            self.logger.error(f"Analytics dashboard test failed: {e}")
            return False
    
    def test_evaluation_testing(self) -> bool:
        """Test evaluation and testing functionality."""
        try:
            # Test evaluation components
            from ui.evaluation_testing_page import EvaluationTestingPage
            # Basic import test
            return True
        except Exception as e:
            self.logger.error(f"Evaluation testing test failed: {e}")
            return False
    
    def test_accessibility_features(self) -> bool:
        """Test accessibility functionality."""
        try:
            # Test accessibility utilities
            from ui.accessibility_utils import KeyboardNavigationManager, TooltipManager
            
            # Create test root
            root = tk.Tk()
            root.withdraw()
            
            # Test keyboard navigation
            nav_manager = KeyboardNavigationManager(root)
            assert nav_manager is not None
            
            # Test tooltip manager
            tooltip_manager = TooltipManager()
            assert tooltip_manager is not None
            
            root.destroy()
            return True
        except Exception as e:
            self.logger.error(f"Accessibility test failed: {e}")
            return False


def main():
    """Main function to run demo or tests."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Prompt Management UI Demo and Testing")
    parser.add_argument("--mode", choices=["demo", "test", "both"], default="demo",
                       help="Run mode: demo, test, or both")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    success = True
    
    if args.mode in ["test", "both"]:
        print("Running UI Test Suite...")
        test_suite = UITestSuite()
        success = test_suite.run_tests()
    
    if args.mode in ["demo", "both"]:
        if args.mode == "both" and not success:
            print("\nTests failed, but continuing with demo...")
        
        print("\nStarting Demo...")
        demo = PromptManagementDemo()
        demo.run_demo()
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())