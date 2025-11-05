"""
Validation and Feedback Systems
===============================

Comprehensive validation and user feedback systems for the UI.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import re
import json
from typing import Dict, List, Optional, Any, Callable, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum


class ValidationLevel(Enum):
    """Validation severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class NotificationType(Enum):
    """Types of notifications."""
    SUCCESS = "success"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class ValidationResult:
    """Result of a validation check."""
    field: str
    level: ValidationLevel
    message: str
    suggestion: Optional[str] = None
    code: Optional[str] = None


@dataclass
class NotificationConfig:
    """Configuration for notifications."""
    show_success: bool = True
    show_info: bool = True
    show_warnings: bool = True
    show_errors: bool = True
    auto_dismiss_success: bool = True
    auto_dismiss_info: bool = True
    success_duration: int = 3000
    info_duration: int = 5000


class TemplateValidator:
    """Validates template content and metadata."""
    
    def __init__(self):
        self.variable_pattern = re.compile(r'\{\{([^}]+)\}\}')
        self.security_patterns = {
            'sql_injection': re.compile(r'(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER)\s+', re.IGNORECASE),
            'script_injection': re.compile(r'<script[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL),
            'command_injection': re.compile(r'(exec|eval|system|shell_exec|passthru)\s*\(', re.IGNORECASE),
        }
    
    def validate_template_content(self, content: str) -> List[ValidationResult]:
        """Validate template content."""
        results = []
        
        # Check if content is empty
        if not content.strip():
            results.append(ValidationResult(
                field="content",
                level=ValidationLevel.ERROR,
                message="Template content cannot be empty",
                suggestion="Add some content to your template"
            ))
            return results
        
        # Check template variables
        variables = self.variable_pattern.findall(content)
        if not variables:
            results.append(ValidationResult(
                field="content",
                level=ValidationLevel.WARNING,
                message="No template variables found",
                suggestion="Consider adding variables like {{variable_name}} for dynamic content"
            ))
        else:
            # Validate variable names
            for var in variables:
                if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', var.strip()):
                    results.append(ValidationResult(
                        field="content",
                        level=ValidationLevel.ERROR,
                        message=f"Invalid variable name: {var}",
                        suggestion="Variable names should start with a letter or underscore and contain only letters, numbers, and underscores"
                    ))
        
        # Security checks
        for check_name, pattern in self.security_patterns.items():
            if pattern.search(content):
                results.append(ValidationResult(
                    field="content",
                    level=ValidationLevel.CRITICAL,
                    message=f"Potential security issue detected: {check_name}",
                    suggestion="Review the content for potential security vulnerabilities",
                    code=check_name
                ))
        
        # Check content length
        if len(content) > 10000:
            results.append(ValidationResult(
                field="content",
                level=ValidationLevel.WARNING,
                message="Template content is very long",
                suggestion="Consider breaking down large templates into smaller, reusable components"
            ))
        
        # Check for common issues
        if content.count('{{') != content.count('}}'):
            results.append(ValidationResult(
                field="content",
                level=ValidationLevel.ERROR,
                message="Mismatched template variable brackets",
                suggestion="Ensure all {{ have matching }} brackets"
            ))
        
        return results
    
    def validate_template_metadata(self, metadata: Dict[str, Any]) -> List[ValidationResult]:
        """Validate template metadata."""
        results = []
        
        # Check required fields
        required_fields = ['name', 'description']
        for field in required_fields:
            if not metadata.get(field, '').strip():
                results.append(ValidationResult(
                    field=field,
                    level=ValidationLevel.ERROR,
                    message=f"{field.title()} is required",
                    suggestion=f"Please provide a {field} for the template"
                ))
        
        # Validate name
        name = metadata.get('name', '')
        if name:
            if len(name) < 3:
                results.append(ValidationResult(
                    field="name",
                    level=ValidationLevel.WARNING,
                    message="Template name is very short",
                    suggestion="Consider using a more descriptive name"
                ))
            elif len(name) > 100:
                results.append(ValidationResult(
                    field="name",
                    level=ValidationLevel.WARNING,
                    message="Template name is very long",
                    suggestion="Consider using a shorter, more concise name"
                ))
            
            if not re.match(r'^[a-zA-Z0-9\s\-_\.]+$', name):
                results.append(ValidationResult(
                    field="name",
                    level=ValidationLevel.WARNING,
                    message="Template name contains special characters",
                    suggestion="Consider using only letters, numbers, spaces, hyphens, underscores, and periods"
                ))
        
        # Validate description
        description = metadata.get('description', '')
        if description and len(description) < 10:
            results.append(ValidationResult(
                field="description",
                level=ValidationLevel.WARNING,
                message="Description is very short",
                suggestion="Provide a more detailed description to help others understand the template's purpose"
            ))
        
        # Validate tags
        tags = metadata.get('tags', [])
        if isinstance(tags, list):
            for tag in tags:
                if not isinstance(tag, str) or not tag.strip():
                    results.append(ValidationResult(
                        field="tags",
                        level=ValidationLevel.WARNING,
                        message="Invalid tag found",
                        suggestion="Tags should be non-empty strings"
                    ))
        
        return results


class RealTimeValidator:
    """Provides real-time validation for UI components."""
    
    def __init__(self, widget: tk.Widget, validator: Callable[[str], List[ValidationResult]]):
        self.widget = widget
        self.validator = validator
        self.validation_label = None
        self.last_validation_time = 0
        self.validation_delay = 500  # ms
        
        # Bind validation events
        if isinstance(widget, tk.Text):
            widget.bind('<KeyRelease>', self._on_text_change)
            widget.bind('<FocusOut>', self._validate_now)
        elif isinstance(widget, (tk.Entry, ttk.Entry)):
            widget.bind('<KeyRelease>', self._on_text_change)
            widget.bind('<FocusOut>', self._validate_now)
    
    def _on_text_change(self, event):
        """Handle text change events."""
        # Cancel previous validation
        if hasattr(self, '_validation_job'):
            self.widget.after_cancel(self._validation_job)
        
        # Schedule new validation
        self._validation_job = self.widget.after(self.validation_delay, self._validate_now)
    
    def _validate_now(self, event=None):
        """Perform validation now."""
        try:
            # Get current value
            if isinstance(self.widget, tk.Text):
                value = self.widget.get(1.0, tk.END).strip()
            else:
                value = self.widget.get().strip()
            
            # Validate
            results = self.validator(value)
            
            # Update UI
            self._update_validation_display(results)
            
        except Exception as e:
            print(f"Validation error: {e}")
    
    def _update_validation_display(self, results: List[ValidationResult]):
        """Update validation display."""
        if not self.validation_label:
            # Create validation label if it doesn't exist
            parent = self.widget.master
            self.validation_label = ttk.Label(parent, text="", foreground="red", font=("Arial", 8))
            
            # Position below the widget
            widget_info = self.widget.grid_info()
            if widget_info:
                self.validation_label.grid(
                    row=widget_info['row'] + 1,
                    column=widget_info['column'],
                    sticky=tk.W,
                    padx=widget_info.get('padx', 0)
                )
            else:
                self.validation_label.pack(anchor=tk.W)
        
        # Update validation message
        if results:
            # Show most severe issue
            critical_results = [r for r in results if r.level == ValidationLevel.CRITICAL]
            error_results = [r for r in results if r.level == ValidationLevel.ERROR]
            warning_results = [r for r in results if r.level == ValidationLevel.WARNING]
            
            if critical_results:
                result = critical_results[0]
                self.validation_label.config(text=f"⚠ {result.message}", foreground="red")
            elif error_results:
                result = error_results[0]
                self.validation_label.config(text=f"✗ {result.message}", foreground="red")
            elif warning_results:
                result = warning_results[0]
                self.validation_label.config(text=f"⚠ {result.message}", foreground="orange")
            else:
                self.validation_label.config(text="✓ Valid", foreground="green")
        else:
            self.validation_label.config(text="✓ Valid", foreground="green")


class NotificationSystem:
    """System for showing user notifications."""
    
    def __init__(self, parent: tk.Widget, config: NotificationConfig = None):
        self.parent = parent
        self.config = config or NotificationConfig()
        self.notifications: List[tk.Toplevel] = []
        self.notification_count = 0
    
    def show_notification(self, message: str, notification_type: NotificationType = NotificationType.INFO,
                         duration: int = None, actions: List[Dict[str, Any]] = None):
        """Show a notification to the user."""
        # Check if this type of notification should be shown
        if not self._should_show_notification(notification_type):
            return
        
        # Determine duration
        if duration is None:
            if notification_type == NotificationType.SUCCESS:
                duration = self.config.success_duration
            elif notification_type == NotificationType.INFO:
                duration = self.config.info_duration
            else:
                duration = 0  # Manual dismiss for warnings and errors
        
        # Create notification window
        notification = self._create_notification_window(message, notification_type, actions)
        
        # Auto-dismiss if configured
        if duration > 0:
            self.parent.after(duration, lambda: self._dismiss_notification(notification))
        
        return notification
    
    def _should_show_notification(self, notification_type: NotificationType) -> bool:
        """Check if notification type should be shown."""
        if notification_type == NotificationType.SUCCESS:
            return self.config.show_success
        elif notification_type == NotificationType.INFO:
            return self.config.show_info
        elif notification_type == NotificationType.WARNING:
            return self.config.show_warnings
        elif notification_type == NotificationType.ERROR:
            return self.config.show_errors
        return True
    
    def _create_notification_window(self, message: str, notification_type: NotificationType,
                                  actions: List[Dict[str, Any]] = None) -> tk.Toplevel:
        """Create notification window."""
        notification = tk.Toplevel(self.parent)
        notification.title("Notification")
        notification.geometry("400x150")
        notification.resizable(False, False)
        
        # Position notification
        self._position_notification(notification)
        
        # Configure colors based on type
        colors = {
            NotificationType.SUCCESS: {"bg": "#d4edda", "fg": "#155724", "border": "#c3e6cb"},
            NotificationType.INFO: {"bg": "#d1ecf1", "fg": "#0c5460", "border": "#bee5eb"},
            NotificationType.WARNING: {"bg": "#fff3cd", "fg": "#856404", "border": "#ffeaa7"},
            NotificationType.ERROR: {"bg": "#f8d7da", "fg": "#721c24", "border": "#f5c6cb"}
        }
        
        color_config = colors.get(notification_type, colors[NotificationType.INFO])
        notification.configure(bg=color_config["bg"])
        
        # Create main frame
        main_frame = tk.Frame(notification, bg=color_config["bg"], relief=tk.RAISED, bd=2)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Icon and message
        content_frame = tk.Frame(main_frame, bg=color_config["bg"])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Icon
        icons = {
            NotificationType.SUCCESS: "✓",
            NotificationType.INFO: "ℹ",
            NotificationType.WARNING: "⚠",
            NotificationType.ERROR: "✗"
        }
        
        icon_label = tk.Label(
            content_frame,
            text=icons.get(notification_type, "ℹ"),
            font=("Arial", 16, "bold"),
            fg=color_config["fg"],
            bg=color_config["bg"]
        )
        icon_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Message
        message_label = tk.Label(
            content_frame,
            text=message,
            font=("Arial", 10),
            fg=color_config["fg"],
            bg=color_config["bg"],
            wraplength=300,
            justify=tk.LEFT
        )
        message_label.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Actions frame
        if actions or notification_type in [NotificationType.WARNING, NotificationType.ERROR]:
            actions_frame = tk.Frame(main_frame, bg=color_config["bg"])
            actions_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
            
            # Add custom actions
            if actions:
                for action in actions:
                    btn = tk.Button(
                        actions_frame,
                        text=action.get("text", "Action"),
                        command=lambda cmd=action.get("command"): self._execute_action(cmd, notification),
                        font=("Arial", 8)
                    )
                    btn.pack(side=tk.LEFT, padx=(0, 5))
            
            # Add dismiss button for warnings and errors
            if notification_type in [NotificationType.WARNING, NotificationType.ERROR]:
                dismiss_btn = tk.Button(
                    actions_frame,
                    text="Dismiss",
                    command=lambda: self._dismiss_notification(notification),
                    font=("Arial", 8)
                )
                dismiss_btn.pack(side=tk.RIGHT)
        
        # Add to notifications list
        self.notifications.append(notification)
        
        # Handle window close
        notification.protocol("WM_DELETE_WINDOW", lambda: self._dismiss_notification(notification))
        
        return notification
    
    def _position_notification(self, notification: tk.Toplevel):
        """Position notification window."""
        # Get parent window position and size
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        
        # Calculate notification position (top-right of parent)
        notification_x = parent_x + parent_width - 420  # 400 width + 20 margin
        notification_y = parent_y + 50 + (self.notification_count * 160)  # Stack notifications
        
        notification.geometry(f"+{notification_x}+{notification_y}")
        self.notification_count += 1
    
    def _execute_action(self, command: Callable, notification: tk.Toplevel):
        """Execute action and dismiss notification."""
        try:
            if command:
                command()
        except Exception as e:
            print(f"Error executing notification action: {e}")
        finally:
            self._dismiss_notification(notification)
    
    def _dismiss_notification(self, notification: tk.Toplevel):
        """Dismiss a notification."""
        try:
            if notification in self.notifications:
                self.notifications.remove(notification)
                self.notification_count = max(0, self.notification_count - 1)
            
            notification.destroy()
        except tk.TclError:
            pass  # Window already destroyed
    
    def dismiss_all(self):
        """Dismiss all notifications."""
        for notification in self.notifications.copy():
            self._dismiss_notification(notification)
    
    def show_success(self, message: str, duration: int = None):
        """Show success notification."""
        return self.show_notification(message, NotificationType.SUCCESS, duration)
    
    def show_info(self, message: str, duration: int = None):
        """Show info notification."""
        return self.show_notification(message, NotificationType.INFO, duration)
    
    def show_warning(self, message: str, actions: List[Dict[str, Any]] = None):
        """Show warning notification."""
        return self.show_notification(message, NotificationType.WARNING, 0, actions)
    
    def show_error(self, message: str, actions: List[Dict[str, Any]] = None):
        """Show error notification."""
        return self.show_notification(message, NotificationType.ERROR, 0, actions)


class ProgressIndicator:
    """Progress indicator for long-running operations."""
    
    def __init__(self, parent: tk.Widget, title: str = "Processing..."):
        self.parent = parent
        self.title = title
        self.progress_window = None
        self.progress_var = None
        self.status_var = None
        self.cancel_callback = None
    
    def show(self, cancelable: bool = False, cancel_callback: Callable = None):
        """Show progress indicator."""
        if self.progress_window:
            return  # Already showing
        
        self.cancel_callback = cancel_callback
        
        # Create progress window
        self.progress_window = tk.Toplevel(self.parent)
        self.progress_window.title(self.title)
        self.progress_window.geometry("400x150")
        self.progress_window.resizable(False, False)
        self.progress_window.transient(self.parent)
        self.progress_window.grab_set()
        
        # Center window
        self._center_window()
        
        # Create content
        main_frame = tk.Frame(self.progress_window, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title label
        title_label = tk.Label(main_frame, text=self.title, font=("Arial", 12, "bold"))
        title_label.pack(pady=(0, 10))
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(
            main_frame,
            variable=self.progress_var,
            maximum=100,
            length=350,
            mode='determinate'
        )
        progress_bar.pack(pady=(0, 10))
        
        # Status label
        self.status_var = tk.StringVar(value="Initializing...")
        status_label = tk.Label(main_frame, textvariable=self.status_var, font=("Arial", 9))
        status_label.pack(pady=(0, 10))
        
        # Cancel button
        if cancelable and cancel_callback:
            cancel_btn = tk.Button(
                main_frame,
                text="Cancel",
                command=self._cancel_operation
            )
            cancel_btn.pack()
        
        # Handle window close
        self.progress_window.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def update_progress(self, progress: float, status: str = None):
        """Update progress and status."""
        if self.progress_var:
            self.progress_var.set(progress)
        
        if status and self.status_var:
            self.status_var.set(status)
        
        if self.progress_window:
            self.progress_window.update()
    
    def hide(self):
        """Hide progress indicator."""
        if self.progress_window:
            self.progress_window.grab_release()
            self.progress_window.destroy()
            self.progress_window = None
            self.progress_var = None
            self.status_var = None
    
    def _center_window(self):
        """Center progress window on parent."""
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        window_width = 400
        window_height = 150
        
        x = parent_x + (parent_width - window_width) // 2
        y = parent_y + (parent_height - window_height) // 2
        
        self.progress_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    def _cancel_operation(self):
        """Cancel the operation."""
        if self.cancel_callback:
            self.cancel_callback()
        self.hide()
    
    def _on_close(self):
        """Handle window close event."""
        if self.cancel_callback:
            self._cancel_operation()
        else:
            self.hide()


# Convenience functions for common validation scenarios

def validate_template_name(name: str) -> List[ValidationResult]:
    """Validate template name."""
    results = []
    
    if not name.strip():
        results.append(ValidationResult(
            field="name",
            level=ValidationLevel.ERROR,
            message="Name is required"
        ))
    elif len(name) < 3:
        results.append(ValidationResult(
            field="name",
            level=ValidationLevel.WARNING,
            message="Name is very short"
        ))
    elif len(name) > 100:
        results.append(ValidationResult(
            field="name",
            level=ValidationLevel.WARNING,
            message="Name is very long"
        ))
    
    return results


def validate_json_content(content: str) -> List[ValidationResult]:
    """Validate JSON content."""
    results = []
    
    if not content.strip():
        results.append(ValidationResult(
            field="content",
            level=ValidationLevel.ERROR,
            message="Content cannot be empty"
        ))
        return results
    
    try:
        json.loads(content)
        results.append(ValidationResult(
            field="content",
            level=ValidationLevel.INFO,
            message="Valid JSON format"
        ))
    except json.JSONDecodeError as e:
        results.append(ValidationResult(
            field="content",
            level=ValidationLevel.ERROR,
            message=f"Invalid JSON: {e.msg}",
            suggestion="Check JSON syntax and formatting"
        ))
    
    return results