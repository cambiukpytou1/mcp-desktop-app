#!/usr/bin/env python3
"""
Templating Engine Context Integration Test Suite
===============================================

Unit tests for the integration between the templating engine and context simulation.
"""

import sys
import os
from pathlib import Path

# Add the application directory to Python path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

from services.prompt.templating_engine import AdvancedTemplatingEngine, TemplateVariable


def test_templating_with_context():
    """Test templating engine with context simulation."""
    print("Testing Templating with Context Simulation...")
    
    engine = AdvancedTemplatingEngine()
    
    # Create a context scenario
    scenario_id = engine.create_context_scenario(
        name="Customer Support",
        description="Customer support scenario",
        system_prompt="You are a helpful customer support agent for {{company_name}}.",
        initial_context="The customer is asking about {{product_type}} issues.",
        variables={"company_name": "TechCorp", "product_type": "software"}
    )
    
    assert scenario_id is not None
    
    # Add few-shot examples
    examples = [
        ("My software won't start", "I'm sorry to hear that. Let me help you troubleshoot the startup issue.", "Helpful response to technical issue"),
        ("I want a refund", "I understand your concern. Let me check your account and see what options are available.", "Professional response to refund request")
    ]
    
    success = engine.add_few_shot_examples(scenario_id, examples)
    assert success == True
    
    # Simulate a conversation
    conversation = [
        ("Hello, I need help", "Hi! I'm here to help. What can I assist you with today?"),
        ("My account is locked", "I can help you unlock your account. Let me check your details.")
    ]
    
    success = engine.simulate_conversation(scenario_id, conversation)
    assert success == True
    
    # Test context preview
    template = "Please help the customer with their {{issue_type}} problem."
    preview = engine.get_context_preview(template, scenario_id)
    

    
    assert "You are a helpful customer support agent for" in preview
    assert "Examples:" in preview
    assert "Conversation History:" in preview
    assert "Please help the customer with their {{issue_type}} problem." in preview
    
    # Test rendering with context
    variables = {"issue_type": "billing"}
    result = engine.render_with_context(template, variables, scenario_id)
    
    assert result.success == True
    assert "You are a helpful customer support agent for TechCorp" in result.rendered_content
    assert "billing problem" in result.rendered_content
    assert result.variables_used["issue_type"] == "billing"
    assert result.variables_used["_context_scenario"] == "Customer Support"
    
    print("✓ Templating with context simulation tests passed")


def test_scenario_management():
    """Test scenario management through templating engine."""
    print("Testing Scenario Management...")
    
    engine = AdvancedTemplatingEngine()
    
    # Create multiple scenarios
    scenario1_id = engine.create_context_scenario(
        name="Technical Support",
        description="Technical support scenario"
    )
    
    scenario2_id = engine.create_context_scenario(
        name="Sales Inquiry",
        description="Sales inquiry scenario"
    )
    
    # List scenarios
    scenarios = engine.list_scenarios()
    assert len(scenarios) >= 2
    
    scenario_names = [s["name"] for s in scenarios]
    assert "Technical Support" in scenario_names
    assert "Sales Inquiry" in scenario_names
    
    # Get scenario info
    info = engine.get_scenario_info(scenario1_id)
    assert info is not None
    assert info["name"] == "Technical Support"
    assert info["description"] == "Technical support scenario"
    assert "conversation_messages" in info
    assert "few_shot_examples" in info
    
    # Test export/import
    exported_data = engine.export_scenario(scenario1_id)
    assert exported_data is not None
    assert exported_data["name"] == "Technical Support"
    
    imported_id = engine.import_scenario(exported_data)
    assert imported_id is not None
    assert imported_id != scenario1_id  # Should be a new ID
    
    imported_info = engine.get_scenario_info(imported_id)
    assert imported_info["name"] == "Technical Support"
    
    print("✓ Scenario management tests passed")


def test_context_rendering_options():
    """Test different context rendering options."""
    print("Testing Context Rendering Options...")
    
    engine = AdvancedTemplatingEngine()
    
    # Create scenario with both conversation and few-shot examples
    scenario_id = engine.create_context_scenario(
        name="Test Scenario",
        system_prompt="You are a test assistant.",
        initial_context="This is test context."
    )
    
    # Add examples and conversation
    engine.add_few_shot_examples(scenario_id, [
        ("Test input", "Test output", "Test explanation")
    ])
    
    engine.simulate_conversation(scenario_id, [
        ("Hello", "Hi there!")
    ])
    
    template = "Process this: {{input}}"
    variables = {"input": "test data"}
    
    # Test with both context types
    result_both = engine.render_with_context(
        template, variables, scenario_id,
        include_few_shot=True, include_conversation=True
    )
    
    assert "Examples:" in result_both.rendered_content
    assert "Conversation History:" in result_both.rendered_content
    
    # Test with only few-shot examples
    result_few_shot = engine.render_with_context(
        template, variables, scenario_id,
        include_few_shot=True, include_conversation=False
    )
    
    assert "Examples:" in result_few_shot.rendered_content
    assert "Conversation History:" not in result_few_shot.rendered_content
    
    # Test with only conversation
    result_conversation = engine.render_with_context(
        template, variables, scenario_id,
        include_few_shot=False, include_conversation=True
    )
    
    assert "Examples:" not in result_conversation.rendered_content
    assert "Conversation History:" in result_conversation.rendered_content
    
    # Test with no context
    result_no_context = engine.render_with_context(
        template, variables, scenario_id,
        include_few_shot=False, include_conversation=False
    )
    
    assert "Examples:" not in result_no_context.rendered_content
    assert "Conversation History:" not in result_no_context.rendered_content
    assert "You are a test assistant." in result_no_context.rendered_content  # System prompt should still be there
    
    print("✓ Context rendering options tests passed")


