"""
Template Management Demo
========================

Comprehensive demo of the new template management features.
"""

import tkinter as tk
from tkinter import messagebox
import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.app import MCPAdminApp


def demo_template_management():
    """Demo the template management features."""
    print("🚀 Starting MCP Admin Application with Template Management Demo...")
    print("\n📝 New Template Management Features:")
    print("   ✅ Rich template editor with syntax highlighting")
    print("   ✅ Template list with search and filtering")
    print("   ✅ Real-time preview functionality")
    print("   ✅ Variable insertion and management")
    print("   ✅ Version control visualization")
    print("   ✅ Template import/export capabilities")
    print("   ✅ Sample templates for demonstration")
    
    print("\n🎯 How to explore the features:")
    print("   1. Click on '🚀 Prompt Management' tab in the left navigation")
    print("   2. Navigate to the 'Templates' tab (should be selected by default)")
    print("   3. Browse the sample templates in the left panel")
    print("   4. Click on any template to load it in the editor")
    print("   5. Try editing the template content and see live preview")
    print("   6. Use the variable insertion buttons")
    print("   7. Test the search and filter functionality")
    print("   8. Create a new template using the 'New' button")
    
    try:
        # Create and run the application
        app = MCPAdminApp()
        
        # Show info about the template management features
        def show_template_management_info():
            messagebox.showinfo(
                "Template Management Features",
                "🎉 Welcome to the Advanced Template Management System!\n\n"
                "New Features Available:\n"
                "• Rich template editor with syntax highlighting\n"
                "• Live preview with variable substitution\n"
                "• Template list with search and filtering\n"
                "• Version control with diff visualization\n"
                "• Variable insertion palette\n"
                "• Template validation and testing\n"
                "• Import/export capabilities\n\n"
                "Navigate to: Prompt Management → Templates tab\n"
                "Try clicking on the sample templates to explore!"
            )
        
        # Show the info after the app loads
        app.after(1500, show_template_management_info)
        
        # Set up close handler
        app.protocol("WM_DELETE_WINDOW", app.on_closing)
        
        # Start the application
        app.mainloop()
        
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        return False
    
    return True


if __name__ == "__main__":
    print("=" * 70)
    print("MCP Admin Application - Template Management Demo")
    print("=" * 70)
    
    success = demo_template_management()
    
    if success:
        print("\n✅ Demo completed successfully!")
    else:
        print("\n❌ Demo failed!")
        sys.exit(1)