"""
Context Simulation Service
=========================

Provides conversation memory simulation, few-shot example management,
and scenario-based context switching for advanced prompt engineering.
"""

import json
import uuid
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ContextType(Enum):
    """Context type enumeration."""
    CONVERSATION = "conversation"
    FEW_SHOT = "few_shot"
    SCENARIO = "scenario"
    SYSTEM = "system"


class MessageRole(Enum):
    """Message role enumeration."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"


@dataclass
class ConversationMessage:
    """Individual conversation message."""
    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationMessage':
        """Create instance from dictionary."""
        return cls(
            role=MessageRole(data["role"]),
            content=data["content"],
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat())),
            metadata=data.get("metadata", {})
        )


@dataclass
class ConversationMemory:
    """Conversation memory with configurable retention."""
    messages: List[ConversationMessage] = field(default_factory=list)
    max_messages: int = 50
    max_tokens: int = 4000
    retention_strategy: str = "sliding_window"  # sliding_window, token_limit, importance
    
    def add_message(self, role: MessageRole, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add a message to conversation memory."""
        message = ConversationMessage(
            role=role,
            content=content,
            metadata=metadata or {}
        )
        self.messages.append(message)
        self._apply_retention_policy()
    
    def get_context_string(self, include_system: bool = True) -> str:
        """Get conversation context as formatted string."""
        context_parts = []
        
        for message in self.messages:
            if not include_system and message.role == MessageRole.SYSTEM:
                continue
            
            role_name = message.role.value.title()
            context_parts.append(f"{role_name}: {message.content}")
        
        return "\n\n".join(context_parts)
    
    def get_messages_for_api(self) -> List[Dict[str, str]]:
        """Get messages formatted for API calls."""
        return [
            {"role": msg.role.value, "content": msg.content}
            for msg in self.messages
        ]
    
    def clear(self) -> None:
        """Clear all messages from memory."""
        self.messages.clear()
    
    def _apply_retention_policy(self) -> None:
        """Apply retention policy to manage memory size."""
        if self.retention_strategy == "sliding_window":
            if len(self.messages) > self.max_messages:
                # Keep system messages and recent messages
                system_messages = [msg for msg in self.messages if msg.role == MessageRole.SYSTEM]
                recent_messages = [msg for msg in self.messages if msg.role != MessageRole.SYSTEM][-self.max_messages:]
                self.messages = system_messages + recent_messages
        
        elif self.retention_strategy == "token_limit":
            # Estimate tokens and remove oldest messages if over limit
            estimated_tokens = sum(len(msg.content.split()) * 1.3 for msg in self.messages)
            while estimated_tokens > self.max_tokens and len(self.messages) > 1:
                # Remove oldest non-system message
                for i, msg in enumerate(self.messages):
                    if msg.role != MessageRole.SYSTEM:
                        self.messages.pop(i)
                        break
                estimated_tokens = sum(len(msg.content.split()) * 1.3 for msg in self.messages)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "messages": [msg.to_dict() for msg in self.messages],
            "max_messages": self.max_messages,
            "max_tokens": self.max_tokens,
            "retention_strategy": self.retention_strategy
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationMemory':
        """Create instance from dictionary."""
        memory = cls(
            max_messages=data.get("max_messages", 50),
            max_tokens=data.get("max_tokens", 4000),
            retention_strategy=data.get("retention_strategy", "sliding_window")
        )
        
        if "messages" in data:
            memory.messages = [ConversationMessage.from_dict(msg) for msg in data["messages"]]
        
        return memory


@dataclass
class FewShotExample:
    """Few-shot learning example."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    input: str = ""
    output: str = ""
    explanation: str = ""
    category: str = ""
    quality_score: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "input": self.input,
            "output": self.output,
            "explanation": self.explanation,
            "category": self.category,
            "quality_score": self.quality_score,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FewShotExample':
        """Create instance from dictionary."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            input=data.get("input", ""),
            output=data.get("output", ""),
            explanation=data.get("explanation", ""),
            category=data.get("category", ""),
            quality_score=data.get("quality_score", 1.0),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat()))
        )


