#!/usr/bin/env python3
"""
Basic Templating System Test
============================

Simple test to verify templating system functionality.
"""

import sys
import os
from pathlib import Path

# Add the application directory to Python path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

from services.prompt.templating_engine import (
    AdvancedTemplatingEngine, TemplateVariable
)


def test_basic_templating():
    """Test basic templating functionality."""
    print("Testing Basic Templating...")
    
    engine = AdvancedTemplatingEngine()
    
    # Test simple variable substitution
    template = "Hello {{name}}, welcome to {{platform}}!"
    variables = {"name": "Alice", "platform": "MCP Admin"}
    
    result = engine.render_template(template, variables)
    
    assert result.success == True
    assert result.rendered_content == "Hello Alice, welcome to MCP Admin!"
    assert result.variables_used == variables
    
    print("✓ Basic templating test passed")


def test_variable_validation():
    """Test variable validation."""
    print("Testing Variable Validation...")
    
    engine = AdvancedTemplatingEngine()
    
    # Define variable constraints
    variables_def = [
        TemplateVariable(
            name="username",
            type="string",
            required=True,
            description="Username"
        ),
        TemplateVariable(
            name="age",
            type="number",
            required=True,
            min_value=0,
            max_value=150,
            description="User age"
        )
    ]
    
    template = "User: {{username}}, Age: {{age}}"
    
    # Test valid variables
    variables = {"username": "john_doe", "age": 25}
    result = engine.render_template(template, variables, variables_def)
    
    assert result.success == True
    assert "User: john_doe, Age: 25" in result.rendered_content
    
    # Test invalid age
    variables = {"username": "john_doe", "age": 200}
    result = engine.render_template(template, variables, variables_def)
    
    assert result.success == False
    assert "must be <= 150" in result.error
    
    print("✓ Variable validation test passed")


def run_basic_tests():
    """Run basic templating tests."""
    print("=" * 50)
    print("BASIC TEMPLATING TESTS")
    print("=" * 50)
    
    try:
        test_basic_templating()
        test_variable_validation()
        
        print("\n" + "=" * 50)
        print("✅ ALL BASIC TESTS PASSED!")
        print("=" * 50)
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_basic_tests()
    sys.exit(0 if success else 1)