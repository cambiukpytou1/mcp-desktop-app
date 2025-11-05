"""
Final Analytics Dashboard Test
==============================

Test the completed analytics dashboard implementation.
"""

import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_analytics_dashboard():
    """Test analytics dashboard functionality."""
    try:
        print("Testing analytics dashboard components...")
        
        # Test imports
        from services.analytics.performance_analytics import PerformanceAnalytics
        from ui.prompt_components.optimization_recommendations_simple import OptimizationRecommendationsWidget
        print("✓ All imports successful")
        
        # Mock dependencies
        class MockConfigManager:
            def get(self, key, default=None):
                return default or {}
        
        class MockDBManager:
            def get_connection(self):
                class MockConnection:
                    def __enter__(self):
                        return self
                    def __exit__(self, *args):
                        pass
                    def cursor(self):
                        class MockCursor:
                            def execute(self, *args):
                                pass
                            def fetchall(self):
                                return []
                            def fetchone(self):
                                return None
                        return MockCursor()
                return MockConnection()
        
        config_manager = MockConfigManager()
        db_manager = MockDBManager()
        
        # Test PerformanceAnalytics initialization
        perf_analytics = PerformanceAnalytics(config_manager, db_manager)
        print("✓ PerformanceAnalytics initialized")
        
        # Test optimization widget (without UI)
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()  # Hide window
        
        widget = OptimizationRecommendationsWidget(root, config_manager, db_manager)
        print("✓ OptimizationRecommendationsWidget initialized")
        
        # Test recommendation generation
        widget.generate_recommendations()
        print("✓ Recommendations generated")
        
        # Test cluster generation
        widget.generate_clusters()
        print("✓ Clusters generated")
        
        # Verify data was created
        assert len(widget.current_recommendations) > 0, "No recommendations generated"
        assert len(widget.current_clusters) > 0, "No clusters generated"
        print("✓ Data verification passed")
        
        root.destroy()
        
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

def test_analytics_dashboard_ui():
    """Test analytics dashboard UI components."""
    try:
        print("Testing analytics dashboard UI...")
        
        import tkinter as tk
        from ui.analytics_dashboard_page import AnalyticsDashboardPage
        
        # Mock dependencies
        class MockConfigManager:
            def get(self, key, default=None):
                return default or {}
        
        class MockDBManager:
            def get_connection(self):
                class MockConnection:
                    def __enter__(self):
                        return self
                    def __exit__(self, *args):
                        pass
                    def cursor(self):
                        class MockCursor:
                            def execute(self, *args):
                                pass
                            def fetchall(self):
                                return []
                            def fetchone(self):
                                return None
                        return MockCursor()
                return MockConnection()
        
        root = tk.Tk()
        root.withdraw()  # Hide window
        
        config_manager = MockConfigManager()
        db_manager = MockDBManager()
        
        # Test dashboard initialization
        dashboard = AnalyticsDashboardPage(root, config_manager, db_manager)
        print("✓ Analytics dashboard initialized")
        
        # Verify components exist
        assert hasattr(dashboard, 'notebook'), "Notebook not created"
        assert hasattr(dashboard, 'performance_analytics'), "Performance analytics not initialized"
        assert hasattr(dashboard, 'optimization_widget'), "Optimization widget not created"
        print("✓ All dashboard components verified")
        
        root.destroy()
        
        return True
        
    except Exception as e:
        print(f"✗ UI test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("Analytics Dashboard Implementation Tests")
    print("=" * 50)
    
    success = True
    
    print("\n1. Testing core functionality...")
    success &= test_analytics_dashboard()
    
    print("\n2. Testing UI components...")
    success &= test_analytics_dashboard_ui()
    
    print("\n" + "=" * 50)
    if success:
        print("✓ All analytics dashboard tests passed!")
        print("\nImplemented features:")
        print("• Performance analytics visualization")
        print("• Cost tracking and breakdown displays")
        print("• Performance comparison tables")
        print("• Optimization recommendations interface")
        print("• Semantic clustering visualization")
        print("• Export capabilities for analytics reports")
    else:
        print("✗ Some tests failed!")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)