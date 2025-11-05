"""
Workflow Data Models for MCP Admin Application
==============================================

Comprehensive data models for workflow definition, execution, and management.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from models.base import generate_id


class WorkflowStatus(Enum):
    """Workflow status enumeration."""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class StepStatus(Enum):
    """Workflow step status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class ConnectionType(Enum):
    """Connection type enumeration."""
    DATA = "data"
    CONTROL = "control"
    ERROR = "error"
    CONDITIONAL = "conditional"


class ConditionOperator(Enum):
    """Condition operator enumeration."""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    CONTAINS = "contains"
    REGEX_MATCH = "regex_match"
    IS_EMPTY = "is_empty"
    IS_NOT_EMPTY = "is_not_empty"


class ExecutionMode(Enum):
    """Workflow execution mode enumeration."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    LOOP = "loop"


@dataclass
class WorkflowPosition:
    """Position coordinates for workflow elements."""
    x: float
    y: float
    z: float = 0.0  # For layering


@dataclass
class ParameterMapping:
    """Parameter mapping between workflow steps."""
    source_step_id: str
    source_parameter: str
    target_parameter: str
    transformation: Optional[str] = None  # JavaScript expression for data transformation
    default_value: Optional[Any] = None


@dataclass
class Condition:
    """Conditional logic for workflow branching."""
    id: str = field(default_factory=generate_id)
    left_operand: str  # Parameter reference or literal value
    operator: ConditionOperator = ConditionOperator.EQUALS
    right_operand: str  # Parameter reference or literal value
    description: str = ""


@dataclass
class WorkflowStep:
    """Individual step in a workflow."""
    id: str = field(default_factory=generate_id)
    name: str = ""
    description: str = ""
    tool_id: str = ""
    position: WorkflowPosition = field(default_factory=lambda: WorkflowPosition(0, 0))
    
    # Execution configuration
    parameters: Dict[str, Any] = field(default_factory=dict)
    parameter_mappings: List[ParameterMapping] = field(default_factory=list)
    timeout: int = 300  # seconds
    retry_count: int = 0
    retry_delay: int = 5  # seconds
    
    # Conditional execution
    conditions: List[Condition] = field(default_factory=list)
    condition_logic: str = "AND"  # "AND" or "OR"
    
    # Status and results
    status: StepStatus = StepStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    execution_time: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    
    # Metadata
    enabled: bool = True
    optional: bool = False  # Can be skipped if conditions not met
    parallel_group: Optional[str] = None  # For parallel execution grouping
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "tool_id": self.tool_id,
            "position": {
                "x": self.position.x,
                "y": self.position.y,
                "z": self.position.z
            },
            "parameters": self.parameters,
            "parameter_mappings": [
                {
                    "source_step_id": pm.source_step_id,
                    "source_parameter": pm.source_parameter,
                    "target_parameter": pm.target_parameter,
                    "transformation": pm.transformation,
                    "default_value": pm.default_value
                } for pm in self.parameter_mappings
            ],
            "timeout": self.timeout,
            "retry_count": self.retry_count,
            "retry_delay": self.retry_delay,
            "conditions": [
                {
                    "id": c.id,
                    "left_operand": c.left_operand,
                    "operator": c.operator.value,
                    "right_operand": c.right_operand,
                    "description": c.description
                } for c in self.conditions
            ],
            "condition_logic": self.condition_logic,
            "status": self.status.value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "execution_time": self.execution_time,
            "result": self.result,
            "error_message": self.error_message,
            "enabled": self.enabled,
            "optional": self.optional,
            "parallel_group": self.parallel_group
        }


@dataclass
class WorkflowConnection:
    """Connection between workflow steps."""
    id: str = field(default_factory=generate_id)
    source_step_id: str = ""
    target_step_id: str = ""
    connection_type: ConnectionType = ConnectionType.DATA
    
    # For data connections
    source_output: Optional[str] = None
    target_input: Optional[str] = None
    
    # For conditional connections
    condition: Optional[Condition] = None
    
    # Visual properties
    label: str = ""
    color: str = "#666666"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "source_step_id": self.source_step_id,
            "target_step_id": self.target_step_id,
            "connection_type": self.connection_type.value,
            "source_output": self.source_output,
            "target_input": self.target_input,
            "condition": {
                "id": self.condition.id,
                "left_operand": self.condition.left_operand,
                "operator": self.condition.operator.value,
                "right_operand": self.condition.right_operand,
                "description": self.condition.description
            } if self.condition else None,
            "label": self.label,
            "color": self.color
        }


@dataclass
class WorkflowVariable:
    """Workflow-level variable definition."""
    name: str
    type: str
    description: str = ""
    default_value: Optional[Any] = None
    required: bool = False
    scope: str = "workflow"  # "workflow", "step", "global"


@dataclass
class WorkflowTrigger:
    """Workflow execution trigger configuration."""
    trigger_type: str  # "manual", "schedule", "event", "webhook"
    configuration: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True


@dataclass
class WorkflowDefinition:
    """Complete workflow definition."""
    id: str = field(default_factory=generate_id)
    name: str = ""
    description: str = ""
    version: str = "1.0.0"
    
    # Workflow structure
    steps: List[WorkflowStep] = field(default_factory=list)
    connections: List[WorkflowConnection] = field(default_factory=list)
    variables: List[WorkflowVariable] = field(default_factory=list)
    
    # Execution configuration
    execution_mode: ExecutionMode = ExecutionMode.SEQUENTIAL
    max_execution_time: int = 3600  # seconds
    max_parallel_steps: int = 5
    error_handling: str = "stop"  # "stop", "continue", "retry"
    
    # Triggers and scheduling
    triggers: List[WorkflowTrigger] = field(default_factory=list)
    
    # Metadata
    status: WorkflowStatus = WorkflowStatus.DRAFT
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
    category: str = "general"
    
    # Analytics
    execution_count: int = 0
    success_count: int = 0
    average_execution_time: float = 0.0
    last_executed: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "steps": [step.to_dict() for step in self.steps],
            "connections": [conn.to_dict() for conn in self.connections],
            "variables": [
                {
                    "name": var.name,
                    "type": var.type,
                    "description": var.description,
                    "default_value": var.default_value,
                    "required": var.required,
                    "scope": var.scope
                } for var in self.variables
            ],
            "execution_mode": self.execution_mode.value,
            "max_execution_time": self.max_execution_time,
            "max_parallel_steps": self.max_parallel_steps,
            "error_handling": self.error_handling,
            "triggers": [
                {
                    "trigger_type": trigger.trigger_type,
                    "configuration": trigger.configuration,
                    "enabled": trigger.enabled
                } for trigger in self.triggers
            ],
            "status": self.status.value,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "tags": self.tags,
            "category": self.category,
            "execution_count": self.execution_count,
            "success_count": self.success_count,
            "average_execution_time": self.average_execution_time,
            "last_executed": self.last_executed.isoformat() if self.last_executed else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowDefinition':
        """Create instance from dictionary."""
        workflow = cls()
        workflow.id = data.get("id", generate_id())
        workflow.name = data.get("name", "")
        workflow.description = data.get("description", "")
        workflow.version = data.get("version", "1.0.0")
        
        # Parse steps
        workflow.steps = []
        for step_data in data.get("steps", []):
            step = WorkflowStep()
            step.id = step_data.get("id", generate_id())
            step.name = step_data.get("name", "")
            step.description = step_data.get("description", "")
            step.tool_id = step_data.get("tool_id", "")
            
            pos_data = step_data.get("position", {})
            step.position = WorkflowPosition(
                x=pos_data.get("x", 0),
                y=pos_data.get("y", 0),
                z=pos_data.get("z", 0)
            )
            
            step.parameters = step_data.get("parameters", {})
            step.timeout = step_data.get("timeout", 300)
            step.retry_count = step_data.get("retry_count", 0)
            step.retry_delay = step_data.get("retry_delay", 5)
            step.condition_logic = step_data.get("condition_logic", "AND")
            step.enabled = step_data.get("enabled", True)
            step.optional = step_data.get("optional", False)
            step.parallel_group = step_data.get("parallel_group")
            
            # Parse parameter mappings
            for pm_data in step_data.get("parameter_mappings", []):
                mapping = ParameterMapping(
                    source_step_id=pm_data.get("source_step_id", ""),
                    source_parameter=pm_data.get("source_parameter", ""),
                    target_parameter=pm_data.get("target_parameter", ""),
                    transformation=pm_data.get("transformation"),
                    default_value=pm_data.get("default_value")
                )
                step.parameter_mappings.append(mapping)
            
            # Parse conditions
            for cond_data in step_data.get("conditions", []):
                condition = Condition(
                    id=cond_data.get("id", generate_id()),
                    left_operand=cond_data.get("left_operand", ""),
                    operator=ConditionOperator(cond_data.get("operator", "equals")),
                    right_operand=cond_data.get("right_operand", ""),
                    description=cond_data.get("description", "")
                )
                step.conditions.append(condition)
            
            workflow.steps.append(step)
        
        # Parse connections
        workflow.connections = []
        for conn_data in data.get("connections", []):
            connection = WorkflowConnection()
            connection.id = conn_data.get("id", generate_id())
            connection.source_step_id = conn_data.get("source_step_id", "")
            connection.target_step_id = conn_data.get("target_step_id", "")
            connection.connection_type = ConnectionType(conn_data.get("connection_type", "data"))
            connection.source_output = conn_data.get("source_output")
            connection.target_input = conn_data.get("target_input")
            connection.label = conn_data.get("label", "")
            connection.color = conn_data.get("color", "#666666")
            
            # Parse condition if present
            if conn_data.get("condition"):
                cond_data = conn_data["condition"]
                connection.condition = Condition(
                    id=cond_data.get("id", generate_id()),
                    left_operand=cond_data.get("left_operand", ""),
                    operator=ConditionOperator(cond_data.get("operator", "equals")),
                    right_operand=cond_data.get("right_operand", ""),
                    description=cond_data.get("description", "")
                )
            
            workflow.connections.append(connection)
        
        # Parse variables
        workflow.variables = []
        for var_data in data.get("variables", []):
            variable = WorkflowVariable(
                name=var_data.get("name", ""),
                type=var_data.get("type", "string"),
                description=var_data.get("description", ""),
                default_value=var_data.get("default_value"),
                required=var_data.get("required", False),
                scope=var_data.get("scope", "workflow")
            )
            workflow.variables.append(variable)
        
        # Parse triggers
        workflow.triggers = []
        for trigger_data in data.get("triggers", []):
            trigger = WorkflowTrigger(
                trigger_type=trigger_data.get("trigger_type", "manual"),
                configuration=trigger_data.get("configuration", {}),
                enabled=trigger_data.get("enabled", True)
            )
            workflow.triggers.append(trigger)
        
        workflow.execution_mode = ExecutionMode(data.get("execution_mode", "sequential"))
        workflow.max_execution_time = data.get("max_execution_time", 3600)
        workflow.max_parallel_steps = data.get("max_parallel_steps", 5)
        workflow.error_handling = data.get("error_handling", "stop")
        workflow.status = WorkflowStatus(data.get("status", "draft"))
        workflow.created_by = data.get("created_by", "")
        workflow.created_at = datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now()
        workflow.updated_at = datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.now()
        workflow.tags = data.get("tags", [])
        workflow.category = data.get("category", "general")
        workflow.execution_count = data.get("execution_count", 0)
        workflow.success_count = data.get("success_count", 0)
        workflow.average_execution_time = data.get("average_execution_time", 0.0)
        workflow.last_executed = datetime.fromisoformat(data["last_executed"]) if data.get("last_executed") else None
        
        return workflow


@dataclass
class WorkflowExecution:
    """Workflow execution instance."""
    id: str = field(default_factory=generate_id)
    workflow_id: str = ""
    workflow_version: str = "1.0.0"
    
    # Execution context
    input_parameters: Dict[str, Any] = field(default_factory=dict)
    variables: Dict[str, Any] = field(default_factory=dict)
    
    # Status and timing
    status: WorkflowStatus = WorkflowStatus.DRAFT
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    execution_time: Optional[float] = None
    
    # Results and errors
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    
    # Step executions
    step_executions: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Metadata
    executed_by: str = ""
    trigger_type: str = "manual"
    parent_execution_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "workflow_version": self.workflow_version,
            "input_parameters": self.input_parameters,
            "variables": self.variables,
            "status": self.status.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "execution_time": self.execution_time,
            "result": self.result,
            "error_message": self.error_message,
            "step_executions": self.step_executions,
            "executed_by": self.executed_by,
            "trigger_type": self.trigger_type,
            "parent_execution_id": self.parent_execution_id
        }


@dataclass
class WorkflowTemplate:
    """Reusable workflow template."""
    id: str = field(default_factory=generate_id)
    name: str = ""
    description: str = ""
    category: str = "general"
    tags: List[str] = field(default_factory=list)
    
    # Template definition
    workflow_definition: WorkflowDefinition = field(default_factory=WorkflowDefinition)
    
    # Template metadata
    author: str = ""
    version: str = "1.0.0"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    usage_count: int = 0
    
    # Configuration
    parameters: List[WorkflowVariable] = field(default_factory=list)
    requirements: List[str] = field(default_factory=list)  # Required tools/services
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "tags": self.tags,
            "workflow_definition": self.workflow_definition.to_dict(),
            "author": self.author,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "usage_count": self.usage_count,
            "parameters": [
                {
                    "name": param.name,
                    "type": param.type,
                    "description": param.description,
                    "default_value": param.default_value,
                    "required": param.required,
                    "scope": param.scope
                } for param in self.parameters
            ],
            "requirements": self.requirements
        }