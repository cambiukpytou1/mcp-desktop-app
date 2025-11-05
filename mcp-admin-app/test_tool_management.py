#!/usr/bin/env python3
"""
Test Tool Management Features
============================

Simple test script to verify the enhanced tool management functionality.
"""

import sys
import os
from pathlib import Path

# Add the application directory to Python path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

from core.config import ConfigurationManager
from data.database import DatabaseManager
from services.tool_manager import AdvancedToolManager, ToolInfo
from models.tool import ToolCategory, ToolStatus, ToolFilters


def test_tool_management():
    """Test the tool management functionality."""
    print("Testing Enhanced Tool Management System")
    print("=" * 50)
    
    # Initialize components
    config_manager = ConfigurationManager()
    config_manager.initialize()
    
    db_manager = DatabaseManager(config_manager.database_path)
    db_manager.initialize()
    
    tool_manager = AdvancedToolManager(db_manager)
    
    # Test 1: Tool Discovery
    print("\n1. Testing Tool Discovery...")
    try:
        # Simulate discovering tools from a server
        discovered_tools = tool_manager.discover_tools("test-server-1")
        print(f"   Discovered {len(discovered_tools)} tools")
        
        # Register discovered tools
        for tool_info in discovered_tools:
            tool_id = tool_manager.register_tool(tool_info)
            print(f"   Registered tool: {tool_info.name} (ID: {tool_id})")
        
        print("   ✓ Tool discovery and registration successful")
    except Exception as e:
        print(f"   ✗ Tool discovery failed: {e}")
    
    # Test 2: Tool Registry Query
    print("\n2. Testing Tool Registry...")
    try:
        # Get all tools
        all_tools = tool_manager.get_tool_registry()
        print(f"   Total tools in registry: {len(all_tools)}")
        
        # Test filtering
        filters = ToolFilters(category=ToolCategory.FILE_OPERATIONS)
        file_tools = tool_manager.get_tool_registry(filters)
        print(f"   File operation tools: {len(file_tools)}")
        
        # Test search
        search_results = tool_manager.search_tools("file")
        print(f"   Search results for 'file': {len(search_results)}")
        
        print("   ✓ Tool registry queries successful")
    except Exception as e:
        print(f"   ✗ Tool registry queries failed: {e}")
    
    # Test 3: Tool Configuration
    print("\n3. Testing Tool Configuration...")
    try:
        if all_tools:
            tool = all_tools[0]
            print(f"   Configuring tool: {tool.name}")
            
            from services.tool_manager import ToolConfiguration
            from models.tool import SecurityLevel
            
            config = ToolConfiguration(
                enabled=True,
                security_level=SecurityLevel.HIGH,
                rate_limit=10,
                daily_quota=100
            )
            
            success = tool_manager.configure_tool(tool.id, config)
            if success:
                print("   ✓ Tool configuration successful")
            else:
                print("   ✗ Tool configuration failed")
        else:
            print("   ⚠ No tools available for configuration test")
    except Exception as e:
        print(f"   ✗ Tool configuration failed: {e}")
    
    # Test 4: Tool Analytics
    print("\n4. Testing Tool Analytics...")
    try:
        if all_tools:
            tool = all_tools[0]
            status = tool_manager.get_tool_status(tool.id)
            print(f"   Tool status: {status.value if status else 'Unknown'}")
            
            # Display tool details
            print(f"   Tool details:")
            print(f"     - Name: {tool.name}")
            print(f"     - Category: {tool.category.value}")
            print(f"     - Security Level: {tool.security_level.value}")
            print(f"     - Usage Count: {tool.usage_count}")
            print(f"     - Success Rate: {tool.success_rate:.2%}")
            
            print("   ✓ Tool analytics successful")
        else:
            print("   ⚠ No tools available for analytics test")
    except Exception as e:
        print(f"   ✗ Tool analytics failed: {e}")
    
    print("\n" + "=" * 50)
    print("Tool Management Test Complete!")
    print("\nTo test the full UI:")
    print("1. Run: python main.py")
    print("2. Navigate to the 'Tools' section")
    print("3. Click 'Discover Tools' to find tools from configured servers")
    print("4. Select a tool to view details and test functionality")


if __name__ == "__main__":
    test_tool_management()