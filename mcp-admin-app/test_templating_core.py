#!/usr/bin/env python3
"""
Core Templating System Unit Tests
=================================

Unit tests for the core templating system functionality including:
- Variable substitution and validation
- Context simulation accuracy
- Template validation
"""

import sys
import os
import json
import tempfile
import csv
from pathlib import Path
from datetime import datetime

# Add the application directory to Python path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

from services.prompt.templating_engine import (
    AdvancedTemplatingEngine, TemplateVariable, TemplateValidationResult, 
    TemplateRenderResult
)


def test_variable_substitution():
    """Test variable substitution functionality."""
    print("Testing Variable Substitution...")
    
    engine = AdvancedTemplatingEngine()
    
    # Test simple variable substitution
    template = "Hello {{name}}, welcome to {{platform}}!"
    variables = {"name": "Alice", "platform": "MCP Admin"}
    
    result = engine.render_template(template, variables)
    
    assert result.success == True
    assert result.rendered_content == "Hello Alice, welcome to MCP Admin!"
    assert result.variables_used == variables
    assert result.render_time > 0
    
    # Test with filters
    template = "Hello {{name|upper}}, your score is {{score}}!"
    variables = {"name": "bob", "score": 85}
    
    result = engine.render_template(template, variables)
    
    assert result.success == True
    assert "Hello BOB" in result.rendered_content
    assert "score is 85" in result.rendered_content
    
    # Test with missing variables
    template = "Hello {{name}}, your {{missing_var}} is ready!"
    variables = {"name": "Charlie"}
    
    result = engine.render_template(template, variables)
    
    assert result.success == False
    assert "Undefined variable" in result.error
    
    print("✓ Variable substitution tests passed")


def test_variable_validation():
    """Test variable validation functionality."""
    print("Testing Variable Validation...")
    
    engine = AdvancedTemplatingEngine()
    
    # Define variable constraints
    variables_def = [
        TemplateVariable(
            name="username",
            type="string",
            required=True,
            validation_pattern=r"^[a-zA-Z0-9_]+$",
            description="Username with alphanumeric characters only"
        ),
        TemplateVariable(
            name="age",
            type="number",
            required=True,
            min_value=0,
            max_value=150,
            description="User age"
        ),
        TemplateVariable(
            name="role",
            type="string",
            required=False,
            allowed_values=["admin", "user", "guest"],
            default="user",
            description="User role"
        ),
        TemplateVariable(
            name="active",
            type="boolean",
            required=False,
            default=True,
            description="Account active status"
        )
    ]
    
    template = "User: {{username}}, Age: {{age}}, Role: {{role}}, Active: {{active}}"
    
    # Test valid variables
    variables = {
        "username": "john_doe",
        "age": 25,
        "role": "admin",
        "active": True
    }
    
    result = engine.render_template(template, variables, variables_def)
    
    assert result.success == True
    assert "User: john_doe" in result.rendered_content
    assert "Age: 25" in result.rendered_content
    assert "Role: admin" in result.rendered_content
    assert "Active: True" in result.rendered_content
    
    # Test with defaults
    variables = {"username": "jane_doe", "age": 30}
    
    result = engine.render_template(template, variables, variables_def)
    
    assert result.success == True
    assert "Role: user" in result.rendered_content  # Default value
    assert "Active: True" in result.rendered_content  # Default value
    
    # Test validation failures
    test_cases = [
        # Invalid username pattern
        ({"username": "john-doe!", "age": 25}, "does not match required pattern"),
        # Age out of range
        ({"username": "john_doe", "age": 200}, "must be <= 150"),
        # Invalid role
        ({"username": "john_doe", "age": 25, "role": "superuser"}, "must be one of"),
        # Wrong type
        ({"username": "john_doe", "age": "twenty-five"}, "must be a number"),
        # Missing required field
        ({"age": 25}, "Required variable 'username' is missing")
    ]
    
    for invalid_vars, expected_error in test_cases:
        result = engine.render_template(template, invalid_vars, variables_def)
        assert result.success == False
        assert expected_error in result.error
    
    print("✓ Variable validation tests passed")