def test_variable_validation_with_context():
    """Test variable validation with context simulation."""
    print("Testing Variable Validation with Context...")
    
    engine = AdvancedTemplatingEngine()
    
    # Create scenario with variables
    scenario_id = engine.create_context_scenario(
        name="Validation Test",
        variables={"default_value": "test"}
    )
    
    # Define template variables
    variables_def = [
        TemplateVariable(
            name="required_field",
            type="string",
            required=True,
            description="A required field"
        ),
        TemplateVariable(
            name="optional_field",
            type="string",
            required=False,
            default="default_value",
            description="An optional field"
        )
    ]
    
    template = "Required: {{required_field}}, Optional: {{optional_field}}"
    
    # Test with valid variables
    variables = {"required_field": "test_value"}
    result = engine.render_with_context(
        template, variables, scenario_id,
        variable_definitions=variables_def
    )
    
    assert result.success == True
    assert "Required: test_value" in result.rendered_content
    assert "Optional: default_value" in result.rendered_content
    
    # Test with missing required variable
    variables = {"optional_field": "custom_value"}
    result = engine.render_with_context(
        template, variables, scenario_id,
        variable_definitions=variables_def
    )
    
    assert result.success == False
    assert "Required variable 'required_field' is missing" in result.error
    
    print("✓ Variable validation with context tests passed")


def test_complex_context_scenario():
    """Test a complex context scenario with multiple features."""
    print("Testing Complex Context Scenario...")
    
    engine = AdvancedTemplatingEngine()
    
    # Create a complex scenario
    scenario_id = engine.create_context_scenario(
        name="AI Assistant Training",
        description="Training scenario for AI assistant",
        system_prompt="You are an AI assistant being trained on {{task_type}} tasks.",
        initial_context="Training session for {{difficulty_level}} level tasks.",
        variables={
            "task_type": "classification",
            "difficulty_level": "intermediate",
            "model_name": "GPT-4"
        }
    )
    
    # Add multiple few-shot examples
    examples = [
        ("Classify: 'This movie is great!'", "Positive sentiment", "Clear positive language"),
        ("Classify: 'This movie is terrible.'", "Negative sentiment", "Clear negative language"),
        ("Classify: 'The movie was okay.'", "Neutral sentiment", "Neutral language"),
        ("Classify: 'I love this film!'", "Positive sentiment", "Strong positive emotion")
    ]
    
    engine.add_few_shot_examples(scenario_id, examples)
    
    # Simulate training conversation
    training_conversation = [
        ("Let's start training", "I'm ready to learn classification tasks."),
        ("Here's your first example", "I'll analyze it carefully."),
        ("Good job on that classification", "Thank you! I'm learning the patterns.")
    ]
    
    engine.simulate_conversation(scenario_id, training_conversation)
    
    # Create a complex template
    template = """
Training Task: {{task_type}} using {{model_name}}
Difficulty: {{difficulty_level}}
Current Task: Classify the sentiment of "{{input_text}}"
Expected Format: [Positive/Negative/Neutral] - [Confidence: 0-1]
"""
    
    variables = {
        "input_text": "I absolutely love this new product!"
    }
    
    # Render with full context
    result = engine.render_with_context(template, variables, scenario_id)
    
    assert result.success == True
    
    # Verify all context elements are present
    content = result.rendered_content
    assert "You are an AI assistant being trained on classification tasks" in content
    assert "Training session for intermediate level tasks" in content
    assert "Examples:" in content
    assert "Classify: 'This movie is great!'" in content
    assert "Conversation History:" in content
    assert "Let's start training" in content
    assert "Training Task: classification using GPT-4" in content
    assert "I absolutely love this new product!" in content
    
    # Verify variables were applied correctly
    assert result.variables_used["task_type"] == "classification"
    assert result.variables_used["model_name"] == "GPT-4"
    assert result.variables_used["input_text"] == "I absolutely love this new product!"
    
    print("✓ Complex context scenario tests passed")


def run_all_tests():
    """Run all templating context integration tests."""
    print("=" * 70)
    print("TEMPLATING ENGINE CONTEXT INTEGRATION TEST SUITE")
    print("=" * 70)
    
    try:
        test_templating_with_context()
        test_scenario_management()
        test_context_rendering_options()
        test_variable_validation_with_context()
        test_complex_context_scenario()
        
        print("\n" + "=" * 70)
        print("✅ ALL TEMPLATING CONTEXT INTEGRATION TESTS PASSED!")
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