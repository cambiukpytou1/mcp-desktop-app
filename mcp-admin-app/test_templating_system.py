#!/usr/bin/env python3
"""
Templating System Unit Test Suite
=================================

Comprehensive unit tests for the templating system including:
- Variable substitution and validation
- Dataset integration and bulk processing
- Template validation and analysis
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
from services.prompt.template_validator import TemplateValidator, TemplateAnalysis
from services.prompt.dataset_integration import (
    DatasetIntegration, ParameterSweepConfig, BulkTestResult
)


def test_variable_substitution():
    """Test basic variable substitution functionality."""
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
    template = "Hello {{name|upper}}, your score is {{score|round}}!"
    variables = {"name": "bob", "score": 85.7}
    
    result = engine.render_template(template, variables)
    
    assert result.success == True
    assert "Hello BOB" in result.rendered_content
    assert "score is 86" in result.rendered_content
    
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
    assert "unused_var" in validation.warnings[0]
    
    print("✓ Template validation tests passed")


def test_template_analysis():
    """Test comprehensive template analysis."""
    print("Testing Template Analysis...")
    
    validator = TemplateValidator()
    
    # Test simple template analysis
    template_content = """
Hello {{user_name}}, welcome to {{platform_name}}!

Your account type is {{account_type}} and you have {{credit_balance}} credits remaining.

{% if premium_user %}
As a premium user, you have access to advanced features.
{% endif %}

Thank you for using our service!
"""
    
    analysis = validator.validate_template_comprehensive(
        "test_template_001",
        template_content
    )
    
    assert analysis.template_id == "test_template_001"
    assert analysis.validation_result.is_valid == True
    assert len(analysis.variables) > 0
    assert analysis.complexity_score > 0
    assert analysis.readability_score > 0
    
    # Check that variables were detected
    var_names = [var.name for var in analysis.variables]
    assert "user_name" in var_names
    assert "platform_name" in var_names
    assert "account_type" in var_names
    assert "credit_balance" in var_names
    assert "premium_user" in var_names
    
    # Test template with security issues
    unsafe_template = """