def test_template_validation():
    """Test template validation functionality."""
    print("Testing Template Validation...")
    
    engine = AdvancedTemplatingEngine()
    
    # Test valid template
    template = "Hello {{name}}, your order {{order_id}} is {{status}}."
    validation = engine.validate_template(template)
    
    assert validation.is_valid == True
    assert len(validation.errors) == 0
    assert "name" in validation.variables_found
    assert "order_id" in validation.variables_found
    assert "status" in validation.variables_found
    
    # Test template with syntax error
    invalid_template = "Hello {{name}, your order {{order_id} is ready."
    validation = engine.validate_template(invalid_template)
    
    assert validation.is_valid == False
    assert len(validation.errors) > 0
    assert "syntax error" in validation.errors[0].lower()
    
    # Test template with variable definitions
    variables_def = [
        TemplateVariable(name="name", type="string"),
        TemplateVariable(name="order_id", type="string"),
        TemplateVariable(name="unused_var", type="string")
    ]
    
    validation = engine.validate_template(template, variables_def)
    
    assert validation.is_valid == True
    assert len(validation.warnings) > 0
    # Check that unused_var appears in one of the warnings
    warning_text = " ".join(validation.warnings)
    assert "unused_var" in warning_text
    
    print("✓ Template validation tests passed")


def test_context_simulation_accuracy():
    """Test context simulation accuracy and consistency."""
    print("Testing Context Simulation Accuracy...")
    
    engine = AdvancedTemplatingEngine()
    
    # Create a scenario with specific context
    scenario_id = engine.create_context_scenario(
        name="Technical Support",
        description="Technical support conversation",
        system_prompt="You are a technical support specialist for {{company}}.",
        initial_context="Customer is experiencing {{issue_type}} with {{product}}.",
        variables={
            "company": "TechCorp",
            "issue_type": "connectivity",
            "product": "WiFi Router"
        }
    )
    
    # Add few-shot examples
    examples = [
        (
            "My internet is not working",
            "I understand you're having connectivity issues. Let me help you troubleshoot your WiFi router.",
            "Standard connectivity troubleshooting response"
        ),
        (
            "The lights on my router are blinking red",
            "Red blinking lights typically indicate a connection problem. Let's check your cable connections first.",
            "Hardware diagnostic response"
        )
    ]
    
    engine.add_few_shot_examples(scenario_id, examples)
    
    # Simulate conversation history
    conversation = [
        ("Hello, I need help with my router", "Hi! I'm here to help with your router issue."),
        ("It's not connecting to the internet", "Let me guide you through some troubleshooting steps.")
    ]
    
    engine.simulate_conversation(scenario_id, conversation)
    
    # Test context consistency across multiple renders
    template = "Current issue: {{current_problem}}. Please provide step-by-step guidance."
    variables = {"current_problem": "intermittent disconnections"}
    
    # Render multiple times and check consistency
    results = []
    for i in range(3):
        result = engine.render_with_context(template, variables, scenario_id)
        assert result.success == True
        results.append(result.rendered_content)
    
    # All results should contain the same context elements
    for result_content in results:
        assert "You are a technical support specialist for TechCorp" in result_content
        assert "Customer is experiencing connectivity with WiFi Router" in result_content
        assert "Examples:" in result_content
        assert "My internet is not working" in result_content
        assert "Conversation History:" in result_content
        assert "Hello, I need help with my router" in result_content
        assert "intermittent disconnections" in result_content
    
    # Test context variable application accuracy
    scenario = engine.context_service.get_scenario(scenario_id)
    test_template = "Support for {{company}} {{product}} {{issue_type}} issues"
    processed = scenario.apply_variables(test_template)
    
    assert processed == "Support for TechCorp WiFi Router connectivity issues"
    
    # Test context switching accuracy
    scenario2_id = engine.create_context_scenario(
        name="Sales Support",
        system_prompt="You are a sales representative for {{company}}.",
        variables={"company": "SalesCorp"}
    )
    
    # Render same template with different scenario
    result2 = engine.render_with_context(template, variables, scenario2_id)
    
    assert result2.success == True
    assert "sales representative for SalesCorp" in result2.rendered_content
    assert "technical support specialist" not in result2.rendered_content
    
    print("✓ Context simulation accuracy tests passed")


def test_template_info_and_metrics():
    """Test template information and metrics calculation."""
    print("Testing Template Info and Metrics...")
    
    engine = AdvancedTemplatingEngine()
    
    # Test simple template
    simple_template = "Hello {{name}}, welcome!"
    info = engine.get_template_info(simple_template)
    
    assert info['variables_count'] == 1
    assert 'name' in info['variables']
    assert info['is_valid'] == True
    assert info['complexity_score'] >= 1
    assert info['estimated_render_time'] > 0
    
    # Test complex template
    complex_template = """
{% if user.premium %}
Hello {{user.name|title}}, welcome to our premium service!

Your benefits include:
{% for benefit in premium_benefits %}
- {{benefit.name}}: {{benefit.description}}
{% endfor %}

{% if user.credits > 100 %}
You have {{user.credits}} credits remaining.
{% endif %}

{% else %}
Hello {{user.name}}, welcome to our standard service!
{% endif %}

Today's date: {{current_date}}
"""
    
    info = engine.get_template_info(complex_template)
    
    assert info['variables_count'] > 3
    assert info['complexity_score'] > 5
    assert len(info['errors']) == 0  # Should be valid
    
    # Test template with errors
    error_template = "Hello {{name}, missing closing brace"
    info = engine.get_template_info(error_template)
    
    assert info['is_valid'] == False
    assert len(info['errors']) > 0
    
    print("✓ Template info and metrics tests passed")


