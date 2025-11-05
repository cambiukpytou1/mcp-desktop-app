"""
Workflow Engine for MCP Admin Application
=========================================

Comprehensive workflow definition, validation, and management system.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import asdict

from models.workflow import (
    WorkflowDefinition, WorkflowStep, WorkflowConnection, WorkflowVariable,
    WorkflowTrigger, WorkflowTemplate, WorkflowStatus, StepStatus,
    ConnectionType, ConditionOperator, ExecutionMode
)
from models.base import generate_id
from core.config import ConfigManager
from data.database import DatabaseManager


class WorkflowValidationError(Exception):
    """Workflow validation error."""
    pass


class WorkflowEngine:
    """Workflow definition and management system."""
    
    def __init__(self, config_manager: ConfigManager, db_manager: DatabaseManager):
        self.config_manager = config_manager
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
        
        # In-memory workflow cache
        self._workflows: Dict[str, WorkflowDefinition] = {}
        self._templates: Dict[str, WorkflowTemplate] = {}
        
        # Initialize workflow storage
        self._initialize_workflow_storage()
    
    def _initialize_workflow_storage(self):
        """Initialize workflow storage and load existing workflows."""
        try:
            # Create workflows directory
            workflows_dir = self.config_manager.get_config_dir() / "workflows"
            workflows_dir.mkdir(exist_ok=True)
            
            # Create templates directory
            templates_dir = self.config_manager.get_config_dir() / "templates" / "workflows"
            templates_dir.mkdir(parents=True, exist_ok=True)
            
            # Load existing workflows
            self._load_workflows()
            self._load_templates()
            
            # Initialize database tables
            self._initialize_database_tables()
            
            self.logger.info("Workflow engine initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize workflow engine: {e}")
            raise
    
    def _initialize_database_tables(self):
        """Initialize workflow-related database tables."""
        try:
            with self.db_manager.get_connection() as conn:
                # Workflow definitions table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS workflow_definitions (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        description TEXT,
                        version TEXT NOT NULL DEFAULT '1.0.0',
                        definition_json TEXT NOT NULL,
                        status TEXT NOT NULL DEFAULT 'draft',
                        created_by TEXT NOT NULL,
                        created_at DATETIME NOT NULL,
                        updated_at DATETIME NOT NULL,
                        tags TEXT,  -- JSON array
                        category TEXT DEFAULT 'general',
                        execution_count INTEGER DEFAULT 0,
                        success_count INTEGER DEFAULT 0,
                        average_execution_time REAL DEFAULT 0.0,
                        last_executed DATETIME
                    )
                """)
                
                # Workflow executions table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS workflow_executions (
                        id TEXT PRIMARY KEY,
                        workflow_id TEXT NOT NULL,
                        workflow_version TEXT NOT NULL,
                        status TEXT NOT NULL DEFAULT 'pending',
                        input_parameters TEXT,  -- JSON
                        variables TEXT,  -- JSON
                        result TEXT,  -- JSON
                        error_message TEXT,
                        start_time DATETIME NOT NULL,
                        end_time DATETIME,
                        execution_time REAL,
                        executed_by TEXT NOT NULL,
                        trigger_type TEXT DEFAULT 'manual',
                        parent_execution_id TEXT,
                        step_executions TEXT,  -- JSON
                        FOREIGN KEY (workflow_id) REFERENCES workflow_definitions (id) ON DELETE CASCADE
                    )
                """)
                
                # Workflow templates table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS workflow_templates (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        description TEXT,
                        category TEXT DEFAULT 'general',
                        tags TEXT,  -- JSON array
                        template_json TEXT NOT NULL,
                        author TEXT NOT NULL,
                        version TEXT NOT NULL DEFAULT '1.0.0',
                        created_at DATETIME NOT NULL,
                        updated_at DATETIME NOT NULL,
                        usage_count INTEGER DEFAULT 0,
                        parameters TEXT,  -- JSON array
                        requirements TEXT  -- JSON array
                    )
                """)
                
                # Workflow step executions table (for detailed tracking)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS workflow_step_executions (
                        id TEXT PRIMARY KEY,
                        workflow_execution_id TEXT NOT NULL,
                        step_id TEXT NOT NULL,
                        tool_id TEXT NOT NULL,
                        status TEXT NOT NULL DEFAULT 'pending',
                        parameters TEXT,  -- JSON
                        result TEXT,  -- JSON
                        error_message TEXT,
                        start_time DATETIME,
                        end_time DATETIME,
                        execution_time REAL,
                        retry_count INTEGER DEFAULT 0,
                        FOREIGN KEY (workflow_execution_id) REFERENCES workflow_executions (id) ON DELETE CASCADE
                    )
                """)
                
                # Create indexes
                conn.execute("CREATE INDEX IF NOT EXISTS idx_workflow_definitions_status ON workflow_definitions(status)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_workflow_definitions_created_by ON workflow_definitions(created_by)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_workflow_definitions_category ON workflow_definitions(category)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_workflow_executions_workflow_id ON workflow_executions(workflow_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_workflow_executions_status ON workflow_executions(status)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_workflow_executions_executed_by ON workflow_executions(executed_by)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_workflow_templates_category ON workflow_templates(category)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_workflow_step_executions_workflow_execution ON workflow_step_executions(workflow_execution_id)")
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to initialize workflow database tables: {e}")
            raise
    
    def _load_workflows(self):
        """Load workflows from file system and database."""
        try:
            workflows_dir = self.config_manager.get_config_dir() / "workflows"
            
            # Load from database first
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT id, definition_json FROM workflow_definitions
                    WHERE status != 'archived'
                """)
                
                for row in cursor.fetchall():
                    try:
                        workflow_data = json.loads(row['definition_json'])
                        workflow = WorkflowDefinition.from_dict(workflow_data)
                        self._workflows[workflow.id] = workflow
                    except Exception as e:
                        self.logger.error(f"Failed to load workflow {row['id']}: {e}")
            
            # Load from files (for backup/migration)
            for workflow_file in workflows_dir.glob("*.json"):
                try:
                    with open(workflow_file, 'r', encoding='utf-8') as f:
                        workflow_data = json.load(f)
                    
                    workflow = WorkflowDefinition.from_dict(workflow_data)
                    if workflow.id not in self._workflows:
                        self._workflows[workflow.id] = workflow
                        # Save to database
                        self.save_workflow(workflow)
                        
                except Exception as e:
                    self.logger.error(f"Failed to load workflow from {workflow_file}: {e}")
            
            self.logger.info(f"Loaded {len(self._workflows)} workflows")
            
        except Exception as e:
            self.logger.error(f"Failed to load workflows: {e}")
    
    def _load_templates(self):
        """Load workflow templates from file system and database."""
        try:
            templates_dir = self.config_manager.get_config_dir() / "templates" / "workflows"
            
            # Load from database first
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("SELECT id, template_json FROM workflow_templates")
                
                for row in cursor.fetchall():
                    try:
                        template_data = json.loads(row['template_json'])
                        template = WorkflowTemplate(**template_data)
                        self._templates[template.id] = template
                    except Exception as e:
                        self.logger.error(f"Failed to load template {row['id']}: {e}")
            
            # Load from files (for backup/migration)
            for template_file in templates_dir.glob("*.json"):
                try:
                    with open(template_file, 'r', encoding='utf-8') as f:
                        template_data = json.load(f)
                    
                    template = WorkflowTemplate(**template_data)
                    if template.id not in self._templates:
                        self._templates[template.id] = template
                        # Save to database
                        self.save_template(template)
                        
                except Exception as e:
                    self.logger.error(f"Failed to load template from {template_file}: {e}")
            
            self.logger.info(f"Loaded {len(self._templates)} workflow templates")
            
        except Exception as e:
            self.logger.error(f"Failed to load templates: {e}")
    
    def create_workflow(self, name: str, description: str = "", created_by: str = "system") -> WorkflowDefinition:
        """Create a new workflow definition."""
        try:
            workflow = WorkflowDefinition(
                name=name,
                description=description,
                created_by=created_by,
                status=WorkflowStatus.DRAFT
            )
            
            # Validate workflow
            self.validate_workflow(workflow)
            
            # Save workflow
            self.save_workflow(workflow)
            
            # Cache workflow
            self._workflows[workflow.id] = workflow
            
            self.logger.info(f"Created workflow: {workflow.name} ({workflow.id})")
            return workflow
            
        except Exception as e:
            self.logger.error(f"Failed to create workflow: {e}")
            raise
    
    def save_workflow(self, workflow: WorkflowDefinition) -> bool:
        """Save workflow to database and file system."""
        try:
            workflow.updated_at = datetime.now()
            
            # Save to database
            with self.db_manager.get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO workflow_definitions (
                        id, name, description, version, definition_json, status,
                        created_by, created_at, updated_at, tags, category,
                        execution_count, success_count, average_execution_time, last_executed
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    workflow.id,
                    workflow.name,
                    workflow.description,
                    workflow.version,
                    json.dumps(workflow.to_dict()),
                    workflow.status.value,
                    workflow.created_by,
                    workflow.created_at,
                    workflow.updated_at,
                    json.dumps(workflow.tags),
                    workflow.category,
                    workflow.execution_count,
                    workflow.success_count,
                    workflow.average_execution_time,
                    workflow.last_executed
                ))
                conn.commit()
            
            # Save to file system (backup)
            workflows_dir = self.config_manager.get_config_dir() / "workflows"
            workflow_file = workflows_dir / f"{workflow.id}.json"
            
            with open(workflow_file, 'w', encoding='utf-8') as f:
                json.dump(workflow.to_dict(), f, indent=2, default=str)
            
            # Update cache
            self._workflows[workflow.id] = workflow
            
            self.logger.info(f"Saved workflow: {workflow.name} ({workflow.id})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save workflow {workflow.id}: {e}")
            return False
    
    def get_workflow(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        """Get workflow by ID."""
        return self._workflows.get(workflow_id)
    
    def list_workflows(self, status: Optional[WorkflowStatus] = None, 
                      category: Optional[str] = None,
                      created_by: Optional[str] = None) -> List[WorkflowDefinition]:
        """List workflows with optional filtering."""
        workflows = list(self._workflows.values())
        
        if status:
            workflows = [w for w in workflows if w.status == status]
        
        if category:
            workflows = [w for w in workflows if w.category == category]
        
        if created_by:
            workflows = [w for w in workflows if w.created_by == created_by]
        
        return sorted(workflows, key=lambda w: w.updated_at, reverse=True)
    
    def delete_workflow(self, workflow_id: str) -> bool:
        """Delete workflow."""
        try:
            if workflow_id not in self._workflows:
                return False
            
            # Delete from database
            with self.db_manager.get_connection() as conn:
                conn.execute("DELETE FROM workflow_definitions WHERE id = ?", (workflow_id,))
                conn.commit()
            
            # Delete file
            workflows_dir = self.config_manager.get_config_dir() / "workflows"
            workflow_file = workflows_dir / f"{workflow_id}.json"
            if workflow_file.exists():
                workflow_file.unlink()
            
            # Remove from cache
            del self._workflows[workflow_id]
            
            self.logger.info(f"Deleted workflow: {workflow_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete workflow {workflow_id}: {e}")
            return False
    
    def validate_workflow(self, workflow: WorkflowDefinition) -> Tuple[bool, List[str]]:
        """Validate workflow definition."""
        errors = []
        
        try:
            # Basic validation
            if not workflow.name.strip():
                errors.append("Workflow name is required")
            
            if not workflow.steps:
                errors.append("Workflow must have at least one step")
            
            # Validate steps
            step_ids = set()
            tool_ids = set()
            
            for step in workflow.steps:
                # Check for duplicate step IDs
                if step.id in step_ids:
                    errors.append(f"Duplicate step ID: {step.id}")
                step_ids.add(step.id)
                
                # Validate step properties
                if not step.name.strip():
                    errors.append(f"Step {step.id} must have a name")
                
                if not step.tool_id.strip():
                    errors.append(f"Step {step.id} must specify a tool")
                
                tool_ids.add(step.tool_id)
                
                # Validate timeout
                if step.timeout <= 0:
                    errors.append(f"Step {step.id} timeout must be positive")
                
                # Validate retry configuration
                if step.retry_count < 0:
                    errors.append(f"Step {step.id} retry count cannot be negative")
                
                if step.retry_delay <= 0 and step.retry_count > 0:
                    errors.append(f"Step {step.id} retry delay must be positive when retries are enabled")
            
            # Validate connections
            connection_ids = set()
            
            for connection in workflow.connections:
                # Check for duplicate connection IDs
                if connection.id in connection_ids:
                    errors.append(f"Duplicate connection ID: {connection.id}")
                connection_ids.add(connection.id)
                
                # Validate connection endpoints
                if connection.source_step_id not in step_ids:
                    errors.append(f"Connection {connection.id} references invalid source step: {connection.source_step_id}")
                
                if connection.target_step_id not in step_ids:
                    errors.append(f"Connection {connection.id} references invalid target step: {connection.target_step_id}")
                
                # Prevent self-connections
                if connection.source_step_id == connection.target_step_id:
                    errors.append(f"Connection {connection.id} cannot connect step to itself")
            
            # Check for cycles (basic check)
            if self._has_cycles(workflow):
                errors.append("Workflow contains cycles")
            
            # Validate variables
            variable_names = set()
            for variable in workflow.variables:
                if variable.name in variable_names:
                    errors.append(f"Duplicate variable name: {variable.name}")
                variable_names.add(variable.name)
            
            # Validate execution configuration
            if workflow.max_execution_time <= 0:
                errors.append("Maximum execution time must be positive")
            
            if workflow.max_parallel_steps <= 0:
                errors.append("Maximum parallel steps must be positive")
            
            # Validate triggers
            for i, trigger in enumerate(workflow.triggers):
                if not trigger.trigger_type:
                    errors.append(f"Trigger {i} must have a type")
            
            return len(errors) == 0, errors
            
        except Exception as e:
            self.logger.error(f"Error validating workflow: {e}")
            errors.append(f"Validation error: {str(e)}")
            return False, errors
    
    def _has_cycles(self, workflow: WorkflowDefinition) -> bool:
        """Check if workflow has cycles using DFS."""
        try:
            # Build adjacency list
            graph = {}
            for step in workflow.steps:
                graph[step.id] = []
            
            for connection in workflow.connections:
                if connection.connection_type in [ConnectionType.DATA, ConnectionType.CONTROL]:
                    if connection.source_step_id in graph:
                        graph[connection.source_step_id].append(connection.target_step_id)
            
            # DFS cycle detection
            visited = set()
            rec_stack = set()
            
            def has_cycle_util(node):
                visited.add(node)
                rec_stack.add(node)
                
                for neighbor in graph.get(node, []):
                    if neighbor not in visited:
                        if has_cycle_util(neighbor):
                            return True
                    elif neighbor in rec_stack:
                        return True
                
                rec_stack.remove(node)
                return False
            
            for step_id in graph:
                if step_id not in visited:
                    if has_cycle_util(step_id):
                        return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking for cycles: {e}")
            return True  # Assume cycle on error for safety
    
    def add_step(self, workflow_id: str, step: WorkflowStep) -> bool:
        """Add step to workflow."""
        try:
            workflow = self.get_workflow(workflow_id)
            if not workflow:
                return False
            
            # Validate step
            if not step.id:
                step.id = generate_id()
            
            # Check for duplicate step ID
            existing_ids = {s.id for s in workflow.steps}
            if step.id in existing_ids:
                return False
            
            # Add step
            workflow.steps.append(step)
            workflow.updated_at = datetime.now()
            
            # Validate and save
            is_valid, errors = self.validate_workflow(workflow)
            if is_valid:
                return self.save_workflow(workflow)
            else:
                # Remove step if validation fails
                workflow.steps.remove(step)
                self.logger.error(f"Failed to add step: {errors}")
                return False
            
        except Exception as e:
            self.logger.error(f"Failed to add step to workflow {workflow_id}: {e}")
            return False
    
    def remove_step(self, workflow_id: str, step_id: str) -> bool:
        """Remove step from workflow."""
        try:
            workflow = self.get_workflow(workflow_id)
            if not workflow:
                return False
            
            # Find and remove step
            step_to_remove = None
            for step in workflow.steps:
                if step.id == step_id:
                    step_to_remove = step
                    break
            
            if not step_to_remove:
                return False
            
            # Remove step
            workflow.steps.remove(step_to_remove)
            
            # Remove connections involving this step
            connections_to_remove = []
            for connection in workflow.connections:
                if connection.source_step_id == step_id or connection.target_step_id == step_id:
                    connections_to_remove.append(connection)
            
            for connection in connections_to_remove:
                workflow.connections.remove(connection)
            
            workflow.updated_at = datetime.now()
            
            return self.save_workflow(workflow)
            
        except Exception as e:
            self.logger.error(f"Failed to remove step {step_id} from workflow {workflow_id}: {e}")
            return False
    
    def add_connection(self, workflow_id: str, connection: WorkflowConnection) -> bool:
        """Add connection to workflow."""
        try:
            workflow = self.get_workflow(workflow_id)
            if not workflow:
                return False
            
            # Validate connection
            if not connection.id:
                connection.id = generate_id()
            
            # Check for duplicate connection ID
            existing_ids = {c.id for c in workflow.connections}
            if connection.id in existing_ids:
                return False
            
            # Validate step references
            step_ids = {s.id for s in workflow.steps}
            if connection.source_step_id not in step_ids or connection.target_step_id not in step_ids:
                return False
            
            # Add connection
            workflow.connections.append(connection)
            workflow.updated_at = datetime.now()
            
            # Validate and save
            is_valid, errors = self.validate_workflow(workflow)
            if is_valid:
                return self.save_workflow(workflow)
            else:
                # Remove connection if validation fails
                workflow.connections.remove(connection)
                self.logger.error(f"Failed to add connection: {errors}")
                return False
            
        except Exception as e:
            self.logger.error(f"Failed to add connection to workflow {workflow_id}: {e}")
            return False
    
    def remove_connection(self, workflow_id: str, connection_id: str) -> bool:
        """Remove connection from workflow."""
        try:
            workflow = self.get_workflow(workflow_id)
            if not workflow:
                return False
            
            # Find and remove connection
            connection_to_remove = None
            for connection in workflow.connections:
                if connection.id == connection_id:
                    connection_to_remove = connection
                    break
            
            if not connection_to_remove:
                return False
            
            # Remove connection
            workflow.connections.remove(connection_to_remove)
            workflow.updated_at = datetime.now()
            
            return self.save_workflow(workflow)
            
        except Exception as e:
            self.logger.error(f"Failed to remove connection {connection_id} from workflow {workflow_id}: {e}")
            return False
    
    def create_template(self, name: str, description: str, workflow: WorkflowDefinition,
                       author: str = "system", category: str = "general") -> WorkflowTemplate:
        """Create workflow template from workflow definition."""
        try:
            template = WorkflowTemplate(
                name=name,
                description=description,
                category=category,
                workflow_definition=workflow,
                author=author
            )
            
            # Save template
            self.save_template(template)
            
            # Cache template
            self._templates[template.id] = template
            
            self.logger.info(f"Created workflow template: {template.name} ({template.id})")
            return template
            
        except Exception as e:
            self.logger.error(f"Failed to create workflow template: {e}")
            raise
    
    def save_template(self, template: WorkflowTemplate) -> bool:
        """Save workflow template to database and file system."""
        try:
            template.updated_at = datetime.now()
            
            # Save to database
            with self.db_manager.get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO workflow_templates (
                        id, name, description, category, tags, template_json,
                        author, version, created_at, updated_at, usage_count,
                        parameters, requirements
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    template.id,
                    template.name,
                    template.description,
                    template.category,
                    json.dumps(template.tags),
                    json.dumps(template.to_dict()),
                    template.author,
                    template.version,
                    template.created_at,
                    template.updated_at,
                    template.usage_count,
                    json.dumps([asdict(p) for p in template.parameters]),
                    json.dumps(template.requirements)
                ))
                conn.commit()
            
            # Save to file system (backup)
            templates_dir = self.config_manager.get_config_dir() / "templates" / "workflows"
            template_file = templates_dir / f"{template.id}.json"
            
            with open(template_file, 'w', encoding='utf-8') as f:
                json.dump(template.to_dict(), f, indent=2, default=str)
            
            # Update cache
            self._templates[template.id] = template
            
            self.logger.info(f"Saved workflow template: {template.name} ({template.id})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save workflow template {template.id}: {e}")
            return False
    
    def get_template(self, template_id: str) -> Optional[WorkflowTemplate]:
        """Get workflow template by ID."""
        return self._templates.get(template_id)
    
    def list_templates(self, category: Optional[str] = None) -> List[WorkflowTemplate]:
        """List workflow templates with optional filtering."""
        templates = list(self._templates.values())
        
        if category:
            templates = [t for t in templates if t.category == category]
        
        return sorted(templates, key=lambda t: t.updated_at, reverse=True)
    
    def create_workflow_from_template(self, template_id: str, name: str,
                                    parameters: Dict[str, Any] = None,
                                    created_by: str = "system") -> Optional[WorkflowDefinition]:
        """Create workflow from template."""
        try:
            template = self.get_template(template_id)
            if not template:
                return None
            
            # Create new workflow from template
            workflow = WorkflowDefinition.from_dict(template.workflow_definition.to_dict())
            workflow.id = generate_id()
            workflow.name = name
            workflow.created_by = created_by
            workflow.created_at = datetime.now()
            workflow.updated_at = datetime.now()
            workflow.status = WorkflowStatus.DRAFT
            
            # Apply template parameters
            if parameters:
                for variable in workflow.variables:
                    if variable.name in parameters:
                        variable.default_value = parameters[variable.name]
            
            # Save workflow
            self.save_workflow(workflow)
            
            # Update template usage count
            template.usage_count += 1
            self.save_template(template)
            
            self.logger.info(f"Created workflow from template: {workflow.name} ({workflow.id})")
            return workflow
            
        except Exception as e:
            self.logger.error(f"Failed to create workflow from template {template_id}: {e}")
            return None
    
    def get_workflow_statistics(self) -> Dict[str, Any]:
        """Get workflow engine statistics."""
        try:
            stats = {
                "total_workflows": len(self._workflows),
                "total_templates": len(self._templates),
                "workflows_by_status": {},
                "workflows_by_category": {},
                "templates_by_category": {},
                "recent_activity": []
            }
            
            # Count by status
            for workflow in self._workflows.values():
                status = workflow.status.value
                stats["workflows_by_status"][status] = stats["workflows_by_status"].get(status, 0) + 1
            
            # Count by category
            for workflow in self._workflows.values():
                category = workflow.category
                stats["workflows_by_category"][category] = stats["workflows_by_category"].get(category, 0) + 1
            
            for template in self._templates.values():
                category = template.category
                stats["templates_by_category"][category] = stats["templates_by_category"].get(category, 0) + 1
            
            # Recent activity (last 10 updated workflows)
            recent_workflows = sorted(self._workflows.values(), key=lambda w: w.updated_at, reverse=True)[:10]
            stats["recent_activity"] = [
                {
                    "id": w.id,
                    "name": w.name,
                    "status": w.status.value,
                    "updated_at": w.updated_at.isoformat()
                } for w in recent_workflows
            ]
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get workflow statistics: {e}")
            return {}