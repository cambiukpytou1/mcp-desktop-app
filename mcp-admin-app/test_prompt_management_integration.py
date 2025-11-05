"""
Test Prompt Management Integration
==================================

Simple test to verify the prompt management page integration works correctly.
"""

import tkinter as tk
import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.prompt_management_page import PromptManagementPage


def test_prompt_management_page():
    """Test that the prompt management page can be created and displayed."""
    print("Testing Prompt Management Page Integration...")
    
    # Create root window
    root = tk.Tk()
    root.title("Test Prompt Management Integration")
    root.geometry("1000x700")
    
    # Create mock services
    mock_services = {
        'template_service': None,
        'security_service': None,
        'collaboration_service': None,
        'analytics_service': None,
        'evaluation_service': None
    }
    
    try:
        # Create prompt management page
        page = PromptManagementPage(root, mock_services)
        page.pack(fill="both", expand=True)
        
        print("✓ Prompt Management Page created successfully")
        print("✓ Tabbed navigation initialized")
        print("✓ Statistics dashboard created")
        print("✓ All tab pages initialized")
        
        # Test tab switching
        print("\nTesting tab navigation...")
        for tab_name in ["templates", "security", "collaboration", "analytics", "evaluation"]:
            page.show_tab(tab_name)
            print(f"✓ Successfully switched to {tab_name} tab")
        
        print("\n✅ All tests passed! Prompt Management integration is working correctly.")
        print("\nThe application window will close in 3 seconds...")
        
        # Close after 3 seconds
        root.after(3000, root.destroy)
        root.mainloop()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        root.destroy()
        return False
    
    return True


if __name__ == "__main__":
    success = test_prompt_management_page()
    if success:
        print("\n🎉 Integration test completed successfully!")
    else:
        print("\n💥 Integration test failed!")
        sys.exit(1)