@dataclass
class FewShotExampleSet:
    """Collection of few-shot examples with management capabilities."""
    name: str = ""
    description: str = ""
    examples: List[FewShotExample] = field(default_factory=list)
    selection_strategy: str = "all"  # all, random, best, category
    max_examples: int = 5
    
    def add_example(self, input_text: str, output_text: str, explanation: str = "", 
                   category: str = "", quality_score: float = 1.0) -> str:
        """Add a new example to the set."""
        example = FewShotExample(
            input=input_text,
            output=output_text,
            explanation=explanation,
            category=category,
            quality_score=quality_score
        )
        self.examples.append(example)
        return example.id
    
    def remove_example(self, example_id: str) -> bool:
        """Remove an example by ID."""
        for i, example in enumerate(self.examples):
            if example.id == example_id:
                self.examples.pop(i)
                return True
        return False
    
    def get_selected_examples(self, category: Optional[str] = None) -> List[FewShotExample]:
        """Get examples based on selection strategy."""
        available_examples = self.examples
        
        # Filter by category if specified
        if category:
            available_examples = [ex for ex in available_examples if ex.category == category]
        
        if self.selection_strategy == "all":
            return available_examples[:self.max_examples]
        
        elif self.selection_strategy == "random":
            import random
            return random.sample(available_examples, min(len(available_examples), self.max_examples))
        
        elif self.selection_strategy == "best":
            sorted_examples = sorted(available_examples, key=lambda x: x.quality_score, reverse=True)
            return sorted_examples[:self.max_examples]
        
        elif self.selection_strategy == "category":
            # Group by category and take best from each
            categories = {}
            for example in available_examples:
                if example.category not in categories:
                    categories[example.category] = []
                categories[example.category].append(example)
            
            selected = []
            examples_per_category = max(1, self.max_examples // len(categories)) if categories else 0
            
            for cat_examples in categories.values():
                sorted_cat = sorted(cat_examples, key=lambda x: x.quality_score, reverse=True)
                selected.extend(sorted_cat[:examples_per_category])
            
            return selected[:self.max_examples]
        
        return available_examples[:self.max_examples]
    
    def format_examples(self, format_template: str = "Input: {input}\nOutput: {output}") -> str:
        """Format examples as text for prompt inclusion."""
        selected_examples = self.get_selected_examples()
        formatted_parts = []
        
        for example in selected_examples:
            formatted = format_template.format(
                input=example.input,
                output=example.output,
                explanation=example.explanation,
                category=example.category
            )
            formatted_parts.append(formatted)
        
        return "\n\n".join(formatted_parts)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "examples": [ex.to_dict() for ex in self.examples],
            "selection_strategy": self.selection_strategy,
            "max_examples": self.max_examples
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FewShotExampleSet':
        """Create instance from dictionary."""
        example_set = cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            selection_strategy=data.get("selection_strategy", "all"),
            max_examples=data.get("max_examples", 5)
        )
        
        if "examples" in data:
            example_set.examples = [FewShotExample.from_dict(ex) for ex in data["examples"]]
        
        return example_set


@dataclass
class ContextScenario:
    """Context scenario for different testing situations."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    context_type: ContextType = ContextType.SCENARIO
    system_prompt: str = ""
    initial_context: str = ""
    conversation_memory: Optional[ConversationMemory] = None
    few_shot_examples: Optional[FewShotExampleSet] = None
    variables: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Initialize default values after creation."""
        if self.conversation_memory is None:
            self.conversation_memory = ConversationMemory()
        if self.few_shot_examples is None:
            self.few_shot_examples = FewShotExampleSet()
    
    def get_full_context(self, include_few_shot: bool = True, include_conversation: bool = True) -> str:
        """Get complete context string for this scenario."""
        context_parts = []
        
        # Add system prompt (with variables applied)
        if self.system_prompt:
            system_prompt = self.apply_variables(self.system_prompt)
            context_parts.append(f"System: {system_prompt}")
        
        # Add initial context (with variables applied)
        if self.initial_context:
            initial_context = self.apply_variables(self.initial_context)
            context_parts.append(initial_context)
        
        # Add few-shot examples
        if include_few_shot and self.few_shot_examples and self.few_shot_examples.examples:
            examples_text = self.few_shot_examples.format_examples()
            if examples_text:
                context_parts.append(f"Examples:\n{examples_text}")
        
        # Add conversation memory (with variables applied to messages)
        if include_conversation and self.conversation_memory and self.conversation_memory.messages:
            # Apply variables to conversation messages
            processed_messages = []
            for msg in self.conversation_memory.messages:
                processed_content = self.apply_variables(msg.content)
                processed_messages.append(f"{msg.role.value.title()}: {processed_content}")
            
            if processed_messages:
                context_parts.append(f"Conversation History:\n\n" + "\n\n".join(processed_messages))
        
        return "\n\n".join(context_parts)
    
    def apply_variables(self, template_content: str) -> str:
        """Apply scenario variables to template content."""
        content = template_content
        for var_name, var_value in self.variables.items():
            placeholder = f"{{{{{var_name}}}}}"
            content = content.replace(placeholder, str(var_value))
        return content
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "context_type": self.context_type.value,
            "system_prompt": self.system_prompt,
            "initial_context": self.initial_context,
            "conversation_memory": self.conversation_memory.to_dict() if self.conversation_memory else None,
            "few_shot_examples": self.few_shot_examples.to_dict() if self.few_shot_examples else None,
            "variables": self.variables,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContextScenario':
        """Create instance from dictionary."""
        scenario = cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            description=data.get("description", ""),
            context_type=ContextType(data.get("context_type", "scenario")),
            system_prompt=data.get("system_prompt", ""),
            initial_context=data.get("initial_context", ""),
            variables=data.get("variables", {}),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat()))
        )
        
        if data.get("conversation_memory"):
            scenario.conversation_memory = ConversationMemory.from_dict(data["conversation_memory"])
        
        if data.get("few_shot_examples"):
            scenario.few_shot_examples = FewShotExampleSet.from_dict(data["few_shot_examples"])
        
        return scenario


