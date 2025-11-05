"""
Workflow Execution Engine for MCP Admin Application
===================================================

Workflow execution and monitoring system with step-by-step processing.
"""

import asyncio
import json
import logging
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from concurrent.futures import ThreadPoolExecutor, Future
from dataclasses import asdict

from models.workflow import (
    WorkflowDefinition, WorkflowStep, WorkflowExecution, WorkflowConnection,
    WorkflowStatus, StepStatus, ConnectionType, ConditionOperator, ExecutionMode
)
from models.tool import ToolExecution, ExecutionStatus
from models.base import generate_id
from services.tool_execution import ToolExecutionService
from services.workflow_engine import WorkflowEngine
from data.database import DatabaseManager


class WorkflowExecutionError(Exception):
    """Workflow execution error."""
    pass


class WorkflowContext:
    """Execution context for a workflow."""
    
    def __init__(self, workflow: WorkflowDefinition, execution: WorkflowExecution):
        self.workflow = workflow
        self.execution = execution
        self.variables: Dict[str, Any] = {}
        self.step_results: Dict[str, Any] = {}
        self.step_statuses: Dict[str, StepStatus] = {}
        self.running_steps: Dict[str, Future] = {}
        self.completed_steps: set = set()
        self.failed_steps: set = set()
        self.cancelled = False
        
        # Initialize variables
        for variable in workflow.variables:
            self.variables[variable.name] = variable.default_value
        
        # Apply input parameters
        self.variables.update(execution.input_parameters)
        
        # Initialize step statuses
        for step in workflow.steps:
            self.step_statuses[step.id] = StepStatus.PENDING


