"""
Advanced Templating Engine
=========================

Jinja2-based templating system for prompt variable substitution and validation
with context simulation support.
"""

import re
import json
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
import jinja2
from jinja2 import Environment, BaseLoader, Template, TemplateSyntaxError, UndefinedError
from jinja2.sandbox import SandboxedEnvironment
from .context_simulation import ContextSimulationService, ContextScenario


@dataclass
class TemplateVariable:
    """Template variable definition."""
    name: str
    type: str  # 'string', 'number', 'boolean', 'list', 'dict'
    description: str = ""
    required: bool = True
    default: Optional[Any] = None
    validation_pattern: Optional[str] = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    allowed_values: Optional[List[Any]] = None


@dataclass
class TemplateValidationResult:
    """Result of template validation."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    variables_found: List[str] = field(default_factory=list)
    variables_missing: List[str] = field(default_factory=list)


@dataclass
class TemplateRenderResult:
    """Result of template rendering."""
    success: bool
    rendered_content: str = ""
    error: Optional[str] = None
    variables_used: Dict[str, Any] = field(default_factory=dict)
    render_time: float = 0.0


class AdvancedTemplatingEngine:
    """
    Advanced templating engine with Jinja2 integration and context simulation.
    
    Provides variable substitution, validation, error handling, and context
    simulation for prompt templates with {{variable_name}} syntax.
    """
    
    def __init__(self):
        """Initialize the templating engine."""
        # Use sandboxed environment for security
        self.env = SandboxedEnvironment(
            loader=BaseLoader(),
            autoescape=False,  # Don't escape for prompt content
            trim_blocks=True,
            lstrip_blocks=True,
            undefined=jinja2.StrictUndefined  # Raise errors for undefined variables
        )
        
        # Add custom filters
        self.env.filters['json'] = json.dumps
        self.env.filters['upper'] = str.upper
        self.env.filters['lower'] = str.lower
        self.env.filters['title'] = str.title
        self.env.filters['strip'] = str.strip
        
        # Variable pattern for detection
        self.variable_pattern = re.compile(r'\{\{\s*([^}]+)\s*\}\}')
        
        # Context simulation service
        self.context_service = ContextSimulationService()
    
    def extract_variables(self, template_content: str) -> List[str]:
        """
        Extract variable names from template content.
        
        Args:
            template_content: Template content to analyze
            
        Returns:
            List of variable names found in template
        """
        variables = []
        matches = self.variable_pattern.findall(template_content)
        
        for match in matches:
            # Clean up variable name (remove filters, etc.)
            var_name = match.split('|')[0].strip()
            if var_name not in variables:
                variables.append(var_name)
        
        return variables
    
    def validate_template(
        self, 
        template_content: str, 
        variable_definitions: Optional[List[TemplateVariable]] = None
    ) -> TemplateValidationResult:
        """
        Validate template syntax and variable usage.
        
        Args:
            template_content: Template content to validate
            variable_definitions: Optional variable definitions for validation
            
        Returns:
            TemplateValidationResult with validation details
        """
        result = TemplateValidationResult(is_valid=True)
        
        try:
            # Test template compilation
            template = self.env.from_string(template_content)
            
            # Extract variables from template
            result.variables_found = self.extract_variables(template_content)
            
            # Validate against definitions if provided
            if variable_definitions:
                defined_vars = {var.name for var in variable_definitions}
                found_vars = set(result.variables_found)
                
                # Check for undefined variables
                result.variables_missing = list(found_vars - defined_vars)
                if result.variables_missing:
                    result.warnings.append(
                        f"Variables used but not defined: {', '.join(result.variables_missing)}"
                    )
                
                # Check for unused definitions
                unused_vars = defined_vars - found_vars
                if unused_vars:
                    result.warnings.append(
                        f"Variables defined but not used: {', '.join(unused_vars)}"
                    )
            
        except TemplateSyntaxError as e:
            result.is_valid = False
            result.errors.append(f"Template syntax error: {e}")
        except Exception as e:
            result.is_valid = False
            result.errors.append(f"Template validation error: {e}")
        
        return result
    
    def validate_variable_value(
        self, 
        variable: TemplateVariable, 
        value: Any
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate a variable value against its definition.
        
        Args:
            variable: Variable definition
            value: Value to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if value is None:
            if variable.required:
                return False, f"Required variable '{variable.name}' is missing"
            return True, None
        
        # Type validation
        if variable.type == 'string':
            if not isinstance(value, str):
                return False, f"Variable '{variable.name}' must be a string"
        elif variable.type == 'number':
            if not isinstance(value, (int, float)):
                return False, f"Variable '{variable.name}' must be a number"
        elif variable.type == 'boolean':
            if not isinstance(value, bool):
                return False, f"Variable '{variable.name}' must be a boolean"
        elif variable.type == 'list':
            if not isinstance(value, list):
                return False, f"Variable '{variable.name}' must be a list"
        elif variable.type == 'dict':
            if not isinstance(value, dict):
                return False, f"Variable '{variable.name}' must be a dictionary"
        
        # Pattern validation for strings
        if variable.validation_pattern and isinstance(value, str):
            if not re.match(variable.validation_pattern, value):
                return False, f"Variable '{variable.name}' does not match required pattern"
        
        # Range validation for numbers
        if isinstance(value, (int, float)):
            if variable.min_value is not None and value < variable.min_value:
                return False, f"Variable '{variable.name}' must be >= {variable.min_value}"
            if variable.max_value is not None and value > variable.max_value:
                return False, f"Variable '{variable.name}' must be <= {variable.max_value}"
        
        # Allowed values validation
        if variable.allowed_values and value not in variable.allowed_values:
            return False, f"Variable '{variable.name}' must be one of: {variable.allowed_values}"
        
        return True, None
    
    def render_template(
        self, 
        template_content: str, 
        variables: Dict[str, Any],
        variable_definitions: Optional[List[TemplateVariable]] = None
    ) -> TemplateRenderResult:
        """
        Render template with provided variables.
        
        Args:
            template_content: Template content to render
            variables: Variable values for substitution
            variable_definitions: Optional variable definitions for validation
            
        Returns:
            TemplateRenderResult with rendered content or error
        """
        start_time = datetime.now()
        result = TemplateRenderResult(success=False)
        
        try:
            # Validate variable values if definitions provided
            if variable_definitions:
                for var_def in variable_definitions:
                    value = variables.get(var_def.name, var_def.default)
                    is_valid, error = self.validate_variable_value(var_def, value)
                    if not is_valid:
                        result.error = error
                        return result
                    
                    # Use default if not provided
                    if var_def.name not in variables and var_def.default is not None:
                        variables[var_def.name] = var_def.default
            
            # Compile and render template
            template = self.env.from_string(template_content)
            result.rendered_content = template.render(**variables)
            result.success = True
            result.variables_used = variables.copy()
            
        except UndefinedError as e:
            result.error = f"Undefined variable: {e}"
        except TemplateSyntaxError as e:
            result.error = f"Template syntax error: {e}"
        except Exception as e:
            result.error = f"Template rendering error: {e}"
        
        # Calculate render time
        end_time = datetime.now()
        result.render_time = (end_time - start_time).total_seconds()
        
        return result
    
    def create_template_from_content(
        self, 
        content: str, 
        auto_detect_variables: bool = True
    ) -> Tuple[Template, List[TemplateVariable]]:
        """
        Create a Jinja2 template and auto-detect variables.
        
        Args:
            content: Template content
            auto_detect_variables: Whether to auto-detect variables
            
        Returns:
            Tuple of (compiled_template, detected_variables)
        """
        template = self.env.from_string(content)
        variables = []
        
        if auto_detect_variables:
            var_names = self.extract_variables(content)
            for var_name in var_names:
                variables.append(TemplateVariable(
                    name=var_name,
                    type='string',  # Default to string
                    description=f"Auto-detected variable: {var_name}",
                    required=True
                ))
        
        return template, variables
    
    def get_template_info(self, template_content: str) -> Dict[str, Any]:
        """
        Get comprehensive information about a template.
        
        Args:
            template_content: Template content to analyze
            
        Returns:
            Dictionary with template information
        """
        variables = self.extract_variables(template_content)
        validation = self.validate_template(template_content)
        
        return {
            'variables_count': len(variables),
            'variables': variables,
            'is_valid': validation.is_valid,
            'errors': validation.errors,
            'warnings': validation.warnings,
            'complexity_score': self._calculate_complexity(template_content),
            'estimated_render_time': self._estimate_render_time(template_content)
        }
    
    def _calculate_complexity(self, template_content: str) -> int:
        """Calculate template complexity score."""
        score = 0
        
        # Count variables
        score += len(self.extract_variables(template_content))
        
        # Count control structures
        score += len(re.findall(r'\{%\s*(if|for|while|with)', template_content))
        
        # Count filters
        score += len(re.findall(r'\|', template_content))
        
        return score
    
    def _estimate_render_time(self, template_content: str) -> float:
        """Estimate template rendering time in seconds."""
        # Simple heuristic based on content length and complexity
        base_time = len(template_content) * 0.00001  # 0.01ms per character
        complexity_time = self._calculate_complexity(template_content) * 0.001  # 1ms per complexity point
        
        return base_time + complexity_time
    
    # Context Simulation Integration
    
    def render_with_context(
        self,
        template_content: str,
        variables: Dict[str, Any],
        scenario_id: Optional[str] = None,
        include_few_shot: bool = True,
        include_conversation: bool = True,
        variable_definitions: Optional[List[TemplateVariable]] = None
    ) -> TemplateRenderResult:
        """
        Render template with context simulation support.
        
        Args:
            template_content: Template content to render
            variables: Variable values for substitution
            scenario_id: Optional scenario ID for context simulation
            include_few_shot: Whether to include few-shot examples
            include_conversation: Whether to include conversation history
            variable_definitions: Optional variable definitions for validation
            
        Returns:
            TemplateRenderResult with rendered content including context
        """
        start_time = datetime.now()
        result = TemplateRenderResult(success=False)
        
        try:
            # Generate context-enhanced prompt
            enhanced_prompt = self.context_service.generate_context_for_prompt(
                template_content,
                scenario_id,
                include_few_shot,
                include_conversation
            )
            
            # Render the enhanced prompt with variables
            render_result = self.render_template(enhanced_prompt, variables, variable_definitions)
            
            # Update result with context information
            result.success = render_result.success
            result.rendered_content = render_result.rendered_content
            result.error = render_result.error
            result.variables_used = render_result.variables_used
            
            # Add context metadata and scenario variables
            if scenario_id:
                scenario = self.context_service.get_scenario(scenario_id)
                if scenario:
                    result.variables_used['_context_scenario'] = scenario.name
                    result.variables_used['_context_type'] = scenario.context_type.value
                    # Include scenario variables in the result
                    result.variables_used.update(scenario.variables)
            
        except Exception as e:
            result.error = f"Context rendering error: {e}"
        
        # Calculate render time
        end_time = datetime.now()
        result.render_time = (end_time - start_time).total_seconds()
        
        return result
    
    def create_context_scenario(
        self,
        name: str,
        description: str = "",
        system_prompt: str = "",
        initial_context: str = "",
        variables: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new context scenario for template rendering.
        
        Args:
            name: Scenario name
            description: Scenario description
            system_prompt: System prompt for the scenario
            initial_context: Initial context text
            variables: Default variables for the scenario
            
        Returns:
            Scenario ID
        """
        scenario_id = self.context_service.create_scenario(
            name=name,
            description=description,
            system_prompt=system_prompt,
            initial_context=initial_context
        )
        
        if variables:
            scenario = self.context_service.get_scenario(scenario_id)
            if scenario:
                scenario.variables.update(variables)
        
        return scenario_id
    
    def add_few_shot_examples(
        self,
        scenario_id: str,
        examples: List[Tuple[str, str, str]]  # (input, output, explanation)
    ) -> bool:
        """
        Add few-shot examples to a scenario.
        
        Args:
            scenario_id: Scenario ID
            examples: List of (input, output, explanation) tuples
            
        Returns:
            Success status
        """
        scenario = self.context_service.get_scenario(scenario_id)
        if not scenario:
            return False
        
        for input_text, output_text, explanation in examples:
            scenario.few_shot_examples.add_example(
                input_text, output_text, explanation
            )
        
        return True
    
    def simulate_conversation(
        self,
        scenario_id: str,
        conversation_turns: List[Tuple[str, str]]  # (user_input, assistant_response)
    ) -> bool:
        """
        Simulate a conversation in a scenario.
        
        Args:
            scenario_id: Scenario ID
            conversation_turns: List of (user_input, assistant_response) tuples
            
        Returns:
            Success status
        """
        return bool(self.context_service.simulate_multi_turn_conversation(
            scenario_id, conversation_turns
        ))
    
    def get_context_preview(
        self,
        template_content: str,
        scenario_id: Optional[str] = None,
        include_few_shot: bool = True,
        include_conversation: bool = True
    ) -> str:
        """
        Get a preview of how the template will look with context.
        
        Args:
            template_content: Template content
            scenario_id: Optional scenario ID
            include_few_shot: Whether to include few-shot examples
            include_conversation: Whether to include conversation history
            
        Returns:
            Preview of the contextualized template
        """
        return self.context_service.generate_context_for_prompt(
            template_content,
            scenario_id,
            include_few_shot,
            include_conversation
        )
    
    def list_scenarios(self) -> List[Dict[str, Any]]:
        """List all available context scenarios."""
        return self.context_service.list_scenarios()
    
    def get_scenario_info(self, scenario_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a scenario."""
        scenario = self.context_service.get_scenario(scenario_id)
        if scenario:
            return {
                "id": scenario.id,
                "name": scenario.name,
                "description": scenario.description,
                "context_type": scenario.context_type.value,
                "system_prompt": scenario.system_prompt,
                "initial_context": scenario.initial_context,
                "variables": scenario.variables,
                "conversation_messages": len(scenario.conversation_memory.messages) if scenario.conversation_memory else 0,
                "few_shot_examples": len(scenario.few_shot_examples.examples) if scenario.few_shot_examples else 0,
                "created_at": scenario.created_at.isoformat()
            }
        return None
    
    def export_scenario(self, scenario_id: str) -> Optional[Dict[str, Any]]:
        """Export a scenario for backup or sharing."""
        return self.context_service.export_scenario(scenario_id)
    
    def import_scenario(self, scenario_data: Dict[str, Any]) -> str:
        """Import a scenario from backup or sharing."""
        return self.context_service.import_scenario(scenario_data)


class TemplatingEngine:
    """Advanced templating engine for prompt processing."""
    
    def __init__(self, config_manager, db_manager):
        self.config_manager = config_manager
        self.db_manager = db_manager
        
        # Initialize Jinja2 environment
        self.env = SandboxedEnvironment(
            loader=BaseLoader(),
            autoescape=False,
            undefined=jinja2.StrictUndefined
        )
        
        # Context simulation service
        self.context_service = ContextSimulationService()
    
    def create_template(self, template_data: Dict[str, Any]) -> str:
        """Create a new template."""
        try:
            # Implementation would create template in database
            template_id = f"template_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            return template_id
        except Exception as e:
            raise Exception(f"Failed to create template: {e}")
    
    def update_template(self, template_id: str, template_data: Dict[str, Any]) -> bool:
        """Update an existing template."""
        try:
            # Implementation would update template in database
            return True
        except Exception as e:
            raise Exception(f"Failed to update template: {e}")
    
    def validate_template(self, content: str) -> TemplateValidationResult:
        """Validate template syntax and structure."""
        try:
            # Parse template to check for syntax errors
            template = self.env.from_string(content)
            
            # Extract variables
            variables = self._extract_variables(content)
            
            return TemplateValidationResult(
                is_valid=True,
                variables_found=variables
            )
        except TemplateSyntaxError as e:
            return TemplateValidationResult(
                is_valid=False,
                errors=[f"Template syntax error: {e}"]
            )
        except Exception as e:
            return TemplateValidationResult(
                is_valid=False,
                errors=[f"Validation error: {e}"]
            )
    
    def render_template(self, content: str, variables: Dict[str, Any]) -> TemplateRenderResult:
        """Render template with provided variables."""
        try:
            template = self.env.from_string(content)
            rendered = template.render(**variables)
            
            return TemplateRenderResult(
                success=True,
                rendered_content=rendered,
                variables_used=variables
            )
        except UndefinedError as e:
            return TemplateRenderResult(
                success=False,
                error=f"Missing variable: {e}"
            )
        except Exception as e:
            return TemplateRenderResult(
                success=False,
                error=f"Rendering error: {e}"
            )
    
    def _extract_variables(self, content: str) -> List[str]:
        """Extract variable names from template content."""
        # Simple regex to find Jinja2 variables
        pattern = r'\{\{\s*([^}]+)\s*\}\}'
        matches = re.findall(pattern, content)
        
        # Clean up variable names
        variables = []
        for match in matches:
            # Remove filters and other Jinja2 syntax
            var_name = match.split('|')[0].split('.')[0].strip()
            if var_name and var_name not in variables:
                variables.append(var_name)
        
        return variables