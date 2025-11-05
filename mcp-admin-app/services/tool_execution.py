"""
Tool Execution Engine
====================

Secure and monitored execution of MCP tools with sandboxing, performance tracking,
and result management.
"""

import logging
import json
import time
import threading
import subprocess
import tempfile
import os
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

from models.tool import (
    ToolExecution, ExecutionStatus, ResourceUsage, ToolRegistryEntry,
    ToolParameter, ValidationRule
)
from models.base import generate_id


logger = logging.getLogger(__name__)


class SandboxType(Enum):
    """Sandbox isolation type."""
    NONE = "none"
    PROCESS = "process"
    CONTAINER = "container"  # Future implementation
    VM = "vm"  # Future implementation


@dataclass
class ExecutionRequest:
    """Tool execution request."""
    tool_id: str
    user_id: str
    parameters: Dict[str, Any]
    timeout: int = 30
    sandbox_type: SandboxType = SandboxType.PROCESS
    resource_limits: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.resource_limits is None:
            self.resource_limits = {
                "max_memory_mb": 512,
                "max_cpu_percent": 50,
                "max_execution_time": 30,
                "max_network_requests": 10
            }


@dataclass
class BatchExecutionRequest:
    """Batch tool execution request."""
    requests: List[ExecutionRequest]
    user_id: str
    parallel: bool = True
    max_concurrent: int = 5
    stop_on_error: bool = False
    timeout: int = 300  # 5 minutes total timeout
    context: Optional[Dict[str, Any]] = None


@dataclass
class BatchExecutionResult:
    """Batch execution result."""
    batch_id: str
    total_requests: int
    completed: int
    failed: int
    cancelled: int
    results: List['ExecutionResult']
    start_time: datetime
    end_time: Optional[datetime] = None
    total_time: float = 0.0
    errors: List[str] = field(default_factory=list)


@dataclass
class ExecutionResult:
    """Tool execution result."""
    execution_id: str
    success: bool
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_time: float = 0.0
    resource_usage: ResourceUsage = field(default_factory=ResourceUsage)
    logs: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SandboxConfig:
    """Sandbox configuration."""
    id: str
    type: SandboxType
    resource_limits: Dict[str, Any]
    working_directory: str
    environment_vars: Dict[str, str] = field(default_factory=dict)
    allowed_network: bool = True
    allowed_file_access: List[str] = field(default_factory=list)
    security_policies: List[str] = field(default_factory=list)


class ParameterValidator:
    """Validates tool parameters against schema."""
    
    @staticmethod
    def validate_parameter(param: ToolParameter, value: Any) -> tuple[bool, str]:
        """Validate a single parameter value."""
        try:
            # Check required parameters
            if param.required and (value is None or value == ""):
                return False, f"Parameter '{param.name}' is required"
            
            # Skip validation if value is None and parameter is optional
            if value is None and not param.required:
                return True, ""
            
            # Type validation
            if param.type == "str" and not isinstance(value, str):
                return False, f"Parameter '{param.name}' must be a string"
            elif param.type == "int":
                try:
                    int(value)
                except (ValueError, TypeError):
                    return False, f"Parameter '{param.name}' must be an integer"
            elif param.type == "float":
                try:
                    float(value)
                except (ValueError, TypeError):
                    return False, f"Parameter '{param.name}' must be a number"
            elif param.type == "bool" and not isinstance(value, bool):
                return False, f"Parameter '{param.name}' must be a boolean"
            elif param.type == "list" and not isinstance(value, list):
                return False, f"Parameter '{param.name}' must be a list"
            elif param.type == "dict" and not isinstance(value, dict):
                return False, f"Parameter '{param.name}' must be a dictionary"
            
            # Validation rules
            for rule in param.validation_rules:
                valid, error = ParameterValidator._validate_rule(param.name, value, rule)
                if not valid:
                    return False, error
            
            return True, ""
            
        except Exception as e:
            return False, f"Validation error for parameter '{param.name}': {e}"
    
    @staticmethod
    def _validate_rule(param_name: str, value: Any, rule: ValidationRule) -> tuple[bool, str]:
        """Validate a specific validation rule."""
        try:
            if rule.rule_type == "enum":
                if value not in rule.value:
                    return False, rule.error_message or f"Value must be one of: {rule.value}"
            
            elif rule.rule_type == "range":
                if isinstance(rule.value, dict):
                    min_val = rule.value.get("min")
                    max_val = rule.value.get("max")
                    
                    if min_val is not None and value < min_val:
                        return False, rule.error_message or f"Value must be >= {min_val}"
                    if max_val is not None and value > max_val:
                        return False, rule.error_message or f"Value must be <= {max_val}"
            
            elif rule.rule_type == "regex":
                import re
                if not re.match(rule.value, str(value)):
                    return False, rule.error_message or f"Value does not match required pattern"
            
            elif rule.rule_type == "length":
                if isinstance(rule.value, dict):
                    min_len = rule.value.get("min", 0)
                    max_len = rule.value.get("max", float('inf'))
                    
                    if len(str(value)) < min_len:
                        return False, rule.error_message or f"Length must be >= {min_len}"
                    if len(str(value)) > max_len:
                        return False, rule.error_message or f"Length must be <= {max_len}"
            
            return True, ""
            
        except Exception as e:
            return False, f"Rule validation error: {e}"