class WorkflowExecutor:
    """Workflow execution and monitoring system."""
    
    def __init__(self, workflow_engine: WorkflowEngine, tool_executor: ToolExecutionService,
                 db_manager: DatabaseManager):
        self.workflow_engine = workflow_engine
        self.tool_executor = tool_executor
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
        
        # Execution management
        self._active_executions: Dict[str, WorkflowContext] = {}
        self._execution_callbacks: Dict[str, List[Callable]] = {}
        self._executor = ThreadPoolExecutor(max_workers=10, thread_name_prefix="workflow-executor")
        
        # Initialize database tables
        self._initialize_database_tables()
    
    def _initialize_database_tables(self):
        """Initialize workflow execution database tables."""
        # Tables are already created in workflow_engine.py
        pass
    
    def execute_workflow(self, workflow_id: str, input_parameters: Dict[str, Any] = None,
                        executed_by: str = "system", trigger_type: str = "manual") -> Optional[WorkflowExecution]:
        """Execute a workflow asynchronously."""
        try:
            workflow = self.workflow_engine.get_workflow(workflow_id)
            if not workflow:
                raise WorkflowExecutionError(f"Workflow not found: {workflow_id}")
            
            if workflow.status != WorkflowStatus.ACTIVE:
                raise WorkflowExecutionError(f"Workflow is not active: {workflow.status.value}")
            
            # Create execution record
            execution = WorkflowExecution(
                workflow_id=workflow_id,
                workflow_version=workflow.version,
                input_parameters=input_parameters or {},
                executed_by=executed_by,
                trigger_type=trigger_type,
                status=WorkflowStatus.DRAFT
            )
            
            # Save execution to database
            self._save_execution(execution)
            
            # Create execution context
            context = WorkflowContext(workflow, execution)
            self._active_executions[execution.id] = context
            
            # Start execution in background
            future = self._executor.submit(self._execute_workflow_sync, context)
            
            self.logger.info(f"Started workflow execution: {execution.id}")
            return execution
            
        except Exception as e:
            self.logger.error(f"Failed to execute workflow {workflow_id}: {e}")
            raise WorkflowExecutionError(str(e))
    
    def _execute_workflow_sync(self, context: WorkflowContext):
        """Execute workflow synchronously in background thread."""
        try:
            execution = context.execution
            workflow = context.workflow
            
            # Update execution status
            execution.status = WorkflowStatus.ACTIVE
            execution.start_time = datetime.now()
            self._save_execution(execution)
            
            self.logger.info(f"Executing workflow: {workflow.name} ({execution.id})")
            
            # Execute based on execution mode
            if workflow.execution_mode == ExecutionMode.SEQUENTIAL:
                self._execute_sequential(context)
            elif workflow.execution_mode == ExecutionMode.PARALLEL:
                self._execute_parallel(context)
            elif workflow.execution_mode == ExecutionMode.CONDITIONAL:
                self._execute_conditional(context)
            else:
                raise WorkflowExecutionError(f"Unsupported execution mode: {workflow.execution_mode}")
            
            # Check final status
            if context.cancelled:
                execution.status = WorkflowStatus.CANCELLED
            elif context.failed_steps:
                execution.status = WorkflowStatus.FAILED
                execution.error_message = f"Failed steps: {', '.join(context.failed_steps)}"
            else:
                execution.status = WorkflowStatus.COMPLETED
            
            # Finalize execution
            execution.end_time = datetime.now()
            execution.execution_time = (execution.end_time - execution.start_time).total_seconds()
            execution.result = context.step_results
            execution.step_executions = {
                step_id: {
                    "status": status.value,
                    "result": context.step_results.get(step_id)
                } for step_id, status in context.step_statuses.items()
            }
            
            # Update workflow statistics
            workflow.execution_count += 1
            if execution.status == WorkflowStatus.COMPLETED:
                workflow.success_count += 1
            
            # Calculate average execution time
            if workflow.execution_count > 0:
                total_time = workflow.average_execution_time * (workflow.execution_count - 1)
                total_time += execution.execution_time
                workflow.average_execution_time = total_time / workflow.execution_count
            
            workflow.last_executed = execution.end_time
            self.workflow_engine.save_workflow(workflow)
            
            # Save final execution state
            self._save_execution(execution)
            
            # Notify callbacks
            self._notify_callbacks(execution.id, execution)
            
            # Clean up
            if execution.id in self._active_executions:
                del self._active_executions[execution.id]
            
            self.logger.info(f"Completed workflow execution: {execution.id} ({execution.status.value})")
            
        except Exception as e:
            self.logger.error(f"Workflow execution failed: {e}")
            
            # Update execution with error
            execution.status = WorkflowStatus.FAILED
            execution.error_message = str(e)
            execution.end_time = datetime.now()
            if execution.start_time:
                execution.execution_time = (execution.end_time - execution.start_time).total_seconds()
            
            self._save_execution(execution)
            self._notify_callbacks(execution.id, execution)
            
            # Clean up
            if execution.id in self._active_executions:
                del self._active_executions[execution.id]
    
    def _execute_sequential(self, context: WorkflowContext):
        """Execute workflow steps sequentially."""
        workflow = context.workflow
        
        # Build execution order based on connections
        execution_order = self._build_execution_order(workflow)
        
        for step_id in execution_order:
            if context.cancelled:
                break
            
            step = self._get_step_by_id(workflow, step_id)
            if not step or not step.enabled:
                continue
            
            # Check step conditions
            if not self._evaluate_step_conditions(step, context):
                if step.optional:
                    context.step_statuses[step_id] = StepStatus.SKIPPED
                    continue
                else:
                    context.step_statuses[step_id] = StepStatus.FAILED
                    context.failed_steps.add(step_id)
                    if workflow.error_handling == "stop":
                        break
                    continue
            
            # Execute step
            success = self._execute_step(step, context)
            
            if not success:
                context.failed_steps.add(step_id)
                if workflow.error_handling == "stop":
                    break
            else:
                context.completed_steps.add(step_id)
    
    def _execute_parallel(self, context: WorkflowContext):
        """Execute workflow steps in parallel where possible."""
        workflow = context.workflow
        
        # Group steps by parallel groups and dependencies
        parallel_groups = self._build_parallel_groups(workflow)
        
        for group in parallel_groups:
            if context.cancelled:
                break
            
            # Execute steps in group concurrently
            futures = {}
            
            for step_id in group:
                step = self._get_step_by_id(workflow, step_id)
                if not step or not step.enabled:
                    continue
                
                # Check step conditions
                if not self._evaluate_step_conditions(step, context):
                    if step.optional:
                        context.step_statuses[step_id] = StepStatus.SKIPPED
                        continue
                    else:
                        context.step_statuses[step_id] = StepStatus.FAILED
                        context.failed_steps.add(step_id)
                        continue
                
                # Submit step for execution
                future = self._executor.submit(self._execute_step, step, context)
                futures[step_id] = future
                context.running_steps[step_id] = future
            
            # Wait for all steps in group to complete
            for step_id, future in futures.items():
                try:
                    success = future.result(timeout=workflow.max_execution_time)
                    if success:
                        context.completed_steps.add(step_id)
                    else:
                        context.failed_steps.add(step_id)
                        if workflow.error_handling == "stop":
                            context.cancelled = True
                            break
                except Exception as e:
                    self.logger.error(f"Step {step_id} execution failed: {e}")
                    context.failed_steps.add(step_id)
                    context.step_statuses[step_id] = StepStatus.FAILED
                finally:
                    if step_id in context.running_steps:
                        del context.running_steps[step_id]
            
            # Stop if error handling is set to stop and we have failures
            if workflow.error_handling == "stop" and context.failed_steps:
                break
    
    def _execute_conditional(self, context: WorkflowContext):
        """Execute workflow with conditional branching."""
        workflow = context.workflow
        
        # Start with steps that have no dependencies
        ready_steps = self._get_ready_steps(workflow, context)
        
        while ready_steps and not context.cancelled:
            # Execute ready steps
            for step_id in ready_steps:
                step = self._get_step_by_id(workflow, step_id)
                if not step or not step.enabled:
                    continue
                
                # Check step conditions
                if not self._evaluate_step_conditions(step, context):
                    if step.optional:
                        context.step_statuses[step_id] = StepStatus.SKIPPED
                    else:
                        context.step_statuses[step_id] = StepStatus.FAILED
                        context.failed_steps.add(step_id)
                    continue
                
                # Execute step
                success = self._execute_step(step, context)
                
                if success:
                    context.completed_steps.add(step_id)
                else:
                    context.failed_steps.add(step_id)
                    if workflow.error_handling == "stop":
                        context.cancelled = True
                        break
            
            # Get next ready steps
            ready_steps = self._get_ready_steps(workflow, context)
    
    def _execute_step(self, step: WorkflowStep, context: WorkflowContext) -> bool:
        """Execute a single workflow step."""
        try:
            step_id = step.id
            context.step_statuses[step_id] = StepStatus.RUNNING
            
            self.logger.info(f"Executing step: {step.name} ({step_id})")
            
            # Prepare step parameters
            parameters = self._prepare_step_parameters(step, context)
            
            # Execute tool
            execution = self.tool_executor.execute_tool(
                tool_id=step.tool_id,
                parameters=parameters,
                user_id=context.execution.executed_by,
                timeout=step.timeout,
                workflow_id=context.execution.workflow_id,
                parent_execution_id=context.execution.id
            )
            
            if not execution:
                raise WorkflowExecutionError(f"Failed to start tool execution for step {step_id}")
            
            # Wait for execution to complete with retries
            retry_count = 0
            while retry_count <= step.retry_count:
                # Wait for execution
                result = self._wait_for_tool_execution(execution.id, step.timeout)
                
                if result and result.status == ExecutionStatus.COMPLETED:
                    # Success
                    context.step_statuses[step_id] = StepStatus.COMPLETED
                    context.step_results[step_id] = result.result
                    
                    # Update context variables with step results
                    if result.result:
                        for key, value in result.result.items():
                            context.variables[f"{step_id}.{key}"] = value
                    
                    self.logger.info(f"Step completed successfully: {step.name} ({step_id})")
                    return True
                
                elif result and result.status in [ExecutionStatus.FAILED, ExecutionStatus.TIMEOUT]:
                    # Retry if configured
                    if retry_count < step.retry_count:
                        retry_count += 1
                        self.logger.warning(f"Step failed, retrying ({retry_count}/{step.retry_count}): {step.name}")
                        time.sleep(step.retry_delay)
                        
                        # Start new execution for retry
                        execution = self.tool_executor.execute_tool(
                            tool_id=step.tool_id,
                            parameters=parameters,
                            user_id=context.execution.executed_by,
                            timeout=step.timeout,
                            workflow_id=context.execution.workflow_id,
                            parent_execution_id=context.execution.id
                        )
                        
                        if not execution:
                            break
                    else:
                        # Max retries reached
                        context.step_statuses[step_id] = StepStatus.FAILED
                        if result:
                            context.step_results[step_id] = {"error": result.error_message}
                        
                        self.logger.error(f"Step failed after {retry_count} retries: {step.name} ({step_id})")
                        return False
                else:
                    # Unexpected status
                    context.step_statuses[step_id] = StepStatus.FAILED
                    context.step_results[step_id] = {"error": "Unexpected execution status"}
                    
                    self.logger.error(f"Step execution failed with unexpected status: {step.name} ({step_id})")
                    return False
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error executing step {step.name} ({step.id}): {e}")
            context.step_statuses[step.id] = StepStatus.FAILED
            context.step_results[step.id] = {"error": str(e)}
            return False
    
    def _prepare_step_parameters(self, step: WorkflowStep, context: WorkflowContext) -> Dict[str, Any]:
        """Prepare parameters for step execution."""
        parameters = step.parameters.copy()
        
        # Apply parameter mappings
        for mapping in step.parameter_mappings:
            source_value = None
            
            # Get source value
            if mapping.source_step_id in context.step_results:
                step_result = context.step_results[mapping.source_step_id]
                if isinstance(step_result, dict) and mapping.source_parameter in step_result:
                    source_value = step_result[mapping.source_parameter]
            
            # Use default if source not available
            if source_value is None and mapping.default_value is not None:
                source_value = mapping.default_value
            
            # Apply transformation if specified
            if source_value is not None and mapping.transformation:
                try:
                    # Simple transformation support (could be extended with JS engine)
                    if mapping.transformation == "uppercase":
                        source_value = str(source_value).upper()
                    elif mapping.transformation == "lowercase":
                        source_value = str(source_value).lower()
                    elif mapping.transformation.startswith("format:"):
                        format_str = mapping.transformation[7:]
                        source_value = format_str.format(source_value)
                except Exception as e:
                    self.logger.warning(f"Parameter transformation failed: {e}")
            
            # Set parameter value
            if source_value is not None:
                parameters[mapping.target_parameter] = source_value
        
        # Substitute variables in parameters
        for key, value in parameters.items():
            if isinstance(value, str):
                # Simple variable substitution
                for var_name, var_value in context.variables.items():
                    placeholder = f"${{{var_name}}}"
                    if placeholder in value:
                        parameters[key] = value.replace(placeholder, str(var_value))
        
        return parameters
    
    def _evaluate_step_conditions(self, step: WorkflowStep, context: WorkflowContext) -> bool:
        """Evaluate step conditions."""
        if not step.conditions:
            return True
        
        results = []
        
        for condition in step.conditions:
            # Get operand values
            left_value = self._resolve_operand(condition.left_operand, context)
            right_value = self._resolve_operand(condition.right_operand, context)
            
            # Evaluate condition
            result = self._evaluate_condition(left_value, condition.operator, right_value)
            results.append(result)
        
        # Apply logic (AND/OR)
        if step.condition_logic == "OR":
            return any(results)
        else:  # Default to AND
            return all(results)
    
    def _resolve_operand(self, operand: str, context: WorkflowContext) -> Any:
        """Resolve operand value from context or literal."""
        # Check if it's a variable reference
        if operand.startswith("${") and operand.endswith("}"):
            var_name = operand[2:-1]
            return context.variables.get(var_name)
        
        # Check if it's a step result reference
        if "." in operand:
            parts = operand.split(".", 1)
            step_id, field = parts
            if step_id in context.step_results:
                step_result = context.step_results[step_id]
                if isinstance(step_result, dict):
                    return step_result.get(field)
        
        # Try to parse as number
        try:
            if "." in operand:
                return float(operand)
            else:
                return int(operand)
        except ValueError:
            pass
        
        # Try to parse as boolean
        if operand.lower() in ["true", "false"]:
            return operand.lower() == "true"
        
        # Return as string
        return operand
    
    def _evaluate_condition(self, left: Any, operator: ConditionOperator, right: Any) -> bool:
        """Evaluate a single condition."""
        try:
            if operator == ConditionOperator.EQUALS:
                return left == right
            elif operator == ConditionOperator.NOT_EQUALS:
                return left != right
            elif operator == ConditionOperator.GREATER_THAN:
                return float(left) > float(right)
            elif operator == ConditionOperator.LESS_THAN:
                return float(left) < float(right)
            elif operator == ConditionOperator.CONTAINS:
                return str(right) in str(left)
            elif operator == ConditionOperator.REGEX_MATCH:
                import re
                return bool(re.search(str(right), str(left)))
            elif operator == ConditionOperator.IS_EMPTY:
                return not left or (isinstance(left, (list, dict, str)) and len(left) == 0)
            elif operator == ConditionOperator.IS_NOT_EMPTY:
                return bool(left) and (not isinstance(left, (list, dict, str)) or len(left) > 0)
            else:
                return False
        except Exception as e:
            self.logger.warning(f"Condition evaluation failed: {e}")
            return False
    
    def _wait_for_tool_execution(self, execution_id: str, timeout: int) -> Optional[ToolExecution]:
        """Wait for tool execution to complete."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            execution = self.tool_executor.get_execution(execution_id)
            if execution and execution.status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, 
                                                 ExecutionStatus.CANCELLED, ExecutionStatus.TIMEOUT]:
                return execution
            
            time.sleep(1)  # Poll every second
        
        # Timeout reached
        self.tool_executor.cancel_execution(execution_id)
        return None
    
    def _build_execution_order(self, workflow: WorkflowDefinition) -> List[str]:
        """Build execution order for sequential execution."""
        # Simple topological sort based on connections
        in_degree = {step.id: 0 for step in workflow.steps}
        graph = {step.id: [] for step in workflow.steps}
        
        # Build graph
        for connection in workflow.connections:
            if connection.connection_type in [ConnectionType.DATA, ConnectionType.CONTROL]:
                graph[connection.source_step_id].append(connection.target_step_id)
                in_degree[connection.target_step_id] += 1
        
        # Topological sort
        queue = [step_id for step_id, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            step_id = queue.pop(0)
            result.append(step_id)
            
            for neighbor in graph[step_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        return result
    
    def _build_parallel_groups(self, workflow: WorkflowDefinition) -> List[List[str]]:
        """Build parallel execution groups."""
        # For now, use simple grouping by parallel_group attribute
        groups = {}
        ungrouped = []
        
        for step in workflow.steps:
            if step.parallel_group:
                if step.parallel_group not in groups:
                    groups[step.parallel_group] = []
                groups[step.parallel_group].append(step.id)
            else:
                ungrouped.append(step.id)
        
        # Return groups as list
        result = list(groups.values())
        if ungrouped:
            result.append(ungrouped)
        
        return result
    
    def _get_ready_steps(self, workflow: WorkflowDefinition, context: WorkflowContext) -> List[str]:
        """Get steps that are ready to execute."""
        ready = []
        
        for step in workflow.steps:
            if (step.id not in context.completed_steps and 
                step.id not in context.failed_steps and
                context.step_statuses[step.id] == StepStatus.PENDING):
                
                # Check if all dependencies are satisfied
                dependencies_met = True
                for connection in workflow.connections:
                    if (connection.target_step_id == step.id and 
                        connection.connection_type in [ConnectionType.DATA, ConnectionType.CONTROL]):
                        if connection.source_step_id not in context.completed_steps:
                            dependencies_met = False
                            break
                
                if dependencies_met:
                    ready.append(step.id)
        
        return ready
    
    def _get_step_by_id(self, workflow: WorkflowDefinition, step_id: str) -> Optional[WorkflowStep]:
        """Get step by ID."""
        for step in workflow.steps:
            if step.id == step_id:
                return step
        return None
    
    def _save_execution(self, execution: WorkflowExecution):
        """Save workflow execution to database."""
        try:
            with self.db_manager.get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO workflow_executions (
                        id, workflow_id, workflow_version, status, input_parameters,
                        variables, result, error_message, start_time, end_time,
                        execution_time, executed_by, trigger_type, parent_execution_id,
                        step_executions
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    execution.id,
                    execution.workflow_id,
                    execution.workflow_version,
                    execution.status.value,
                    json.dumps(execution.input_parameters),
                    json.dumps(execution.variables),
                    json.dumps(execution.result) if execution.result else None,
                    execution.error_message,
                    execution.start_time,
                    execution.end_time,
                    execution.execution_time,
                    execution.executed_by,
                    execution.trigger_type,
                    execution.parent_execution_id,
                    json.dumps(execution.step_executions)
                ))
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to save workflow execution {execution.id}: {e}")
    
    def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get workflow execution by ID."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM workflow_executions WHERE id = ?
                """, (execution_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                execution = WorkflowExecution(
                    id=row['id'],
                    workflow_id=row['workflow_id'],
                    workflow_version=row['workflow_version'],
                    status=WorkflowStatus(row['status']),
                    input_parameters=json.loads(row['input_parameters']) if row['input_parameters'] else {},
                    variables=json.loads(row['variables']) if row['variables'] else {},
                    result=json.loads(row['result']) if row['result'] else None,
                    error_message=row['error_message'],
                    start_time=datetime.fromisoformat(row['start_time']),
                    end_time=datetime.fromisoformat(row['end_time']) if row['end_time'] else None,
                    execution_time=row['execution_time'],
                    executed_by=row['executed_by'],
                    trigger_type=row['trigger_type'],
                    parent_execution_id=row['parent_execution_id'],
                    step_executions=json.loads(row['step_executions']) if row['step_executions'] else {}
                )
                
                return execution
                
        except Exception as e:
            self.logger.error(f"Failed to get workflow execution {execution_id}: {e}")
            return None
    
    def cancel_execution(self, execution_id: str) -> bool:
        """Cancel workflow execution."""
        try:
            if execution_id in self._active_executions:
                context = self._active_executions[execution_id]
                context.cancelled = True
                
                # Cancel running steps
                for step_id, future in context.running_steps.items():
                    future.cancel()
                
                # Update execution status
                context.execution.status = WorkflowStatus.CANCELLED
                context.execution.end_time = datetime.now()
                if context.execution.start_time:
                    context.execution.execution_time = (
                        context.execution.end_time - context.execution.start_time
                    ).total_seconds()
                
                self._save_execution(context.execution)
                
                self.logger.info(f"Cancelled workflow execution: {execution_id}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to cancel workflow execution {execution_id}: {e}")
            return False
    
    def add_execution_callback(self, execution_id: str, callback: Callable):
        """Add callback for execution completion."""
        if execution_id not in self._execution_callbacks:
            self._execution_callbacks[execution_id] = []
        self._execution_callbacks[execution_id].append(callback)
    
    def _notify_callbacks(self, execution_id: str, execution: WorkflowExecution):
        """Notify execution callbacks."""
        if execution_id in self._execution_callbacks:
            for callback in self._execution_callbacks[execution_id]:
                try:
                    callback(execution)
                except Exception as e:
                    self.logger.error(f"Execution callback failed: {e}")
            
            # Clean up callbacks
            del self._execution_callbacks[execution_id]
    
    def get_active_executions(self) -> List[WorkflowExecution]:
        """Get all active workflow executions."""
        return [context.execution for context in self._active_executions.values()]
    
    def get_execution_statistics(self) -> Dict[str, Any]:
        """Get workflow execution statistics."""
        try:
            with self.db_manager.get_connection() as conn:
                # Total executions
                cursor = conn.execute("SELECT COUNT(*) FROM workflow_executions")
                total_executions = cursor.fetchone()[0]
                
                # Executions by status
                cursor = conn.execute("""
                    SELECT status, COUNT(*) FROM workflow_executions 
                    GROUP BY status
                """)
                status_counts = dict(cursor.fetchall())
                
                # Average execution time
                cursor = conn.execute("""
                    SELECT AVG(execution_time) FROM workflow_executions 
                    WHERE execution_time IS NOT NULL
                """)
                avg_execution_time = cursor.fetchone()[0] or 0.0
                
                # Recent executions
                cursor = conn.execute("""
                    SELECT id, workflow_id, status, start_time 
                    FROM workflow_executions 
                    ORDER BY start_time DESC 
                    LIMIT 10
                """)
                recent_executions = [
                    {
                        "id": row[0],
                        "workflow_id": row[1],
                        "status": row[2],
                        "start_time": row[3]
                    } for row in cursor.fetchall()
                ]
                
                return {
                    "total_executions": total_executions,
                    "active_executions": len(self._active_executions),
                    "status_counts": status_counts,
                    "average_execution_time": avg_execution_time,
                    "recent_executions": recent_executions
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get execution statistics: {e}")
            return {}