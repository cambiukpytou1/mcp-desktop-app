"""
Evaluation and Testing UI Page
==============================

User interface for multi-model testing and human rating evaluation.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import json
from datetime import datetime
from typing import Dict, List, Optional, Any

from services.evaluation.multi_model_testing import MultiModelTestingInfrastructure, TestConfiguration, TestSession
from services.evaluation.human_rating import HumanRatingService
from services.evaluation.scoring_engine import ScoringEngine


import tkinter as tk

class EvaluationTestingPage(tk.Frame):
    """Evaluation and testing management page."""
    
    def __init__(self, parent, config_manager, db_manager):
        super().__init__(parent, bg="#f9f9f9")
        self.parent = parent
        self.config_manager = config_manager
        self.db_manager = db_manager
        
        # Initialize services
        self.multi_model_testing = MultiModelTestingInfrastructure(config_manager, db_manager)
        self.human_rating = HumanRatingService(config_manager, db_manager)
        self.scoring_engine = ScoringEngine(config_manager, db_manager)
        
        # UI state
        self.current_test_session = None
        self.available_providers = []
        self.test_results = []
        
        self.setup_ui()
        self.load_providers()
    
    def setup_ui(self):
        """Set up the user interface."""
        # Main container
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(
            self.main_frame, 
            text="Evaluation & Testing", 
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self.create_multi_model_tab()
        self.create_human_rating_tab()
        self.create_results_tab()
    
    def create_multi_model_tab(self):
        """Create multi-model testing interface tab."""
        multi_model_frame = ttk.Frame(self.notebook)
        self.notebook.add(multi_model_frame, text="Multi-Model Testing")
        
        # Test configuration panel
        config_frame = ttk.LabelFrame(multi_model_frame, text="Test Configuration", padding=10)
        config_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Test name
        ttk.Label(config_frame, text="Test Name:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.test_name_var = tk.StringVar()
        test_name_entry = ttk.Entry(config_frame, textvariable=self.test_name_var, width=30)
        test_name_entry.grid(row=0, column=1, padx=(0, 10), sticky=tk.W)
        
        # Prompt template selection
        ttk.Label(config_frame, text="Prompt Template:").grid(row=0, column=2, sticky=tk.W, padx=(10, 5))
        self.prompt_template_var = tk.StringVar()
        self.prompt_template_combo = ttk.Combobox(
            config_frame, 
            textvariable=self.prompt_template_var,
            width=25,
            state="readonly"
        )
        self.prompt_template_combo.grid(row=0, column=3, padx=(0, 10))
        
        # Iterations
        ttk.Label(config_frame, text="Iterations:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=(10, 0))
        self.iterations_var = tk.StringVar(value="1")
        iterations_spin = ttk.Spinbox(config_frame, from_=1, to=10, textvariable=self.iterations_var, width=10)
        iterations_spin.grid(row=1, column=1, padx=(0, 10), pady=(10, 0), sticky=tk.W)
        
        # Parallel execution
        self.parallel_var = tk.BooleanVar(value=True)
        parallel_check = ttk.Checkbutton(
            config_frame,
            text="Parallel Execution",
            variable=self.parallel_var
        )
        parallel_check.grid(row=1, column=2, padx=(10, 0), pady=(10, 0), sticky=tk.W)
        
        # Provider selection panel
        provider_frame = ttk.LabelFrame(multi_model_frame, text="Provider Selection", padding=10)
        provider_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Provider list with checkboxes
        provider_list_frame = ttk.Frame(provider_frame)
        provider_list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Providers treeview
        provider_columns = ("Select", "Provider", "Type", "Status", "Models")
        self.provider_tree = ttk.Treeview(provider_list_frame, columns=provider_columns, show="headings", height=8)
        
        for col in provider_columns:
            self.provider_tree.heading(col, text=col)
            self.provider_tree.column(col, width=120)
        
        provider_scrollbar = ttk.Scrollbar(provider_list_frame, orient=tk.VERTICAL, command=self.provider_tree.yview)
        self.provider_tree.configure(yscrollcommand=provider_scrollbar.set)
        
        self.provider_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        provider_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind selection events
        self.provider_tree.bind("<Button-1>", self.on_provider_click)
        
        # Control buttons
        button_frame = ttk.Frame(multi_model_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Start test button
        start_test_btn = ttk.Button(
            button_frame,
            text="Start Test",
            command=self.start_multi_model_test
        )
        start_test_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Stop test button
        stop_test_btn = ttk.Button(
            button_frame,
            text="Stop Test",
            command=self.stop_multi_model_test
        )
        stop_test_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Refresh providers button
        refresh_btn = ttk.Button(
            button_frame,
            text="Refresh Providers",
            command=self.load_providers
        )
        refresh_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            button_frame,
            variable=self.progress_var,
            maximum=100,
            length=200
        )
        self.progress_bar.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Status label
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(button_frame, textvariable=self.status_var)
        status_label.pack(side=tk.RIGHT, padx=(10, 0))
    
    def create_human_rating_tab(self):
        """Create human rating and quality assessment interface tab."""
        rating_frame = ttk.Frame(self.notebook)
        self.notebook.add(rating_frame, text="Human Rating")
        
        # Rating session panel
        session_frame = ttk.LabelFrame(rating_frame, text="Rating Session", padding=10)
        session_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Session selection
        ttk.Label(session_frame, text="Test Session:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.rating_session_var = tk.StringVar()
        self.rating_session_combo = ttk.Combobox(
            session_frame,
            textvariable=self.rating_session_var,
            width=30,
            state="readonly"
        )
        self.rating_session_combo.grid(row=0, column=1, padx=(0, 10))
        
        # Load session button
        load_session_btn = ttk.Button(
            session_frame,
            text="Load Session",
            command=self.load_rating_session
        )
        load_session_btn.grid(row=0, column=2, padx=(0, 10))
        
        # Rating interface
        rating_interface_frame = ttk.LabelFrame(rating_frame, text="Rating Interface", padding=10)
        rating_interface_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Current item display
        current_item_frame = ttk.Frame(rating_interface_frame)
        current_item_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Prompt display
        ttk.Label(current_item_frame, text="Prompt:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        self.prompt_display = tk.Text(current_item_frame, height=4, wrap=tk.WORD, state=tk.DISABLED)
        self.prompt_display.pack(fill=tk.X, pady=(5, 10))
        
        # Response display
        ttk.Label(current_item_frame, text="Response:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        self.response_display = tk.Text(current_item_frame, height=6, wrap=tk.WORD, state=tk.DISABLED)
        self.response_display.pack(fill=tk.X, pady=(5, 10))
        
        # Rating controls
        rating_controls_frame = ttk.Frame(rating_interface_frame)
        rating_controls_frame.pack(fill=tk.X)
        
        # Quality score
        ttk.Label(rating_controls_frame, text="Quality Score:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.quality_score_var = tk.StringVar(value="5")
        quality_scale = ttk.Scale(
            rating_controls_frame,
            from_=1,
            to=10,
            orient=tk.HORIZONTAL,
            variable=self.quality_score_var,
            length=200
        )
        quality_scale.grid(row=0, column=1, padx=(0, 10))
        
        quality_label = ttk.Label(rating_controls_frame, textvariable=self.quality_score_var)
        quality_label.grid(row=0, column=2, padx=(0, 10))
        
        # Relevance score
        ttk.Label(rating_controls_frame, text="Relevance:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=(10, 0))
        self.relevance_score_var = tk.StringVar(value="5")
        relevance_scale = ttk.Scale(
            rating_controls_frame,
            from_=1,
            to=10,
            orient=tk.HORIZONTAL,
            variable=self.relevance_score_var,
            length=200
        )
        relevance_scale.grid(row=1, column=1, padx=(0, 10), pady=(10, 0))
        
        relevance_label = ttk.Label(rating_controls_frame, textvariable=self.relevance_score_var)
        relevance_label.grid(row=1, column=2, padx=(0, 10), pady=(10, 0))
        
        # Comments
        ttk.Label(rating_controls_frame, text="Comments:").grid(row=2, column=0, sticky=tk.NW, padx=(0, 5), pady=(10, 0))
        self.comments_text = tk.Text(rating_controls_frame, height=3, width=40)
        self.comments_text.grid(row=2, column=1, columnspan=2, padx=(0, 10), pady=(10, 0), sticky=tk.W)
        
        # Rating action buttons
        rating_actions_frame = ttk.Frame(rating_frame)
        rating_actions_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Submit rating button
        submit_rating_btn = ttk.Button(
            rating_actions_frame,
            text="Submit Rating",
            command=self.submit_rating
        )
        submit_rating_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Skip item button
        skip_btn = ttk.Button(
            rating_actions_frame,
            text="Skip Item",
            command=self.skip_rating_item
        )
        skip_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Progress info
        self.rating_progress_var = tk.StringVar(value="No session loaded")
        progress_label = ttk.Label(rating_actions_frame, textvariable=self.rating_progress_var)
        progress_label.pack(side=tk.RIGHT)
    
    def create_results_tab(self):
        """Create test results and analysis tab."""
        results_frame = ttk.Frame(self.notebook)
        self.notebook.add(results_frame, text="Results & Analysis")
        
        # Results control panel
        results_control_frame = ttk.LabelFrame(results_frame, text="Results Control", padding=10)
        results_control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Session selection for results
        ttk.Label(results_control_frame, text="Test Session:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.results_session_var = tk.StringVar()
        self.results_session_combo = ttk.Combobox(
            results_control_frame,
            textvariable=self.results_session_var,
            width=30,
            state="readonly"
        )
        self.results_session_combo.grid(row=0, column=1, padx=(0, 10))
        
        # Load results button
        load_results_btn = ttk.Button(
            results_control_frame,
            text="Load Results",
            command=self.load_test_results
        )
        load_results_btn.grid(row=0, column=2, padx=(0, 10))
        
        # Export results button
        export_btn = ttk.Button(
            results_control_frame,
            text="Export Results",
            command=self.export_test_results
        )
        export_btn.grid(row=0, column=3)
        
        # Results display
        results_display_frame = ttk.LabelFrame(results_frame, text="Test Results", padding=10)
        results_display_frame.pack(fill=tk.BOTH, expand=True)
        
        # Results treeview
        results_columns = ("Provider", "Model", "Score", "Cost", "Response Time", "Status")
        self.results_tree = ttk.Treeview(results_display_frame, columns=results_columns, show="headings", height=12)
        
        for col in results_columns:
            self.results_tree.heading(col, text=col)
            self.results_tree.column(col, width=120)
        
        results_scrollbar = ttk.Scrollbar(results_display_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=results_scrollbar.set)
        
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        results_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind selection event
        self.results_tree.bind("<<TreeviewSelect>>", self.on_result_selected)
        
        # Result details panel
        details_frame = ttk.LabelFrame(results_frame, text="Result Details", padding=10)
        details_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.result_details_text = tk.Text(details_frame, height=8, wrap=tk.WORD)
        details_scrollbar = ttk.Scrollbar(details_frame, orient=tk.VERTICAL, command=self.result_details_text.yview)
        self.result_details_text.configure(yscrollcommand=details_scrollbar.set)
        
        self.result_details_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        details_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def load_providers(self):
        """Load available providers into the provider tree."""
        try:
            # Clear existing items
            self.provider_tree.delete(*self.provider_tree.get_children())
            
            # Get available providers
            self.available_providers = self.multi_model_testing.get_available_providers()
            
            # Populate provider tree
            for provider in self.available_providers:
                status = "✓ Ready" if provider["initialized"] else "✗ Not Ready"
                model_count = len(provider["models"])
                
                self.provider_tree.insert("", tk.END, values=(
                    "☐",  # Checkbox placeholder
                    provider["name"],
                    provider["type"],
                    status,
                    f"{model_count} models"
                ), tags=(provider["id"],))
            
            # Load prompt templates
            self.load_prompt_templates()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load providers: {e}")
    
    def load_prompt_templates(self):
        """Load available prompt templates."""
        try:
            # Get prompt templates from database
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, name FROM prompts ORDER BY name")
                templates = cursor.fetchall()
            
            # Update combo box
            template_values = [f"{row[1]} ({row[0]})" for row in templates]
            self.prompt_template_combo['values'] = template_values
            
            if template_values:
                self.prompt_template_combo.set(template_values[0])
            
        except Exception as e:
            print(f"Error loading prompt templates: {e}")
    
    def on_provider_click(self, event):
        """Handle provider selection click."""
        try:
            item = self.provider_tree.selection()[0]
            current_values = list(self.provider_tree.item(item, "values"))
            
            # Toggle checkbox
            if current_values[0] == "☐":
                current_values[0] = "☑"
            else:
                current_values[0] = "☐"
            
            self.provider_tree.item(item, values=current_values)
            
        except (IndexError, tk.TclError):
            pass  # Click outside of item
    
    def get_selected_providers(self):
        """Get list of selected provider IDs."""
        selected = []
        for item in self.provider_tree.get_children():
            values = self.provider_tree.item(item, "values")
            if values[0] == "☑":
                tags = self.provider_tree.item(item, "tags")
                if tags:
                    selected.append(tags[0])
        return selected
    
    def start_multi_model_test(self):
        """Start multi-model testing."""
        try:
            # Validate inputs
            test_name = self.test_name_var.get().strip()
            if not test_name:
                messagebox.showerror("Error", "Please enter a test name")
                return
            
            prompt_template = self.prompt_template_var.get()
            if not prompt_template:
                messagebox.showerror("Error", "Please select a prompt template")
                return
            
            selected_providers = self.get_selected_providers()
            if not selected_providers:
                messagebox.showerror("Error", "Please select at least one provider")
                return
            
            # Extract prompt template ID
            template_id = prompt_template.split("(")[-1].rstrip(")")
            
            # Create test configuration
            config = TestConfiguration(
                name=test_name,
                description=f"Multi-model test: {test_name}",
                prompt_template_id=template_id,
                provider_configs=selected_providers,
                iterations=int(self.iterations_var.get()),
                parallel_execution=self.parallel_var.get()
            )
            
            # Create test session
            session = TestSession(
                name=test_name,
                configurations=[config]
            )
            
            self.current_test_session = session
            
            # Start test in background thread
            self.status_var.set("Starting test...")
            self.progress_var.set(0)
            
            test_thread = threading.Thread(
                target=self._run_test_session,
                args=(session,),
                daemon=True
            )
            test_thread.start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start test: {e}")
    
    def _run_test_session(self, session: TestSession):
        """Run test session in background thread."""
        try:
            self.status_var.set("Running tests...")
            
            # Simulate test execution with progress updates
            total_tests = len(session.configurations[0].provider_configs) * session.configurations[0].iterations
            completed = 0
            
            for provider_id in session.configurations[0].provider_configs:
                for iteration in range(session.configurations[0].iterations):
                    # Simulate test execution
                    import time
                    time.sleep(1)  # Simulate work
                    
                    completed += 1
                    progress = (completed / total_tests) * 100
                    self.progress_var.set(progress)
                    
                    # Update status
                    provider_name = next(
                        (p["name"] for p in self.available_providers if p["id"] == provider_id),
                        provider_id
                    )
                    self.status_var.set(f"Testing {provider_name} (iteration {iteration + 1})")
            
            # Test completed
            self.status_var.set("Test completed")
            self.progress_var.set(100)
            
            # Generate mock results
            self._generate_mock_results(session)
            
            # Update UI on main thread
            self.parent.after(0, self._on_test_completed, session)
            
        except Exception as e:
            self.parent.after(0, lambda: messagebox.showerror("Error", f"Test failed: {e}"))
    
    def _generate_mock_results(self, session: TestSession):
        """Generate mock test results for demonstration."""
        import random
        
        for provider_id in session.configurations[0].provider_configs:
            provider_name = next(
                (p["name"] for p in self.available_providers if p["id"] == provider_id),
                provider_id
            )
            
            # Generate mock result
            result = {
                "provider_id": provider_id,
                "provider_name": provider_name,
                "model": "default-model",
                "score": round(random.uniform(0.6, 0.95), 3),
                "cost": round(random.uniform(0.001, 0.01), 4),
                "response_time": round(random.uniform(500, 2000), 0),
                "status": "success",
                "response": f"Mock response from {provider_name}",
                "timestamp": datetime.now().isoformat()
            }
            
            session.results.append(result)
        
        session.status = "completed"
        session.completed_at = datetime.now()
        session.successful_executions = len(session.results)
        session.total_executions = len(session.results)
    
    def _on_test_completed(self, session: TestSession):
        """Handle test completion on main thread."""
        messagebox.showinfo("Success", f"Test '{session.name}' completed successfully!")
        
        # Update session combo boxes
        self.update_session_combos()
        
        # Auto-load results
        self.results_session_var.set(session.name)
        self.load_test_results()
    
    def stop_multi_model_test(self):
        """Stop current multi-model test."""
        self.status_var.set("Stopping test...")
        # In a real implementation, this would signal the test thread to stop
        self.status_var.set("Test stopped")
        self.progress_var.set(0)
    
    def update_session_combos(self):
        """Update session combo boxes with available sessions."""
        if self.current_test_session:
            session_name = self.current_test_session.name
            
            # Update rating session combo
            current_values = list(self.rating_session_combo['values'])
            if session_name not in current_values:
                current_values.append(session_name)
                self.rating_session_combo['values'] = current_values
            
            # Update results session combo
            current_values = list(self.results_session_combo['values'])
            if session_name not in current_values:
                current_values.append(session_name)
                self.results_session_combo['values'] = current_values
    
    def load_rating_session(self):
        """Load session for human rating."""
        try:
            session_name = self.rating_session_var.get()
            if not session_name:
                messagebox.showwarning("Warning", "Please select a session")
                return
            
            if self.current_test_session and self.current_test_session.name == session_name:
                # Load first unrated item
                self.current_rating_index = 0
                self.load_rating_item()
                messagebox.showinfo("Success", f"Loaded session: {session_name}")
            else:
                messagebox.showwarning("Warning", "Session not found or not loaded")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load rating session: {e}")
    
    def load_rating_item(self):
        """Load current item for rating."""
        try:
            if not self.current_test_session or not self.current_test_session.results:
                return
            
            if not hasattr(self, 'current_rating_index'):
                self.current_rating_index = 0
            
            if self.current_rating_index >= len(self.current_test_session.results):
                messagebox.showinfo("Complete", "All items have been rated!")
                return
            
            result = self.current_test_session.results[self.current_rating_index]
            
            # Display prompt (mock)
            self.prompt_display.config(state=tk.NORMAL)
            self.prompt_display.delete(1.0, tk.END)
            self.prompt_display.insert(1.0, f"Test prompt for {result['provider_name']}")
            self.prompt_display.config(state=tk.DISABLED)
            
            # Display response
            self.response_display.config(state=tk.NORMAL)
            self.response_display.delete(1.0, tk.END)
            self.response_display.insert(1.0, result.get('response', 'No response available'))
            self.response_display.config(state=tk.DISABLED)
            
            # Update progress
            total_items = len(self.current_test_session.results)
            self.rating_progress_var.set(f"Item {self.current_rating_index + 1} of {total_items}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load rating item: {e}")
    
    def submit_rating(self):
        """Submit rating for current item."""
        try:
            if not hasattr(self, 'current_rating_index'):
                return
            
            # Get rating values
            quality_score = float(self.quality_score_var.get())
            relevance_score = float(self.relevance_score_var.get())
            comments = self.comments_text.get(1.0, tk.END).strip()
            
            # Store rating (in a real implementation, this would be saved to database)
            result = self.current_test_session.results[self.current_rating_index]
            result['human_rating'] = {
                'quality_score': quality_score,
                'relevance_score': relevance_score,
                'comments': comments,
                'rated_at': datetime.now().isoformat()
            }
            
            # Clear comments
            self.comments_text.delete(1.0, tk.END)
            
            # Move to next item
            self.current_rating_index += 1
            self.load_rating_item()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to submit rating: {e}")
    
    def skip_rating_item(self):
        """Skip current rating item."""
        if hasattr(self, 'current_rating_index'):
            self.current_rating_index += 1
            self.load_rating_item()
    
    def load_test_results(self):
        """Load test results for display."""
        try:
            # Clear existing results
            self.results_tree.delete(*self.results_tree.get_children())
            self.result_details_text.delete(1.0, tk.END)
            
            session_name = self.results_session_var.get()
            if not session_name:
                return
            
            if self.current_test_session and self.current_test_session.name == session_name:
                # Display results
                for result in self.current_test_session.results:
                    self.results_tree.insert("", tk.END, values=(
                        result["provider_name"],
                        result["model"],
                        f"{result['score']:.3f}",
                        f"${result['cost']:.4f}",
                        f"{result['response_time']:.0f}ms",
                        result["status"].title()
                    ))
                
                messagebox.showinfo("Success", f"Loaded {len(self.current_test_session.results)} results")
            else:
                messagebox.showwarning("Warning", "Session not found")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load results: {e}")
    
    def on_result_selected(self, event):
        """Handle result selection."""
        try:
            selection = self.results_tree.selection()
            if not selection:
                return
            
            # Get selected item index
            item = selection[0]
            item_index = self.results_tree.index(item)
            
            if (self.current_test_session and 
                item_index < len(self.current_test_session.results)):
                
                result = self.current_test_session.results[item_index]
                
                # Display result details
                self.result_details_text.delete(1.0, tk.END)
                
                details = f"RESULT DETAILS\n"
                details += "=" * 30 + "\n\n"
                details += f"Provider: {result['provider_name']}\n"
                details += f"Model: {result['model']}\n"
                details += f"Score: {result['score']:.3f}\n"
                details += f"Cost: ${result['cost']:.4f}\n"
                details += f"Response Time: {result['response_time']:.0f}ms\n"
                details += f"Status: {result['status'].title()}\n"
                details += f"Timestamp: {result['timestamp']}\n\n"
                
                details += f"Response:\n"
                details += "-" * 20 + "\n"
                details += result.get('response', 'No response available') + "\n\n"
                
                # Add human rating if available
                if 'human_rating' in result:
                    rating = result['human_rating']
                    details += f"Human Rating:\n"
                    details += "-" * 20 + "\n"
                    details += f"Quality Score: {rating['quality_score']}/10\n"
                    details += f"Relevance Score: {rating['relevance_score']}/10\n"
                    details += f"Comments: {rating['comments']}\n"
                    details += f"Rated At: {rating['rated_at']}\n"
                
                self.result_details_text.insert(1.0, details)
            
        except Exception as e:
            print(f"Error displaying result details: {e}")
    
    def export_test_results(self):
        """Export test results to file."""
        try:
            session_name = self.results_session_var.get()
            if not session_name or not self.current_test_session:
                messagebox.showwarning("Warning", "No session selected or loaded")
                return
            
            # Generate export content
            export_data = {
                "session_name": session_name,
                "exported_at": datetime.now().isoformat(),
                "results": []
            }
            
            for result in self.current_test_session.results:
                export_data["results"].append({
                    "provider": result["provider_name"],
                    "model": result["model"],
                    "score": result["score"],
                    "cost": result["cost"],
                    "response_time": result["response_time"],
                    "status": result["status"],
                    "response": result.get("response", ""),
                    "human_rating": result.get("human_rating", {}),
                    "timestamp": result["timestamp"]
                })
            
            # Save to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_results_{session_name}_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2)
            
            messagebox.showinfo("Success", f"Results exported to {filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export results: {e}")