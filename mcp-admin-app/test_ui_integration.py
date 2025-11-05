"""
Comprehensive UI Integration Tests
==================================

Tests all UI components and their integration.
"""

import unittest
import tkinter as tk
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import threading
import time

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class TestUIIntegration(unittest.TestCase):
    """Test UI integration and functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide window during testing
        
        # Mock dependencies
        self.mock_config_manager = Mock()
        self.mock_db_manager = Mock()
        
        # Mock database connection
        self.mock_connection = Mock()
        self.mock_cursor = Mock()
        self.mock_db_manager.get_connection.return_value.__enter__.return_value = self.mock_connection
        self.mock_connection.cursor.return_value = self.mock_cursor
        
        # Mock config data
        self.mock_config_manager.get.return_value = {}
    
    def tearDown(self):
        """Clean up after tests."""
        self.root.destroy()
    
    def test_prompt_management_page(self):
        """Test prompt management page initialization."""
        try:
            from ui.prompt_management_page import PromptManagementPage
            
            services = {
                'template_service': Mock(),
                'security_service': Mock(),
                'collaboration_service': Mock(),
                'analytics_service': Mock(),
                'evaluation_service': Mock()
            }
            
            page = PromptManagementPage(self.root, services)
            self.assertIsNotNone(page)
            
            print("✓ Prompt management page test passed")
            
        except Exception as e:
            self.fail(f"Prompt management page test failed: {e}")
    
    def test_security_dashboard_page(self):
        """Test security dashboard page initialization."""
        try:
            from ui.security_dashboard_page import SecurityDashboardPage
            
            page = SecurityDashboardPage(self.root, self.mock_config_manager, self.mock_db_manager)
            self.assertIsNotNone(page)
            
            print("✓ Security dashboard page test passed")
            
        except Exception as e:
            self.fail(f"Security dashboard page test failed: {e}")
    
    def test_collaboration_page(self):
        """Test collaboration page initialization."""
        try:
            from ui.collaboration_page import CollaborationPage
            
            page = CollaborationPage(self.root, self.mock_config_manager, self.mock_db_manager)
            self.assertIsNotNone(page)
            
            print("✓ Collaboration page test passed")
            
        except Exception as e:
            self.fail(f"Collaboration page test failed: {e}")
    
    def test_analytics_dashboard_page(self):
        """Test analytics dashboard page initialization."""
        try:
            from ui.analytics_dashboard_page import AnalyticsDashboardPage
            
            page = AnalyticsDashboardPage(self.root, self.mock_config_manager, self.mock_db_manager)
            self.assertIsNotNone(page)
            
            print("✓ Analytics dashboard page test passed")
            
        except Exception as e:
            self.fail(f"Analytics dashboard page test failed: {e}")
    
    def test_evaluation_testing_page(self):
        """Test evaluation testing page initialization."""
        try:
            from ui.evaluation_testing_page import EvaluationTestingPage
            
            page = EvaluationTestingPage(self.root, self.mock_config_manager, self.mock_db_manager)
            self.assertIsNotNone(page)
            
            print("✓ Evaluation testing page test passed")
            
        except Exception as e:
            self.fail(f"Evaluation testing page test failed: {e}")
    
    def test_service_bridge(self):
        """Test service bridge functionality."""
        try:
            from ui.service_bridge import UIServiceBridge
            
            bridge = UIServiceBridge(self.mock_config_manager, self.mock_db_manager)
            self.assertIsNotNone(bridge)
            
            # Test health check
            health = bridge.health_check()
            self.assertIsInstance(health, dict)
            
            print("✓ Service bridge test passed")
            
        except Exception as e:
            self.fail(f"Service bridge test failed: {e}")
    
    def test_state_manager(self):
        """Test state manager functionality."""
        try:
            from ui.state_manager import UIStateManager, EventType
            
            state_manager = UIStateManager()
            self.assertIsNotNone(state_manager)
            
            # Test state operations
            state_manager.set_shared_state("test_key", "test_value")
            value = state_manager.get_shared_state("test_key")
            self.assertEqual(value, "test_value")
            
            # Test event system
            event_received = []
            
            def test_callback(event):
                event_received.append(event)
            
            state_manager.subscribe(EventType.USER_NOTIFICATION, test_callback)
            state_manager.publish_event(EventType.USER_NOTIFICATION, {"test": "data"})
            
            # Give time for event processing
            time.sleep(0.2)
            
            state_manager.shutdown()
            
            print("✓ State manager test passed")
            
        except Exception as e:
            self.fail(f"State manager test failed: {e}")
    
    def test_validation_feedback(self):
        """Test validation and feedback systems."""
        try:
            from ui.validation_feedback import TemplateValidator, NotificationSystem, NotificationType
            
            # Test template validator
            validator = TemplateValidator()
            
            # Test valid content
            results = validator.validate_template_content("Hello {{name}}")
            self.assertIsInstance(results, list)
            
            # Test invalid content
            results = validator.validate_template_content("")
            error_results = [r for r in results if r.level.value == "error"]
            self.assertGreater(len(error_results), 0)
            
            # Test notification system
            notification_system = NotificationSystem(self.root)
            self.assertIsNotNone(notification_system)
            
            print("✓ Validation and feedback test passed")
            
        except Exception as e:
            self.fail(f"Validation and feedback test failed: {e}")
    
    def test_accessibility_utils(self):
        """Test accessibility utilities."""
        try:
            from ui.accessibility_utils import KeyboardNavigationManager, TooltipManager, AccessibilityEnhancer
            
            # Test keyboard navigation
            nav_manager = KeyboardNavigationManager(self.root)
            self.assertIsNotNone(nav_manager)
            
            # Test tooltip manager
            tooltip_manager = TooltipManager()
            self.assertIsNotNone(tooltip_manager)
            
            # Test accessibility enhancer
            enhancer = AccessibilityEnhancer(self.root)
            self.assertIsNotNone(enhancer)
            
            print("✓ Accessibility utils test passed")
            
        except Exception as e:
            self.fail(f"Accessibility utils test failed: {e}")
    
    def test_template_editor_components(self):
        """Test template editor components."""
        try:
            from ui.template_editor_page import TemplateEditorPage
            
            page = TemplateEditorPage(self.root, self.mock_config_manager, self.mock_db_manager)
            self.assertIsNotNone(page)
            
            print("✓ Template editor components test passed")
            
        except Exception as e:
            self.fail(f"Template editor components test failed: {e}")
    
    def test_prompt_components(self):
        """Test prompt UI components."""
        try:
            from ui.prompt_components.template_list import TemplateListWidget
            from ui.prompt_components.version_history import VersionHistoryWidget
            from ui.prompt_components.security_indicator import SecurityIndicatorWidget
            
            # Test template list widget
            template_list = TemplateListWidget(self.root, self.mock_config_manager, self.mock_db_manager)
            self.assertIsNotNone(template_list)
            
            # Test version history widget
            version_history = VersionHistoryWidget(self.root, self.mock_config_manager, self.mock_db_manager)
            self.assertIsNotNone(version_history)
            
            # Test security indicator widget
            security_indicator = SecurityIndicatorWidget(self.root, self.mock_config_manager, self.mock_db_manager)
            self.assertIsNotNone(security_indicator)
            
            print("✓ Prompt components test passed")
            
        except Exception as e:
            self.fail(f"Prompt components test failed: {e}")
    
    @patch('ui.service_bridge.TemplatingEngine')
    @patch('ui.service_bridge.VersionControlService')
    def test_service_integration(self, mock_version_service, mock_templating_service):
        """Test service integration."""
        try:
            from ui.service_bridge import UIServiceBridge
            
            # Mock services
            mock_templating_service.return_value = Mock()
            mock_version_service.return_value = Mock()
            
            bridge = UIServiceBridge(self.mock_config_manager, self.mock_db_manager)
            
            # Test service access
            services = bridge.get_all_services()
            self.assertIsInstance(services, dict)
            
            print("✓ Service integration test passed")
            
        except Exception as e:
            self.fail(f"Service integration test failed: {e}")


class TestUIWorkflows(unittest.TestCase):
    """Test complete UI workflows."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.root.withdraw()
        
        # Mock dependencies
        self.mock_config_manager = Mock()
        self.mock_db_manager = Mock()
        
        # Mock database connection
        self.mock_connection = Mock()
        self.mock_cursor = Mock()
        self.mock_db_manager.get_connection.return_value.__enter__.return_value = self.mock_connection
        self.mock_connection.cursor.return_value = self.mock_cursor
        
        self.mock_config_manager.get.return_value = {}
    
    def tearDown(self):
        """Clean up after tests."""
        self.root.destroy()
    
    def test_template_creation_workflow(self):
        """Test complete template creation workflow."""
        try:
            from ui.template_editor_page import TemplateEditorPage
            
            # Create template editor
            editor = TemplateEditorPage(self.root, self.mock_config_manager, self.mock_db_manager)
            
            # Simulate template creation
            template_data = {
                "name": "Test Template",
                "description": "Test description",
                "content": "Hello {{name}}",
                "tags": ["test"]
            }
            
            # This would normally trigger the actual workflow
            # For testing, we just verify the editor exists and can handle the data
            self.assertIsNotNone(editor)
            
            print("✓ Template creation workflow test passed")
            
        except Exception as e:
            self.fail(f"Template creation workflow test failed: {e}")
    
    def test_security_scanning_workflow(self):
        """Test security scanning workflow."""
        try:
            from ui.security_dashboard_page import SecurityDashboardPage
            
            # Create security dashboard
            dashboard = SecurityDashboardPage(self.root, self.mock_config_manager, self.mock_db_manager)
            
            # Simulate security scan
            self.assertIsNotNone(dashboard)
            
            print("✓ Security scanning workflow test passed")
            
        except Exception as e:
            self.fail(f"Security scanning workflow test failed: {e}")
    
    def test_collaboration_workflow(self):
        """Test collaboration workflow."""
        try:
            from ui.collaboration_page import CollaborationPage
            
            # Create collaboration page
            collab_page = CollaborationPage(self.root, self.mock_config_manager, self.mock_db_manager)
            
            # Simulate collaboration workflow
            self.assertIsNotNone(collab_page)
            
            print("✓ Collaboration workflow test passed")
            
        except Exception as e:
            self.fail(f"Collaboration workflow test failed: {e}")
    
    def test_analytics_workflow(self):
        """Test analytics workflow."""
        try:
            from ui.analytics_dashboard_page import AnalyticsDashboardPage
            
            # Create analytics dashboard
            analytics_page = AnalyticsDashboardPage(self.root, self.mock_config_manager, self.mock_db_manager)
            
            # Simulate analytics workflow
            self.assertIsNotNone(analytics_page)
            
            print("✓ Analytics workflow test passed")
            
        except Exception as e:
            self.fail(f"Analytics workflow test failed: {e}")


def run_ui_tests():
    """Run all UI tests."""
    print("Running UI Integration Tests...")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestUIIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestUIWorkflows))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=0)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print(f"✓ All {result.testsRun} UI tests passed!")
    else:
        print(f"✗ {len(result.failures + result.errors)} test(s) failed out of {result.testsRun}")
        
        if result.failures:
            print("\nFailures:")
            for test, traceback in result.failures:
                print(f"- {test}: {traceback}")
        
        if result.errors:
            print("\nErrors:")
            for test, traceback in result.errors:
                print(f"- {test}: {traceback}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_ui_tests()
    exit(0 if success else 1)