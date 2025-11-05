#!/usr/bin/env python3
"""
Context Simulation Test Suite
=============================

Unit tests for context simulation functionality including conversation memory,
few-shot example management, and scenario-based context switching.
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime

# Add the application directory to Python path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

from services.prompt.context_simulation import (
    ContextSimulationService, ConversationMemory, FewShotExampleSet,
    ContextScenario, ConversationMessage, FewShotExample,
    MessageRole, ContextType
)


def test_conversation_memory():
    """Test conversation memory functionality."""
    print("Testing Conversation Memory...")
    
    # Create conversation memory
    memory = ConversationMemory(max_messages=5, retention_strategy="sliding_window")
    
    # Add messages
    memory.add_message(MessageRole.SYSTEM, "You are a helpful assistant.")
    memory.add_message(MessageRole.USER, "Hello!")
    memory.add_message(MessageRole.ASSISTANT, "Hi there! How can I help you?")
    memory.add_message(MessageRole.USER, "What's the weather like?")
    memory.add_message(MessageRole.ASSISTANT, "I don't have access to current weather data.")
    
    assert len(memory.messages) == 5
    
    # Test context string generation
    context = memory.get_context_string()
    assert "System: You are a helpful assistant." in context
    assert "User: Hello!" in context
    assert "Assistant: Hi there!" in context
    
    # Test API format
    api_messages = memory.get_messages_for_api()
    assert len(api_messages) == 5
    assert api_messages[0]["role"] == "system"
    assert api_messages[1]["role"] == "user"
    
    # Test retention policy
    memory.add_message(MessageRole.USER, "Another question")
    memory.add_message(MessageRole.ASSISTANT, "Another answer")
    
    # Should still have system message plus recent messages
    assert len(memory.messages) <= 6  # System + 5 recent
    system_messages = [msg for msg in memory.messages if msg.role == MessageRole.SYSTEM]
    assert len(system_messages) == 1
    
    print("✓ Conversation memory tests passed")


def test_few_shot_examples():
    """Test few-shot example management."""
    print("Testing Few-Shot Examples...")
    
    # Create example set
    example_set = FewShotExampleSet(
        name="Classification Examples",
        description="Examples for text classification",
        selection_strategy="best",
        max_examples=3
    )
    
    # Add examples
    id1 = example_set.add_example(
        "This movie is amazing!",
        "positive",
        "Clear positive sentiment",
        "sentiment",
        0.9
    )
    
    id2 = example_set.add_example(
        "This movie is terrible.",
        "negative", 
        "Clear negative sentiment",
        "sentiment",
        0.8
    )
    
    id3 = example_set.add_example(
        "The movie was okay.",
        "neutral",
        "Neutral sentiment",
        "sentiment",
        0.7
    )
    
    id4 = example_set.add_example(
        "I love this film!",
        "positive",
        "Another positive example",
        "sentiment",
        0.95
    )
    
    assert len(example_set.examples) == 4
    
    # Test selection strategies
    selected = example_set.get_selected_examples()
    assert len(selected) == 3  # max_examples limit
    
    # Test "best" strategy - should select highest quality scores
    example_set.selection_strategy = "best"
    best_examples = example_set.get_selected_examples()
    assert best_examples[0].quality_score == 0.95  # Highest score first
    
    # Test formatting
    formatted = example_set.format_examples("Input: {input}\nOutput: {output}")
    assert "Input: I love this film!" in formatted
    assert "Output: positive" in formatted
    
    # Test removal
    assert example_set.remove_example(id1) == True
    assert len(example_set.examples) == 3
    assert example_set.remove_example("nonexistent") == False
    
    print("✓ Few-shot example tests passed")


def test_context_scenarios():
    """Test context scenario functionality."""
    print("Testing Context Scenarios...")
    
    # Create scenario
    scenario = ContextScenario(
        name="Customer Support",
        description="Customer support conversation scenario",
        context_type=ContextType.CONVERSATION,
        system_prompt="You are a helpful customer support agent.",
        initial_context="The customer has a billing question.",
        variables={"company_name": "TechCorp", "customer_tier": "premium"}
    )
    
    # Add conversation memory
    scenario.conversation_memory.add_message(
        MessageRole.SYSTEM, 
        "You are a helpful customer support agent."
    )
    scenario.conversation_memory.add_message(
        MessageRole.USER,
        "I have a question about my bill."
    )
    
    # Add few-shot examples
    scenario.few_shot_examples.add_example(
        "My bill seems too high this month.",
        "I'd be happy to help you review your bill. Let me look at your account details.",
        "Polite response to billing concern"
    )
    
    # Test full context generation
    full_context = scenario.get_full_context()
    assert "You are a helpful customer support agent." in full_context
    assert "The customer has a billing question." in full_context
    assert "Examples:" in full_context
    assert "Conversation History:" in full_context
    
    # Test variable application
    template = "Welcome to {{company_name}}! As a {{customer_tier}} customer..."
    processed = scenario.apply_variables(template)
    assert "Welcome to TechCorp!" in processed
    assert "premium customer" in processed
    
    # Test serialization
    scenario_dict = scenario.to_dict()
    assert scenario_dict["name"] == "Customer Support"
    assert scenario_dict["variables"]["company_name"] == "TechCorp"
    
    # Test deserialization
    restored_scenario = ContextScenario.from_dict(scenario_dict)
    assert restored_scenario.name == scenario.name
    assert restored_scenario.variables == scenario.variables
    
    print("✓ Context scenario tests passed")


def test_context_simulation_service():
    """Test the main context simulation service."""
    print("Testing Context Simulation Service...")
    
    service = ContextSimulationService()
    
    # Test scenario creation
    scenario_id = service.create_scenario(
        name="Test Scenario",
        description="A test scenario",
        system_prompt="You are a test assistant.",
        initial_context="This is a test context."
    )
    
    assert scenario_id is not None
    assert len(service.scenarios) == 1
    
    # Test scenario retrieval
    scenario = service.get_scenario(scenario_id)
    assert scenario is not None
    assert scenario.name == "Test Scenario"
    
    # Test scenario update
    success = service.update_scenario(scenario_id, description="Updated description")
    assert success == True
    
    updated_scenario = service.get_scenario(scenario_id)
    assert updated_scenario.description == "Updated description"
    
    # Test active scenario management
    assert service.set_active_scenario(scenario_id) == True
    assert service.get_active_scenario().id == scenario_id
    
    # Test conversation memory creation
    memory = service.create_conversation_memory(max_messages=10)
    assert memory.max_messages == 10
    
    service.add_conversation_message(memory, "user", "Hello!")
    service.add_conversation_message(memory, "assistant", "Hi there!")
    
    assert len(memory.messages) == 2
    
    # Test conversation turn simulation
    service.simulate_conversation_turn(memory, "How are you?", "I'm doing well!")
    assert len(memory.messages) == 4
    
    # Test few-shot set creation
    few_shot_set = service.create_few_shot_set("Test Examples", max_examples=2)
    example_id = service.add_few_shot_example(
        few_shot_set, 
        "Test input", 
        "Test output",
        "Test explanation"
    )
    
    assert len(few_shot_set.examples) == 1
    assert few_shot_set.examples[0].id == example_id
    
    # Test context generation
    prompt = "Please help me with {{task}}."
    scenario.variables = {"task": "writing"}
    
    context = service.generate_context_for_prompt(prompt, scenario_id)
    assert "You are a test assistant." in context
    assert "Please help me with writing." in context
    
    # Test multi-turn conversation simulation
    turns = [
        ("Hello", "Hi there!"),
        ("How are you?", "I'm doing well, thanks!"),
        ("What can you do?", "I can help with various tasks.")
    ]
    
    conversation = service.simulate_multi_turn_conversation(scenario_id, turns)
    assert "User: Hello" in conversation
    assert "Assistant: Hi there!" in conversation
    
    # Test scenario cloning
    cloned_id = service.clone_scenario(scenario_id, "Cloned Scenario")
    assert cloned_id is not None
    assert cloned_id != scenario_id
    
    cloned_scenario = service.get_scenario(cloned_id)
    assert cloned_scenario.name == "Cloned Scenario"
    assert cloned_scenario.system_prompt == scenario.system_prompt
    
    # Test scenario export/import
    exported_data = service.export_scenario(scenario_id)
    assert exported_data is not None
    assert exported_data["name"] == "Test Scenario"
    
    imported_id = service.import_scenario(exported_data)
    assert imported_id is not None
    assert imported_id != scenario_id
    
    # Test statistics
    stats = service.get_context_statistics(scenario_id)
    assert "scenario_name" in stats
    assert stats["scenario_name"] == "Test Scenario"
    assert "estimated_total_tokens" in stats
    
    # Test scenario listing
    scenarios = service.list_scenarios()
    assert len(scenarios) >= 3  # Original + cloned + imported
    
    # Test scenario deletion
    assert service.delete_scenario(cloned_id) == True
    assert service.get_scenario(cloned_id) is None
    
    print("✓ Context simulation service tests passed")


def test_message_serialization():
    """Test message serialization and deserialization."""
    print("Testing Message Serialization...")
    
    # Create message
    message = ConversationMessage(
        role=MessageRole.USER,
        content="Test message",
        metadata={"source": "test"}
    )
    
    # Test serialization
    message_dict = message.to_dict()
    assert message_dict["role"] == "user"
    assert message_dict["content"] == "Test message"
    assert message_dict["metadata"]["source"] == "test"
    
    # Test deserialization
    restored_message = ConversationMessage.from_dict(message_dict)
    assert restored_message.role == MessageRole.USER
    assert restored_message.content == "Test message"
    assert restored_message.metadata["source"] == "test"
    
    print("✓ Message serialization tests passed")


def test_retention_strategies():
    """Test different memory retention strategies."""
    print("Testing Retention Strategies...")
    
    # Test sliding window strategy
    memory = ConversationMemory(max_messages=3, retention_strategy="sliding_window")
    
    memory.add_message(MessageRole.SYSTEM, "System message")
    memory.add_message(MessageRole.USER, "Message 1")
    memory.add_message(MessageRole.ASSISTANT, "Response 1")
    memory.add_message(MessageRole.USER, "Message 2")
    memory.add_message(MessageRole.ASSISTANT, "Response 2")
    
    # Should keep system message + recent messages
    assert len(memory.messages) <= 4  # System + 3 recent
    system_messages = [msg for msg in memory.messages if msg.role == MessageRole.SYSTEM]
    assert len(system_messages) == 1
    
    # Test token limit strategy
    memory = ConversationMemory(max_tokens=50, retention_strategy="token_limit")
    
    memory.add_message(MessageRole.SYSTEM, "System")
    memory.add_message(MessageRole.USER, "Short message")
    memory.add_message(MessageRole.ASSISTANT, "Short response")
    
    # Add a very long message that should trigger retention
    long_message = "This is a very long message " * 20
    memory.add_message(MessageRole.USER, long_message)
    
    # Should have removed some messages to stay under token limit
    estimated_tokens = sum(len(msg.content.split()) * 1.3 for msg in memory.messages)
    assert estimated_tokens <= memory.max_tokens * 1.2  # Allow some tolerance
    
    print("✓ Retention strategy tests passed")


def test_few_shot_selection_strategies():
    """Test different few-shot example selection strategies."""
    print("Testing Few-Shot Selection Strategies...")
    
    example_set = FewShotExampleSet(max_examples=2)
    
    # Add examples with different categories and scores
    example_set.add_example("Input A", "Output A", category="cat1", quality_score=0.8)
    example_set.add_example("Input B", "Output B", category="cat1", quality_score=0.9)
    example_set.add_example("Input C", "Output C", category="cat2", quality_score=0.7)
    example_set.add_example("Input D", "Output D", category="cat2", quality_score=0.95)
    
    # Test "all" strategy
    example_set.selection_strategy = "all"
    selected = example_set.get_selected_examples()
    assert len(selected) == 2  # Limited by max_examples
    
    # Test "best" strategy
    example_set.selection_strategy = "best"
    selected = example_set.get_selected_examples()
    assert len(selected) == 2
    assert selected[0].quality_score == 0.95  # Highest score
    assert selected[1].quality_score == 0.9   # Second highest
    
    # Test "random" strategy
    example_set.selection_strategy = "random"
    selected = example_set.get_selected_examples()
    assert len(selected) == 2
    
    # Test "category" strategy
    example_set.selection_strategy = "category"
    example_set.max_examples = 4  # Allow all examples
    selected = example_set.get_selected_examples()
    
    # Should get best from each category
    cat1_examples = [ex for ex in selected if ex.category == "cat1"]
    cat2_examples = [ex for ex in selected if ex.category == "cat2"]
    assert len(cat1_examples) >= 1
    assert len(cat2_examples) >= 1
    
    print("✓ Few-shot selection strategy tests passed")


def run_all_tests():
    """Run all context simulation tests."""
    print("=" * 60)
    print("CONTEXT SIMULATION TEST SUITE")
    print("=" * 60)
    
    try:
        test_conversation_memory()
        test_few_shot_examples()
        test_context_scenarios()
        test_context_simulation_service()
        test_message_serialization()
        test_retention_strategies()
        test_few_shot_selection_strategies()
        
        print("\n" + "=" * 60)
        print("✅ ALL CONTEXT SIMULATION TESTS PASSED!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)