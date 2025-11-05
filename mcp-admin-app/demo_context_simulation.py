#!/usr/bin/env python3
"""
Context Simulation Demonstration
===============================

Demonstrates the context simulation capabilities including conversation memory,
few-shot examples, and scenario-based context switching.
"""

import sys
from pathlib import Path

# Add the application directory to Python path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

from services.prompt.templating_engine import AdvancedTemplatingEngine


def demo_customer_support_scenario():
    """Demonstrate a customer support context scenario."""
    print("=" * 60)
    print("CUSTOMER SUPPORT SCENARIO DEMO")
    print("=" * 60)
    
    engine = AdvancedTemplatingEngine()
    
    # Create customer support scenario
    scenario_id = engine.create_context_scenario(
        name="Customer Support Agent",
        description="AI assistant trained for customer support interactions",
        system_prompt="You are a helpful customer support agent for {{company_name}}. "
                     "You should be professional, empathetic, and solution-focused.",
        initial_context="The customer is contacting support about {{issue_category}} issues. "
                       "They are a {{customer_tier}} customer.",
        variables={
            "company_name": "TechCorp Solutions",
            "issue_category": "billing",
            "customer_tier": "premium"
        }
    )
    
    # Add few-shot examples for customer support
    examples = [
        (
            "My bill seems too high this month",
            "I understand your concern about your billing. Let me review your account details "
            "and help you understand the charges. Can you provide your account number?",
            "Professional response acknowledging concern and requesting information"
        ),
        (
            "I can't log into my account",
            "I'm sorry you're having trouble accessing your account. Let me help you resolve "
            "this login issue. Have you tried resetting your password recently?",
            "Helpful response offering immediate assistance"
        ),
        (
            "I want to cancel my subscription",
            "I understand you're considering canceling your subscription. Before we proceed, "
            "I'd like to understand if there's anything we can do to address your concerns.",
            "Retention-focused response while respecting customer choice"
        )
    ]
    
    engine.add_few_shot_examples(scenario_id, examples)
    
    # Simulate a conversation history
    conversation = [
        ("Hello, I need help with my account", "Hi! I'm here to help you with your account. What specific issue are you experiencing?"),
        ("I'm having trouble with my recent bill", "I can definitely help you with billing questions. Let me pull up your account information."),
        ("The charges seem higher than usual", "I see your concern. Let me review your recent usage and explain any changes in your billing.")
    ]
    
    engine.simulate_conversation(scenario_id, conversation)
    
    # Create a prompt template
    template = """
Current Issue: {{customer_issue}}
Priority Level: {{priority}}
Resolution Goal: {{resolution_goal}}

Please provide a professional response that addresses the customer's concern.
"""
    
    # Variables for this specific interaction
    variables = {
        "customer_issue": "Unexpected charges on monthly bill",
        "priority": "high",
        "resolution_goal": "Explain charges and provide resolution options"
    }
    
    # Render with full context
    result = engine.render_with_context(template, variables, scenario_id)
    
    print("RENDERED PROMPT WITH CONTEXT:")
    print("-" * 40)
    print(result.rendered_content)
    print("-" * 40)
    print(f"Success: {result.success}")
    print(f"Render Time: {result.render_time:.4f} seconds")
    print(f"Variables Used: {len(result.variables_used)}")
    
    return scenario_id


