"""
UI Service Bridge Layer
=======================

Bridge layer connecting UI components with backend services, providing error handling,
progress indicators, and user-friendly error messages.
"""

import logging
import asyncio
import threading
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

# Import all services
from services.prompt.templating_engine import TemplatingEngine
from services.prompt.version_control import VersionControlService
from services.security.security_scanner import SecurityScanner
from services.collaboration.workspace_management import WorkspaceManagementService
from services.collaboration.approval_workflow import ApprovalWorkflowService
from services.analytics.performance_analytics import PerformanceAnalytics
from services.evaluation.multi_model_testing import MultiModelTestingInfrastructure
from services.evaluation.human_rating import HumanRatingService


class OperationStatus(Enum):
    """Status of an operation."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class OperationResult:
    """Result of a service operation."""
    operation_id: str
    status: OperationStatus
    data: Any = None
    error: Optional[str] = None
    progress: float = 0.0
    message: str = ""
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class UIServiceBridge:
    """Bridge layer connecting UI components with backend services."""
    
    def __init__(self, config_manager, db_manager):
        self.logger = logging.getLogger(__name__)
        self.config_manager = config_manager
        self.db_manager = db_manager
        
        # Initialize services
        self.services = {}
        self._initialize_services()
        
        # Operation tracking
        self.active_operations: Dict[str, OperationResult] = {}
        self.operation_callbacks: Dict[str, List[Callable]] = {}
        
        # Error handling
        self.error_handlers: Dict[type, Callable] = {}
        self._setup_error_handlers()
        
        self.logger.info("UI Service Bridge initialized")
    
    def _initialize_services(self):
        """Initialize all backend services."""
        try:
            # Template management services
            self.services['templating'] = TemplatingEngine(self.config_manager, self.db_manager)
            self.services['version_control'] = VersionControlService(self.config_manager, self.db_manager)
            
            # Security services
            self.services['security'] = SecurityScanner()
            
            # Collaboration services
            self.services['workspace'] = WorkspaceManagementService(self.db_manager)
            self.services['approval'] = ApprovalWorkflowService(self.db_manager)
            
            # Analytics services
            self.services['analytics'] = PerformanceAnalytics(self.config_manager, self.db_manager)
            
            # Evaluation services
            self.services['testing'] = MultiModelTestingInfrastructure(self.config_manager, self.db_manager)
            self.services['rating'] = HumanRatingService(self.config_manager, self.db_manager)
            
            self.logger.info("All services initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize services: {e}")
            raise
    
    def _setup_error_handlers(self):
        """Set up error handlers for different exception types."""
        self.error_handlers = {
            FileNotFoundError: self._handle_file_not_found,
            PermissionError: self._handle_permission_error,
            ConnectionError: self._handle_connection_error,
            ValueError: self._handle_value_error,
            Exception: self._handle_generic_error
        }
    
    def _handle_file_not_found(self, error: FileNotFoundError) -> str:
        """Handle file not found errors."""
        return f"File not found: {error.filename}. Please check if the file exists and try again."
    
    def _handle_permission_error(self, error: PermissionError) -> str:
        """Handle permission errors."""
        return f"Permission denied: {error}. Please check file permissions or run with appropriate privileges."
    
    def _handle_connection_error(self, error: ConnectionError) -> str:
        """Handle connection errors."""
        return f"Connection failed: {error}. Please check your network connection and service availability."
    
    def _handle_value_error(self, error: ValueError) -> str:
        """Handle value errors."""
        return f"Invalid input: {error}. Please check your input values and try again."
    
    def _handle_generic_error(self, error: Exception) -> str:
        """Handle generic errors."""
        return f"An unexpected error occurred: {error}. Please try again or contact support."
    
    def _get_user_friendly_error(self, error: Exception) -> str:
        """Convert technical error to user-friendly message."""
        error_type = type(error)
        
        # Find the most specific error handler
        for exc_type, handler in self.error_handlers.items():
            if issubclass(error_type, exc_type):
                return handler(error)
        
        return self._handle_generic_error(error)
    
    def execute_operation(self, operation_name: str, service_name: str, 
                         method_name: str, *args, **kwargs) -> str:
        """Execute a service operation with error handling and progress tracking."""
        operation_id = f"{operation_name}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # Initialize operation result
        result = OperationResult(
            operation_id=operation_id,
            status=OperationStatus.PENDING,
            message=f"Starting {operation_name}..."
        )
        self.active_operations[operation_id] = result
        
        # Execute in background thread
        thread = threading.Thread(
            target=self._execute_operation_thread,
            args=(operation_id, service_name, method_name, args, kwargs),
            daemon=True
        )
        thread.start()
        
        return operation_id
    
    def _execute_operation_thread(self, operation_id: str, service_name: str,
                                method_name: str, args: tuple, kwargs: dict):
        """Execute operation in background thread."""
        result = self.active_operations[operation_id]
        
        try:
            # Update status
            result.status = OperationStatus.IN_PROGRESS
            result.message = f"Executing {method_name}..."
            result.progress = 10.0
            self._notify_callbacks(operation_id)
            
            # Get service
            if service_name not in self.services:
                raise ValueError(f"Service '{service_name}' not found")
            
            service = self.services[service_name]
            
            # Get method
            if not hasattr(service, method_name):
                raise ValueError(f"Method '{method_name}' not found in service '{service_name}'")
            
            method = getattr(service, method_name)
            
            # Update progress
            result.progress = 30.0
            result.message = f"Processing {method_name}..."
            self._notify_callbacks(operation_id)
            
            # Execute method
            if asyncio.iscoroutinefunction(method):
                # Handle async methods
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    data = loop.run_until_complete(method(*args, **kwargs))
                finally:
                    loop.close()
            else:
                # Handle sync methods
                data = method(*args, **kwargs)
            
            # Update progress
            result.progress = 90.0
            result.message = "Finalizing..."
            self._notify_callbacks(operation_id)
            
            # Complete operation
            result.status = OperationStatus.COMPLETED
            result.data = data
            result.progress = 100.0
            result.message = f"{method_name} completed successfully"
            
        except Exception as e:
            # Handle error
            result.status = OperationStatus.FAILED
            result.error = self._get_user_friendly_error(e)
            result.message = f"{method_name} failed: {result.error}"
            result.progress = 0.0
            
            self.logger.error(f"Operation {operation_id} failed: {e}")
        
        finally:
            # Notify callbacks
            self._notify_callbacks(operation_id)
    
    def _notify_callbacks(self, operation_id: str):
        """Notify registered callbacks about operation updates."""
        if operation_id in self.operation_callbacks:
            result = self.active_operations[operation_id]
            for callback in self.operation_callbacks[operation_id]:
                try:
                    callback(result)
                except Exception as e:
                    self.logger.error(f"Callback error for operation {operation_id}: {e}")
    
    def register_callback(self, operation_id: str, callback: Callable[[OperationResult], None]):
        """Register callback for operation updates."""
        if operation_id not in self.operation_callbacks:
            self.operation_callbacks[operation_id] = []
        self.operation_callbacks[operation_id].append(callback)
    
    def get_operation_status(self, operation_id: str) -> Optional[OperationResult]:
        """Get current status of an operation."""
        return self.active_operations.get(operation_id)
    
    def cancel_operation(self, operation_id: str) -> bool:
        """Cancel an active operation."""
        if operation_id in self.active_operations:
            result = self.active_operations[operation_id]
            if result.status == OperationStatus.IN_PROGRESS:
                result.status = OperationStatus.CANCELLED
                result.message = "Operation cancelled by user"
                self._notify_callbacks(operation_id)
                return True
        return False
    
    def cleanup_completed_operations(self, max_age_hours: int = 24):
        """Clean up completed operations older than specified hours."""
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        
        to_remove = []
        for operation_id, result in self.active_operations.items():
            if (result.status in [OperationStatus.COMPLETED, OperationStatus.FAILED, OperationStatus.CANCELLED] and
                result.timestamp.timestamp() < cutoff_time):
                to_remove.append(operation_id)
        
        for operation_id in to_remove:
            del self.active_operations[operation_id]
            if operation_id in self.operation_callbacks:
                del self.operation_callbacks[operation_id]
        
        if to_remove:
            self.logger.info(f"Cleaned up {len(to_remove)} completed operations")
    
    # Convenience methods for common operations
    
    def create_template(self, template_data: Dict[str, Any], callback: Callable = None) -> str:
        """Create a new template."""
        operation_id = self.execute_operation(
            "Create Template", "templating", "create_template", template_data
        )
        if callback:
            self.register_callback(operation_id, callback)
        return operation_id
    
    def update_template(self, template_id: str, template_data: Dict[str, Any], callback: Callable = None) -> str:
        """Update an existing template."""
        operation_id = self.execute_operation(
            "Update Template", "templating", "update_template", template_id, template_data
        )
        if callback:
            self.register_callback(operation_id, callback)
        return operation_id
    
    def scan_template_security(self, template_id: str, callback: Callable = None) -> str:
        """Scan template for security issues."""
        operation_id = self.execute_operation(
            "Security Scan", "security", "scan_template", template_id
        )
        if callback:
            self.register_callback(operation_id, callback)
        return operation_id
    
    def create_workspace(self, workspace_data: Dict[str, Any], callback: Callable = None) -> str:
        """Create a new workspace."""
        operation_id = self.execute_operation(
            "Create Workspace", "workspace", "create_workspace", workspace_data
        )
        if callback:
            self.register_callback(operation_id, callback)
        return operation_id
    
    def submit_for_approval(self, item_id: str, item_type: str, callback: Callable = None) -> str:
        """Submit item for approval."""
        operation_id = self.execute_operation(
            "Submit for Approval", "approval", "submit_for_approval", item_id, item_type
        )
        if callback:
            self.register_callback(operation_id, callback)
        return operation_id
    
    def generate_analytics(self, prompt_ids: List[str] = None, callback: Callable = None) -> str:
        """Generate performance analytics."""
        operation_id = self.execute_operation(
            "Generate Analytics", "analytics", "generate_performance_insights", prompt_ids
        )
        if callback:
            self.register_callback(operation_id, callback)
        return operation_id
    
    def start_multi_model_test(self, test_config: Dict[str, Any], callback: Callable = None) -> str:
        """Start multi-model testing."""
        operation_id = self.execute_operation(
            "Multi-Model Test", "testing", "create_test_session", test_config
        )
        if callback:
            self.register_callback(operation_id, callback)
        return operation_id
    
    def get_service(self, service_name: str):
        """Get direct access to a service (use with caution)."""
        return self.services.get(service_name)
    
    def get_all_services(self) -> Dict[str, Any]:
        """Get all available services."""
        return self.services.copy()
    
    def health_check(self) -> Dict[str, bool]:
        """Check health of all services."""
        health_status = {}
        
        for service_name, service in self.services.items():
            try:
                # Try to call a basic method or check if service is initialized
                if hasattr(service, 'health_check'):
                    health_status[service_name] = service.health_check()
                elif hasattr(service, 'is_initialized'):
                    health_status[service_name] = service.is_initialized()
                else:
                    # Assume healthy if service exists
                    health_status[service_name] = True
            except Exception as e:
                health_status[service_name] = False
                self.logger.error(f"Health check failed for {service_name}: {e}")
        
        return health_status