def test_edge_cases():
    """Test edge cases and error handling."""
    print("Testing Edge Cases...")
    
    engine = AdvancedTemplatingEngine()
    
    # Test empty template
    result = engine.render_template("", {})
    assert result.success == True
    assert result.rendered_content == ""
    
    # Test template with only whitespace
    result = engine.render_template("   \n\t  ", {})
    assert result.success == True
    
    # Test very large template
    large_template = "Hello {{name}}! " * 100
    variables = {"name": "Test"}
    result = engine.render_template(large_template, variables)
    assert result.success == True
    assert result.rendered_content.count("Hello Test!") == 100
    
    # Test template with special characters
    special_template = "Héllo {{nämé}}, wëlcömé tö {{plätförm}}! 🎉"
    variables = {"nämé": "Tëst", "plätförm": "MCP"}
    result = engine.render_template(special_template, variables)
    assert result.success == True
    assert "Héllo Tëst" in result.rendered_content
    assert "🎉" in result.rendered_content
    
    # Test with None values
    template = "Value: {{value}}"
    variables = {"value": None}
    result = engine.render_template(template, variables)
    assert result.success == True
    assert "Value: None" in result.rendered_content
    
    # Test with nested dictionaries
    template = "User: {{user.profile.name}}, Age: {{user.profile.age}}"
    variables = {
        "user": {
            "profile": {
                "name": "Alice",
                "age": 30
            }
        }
    }
    result = engine.render_template(template, variables)
    assert result.success == True
    assert "User: Alice, Age: 30" in result.rendered_content
    
    print("✓ Edge cases tests passed")


def test_bulk_processing_simulation():
    """Test bulk processing simulation without external dependencies."""
    print("Testing Bulk Processing Simulation...")
    
    engine = AdvancedTemplatingEngine()
    
    # Simulate dataset processing
    template = "Dear {{customer_name}}, your {{item}} order for ${{cost}} is confirmed."
    
    # Simulate dataset rows
    test_data = [
        {'customer_name': 'Alice', 'item': 'laptop', 'cost': '1200'},
        {'customer_name': 'Bob', 'item': 'phone', 'cost': '800'},
        {'customer_name': 'Charlie', 'item': 'tablet', 'cost': '600'},
        {'customer_name': 'Diana', 'item': 'watch', 'cost': '300'}
    ]
    
    # Process each row
    results = []
    for i, row_data in enumerate(test_data):
        result = engine.render_template(template, row_data)
        
        test_result = {
            'row_index': i,
            'template_variables': row_data,
            'success': result.success,
            'rendered_content': result.rendered_content if result.success else '',
            'error': result.error if not result.success else None,
            'render_time': result.render_time
        }
        
        results.append(test_result)
    
    # Verify results
    assert len(results) == 4
    assert all(r['success'] for r in results)
    
    # Check first result
    first_result = results[0]
    assert 'Dear Alice' in first_result['rendered_content']
    assert 'laptop order' in first_result['rendered_content']
    assert '$1200' in first_result['rendered_content']
    
    # Check that all customers were processed
    customer_names = [r['template_variables']['customer_name'] for r in results]
    assert 'Alice' in customer_names
    assert 'Bob' in customer_names
    assert 'Charlie' in customer_names
    assert 'Diana' in customer_names
    
    print("✓ Bulk processing simulation tests passed")


def run_all_tests():
    """Run all core templating system tests."""
    print("=" * 70)
    print("CORE TEMPLATING SYSTEM UNIT TEST SUITE")
    print("=" * 70)
    
    try:
        test_variable_substitution()
        test_variable_validation()
        test_template_validation()
        test_context_simulation_accuracy()
        test_template_info_and_metrics()
        test_edge_cases()
        test_bulk_processing_simulation()
        
        print("\n" + "=" * 70)
        print("✅ ALL CORE TEMPLATING SYSTEM TESTS PASSED!")
        print("=" * 70)
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)