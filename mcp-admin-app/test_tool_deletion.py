#!/usr/bin/env python3
"""
Test Tool Deletion Functionality
================================

Test script to verify the tool deletion capabilities.
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


def test_tool_deletion():
    """Test the tool deletion functionality."""
    print("Testing Tool Deletion Functionality")
    print("=" * 40)
    
    # Initialize components
    config_manager = ConfigurationManager()
    config_manager.initialize()
    
    db_manager = DatabaseManager(config_manager.database_path)
    db_manager.initialize()
    
    tool_manager = AdvancedToolManager(db_manager)
    
    # Test 1: Get initial tool count
    print("\n1. Getting Initial Tool Count...")
    try:
        initial_tools = tool_manager.get_tool_registry()
        initial_count = len(initial_tools)
        print(f"   Initial tool count: {initial_count}")
        
        if initial_count == 0:
            print("   No tools found. Adding some test tools first...")
            # Discover some tools
            discovered = tool_manager.discover_tools("test-server")
            for tool_info in discovered:
                tool_manager.register_tool(tool_info)
            
            # Get updated count
            initial_tools = tool_manager.get_tool_registry()
            initial_count = len(initial_tools)
            print(f"   Tool count after discovery: {initial_count}")
        
        print("   ✓ Initial tool count retrieved")
    except Exception as e:
        print(f"   ✗ Error getting initial tool count: {e}")
        return
    
    # Test 2: Single Tool Deletion
    print("\n2. Testing Single Tool Deletion...")
    try:
        if initial_count > 0:
            # Select a tool to delete
            test_tool = initial_tools[0]
            tool_id = test_tool.id
            tool_name = test_tool.name
            
            print(f"   Deleting tool: {tool_name} (ID: {tool_id})")
            
            # Delete the tool
            success = tool_manager.delete_tool(tool_id)
            
            if success:
                print("   ✓ Tool deletion successful")
                
                # Verify tool is gone
                deleted_tool = tool_manager.get_tool_by_id(tool_id)
                if deleted_tool is None:
                    print("   ✓ Tool successfully removed from registry")
                else:
                    print("   ⚠ Tool still exists in registry")
                
                # Check updated count
                updated_tools = tool_manager.get_tool_registry()
                new_count = len(updated_tools)
                expected_count = initial_count - 1
                
                if new_count == expected_count:
                    print(f"   ✓ Tool count updated correctly: {new_count}")
                else:
                    print(f"   ⚠ Tool count mismatch: expected {expected_count}, got {new_count}")
            else:
                print("   ✗ Tool deletion failed")
        else:
            print("   ⚠ No tools available for deletion test")
    except Exception as e:
        print(f"   ✗ Single tool deletion test failed: {e}")
    
    # Test 3: Bulk Tool Deletion
    print("\n3. Testing Bulk Tool Deletion...")
    try:
        current_tools = tool_manager.get_tool_registry()
        current_count = len(current_tools)
        
        if current_count >= 3:
            # Select multiple tools to delete
            tools_to_delete = current_tools[:3]
            tool_ids = [tool.id for tool in tools_to_delete]
            tool_names = [tool.name for tool in tools_to_delete]
            
            print(f"   Deleting {len(tools_to_delete)} tools:")
            for name in tool_names:
                print(f"     - {name}")
            
            # Bulk delete
            results = tool_manager.bulk_delete_tools(tool_ids)
            
            # Check results
            successful_deletes = sum(1 for success in results.values() if success)
            failed_deletes = len(results) - successful_deletes
            
            print(f"   Bulk deletion results: {successful_deletes} successful, {failed_deletes} failed")
            
            if successful_deletes > 0:
                print("   ✓ Bulk deletion partially or fully successful")
                
                # Verify tools are gone
                remaining_tools = tool_manager.get_tool_registry()
                remaining_count = len(remaining_tools)
                expected_count = current_count - successful_deletes
                
                if remaining_count == expected_count:
                    print(f"   ✓ Tool count updated correctly: {remaining_count}")
                else:
                    print(f"   ⚠ Tool count mismatch: expected {expected_count}, got {remaining_count}")
            else:
                print("   ✗ Bulk deletion completely failed")
        
        elif current_count > 0:
            print(f"   ⚠ Only {current_count} tools available, testing with available tools")
            
            # Delete all remaining tools
            tool_ids = [tool.id for tool in current_tools]
            results = tool_manager.bulk_delete_tools(tool_ids)
            
            successful_deletes = sum(1 for success in results.values() if success)
            print(f"   Deleted {successful_deletes}/{len(tool_ids)} remaining tools")
        else:
            print("   ⚠ No tools available for bulk deletion test")
    except Exception as e:
        print(f"   ✗ Bulk tool deletion test failed: {e}")
    
    # Test 4: Delete Non-existent Tool
    print("\n4. Testing Delete Non-existent Tool...")
    try:
        fake_tool_id = "non-existent-tool-id-12345"
        success = tool_manager.delete_tool(fake_tool_id)
        
        if not success:
            print("   ✓ Correctly handled non-existent tool deletion")
        else:
            print("   ⚠ Unexpectedly succeeded in deleting non-existent tool")
    except Exception as e:
        print(f"   ✗ Non-existent tool deletion test failed: {e}")
    
    # Test 5: Final Tool Count
    print("\n5. Final Tool Count Check...")
    try:
        final_tools = tool_manager.get_tool_registry()
        final_count = len(final_tools)
        print(f"   Final tool count: {final_count}")
        
        # Show remaining tools
        if final_count > 0:
            print("   Remaining tools:")
            for tool in final_tools[:5]:  # Show first 5
                print(f"     - {tool.name} ({tool.category.value})")
            if final_count > 5:
                print(f"     ... and {final_count - 5} more")
        else:
            print("   No tools remaining in registry")
        
        print("   ✓ Final count check complete")
    except Exception as e:
        print(f"   ✗ Final count check failed: {e}")
    
    print("\n" + "=" * 40)
    print("Tool Deletion Test Complete!")
    print("\nDeletion Features Available:")
    print("1. Single tool deletion with confirmation")
    print("2. Bulk tool deletion for multiple tools")
    print("3. Execution history cleanup on deletion")
    print("4. Error handling for non-existent tools")
    print("5. Registry count validation")
    print("\nTo test in UI:")
    print("1. Run: python main.py")
    print("2. Go to Tools section")
    print("3. Select a tool and click 'Delete Tool'")
    print("4. Or select multiple tools and click 'Bulk Delete'")
    print("5. Or right-click on tools for context menu options")


if __name__ == "__main__":
    test_tool_deletion()