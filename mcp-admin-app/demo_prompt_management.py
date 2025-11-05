"""
Prompt Management Integration Demo
==================================

Demonstrates the new prompt management features integrated into the MCP Admin Application.
"""

import tkinter as tk
from tkinter import messagebox
import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.app import MCPAdminApp


def demo_prompt_management():
    """Demo the prompt management integration."""
    print("🚀 Starting MCP Admin Application with Prompt Management...")
    print("📝 New features available:")
    print("   • Advanced Prompt Management tab in navigation")
    print("   • Tabbed interface for Templates, Security, Collaboration, Analytics, and Evaluation")
    print("   • Shared UI components for template management")
    print("   • Security indicators and version control widgets")
    print("   • Statistics dashboard with real-time updates")
    print("\n💡 Navigate to the 'Prompt Management' tab to explore the new features!")
    
    try:
        # Create and run the application
        app = MCPAdminApp()
        
        # Show info about the new features
        def show_prompt_management_info():
            messagebox.showinfo(
                "New Feature: Advanced Prompt Management",
                "🎉 Welcome to the new Advanced Prompt Management system!\n\n"
                "Features now available:\n"
                "• Template creation and management\n"
                "• Security scanning and compliance\n"
                "• Team collaboration and workflows\n"
                "• Performance analytics and insights\n"
                "• Multi-model evaluation and testing\n\n"
                "Click on the '🚀 Prompt Management' tab to get started!"
            )
        
        # Show the info after the app loads
        app.after(1000, show_prompt_management_info)
        
        # Set up close handler
        app.protocol("WM_DELETE_WINDOW", app.on_closing)
        
        # Start the application
        app.mainloop()
        
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        return False
    
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("MCP Admin Application - Prompt Management Integration Demo")
    print("=" * 60)
    
    success = demo_prompt_management()
    
    if success:
        print("\n✅ Demo completed successfully!")
    else:
        print("\n❌ Demo failed!")
        sys.exit(1)