class ProcessSandbox:
    """Process-based sandbox for tool execution."""
    
    def __init__(self, config: SandboxConfig):
        self.config = config
        self.process = None
        self.start_time = None
        self.resource_monitor = None
        self.monitoring_thread = None
        self.resource_usage = ResourceUsage()
        
    def create(self) -> bool:
        """Create the sandbox environment."""
        try:
            # Create working directory
            os.makedirs(self.config.working_directory, exist_ok=True)
            
            # Set up environment
            self.env = os.environ.copy()
            self.env.update(self.config.environment_vars)
            
            # Add security restrictions
            self.env["PYTHONPATH"] = ""  # Clear Python path for security
            self.env["PATH"] = "/usr/bin:/bin"  # Restrict PATH
            
            logger.info(f"Created sandbox {self.config.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create sandbox {self.config.id}: {e}")
            return False
    
    def execute(self, command: List[str], input_data: Optional[str] = None) -> ExecutionResult:
        """Execute a command in the sandbox."""
        execution_id = generate_id()
        result = ExecutionResult(execution_id=execution_id, success=False)
        
        try:
            self.start_time = time.time()
            
            # Start resource monitoring
            self._start_resource_monitoring()
            
            # Execute the command
            popen_kwargs = {
                "cwd": self.config.working_directory,
                "env": self.env,
                "stdin": subprocess.PIPE,
                "stdout": subprocess.PIPE,
                "stderr": subprocess.PIPE,
                "text": True
            }
            
            # Add preexec_fn only on Unix systems
            if os.name != 'nt':  # Not Windows
                popen_kwargs["preexec_fn"] = self._setup_process_limits
            
            self.process = subprocess.Popen(command, **popen_kwargs)
            
            # Communicate with process
            stdout, stderr = self.process.communicate(
                input=input_data,
                timeout=self.config.resource_limits.get("max_execution_time", 30)
            )
            
            # Calculate execution time
            result.execution_time = time.time() - self.start_time
            
            # Stop monitoring
            self._stop_resource_monitoring()
            
            # Process results
            if self.process.returncode == 0:
                result.success = True
                try:
                    # Try to parse JSON output
                    result.result = json.loads(stdout) if stdout.strip() else {}
                except json.JSONDecodeError:
                    # If not JSON, return as text
                    result.result = {"output": stdout, "type": "text"}
            else:
                result.error_message = stderr or f"Process exited with code {self.process.returncode}"
            
            result.resource_usage = self.resource_usage
            result.logs = [stdout, stderr] if stderr else [stdout]
            
            logger.info(f"Executed command in sandbox {self.config.id}: success={result.success}")
            
        except subprocess.TimeoutExpired:
            result.error_message = "Execution timeout"
            self._terminate_process()
        except Exception as e:
            result.error_message = f"Execution error: {e}"
            logger.error(f"Sandbox execution error: {e}")
        finally:
            self._cleanup()
        
        return result
    
    def _setup_process_limits(self):
        """Set up process resource limits (Unix only)."""
        try:
            import resource
            
            # Set memory limit
            max_memory = self.config.resource_limits.get("max_memory_mb", 512) * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (max_memory, max_memory))
            
            # Set CPU time limit
            max_cpu_time = self.config.resource_limits.get("max_execution_time", 30)
            resource.setrlimit(resource.RLIMIT_CPU, (max_cpu_time, max_cpu_time))
            
        except (ImportError, AttributeError):
            # Windows doesn't support resource module
            pass
    
    def _start_resource_monitoring(self):
        """Start monitoring resource usage."""
        self.monitoring_thread = threading.Thread(target=self._monitor_resources)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
    
    def _monitor_resources(self):
        """Monitor process resource usage."""
        try:
            if not HAS_PSUTIL:
                # Basic monitoring without psutil
                while self.process and self.process.poll() is None:
                    time.sleep(0.1)
                return
            
            while self.process and self.process.poll() is None:
                if self.process.pid:
                    try:
                        proc = psutil.Process(self.process.pid)
                        
                        # Get memory usage
                        memory_info = proc.memory_info()
                        self.resource_usage.memory_mb = memory_info.rss / 1024 / 1024
                        
                        # Get CPU usage
                        cpu_percent = proc.cpu_percent()
                        
                        # Check limits
                        max_memory = self.config.resource_limits.get("max_memory_mb", 512)
                        max_cpu = self.config.resource_limits.get("max_cpu_percent", 50)
                        
                        if self.resource_usage.memory_mb > max_memory:
                            logger.warning(f"Memory limit exceeded: {self.resource_usage.memory_mb}MB > {max_memory}MB")
                            self._terminate_process()
                            break
                        
                        if cpu_percent > max_cpu:
                            logger.warning(f"CPU limit exceeded: {cpu_percent}% > {max_cpu}%")
                    
                    except psutil.NoSuchProcess:
                        break
                
                time.sleep(0.1)  # Monitor every 100ms
                
        except Exception as e:
            logger.error(f"Resource monitoring error: {e}")
    
    def _stop_resource_monitoring(self):
        """Stop resource monitoring."""
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            # Thread will stop when process ends
            pass
    
    def _terminate_process(self):
        """Terminate the running process."""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            except Exception as e:
                logger.error(f"Error terminating process: {e}")
    
    def _cleanup(self):
        """Clean up sandbox resources."""
        try:
            # Terminate process if still running
            if self.process and self.process.poll() is None:
                self._terminate_process()
            
            # Clean up temporary files (optional)
            # Could implement cleanup of working directory here
            
        except Exception as e:
            logger.error(f"Sandbox cleanup error: {e}")
    
    def destroy(self):
        """Destroy the sandbox."""
        self._cleanup()
        logger.info(f"Destroyed sandbox {self.config.id}")


