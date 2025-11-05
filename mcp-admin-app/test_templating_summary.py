#!/usr/bin/env python3
"""
Templating System Test Summary
==============================

Comprehensive test runner for all templating system functionality.
"""

import sys
import subprocess
from pathlib import Path

def run_test_suite(test_file: str, description: str) -> bool:
    """Run a test suite and return success status."""
    print(f"\n{'='*60}")
    print(f"Running {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run([sys.executable, test_file], 
                              capture_output=False, 
                              cwd=Path(__file__).parent)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running {test_file}: {e}")
        return False

def main():
    """Run all templating system tests."""
    print("TEMPLATING SYSTEM COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    
    test_suites = [
        ("test_templating_basic.py", "Basic Templating Tests"),
        ("test_templating_core.py", "Core Templating System Tests"),
        ("test_context_simulation.py", "Context Simulation Tests"),
        ("test_templating_context_integration.py", "Templating Context Integration Tests")
    ]
    
    results = []
    
    for test_file, description in test_suites:
        success = run_test_suite(test_file, description)
        results.append((description, success))
    
    # Summary
    print(f"\n{'='*80}")
    print("TEST RESULTS SUMMARY")
    print(f"{'='*80}")
    
    all_passed = True
    for description, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{description:<50} {status}")
        if not success:
            all_passed = False
    
    print(f"\n{'='*80}")
    if all_passed:
        print("🎉 ALL TEMPLATING SYSTEM TESTS PASSED!")
        print("\nTest Coverage Summary:")
        print("✓ Variable substitution and validation")
        print("✓ Template validation and analysis")
        print("✓ Context simulation accuracy")
        print("✓ Dataset integration simulation")
        print("✓ Conversation memory management")
        print("✓ Few-shot example handling")
        print("✓ Scenario-based context switching")
        print("✓ Template-context integration")
        print("✓ Edge cases and error handling")
        print("✓ Performance metrics calculation")
    else:
        print("❌ SOME TESTS FAILED - Please check the output above")
    
    print(f"{'='*80}")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)