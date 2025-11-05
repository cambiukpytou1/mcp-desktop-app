"""
Simple Analytics Dashboard Test
===============================

Basic test to verify analytics dashboard components work.
"""

import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all required modules can be imported."""
    try:
        from services.analytics.performance_analytics import PerformanceAnalytics
        print("✓ PerformanceAnalytics imported successfully")
        
        from services.analytics.semantic_clustering import SemanticClustering
        print("✓ SemanticClustering imported successfully")
        
        from ui.prompt_components.optimization_recommendations import OptimizationRecommendationsWidget
        print("✓ OptimizationRecommendationsWidget imported successfully")
        
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

def test_basic_functionality():
    """Test basic functionality without UI."""
    try:
        # Mock config and db managers
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
        
        # Test PerformanceAnalytics
        perf_analytics = PerformanceAnalytics(config_manager, db_manager)
        print("✓ PerformanceAnalytics initialized successfully")
        
        # Test SemanticClustering
        semantic_clustering = SemanticClustering(config_manager, db_manager, None)
        print("✓ SemanticClustering initialized successfully")
        
        return True
    except Exception as e:
        print(f"✗ Basic functionality test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("Analytics Dashboard Component Tests")
    print("=" * 40)
    
    success = True
    
    print("\n1. Testing imports...")
    success &= test_imports()
    
    print("\n2. Testing basic functionality...")
    success &= test_basic_functionality()
    
    print("\n" + "=" * 40)
    if success:
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed!")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)