"""
Workflow Management UI for MCP Admin Application
===============================================

User interface for workflow creation, management, and execution.
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from models.workflow import (
    WorkflowDefinition, WorkflowStep, WorkflowConnection, WorkflowVariable,
    WorkflowStatus, StepStatus, ConnectionType, ExecutionMode, WorkflowPosition
)
from models.base import generate_id
from services.workflow_engine import WorkflowEngine
from services.workflow_executor import WorkflowExecutor


class WorkflowCanvas(tk.Canvas):
    """Canvas for visual workflow design."""
    
    def __init__(self, parent, workflow_page):
        super().__init__(parent, bg="white", highlightthickness=1, highlightcolor="gray")
        self.workflow_page = workflow_page
        self.logger = logging.getLogger(__name__)
        
        # Canvas state
        self.workflow: Optional[WorkflowDefinition] = None
        self.selected_items = set()
        self.drag_data = {"x": 0, "y": 0, "item": None}
        
        # Visual elements
        self.step_items = {}  # step_id -> canvas_item_id
        self.connection_items = {}  # connection_id -> canvas_item_id
        
        # Bind events
        self.bind("<Button-1>", self.on_click)
        self.bind("<B1-Motion>", self.on_drag)
        self.bind("<ButtonRelease-1>", self.on_release)
        self.bind("<Button-3>", self.on_right_click)
        self.bind("<Double-Button-1>", self.on_double_click)
        
        # Configure scrolling
        self.configure(scrollregion=(0, 0, 2000, 2000))
    
    def load_workflow(self, workflow: WorkflowDefinition):
        """Load workflow into canvas."""
        self.workflow = workflow
        self.clear_canvas()
        self.draw_workflow()
    
    def clear_canvas(self):
        """Clear all items from canvas."""
        self.delete("all")
        self.step_items.clear()
        self.connection_items.clear()
        self.selected_items.clear()
    
    def draw_workflow(self):
        """Draw workflow on canvas."""
        if not self.workflow:
            return
        
        # Draw connections first (so they appear behind steps)
        for connection in self.workflow.connections:
            self.draw_connection(connection)
        
        # Draw steps
        for step in self.workflow.steps:
            self.draw_step(step)
    
    def draw_step(self, step: WorkflowStep):
        """Draw a workflow step."""
        x, y = step.position.x, step.position.y
        width, height = 120, 60
        
        # Determine step color based on status
        if hasattr(step, 'status'):
            if step.status == StepStatus.COMPLETED:
                fill_color = "#d4edda"
                outline_color = "#28a745"
            elif step.status == StepStatus.FAILED:
                fill_color = "#f8d7da"
                outline_color = "#dc3545"
            elif step.status == StepStatus.RUNNING:
                fill_color = "#fff3cd"
                outline_color = "#ffc107"
            else:
                fill_color = "#e9ecef"
                outline_color = "#6c757d"
        else:
            fill_color = "#f8f9fa"
            outline_color = "#dee2e6"
        
        # Draw step rectangle
        rect_id = self.create_rectangle(
            x, y, x + width, y + height,
            fill=fill_color, outline=outline_color, width=2,
            tags=("step", step.id)
        )
        
        # Draw step name
        text_id = self.create_text(
            x + width/2, y + height/2,
            text=step.name or step.tool_id,
            font=("Arial", 10, "bold"),
            tags=("step", step.id)
        )
        
        # Store canvas items
        self.step_items[step.id] = [rect_id, text_id]
    
    def draw_connection(self, connection: WorkflowConnection):
        """Draw a workflow connection."""
        source_step = self.get_step_by_id(connection.source_step_id)
        target_step = self.get_step_by_id(connection.target_step_id)
        
        if not source_step or not target_step:
            return
        
        # Calculate connection points
        x1 = source_step.position.x + 120  # Right edge of source
        y1 = source_step.position.y + 30   # Middle of source
        x2 = target_step.position.x         # Left edge of target
        y2 = target_step.position.y + 30    # Middle of target
        
        # Determine connection color
        if connection.connection_type == ConnectionType.DATA:
            color = "#007bff"
        elif connection.connection_type == ConnectionType.CONTROL:
            color = "#28a745"
        elif connection.connection_type == ConnectionType.ERROR:
            color = "#dc3545"
        else:
            color = "#6c757d"
        
        # Draw arrow line
        line_id = self.create_line(
            x1, y1, x2, y2,
            fill=color, width=2, arrow=tk.LAST,
            tags=("connection", connection.id)
        )
        
        # Draw connection label if present
        if connection.label:
            mid_x = (x1 + x2) / 2
            mid_y = (y1 + y2) / 2
            label_id = self.create_text(
                mid_x, mid_y - 10,
                text=connection.label,
                font=("Arial", 8),
                fill=color,
                tags=("connection", connection.id)
            )
            self.connection_items[connection.id] = [line_id, label_id]
        else:
            self.connection_items[connection.id] = [line_id]
    
    def get_step_by_id(self, step_id: str) -> Optional[WorkflowStep]:
        """Get step by ID."""
        if not self.workflow:
            return None
        
        for step in self.workflow.steps:
            if step.id == step_id:
                return step
        return None
    
    def on_click(self, event):
        """Handle mouse click."""
        item = self.find_closest(event.x, event.y)[0]
        tags = self.gettags(item)f