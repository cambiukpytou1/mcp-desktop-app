"""
Simple UI Integration Tests
===========================

Basic tests to verify UI components can be imported and initialized.
"""

import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_imports():
    """Test that all UI components can be imported."""
    print("Testing UI component imports...")
    
    try:
        # Test core UI components
        from ui.service_bridge import UIServiceBridge
        print("✓ Service bridge imported")
        
        from ui.state_manager import UIStateManager
        print("✓ State manager imported")
        
        from ui.validation_feedback import TemplateValidator, NotificationSystem
        print("✓ Validation and feedback imported")
        
        from ui.accessibility_utils import KeyboardNavigationManager, TooltipManager
        print("✓ Accessibility utils imported")
        
        # Test page components
        from ui.template_editor_page import TemplateEditorPage
        print("✓ Template editor page imported")
        
        from ui.security_dashboard_page import SecurityDashboardPage
        print("✓ Security dashboard page imported")
        
        from ui.collaboration_page import CollaborationPage
        print("✓ Collaboration page imported")
        
        from ui.analytics_dashboard_page import AnalyticsDashboardPage
        print("✓ Analytics dashboard page imported")
        
        from ui.evaluation_testing_page import EvaluationTestingPage
        print("✓ Evaluation testing page imported")
        
        # Test prompt components
        from ui.prompt_components.template_list import TemplateListWidget
        print("✓ Template list widget imported")
        
        from ui.prompt_components.version_history import VersionHistoryWidget
        print("✓ Version history widget imported")
        
        from ui.prompt_components.security_indicator import SecurityIndicatorWidget
        print("✓ Security indicator widget imported")
        
        from ui.prompt_components.optimization_recommendations_simple import OptimizationRecommendationsWidget
        print("✓ Optimization recommendations widget imported")
        
        return True
        
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False


def test_basic_functionality():
    """Test basic functionality without UI."""
    print("\nTesting basic functionality...")
    
    try:
        # Test template validation
        from ui.validation_feedback import TemplateValidator
        validator = TemplateValidator()
        
        # Test valid template
        results = validator.validate_template_content("Hello {{name}}")
        print(f"✓ Template validation works ({len(results)} results)")
        
        # Test state manager
        from ui.state_manager import UIStateManager
        state_manager = UIStateManager()
        
        # Test state operations
        state_manager.set_shared_state("test", "value")
        value = state_manager.get_shared_state("test")
        assert value == "value"
        print("✓ State manager works")
        
        state_manager.shutdown()
        
        return True
        
    except Exception as e:
        print(f"✗ Functionality test failed: {e}")
        return False


def test_application_structure():
    """Test application structure."""
    print("\nTesting application structure...")
    
    try:
        # Test main application import
        from core.app import MCPAdminApp
        print("✓ Main application can be imported")
        
        # Test configuration
        from core.config import ConfigurationManager
        config = ConfigurationManager()
        print("✓ Configuration manager works")
        
        return True
        
    except Exception as e:
        print(f"✗ Application structure test failed: {e}")
        return False


def main():
    """Run all simple tests."""
    print("=" * 60)
    print("SIMPLE UI INTEGRATION TESTS")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_basic_functionality,
        test_application_structure
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} failed with exception: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("✓ All UI integration tests passed!")
        print("\nUI Integration Summary:")
        print("• All UI components can be imported successfully")
        print("• Basic functionality works without errors")
        print("• Application structure is correct")
        print("• Ready for full application testing")
    else:
        print("✗ Some tests failed - check the output above")
    
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)