class ToolExecutionEngine:
    """Main tool execution engine with sandboxing and monitoring."""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.active_executions = {}
        self.execution_history = []
        self._ensure_tables()
    
    def _ensure_tables(self):
        """Ensure execution-related database tables exist."""
        try:
            with self.db_manager.get_connection() as conn:
                # Tool executions table (already exists from tool_manager)
                # Add sandbox configurations table
                conn.execute("""
                CREATE TABLE IF NOT EXISTS sandbox_configs (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    resource_limits TEXT NOT NULL,
                    working_directory TEXT NOT NULL,
                    environment_vars TEXT,
                    security_policies TEXT,
                    created_at TEXT NOT NULL,
                    last_used TEXT
                )
                """)
                
                conn.commit()
                
            logger.info("Tool execution tables initialized")
            
        except Exception as e:
            logger.error(f"Error creating execution tables: {e}")
    
    def validate_parameters(self, tool: ToolRegistryEntry, parameters: Dict[str, Any]) -> tuple[bool, str]:
        """Validate execution parameters against tool schema."""
        try:
            # Check for required parameters
            for param in tool.parameters:
                if param.required and param.name not in parameters:
                    return False, f"Required parameter '{param.name}' is missing"
            
            # Validate each provided parameter
            for param_name, param_value in parameters.items():
                # Find parameter definition
                param_def = None
                for param in tool.parameters:
                    if param.name == param_name:
                        param_def = param
                        break
                
                if param_def is None:
                    return False, f"Unknown parameter '{param_name}'"
                
                # Validate parameter
                valid, error = ParameterValidator.validate_parameter(param_def, param_value)
                if not valid:
                    return False, error
            
            return True, ""
            
        except Exception as e:
            return False, f"Parameter validation error: {e}"
    
    def execute_tool(self, request: ExecutionRequest, tool: ToolRegistryEntry) -> ExecutionResult:
        """Execute a tool with the given parameters."""
        execution_id = generate_id()
        
        try:
            logger.info(f"Starting tool execution {execution_id} for tool {tool.name}")
            
            # Validate parameters
            valid, error = self.validate_parameters(tool, request.parameters)
            if not valid:
                return ExecutionResult(
                    execution_id=execution_id,
                    success=False,
                    error_message=f"Parameter validation failed: {error}"
                )
            
            # Create execution record
            execution = ToolExecution(
                id=execution_id,
                tool_id=request.tool_id,
                user_id=request.user_id,
                parameters=request.parameters,
                status=ExecutionStatus.RUNNING
            )
            
            self.active_executions[execution_id] = execution
            self._save_execution(execution)
            
            # Create sandbox
            sandbox_config = self._create_sandbox_config(request)
            sandbox = ProcessSandbox(sandbox_config)
            
            if not sandbox.create():
                return ExecutionResult(
                    execution_id=execution_id,
                    success=False,
                    error_message="Failed to create sandbox"
                )
            
            # Execute tool
            result = self._execute_tool_in_sandbox(tool, request.parameters, sandbox)
            
            # Update execution record
            execution.status = ExecutionStatus.COMPLETED if result.success else ExecutionStatus.FAILED
            execution.end_time = datetime.now()
            execution.execution_time = result.execution_time
            execution.result = result.result
            execution.error_message = result.error_message
            execution.resource_usage = result.resource_usage
            execution.sandbox_id = sandbox_config.id
            
            self._save_execution(execution)
            
            # Clean up
            sandbox.destroy()
            if execution_id in self.active_executions:
                del self.active_executions[execution_id]
            
            logger.info(f"Completed tool execution {execution_id}: success={result.success}")
            return result
            
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            
            # Update execution record with error
            if execution_id in self.active_executions:
                execution = self.active_executions[execution_id]
                execution.status = ExecutionStatus.FAILED
                execution.error_message = str(e)
                execution.end_time = datetime.now()
                self._save_execution(execution)
                del self.active_executions[execution_id]
            
            return ExecutionResult(
                execution_id=execution_id,
                success=False,
                error_message=f"Execution error: {e}"
            )
    
    def _create_sandbox_config(self, request: ExecutionRequest) -> SandboxConfig:
        """Create sandbox configuration for execution."""
        sandbox_id = generate_id()
        
        # Create temporary working directory
        temp_dir = tempfile.mkdtemp(prefix=f"mcp_sandbox_{sandbox_id}_")
        
        config = SandboxConfig(
            id=sandbox_id,
            type=request.sandbox_type,
            resource_limits=request.resource_limits,
            working_directory=temp_dir,
            environment_vars={
                "MCP_EXECUTION_ID": sandbox_id,
                "MCP_USER_ID": request.user_id,
                "MCP_TOOL_ID": request.tool_id
            }
        )
        
        return config
    
    def _execute_tool_in_sandbox(self, tool: ToolRegistryEntry, parameters: Dict[str, Any], 
                                sandbox: ProcessSandbox) -> ExecutionResult:
        """Execute the actual tool in the sandbox."""
        try:
            # For now, simulate tool execution
            # In a real implementation, this would:
            # 1. Generate the appropriate command based on tool schema
            # 2. Prepare input data
            # 3. Execute via sandbox
            
            # Simulate execution based on tool category
            if "file" in tool.name.lower():
                # Simulate file operation
                command = ["python", "-c", f"import json; print(json.dumps({{'result': 'File operation completed', 'parameters': {json.dumps(parameters)}}}))"]
            elif "web" in tool.name.lower():
                # Simulate web request
                command = ["python", "-c", f"import json; print(json.dumps({{'result': 'Web request completed', 'data': 'Sample data', 'parameters': {json.dumps(parameters)}}}))"]
            elif "code" in tool.name.lower():
                # Simulate code analysis
                command = ["python", "-c", f"import json; print(json.dumps({{'result': 'Code analysis completed', 'issues': [], 'parameters': {json.dumps(parameters)}}}))"]
            else:
                # Generic tool execution
                command = ["python", "-c", f"import json; print(json.dumps({{'result': 'Tool execution completed', 'parameters': {json.dumps(parameters)}}}))"]
            
            # Execute in sandbox
            result = sandbox.execute(command)
            
            return result
            
        except Exception as e:
            return ExecutionResult(
                execution_id=generate_id(),
                success=False,
                error_message=f"Tool execution error: {e}"
            )
    
    def get_execution_status(self, execution_id: str) -> Optional[ExecutionStatus]:
        """Get the status of an execution."""
        if execution_id in self.active_executions:
            return self.active_executions[execution_id].status
        
        # Check database for completed executions
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT status FROM tool_executions WHERE id = ?",
                    (execution_id,)
                )
                row = cursor.fetchone()
                if row:
                    return ExecutionStatus(row[0])
        except Exception as e:
            logger.error(f"Error getting execution status: {e}")
        
        return None
    
    def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a running execution."""
        try:
            if execution_id in self.active_executions:
                execution = self.active_executions[execution_id]
                execution.status = ExecutionStatus.CANCELLED
                execution.end_time = datetime.now()
                self._save_execution(execution)
                
                # TODO: Terminate sandbox process
                
                del self.active_executions[execution_id]
                logger.info(f"Cancelled execution {execution_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error cancelling execution: {e}")
            return False
    
    def get_execution_history(self, filters: Optional[Dict[str, Any]] = None) -> List[ToolExecution]:
        """Get execution history with optional filtering."""
        try:
            query = "SELECT * FROM tool_executions"
            params = []
            
            if filters:
                conditions = []
                if "tool_id" in filters:
                    conditions.append("tool_id = ?")
                    params.append(filters["tool_id"])
                if "user_id" in filters:
                    conditions.append("user_id = ?")
                    params.append(filters["user_id"])
                if "status" in filters:
                    conditions.append("status = ?")
                    params.append(filters["status"])
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY start_time DESC LIMIT 100"
            
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()
            
            executions = []
            for row in rows:
                execution = self._row_to_execution(row)
                executions.append(execution)
            
            return executions
            
        except Exception as e:
            logger.error(f"Error getting execution history: {e}")
            return []
    
    def _save_execution(self, execution: ToolExecution):
        """Save execution to database."""
        try:
            query = """
                INSERT OR REPLACE INTO tool_executions (
                    id, tool_id, user_id, parameters, result, status,
                    start_time, end_time, execution_time, error_message,
                    resource_usage, sandbox_id, workflow_id, parent_execution_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                execution.id,
                execution.tool_id,
                execution.user_id,
                json.dumps(execution.parameters),
                json.dumps(execution.result) if execution.result else None,
                execution.status.value,
                execution.start_time.isoformat(),
                execution.end_time.isoformat() if execution.end_time else None,
                execution.execution_time,
                execution.error_message,
                json.dumps(execution.resource_usage.__dict__),
                execution.sandbox_id,
                execution.workflow_id,
                execution.parent_execution_id
            )
            
            with self.db_manager.get_connection() as conn:
                conn.execute(query, params)
                conn.commit()
            
        except Exception as e:
            logger.error(f"Error saving execution: {e}")
    
    def _row_to_execution(self, row: tuple) -> ToolExecution:
        """Convert database row to ToolExecution object."""
        execution = ToolExecution()
        execution.id = row[0]
        execution.tool_id = row[1]
        execution.user_id = row[2]
        execution.parameters = json.loads(row[3]) if row[3] else {}
        execution.result = json.loads(row[4]) if row[4] else None
        execution.status = ExecutionStatus(row[5])
        execution.start_time = datetime.fromisoformat(row[6])
        execution.end_time = datetime.fromisoformat(row[7]) if row[7] else None
        execution.execution_time = row[8] or 0.0
        execution.error_message = row[9]
        
        if row[10]:
            resource_data = json.loads(row[10])
            execution.resource_usage = ResourceUsage(**resource_data)
        
        execution.sandbox_id = row[11]
        execution.workflow_id = row[12]
        execution.parent_execution_id = row[13]
        
        return execution
    
    def execute_batch(self, batch_request: BatchExecutionRequest, 
                     tools: Dict[str, ToolRegistryEntry]) -> BatchExecutionResult:
        """Execute multiple tools in batch."""
        batch_id = generate_id()
        
        try:
            logger.info(f"Starting batch execution {batch_id} with {len(batch_request.requests)} tools")
            
            batch_result = BatchExecutionResult(
                batch_id=batch_id,
                total_requests=len(batch_request.requests),
                completed=0,
                failed=0,
                cancelled=0,
                results=[],
                start_time=datetime.now()
            )
            
            if batch_request.parallel:
                # Execute in parallel using threads
                batch_result = self._execute_batch_parallel(batch_request, tools, batch_result)
            else:
                # Execute sequentially
                batch_result = self._execute_batch_sequential(batch_request, tools, batch_result)
            
            batch_result.end_time = datetime.now()
            batch_result.total_time = (batch_result.end_time - batch_result.start_time).total_seconds()
            
            logger.info(f"Batch execution {batch_id} completed: {batch_result.completed} success, {batch_result.failed} failed")
            return batch_result
            
        except Exception as e:
            logger.error(f"Batch execution error: {e}")
            batch_result.errors.append(str(e))
            batch_result.end_time = datetime.now()
            return batch_result
    
    def _execute_batch_parallel(self, batch_request: BatchExecutionRequest, 
                               tools: Dict[str, ToolRegistryEntry], 
                               batch_result: BatchExecutionResult) -> BatchExecutionResult:
        """Execute batch requests in parallel."""
        import concurrent.futures
        
        max_workers = min(batch_request.max_concurrent, len(batch_request.requests))
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_request = {}
            for request in batch_request.requests:
                if request.tool_id in tools:
                    tool = tools[request.tool_id]
                    future = executor.submit(self.execute_tool, request, tool)
                    future_to_request[future] = request
                else:
                    # Tool not found
                    error_result = ExecutionResult(
                        execution_id=generate_id(),
                        success=False,
                        error_message=f"Tool {request.tool_id} not found"
                    )
                    batch_result.results.append(error_result)
                    batch_result.failed += 1
            
            # Collect results
            try:
                for future in concurrent.futures.as_completed(future_to_request, timeout=batch_request.timeout):
                    try:
                        result = future.result()
                        batch_result.results.append(result)
                        
                        if result.success:
                            batch_result.completed += 1
                        else:
                            batch_result.failed += 1
                            
                            # Stop on error if requested
                            if batch_request.stop_on_error:
                                # Cancel remaining futures
                                for remaining_future in future_to_request:
                                    if not remaining_future.done():
                                        remaining_future.cancel()
                                        batch_result.cancelled += 1
                                break
                    
                    except Exception as e:
                        batch_result.failed += 1
                        batch_result.errors.append(f"Execution error: {e}")
                        
                        if batch_request.stop_on_error:
                            break
            
            except concurrent.futures.TimeoutError:
                batch_result.errors.append("Batch execution timeout")
                # Cancel remaining futures
                for future in future_to_request:
                    if not future.done():
                        future.cancel()
                        batch_result.cancelled += 1
        
        return batch_result
    
    def _execute_batch_sequential(self, batch_request: BatchExecutionRequest, 
                                 tools: Dict[str, ToolRegistryEntry], 
                                 batch_result: BatchExecutionResult) -> BatchExecutionResult:
        """Execute batch requests sequentially."""
        for request in batch_request.requests:
            try:
                if request.tool_id in tools:
                    tool = tools[request.tool_id]
                    result = self.execute_tool(request, tool)
                    batch_result.results.append(result)
                    
                    if result.success:
                        batch_result.completed += 1
                    else:
                        batch_result.failed += 1
                        
                        # Stop on error if requested
                        if batch_request.stop_on_error:
                            break
                else:
                    # Tool not found
                    error_result = ExecutionResult(
                        execution_id=generate_id(),
                        success=False,
                        error_message=f"Tool {request.tool_id} not found"
                    )
                    batch_result.results.append(error_result)
                    batch_result.failed += 1
                    
                    if batch_request.stop_on_error:
                        break
            
            except Exception as e:
                batch_result.failed += 1
                batch_result.errors.append(f"Execution error: {e}")
                
                if batch_request.stop_on_error:
                    break
        
        return batch_result
    
    def get_batch_progress(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """Get progress of a batch execution (placeholder for future implementation)."""
        # In a full implementation, this would track active batch executions
        # For now, return None as batches complete synchronously
        return None
    
    def cancel_batch(self, batch_id: str) -> bool:
        """Cancel a batch execution (placeholder for future implementation)."""
        # In a full implementation, this would cancel active batch executions
        logger.info(f"Batch cancellation requested for {batch_id}")
        return False