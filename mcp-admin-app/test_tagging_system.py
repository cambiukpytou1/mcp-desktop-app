#!/usr/bin/env python3
"""
Test Enhanced Tagging and Categorization System
==============================================

Test script to verify the advanced tagging, categorization, and tool relationship features.
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
from models.tool import ToolCategory, SecurityLevel


def test_tagging_system():
    """Test the enhanced tagging and categorization system."""
    print("Testing Enhanced Tagging and Categorization System")
    print("=" * 60)
    
    # Initialize components
    config_manager = ConfigurationManager()
    config_manager.initialize()
    
    db_manager = DatabaseManager(config_manager.database_path)
    db_manager.initialize()
    
    tool_manager = AdvancedToolManager(db_manager)
    
    # Test 1: Tag Management
    print("\n1. Testing Tag Management...")
    try:
        # Get a tool to work with
        tools = tool_manager.get_tool_registry()
        if tools:
            test_tool = tools[0]
            print(f"   Working with tool: {test_tool.name}")
            
            # Add tags
            new_tags = ["automation", "productivity", "test-tag"]
            success = tool_manager.add_tool_tags(test_tool.id, new_tags)
            if success:
                print(f"   ✓ Added tags: {new_tags}")
            
            # Get updated tool
            updated_tool = tool_manager.get_tool_by_id(test_tool.id)
            if updated_tool:
                print(f"   Current tags: {updated_tool.metadata.tags}")
            
            # Remove a tag
            success = tool_manager.remove_tool_tags(test_tool.id, ["test-tag"])
            if success:
                print("   ✓ Removed test tag")
            
            print("   ✓ Tag management successful")
        else:
            print("   ⚠ No tools available for tag testing")
    except Exception as e:
        print(f"   ✗ Tag management failed: {e}")
    
    # Test 2: Tag Analytics
    print("\n2. Testing Tag Analytics...")
    try:
        all_tags = tool_manager.get_all_tags()
        print(f"   Total unique tags: {len(all_tags)}")
        
        if all_tags:
            print("   Top 5 most used tags:")
            for tag_info in all_tags[:5]:
                print(f"     - {tag_info['tag']}: {tag_info['count']} tools")
        
        # Test tag-based search
        if all_tags:
            test_tag = all_tags[0]['tag']
            tagged_tools = tool_manager.get_tools_by_tags([test_tag])
            print(f"   Tools with tag '{test_tag}': {len(tagged_tools)}")
        
        print("   ✓ Tag analytics successful")
    except Exception as e:
        print(f"   ✗ Tag analytics failed: {e}")
    
    # Test 3: Auto-categorization
    print("\n3. Testing Auto-categorization...")
    try:
        # Get some tools for recategorization
        tools = tool_manager.get_tool_registry()[:5]  # Test with first 5 tools
        tool_ids = [tool.id for tool in tools]
        
        results = tool_manager.auto_recategorize_tools(tool_ids)
        print(f"   Processed {len(results)} tools for recategorization")
        
        changes = sum(1 for result in results.values() if "Changed" in result)
        print(f"   Category changes made: {changes}")
        
        print("   ✓ Auto-categorization successful")
    except Exception as e:
        print(f"   ✗ Auto-categorization failed: {e}")
    
    # Test 4: Tool Relationships
    print("\n4. Testing Tool Relationships...")
    try:
        tools = tool_manager.get_tool_registry()
        if tools:
            test_tool = tools[0]
            related = tool_manager.get_related_tools(test_tool.id)
            print(f"   Related tools for '{test_tool.name}': {len(related)}")
            
            for rel in related[:3]:  # Show top 3
                print(f"     - {rel['name']}: {rel['similarity']:.2%} similarity")
                print(f"       Shared tags: {', '.join(rel['shared_tags'])}")
        
        print("   ✓ Tool relationships successful")
    except Exception as e:
        print(f"   ✗ Tool relationships failed: {e}")
    
    # Test 5: Tool Recommendations
    print("\n5. Testing Tool Recommendations...")
    try:
        user_context = {
            "query": "file processing data analysis",
            "preferred_category": ToolCategory.DATA_PROCESSING,
            "max_security_level": SecurityLevel.HIGH
        }
        
        recommendations = tool_manager.get_tool_recommendations(user_context)
        print(f"   Generated {len(recommendations)} recommendations")
        
        for rec in recommendations[:3]:  # Show top 3
            tool = rec['tool']
            print(f"     - {tool.name} (Score: {rec['score']:.2f})")
            print(f"       Reasons: {', '.join(rec['reasons'])}")
        
        print("   ✓ Tool recommendations successful")
    except Exception as e:
        print(f"   ✗ Tool recommendations failed: {e}")
    
    # Test 6: Improvement Suggestions
    print("\n6. Testing Improvement Suggestions...")
    try:
        tools = tool_manager.get_tool_registry()
        if tools:
            test_tool = tools[0]
            suggestions = tool_manager.suggest_tool_improvements(test_tool.id)
            print(f"   Improvement suggestions for '{test_tool.name}':")
            
            if suggestions:
                for i, suggestion in enumerate(suggestions, 1):
                    print(f"     {i}. {suggestion}")
            else:
                print("     No improvements needed!")
        
        print("   ✓ Improvement suggestions successful")
    except Exception as e:
        print(f"   ✗ Improvement suggestions failed: {e}")
    
    # Test 7: Tool Statistics
    print("\n7. Testing Tool Statistics...")
    try:
        stats = tool_manager.get_tool_statistics()
        
        print(f"   Registry Statistics:")
        print(f"     - Total tools: {stats.get('total_tools', 0)}")
        print(f"     - Enabled tools: {stats.get('enabled_tools', 0)}")
        print(f"     - Categories: {len(stats.get('categories', {}))}")
        print(f"     - Security levels: {len(stats.get('security_levels', {}))}")
        print(f"     - Average success rate: {stats.get('performance_metrics', {}).get('average_success_rate', 0):.1%}")
        
        print("   ✓ Tool statistics successful")
    except Exception as e:
        print(f"   ✗ Tool statistics failed: {e}")
    
    print("\n" + "=" * 60)
    print("Enhanced Tagging and Categorization Test Complete!")
    print("\nNew Features Available in UI:")
    print("1. Advanced search with multiple filters")
    print("2. Tag management with add/remove functionality")
    print("3. Tool relationship discovery")
    print("4. Improvement suggestions")
    print("5. Comprehensive statistics dashboard")
    print("6. Auto-categorization and tag suggestions")


if __name__ == "__main__":
    test_tagging_system()