Hello {{name}},
Your file is at {{file.__class__.__bases__[0].__subclasses__()}}
Please run: {{system('rm -rf /')}}
"""
    
    analysis = validator.validate_template_comprehensive(
        "unsafe_template",
        unsafe_template
    )
    
    assert len(analysis.security_issues) > 0
    
    # Test performance warnings
    complex_template = """
{% for item in large_list %}
  {% for subitem in item.subitems %}
    {% if subitem.condition %}
      Processing {{subitem.name|complex_filter|another_filter}}
    {% endif %}
  {% endfor %}
{% endfor %}
"""
    
    analysis = validator.validate_template_comprehensive(
        "complex_template",
        complex_template
    )
    
    assert len(analysis.performance_warnings) > 0
    assert analysis.complexity_score > 10
    
    print("✓ Template analysis tests passed")


def test_dataset_integration():
    """Test dataset integration functionality."""
    print("Testing Dataset Integration...")
    
    dataset_integration = DatasetIntegration()
    
    # Create test CSV data
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        csv_writer = csv.writer(f)
        csv_writer.writerow(['name', 'age', 'city', 'occupation'])
        csv_writer.writerow(['Alice', '25', 'New York', 'Engineer'])
        csv_writer.writerow(['Bob', '30', 'San Francisco', 'Designer'])
        csv_writer.writerow(['Charlie', '35', 'Chicago', 'Manager'])
        csv_writer.writerow(['Diana', '28', 'Boston', 'Analyst'])
        csv_file_path = f.name
    
    try:
        # Test dataset loading and analysis
        dataset_info = dataset_integration.analyze_dataset(csv_file_path)
        
        assert dataset_info.format == 'csv'
        assert dataset_info.row_count == 4
        assert dataset_info.column_count == 4
        assert len(dataset_info.columns) == 4
        
        column_names = [col.name for col in dataset_info.columns]
        assert 'name' in column_names
        assert 'age' in column_names
        assert 'city' in column_names
        assert 'occupation' in column_names
        
        # Test data loading
        data = dataset_integration.load_dataset(csv_file_path)
        assert len(data) == 4
        assert data[0]['name'] == 'Alice'
        assert data[1]['age'] == '30'
        
        print("✓ Dataset integration tests passed")
        
    finally:
        # Clean up temporary file
        os.unlink(csv_file_path)


def test_bulk_processing():
    """Test bulk template processing with datasets."""
    print("Testing Bulk Processing...")
    
    engine = AdvancedTemplatingEngine()
    dataset_integration = DatasetIntegration()
    
    # Create test data
    test_data = [
        {'name': 'Alice', 'product': 'laptop', 'price': '1200'},
        {'name': 'Bob', 'product': 'phone', 'price': '800'},
        {'name': 'Charlie', 'product': 'tablet', 'price': '600'},
        {'name': 'Diana', 'product': 'watch', 'price': '300'}
    ]
    
    # Create temporary CSV file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        csv_writer = csv.DictWriter(f, fieldnames=['name', 'product', 'price'])
        csv_writer.writeheader()
        csv_writer.writerows(test_data)
        csv_file_path = f.name
    
    try:
        # Configure parameter sweep
        config = ParameterSweepConfig(
            template_id="bulk_test_template",
            dataset_path=csv_file_path,
            variable_mappings={
                'customer_name': 'name',
                'item': 'product',
                'cost': 'price'
            },
            batch_size=2,
            max_rows=3
        )
        
        template = "Dear {{customer_name}}, your {{item}} order for ${{cost}} is confirmed."
        
        # Run bulk test
        result = dataset_integration.run_bulk_test(template, config, engine)
        
        assert result.total_rows == 3  # Limited by max_rows
        assert result.successful_renders == 3
        assert result.failed_renders == 0
        assert len(result.results) == 3
        
        # Check first result
        first_result = result.results[0]
        assert 'Dear Alice' in first_result['rendered_content']
        assert 'laptop order' in first_result['rendered_content']
        assert '$1200' in first_result['rendered_content']
        
        # Test with filtering
        config.filter_conditions = {'product': 'phone'}
        result = dataset_integration.run_bulk_test(template, config, engine)
        
        assert result.total_rows == 1
        assert result.successful_renders == 1
        assert 'Bob' in result.results[0]['rendered_content']
        
        print("✓ Bulk processing tests passed")
        
    finally:
        # Clean up temporary file
        os.unlink(csv_file_path)


def test_json_dataset_integration():
    """Test JSON dataset integration."""
    print("Testing JSON Dataset Integration...")
    
    dataset_integration = DatasetIntegration()
    
    # Create test JSON data
    test_data = [
        {
            'user': {'name': 'Alice', 'id': 1},
            'preferences': {'theme': 'dark', 'notifications': True},
            'stats': {'login_count': 45, 'last_active': '2024-01-15'}
        },
        {
            'user': {'name': 'Bob', 'id': 2},
            'preferences': {'theme': 'light', 'notifications': False},
            'stats': {'login_count': 23, 'last_active': '2024-01-10'}
        }
    ]
    
    # Create temporary JSON file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(test_data, f)
        json_file_path = f.name
    
    try:
        # Test dataset analysis
        dataset_info = dataset_integration.analyze_dataset(json_file_path)
        
        assert dataset_info.format == 'json'
        assert dataset_info.row_count == 2
        
        # Test data loading
        data = dataset_integration.load_dataset(json_file_path)
        assert len(data) == 2
        assert data[0]['user']['name'] == 'Alice'
        assert data[1]['preferences']['theme'] == 'light'
        
        # Test flattening for template use
        flattened = dataset_integration.flatten_json_data(data)
        assert len(flattened) == 2
        assert 'user.name' in flattened[0]
        assert 'preferences.theme' in flattened[0]
        assert flattened[0]['user.name'] == 'Alice'
        
        print("✓ JSON dataset integration tests passed")
        
    finally:
        # Clean up temporary file
        os.unlink(json_file_path)


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

Today's date: {{current_date|strftime('%Y-%m-%d')}}
"""
    
    info = engine.get_template_info(complex_template)
    
    assert info['variables_count'] > 3
    assert info['complexity_score'] > 10
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
    large_template = "Hello {{name}}! " * 1000
    variables = {"name": "Test"}
    result = engine.render_template(large_template, variables)
    assert result.success == True
    assert result.rendered_content.count("Hello Test!") == 1000
    
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


def run_all_tests():
    """Run all templating system tests."""
    print("=" * 70)
    print("TEMPLATING SYSTEM UNIT TEST SUITE")
    print("=" * 70)
    
    try:
        test_variable_substitution()
        test_variable_validation()
        test_template_validation()
        test_template_analysis()
        test_dataset_integration()
        test_bulk_processing()
        test_json_dataset_integration()
        test_context_simulation_accuracy()
        test_template_info_and_metrics()
        test_edge_cases()
        
        print("\n" + "=" * 70)
        print("✅ ALL TEMPLATING SYSTEM TESTS PASSED!")
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