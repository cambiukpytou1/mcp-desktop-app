#!/usr/bin/env python3
"""
Test Batch Tool Execution
=========================

Test script to verify the batch tool execution capabilities.
"""

import sys
import os
from pathlib import Path

# Add the application directory to Python path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

from core.config import ConfigurationManager
from data.database import DatabaseManager
from services.tool_manager import AdvancedToolManager
from services.tool_execution import (
    ToolExecutionEngine, ExecutionRequest, BatchExecutionRequest, SandboxType
)


def test_batch_execution():
    """Test the batch tool execution capabilities."""
    print("Testing Batch Tool Execution")
    print("=" * 40)
    
    # Initialize components
    config_manager = ConfigurationManager()
    config_manager.initialize()
    
    db_manager = DatabaseManager(config_manager.database_path)
    db_manager.initialize()
    
    tool_manager = AdvancedToolManager(db_manager)
    execution_engine = ToolExecutionEngine(db_manager)
    
    # Test 1: Sequential Batch Execution
    print("\n1. Testing Sequential Batch Execution...")
    try:
        tools = tool_manager.get_tool_registry()[:3]  # Test with first 3 tools
        if len(tools) >= 2:
            print(f"   Testing with {len(tools)} tools")
            
            # Create execution requests
            requests = []
            tools_dict = {}
            
            for tool in tools:
                # Create basic parameters
                parameters = {}
                for param in tool.parameters:
                    if param.required:
                        if param.type == "str":
                            parameters[param.name] = f"test_value_for_{tool.name}"
                        elif param.type == "int":
                            parameters[param.name] = 42
                        elif param.type == "bool":
                            parameters[param.name] = True
                        else:
                            parameters[param.name] = "default"
                
                request = ExecutionRequest(
                    tool_id=tool.id,
                    user_id="batch_test_user",
                    parameters=parameters,
                    timeout=10
                )
                requests.append(request)
                tools_dict[tool.id] = tool
            
            # Create batch request (sequential)
            batch_request = BatchExecutionRequest(
                requests=requests,
                user_id="batch_test_user",
                parallel=False,  # Sequential execution
                max_concurrent=1,
                stop_on_error=False,
                timeout=60
            )
            
            # Execute batch
            batch_result = execution_engine.execute_batch(batch_request, tools_dict)
            
            print(f"   Batch ID: {batch_result.batch_id}")
            print(f"   Total requests: {batch_result.total_requests}")
            print(f"   Completed: {batch_result.completed}")
            print(f"   Failed: {batch_result.failed}")
            print(f"   Total time: {batch_result.total_time:.2f}s")
            
            if batch_result.completed > 0:
                print("   ✓ Sequential batch execution successful")
            else:
                print("   ⚠ No tools completed successfully")
        
        else:
            print("   ⚠ Not enough tools for batch testing")
    except Exception as e:
        print(f"   ✗ Sequential batch execution failed: {e}")
    
    # Test 2: Parallel Batch Execution
    print("\n2. Testing Parallel Batch Execution...")
    try:
        tools = tool_manager.get_tool_registry()[:5]  # Test with first 5 tools
        if len(tools) >= 3:
            print(f"   Testing with {len(tools)} tools in parallel")
            
            # Create execution requests
            requests = []
            tools_dict = {}
            
            for tool in tools:
                # Create basic parameters
                parameters = {}
                for param in tool.parameters:
                    if param.required:
                        if param.type == "str":
                            parameters[param.name] = f"parallel_test_{tool.name}"
                        elif param.type == "int":
                            parameters[param.name] = 123
                        elif param.type == "bool":
                            parameters[param.name] = True
                        else:
                            parameters[param.name] = "parallel_default"
                
                request = ExecutionRequest(
                    tool_id=tool.id,
                    user_id="parallel_test_user",
                    parameters=parameters,
                    timeout=15
                )
                requests.append(request)
                tools_dict[tool.id] = tool
            
            # Create batch request (parallel)
            batch_request = BatchExecutionRequest(
                requests=requests,
                user_id="parallel_test_user",
                parallel=True,  # Parallel execution
                max_concurrent=3,
                stop_on_error=False,
                timeout=90
            )
            
            # Execute batch
            batch_result = execution_engine.execute_batch(batch_request, tools_dict)
            
            print(f"   Batch ID: {batch_result.batch_id}")
            print(f"   Total requests: {batch_result.total_requests}")
            print(f"   Completed: {batch_result.completed}")
            print(f"   Failed: {batch_result.failed}")
            print(f"   Total time: {batch_result.total_time:.2f}s")
            
            # Check if parallel execution was faster (should be similar or faster than sequential)
            if batch_result.completed > 0:
                avg_time_per_tool = batch_result.total_time / batch_result.total_requests
                print(f"   Average time per tool: {avg_time_per_tool:.2f}s")
                print("   ✓ Parallel batch execution successful")
            else:
                print("   ⚠ No tools completed successfully")
        
        else:
            print("   ⚠ Not enough tools for parallel batch testing")
    except Exception as e:
        print(f"   ✗ Parallel batch execution failed: {e}")
    
    # Test 3: Batch Execution with Stop on Error
    print("\n3. Testing Batch Execution with Stop on Error...")
    try:
        tools = tool_manager.get_tool_registry()[:3]
        if len(tools) >= 2:
            print(f"   Testing stop-on-error with {len(tools)} tools")
            
            # Create requests with one that will likely fail
            requests = []
            tools_dict = {}
            
            for i, tool in enumerate(tools):
                # For the second tool, use invalid parameters to force failure
                if i == 1:
                    parameters = {"invalid_param": "this_should_fail"}
                else:
                    parameters = {}
                    for param in tool.parameters:
                        if param.required:
                            if param.type == "str":
                                parameters[param.name] = f"stop_test_{tool.name}"
                            elif param.type == "int":
                                parameters[param.name] = 456
                            else:
                                parameters[param.name] = "stop_default"
                
                request = ExecutionRequest(
                    tool_id=tool.id,
                    user_id="stop_test_user",
                    parameters=parameters,
                    timeout=10
                )
                requests.append(request)
                tools_dict[tool.id] = tool
            
            # Create batch request with stop on error
            batch_request = BatchExecutionRequest(
                requests=requests,
                user_id="stop_test_user",
                parallel=False,
                max_concurrent=1,
                stop_on_error=True,  # Stop on first error
                timeout=60
            )
            
            # Execute batch
            batch_result = execution_engine.execute_batch(batch_request, tools_dict)
            
            print(f"   Batch ID: {batch_result.batch_id}")
            print(f"   Total requests: {batch_result.total_requests}")
            print(f"   Completed: {batch_result.completed}")
            print(f"   Failed: {batch_result.failed}")
            print(f"   Results processed: {len(batch_result.results)}")
            
            # Should stop after first failure
            if batch_result.failed > 0 and len(batch_result.results) < len(requests):
                print("   ✓ Stop-on-error functionality working")
            else:
                print("   ⚠ Stop-on-error may not have triggered as expected")
        
        else:
            print("   ⚠ Not enough tools for stop-on-error testing")
    except Exception as e:
        print(f"   ✗ Stop-on-error batch execution failed: {e}")
    
    # Test 4: Batch Execution Results Analysis
    print("\n4. Testing Batch Results Analysis...")
    try:
        # Get execution history to analyze batch results
        history = execution_engine.get_execution_history()
        batch_executions = [exec for exec in history if exec.user_id.startswith("batch_test") or exec.user_id.startswith("parallel_test")]
        
        print(f"   Found {len(batch_executions)} batch-related executions")
        
        if batch_executions:
            # Analyze success rates
            successful = sum(1 for exec in batch_executions if exec.result is not None)
            total = len(batch_executions)
            success_rate = (successful / total) * 100 if total > 0 else 0
            
            print(f"   Success rate: {success_rate:.1f}% ({successful}/{total})")
            
            # Analyze execution times
            exec_times = [exec.execution_time for exec in batch_executions if exec.execution_time]
            if exec_times:
                avg_time = sum(exec_times) / len(exec_times)
                min_time = min(exec_times)
                max_time = max(exec_times)
                
                print(f"   Execution times: avg={avg_time:.3f}s, min={min_time:.3f}s, max={max_time:.3f}s")
            
            print("   ✓ Batch results analysis successful")
        else:
            print("   ⚠ No batch executions found for analysis")
    except Exception as e:
        print(f"   ✗ Batch results analysis failed: {e}")
    
    print("\n" + "=" * 40)
    print("Batch Tool Execution Test Complete!")
    print("\nBatch Execution Features Available:")
    print("1. Sequential batch execution")
    print("2. Parallel batch execution with configurable concurrency")
    print("3. Stop-on-error functionality")
    print("4. Comprehensive result tracking and analysis")
    print("5. Timeout management for batch operations")
    print("6. Resource usage monitoring across batch")
    print("\nTo test in UI:")
    print("1. Run: python main.py")
    print("2. Go to Tools section")
    print("3. Click 'Batch Test' button")
    print("4. Select multiple tools and configure batch options")
    print("5. Execute and view comprehensive results")


if __name__ == "__main__":
    test_batch_execution()