class ContextSimulationService:
    """
    Service for managing context simulation including conversation memory,
    few-shot examples, and scenario-based context switching.
    """
    
    def __init__(self):
        """Initialize the context simulation service."""
        self.scenarios: Dict[str, ContextScenario] = {}
        self.active_scenario_id: Optional[str] = None
    
    # Conversation Memory Management
    
    def create_conversation_memory(self, max_messages: int = 50, max_tokens: int = 4000,
                                 retention_strategy: str = "sliding_window") -> ConversationMemory:
        """Create a new conversation memory instance."""
        return ConversationMemory(
            max_messages=max_messages,
            max_tokens=max_tokens,
            retention_strategy=retention_strategy
        )
    
    def add_conversation_message(self, memory: ConversationMemory, role: str, content: str,
                               metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add a message to conversation memory."""
        message_role = MessageRole(role.lower())
        memory.add_message(message_role, content, metadata)
    
    def simulate_conversation_turn(self, memory: ConversationMemory, user_input: str,
                                 assistant_response: str) -> None:
        """Simulate a complete conversation turn."""
        memory.add_message(MessageRole.USER, user_input)
        memory.add_message(MessageRole.ASSISTANT, assistant_response)
    
    # Few-Shot Example Management
    
    def create_few_shot_set(self, name: str, description: str = "",
                           selection_strategy: str = "all", max_examples: int = 5) -> FewShotExampleSet:
        """Create a new few-shot example set."""
        return FewShotExampleSet(
            name=name,
            description=description,
            selection_strategy=selection_strategy,
            max_examples=max_examples
        )
    
    def add_few_shot_example(self, example_set: FewShotExampleSet, input_text: str,
                           output_text: str, explanation: str = "", category: str = "",
                           quality_score: float = 1.0) -> str:
        """Add a few-shot example to a set."""
        return example_set.add_example(input_text, output_text, explanation, category, quality_score)
    
    def get_few_shot_context(self, example_set: FewShotExampleSet, category: Optional[str] = None,
                           format_template: str = "Input: {input}\nOutput: {output}") -> str:
        """Get formatted few-shot examples for context."""
        if category:
            # Temporarily filter by category
            original_examples = example_set.examples
            example_set.examples = [ex for ex in original_examples if ex.category == category]
            result = example_set.format_examples(format_template)
            example_set.examples = original_examples
            return result
        
        return example_set.format_examples(format_template)
    
    # Scenario Management
    
    def create_scenario(self, name: str, description: str = "", context_type: str = "scenario",
                       system_prompt: str = "", initial_context: str = "") -> str:
        """Create a new context scenario."""
        scenario = ContextScenario(
            name=name,
            description=description,
            context_type=ContextType(context_type),
            system_prompt=system_prompt,
            initial_context=initial_context
        )
        
        self.scenarios[scenario.id] = scenario
        return scenario.id
    
    def get_scenario(self, scenario_id: str) -> Optional[ContextScenario]:
        """Get a scenario by ID."""
        return self.scenarios.get(scenario_id)
    
    def update_scenario(self, scenario_id: str, **updates) -> bool:
        """Update scenario properties."""
        scenario = self.scenarios.get(scenario_id)
        if not scenario:
            return False
        
        for key, value in updates.items():
            if hasattr(scenario, key):
                setattr(scenario, key, value)
        
        return True
    
    def delete_scenario(self, scenario_id: str) -> bool:
        """Delete a scenario."""
        if scenario_id in self.scenarios:
            del self.scenarios[scenario_id]
            if self.active_scenario_id == scenario_id:
                self.active_scenario_id = None
            return True
        return False
    
    def list_scenarios(self) -> List[Dict[str, Any]]:
        """List all scenarios with basic info."""
        return [
            {
                "id": scenario.id,
                "name": scenario.name,
                "description": scenario.description,
                "context_type": scenario.context_type.value,
                "created_at": scenario.created_at.isoformat()
            }
            for scenario in self.scenarios.values()
        ]
    
    def set_active_scenario(self, scenario_id: str) -> bool:
        """Set the active scenario for context switching."""
        if scenario_id in self.scenarios:
            self.active_scenario_id = scenario_id
            return True
        return False
    
    def get_active_scenario(self) -> Optional[ContextScenario]:
        """Get the currently active scenario."""
        if self.active_scenario_id:
            return self.scenarios.get(self.active_scenario_id)
        return None
    
    # Context Generation and Application
    
    def generate_context_for_prompt(self, prompt_content: str, scenario_id: Optional[str] = None,
                                  include_few_shot: bool = True, include_conversation: bool = True) -> str:
        """Generate complete context for a prompt using a scenario."""
        scenario = None
        if scenario_id:
            scenario = self.get_scenario(scenario_id)
        elif self.active_scenario_id:
            scenario = self.get_active_scenario()
        
        if not scenario:
            return prompt_content
        
        # Get scenario context
        context = scenario.get_full_context(include_few_shot, include_conversation)
        
        # Apply variables to prompt
        processed_prompt = scenario.apply_variables(prompt_content)
        
        # Combine context and prompt
        if context:
            return f"{context}\n\n{processed_prompt}"
        
        return processed_prompt
    
    def simulate_multi_turn_conversation(self, scenario_id: str, turns: List[Tuple[str, str]]) -> str:
        """Simulate a multi-turn conversation in a scenario."""
        scenario = self.get_scenario(scenario_id)
        if not scenario or not scenario.conversation_memory:
            return ""
        
        # Clear existing conversation
        scenario.conversation_memory.clear()
        
        # Add system prompt if available
        if scenario.system_prompt:
            scenario.conversation_memory.add_message(MessageRole.SYSTEM, scenario.system_prompt)
        
        # Add conversation turns
        for user_input, assistant_response in turns:
            scenario.conversation_memory.add_message(MessageRole.USER, user_input)
            scenario.conversation_memory.add_message(MessageRole.ASSISTANT, assistant_response)
        
        return scenario.conversation_memory.get_context_string()
    
    def clone_scenario(self, scenario_id: str, new_name: str) -> Optional[str]:
        """Clone an existing scenario with a new name."""
        original = self.get_scenario(scenario_id)
        if not original:
            return None
        
        # Create new scenario from original data
        scenario_data = original.to_dict()
        scenario_data["name"] = new_name
        scenario_data["id"] = str(uuid.uuid4())
        
        new_scenario = ContextScenario.from_dict(scenario_data)
        self.scenarios[new_scenario.id] = new_scenario
        
        return new_scenario.id
    
    def export_scenario(self, scenario_id: str) -> Optional[Dict[str, Any]]:
        """Export scenario data for backup or sharing."""
        scenario = self.get_scenario(scenario_id)
        if scenario:
            return scenario.to_dict()
        return None
    
    def import_scenario(self, scenario_data: Dict[str, Any]) -> str:
        """Import scenario data from backup or sharing."""
        scenario = ContextScenario.from_dict(scenario_data)
        # Generate new ID to avoid conflicts
        scenario.id = str(uuid.uuid4())
        self.scenarios[scenario.id] = scenario
        return scenario.id
    
    def get_context_statistics(self, scenario_id: str) -> Dict[str, Any]:
        """Get statistics about a scenario's context."""
        scenario = self.get_scenario(scenario_id)
        if not scenario:
            return {}
        
        stats = {
            "scenario_name": scenario.name,
            "context_type": scenario.context_type.value,
            "system_prompt_length": len(scenario.system_prompt),
            "initial_context_length": len(scenario.initial_context),
            "variable_count": len(scenario.variables),
            "conversation_messages": 0,
            "few_shot_examples": 0,
            "estimated_total_tokens": 0
        }
        
        if scenario.conversation_memory:
            stats["conversation_messages"] = len(scenario.conversation_memory.messages)
        
        if scenario.few_shot_examples:
            stats["few_shot_examples"] = len(scenario.few_shot_examples.examples)
        
        # Estimate total tokens (rough approximation)
        full_context = scenario.get_full_context()
        stats["estimated_total_tokens"] = len(full_context.split()) * 1.3
        
        return stats