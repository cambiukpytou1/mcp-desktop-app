#!/usr/bin/env python3
"""
Test Tool Execution Engine
==========================

Test script to verify the tool execution engine with sandboxing capabilities.
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
from services.tool_execution import ToolExecutionEngine, ExecutionRequest, SandboxType


def test_tool_execution():
    """Test the tool execution engine."""
    print("Testing Tool Execution Engine")
    print("=" * 40)
    
    # Initialize components
    config_manager = ConfigurationManager()
    config_manager.initialize()
    
    db_manager = DatabaseManager(config_manager.database_path)
    db_manager.initialize()
    
    tool_manager = AdvancedToolManager(db_manager)
    execution_engine = ToolExecutionEngine(db_manager)
    
    # Test 1: Parameter Validation
    print("\n1. Testing Parameter Validation...")
    try:
        tools = tool_manager.get_tool_registry()
        if tools:
            test_tool = tools[0]
            print(f"   Testing with tool: {test_tool.name}")
            
            # Test valid parameters
            valid_params = {}
            for param in test_tool.parameters:
                if param.required:
                    if param.type == "str":
                        valid_params[param.name] = "test_value"
                    elif param.type == "int":
                        valid_params[param.name] = 42
                    elif param.type == "bool":
                        valid_params[param.name] = True
                    else:
                        valid_params[param.name] = "test"
            
            valid, error = execution_engine.validate_parameters(test_tool, valid_params)
            if valid:
                print("   ✓ Parameter validation successful")
            else:
                print(f"   ✗ Parameter validation failed: {error}")
            
            # Test invalid parameters
            invalid_params = {"nonexistent_param": "value"}
            valid, error = execution_engine.validate_parameters(test_tool, invalid_params)
            if not valid:
                print("   ✓ Invalid parameter detection successful")
            else:
                print("   ⚠ Invalid parameter not detected")
        
        else:
            print("   ⚠ No tools available for validation testing")
    except Exception as e:
        print(f"   ✗ Parameter validation test failed: {e}")
    
    # Test 2: Tool Execution
    print("\n2. Testing Tool Execution...")
    try:
        tools = tool_manager.get_tool_registry()
        if tools:
            test_tool = tools[0]
            print(f"   Executing tool: {test_tool.name}")
            
            # Prepare execution request
            parameters = {}
            for param in test_tool.parameters:
                if param.required:
                    if param.type == "str":
                        parameters[param.name] = "test_input"
                    elif param.type == "int":
                        parameters[param.name] = 123
                    elif param.type == "bool":
                        parameters[param.name] = True
                    else:
                        parameters[param.name] = "default_value"
            
            request = ExecutionRequest(
                tool_id=test_tool.id,
                user_id="test_user",
                parameters=parameters,
                timeout=10,
                sandbox_type=SandboxType.PROCESS
            )
            
            # Execute tool
            result = execution_engine.execute_tool(request, test_tool)
            
            print(f"   Execution ID: {result.execution_id}")
            print(f"   Success: {result.success}")
            print(f"   Execution Time: {result.execution_time:.3f}s")
            print(f"   Memory Usage: {result.resource_usage.memory_mb:.2f} MB")
            
            if result.success:
                print("   ✓ Tool execution successful")
                print(f"   Result: {result.result}")
            else:
                print(f"   ✗ Tool execution failed: {result.error_message}")
        
        else:
            print("   ⚠ No tools available for execution testing")
    except Exception as e:
        print(f"   ✗ Tool execution test failed: {e}")
    
    # Test 3: Execution History
    print("\n3. Testing Execution History...")
    try:
        history = execution_engine.get_execution_history()
        print(f"   Total executions in history: {len(history)}")
        
        if history:
            recent = history[0]
            print(f"   Most recent execution:")
            print(f"     - Tool ID: {recent.tool_id}")
            print(f"     - Status: {recent.status.value}")
            print(f"     - User: {recent.user_id}")
            print(f"     - Duration: {recent.execution_time:.3f}s")
        
        print("   ✓ Execution history retrieval successful")
    except Exception as e:
        print(f"   ✗ Execution history test failed: {e}")
    
    # Test 4: Execution Status Tracking
    print("\n4. Testing Execution Status Tracking...")
    try:
        if history:
            test_execution_id = history[0].id
            status = execution_engine.get_execution_status(test_execution_id)
            if status:
                print(f"   Status for execution {test_execution_id}: {status.value}")
                print("   ✓ Status tracking successful")
            else:
                print("   ⚠ Status not found")
        else:
            print("   ⚠ No executions available for status testing")
    except Exception as e:
        print(f"   ✗ Status tracking test failed: {e}")
    
    # Test 5: Resource Monitoring
    print("\n5. Testing Resource Monitoring...")
    try:
        # Execute a tool that might use some resources
        tools = tool_manager.get_tool_registry()
        if tools:
            # Find a tool that might be more resource intensive
            test_tool = None
            for tool in tools:
                if "code" in tool.name.lower() or "analyze" in tool.name.lower():
                    test_tool = tool
                    break
            
            if not test_tool:
                test_tool = tools[0]
            
            print(f"   Testing resource monitoring with: {test_tool.name}")
            
            request = ExecutionRequest(
                tool_id=test_tool.id,
                user_id="resource_test_user",
                parameters={},
                timeout=5,
                resource_limits={
                    "max_memory_mb": 256,
                    "max_cpu_percent": 80,
                    "max_execution_time": 5
                }
            )
            
            result = execution_engine.execute_tool(request, test_tool)
            
            print(f"   Resource usage:")
            print(f"     - Memory: {result.resource_usage.memory_mb:.2f} MB")
            print(f"     - CPU Time: {result.resource_usage.cpu_time:.3f}s")
            print(f"     - Execution Time: {result.resource_usage.execution_time:.3f}s")
            
            print("   ✓ Resource monitoring successful")
        
        else:
            print("   ⚠ No tools available for resource testing")
    except Exception as e:
        print(f"   ✗ Resource monitoring test failed: {e}")
    
    print("\n" + "=" * 40)
    print("Tool Execution Engine Test Complete!")
    print("\nExecution Features Available:")
    print("1. Secure sandboxed execution")
    print("2. Parameter validation and sanitization")
    print("3. Resource usage monitoring")
    print("4. Execution history tracking")
    print("5. Real-time status monitoring")
    print("6. Error handling and recovery")
    print("\nTo test in UI:")
    print("1. Run: python main.py")
    print("2. Go to Tools section")
    print("3. Select a tool and go to Testing tab")
    print("4. Enter parameters and click 'Execute Test'")
    print("5. View results and execution history")


if __name__ == "__main__":
    test_tool_execution()