def demo_code_review_scenario():
    """Demonstrate a code review context scenario."""
    print("\n" + "=" * 60)
    print("CODE REVIEW SCENARIO DEMO")
    print("=" * 60)
    
    engine = AdvancedTemplatingEngine()
    
    # Create code review scenario
    scenario_id = engine.create_context_scenario(
        name="Code Review Assistant",
        description="AI assistant for code review and feedback",
        system_prompt="You are an experienced software engineer providing code reviews. "
                     "Focus on {{review_focus}} and maintain a {{review_tone}} tone.",
        initial_context="This is a {{review_type}} review for a {{language}} project. "
                       "The code follows {{coding_standard}} standards.",
        variables={
            "review_focus": "security and performance",
            "review_tone": "constructive and educational",
            "review_type": "pull request",
            "language": "Python",
            "coding_standard": "PEP 8"
        }
    )
    
    # Add few-shot examples for code review
    examples = [
        (
            "def process_data(data):\n    return [x*2 for x in data]",
            "Good use of list comprehension! Consider adding type hints and docstring:\n"
            "def process_data(data: List[int]) -> List[int]:\n"
            "    \"\"\"Double each value in the input data.\"\"\"\n"
            "    return [x * 2 for x in data]",
            "Positive feedback with improvement suggestions"
        ),
        (
            "password = request.form['password']\nuser = authenticate(password)",
            "Security concern: This code is vulnerable to timing attacks. Consider using "
            "secure comparison methods and implement rate limiting for authentication attempts.",
            "Security-focused feedback with specific recommendations"
        )
    ]
    
    engine.add_few_shot_examples(scenario_id, examples)
    
    # Simulate code review conversation
    conversation = [
        ("Starting code review for user authentication module", "I'll review this module focusing on security best practices and code quality."),
        ("Found several areas for improvement", "Let me provide detailed feedback on each issue I've identified."),
        ("The authentication logic needs attention", "I'll focus on the security aspects and suggest improvements.")
    ]
    
    engine.simulate_conversation(scenario_id, conversation)
    
    # Create code review template
    template = """
Code Review for: {{file_name}}
Author: {{author}}
Review Type: {{review_type}}

Code to Review:
```{{language}}
{{code_snippet}}
```

Areas of Focus:
- {{focus_area_1}}
- {{focus_area_2}}
- {{focus_area_3}}

Please provide a comprehensive code review.
"""
    
    # Variables for this code review
    variables = {
        "file_name": "auth_handler.py",
        "author": "junior_dev",
        "code_snippet": """
def login(username, password):
    user = User.query.filter_by(username=username).first()
    if user and user.password == password:
        session['user_id'] = user.id
        return True
    return False
""",
        "focus_area_1": "Security vulnerabilities",
        "focus_area_2": "Error handling",
        "focus_area_3": "Code structure and readability"
    }
    
    # Render with context
    result = engine.render_with_context(template, variables, scenario_id)
    
    print("RENDERED CODE REVIEW PROMPT:")
    print("-" * 40)
    print(result.rendered_content)
    print("-" * 40)
    print(f"Success: {result.success}")
    print(f"Context Type: {result.variables_used.get('_context_type', 'N/A')}")
    
    return scenario_id


def demo_scenario_management():
    """Demonstrate scenario management features."""
    print("\n" + "=" * 60)
    print("SCENARIO MANAGEMENT DEMO")
    print("=" * 60)
    
    engine = AdvancedTemplatingEngine()
    
    # List all scenarios
    scenarios = engine.list_scenarios()
    print(f"Total scenarios available: {len(scenarios)}")
    
    for scenario in scenarios:
        print(f"- {scenario['name']}: {scenario['description']}")
        
        # Get detailed info
        info = engine.get_scenario_info(scenario['id'])
        if info:
            print(f"  * Messages: {info['conversation_messages']}")
            print(f"  * Examples: {info['few_shot_examples']}")
            print(f"  * Variables: {len(info['variables'])}")
    
    if scenarios:
        # Export and import demo
        first_scenario = scenarios[0]
        print(f"\nExporting scenario: {first_scenario['name']}")
        
        exported_data = engine.export_scenario(first_scenario['id'])
        if exported_data:
            print("✓ Export successful")
            
            # Import as new scenario
            imported_id = engine.import_scenario(exported_data)
            print(f"✓ Imported as new scenario with ID: {imported_id[:8]}...")


def main():
    """Run all context simulation demonstrations."""
    print("CONTEXT SIMULATION DEMONSTRATION")
    print("This demo shows the advanced context simulation capabilities")
    print("including conversation memory, few-shot examples, and scenarios.")
    
    try:
        # Run demonstrations
        support_scenario = demo_customer_support_scenario()
        review_scenario = demo_code_review_scenario()
        demo_scenario_management()
        
        print("\n" + "=" * 60)
        print("✅ CONTEXT SIMULATION DEMO COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("\nKey Features Demonstrated:")
        print("• Conversation memory with configurable retention")
        print("• Few-shot example management with selection strategies")
        print("• Scenario-based context switching")
        print("• Variable substitution in context elements")
        print("• Integration with templating engine")
        print("• Scenario export/import capabilities")
        
    except Exception as e:
        print(f"\n❌ DEMO FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()